hi there! long time no see
i made some progress but i don't know why it doesn't want to **accept placing bet**

this is what i have:
```python
from typing import Any, Literal

from ps3838api.api import BetPlacementResponse, _post # type: ignore
from ps3838api.models.bets import PlaceStraightBetResponse

def place_straigh_bet(
    stake: float,
    win_risk_stake: Literal["WIN", "RISK"],

    unique_request_id: str,
    
    line_id: int,
    # pitcher1_must_start: bool,
    # pitcher2_must_start: bool,
    sport_id: int,
    event_id: int,
    period_number: int,
    bet_type: Literal["MONEYLINE", "TEAM_TOTAL_POINTS", "SPREAD", "TOTAL_POINTS"],
    # team: Literal["TEAM1", "TEAM2", "DRAW"],
    odds_format: Literal["AMERICAN", "DECIMAL", "HONGKONG", "INDONESIAN", "MALAY"] = "DECIMAL",

    fill_type: Literal["NORMAL", "FILLANDKILL", "FILLMAXLIMIT"] = "NORMAL",
    accept_better_line: bool = True,
    alt_line_id: int | None = None,
    side: Literal["OVER", "UNDER"] | None = None,
    handicap: float | None = None,
) -> PlaceStraightBetResponse:
    params: dict[str, Any] = {
        "oddsFormat": odds_format,
        "uniqueRequestId": unique_request_id,
        "acceptBetterLine": int(accept_better_line),
        "stake": stake,
        "winRiskStake": win_risk_stake,
        "lineId": line_id,
        "pitcher1MustStart": 1, #int(pitcher1_must_start),
        "pitcher2MustStart": 1, #int(pitcher2_must_start),
        "fillType": fill_type,
        "sportId": sport_id,
        "eventId": event_id,
        "periodNumber": period_number,
        "betType": bet_type,
        # "team": team,
    }
    if alt_line_id is not None:
        params["altLineId"] = alt_line_id
    if side is not None:
        params["side"] = side
    if handicap is not None:
        params["handicap"] = handicap


    endpoint = "/v2/bets"
    data = _post(endpoint, params)
    return cast(PlaceStraightBetResponse, data)
```
PlaceStraightBetResponse just a typed dict with all data

This is what docs say:

```
Place straight bet - v2
Place straight bet (SPREAD, MONEYLINE, TOTAL_POINTS, TEAM_TOTAL_POINTS).

Please note when the status is PENDING_ACCEPTANCE and if the live delay was applied, the response will not have betId. Client would have to call /bets by uniqueRequestId to check the status if the bet was ACCEPTED.

For more details please see How to place a bet on live events?

Authorizations:
basicAuth
Request Body schema: application/json
oddsFormat	
string (OddsFormat)
Enum: "AMERICAN" "DECIMAL" "HONGKONG" "INDONESIAN" "MALAY"
Bet odds format.
AMERICAN = American odds format,
DECIMAL = Decimal (European) odds format,
HONGKONG = Hong Kong odds format,
INDONESIAN = Indonesian odds format,
MALAY = Malaysian odds format

uniqueRequestId	
string <uuid>
This is a Unique ID for PlaceBet requests. This is to support idempotent requests.

acceptBetterLine	
boolean
Whether or not to accept a bet when there is a line change in favor of the client.

stake	
number <double>
amount in client’s currency.

winRiskStake	
string
Enum: "WIN" "RISK"
Whether the stake amount is risk or win amount.

lineId	
integer <int64>
Line identification.

altLineId	
integer or null <int64>
Alternate line identification.

pitcher1MustStart	
boolean
Baseball only. Refers to the pitcher for Team1. This applicable only for MONEYLINE bet type, for all other bet types this has to be TRUE.

pitcher2MustStart	
boolean
Baseball only. Refers to the pitcher for Team2. This applicable only for MONEYLINE bet type, for all other bet types this has to be TRUE.

fillType	
string
Default: "NORMAL"
Enum: "NORMAL" "FILLANDKILL" "FILLMAXLIMIT"
NORMAL - bet will be placed on specified stake.
FILLANDKILL - If the stake is over the max limit, bet will be placed on max limit, otherwise it will be placed on specified stake.
FILLMAXLIMIT - bet will be places on max limit, stake amount will be ignored. Please note that maximum limits can change at any moment, which may result in risking more than anticipated. This option is replacement of isMaxStakeBet from v1/bets/place'

sportId	
integer <int32>
eventId	
integer <int64>
periodNumber	
integer <int32>
betType	
string
Enum: "MONEYLINE" "TEAM_TOTAL_POINTS" "SPREAD" "TOTAL_POINTS"
Bet type.

team	
string
Enum: "TEAM1" "TEAM2" "DRAW"
Team type.

side	
string or null
Enum: "OVER" "UNDER"
Side type.

handicap	
number <double>
This is optional parameter for SPREAD, TOTAL_POINTS and TEAM_TOTAL_POINTS bet types.

```

Note that it is not stated which parameters required and which don't, so i am actually guessing and use common sence

Live events differ only in the Response

I am going to bet on TOTAL_POINTS, OVER

No matter I tried with this request:

```python
place_straigh_bet(
    stake=1.0,
    win_risk_stake="RISK",
    unique_request_id=str(uniqueRequestId),
    line_id=line_id,
    sport_id=ps.SOCCER_SPORT_ID,
    event_id=event_id,
    period_number=0,
    bet_type='TOTAL_POINTS',
    handicap=2.75,
    side='OVER'
)
```
I am getting "HTTPError: 405 Client Error: Not Allowed for url: https://api.ps3838.com/v2/bets"

At the same time line_id 100% exist:
```python
ps.get_line(
    sport_id=ps.SOCCER_SPORT_ID,
    league_id=league_id,
    event_id=event_id,
    period_number=0,
    bet_type="TOTAL_POINTS",
    handicap=2.75,
    side='OVER'
)
```
results in
```
{'status': 'SUCCESS',
 'price': 1.847,
 'lineId': 3023664311,
 'altLineId': None,
 'team1Score': None,
 'team2Score': None,
 'team1RedCards': None,
 'team2RedCards': None,
 'maxRiskStake': 4425.0,
 'minRiskStake': 1.0,
 'maxWinStake': 3750.0,
 'minWinStake': 0.85,
 'effectiveAsOf': '2025-04-02T05:15:27Z',
 'periodTeam1Score': None,
 'periodTeam2Score': None,
 'periodTeam1RedCards': None,
 'periodTeam2RedCards': None}
```

my main question: is this problems with requests? or with my API?
in the retrieving requests some times rate limits use HTTP ERROR (requests.exceptions.HTTPError: 429 Client Error) but sometimes just return empty response (literally empty string, not even json)

i could try different account. but still isn't it weird if API response in 405 if it just don't like u?

or maybe i missed some essential part of the request?
is it okay if i used int for the booleans?
Ok i rewrite it to the booleans and it still the same response
this is yours _post function


this is what some third party lib has
compare if we have any differences:
```python
    def place_bet(
        self, 
        stake: float, 
        line_id: int, 
        sport_id: int, 
        event_id: int, 
        period_number: int, 
        team: str, 
        side: str = None, 
        handicap: float = None
    ) -> Dict[str, Any]:
        """
        Place a bet on the PS3838 API.
        
        Parameters:
            stake: The amount of the bet (min 5 euros)
            line_id: The line ID of the bet
            sport_id: The sport ID of the event (football = 29)
            event_id: The event ID of the event
            period_number: The period number of the event (0 for full time)
            team: The team to bet on "TEAM1" or "TEAM2" or "DRAW"
            side: The side to bet on (optional)
            handicap: The handicap value (optional)
            Other values that will be passed to the API are hardcoded
            
        Returns:
            The response from the API
        """

        # Generate a unique request ID
        unique_request_id = str(uuid.uuid4())  
        
        # Construct the data payload
        data = {
            "oddsFormat": "DECIMAL",
            "uniqueRequestId": unique_request_id,
            "acceptBetterLine": True,
            "stake": stake,
            "winRiskStake": "RISK",
            "lineId": line_id,
            "altLineId": None,
            "pitcher1MustStart": True,
            "pitcher2MustStart": True,
            "fillType": "NORMAL",
            "sportId": sport_id,
            "eventId": event_id,
            "periodNumber": period_number,
            "betType": "MONEYLINE",
            "team": team,
            "side": side,
            "handicap": handicap
        }

        return self._make_request('/v2/bets/place', data=data, method='POST')
```