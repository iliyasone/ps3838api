"""
PACKAGE: ps3838api.api

This package exposes the :class:`Client` and the legacy convenience helpers that
use a shared default client (imported from :mod:`ps3838api.api.default_client`).
"""

from ps3838api.models.client import BalanceData, LeagueV3, PeriodData
from ps3838api.models.sports import BASEBALL_SPORT_ID, SOCCER_SPORT_ID

from .client import DEFAULT_API_BASE_URL, PinnacleClient
from .default_client import (
    export_my_bets,  # pyright: ignore[reportDeprecated]
    get_betting_status,  # pyright: ignore[reportDeprecated]
    get_client_balance,  # pyright: ignore[reportDeprecated]
    get_fixtures,  # pyright: ignore[reportDeprecated]
    get_leagues,  # pyright: ignore[reportDeprecated]
    get_line,  # pyright: ignore[reportDeprecated]
    get_odds,  # pyright: ignore[reportDeprecated]
    get_periods,  # pyright: ignore[reportDeprecated]
    get_special_fixtures,  # pyright: ignore[reportDeprecated]
    get_sports,  # pyright: ignore[reportDeprecated]
    place_straigh_bet,  # pyright: ignore[reportDeprecated]
)

__all__ = [
    "PinnacleClient",
    "DEFAULT_API_BASE_URL",  # legacy
    "SOCCER_SPORT_ID",  # legacy
    "BASEBALL_SPORT_ID",  # legacy
    "get_client_balance",
    "get_periods",
    "get_sports",
    "get_leagues",
    "get_fixtures",
    "get_odds",
    "get_special_fixtures",
    "get_line",
    "place_straigh_bet",
    "get_betting_status",
    "BalanceData",  # legacy, was in ps3838api.api
    "PeriodData",  # was in ps3838api.api
    "LeagueV3",  # was in ps3838api.api
    "export_my_bets",
]
