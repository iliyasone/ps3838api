from dataclasses import dataclass, field
import json
from pathlib import Path
from time import time
from typing import TypedDict

from ps3838api import ROOT_DIR
import ps3838api.api as ps

from ps3838api.logic import (
    filter_odds,
    find_league_in_fixtures,
    merge_fixtures,
    merge_odds_response,
)
from ps3838api.matching import find_event_in_league, match_league
from ps3838api.models.fixtures import FixturesResponse
from ps3838api.models.odds import OddsEventV3, OddsResponse
from ps3838api.models.event import (
    Failure,
    NoResult,
    NoSuchLeague,
)


class FixtureTank:
    """Stores ps3838 events in a big tank (storage)

    Responsibilites:
    - get the odds
    - keep the `since` parameter
    - update and "zip" them
    - TODO: remove old ones
    """

    def __init__(self, file_path: str | Path = ROOT_DIR / "temp/fixtures.json") -> None:
        self.file_path = file_path
        try:
            with open(self.file_path) as file:
                self.data: FixturesResponse = json.load(file)
        except FileNotFoundError:
            self.data: FixturesResponse = ps.get_fixtures(ps.SOCCER_SPORT_ID)

    def update(self):
        delta = ps.get_fixtures(ps.SOCCER_SPORT_ID, since=self.data["last"])
        self.data = merge_fixtures(self.data, delta)

    def save(self):
        with open(self.file_path, "w") as file:
            json.dump(self.data, file, indent=4)


MIN_TIME_DELTA_UPDATE = 5
"""
Delta calls to /fixtures and /odds endpoints must be restricted to once every 5 seconds, 
regardless of the leagueIds, eventIds or islive parameters.

Source: Fair Use Policy: https://ps3838api.github.io/FairUsePolicy.html
"""


class OddsTank:
    def __init__(self, file_path: str | Path = ROOT_DIR / "temp/odds.json") -> None:
        self.file_path = file_path
        self.last_time_updated: float = 0
        self.is_live: bool | None = None
        try:
            with open(file_path) as file:
                self.data: OddsResponse = json.load(file)
        except FileNotFoundError:
            self.data: OddsResponse = ps.get_odds(ps.SOCCER_SPORT_ID)
            self.last_time_updated = time()

    def update(self):
        if time() - self.last_time_updated < MIN_TIME_DELTA_UPDATE:
            return
        delta = ps.get_odds(
            ps.SOCCER_SPORT_ID, is_live=self.is_live, since=self.data["last"]
        )
        self.data = merge_odds_response(self.data, delta)

    def save(self):
        with open(self.file_path, "w") as file:
            json.dump(self.data, file, indent=4)


class EventInfo(TypedDict):
    leagueId: int
    eventId: int


@dataclass
class EventMatcher:
    fixtures: FixtureTank = field(default_factory=FixtureTank)
    odds: OddsTank = field(default_factory=OddsTank)

    def save(self):
        self.fixtures.save()
        self.odds.save()

    def get_league_id_and_event_id(
        self, league: str, home: str, away: str, force_local: bool = False
    ) -> EventInfo | Failure:
        match match_league(league_betsapi=league):
            case NoSuchLeague() as f:
                return f
            case matched_league:
                league_id = matched_league["ps3838_id"]
                assert league_id is not None
        leagueV3 = find_league_in_fixtures(self.fixtures.data, league, league_id)
        if isinstance(leagueV3, NoSuchLeague):
            if force_local:
                return leagueV3
            print("updating fixtures...")
            self.fixtures.update()
            leagueV3 = find_league_in_fixtures(self.fixtures.data, league, league_id)
            if isinstance(leagueV3, NoSuchLeague):
                return leagueV3
        return find_event_in_league(leagueV3, league, home, away)

    def get_odds(self, event: EventInfo) -> OddsEventV3 | NoResult:
        self.odds.update()
        self.save()
        return filter_odds(self.odds.data, event["eventId"])
