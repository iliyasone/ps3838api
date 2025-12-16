import warnings

from ps3838api.models.event import NoSuchLeagueFixtures, NoSuchOddsAvailable
from ps3838api.models.fixtures import FixturesLeagueV3, FixturesResponse, FixtureV3
from ps3838api.models.odds import OddsEventV3, OddsLeagueV3, OddsResponse
from ps3838api.models.tank import EventInfo

warnings.warn(
    f"{__name__} is experimental, incomplete, and may change in future versions.",
    UserWarning,
)


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

    Based on "How to get odds changes?" from https://ps3838api.github.io/FAQs.html
    """
    # Index the old leagues by their IDs
    league_index: dict[int, OddsLeagueV3] = {league["id"]: league for league in old.get("leagues", [])}

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
            old_period_index = {p["number"]: p for p in old_event.get("periods", []) if "number" in p}

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


def merge_fixtures(old: FixturesResponse, new: FixturesResponse) -> FixturesResponse:
    league_index: dict[int, FixturesLeagueV3] = {league["id"]: league for league in old.get("league", [])}

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


def find_league_in_fixtures(
    fixtures: FixturesResponse, league: str, league_id: int
) -> FixturesLeagueV3 | NoSuchLeagueFixtures:
    for leagueV3 in fixtures["league"]:
        if leagueV3["id"] == league_id:
            return leagueV3
    else:
        return NoSuchLeagueFixtures(league)


def find_fixtureV3_in_league(leagueV3: FixturesLeagueV3, event_id: int) -> FixtureV3:
    for eventV3 in leagueV3["events"]:
        if eventV3["id"] == event_id:
            return eventV3
    raise ValueError("No such event")


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
    return set(name.replace(" II", " 2").replace(" I", "").lower().replace("-", " ").split())


def find_event_by_id(fixtures: FixturesResponse, event: EventInfo) -> FixtureV3 | None:
    for leagueV3 in fixtures["league"]:
        if leagueV3["id"] == event["leagueId"]:
            for fixtureV3 in leagueV3["events"]:
                if fixtureV3["id"] == event["eventId"]:
                    return fixtureV3
    return None
