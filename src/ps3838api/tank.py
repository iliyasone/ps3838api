from dataclasses import dataclass, field
import json
from pathlib import Path
from typing import Final

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
        try:
            with open(file_path) as file:
                self.data: FixturesResponse = json.load(file)
        except FileNotFoundError:
            self.data: FixturesResponse = ps.get_fixtures(ps.SOCCER_SPORT_ID)


    def update(self):
        delta = ps.get_fixtures(ps.SOCCER_SPORT_ID, since=self.data["last"])
        self.data = merge_fixtures(self.data, delta)

    def save(self):
        with open(ROOT_DIR / "temp/fixtures.json", "w") as file:
            json.dump(self.data, file, indent=4)


class OddsTank:
    def __init__(self) -> None:
        self.data: OddsResponse = ps.get_odds(ps.SOCCER_SPORT_ID)

    def update(self):
        delta = ps.get_odds(ps.SOCCER_SPORT_ID, since=self.data["last"])
        self.data = merge_odds_response(self.data, delta)

    def save(self):
        # TODO: Impellement
        return None


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

    def _get_ps3838_event_id(self, league: str, home: str, away: str) -> int | Failure:
        match find_event_bets_ps3838_id(self.fixtures.data, league, home, away):
            case int() as event:
                print("event founded")
                return event
            case NoSuchLeague() as f:
                return f
            case NoSuchEvent():
                print("updating fixtures...")
                self.fixtures.update()
                return find_event_bets_ps3838_id(self.fixtures.data, league, home, away)

    def get_odds(self, league: str, home: str, away: str) -> OddsEventV3 | NoResult:
        match self._get_ps3838_event_id(league, home, away):
            case int() as event_id:
                event_id = event_id
            case f:
                return f
        print("updating odds")
        self.odds.update()
        return filter_odds(self.odds.data, event_id)


with open(ROOT_DIR / "out/matched_leagues.json") as file:
    MATCHED_LEAGUES: Final[list[MatchedLeague]] = json.load(file)


def match_league(
    leagues_mapping: list[MatchedLeague] = MATCHED_LEAGUES, *, league_betsapi: str
) -> MatchedLeague | NoSuchLeague:
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


def find_event_bets_ps3838_id(
    fixtures: FixturesResponse, league_betsapi: str, home: str, away: str
) -> int | Failure:
    """returns ps3838 event id like"""
    match match_league(league_betsapi=league_betsapi):
        case {"ps3838_id": int()} as value:
            league_id: int = value["ps3838_id"]  # type: ignore
        case _:
            return NoSuchLeagueMatching(league_betsapi)

    for league in fixtures["league"]:
        if league["id"] == league_id:
            break
    else:
        return NoSuchLeagueFixtures(league_betsapi)

    for event in league["events"]:
        if normalize_to_set(event.get("home", "")) != normalize_to_set(home):
            continue
        if normalize_to_set(event.get("away", "")) != normalize_to_set(away):
            continue
        return event["id"]

    return NoSuchEvent(league_betsapi, home, away)


def filter_odds(
    odds: OddsResponse, event_id: int, league_id: int | None = None
) -> OddsEventV3 | NoSuchOddsAvailable:
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
