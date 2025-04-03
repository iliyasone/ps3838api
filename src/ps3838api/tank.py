from dataclasses import dataclass, field
import json
from pathlib import Path
from typing import Final, TypedDict

from ps3838api import ROOT_DIR
import ps3838api.api as ps

from ps3838api.models.fixtures import FixturesLeagueV3, FixturesResponse
from ps3838api.models.odds import OddsEventV3, OddsLeagueV3, OddsResponse
from ps3838api.models.event import (
    Failure,
    MatchedLeague,
    NoResult,
    NoSuchLeague,
    NoSuchEvent,
    NoSuchLeagueFixtures,
    NoSuchLeagueMatching,
    NoSuchOddsAvailable,
)


def merge_fixtures(old: FixturesResponse, new: FixturesResponse) -> FixturesResponse:
    league_index: dict[int, FixturesLeagueV3] = {
        league["id"]: league for league in old.get("league", [])
    }

    for new_league in new.get("league", []):
        lid = new_league["id"]
        if lid in league_index:
            old_events = {e["id"]: e for e in league_index[lid]["events"]}
            for event in new_league["events"]:
                old_events[event["id"]] = event  # override or insert
            league_index[lid]["events"] = list(old_events.values())
        else:
            league_index[lid] = new_league  # new league entirely
    return {
        "sportId": new.get("sportId", old["sportId"]),
        "last": new["last"],
        "league": list(league_index.values()),
    }


def merge_odds_response(old: OddsResponse, new: OddsResponse) -> OddsResponse:
    league_index: dict[int, OddsLeagueV3] = {
        league["id"]: league for league in old.get("leagues", [])
    }

    for new_league in new.get("leagues", []):
        lid = new_league["id"]
        if lid in league_index:
            old_event_index = {
                event["id"]: event for event in league_index[lid]["events"]
            }

            for new_event in new_league["events"]:
                eid = new_event["id"]
                old_event_index[eid] = new_event  # override or insert

            league_index[lid]["events"] = list(old_event_index.values())
        else:
            league_index[lid] = new_league  # entirely new league

    return {
        "sportId": new.get("sportId", old["sportId"]),
        "last": new["last"],  # always take latest timestamp
        "leagues": list(league_index.values()),
    }


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


class OddsTank:
    def __init__(self, file_path: str | Path = ROOT_DIR / "temp/odds.json") -> None:
        self.file_path = file_path
        try:
            with open(file_path) as file:
                self.data: OddsResponse = json.load(file)
        except FileNotFoundError:
            self.data: OddsResponse = ps.get_odds(ps.SOCCER_SPORT_ID)

    def update(self):
        delta = ps.get_odds(ps.SOCCER_SPORT_ID, since=self.data["last"])
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

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):  # type: ignore
        self.save()

    def save(self):
        self.fixtures.save()
        self.odds.save()

    def get_league_id_and_event_id(
        self, league: str, home: str, away: str
    ) -> EventInfo | Failure:
        match _find_event_bets_ps3838_id(self.fixtures.data, league, home, away):
            case NoSuchLeague() as f:
                return f
            case NoSuchEvent():
                print("updating fixtures...")
                self.fixtures.update()
                return _find_event_bets_ps3838_id(
                    self.fixtures.data, league, home, away
                )
            case event:
                return event

    def get_odds(self, event: EventInfo) -> OddsEventV3 | NoResult:
        self.odds.update()
        self.save()
        return filter_odds(self.odds.data, event["eventId"])


with open(ROOT_DIR / "out/matched_leagues.json") as file:
    MATCHED_LEAGUES: Final[list[MatchedLeague]] = json.load(file)

with open(ROOT_DIR / "out/ps3838_leagues.json") as file:
    ALL_LEAGUES: Final[list[ps.LeagueV3]] = json.load(file)


def match_league(
    *,
    league_betsapi: str,
    leagues_mapping: list[MatchedLeague] = MATCHED_LEAGUES,
) -> MatchedLeague | NoSuchLeagueMatching:
    for league in leagues_mapping:
        if league["betsapi_league"] == league_betsapi:
            if league["ps3838_id"]:
                return league
            break

    return NoSuchLeagueMatching(league_betsapi)


def find_league_by_name(
    league: str, leagues: list[ps.LeagueV3] = ALL_LEAGUES
) -> ps.LeagueV3 | NoSuchLeague:
    normalized = normalize_to_set(league)
    for leagueV3 in leagues:
        if normalize_to_set(leagueV3["name"]) == normalized:
            return leagueV3
    return NoSuchLeagueMatching(league)


def _find_event_bets_ps3838_id(
    fixtures: FixturesResponse, league: str, home: str, away: str
) -> EventInfo | Failure:
    """returns ps3838 event id like"""

    leagueV3 = find_league_by_name(league)
    if isinstance(leagueV3, NoSuchLeague):
        match match_league(league_betsapi=league):
            case {"ps3838_id": int()} as value:
                league_id: int = value["ps3838_id"]  # type: ignore
            case _:
                return NoSuchLeagueMatching(league)
    else:
        league_id = leagueV3["id"]

    for leagueV3 in fixtures["league"]:
        if leagueV3["id"] == league_id:
            break
    else:
        return NoSuchLeagueFixtures(league)

    for event in leagueV3["events"]:
        if normalize_to_set(event.get("home", "")) != normalize_to_set(home):
            continue
        if normalize_to_set(event.get("away", "")) != normalize_to_set(away):
            continue
        return {"eventId": event["id"], "leagueId": league_id}

    return NoSuchEvent(league, home, away)


def filter_odds(
    odds: OddsResponse, event_id: int, league_id: int | None = None
) -> OddsEventV3 | NoSuchOddsAvailable:
    """passing `league_id` makes search in json faster"""
    for league in odds["leagues"]:
        if league_id and league_id != league["id"]:
            continue
        for fixture in league["events"]:
            if fixture["id"] == event_id:
                return fixture
    return NoSuchOddsAvailable(event_id)


def normalize_to_set(name: str) -> set[str]:
    return set(
        name.replace(" II", " 2").replace(" I", "").lower().replace("-", " ").split()
    )
