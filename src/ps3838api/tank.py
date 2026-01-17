"""Centralised fixtures/odds caching that respects PS3838 rate‑limits.

The core idea is identical for both resources:
• ≥ 60 s since previous call → **snapshot** (full refresh)
• 5–59 s                            → **delta** (incremental update, merged into cache)
• < 5 s                             → **use in‑memory cache**, no API hit

Odds were already following this contract.  Fixtures now do too.
Additionally, fixtures are **no longer persisted** as one huge
``fixtures.json`` file.  Every API response (snapshot *and* delta)
gets stored verbatim in *temp/responses/* for replay/debugging just
like odds.  If a full history is ever required you can reconstruct it
from those files.
"""

from dataclasses import dataclass, field
import datetime
import json
from pathlib import Path
from time import time

import ps3838api.api as ps

from ps3838api.logic import (
    filter_odds,
    find_fixtureV3_in_league,
    find_league_in_fixtures,
    merge_fixtures,
    merge_odds_response,
)
from ps3838api.matching import find_event_in_league, match_league, MATCHED_LEAGUES
from ps3838api.models.event import (
    EventTooFarInFuture,
    Failure,
    NoSuchEvent,
    NoSuchLeague,
    NoSuchOddsAvailable,
)
from ps3838api.models.fixtures import FixturesResponse
from ps3838api.models.odds import OddsEventV3, OddsResponse
from ps3838api.models.tank import EventInfo

SNAPSHOT_INTERVAL = 60  # seconds
DELTA_INTERVAL = 5      # seconds

RESPONSES_DIR = Path("temp/responses")
RESPONSES_DIR.mkdir(parents=True, exist_ok=True)

TOP_LEAGUES = [league["ps3838_id"] for league in MATCHED_LEAGUES if league["ps3838_id"]]

# ──────────────────────────────────────────────────────────────────────────────
# Fixture Tank –  in‑memory, snapshot/delta, no huge fixtures.json
# ──────────────────────────────────────────────────────────────────────────────
class FixtureTank:
    """Lightweight cache for ps3838 *fixtures*.

    * No big persisted file – only individual API responses are archived.
    * Shares the same timing policy as :class:`OddsTank`.
    """

    def __init__(self, league_ids: list[int] | None = None) -> None:
        self._last_call_time: float = 0.0
        # start with a fresh snapshot (fast + guarantees consistency)
        self.data: FixturesResponse = ps.get_fixtures(league_ids=league_ids)
        self._last_call_time = time()
        self._save_response(self.data, snapshot=True)

    # ──────────────────────────────────────────────────────────────────────
    # Private helpers
    # ──────────────────────────────────────────────────────────────────────
    def _save_response(self, response_data: FixturesResponse, snapshot: bool) -> None:
        """
        Save fixture response to the temp/responses folder for future testing.
        """
        kind = "snapshot" if snapshot else "delta"
        fn = RESPONSES_DIR / f"fixtures_{kind}_{int(time())}.json"
        with open(fn, "w") as f:
            json.dump(response_data, f, indent=4)

    # ──────────────────────────────────────────────────────────────────────
    # Public API
    # ──────────────────────────────────────────────────────────────────────
    def update(self) -> None:
        """Refresh internal cache if timing thresholds are met."""
        now = time()
        elapsed = now - self._last_call_time

        if elapsed < DELTA_INTERVAL:
            return  # 💡 Too soon – use cached data

        if elapsed >= SNAPSHOT_INTERVAL:
            # ── Full refresh ────────────────────────────────────────────
            resp = ps.get_fixtures()
            self.data = resp
            self._save_response(resp, snapshot=True)
        else:
            # ── Incremental update ──────────────────────────────────────
            delta = ps.get_fixtures(since=self.data["last"])
            self.data = merge_fixtures(self.data, delta)
            self._save_response(delta, snapshot=False)

        self._last_call_time = now

    # Legacy no‑op so existing callers don’t blow up
    def save(self) -> None:  # noqa: D401 (imperative mood not needed)
        """(Deprecated) Previously wrote *fixtures.json*; now no‑op."""
        return

# ──────────────────────────────────────────────────────────────────────────────
# Odds Tank – unchanged logic (snapshot/delta/history archiving)
# ──────────────────────────────────────────────────────────────────────────────
class OddsTank:
    """Stores ps3838 odds locally, rate‑limited exactly like *FixtureTank*."""

    def __init__(
        self,
        league_ids: list[int] | None = None,
    ) -> None:
        self.is_live: bool | None = None

        self.data = ps.get_odds(league_ids=league_ids)
        self._last_call_time = time()
        self._save_response(self.data, snapshot=True)

    def _save_response(self, resp: OddsResponse, *, snapshot: bool) -> None:
        kind = "snapshot" if snapshot else "delta"
        fn = RESPONSES_DIR / f"odds_{kind}_{int(time())}.json"
        with open(fn, "w") as f:
            json.dump(resp, f, indent=4)

    def update(self) -> None:
        now = time()
        elapsed = now - self._last_call_time

        if elapsed < DELTA_INTERVAL:
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

        self._last_call_time = now

    # Legacy no‑op so existing callers don’t blow up
    def save(self) -> None:  # noqa: D401 (imperative mood not needed)
        """(Deprecated) Previously wrote *fixtures.json*; now no‑op."""
        return

# ──────────────────────────────────────────────────────────────────────────────
# High‑level convenience wrapper
# ──────────────────────────────────────────────────────────────────────────────
@dataclass
class EventMatcher:
    fixtures: FixtureTank = field(init=False)
    odds: OddsTank = field(init=False)
    league_ids: list[int] | None = None

    def __post_init__(self):
        self.fixtures = FixtureTank(league_ids=self.league_ids)
        self.odds = OddsTank(league_ids=self.league_ids)

    def save(self):
        self.fixtures.save()
        self.odds.save()

    # ──────────────────────────────────────────────────────────────────────
    # Lookup helpers
    # ──────────────────────────────────────────────────────────────────────
    def get_league_id_and_event_id(
        self, league: str, home: str, away: str, force_local: bool = False
    ) -> EventInfo | Failure:
        match match_league(league_betsapi=league):
            case NoSuchLeague() as f:
                return f
            case matched_league:
                league_id = matched_league["ps3838_id"]
                assert league_id is not None

        if force_local:
            print('WARNING: `force_local=True` may lead to silent incorrect matching')
        else:
            self.fixtures.update()
        leagueV3 = find_league_in_fixtures(self.fixtures.data, league, league_id)

        if isinstance(leagueV3, NoSuchLeague):
            return leagueV3

        match find_event_in_league(leagueV3, league, home, away):
            case NoSuchEvent() as f:
                return f
            case event:
                event = event
        fixture = find_fixtureV3_in_league(leagueV3, event['eventId'])

        if 'starts' in fixture:
            fixture_start = datetime.datetime.fromisoformat(fixture['starts'])
            now = datetime.datetime.now(datetime.timezone.utc)
            time_diff = fixture_start - now
            # Check if the event starts in 60 minutes or less, but not in the past
            if datetime.timedelta(0) <= time_diff <= datetime.timedelta(minutes=60):
                return event
        return EventTooFarInFuture(league, home, away)

    def get_odds(
        self, event: EventInfo, force_local: bool = False
    ) -> OddsEventV3 | NoSuchOddsAvailable:
        """
        Update the odds tank and then look up the odds for the given event.
        """
        if not force_local:
            self.odds.update()
            self.save()
        return filter_odds(self.odds.data, event["eventId"])
