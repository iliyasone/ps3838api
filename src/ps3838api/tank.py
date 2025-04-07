from dataclasses import dataclass, field
import json
from pathlib import Path
from time import time
from typing import Final, TypedDict

from ps3838api import ROOT_DIR
import ps3838api.api as ps

from ps3838api.models.fixtures import FixtureV3, FixturesLeagueV3, FixturesResponse
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
    WrongLeague,
)

from rapidfuzz import fuzz


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
    """
    Merge a snapshot OddsResponse (old) with a delta OddsResponse (new).
    - Leagues are matched by league["id"].
    - Events are matched by event["id"].
    - Periods are matched by period["number"].
    - Any period present in 'new' entirely replaces the same period number in 'old'.
    - Periods not present in 'new' remain as they were in 'old'.

    Returns a merged OddsResponse that includes updated odds and periods, retaining
    old entries when no changes were reported in the delta.
    """
    # Index the old leagues by their IDs
    league_index: dict[int, OddsLeagueV3] = {
        league["id"]: league for league in old.get("leagues", [])
    }

    # Loop through the new leagues
    for new_league in new.get("leagues", []):
        lid = new_league["id"]

        # If it's an entirely new league, just store it
        if lid not in league_index:
            league_index[lid] = new_league
            continue

        # Otherwise merge it with the existing league
        old_league = league_index[lid]
        old_event_index = {event["id"]: event for event in old_league.get("events", [])}

        # Loop through the new events
        for new_event in new_league.get("events", []):
            eid = new_event["id"]

            # If it's an entirely new event, just store it
            if eid not in old_event_index:
                old_event_index[eid] = new_event
                continue

            # Otherwise, merge with the existing event
            old_event = old_event_index[eid]

            # Periods: build an index by 'number' from the old event
            old_period_index = {
                p["number"]: p for p in old_event.get("periods", []) if "number" in p
            }

            # Take all the new event's periods and override or insert them by 'number'
            for new_period in new_event.get("periods", []):
                if "number" not in new_period:
                    continue
                old_period_index[new_period["number"]] = new_period

            # Merge top-level fields: new event fields override old ones
            merged_event = old_event.copy()
            merged_event.update(new_event)

            # Rebuild the merged_event's periods from the updated dictionary
            merged_event["periods"] = list(old_period_index.values())

            # Store back in the event index
            old_event_index[eid] = merged_event

        # Rebuild league's events list from the merged event index
        old_league["events"] = list(old_event_index.values())

    return {
        "sportId": new.get("sportId", old["sportId"]),
        # Always take the latest `last` timestamp from the new (delta) response
        "last": new["last"],
        # Rebuild leagues list
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


with open(ROOT_DIR / "out/matched_leagues.json") as file:
    MATCHED_LEAGUES: Final[list[MatchedLeague]] = json.load(file)

with open(ROOT_DIR / "out/ps3838_leagues.json") as file:
    ALL_LEAGUES: Final[list[ps.LeagueV3]] = json.load(file)


def match_league(
    *,
    league_betsapi: str,
    leagues_mapping: list[MatchedLeague] = MATCHED_LEAGUES,
) -> MatchedLeague | NoSuchLeagueMatching | WrongLeague:
    for league in leagues_mapping:
        if league["betsapi_league"] == league_betsapi:
            if league["ps3838_id"]:
                return league
            else:
                return NoSuchLeagueMatching(league_betsapi)
    return WrongLeague(league_betsapi)


def find_league_by_name(
    league: str, leagues: list[ps.LeagueV3] = ALL_LEAGUES
) -> ps.LeagueV3 | NoSuchLeague:
    normalized = normalize_to_set(league)
    for leagueV3 in leagues:
        if normalize_to_set(leagueV3["name"]) == normalized:
            return leagueV3
    return NoSuchLeagueMatching(league)


def find_league_in_fixtures(
    fixtures: FixturesResponse, league: str, league_id: int
) -> FixturesLeagueV3 | NoSuchLeagueFixtures:
    for leagueV3 in fixtures["league"]:
        if leagueV3["id"] == league_id:
            return leagueV3
    else:
        return NoSuchLeagueFixtures(league)


def magic_find_event(
    fixtures: FixturesResponse, league: str, home: str, away: str
) -> EventInfo | Failure:
    """
    1. Tries to find league by normalizng names;
    2. If don't, search for a league matching
    """

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

    return find_event_in_league(leagueV3, league, home, away)


def find_event_in_league(
    league_data: FixturesLeagueV3, league: str, home: str, away: str
) -> EventInfo | NoSuchEvent:
    """
    Scans `league_data["events"]` for the best fuzzy match to `home` and `away`.
    Returns the matching event with the highest sum of match scores, as long as
    that sum >= 75 (which is 37.5% of the max possible 200).
    Otherwise, returns NoSuchEvent.
    """
    best_event = None
    best_sum_score = 0
    for event in league_data["events"]:
        # Compare the user-provided home and away vs. the fixture's home and away.
        # Using token_set_ratio (see below for comparison vs token_sort_ratio).
        score_home = fuzz.token_set_ratio(home, event.get("home", ""))
        score_away = fuzz.token_set_ratio(away, event.get("away", ""))
        total_score = score_home + score_away
        if total_score > best_sum_score:
            best_sum_score = total_score
            best_event = event
    # If the best event's combined fuzzy match is < 37.5% of the total possible 200,
    # treat it as no match:
    if best_event is None or best_sum_score < 75:
        return NoSuchEvent(league, home, away)
    return {"eventId": best_event["id"], "leagueId": league_data["id"]}


def find_event_by_id(fixtures: FixturesResponse, event: EventInfo) -> FixtureV3 | None:
    for leagueV3 in fixtures["league"]:
        if leagueV3["id"] == event["leagueId"]:
            for fixtureV3 in leagueV3["events"]:
                if fixtureV3["id"] == event["eventId"]:
                    return fixtureV3
    return None


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
