from typing import Literal, Required, TypedDict


class LineResponse(TypedDict, total=False):
    status: Required[Literal["SUCCESS", "NOT_EXISTS"]]

    # The following fields are present only when status == "SUCCESS"
    price: float
    lineId: int
    altLineId: int

    team1Score: int
    team2Score: int
    team1RedCards: int
    team2RedCards: int

    maxRiskStake: float
    minRiskStake: float
    maxWinStake: float
    minWinStake: float

    effectiveAsOf: str

    periodTeam1Score: int
    periodTeam2Score: int
    periodTeam1RedCards: int
    periodTeam2RedCards: int
