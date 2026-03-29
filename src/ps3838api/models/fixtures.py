# models/fixtures.py
from datetime import datetime
from enum import IntEnum
from typing import Required, TypedDict


class LiveStatus(IntEnum):
    NO_LIVE_BETTING = 0
    """No live betting will be offered on this event"""

    LIVE_BETTING_EVENT = 1
    """Live betting event"""
    LIVE_WILL_BE_OFERED = 2
    """Live betting will be offered on this event"""


class FixtureV3(TypedDict, total=False):
    """
    Represents a single fixture within the API response.

    - liveStatus: 0=no live, 1=live event, 2=will be offered live
    - status: Deprecated; check period status in /odds
    - betAcceptanceType: 0=none, 1=danger zone, 2=live delay, 3=both
    - parlayRestriction: 0=full parlay allowed, 1=not allowed, 2=partial
    """

    id: Required[int]
    parentId: int
    starts: datetime  # date-time in UTC
    home: Required[str]
    away: Required[str]
    rotNum: str  # Will be removed in future; see docs
    liveStatus: Required[LiveStatus]
    homePitcher: str  # Baseball only
    awayPitcher: str  # Baseball only
    status: str  # "O", "H", or "I" (deprecated)
    betAcceptanceType: int
    parlayRestriction: int
    altTeaser: bool
    resultingUnit: Required[str]  # e.g. "corners", "bookings"
    version: int  # fixture version changes with any update


class FixturesLeagueV3(TypedDict):
    """
    Container for leagues in the Get Fixtures response.
    """

    id: int
    name: str
    events: list[FixtureV3]


class FixturesResponse(TypedDict):
    """
    Full response for GET /v3/fixtures

    - sportId: same as requested ID
    - last: for delta updates (use as 'since' in next request)
    """

    sportId: int
    last: int
    league: list[FixturesLeagueV3]
    """list of leagues"""
