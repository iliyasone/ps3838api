from dataclasses import dataclass
from typing import TypedDict


class MatchedLeague(TypedDict):
    betsapi_league: str
    ps3838_league: str | None
    ps3838_id: int | None


#######################################
# Return Types For the Matching Tanks #
#######################################


@dataclass
class NoSuchLeague:
    league: str


@dataclass
class NoSuchLeagueMatching(NoSuchLeague):
    pass


@dataclass
class NoSuchLeagueFixtures(NoSuchLeague):
    pass


@dataclass
class WrongLeague(NoSuchLeague):
    pass


@dataclass
class NoSuchEvent:
    league: str
    home: str
    away: str


@dataclass
class EventTooFarInFuture(NoSuchEvent):
    pass


type Failure = NoSuchLeague | NoSuchEvent


#######################################
# Return Types For the Odds Tank      #
#######################################


@dataclass
class NoSuchOddsAvailable:
    event_id: int


type NoResult = NoSuchLeague | NoSuchEvent | NoSuchOddsAvailable
