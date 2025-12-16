from typing import Literal, NotRequired, TypedDict


class BalanceData(TypedDict):
    availableBalance: float
    outstandingTransactions: float
    givenCredit: NotRequired[float]
    currency: str


class PeriodData(TypedDict, total=False):
    number: NotRequired[int]
    description: NotRequired[str]
    shortDescription: NotRequired[str]
    spreadDescription: NotRequired[str]
    moneylineDescription: NotRequired[str]
    totalDescription: NotRequired[str]
    team1TotalDescription: NotRequired[str]
    team2TotalDescription: NotRequired[str]
    spreadShortDescription: NotRequired[str]
    moneylineShortDescription: NotRequired[str]
    totalShortDescription: NotRequired[str]
    team1TotalShortDescription: NotRequired[str]
    team2TotalShortDescription: NotRequired[str]


class LeagueV3(TypedDict):
    id: int
    name: str
    homeTeamType: NotRequired[str]
    hasOfferings: NotRequired[bool]
    container: NotRequired[str]
    allowRoundRobins: NotRequired[bool]
    leagueSpecialsCount: NotRequired[int]
    eventSpecialsCount: NotRequired[int]
    eventCount: NotRequired[int]


class BettingStatusResponse(TypedDict):
    status: Literal["ALL_BETTING_ENABLED", "ALL_LIVE_BETTING_CLOSED", "ALL_BETTING_CLOSED"]


__all__ = [
    "BalanceData",
    "PeriodData",
    "LeagueV3",
    "BettingStatusResponse",
]
