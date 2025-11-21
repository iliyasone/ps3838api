"""
bets_ps3838.py

A simplified module providing functions to interact with the PS3838 API.
All endpoints required for basic usage (sports, leagues, fixtures, odds,
totals, placing bets, client balance, etc.) are included.

Environment Variables:
    PS3838_LOGIN:    str  # The account username
    PS3838_PASSWORD: str  # The account password

Python Version: 3.12.8 (Strict type hints)
"""

import os
import base64
import uuid
import requests


from typing import Literal, TypedDict, Any, NotRequired
from typing import cast
from typing import Callable, ParamSpec, TypeVar
from functools import wraps
from datetime import datetime

from ps3838api.models.errors import (
    AccessBlockedError,
    BaseballOnlyArgumentError,
    PS3838APIError,
    WrongEndpoint,
)
from ps3838api.models.fixtures import FixturesResponse
from ps3838api.models.lines import LineResponse
from ps3838api.models.odds import OddsResponse
from ps3838api.models.bets import (
    BetType,
    BetsResponse,
    FillType,
    OddsFormat,
    PlaceStraightBetResponse,
    Side,
    Team,
)

###############################################################################
# Environment Variables & Authorization
###############################################################################

_USERNAME: str = os.environ.get("PS3838_LOGIN", "")
_PASSWORD: str = os.environ.get("PS3838_PASSWORD", "")

if not _USERNAME or not _PASSWORD:
    raise ValueError("PS3838_LOGIN and PS3838_PASSWORD must be set in environment.")

# Basic HTTP Auth header
_token: str = base64.b64encode(f"{_USERNAME}:{_PASSWORD}".encode("utf-8")).decode(
    "utf-8"
)
_HEADERS = {
    "Authorization": f"Basic {_token}",
    "User-Agent": "Mozilla/5.0 (PS3838 client)",
    "Content-Type": "application/json",
}


###############################################################################
# API Base
###############################################################################

_BASE_URL: str = os.environ.get("API_BASE_URL",  "https://api.ps3838.com")

###############################################################################
# TypedDict Classes
###############################################################################


class BalanceData(TypedDict):
    availableBalance: float
    outstandingTransactions: float
    givenCredit: float
    currency: str


class PeriodData(TypedDict, total=False):
    number: NotRequired[int]
    description: NotRequired[str]
    shortDescription: NotRequired[str]
    spreadDescription: NotRequired[str]
    moneylineDescription: NotRequired[str]
    totalDescription: NotRequired[str]
    team1TotalDescription: NotRequired[str]
    team2TotalDescription: NotRequired[str]
    spreadShortDescription: NotRequired[str]
    moneylineShortDescription: NotRequired[str]
    totalShortDescription: NotRequired[str]
    team1TotalShortDescription: NotRequired[str]
    team2TotalShortDescription: NotRequired[str]


class LeagueV3(TypedDict):
    id: int
    name: str
    homeTeamType: NotRequired[str]  # Usually "Team1" or "Team2"
    hasOfferings: NotRequired[bool]
    container: NotRequired[str]  # Region/country (e.g., "England")
    allowRoundRobins: NotRequired[bool]
    leagueSpecialsCount: NotRequired[int]
    eventSpecialsCount: NotRequired[int]
    eventCount: NotRequired[int]


###############################################################################
# A normal SPORTS dict (subset or full). You can move this to a JSON if desired.
###############################################################################
_SPORTS: dict[int, str] = {
    1: "Badminton",
    2: "Bandy",
    3: "Baseball",
    4: "Basketball",
    5: "Beach Volleyball",
    6: "Boxing",
    7: "Chess",
    8: "Cricket",
    9: "Curling",
    10: "Darts",
    13: "Field Hockey",
    14: "Floorball",
    15: "Football",
    16: "Futsal",
    17: "Golf",
    18: "Handball",
    19: "Hockey",
    20: "Horse Racing Specials",
    21: "Lacrosse",
    22: "Mixed Martial Arts",
    23: "Other Sports",
    24: "Politics",
    26: "Rugby League",
    27: "Rugby Union",
    28: "Snooker",
    29: "Soccer",
    30: "Softball",
    31: "Squash",
    32: "Table Tennis",
    33: "Tennis",
    34: "Volleyball",
    36: "Water Polo",
    37: "Padel Tennis",
    39: "Aussie Rules",
    40: "Alpine Skiing",
    41: "Biathlon",
    42: "Ski Jumping",
    43: "Cross Country",
    44: "Formula 1",
    45: "Cycling",
    46: "Bobsleigh",
    47: "Figure Skating",
    48: "Freestyle Skiing",
    49: "Luge",
    50: "Nordic Combined",
    51: "Short Track",
    52: "Skeleton",
    53: "Snow Boarding",
    54: "Speed Skating",
    55: "Olympics",
    56: "Athletics",
    57: "Crossfit",
    58: "Entertainment",
    59: "Archery",
    60: "Drone Racing",
    62: "Poker",
    63: "Motorsport",
    64: "Simulated Games",
    65: "Sumo",
}

SOCCER_SPORT_ID = 29
BASEBALL_SPORT_ID = 3


P = ParamSpec("P")
R = TypeVar("R")


def raise_ps3838_api_errors(
    func: Callable[P, requests.Response],
) -> Callable[P, dict[str, Any]]:
    @wraps(func)
    def wrapper(*args: P.args, **kwargs: P.kwargs) -> dict[str, Any]:
        response = func(*args, **kwargs)

        try:
            response.raise_for_status()
            result = response.json()
        except requests.exceptions.HTTPError as e:
            if e.response and e.response.status_code == 405:
                raise WrongEndpoint()
            match e.response.json():
                case {"code": str(code), "message": str(message)}:
                    raise AccessBlockedError(message)
                case _:
                    raise AccessBlockedError(
                        e.response.status_code if e.response else "Unknown"
                    )
        except requests.exceptions.JSONDecodeError:
            raise AccessBlockedError("Empty response")

        match result:
            case {"code": str(code), "message": str(message)}:
                raise PS3838APIError(code=code, message=message)
            case _:
                return result

    return wrapper


###############################################################################
# Helper to make GET requests
###############################################################################
@raise_ps3838_api_errors
def _get(endpoint: str, params: dict[str, Any] | None = None):
    """
    Internal helper to perform GET requests to the PS3838 API.
    Returns JSON-decoded response as Any. Raise errors on non-200.
    """
    url: str = f"{_BASE_URL}{endpoint}"
    response = requests.get(url, headers=_HEADERS, params=params or {})
    return response


###############################################################################
# Helper to make POST requests (for placing bets, etc.)
###############################################################################
@raise_ps3838_api_errors
def _post(endpoint: str, body: dict[str, Any]):
    """
    Internal helper to perform POST requests to the PS3838 API.
    Returns JSON-decoded response as Any. Raise errors on non-200.
    """
    url: str = f"{_BASE_URL}{endpoint}"
    response = requests.post(url, headers=_HEADERS, json=body)
    return response


###############################################################################
# Endpoints
###############################################################################


def get_client_balance() -> BalanceData:
    """
    Returns current client balance, outstanding transactions, credit, and currency.
    GET https://api.ps3838.com/v1/client/balance
    """
    endpoint = "/v1/client/balance"
    data: Any = _get(endpoint)
    # We expect data like:
    # {
    #   "availableBalance": float,
    #   "outstandingTransactions": float,
    #   "givenCredit": float,
    #   "currency": "USD"
    # }
    return cast(BalanceData, data)


def get_periods(sport_id: int = SOCCER_SPORT_ID) -> list[PeriodData]:
    """
    Returns all periods for a given sport.
    GET https://api.ps3838.com/v1/periods?sportId={sport_id}
    """
    endpoint = "/v1/periods"
    data = _get(endpoint, params={"sportId": str(sport_id)})
    # Typically the response is { "periods": [ { ...PeriodData... }, ... ] }
    # We'll return just the list of PeriodData.
    periods_data = data.get("periods", [])
    return cast(list[PeriodData], periods_data)


def get_sports() -> Any:
    """
    GET https://api.ps3838.com/v3/sports
    Returns available sports. Fields uncertain, so use Any.
    """
    endpoint = "/v3/sports"
    return _get(endpoint)


def get_leagues(sport_id: int = SOCCER_SPORT_ID) -> list[LeagueV3]:
    """
    GET https://api.ps3838.com/v3/leagues?sportId={sport_id}
    Returns leagues for a particular sport. Fields uncertain, so use Any.
    """
    endpoint = "/v3/leagues"
    data = _get(endpoint, params={"sportId": sport_id})
    leagues_data = data.get("leagues", [])
    return cast(list[LeagueV3], leagues_data)


def get_fixtures(
    sport_id: int = SOCCER_SPORT_ID,
    league_ids: list[int] | None = None,
    is_live: bool | None = None,
    since: int | None = None,
    event_ids: list[int] | None = None,
    settled: bool = False,
) -> FixturesResponse:
    """
    GET https://api.ps3838.com/v3/fixtures  or  /v3/fixtures/settled
    Query parameters:
        sportId, leagueIds, isLive, since, eventIds, ...
    Returns fixtures data. Use Any for uncertain fields.
    """
    subpath = "/v3/fixtures/settled" if settled else "/v3/fixtures"
    endpoint = f"{subpath}"

    params: dict[str, Any] = {"sportId": sport_id}
    if league_ids:
        params["leagueIds"] = ",".join(map(str, league_ids))
    if is_live is not None:
        params["isLive"] = int(is_live)
    if since is not None:
        params["since"] = since
    if event_ids:
        params["eventIds"] = ",".join(map(str, event_ids))

    return cast(FixturesResponse, _get(endpoint, params))


def get_odds(
    sport_id: int = SOCCER_SPORT_ID,
    is_special: bool = False,
    league_ids: list[int] | None = None,
    odds_format: OddsFormat = "DECIMAL",
    since: int | None = None,
    is_live: bool | None = None,
    event_ids: list[int] | None = None,
) -> OddsResponse:
    """
    GET Straight Odds (v3) or GET Special Odds (v2) for non-settled events.
    - If is_special=True -> https://api.ps3838.com/v2/odds/special
    - Else -> https://api.ps3838.com/v3/odds
    Allows filtering by leagueIds, eventIds, etc.
    """
    if is_special:
        endpoint = "/v2/odds/special"
    else:
        endpoint = "/v3/odds"

    params: dict[str, Any] = {
        "sportId": sport_id,
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

    return cast(OddsResponse, _get(endpoint, params))


def get_special_fixtures(
    sport_id: int = SOCCER_SPORT_ID,
    league_ids: list[int] | None = None,
    event_id: int | None = None,
) -> Any:
    """
    GET https://api.ps3838.com/v2/fixtures/special
    Returns special fixtures for non-settled events in a given sport.
    Possibly filter by leagueIds or eventId.
    """
    endpoint = "/v2/fixtures/special"
    params: dict[str, Any] = {"sportId": sport_id, "oddsFormat": "Decimal"}

    if league_ids:
        params["leagueIds"] = ",".join(map(str, league_ids))
    if event_id is not None:
        params["eventId"] = event_id

    return _get(endpoint, params)


def get_line(
    league_id: int,
    event_id: int,
    period_number: int,
    bet_type: Literal["SPREAD", "MONEYLINE", "TOTAL_POINTS", "TEAM_TOTAL_POINTS"],
    handicap: float,
    team: Literal["Team1", "Team2", "Draw"] | None = None,
    side: Literal["OVER", "UNDER"] | None = None,
    sport_id: int = SOCCER_SPORT_ID,
    odds_format: str = "Decimal",
) -> LineResponse:
    """
    GET https://api.ps3838.com/v2/line
    or known in docs as "Get Straight Line (v2)".
    Use this to get the exact line, odds, and limit for a single bet (Spread, Total, etc.)

    side is required for TOTAL_POINTS and TEAM_TOTAL_POINTS
    """
    endpoint = "/v2/line"
    params: dict[str, Any] = {
        "sportId": sport_id,
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

    return cast(LineResponse, _get(endpoint, params))

#
# parameters are key only, because all are very important
def place_straigh_bet(
    *,
    stake: float,
    event_id: int,
    bet_type: BetType,
    line_id: int | None,
    # EVENT INFO (JUST GUESSING)
    period_number: int = 0,
    sport_id: int = SOCCER_SPORT_ID,
    # ALT LINE ID
    alt_line_id: int | None = None,
    # BET UUID
    unique_request_id: str | None = None,
    # BETS PARAMETERS
    odds_format: OddsFormat = "DECIMAL",
    fill_type: FillType = "NORMAL",
    accept_better_line: bool = True,
    win_risk_stake: Literal["WIN", "RISK"] = "RISK",
    # BASEBALL ONLY
    pitcher1_must_start: bool = True,
    pitcher2_must_start: bool = True,
    # TEAM
    team: Team | None = None,
    # SIDE (FOR TOTALS)
    side: Side | None = None,
    # HANDICAP (OR POINTS)
    handicap: float | None = None,
) -> PlaceStraightBetResponse:
    """
    https://ps3838api.github.io/docs/#tag/Place-Bets/operation/Bets_StraightV2
    """
    if unique_request_id is None:
        unique_request_id = str(uuid.uuid1())
    if sport_id != BASEBALL_SPORT_ID:
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
        "sportId": sport_id,
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
    data = _post(endpoint, params)
    return cast(PlaceStraightBetResponse, data)


def get_bets(
    bet_ids: list[int] | None = None,
    unique_request_ids: list[str] | None = None,
    since: int | None = None,
) -> BetsResponse:
    """
    GET https://api.ps3838.com/v3/bets
    Retrieve status for placed bets. Filter by betId or since.
    If bet is in PENDING_ACCEPTANCE state, you can poll this every 5s to see if accepted or rejected.
    """
    endpoint = "/v3/bets"
    params: dict[str, Any] = {}
    if bet_ids:
        # Usually you can pass betIds= comma separated.
        params["betIds"] = ",".join(map(str, bet_ids))
    if unique_request_ids:
        params["uniqueRequestIds"] = ",".join(unique_request_ids)
    if since is not None:
        params["since"] = since

    return cast(BetsResponse, _get(endpoint, params))


class BettingStatusResponse(TypedDict):
    status: Literal[
        "ALL_BETTING_ENABLED", "ALL_LIVE_BETTING_CLOSED", "ALL_BETTING_CLOSED"
    ]


def get_betting_status() -> BettingStatusResponse:
    """
    GET https://api.ps3838.com/v1/bets/betting-status

    Returns:
        BettingStatusResponse: A dict containing the current betting status.
        The 'status' field can be one of:
            - "ALL_BETTING_ENABLED"
            - "ALL_LIVE_BETTING_CLOSED"
            - "ALL_BETTING_CLOSED"

    Note:
        During maintenance windows, betting might be disabled.
    """
    endpoint: str = "/v1/bets/betting-status"
    return cast(BettingStatusResponse, _get(endpoint, {}))


def export_my_bets(
    *,
    from_datetime: datetime,
    to_datetime: datetime,
    d: int = -1,
    status: Literal["UNSETTLED","SETTLED"] = "SETTLED",
    sd: bool = False,
    bet_type: str = "WAGER",
    product: str = "SB,PP,BG",
    locale: str = "en_US",
    timezone: str = "GMT-4",
) -> bytes:
    """
    Export account bets for a given time range.

    This wraps the website endpoint:
    GET https://www.ps3838.com/member-service/v2/export/my-bets/all

    Args:
        from_datetime: Start of the export interval.
        to_datetime: End of the export interval.
        d: Extra filter parameter (kept as-is, default -1).
        status: Bet status filter, e.g. "SETTLED".
        sd: Whether to sort descending.
        bet_type: Type of export, e.g. "WAGER".
        product: Comma-separated product list, e.g. "SB,PP,BG".
        locale: Locale string, e.g. "en_US".
        timezone: Timezone identifier, e.g. "GMT-4".

    Returns:
        Raw bytes of .xls file.
    """
    raise NotImplementedError
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

    response = requests.get(url, headers=_HEADERS, params=params)
    response.raise_for_status()
    return response.content
