# type: ignore[RereportDeprecated]
"""
PACKAGE: ps3838api.api

This package exposes the :class:`Client` and the legacy convenience helpers that
use a shared default client (imported from :mod:`ps3838api.api.default_client`).
"""


from ps3838api.models.sports import BASEBALL_SPORT_ID, SOCCER_SPORT_ID
from ps3838api.models.client import BalanceData, PeriodData, LeagueV3

from .client import PinnacleClient, DEFAULT_API_BASE_URL
from .default_client import (
    export_my_bets,
    get_betting_status,
    get_bets,
    get_client_balance,
    get_fixtures,
    get_line,
    get_leagues,
    get_odds,
    get_periods,
    get_special_fixtures,
    get_sports,
    place_straigh_bet,
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
    "get_bets",
    "get_betting_status",
    "BalanceData",  # legacy, was in ps3838api.api
    "PeriodData",  # was in ps3838api.api
    "LeagueV3",  # was in ps3838api.api
    "export_my_bets",
]
