from typing import Literal, NotRequired, TypedDict

type OddsFormat = Literal["AMERICAN", "DECIMAL", "HONGKONG", "INDONESIAN", "MALAY"]

type FillType = Literal["NORMAL", "FILLANDKILL", "FILLMAXLIMIT"]
"""
### NORMAL
bet will be placed on specified stake.  

### FILLANDKILL

If the stake is over the max limit, bet will be placed on max limit, 
otherwise it will be placed on specified stake.  

### FILLMAXLIMIT⚠️

bet will be places on max limit⚠️, stake amount will be ignored. 
Please note that maximum limits can change at any moment, which may result in 
risking more than anticipated. This option is replacement of isMaxStakeBet from 
v1/bets/place'
"""

type Team = Literal["TEAM1", "TEAM2", "DRAW"]
type Side = Literal["OVER", "UNDER"]

type BetList = Literal["SETTLED", "RUNNING", "ALL"]

type SortDir = Literal["ASC", "DESC"]

type BetStatus = Literal[
    "ACCEPTED",
    "CANCELLED",
    "LOSE",
    "PENDING_ACCEPTANCE",
    "REFUNDED",
    "NOT_ACCEPTED",
    "WON",
    "REJECTED",
]

type BetStatus2 = Literal[
    "ACCEPTED",
    "CANCELLED",
    "LOST",
    "PENDING_ACCEPTANCE",
    "REFUNDED",
    "NOT_ACCEPTED",
    "WON",
    "REJECTED",
    "HALF_WON_HALF_PUSHED",
    "HALF_LOST_HALF_PUSHED",
]

type BetType = Literal["MONEYLINE", "TEAM_TOTAL_POINTS", "SPREAD", "TOTAL_POINTS"]

type BetTypeFull = Literal[
    "MONEYLINE",
    "TEAM_TOTAL_POINTS",
    "SPREAD",
    "TOTAL_POINTS",
    "SPECIAL",
    "PARLAY",
    "TEASER",
    "MANUAL",
]


class PlaceStraightBetRequest(TypedDict):
    oddsFormat: OddsFormat
    uniqueRequestId: str
    acceptBetterLine: bool
    stake: float
    winRiskStake: Literal["WIN", "RISK"]
    lineId: int
    altLineId: NotRequired[int]
    pitcher1MustStart: bool
    pitcher2MustStart: bool
    fillType: Literal["NORMAL", "FILLANDKILL", "FILLMAXLIMIT"]
    sportId: int
    eventId: int
    periodNumber: int
    betType: BetTypeFull
    team: Literal["TEAM1", "TEAM2", "DRAW"]
    side: NotRequired[Literal["OVER", "UNDER"]]
    handicap: NotRequired[float]


class CancellationDetails(TypedDict):
    key: str
    value: str


class CancellationReason(TypedDict):
    code: str
    details: list[CancellationDetails]


class RejectedBet(TypedDict):
    uniqueRequestId: str
    betStatus: Literal["NOT_ACCEPTED"]
    resultingUnit: NotRequired[str | None]


class StraightBet(TypedDict):
    betId: int
    wagerNumber: int
    placedAt: str
    betStatus: Literal[
        "ACCEPTED",
        "CANCELLED",
        "LOSE",
        "PENDING_ACCEPTANCE",
        "REFUNDED",
        "NOT_ACCEPTED",
        "WON",
    ]
    betType: BetTypeFull
    win: float
    risk: float
    oddsFormat: OddsFormat
    updateSequence: int
    price: float
    winLoss: NotRequired[float]
    customerCommission: NotRequired[float]
    cancellationReason: NotRequired[CancellationReason]
    handicap: NotRequired[float]
    side: NotRequired[Literal["OVER", "UNDER"]]
    pitcher1: NotRequired[str]
    pitcher2: NotRequired[str]
    pitcher1MustStart: NotRequired[str]
    pitcher2MustStart: NotRequired[str]
    teamName: NotRequired[str]
    team1: NotRequired[str]
    team2: NotRequired[str]
    periodNumber: NotRequired[int]
    team1Score: NotRequired[float]
    team2Score: NotRequired[float]
    ftTeam1Score: NotRequired[float]
    ftTeam2Score: NotRequired[float]
    pTeam1Score: NotRequired[float]
    pTeam2Score: NotRequired[float]
    isLive: Literal["true", "false"]


class PlaceStraightBetResponse(TypedDict):
    status: Literal["ACCEPTED", "PENDING_ACCEPTANCE", "PROCESSED_WITH_ERROR"]
    uniqueRequestId: str
    errorCode: NotRequired[
        Literal[
            "ALL_BETTING_CLOSED",
            "ALL_LIVE_BETTING_CLOSED",
            "ABOVE_EVENT_MAX",
            "ABOVE_MAX_BET_AMOUNT",
            "BELOW_MIN_BET_AMOUNT",
            "BLOCKED_BETTING",
            "BLOCKED_CLIENT",
            "INSUFFICIENT_FUNDS",
            "INVALID_COUNTRY",
            "INVALID_EVENT",
            "INVALID_ODDS_FORMAT",
            "LINE_CHANGED",
            "LISTED_PITCHERS_SELECTION_ERROR",
            "OFFLINE_EVENT",
            "PAST_CUTOFFTIME",
            "RED_CARDS_CHANGED",
            "SCORE_CHANGED",
            "DUPLICATE_UNIQUE_REQUEST_ID",
            "INCOMPLETE_CUSTOMER_BETTING_PROFILE",
            "INVALID_CUSTOMER_PROFILE",
            "LIMITS_CONFIGURATION_ISSUE",
            "RESPONSIBLE_BETTING_LOSS_LIMIT_EXCEEDED",
            "RESPONSIBLE_BETTING_RISK_LIMIT_EXCEEDED",
            "RESUBMIT_REQUEST",
            "SYSTEM_ERROR_3",
            "LICENCE_RESTRICTION_LIVE_BETTING_BLOCKED",
            "INVALID_HANDICAP",
            "BETTING_SUSPENDED",
        ]
    ]
    straightBet: NotRequired[StraightBet]


class CancellationDetailsV3(TypedDict):
    key: str
    value: str


class CancellationReasonV3(TypedDict):
    code: str
    details: list[CancellationDetailsV3]


class StraightBetV3(TypedDict):
    betId: int
    wagerNumber: int
    placedAt: str
    betStatus: BetStatus
    betStatus2: BetStatus2
    betType: BetTypeFull
    win: float
    risk: float
    oddsFormat: OddsFormat
    updateSequence: int
    price: float
    isLive: bool
    eventStartTime: str

    # Optional fields (use NotRequired for fields that may be absent)
    winLoss: NotRequired[float | None]
    customerCommission: NotRequired[float | None]
    cancellationReason: NotRequired[CancellationReasonV3]
    sportId: NotRequired[int]
    leagueId: NotRequired[int]
    eventId: NotRequired[int]
    handicap: NotRequired[float | None]
    teamName: NotRequired[str]
    side: NotRequired[Literal["OVER", "UNDER"] | None]
    pitcher1: NotRequired[str | None]
    pitcher2: NotRequired[str | None]
    pitcher1MustStart: NotRequired[bool | None]
    pitcher2MustStart: NotRequired[bool | None]
    team1: NotRequired[str]
    team2: NotRequired[str]
    periodNumber: NotRequired[int]
    team1Score: NotRequired[float | None]
    team2Score: NotRequired[float | None]
    ftTeam1Score: NotRequired[float | None]
    ftTeam2Score: NotRequired[float | None]
    pTeam1Score: NotRequired[float | None]
    pTeam2Score: NotRequired[float | None]
    resultingUnit: NotRequired[str]


# Not implemented placeholders:
class ParlayBetV2(TypedDict): ...


class TeaserBet(TypedDict): ...


class SpecialBetV3(TypedDict): ...


class ManualBet(TypedDict): ...


class BetsResponse(TypedDict):
    moreAvailable: bool
    pageSize: int
    fromRecord: int
    toRecord: int
    straightBets: NotRequired[list[StraightBetV3 | RejectedBet]]
    parlayBets: NotRequired[list[ParlayBetV2]]
    teaserBets: NotRequired[list[TeaserBet]]
    specialBets: NotRequired[list[SpecialBetV3]]
    manualBets: NotRequired[list[ManualBet]]
