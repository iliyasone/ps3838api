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
import requests

from typing import TypedDict, Any, NotRequired
from typing import cast

from ps3838api.models.errors import AccessBlockedError, PS3838APIError
from ps3838api.models.fixtures import FixturesResponse
from ps3838api.models.odds import OddsResponse

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

_BASE_URL: str = "https://api.ps3838.com"


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


class BetPlacementRequest(TypedDict, total=False):
    uniqueRequestId: NotRequired[str]
    sportId: int
    eventId: int
    periodNumber: int
    betType: str  # e.g. "TOTAL_POINTS", "MONEYLINE", ...
    team: NotRequired[str]  # e.g. "Team1", "Team2", "Draw"
    side: NotRequired[str]  # e.g. "OVER", "UNDER"
    handicap: NotRequired[float]
    oddsFormat: NotRequired[str]  # "Decimal", "American", ...
    stake: float
    acceptBetterLine: NotRequired[bool]


class BetPlacementResponse(TypedDict, total=False):
    status: NotRequired[str]
    betId: NotRequired[int]
    # Additional fields if needed:
    # "price": float, "errorMessage": str, etc.


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


###############################################################################
# Helper to make GET requests
###############################################################################
def _get(endpoint: str, params: dict[str, Any] | None = None) -> dict[str, Any]:
    """
    Internal helper to perform GET requests to the PS3838 API.
    Returns JSON-decoded response as Any. Raise errors on non-200.
    """
    url: str = f"{_BASE_URL}{endpoint}"
    response = requests.get(url, headers=_HEADERS, params=params or {})
    
    try:
        response.raise_for_status()
        result = response.json()
    except (requests.exceptions.JSONDecodeError, requests.exceptions.HTTPError):
        raise AccessBlockedError()

    
    match result:
        case {"code": str(code), "message": str(message)}:
            raise PS3838APIError(code=code, message=message)
        case _:
            pass
    return result
###############################################################################
# Helper to make POST requests (for placing bets, etc.)
###############################################################################
def _post(endpoint: str, body: dict[str, Any]) -> dict[str, Any]:
    """
    Internal helper to perform POST requests to the PS3838 API.
    Returns JSON-decoded response as Any. Raise errors on non-200.
    """
    url: str = f"{_BASE_URL}{endpoint}"
    response = requests.post(url, headers=_HEADERS, json=body)
    response.raise_for_status()
    return response.json()


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


def get_periods(sport_id: int) -> list[PeriodData]:
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


def get_leagues(sport_id: int) -> list[LeagueV3]:
    """
    GET https://api.ps3838.com/v3/leagues?sportId={sport_id}
    Returns leagues for a particular sport. Fields uncertain, so use Any.
    """
    endpoint = "/v3/leagues"
    data = _get(endpoint, params={"sportId": sport_id})
    leagues_data = data.get("leagues", [])
    return cast(list[LeagueV3], leagues_data)


def get_fixtures(
    sport_id: int,
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
    sport_id: int,
    is_special: bool = False,
    league_ids: list[int] | None = None,
    odds_format: str = "Decimal",
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
    sport_id: int, league_ids: list[int] | None = None, event_id: int | None = None
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
    sport_id: int,
    league_id: int,
    event_id: int,
    period_number: int,
    bet_type: str,
    handicap: float,
    team: str | None = None,
    side: str | None = None,
    odds_format: str = "Decimal",
) -> Any:
    """
    GET https://api.ps3838.com/v2/line
    or known in docs as "Get Straight Line (v2)".
    Use this to get the exact line, odds, and limit for a single bet (Spread, Total, etc.)
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

    return _get(endpoint, params)


def place_bet(bet_data: BetPlacementRequest) -> BetPlacementResponse:
    """
    POST https://api.ps3838.com/v2/bets
    Place a straight bet with the specified data.
    E.g. betData = {
        "uniqueRequestId": "abc-123",
        "sportId": 29,
        "eventId": 1234567890,
        "periodNumber": 0,
        "betType": "TOTAL_POINTS",
        "side": "OVER",
        "handicap": 2.5,
        "oddsFormat": "Decimal",
        "stake": 100.0,
        "acceptBetterLine": True
    }

    Returns the bet placement result in a typed dict (status, betId, etc.).
    """
    endpoint = "/v2/bets"
    data = _post(endpoint, dict(bet_data))
    return cast(BetPlacementResponse, data)


def get_bets(bet_ids: list[int] | None = None, since: int | None = None) -> Any:
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
    if since is not None:
        params["since"] = since

    return _get(endpoint, params)
