from typing import TYPE_CHECKING, Any, cast

from ps3838api.models.bets import OddsFormat
from ps3838api.models.odds import OddsResponseV4

if TYPE_CHECKING:
    # to avoid ciruclar imports
    from ps3838api.api.client import PinnacleClient


class V4PinnacleClient:
    """Subclient for V4 API endpoints.

    V4 endpoints provide enhanced responses, particularly for team totals
    which return arrays of alternative lines instead of single objects.
    """

    def __init__(self, client: "PinnacleClient"):
        self._client = client

    def get_odds(
        self,
        sport_id: int | None = None,
        league_ids: list[int] | None = None,
        odds_format: OddsFormat = "DECIMAL",
        since: int | None = None,
        is_live: bool | None = None,
        event_ids: list[int] | None = None,
        to_currency_code: str | None = None,
    ) -> OddsResponseV4:
        """Get straight odds for non-settled events using V4 endpoint.

        V4 returns enhanced team total data with arrays of alternative lines.

        Args:
            sport_id: Sport ID. Uses client's default_sport if not provided.
            league_ids: List of league IDs to filter.
            odds_format: Format for odds (DECIMAL, AMERICAN, etc.).
            since: Used for incremental updates. Use 'last' from previous response.
            is_live: True for live events only, False for prematch only.
            event_ids: List of event IDs to filter.
            to_currency_code: Convert limits to specified currency.

        Returns:
            OddsResponseV4 containing odds data with V4 enhanced structure.
        """
        endpoint = "/v4/odds"

        resolved_sport_id = sport_id if sport_id is not None else self._client.default_sport

        params: dict[str, Any] = {
            "sportId": resolved_sport_id,
            "oddsFormat": odds_format,
        }
        if league_ids:
            params["leagueIds"] = ",".join(map(str, league_ids))
        if since is not None:
            params["since"] = since
        if is_live is not None:
            params["isLive"] = int(is_live)
        if event_ids:
            params["eventIds"] = ",".join(map(str, event_ids))
        if to_currency_code is not None:
            params["toCurrencyCode"] = to_currency_code

        return cast(OddsResponseV4, self._client._get(endpoint, params))  # pyright: ignore[reportPrivateUsage]

    def get_parlay_odds(
        self,
        sport_id: int | None = None,
        league_ids: list[int] | None = None,
        odds_format: OddsFormat = "DECIMAL",
        since: int | None = None,
        is_live: bool | None = None,
        event_ids: list[int] | None = None,
    ) -> OddsResponseV4:
        """Get parlay odds for non-settled events using V4 endpoint.

        Args:
            sport_id: Sport ID. Uses client's default_sport if not provided.
            league_ids: List of league IDs to filter.
            odds_format: Format for odds (DECIMAL, AMERICAN, etc.).
            since: Used for incremental updates. Use 'last' from previous response.
            is_live: True for live events only, False for prematch only.
            event_ids: List of event IDs to filter.

        Returns:
            OddsResponseV4 containing parlay odds data.
        """
        endpoint = "/v4/odds/parlay"

        resolved_sport_id = sport_id if sport_id is not None else self._client.default_sport

        params: dict[str, Any] = {
            "sportId": resolved_sport_id,
            "oddsFormat": odds_format,
        }
        if league_ids:
            params["leagueIds"] = ",".join(map(str, league_ids))
        if since is not None:
            params["since"] = since
        if is_live is not None:
            params["isLive"] = int(is_live)
        if event_ids:
            params["eventIds"] = ",".join(map(str, event_ids))

        return cast(OddsResponseV4, self._client._get(endpoint, params))  # pyright: ignore[reportPrivateUsage]
