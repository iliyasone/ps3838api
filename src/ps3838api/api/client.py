"""
Client implementation for the PS3838 API.

The Client exposes all endpoints required by the public helper functions while
encapsulating session management, credentials, and error handling.
"""

import base64
import os
import uuid
from datetime import datetime
from typing import Any, Literal, cast, overload

import requests
from requests import Response, Session

from ps3838api.api.v4client import V4PinnacleClient
from ps3838api.models.bets import (
    BetList,
    BetsResponse,
    BetStatus,
    BetType,
    FillType,
    OddsFormat,
    PlaceStraightBetResponse,
    Side,
    SortDir,
    Team,
)
from ps3838api.models.client import BalanceData, BettingStatusResponse, LeagueV3, PeriodData
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


class PinnacleClient:
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
        # prepare login and password
        self.default_sport = default_sport
        self._login = login or os.environ.get("PS3838_LOGIN") or os.environ.get("PINNACLE_LOGIN")
        self._password = password or os.environ.get("PS3838_PASSWORD") or os.environ.get("PINNACLE_PASSWORD")
        if not self._login or not self._password:
            raise ValueError(
                "login and password must be provided either via "
                "Client() arguments or PINNACLE_LOGIN/PS3838_LOGIN and PINNACLE_PASSWORD/PS3838_PASSWORD"
                "environment variables."
            )

        env_base_url = os.environ.get("PS3838_API_BASE_URL") or os.environ.get("PINNACLE_API_BASE_URL")
        resolved_base_url = api_base_url or env_base_url or DEFAULT_API_BASE_URL
        self._base_url = resolved_base_url.rstrip("/")
        # prepare session and headers
        token = base64.b64encode(f"{self._login}:{self._password}".encode("utf-8"))
        self._headers = {
            "Authorization": f"Basic {token.decode('utf-8')}",
            "User-Agent": "ps3838api (https://github.com/iliyasone/ps3838api)",
            "Content-Type": "application/json",
        }

        self._session = session or requests.Session()
        self._session.headers.update(self._headers)
        # init v4 subclient
        self.v4 = V4PinnacleClient(self)

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
                    case object():
                        pass

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

    def place_straight_bet(
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

    @overload
    def get_bets(
        self,
        *,
        unique_request_ids: list[str],
    ) -> "BetsResponse":
        """Get bets by unique request IDs.

        A comma separated list of `uniqueRequestId` from the place bet request.
        If specified, it's highest priority, all other parameters are ignored.
        Maximum is 10 ids. If client has bet id, preferred way is to use `betIds`
        query parameter, you can use `uniqueRequestIds` when you do not have bet id.

        There are 2 cases when client may not have a bet id:

        1. When you bet on live event with live delay, place bet response in that
           case does not return bet id, so client can query bet status by
           `uniqueRequestIds`.
        2. In case of any network issues when client is not sure what happened
           with his place bet request. Empty response means that the bet was not
           placed.

        Note that there is a restriction: querying by uniqueRequestIds is supported
        for straight and special bets and only up to 30 min from the moment the
        bet was placed.

        Args:
            unique_request_ids: List of unique request IDs. Maximum is 10 ids.

        Returns:
            BetsResponse containing matching bets.
        """
        ...

    @overload
    def get_bets(
        self,
        *,
        bet_ids: list[int],
    ) -> "BetsResponse":
        """Get bets by bet IDs.

        A comma separated list of bet ids. When betids is submitted, no other
        parameter is necessary. Maximum is 100 ids. Works for all non settled
        bets and all bets settled in the last 30 days.

        Args:
            bet_ids: List of bet IDs. Maximum is 100 ids.

        Returns:
            BetsResponse containing matching bets.
        """
        ...

    @overload
    def get_bets(
        self,
        *,
        betlist: BetList,
        from_date: datetime,
        to_date: datetime,
        bet_statuses: list[BetStatus] | None = ...,
        sort_dir: SortDir = ...,
        page_size: int = ...,
        from_record: int = ...,
        bet_type: list[BetType] | None = ...,
    ) -> "BetsResponse":
        """Get bets by date range and bet list type.

        Args:
            betlist: Type of bet list to return (SETTLED, RUNNING, ALL).
            from_date: Start date of the requested period. Required when betlist
                parameter is submitted. Start date can be up to 30 days in the past.
                Expected format is ISO8601 - can be set to just date or date and time.
            to_date: End date of the requested period. Required when betlist
                parameter is submitted. Expected format is ISO8601 - can be set to
                just date or date and time. toDate value is exclusive, meaning it
                cannot be equal to fromDate.
            bet_statuses: Type of bet statuses to return (WON, LOSE, CANCELLED,
                REFUNDED, NOT_ACCEPTED, ACCEPTED, PENDING_ACCEPTANCE). This works
                only in conjunction with betlist, as additional filter.
            sort_dir: Sort direction by postedAt/settledAt (ASC, DESC). Respected
                only when querying by date range. Defaults to ASC.
            page_size: Page size. Max is 1000. Respected only when querying by date
                range. Defaults to 1000.
            from_record: Starting record (inclusive) of the result. Respected only
                when querying by date range. To fetch next page set it to toRecord+1.
                Defaults to 0.
            bet_type: A comma separated list of bet types (SPREAD, MONEYLINE,
                TOTAL_POINTS, TEAM_TOTAL_POINTS, SPECIAL, PARLAY, TEASER, MANUAL).

        Returns:
            BetsResponse containing matching bets.
        """
        ...

    def get_bets(
        self,
        *,
        bet_ids: list[int] | None = None,
        unique_request_ids: list[str] | None = None,
        betlist: BetList | None = None,
        bet_statuses: list[BetStatus] | None = None,
        from_date: datetime | None = None,
        to_date: datetime | None = None,
        sort_dir: SortDir = "ASC",
        page_size: int = 1000,
        from_record: int = 0,
        bet_type: list[BetType] | None = None,
    ) -> "BetsResponse":
        endpoint = "/v3/bets"
        params: dict[str, Any] = {}

        if unique_request_ids is not None:
            if not unique_request_ids:
                raise ValueError("uniqueRequestIds must not be empty")
            if len(unique_request_ids) > 10:
                raise ValueError("uniqueRequestIds max is 10")
            params["uniqueRequestIds"] = ",".join(unique_request_ids)
            return cast("BetsResponse", self._get(endpoint, params))

        if bet_ids is not None:
            if not bet_ids:
                raise ValueError("betIds must not be empty")
            if len(bet_ids) > 100:
                raise ValueError("betIds max is 100")
            params["betIds"] = ",".join(map(str, bet_ids))
            return cast("BetsResponse", self._get(endpoint, params))

        if betlist is None:
            raise ValueError("betlist is required when betIds and uniqueRequestIds are not provided")
        if from_date is None or to_date is None:
            raise ValueError("fromDate and toDate are required when betlist is submitted")
        if to_date <= from_date:
            raise ValueError("toDate must be exclusive and greater than fromDate")
        if not (1 <= page_size <= 1000):
            raise ValueError("pageSize must be between 1 and 1000")
        if from_record < 0:
            raise ValueError("fromRecord must be >= 0")

        params["betlist"] = betlist
        params["fromDate"] = from_date.isoformat()
        params["toDate"] = to_date.isoformat()
        params["sortDir"] = sort_dir
        params["pageSize"] = page_size
        params["fromRecord"] = from_record

        if bet_statuses:
            params["betStatuses"] = ",".join(bet_statuses)
        if bet_type:
            params["betType"] = ",".join(bet_type)

        return cast("BetsResponse", self._get(endpoint, params))

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


__all__ = ["PinnacleClient", "DEFAULT_API_BASE_URL"]
