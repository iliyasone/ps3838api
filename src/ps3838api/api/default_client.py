"""
Legacy helper functions that use a shared default :class:`Client`.
"""

import sys
import warnings
from datetime import datetime
from typing import Any, Literal

if sys.version_info >= (3, 13):
    from warnings import deprecated
else:

    def deprecated(reason: str):  # type: ignore
        def decorator(func):  # type: ignore
            def wrapper(*args, **kwargs):  # type: ignore
                warnings.warn(
                    f"{func.__name__} is deprecated: {reason}",  # type: ignore
                    DeprecationWarning,
                    stacklevel=2,
                )
                return func(*args, **kwargs)  # type: ignore

            wrapper.__name__ = func.__name__  # type: ignore
            wrapper.__doc__ = func.__doc__  # type: ignore
            wrapper.__dict__.update(func.__dict__)  # type: ignore
            return wrapper  # type: ignore

        return decorator  # type: ignore


from ps3838api.models.bets import BetType, FillType, OddsFormat, PlaceStraightBetResponse, Side, Team
from ps3838api.models.client import BalanceData, BettingStatusResponse, LeagueV3, PeriodData
from ps3838api.models.fixtures import FixturesResponse
from ps3838api.models.lines import LineResponse
from ps3838api.models.odds import OddsResponse
from ps3838api.models.sports import SOCCER_SPORT_ID

from .client import PinnacleClient

_default_client: PinnacleClient | None = None


def _get_default_client() -> PinnacleClient:
    global _default_client  # noqa: PLW0603
    if _default_client is None:
        _default_client = PinnacleClient()
    return _default_client


@deprecated("Use `ps3838api.client.PinnacleClient` base methods")
def get_client_balance() -> BalanceData:
    return _get_default_client().get_client_balance()


@deprecated("Use `ps3838api.client.PinnacleClient` base methods")
def get_periods(sport_id: int | None = None) -> list[PeriodData]:
    return _get_default_client().get_periods(sport_id=sport_id)


@deprecated("Use `ps3838api.models.sports` sports constant")
def get_sports() -> Any:
    return _get_default_client().get_sports()


@deprecated("Use `ps3838api.client.PinnacleClient` base methods")
def get_leagues(sport_id: int | None = None) -> list[LeagueV3]:
    return _get_default_client().get_leagues(sport_id=sport_id)


@deprecated("Use `ps3838api.client.PinnacleClient` base methods")
def get_fixtures(
    sport_id: int | None = None,
    league_ids: list[int] | None = None,
    is_live: bool | None = None,
    since: int | None = None,
    event_ids: list[int] | None = None,
    settled: bool = False,
) -> FixturesResponse:
    return _get_default_client().get_fixtures(
        sport_id=sport_id,
        league_ids=league_ids,
        is_live=is_live,
        since=since,
        event_ids=event_ids,
        settled=settled,
    )


@deprecated("Use `ps3838api.client.PinnacleClient` base methods")
def get_odds(
    sport_id: int | None = None,
    is_special: bool = False,
    league_ids: list[int] | None = None,
    odds_format: OddsFormat = "DECIMAL",
    since: int | None = None,
    is_live: bool | None = None,
    event_ids: list[int] | None = None,
) -> OddsResponse:
    return _get_default_client().get_odds(
        sport_id=sport_id,
        is_special=is_special,
        league_ids=league_ids,
        odds_format=odds_format,
        since=since,
        is_live=is_live,
        event_ids=event_ids,
    )


@deprecated("Use `ps3838api.client.PinnacleClient` base methods")
def get_special_fixtures(
    sport_id: int | None = None,
    league_ids: list[int] | None = None,
    event_id: int | None = None,
) -> Any:
    return _get_default_client().get_special_fixtures(
        sport_id=sport_id, league_ids=league_ids, event_id=event_id
    )


@deprecated("Use `ps3838api.client.PinnacleClient` base methods")
def get_line(
    league_id: int,
    event_id: int,
    period_number: int,
    bet_type: Literal["SPREAD", "MONEYLINE", "TOTAL_POINTS", "TEAM_TOTAL_POINTS"],
    handicap: float,
    team: Literal["Team1", "Team2", "Draw"] | None = None,
    side: Literal["OVER", "UNDER"] | None = None,
    sport_id: int | None = None,
    odds_format: str = "Decimal",
) -> LineResponse:
    return _get_default_client().get_line(
        league_id=league_id,
        event_id=event_id,
        period_number=period_number,
        bet_type=bet_type,
        handicap=handicap,
        team=team,
        side=side,
        sport_id=sport_id,
        odds_format=odds_format,
    )


@deprecated("Use `ps3838api.client.PinnacleClient` base methods")
def place_straigh_bet(
    *,
    stake: float,
    event_id: int,
    bet_type: BetType,
    line_id: int | None,
    period_number: int = 0,
    sport_id: int = SOCCER_SPORT_ID,
    alt_line_id: int | None = None,
    unique_request_id: str | None = None,
    odds_format: OddsFormat = "DECIMAL",
    fill_type: FillType = "NORMAL",
    accept_better_line: bool = True,
    win_risk_stake: Literal["WIN", "RISK"] = "RISK",
    pitcher1_must_start: bool = True,
    pitcher2_must_start: bool = True,
    team: Team | None = None,
    side: Side | None = None,
    handicap: float | None = None,
) -> PlaceStraightBetResponse:
    return _get_default_client().place_straight_bet(
        stake=stake,
        event_id=event_id,
        bet_type=bet_type,
        line_id=line_id,
        period_number=period_number,
        sport_id=sport_id,
        alt_line_id=alt_line_id,
        unique_request_id=unique_request_id,
        odds_format=odds_format,
        fill_type=fill_type,
        accept_better_line=accept_better_line,
        win_risk_stake=win_risk_stake,
        pitcher1_must_start=pitcher1_must_start,
        pitcher2_must_start=pitcher2_must_start,
        team=team,
        side=side,
        handicap=handicap,
    )


@deprecated("Use `ps3838api.client.PinnacleClient` base methods")
def get_betting_status() -> BettingStatusResponse:
    return _get_default_client().get_betting_status()


def export_my_bets(
    *,
    from_datetime: datetime,
    to_datetime: datetime,
    d: int = -1,
    status: Literal["UNSETTLED", "SETTLED"] = "SETTLED",
    sd: bool = False,
    bet_type: str = "WAGER",
    product: str = "SB,PP,BG",
    locale: str = "en_US",
    timezone: str = "GMT-4",
) -> bytes:
    return _get_default_client().export_my_bets(
        from_datetime=from_datetime,
        to_datetime=to_datetime,
        d=d,
        status=status,
        sd=sd,
        bet_type=bet_type,
        product=product,
        locale=locale,
        timezone=timezone,
    )


__all__ = [
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
    "export_my_bets",
]
