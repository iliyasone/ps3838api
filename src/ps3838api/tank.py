"""Centralised fixtures/odds caching that respects PS3838 rate‑limits.

The core idea is identical for both resources:
• ≥ 60 s since previous call → **snapshot** (full refresh)
• 5–59 s                            → **delta** (incremental update, merged into cache)
• < 5 s                             → **use in‑memory cache**, no API hit

Odds were already following this contract.  Fixtures now do too.
Additionally, fixtures are **no longer persisted** as one huge
``fixtures.json`` file.  Every API response (snapshot *and* delta)
gets stored verbatim in *temp/responses/* for replay/debugging just
like odds.  If a full history is ever required you can reconstruct it
from those files.
"""

import json
import logging
import warnings
from pathlib import Path
from time import time

from ps3838api.api.client import PinnacleClient
from ps3838api.matching import MATCHED_LEAGUES
from ps3838api.models.fixtures import FixturesResponse
from ps3838api.utils.ops import merge_fixtures

warnings.warn(
    f"{__name__} is experimental, incomplete, and may change in future versions.",
    UserWarning,
)


SNAPSHOT_INTERVAL = 60
DELTA_INTERVAL = 5


TOP_LEAGUES = [league["ps3838_id"] for league in MATCHED_LEAGUES if league["ps3838_id"]]

logger = logging.getLogger(__name__)


class FixtureTank:
    """Lightweight cache for Pinnacle *fixtures*.

    * No big persisted file – only individual API responses are archived.
    * Shares the same timing policy as :class:`OddsTank`.
    """

    def __init__(
        self,
        client: PinnacleClient,
        league_ids: list[int] | None = None,
        response_dir: Path | str | None = None,  # Path("temp/responses")
    ) -> None:
        self.client = client
        self.response_dir = Path(response_dir) if response_dir else None
        # start with a fresh snapshot (fast + guarantees consistency)
        self.data: FixturesResponse = client.get_fixtures(league_ids=league_ids)
        self._last_call_time = time()
        self._save_response(self.data, snapshot=True)

    def _save_response(self, response_data: FixturesResponse, snapshot: bool) -> None:
        """
        Save fixture response to the temp/responses folder for future testing.
        """
        if not self.response_dir:
            return
        kind = "snapshot" if snapshot else "delta"
        self.response_dir.mkdir(parents=True, exist_ok=True)
        fn = self.response_dir / f"fixtures_{kind}_{int(time())}.json"
        with open(fn, "w") as f:
            json.dump(response_data, f, indent=4)

    def update(self) -> None:
        """Refresh internal cache if timing thresholds are met."""
        now = time()
        elapsed = now - self._last_call_time

        if elapsed < DELTA_INTERVAL:
            return  # 💡 Too soon – use cached data

        if elapsed >= SNAPSHOT_INTERVAL:
            # ── Full refresh ────────────────────────────────────────────
            resp = self.client.get_fixtures()
            self.data = resp
            self._save_response(resp, snapshot=True)
        else:
            # ── Incremental update ──────────────────────────────────────
            delta = self.client.get_fixtures(since=self.data["last"])
            self.data = merge_fixtures(self.data, delta)
            self._save_response(delta, snapshot=False)

        self._last_call_time = now
