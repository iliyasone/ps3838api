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
from ps3838api.matching import find_event_in_league, match_league, MATCHED_LEAGUES
from ps3838api.models.fixtures import FixturesResponse
from ps3838api.models.odds import OddsEventV3, OddsResponse
from ps3838api.models.event import (
    Failure,
    NoResult,
    NoSuchLeague,
)

SNAPSHOT_INTERVAL = 60  # 1 minute
DELTA_INTERVAL = 5  # 5 seconds

RESPONSES_DIR = ROOT_DIR / "temp" / "responses"
RESPONSES_DIR.mkdir(parents=True, exist_ok=True)

TOP_LEAGUES = [league["ps3838_id"] for league in MATCHED_LEAGUES if league["ps3838_id"]]


class FixtureTank:
    """
    Stores ps3838 fixtures in a local JSON file, updating either via
    a full snapshot or a delta call, depending on time elapsed since last call.
    """

    def __init__(
        self,
        league_ids: list[int] | None = TOP_LEAGUES,
        file_path: str | Path = ROOT_DIR / "temp" / "fixtures.json",
    ) -> None:
        self.file_path = Path(file_path)
        self.last_call_time = 0.0

        # Load local cache or pull a snapshot from the API if file not found
        try:
            with open(self.file_path) as file:
                self.data: FixturesResponse = json.load(file)
        except FileNotFoundError:
            self.data: FixturesResponse = ps.get_fixtures(league_ids=league_ids)
            self.last_call_time = time()
            self._save_response(self.data, snapshot=True)

    def _save_response(self, response_data: FixturesResponse, snapshot: bool) -> None:
        """
        Save fixture response to the temp/responses folder for future testing.
        """
        kind = "snapshot" if snapshot else "delta"
        timestamp = int(time())
        filename = RESPONSES_DIR / f"fixtures_{kind}_{timestamp}.json"
        with open(filename, "w") as f:
            json.dump(response_data, f, indent=4)

    def update(self):
        """
        Decide whether to make a snapshot call, delta call, or do nothing,
        based on how much time has elapsed since the last call.
        """
        now = time()
        elapsed = now - self.last_call_time

        if elapsed < DELTA_INTERVAL:
            # Less than 5 seconds → do nothing
            return

        if elapsed >= SNAPSHOT_INTERVAL:
            # More than 1 minute → snapshot call
            response = ps.get_fixtures(ps.SOCCER_SPORT_ID)
            self.data = response
            self._save_response(response, snapshot=True)

        else:
            # [5, 60) → delta call
            delta = ps.get_fixtures(ps.SOCCER_SPORT_ID, since=self.data["last"])
            self.data = merge_fixtures(self.data, delta)
            self._save_response(delta, snapshot=False)

        self.last_call_time = now

    def save(self):
        """
        Save the current fixture data to fixtures.json (the local cache).
        """
        with open(self.file_path, "w") as file:
            json.dump(self.data, file, indent=4)


class OddsTank:
    """
    Stores ps3838 odds in a local JSON file, updating either via
    a full snapshot or a delta call, depending on time elapsed since last call.
    """

    def __init__(
        self,
        league_ids: list[int] | None = TOP_LEAGUES,
        file_path: str | Path = ROOT_DIR / "temp" / "odds.json",
    ) -> None:
        self.file_path = Path(file_path)
        self.last_call_time = 0.0
        self.is_live: bool | None = None

        # Load local cache or pull a snapshot from the API if file not found
        try:
            with open(file_path) as file:
                self.data: OddsResponse = json.load(file)
        except FileNotFoundError:
            self.data: OddsResponse = ps.get_odds(league_ids=league_ids)
            self.last_call_time = time()
            self._save_response(self.data, snapshot=True)

    def _save_response(self, response_data: OddsResponse, snapshot: bool) -> None:
        """
        Save odds response to the temp/responses folder for future testing.
        """
        kind = "snapshot" if snapshot else "delta"
        timestamp = int(time())
        filename = RESPONSES_DIR / f"odds_{kind}_{timestamp}.json"
        with open(filename, "w") as f:
            json.dump(response_data, f, indent=4)

    def update(self):
        """
        Decide whether to make a snapshot call, delta call, or do nothing,
        based on how much time has elapsed since the last call.
        """
        now = time()
        elapsed = now - self.last_call_time

        if elapsed < DELTA_INTERVAL:
            # Less than 5 seconds → do nothing
            return

        if elapsed >= SNAPSHOT_INTERVAL:
            # More than 1 minute → snapshot call
            response = ps.get_odds(ps.SOCCER_SPORT_ID, is_live=self.is_live)
            self.data = response
            self._save_response(response, snapshot=True)

        else:
            # [5, 60) → delta call
            delta = ps.get_odds(
                ps.SOCCER_SPORT_ID, is_live=self.is_live, since=self.data["last"]
            )
            self.data = merge_odds_response(self.data, delta)
            self._save_response(delta, snapshot=False)

        self.last_call_time = now

    def save(self):
        """
        Save the current odds data to odds.json (the local cache).
        """
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

    def get_odds(
        self, event: EventInfo, force_local: bool = False
    ) -> OddsEventV3 | NoResult:
        """
        Update the odds tank and then look up the odds for the given event.
        """
        if not force_local:
            self.odds.update()
            self.save()
        return filter_odds(self.odds.data, event["eventId"])
