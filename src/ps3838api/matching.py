from typing import Literal, Sequence, TypedDict

from rapidfuzz import fuzz

from ps3838api.models.fixtures import FixturesLeagueV3, FixturesResponse, FixtureV3, ResultingUnit
from ps3838api.utils.ops import normalize_to_set


class LeagueLike(TypedDict):
    name: str


def find_league_by_name[L: LeagueLike](league: str, leagues: Sequence[L]) -> L:
    normalized = normalize_to_set(league)
    for leagueV3 in leagues:
        if normalize_to_set(leagueV3["name"]) == normalized:
            return leagueV3
    raise ValueError("No such league")


def find_event_in_league(
    leagueV3: FixturesLeagueV3,
    home: str,
    away: str,
    resulting_unit: ResultingUnit = "Regular",
    live_status: Literal["PREMATCH", "LIVE"] | None = None,
) -> FixtureV3:
    """
    Scan `leagueV3["events"]` for the best fuzzy match to `home` and `away`.

    Pinnacle exposes separate prematch and live events, so `live_status`
    controls which kind of event is searched.

    `resulting_unit` controls which event type is searched, for example
    `Regular`, `Corners`, or `Bookings`.

    Returns the matching `FixtureV3` with the highest sum of match scores, as
    long as that sum is at least 75. Raises `ValueError` if no such event is
    found.
    """
    best_event = None
    best_sum_score = 0
    for event in leagueV3["events"]:
        if event["resultingUnit"] != resulting_unit:
            continue
        match (live_status, "parentId" in event):
            case None, _:
                pass
            case "PREMATCH", False:
                pass
            case "LIVE", True:
                pass
            case _:
                continue

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
        raise ValueError("No such event")
    return best_event


def magic_find_event(
    live_status: Literal["PREMATCH", "LIVE"],
    league: str,
    home: str,
    away: str,
    all_fixtures: FixturesResponse,
    *,
    resulting_unit: ResultingUnit = "Regular",
) -> FixtureV3:
    """
    Find a league in `all_fixtures` by normalized name and then locate the best
    matching event inside that league.

    Pinnacle exposes separate prematch and live events, so `live_status` is
    required and must be chosen explicitly.

    Use `resulting_unit` for `Regular`, `Corners`, `Bookings`, and other
    resulting units returned by the API.

    Raises `ValueError` if the league or event cannot be found.
    """

    leagueV3 = find_league_by_name(league, all_fixtures["league"])
    return find_event_in_league(leagueV3, home, away, resulting_unit, live_status)
