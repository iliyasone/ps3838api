# models/fixtures.py
from datetime import datetime
from enum import IntEnum
from typing import Required, TypedDict


class LiveStatus(IntEnum):
    NO_LIVE_BETTING = 0
    """No live betting will be offered on this event"""

    LIVE_BETTING_EVENT = 1
    """Live betting event"""

    LIVE_WILL_BE_OFFERED = 2
    """Live betting will be offered on this event"""


class BetAcceptanceType(IntEnum):
    NOT_APPLICABLE = 0
    """No bet acceptance type restriction applies"""

    DANGER_ZONE = 1
    """Soccer live event is in the danger zone"""

    LIVE_DELAY = 2
    """Soccer live event is subject to live delay"""

    BOTH = 3
    """Both danger zone and live delay apply"""


class ParlayRestriction(IntEnum):
    ALLOWED = 0
    """Allowed to parlay without restrictions"""

    NOT_ALLOWED = 1
    """Not allowed to parlay this event"""

    RESTRICTED = 2
    """Allowed to parlay, but only one leg from the same event is allowed"""


class FixtureV3(TypedDict, total=False):
    """
    Represents a single fixture returned by `GET /v3/fixtures`.
    """

    id: Required[int]
    """Event id."""

    parentId: int
    """Parent event id when the event is linked to another event."""

    starts: Required[datetime]
    """Event start time in UTC."""

    home: Required[str]
    """Home team name."""

    away: Required[str]
    """Away team name."""

    rotNum: str
    """Rotation number. Scheduled for removal in a future API version."""

    liveStatus: Required[LiveStatus]
    """Live availability status for the event."""

    homePitcher: str
    """Home team pitcher. Present only for baseball."""

    awayPitcher: str
    """Away team pitcher. Present only for baseball."""

    betAcceptanceType: BetAcceptanceType
    """Soccer live event bet acceptance type for the current customer."""

    parlayRestriction: ParlayRestriction
    """Parlay availability and restriction level for the event."""

    altTeaser: bool
    """Whether the event offers alternative teaser points."""

    resultingUnit: str
    """Unit used for resulting the event, for example `Corners` or `Bookings`."""

    version: int
    """Fixture version. Increments whenever the fixture changes."""


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
