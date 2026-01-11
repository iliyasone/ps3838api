from __future__ import annotations

from typing import NotRequired, Required, TypedDict


# ─────────────────────────────────────────
# Top-level structure of the response (V3)
# ─────────────────────────────────────────
class OddsResponse(TypedDict):
    sportId: int
    last: int  # Used for `since` in future incremental updates
    leagues: list[OddsLeagueV3]


# ─────────────────────────────────────────
# League level
# ─────────────────────────────────────────
class OddsLeagueV3(TypedDict):
    id: int
    events: list[OddsEventV3]


# ─────────────────────────────────────────
# Event level
# ─────────────────────────────────────────
class OddsEventV3(TypedDict, total=False):
    id: Required[int]
    awayScore: float
    homeScore: float
    awayRedCards: int
    homeRedCards: int
    periods: list[OddsPeriodV3]


# ─────────────────────────────────────────
# Period level (e.g., full match, 1st half, etc.)
# ─────────────────────────────────────────
class OddsPeriodV3(TypedDict, total=False):
    lineId: int
    number: int  # 0 = full match, 1 = 1st half, etc.
    cutoff: str  # ISO datetime string (UTC)
    status: int  # 1 = online, 2 = offline

    maxSpread: float
    maxMoneyline: float
    maxTotal: float
    maxTeamTotal: float

    moneylineUpdatedAt: str
    spreadUpdatedAt: str
    totalUpdatedAt: str
    teamTotalUpdatedAt: str

    spreads: list[OddsSpreadV3]
    moneyline: OddsMoneylineV3
    totals: list[OddsTotalV3]
    teamTotal: OddsTeamTotalsV3

    # Live stats at period level (Match and Extra Time only)
    awayScore: float
    homeScore: float
    awayRedCards: int
    homeRedCards: int


# ─────────────────────────────────────────
# Spread line data (handicap)
# ─────────────────────────────────────────
class OddsSpreadV3(TypedDict, total=False):
    altLineId: int  # Present only for alternative lines
    hdp: float  # Handicap
    home: float  # Decimal odds for home team
    away: float  # Decimal odds for away team
    max: float  # Overrides `maxSpread` if present


# ─────────────────────────────────────────
# Moneyline data (1X2 market)
# ─────────────────────────────────────────
class OddsMoneylineV3(TypedDict, total=False):
    home: float
    away: float
    draw: float  # Optional, only for sports/events with a draw


# ─────────────────────────────────────────
# Total Points line (Over/Under market)
# ─────────────────────────────────────────
class OddsTotalV3(TypedDict):
    altLineId: NotRequired[int]  # Optional alternative line
    points: float  # Total goals/points line
    over: float  # Decimal odds for over
    under: float  # Decimal odds for under
    max: NotRequired[float]  # Overrides `maxTotal` if present


# ─────────────────────────────────────────
# Team Total Points (each team separately)
# ─────────────────────────────────────────
class OddsTeamTotalsV3(TypedDict, total=False):
    home: OddsTeamTotalV3
    away: OddsTeamTotalV3


class OddsTeamTotalV3(TypedDict, total=False):
    points: float  # Team-specific total line
    over: float
    under: float


# ═════════════════════════════════════════════════════════════════════════════
# V4 Odds Models
# ═════════════════════════════════════════════════════════════════════════════


# ─────────────────────────────────────────
# V4 Top-level response structure
# ─────────────────────────────────────────
class OddsResponseV4(TypedDict):
    sportId: int
    last: int  # Used for `since` in future incremental updates
    leagues: list[OddsLeagueV4]


# ─────────────────────────────────────────
# V4 League level
# ─────────────────────────────────────────
class OddsLeagueV4(TypedDict):
    id: int
    events: list[OddsEventV4]


# ─────────────────────────────────────────
# V4 Event level
# ─────────────────────────────────────────
class OddsEventV4(TypedDict, total=False):
    id: Required[int]
    awayScore: float
    homeScore: float
    awayRedCards: int
    homeRedCards: int
    periods: list[OddsPeriodV4]


# ─────────────────────────────────────────
# V4 Period level
# ─────────────────────────────────────────
class OddsPeriodV4(TypedDict, total=False):
    lineId: int
    number: int  # 0 = full match, 1 = 1st half, etc.
    cutoff: str  # ISO datetime string (UTC)
    status: int  # 1 = online, 2 = offline

    maxSpread: float
    maxMoneyline: float
    maxTotal: float
    maxTeamTotal: float

    moneylineUpdatedAt: str
    spreadUpdatedAt: str
    totalUpdatedAt: str
    teamTotalUpdatedAt: str

    spreads: list[OddsSpreadV4]
    moneyline: OddsMoneylineV4
    totals: list[OddsTotalV4]
    teamTotal: OddsTeamTotalsV4

    # Live stats at period level (Match and Extra Time only)
    awayScore: float
    homeScore: float
    awayRedCards: int
    homeRedCards: int


# ─────────────────────────────────────────
# V4 Spread line data (handicap)
# ─────────────────────────────────────────
class OddsSpreadV4(TypedDict, total=False):
    altLineId: int  # Present only for alternative lines
    hdp: float  # Handicap
    home: float  # Decimal odds for home team
    away: float  # Decimal odds for away team
    max: float  # Overrides `maxSpread` if present


# ─────────────────────────────────────────
# V4 Moneyline data (1X2 market)
# ─────────────────────────────────────────
class OddsMoneylineV4(TypedDict, total=False):
    home: float
    away: float
    draw: float  # Optional, only for sports/events with a draw


# ─────────────────────────────────────────
# V4 Total Points line (Over/Under market)
# ─────────────────────────────────────────
class OddsTotalV4(TypedDict, total=False):
    altLineId: int  # Optional alternative line
    points: Required[float]  # Total goals/points line
    over: Required[float]  # Decimal odds for over
    under: Required[float]  # Decimal odds for under
    max: float  # Overrides `maxTotal` if present


# ─────────────────────────────────────────
# V4 Team Total Points (each team separately)
# Key difference from V3: arrays instead of single objects
# ─────────────────────────────────────────
class OddsTeamTotalsV4(TypedDict, total=False):
    home: list[OddsTeamTotalV4]
    away: list[OddsTeamTotalV4]


class OddsTeamTotalV4(TypedDict, total=False):
    points: Required[float]  # Team-specific total line
    over: Required[float]
    under: Required[float]
    altLineId: int  # Present only for alternative lines
    max: float  # Maximum bet volume for alternative lines
