"""
Client implementation for the PS3838 API.

The Client exposes all endpoints required by the public helper functions while
encapsulating session management, credentials, and error handling.
"""

import base64
import os
import uuid
from datetime import datetime
from typing import Any, Literal, cast

import requests
from requests import Response, Session

from ps3838api.models.bets import (
    BetType,
    BetsResponse,
    FillType,
    OddsFormat,
    PlaceStraightBetResponse,
    Side,
    Team,
)
from ps3838api.models.client import (
    BalanceData,
    BettingStatusResponse,
    LeagueV3,
    PeriodData,
)
from ps3838api.models.errors import (
    AccessBlockedError,
    BaseballOnlyArgumentError,
    PS3838APIError,
    WrongEndpoint,
)
from ps3838api.models.fixtures import FixturesResponse
from ps3838api.models.lines import LineResponse
from ps3838api.models.odds import OddsResponse
from ps3838api.models.sports import BASEBALL_SPORT_ID, SOCCER_SPORT_ID, Sport

DEFAULT_API_BASE_URL = "https://api.ps3838.com"


class Client:
    """Stateful PS3838 API client backed by ``requests.Session``."""

    def __init__(
        self,
        login: str | None = None,
        password: str | None = None,
        api_base_url: str | None = None,
        default_sport: Sport = SOCCER_SPORT_ID,
        *,
        session: Session | None = None,
    ) -> None:
        self.default_sport = default_sport
        self._login = login or os.environ.get("PS3838_LOGIN")
        self._password = password or os.environ.get("PS3838_PASSWORD")
        if not self._login or not self._password:
            raise ValueError(
                "PS3838_LOGIN and PS3838_PASSWORD must be provided either via "
                "Client() arguments or environment variables."
            )

        env_base_url = os.environ.get("PS3838_API_BASE_URL")
        resolved_base_url = api_base_url or env_base_url or DEFAULT_API_BASE_URL
        self._base_url = resolved_base_url.rstrip("/")

        token = base64.b64encode(f"{self._login}:{self._password}".encode("utf-8"))
        self._headers = {
            "Authorization": f"Basic {token.decode('utf-8')}",
            "User-Agent": "ps3838api (https://github.com/iliyasone/ps3838api)",
            "Content-Type": "application/json",
        }

        self._session = session or requests.Session()
        self._session.headers.update(self._headers)

    # ------------------------------------------------------------------ #
    # Core request helpers
    # ------------------------------------------------------------------ #
    def _handle_response(self, response: Response) -> Any:
        try:
            response.raise_for_status()
            result: Any = response.json()
        except requests.exceptions.HTTPError as exc:
            if exc.response and exc.response.status_code == 405:
                raise WrongEndpoint() from exc

            payload: Any | None = None
            if exc.response is not None:
                try:
                    payload = exc.response.json()
                except requests.exceptions.JSONDecodeError:
                    payload = None

            if isinstance(payload, dict):
                match payload:
                    case {"code": str(code), "message": str(message)}:
                        raise AccessBlockedError(message) from exc

            status_code = exc.response.status_code if exc.response else "Unknown"
            raise AccessBlockedError(status_code) from exc
        except requests.exceptions.JSONDecodeError as exc:
            raise AccessBlockedError("Empty response") from exc

        match result:
            case {"code": str(code), "message": str(message)}:
                raise PS3838APIError(code=code, message=message)
            case _:
                return result

    def _request(
        self,
        method: Literal["GET", "POST"],
        endpoint: str,
        *,
        params: dict[str, Any] | None = None,
        body: dict[str, Any] | None = None,
    ) -> Any:
        url = f"{self._base_url}{endpoint}"
        response = self._session.request(method, url, params=params, json=body)
        return self._handle_response(response)

    def _get(self, endpoint: str, params: dict[str, Any] | None = None) -> Any:
        return self._request("GET", endpoint, params=params)

    def _post(self, endpoint: str, body: dict[str, Any]) -> Any:
        return self._request("POST", endpoint, body=body)

    # ------------------------------------------------------------------ #
    # API endpoints
    # ------------------------------------------------------------------ #
    def get_client_balance(self) -> BalanceData:
        endpoint = "/v1/client/balance"
        data = self._get(endpoint)
        return cast(BalanceData, data)

    def get_periods(self, sport_id: int | None = None) -> list[PeriodData]:
        resolved_sport_id = sport_id if sport_id is not None else self.default_sport
        endpoint = "/v1/periods"
        response = self._get(endpoint, params={"sportId": str(resolved_sport_id)})
        periods_data = response.get("periods", [])
        return cast(list[PeriodData], periods_data)

    def get_sports(self) -> Any:
        endpoint = "/v3/sports"
        return self._get(endpoint)

    def get_leagues(self, sport_id: int | None = None) -> list[LeagueV3]:
        resolved_sport_id = sport_id if sport_id is not None else self.default_sport
        endpoint = "/v3/leagues"
        data = self._get(endpoint, params={"sportId": resolved_sport_id})
        leagues_data = data.get("leagues", [])
        return cast(list[LeagueV3], leagues_data)

    def get_fixtures(
        self,
        sport_id: int | None = None,
        league_ids: list[int] | None = None,
        is_live: bool | None = None,
        since: int | None = None,
        event_ids: list[int] | None = None,
        settled: bool = False,
    ) -> FixturesResponse:
        subpath = "/v3/fixtures/settled" if settled else "/v3/fixtures"
        endpoint = f"{subpath}"

        resolved_sport_id = sport_id if sport_id is not None else self.default_sport

        params: dict[str, Any] = {"sportId": resolved_sport_id}
        if league_ids:
            params["leagueIds"] = ",".join(map(str, league_ids))
        if is_live is not None:
            params["isLive"] = int(is_live)
        if since is not None:
            params["since"] = since
        if event_ids:
            params["eventIds"] = ",".join(map(str, event_ids))

        return cast(FixturesResponse, self._get(endpoint, params))

    def get_odds(
        self,
        sport_id: int | None = None,
        is_special: bool = False,
        league_ids: list[int] | None = None,
        odds_format: OddsFormat = "DECIMAL",
        since: int | None = None,
        is_live: bool | None = None,
        event_ids: list[int] | None = None,
    ) -> OddsResponse:
        endpoint = "/v2/odds/special" if is_special else "/v3/odds"

        resolved_sport_id = sport_id if sport_id is not None else self.default_sport

        params: dict[str, Any] = {
            "sportId": resolved_sport_id,
            "oddsFormat": odds_format,
        }
        if league_ids:
            params["leagueIds"] = ",".join(map(str, league_ids))
        if since is not None:
            params["since"] = since
        if is_live is not None:
            params["isLive"] = int(is_live)
        if event_ids:
            params["eventIds"] = ",".join(map(str, event_ids))

        return cast(OddsResponse, self._get(endpoint, params))

    def get_special_fixtures(
        self,
        sport_id: int | None = None,
        league_ids: list[int] | None = None,
        event_id: int | None = None,
    ) -> Any:
        endpoint = "/v2/fixtures/special"
        resolved_sport_id = sport_id if sport_id is not None else self.default_sport
        params: dict[str, Any] = {"sportId": resolved_sport_id, "oddsFormat": "Decimal"}

        if league_ids:
            params["leagueIds"] = ",".join(map(str, league_ids))
        if event_id is not None:
            params["eventId"] = event_id

        return self._get(endpoint, params)

    def get_line(
        self,
        league_id: int,
        event_id: int,
        period_number: int,
        bet_type: Literal["SPREAD", "MONEYLINE", "TOTAL_POINTS", "TEAM_TOTAL_POINTS"],
        handicap: float,
        team: Literal["Team1", "Team2", "Draw"] | None = None,
        side: Literal["OVER", "UNDER"] | None = None,
        sport_id: int | None = None,
        odds_format: str = "Decimal",
    ) -> LineResponse:
        endpoint = "/v2/line"
        resolved_sport_id = sport_id if sport_id is not None else self.default_sport
        params: dict[str, Any] = {
            "sportId": resolved_sport_id,
            "leagueId": league_id,
            "eventId": event_id,
            "periodNumber": period_number,
            "betType": bet_type,
            "handicap": handicap,
            "oddsFormat": odds_format,
        }
        if team:
            params["team"] = team
        if side:
            params["side"] = side

        return cast(LineResponse, self._get(endpoint, params))

    def place_straigh_bet(
        self,
        *,
        stake: float,
        event_id: int,
        bet_type: BetType,
        line_id: int | None,
        period_number: int = 0,
        sport_id: int | None = None,
        alt_line_id: int | None = None,
        unique_request_id: str | None = None,
        odds_format: OddsFormat = "DECIMAL",
        fill_type: FillType = "NORMAL",
        accept_better_line: bool = True,
        win_risk_stake: Literal["WIN", "RISK"] = "RISK",
        pitcher1_must_start: bool = True,
        pitcher2_must_start: bool = True,
        team: Team | None = None,
        side: Side | None = None,
        handicap: float | None = None,
    ) -> PlaceStraightBetResponse:
        if unique_request_id is None:
            unique_request_id = str(uuid.uuid1())

        resolved_sport_id = sport_id if sport_id is not None else self.default_sport

        if resolved_sport_id != BASEBALL_SPORT_ID:
            if not pitcher1_must_start or not pitcher2_must_start:
                raise BaseballOnlyArgumentError()
        params: dict[str, Any] = {
            "oddsFormat": odds_format,
            "uniqueRequestId": unique_request_id,
            "acceptBetterLine": accept_better_line,
            "stake": stake,
            "winRiskStake": win_risk_stake,
            "pitcher1MustStart": pitcher1_must_start,
            "pitcher2MustStart": pitcher2_must_start,
            "fillType": fill_type,
            "sportId": resolved_sport_id,
            "eventId": event_id,
            "periodNumber": period_number,
            "betType": bet_type,
        }
        if team is not None:
            params["team"] = team
        if line_id is not None:
            params["lineId"] = line_id
        if alt_line_id is not None:
            params["altLineId"] = alt_line_id
        if side is not None:
            params["side"] = side
        if handicap is not None:
            params["handicap"] = handicap

        endpoint = "/v2/bets/place"
        data = self._post(endpoint, params)
        return cast(PlaceStraightBetResponse, data)

    def get_bets(
        self,
        bet_ids: list[int] | None = None,
        unique_request_ids: list[str] | None = None,
        since: int | None = None,
    ) -> BetsResponse:
        endpoint = "/v3/bets"
        params: dict[str, Any] = {}
        if bet_ids:
            params["betIds"] = ",".join(map(str, bet_ids))
        if unique_request_ids:
            params["uniqueRequestIds"] = ",".join(unique_request_ids)
        if since is not None:
            params["since"] = since

        return cast(BetsResponse, self._get(endpoint, params))

    def get_betting_status(self) -> BettingStatusResponse:
        endpoint = "/v1/bets/betting-status"
        return cast(BettingStatusResponse, self._get(endpoint, {}))

    def export_my_bets(
        self,
        *,
        from_datetime: datetime,
        to_datetime: datetime,
        d: int = -1,
        status: Literal["UNSETTLED", "SETTLED"] = "SETTLED",
        sd: bool = False,
        bet_type: str = "WAGER",
        product: str = "SB,PP,BG",
        locale: str = "en_US",
        timezone: str = "GMT-4",
    ) -> bytes:
        url = "https://www.ps3838.com/member-service/v2/export/my-bets/all"

        params: dict[str, Any] = {
            "f": from_datetime.strftime("%Y-%m-%d %H:%M:%S"),
            "t": to_datetime.strftime("%Y-%m-%d %H:%M:%S"),
            "d": d,
            "s": status,
            "sd": str(sd).lower(),
            "type": bet_type,
            "product": product,
            "locale": locale,
            "timezone": timezone,
        }

        response = self._session.get(url, headers=self._headers, params=params)
        response.raise_for_status()
        return response.content


__all__ = ["Client", "DEFAULT_API_BASE_URL"]
