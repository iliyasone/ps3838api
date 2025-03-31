I have football (soccerr) event as league, Home and Away strings

I want to bet on the total over of number of goals via api on the ps3838

I bet on live events

This is extraction from the API
How to Place a Straight Bet?

```
Getting Started
Step 1 – Sign Up
To get started you would need to create an account.

Please note that in order to access PS3838 API the account must be funded.

Step 2 - Get a List of Offered Sports and Leagues
You would need to get the list of sports from Get Sports operation. If you are interested in particular leagues you can get all sport leagues by calling Get Leagues operation. Lines API

Step 3 - Place Bet
To place a bet, please check sections How to place a straight bet? And How to place a parlay bet?

Step 4 - Get Bets
To check the status of the placed bet you need to call Get Bets operation. The recommended way is to use bet id.

For bets on live events that are in PENDING_ACCEPTANCE state, you can call Get Bets every 5 sec to get the new status of the bet, to see if it’s accepted or rejected.

How to Place a Straight Bet?
Step 1 – Call Get Fixtures operation Lines API
This will return the list of events that are currently offered. To get updates use delta requests (with since parameter).

Step 2 – Call Get Odds operation Lines API
This will return the list of odds that are currently offered. To get updates use delta requests (with since parameter).

Step 3 - Get Line (optional) Lines API
Call Get Line operation if you need exact stake limits or if you are interested only in a specific line. Please note that the limits in the Get Feed response are just general limits. Limits in the Get Line response are the exact limits.

Step 4 - Place Bet Bets API
To place a bet you need to call Place Bet operation.

The table shows how to do mapping of Get Odds operation response to Place Bet and Get Line request.

Parameter Get Odds response parameter sportId sportId leagueId League Type -> id eventId Event Type -> id periodNumber Period Type -> number team Depends on selected odds from:

· Spread Type · Moneyline Type · Team Total Points

check the value in the corresponding Get Leagues Response -> League Type -> homeTeamType and set the appropriate value. Example 1:

Given: homeTeamType=”Team1” When: Selected odds is Spread Type -> away Then: team=Team2

Example 2: When: Selected odds is Moneyline Type -> draw Then: team=Draw

Example 3:

Given: homeTeamType=”Team2” When: Selected odds is Team Total Points Type -> away Then: team=Team1 handicap Spread Type -> hdp Total Points Type -> points Team Total Points Type -> Total Points Type -> points lineId Period Type -> lineId altLineId Spread Type ->altLineId Total Points Type -> altLineId If you call Get Line operation, use the lineId (altLineId) from the response.

A period in an event is open for betting if:

Get Fixtures Response -> Event Type -> status has a value I or O Event period has odds in Get Odds Response Get Odds Response -> Period Type -> cutoff is in the future. Please note that for live events, odds change quite frequently as well as the event status, from O/I to H and vice versa. Due to these frequent changes, it’s possible that you will be getting status NOT_EXISTS in the Get Line response more often than for the dead ball events.
```

A few years ago i was already working with ps3838 api and i have some understanding, however i may not remeber exact details about my code. Back then I did not read this getting started guide and may missed some essencial points (but system still working bro hah)
My system was not betting, just examing the difference in odds. As i understand, system is searching for new odds and major changes in them.

The main thing that i don't understand about this API, how to bet on **total over** of number of goals? Not on the win/lose (as i understand this is what my system analyzing now)
I understand basics of betting, handicaps. I prefer Decimal odds view. I don't clearly understand the difference betweens Get Straigh Odds and Get Starigh Line in this API.
Also there is some weirdness in this API, because as i understand, Straight odd means only moneyline, but in this api total over/under is also could be obtained from Get Straigh Line 


Some API reference:
Or you could examine API yourself (goodluck hah)
https://ps3838api.github.io/docs/?api=lines#tag/Odds

```
Get Special Odds - v2
Returns odds for specials for all non-settled events.

Authorizations:
basicAuth
query Parameters
oddsFormat	
string
Enum: "American" "Decimal" "HongKong" "Indonesian" "Malay"
Format the odds are returned in. [American, Decimal, HongKong, Indonesian, Malay]

sportId
required
integer <int32>
Id of a sport for which to retrieve the specials.

leagueIds	
Array of integers <int32> [ items <int32 > ]
The leagueIds array may contain a list of comma separated league ids.

since	
integer <int64>
This is used to receive incremental updates. Use the value of last from previous response. When since parameter is not provided, the fixtures are delayed up to 1 min to encourage the use of the parameter.

specialId	
integer <int64>
Id of the special. This is an optional argument.
```


```
Get Straight Odds - v3
Returns straight odds for all non-settled events. Please note that it is possible that the event is in Get Fixtures response but not in Get Odds. This happens when the odds are not currently available for wagering.

Authorizations:
basicAuth
query Parameters
sportId
required
integer <int32>
The sportid for which to retrieve the odds.

leagueIds	
Array of integers <int32> [ items <int32 > ]
The leagueIds array may contain a list of comma separated league ids.

oddsFormat	
string
Enum: "American" "Decimal" "HongKong" "Indonesian" "Malay"
Format in which we return the odds. Default is American. [American, Decimal, HongKong, Indonesian, Malay]

since	
integer <int64>
This is used to receive incremental updates. Use the value of last from previous odds response. When since parameter is not provided, the odds are delayed up to 1 min to encourage the use of the parameter. Please note that when using since parameter you will get in the response ONLY changed periods. If a period did not have any changes it will not be in the response.

isLive	
boolean
To retrieve ONLY live odds set the value to 1 (isLive=1). Otherwise response will have all odds.

eventIds	
Array of integers <int64> [ items <int64 > ]
Filter by EventIds

toCurrencyCode	
string
3 letter currency code as in the /currency response. Limits will be returned in the requested currency. Default is USD.

```

```
Get Straight Line - v2
Returns latest line.

Authorizations:
basicAuth
query Parameters
leagueId
required
integer <int32>
League Id.

handicap
required
number <double>
This is needed for SPREAD, TOTAL_POINTS and TEAM_TOTAL_POINTS bet types

oddsFormat
required
string
Enum: "American" "Decimal" "HongKong" "Indonesian" "Malay"
Format in which we return the odds. Default is American.

sportId
required
integer <int32>
Sport identification

eventId
required
integer <int64>
Event identification

periodNumber
required
integer <int32>
This represents the period of the match. Please check Get Periods endpoint for the list of currently supported periods per sport.

betType
required
string
Enum: "SPREAD" "MONEYLINE" "TOTAL_POINTS" "TEAM_TOTAL_POINTS"
Bet Type

team	
string
Enum: "Team1" "Team2" "Draw"
Chosen team type. This is needed only for SPREAD, MONEYLINE and TEAM_TOTAL_POINTS bet types

side	
string
Enum: "OVER" "UNDER"
Chosen side. This is needed only for TOTAL_POINTS and TEAM_TOTAL_POINTS

```


My code from the Past

main file for working with api:
bets_ps3838.py
```python
# from __future__ import annotations
import base64
from collections import namedtuple
from json import JSONDecodeError, dumps
from time import sleep
from typing import Iterable

import dateutil.parser as dp
import requests

import logger
from models import FixturesData, League, LeaguesData, OddsData
from my_types import BijectiveDict, Market1_1, Market1_2, MatchesTuple, ResultBets

MIN_DELAY_BETWEEN_SPORTS_UPDATE = 60


class BetsPs3838Exception(Exception):
    pass


class EmptyResponse(BetsPs3838Exception):
    pass


class NoFixturesNow(BetsPs3838Exception):
    pass


SPORTS = BijectiveDict()
SPORTS.update(
    {
        1: "Badminton",
        2: "Bandy",
        3: "Baseball",
        4: "Basketball",
        5: "Beach Volleyball",
        6: "Boxing",
        7: "Chess",
        8: "Cricket",
        9: "Curling",
        10: "Darts",
        13: "Field Hockey",
        14: "Floorball",
        15: "Football",
        16: "Futsal",
        17: "Golf",
        18: "Handball",
        19: "Hockey",
        20: "Horse Racing Specials",
        21: "Lacrosse",
        22: "Mixed Martial Arts",
        23: "Other Sports",
        24: "Politics",
        26: "Rugby League",
        27: "Rugby Union",
        28: "Snooker",
        29: "Soccer",
        30: "Softball",
        31: "Squash",
        32: "Table Tennis",
        33: "Tennis",
        34: "Volleyball",
        36: "Water Polo",
        37: "Padel Tennis",
        39: "Aussie Rules",
        40: "Alpine Skiing",
        41: "Biathlon",
        42: "Ski Jumping",
        43: "Cross Country",
        44: "Formula 1",
        45: "Cycling",
        46: "Bobsleigh",
        47: "Figure Skating",
        48: "Freestyle Skiing",
        49: "Luge",
        50: "Nordic Combined",
        51: "Short Track",
        52: "Skeleton",
        53: "Snow Boarding",
        54: "Speed Skating",
        55: "Olympics",
        56: "Athletics",
        57: "Crossfit",
        58: "Entertainment",
        59: "Archery",
        60: "Drone Racing",
        62: "Poker",
        63: "Motorsport",
        64: "Simulated Games",
        65: "Sumo",
    }
)

BetTuple = namedtuple(
    "BetTuple",
    ["handicap", "home_odd", "away_odd", "max_spread", "limit_home", "limit_away"],
)

username = "SECRET"
password = "SECRET"


token = base64.b64encode(bytes(f"{username}:{password}", "utf-8")).decode("utf-8")

headers = {"Authorization": f"Basic {token}", "User-Agent": "Mozilla/5.0"}

pinnacle_api = "https://api.ps3838.com"



def get_json_response(link, params={}, headers=headers):
    n = 1
    while True:
        try:
            response = requests.get(link, params=params, headers=headers)
            response.text
            response.raise_for_status()
            return response.json()
        except JSONDecodeError:
            if n == 1 and "sportId" in params:
                init_sports_dict()
                if params["sportId"] not in sports_dict:
                    raise NoFixturesNow(
                        f"No fixtures now for {SPORTS[params['sportId']]} (id {params['sportId']})"
                    )
                    # f"\nlink {link}\nparams {params}")
            if n > 2:
                raise EmptyResponse(f"Empty response \nlink {link}\nparams {params}")
            sleep(2**n)
            n += 1
        except requests.exceptions.ConnectionError:
            if n > 2:
                raise EmptyResponse(f"No connection \nlink {link}\nparams {params}")
            sleep(2**n)
            n += 1


def params_generator():
    return {"sportId": SPORTS["Football"]}


def get_sports():
    link = pinnacle_api + "/v3/sports"
    return get_json_response(link)


def get_sports_dict():
    link = pinnacle_api + "/v3/sports"

    params = {}

    response = get_json_response(link, params=params, headers=headers)
    save_answer(response, "sports.json")
    result = BijectiveDict()
    for sport in response["sports"]:
        if sport["hasOfferings"]:
            result[int(sport["id"])] = sport["name"]

    return result


def get_leagues(sportId=SPORTS["Football"]) -> LeaguesData:
    link = pinnacle_api + "/v3/leagues"

    params = {"sportId": sportId}

    return get_json_response(link, params=params)


def get_fixtures(
    sportId: int | str = SPORTS["Football"],
    leagueIds: Iterable[int | str] | None = None,
    isLive: bool | None = None,
    since: int | None = None,
    eventIds: Iterable[int | str] = None,
    settled: bool = False,
    **kwargs,
):
    link = pinnacle_api + "/v3/fixtures" + ("/settled" if settled else "")

    params = {"sportId": sportId}

    if leagueIds is not None:
        params["leagueIds"] = ",".join(map(str, leagueIds))
    if isLive is not None:
        params["isLive"] = int(isLive)
    if since is not None:
        params["since"] = since
    if eventIds is not None:
        params["eventsIds"] = ",".join(map(str, eventIds))
    for key, value in kwargs.items():
        params[key] = value

    return get_json_response(link, params)


def get_odds(sportId=SPORTS["Football"], special: bool = False, **kwargs) -> OddsData:
    if special:
        link = pinnacle_api + "/v2/odds/special"
    else:
        link = pinnacle_api + "/v3/odds"

    params = {"sportId": sportId, "oddsFormat": "Decimal"}
    params.update(kwargs)
    # if event_id is not None:
    #     params['eventIds'] = event_id

    return get_json_response(link, params)


def get_special_fixtures(
    sportId=SPORTS["Olympics"], event_id=None, **kwargs
) -> FixturesData:
    link = pinnacle_api + "/v2/fixtures/special"

    params = {"sportId": sportId, "oddsFormat": "Decimal"}
    params.update(kwargs)
    if event_id is not None:
        params["eventId"] = event_id

    return get_json_response(link, params)


def get_periods(sportId):
    link = pinnacle_api + "/v1/periods"

    params = {"sportId": sportId}

    return get_json_response(link, params)


def makeMatchesTuple(ans, only_one_from_league=False):
    for league in ans["league"]:
        league_id = league["id"]
        league_name = league["name"]
        for event in league["events"]:
            yield MatchesTuple(
                event_id=event["id"],
                time=int(dp.parse(event["starts"]).timestamp()),
                time_status=event["liveStatus"],
                league_id=league_id,
                league=league_name,
                home_id=-1,
                home=event["home"],
                away_id=-1,
                away=event["away"],
                is_filled=False,
                is_completed=False,
                is_sended="NO",
            )
            if only_one_from_league:
                break


def get_fixtures_generator():
    ans = get_fixtures()
    for match in makeMatchesTuple(ans):
        yield match


def get_equal_line_with_limits(odds):
    hdp = odds["leagues"][0]["events"][0]["periods"][0]["spreads"][0]["hdp"]
    home_odd = odds["leagues"][0]["events"][0]["periods"][0]["spreads"][0]["home"]
    away_odd = odds["leagues"][0]["events"][0]["periods"][0]["spreads"][0]["away"]
    max_spread = odds["leagues"][0]["events"][0]["periods"][0]["maxSpread"]
    limit_home = max_spread / (home_odd - 1)
    limit_away = max_spread / (away_odd - 1)
    return BetTuple(hdp, home_odd, away_odd, max_spread, limit_home, limit_away)


def get_event_status(event) -> int:
    return event["periods"][0]["status"]


def get_equal_line_with_limits_from_event(event):
    hdp = event["periods"][0]["spreads"][0]["hdp"]
    home_odd = event["periods"][0]["spreads"][0]["home"]
    away_odd = event["periods"][0]["spreads"][0]["away"]
    max_spread = event["periods"][0]["maxSpread"]
    limit_home = max_spread / (home_odd - 1)
    limit_away = max_spread / (away_odd - 1)
    return BetTuple(hdp, home_odd, away_odd, max_spread, limit_home, limit_away)


def get_event_id(event):
    return event["id"]


def change_bet_format(odds: BetTuple) -> ResultBets:
    result = ResultBets()

    result["1_1"] = Market1_1(home_od="1.0", away_od="1.0")

    result["1_2"] = {
        odds.handicap: Market1_2(home_od=odds.home_odd, away_od=odds.away_odd)
    }

    result["1_3"] = {
        "max_spread": odds.max_spread,
        "limit_home": odds.limit_home,
        "limit_away": odds.limit_away,
    }

    return result


def get_all_odds_generator():
    ans = get_odds()
    for league in ans["leagues"]:
        for event in league["events"]:
            if get_event_status(event) == 1:
                result_odds = change_bet_format(
                    get_equal_line_with_limits_from_event(event)
                )
                yield get_event_id(event), result_odds


##
from time import time

last_time_init_sport = 0


def init_sports_dict():
    global sports_dict
    if time() - last_time_init_sport > MIN_DELAY_BETWEEN_SPORTS_UPDATE:
        sports_dict = get_sports_dict()
        return sports_dict
    return sports_dict


## TESTS


def save_answer(ans, name="output.json", folder=None):
    if folder != None:
        name = folder + "/" + name
    with open(name, "w", encoding="utf-8") as f:
        # print(dumps(ans))
        f.write(dumps(ans))


def test_get_all_matches_and_save():
    ans = get_fixtures()
    save_answer(ans, name="all_fixtures.json")


def test_get_special_league_settled(league_id=10747):
    ans = get_fixtures(leagueIds=(league_id,), settled=True)
    print(ans)
    save_answer(ans)


def get_all_settled_matches_and_save():
    ans = get_fixtures(settled=True)
    save_answer(ans, name="all_settled.json")


def test_get_matches_and_odds(sportId):
    for match in makeMatchesTuple(get_fixtures(sportId, only_one_from_league=True)):
        print(match)
        # logger.log(match)
        try:
            odds = get_equal_line_with_limits(get_odds(match.event_id))

            # logger.log(odds)
            print(odds)
            print(change_bet_format(odds))
            # logger.log(change_bet_format(odds))

            input("PRESS ENTER TO CONTINUE")
        except JSONDecodeError:

            print("skipped, odds didn't find")
            # logger.log("skipped, odds didn't find")
            pass


def get_separated_fixture(sportId, eventId, leagueId=None):
    kwargs = {}

    if leagueId is not None:
        kwargs["leagueIds"] = (leagueId,)
    ans = get_fixtures(sportId=sportId, eventIds=(eventId,), **kwargs)
    for league in ans["league"]:
        if leagueId is None or int(league["id"]) == int(leagueId):
            league_name = league["name"]
            for event in league["events"]:
                if int(event["id"]) != int(eventId):
                    continue
                event["league_name"] = league_name
                return event
    raise KeyError("Fixture did not found")


def test_get_all_odds():
    ans = get_odds()
    save_answer(ans, "all_odds.json")


def test_get_all_odds_generator():
    for event_id, results in get_all_odds_generator():
        print(event_id, ":", results)


def test_save_db_odds():
    ans = get_odds()
    from dataBase import DataBase

    db = DataBase()
    for event_id, resultBets in get_all_odds_generator():
        db.update_odds(event_id=event_id, **resultBets)
        print(event_id, resultBets)
        input("PRESS ENTER TO CONTIUNE")


def test_get_odds(event_id=1566258450):
    ans = get_equal_line_with_limits(get_odds(event_id=event_id))
    print(ans)


def test_settled_matches():
    ans = get_fixtures(settled=True, since=12_000_000)
    save_answer(ans)


def colored_logger_print():
    global print
    print = logger.init_logger(logger.Console_colored_logger()).log
    return print


if __name__ == "__main__":
    colored_logger_print()

    # ans = (
    #     get_special_fixtures(
    #         event_id=1593961024, sportId=SPORTS["Olympics"], leagueIds=(236414,)
    #     ),
    # )  # eventIds=(1593961012,)

    # ans = None or get_json_response(link = pinnacle_api + "/v2/fixtures/special",
    #                         params={'sportId': SPORTS['Olympics'], 'oddsFormat': 'Decimal',} )#'since': 1678489406923})

    # ans = get_special_fixtures(eventIds=(1594127653,))

    ans = get_odds(SPORTS["Olympics"], special=True, since=int(time()*1000)-1000*60*60)

    print(ans)
    save_answer(ans)

    # sports = get_sports()

    # save_answer(get_sports(), "sports.json")

    # sportId = 40
    # ans = get_periods(sportId=sportId)
    # ans = get_fixtures(sportId=sportId,eventIds=(1567820869,))
    # test_get_matches_and_odds(sportId)
    # ans = get_odds(sportId)
    # save_answer(ans, f"odds_{sportId}.json")
``` 

odss_tracker.py
```python
import time
from enum import Enum
from json import dumps

import bets_ps3838
import logger
from bets_ps3838 import (SPORTS, BetsPs3838Exception, EmptyResponse,
                         NoFixturesNow)
from InvertibleDict import InvertibleDict
from models import (HistoryNote, ZippedLeague, remove_ancient_notes,
                    traverse_zipped_data, zip_json_files)

DEBUG = False
LOG_DUMBS = False

DELAY_IF_NO_FIXTURES_NOW = 60 * 5
DELAY_IF_EMPTY_RESPONSE = 60

DELAY_FOR_DELETENIG_ANCIENT_EVENTS_ID = 60 * 60 * 24 * 5  # 5 days


class ChangeStatus(Enum):
    CHANGE_EXISTS = 1
    NO_CHANGE_EXISTS = 2
    NOTHING_TO_CHANGE = 3


EmptyResponse


class OddsTracker:
    def __init__(self, sportId, out_logger=None, p=1.1) -> None:
        self.sportId = sportId
        self.fixtures = {}
        self.logger = out_logger or logger.global_logger
        self.p = p
        self.status = ChangeStatus.CHANGE_EXISTS
        self.status_special = ChangeStatus.CHANGE_EXISTS
        self.last_time_request = time.time()
        self.last_time_request_special = time.time()
        self.last = None
        self.last_special = None

        self.history: InvertibleDict[int, str] = InvertibleDict()

        try:
            ans = bets_ps3838.get_odds(sportId=sportId)
        except NoFixturesNow as er:
            self.logger.log(er)
            self.status = ChangeStatus.NOTHING_TO_CHANGE
            return

        if LOG_DUMBS:
            self.logger.log_file(
                dumps(ans), time.strftime(f"sport-{sportId}-%Y%m%d-%H%M%S-init.json")
            )

        if DEBUG:
            bets_ps3838.save_answer(
                ans, time.strftime(f"sport-{sportId}-%Y%m%d-%H%M%S-init.json"), "logs"
            )
        self.last = ans["last"]

        for leagues in ans["leagues"]:
            for event in leagues["events"]:
                id = event["id"]
                if self.is_good_event(event) == "GOOD":
                    current_money_line = event["periods"][0]["moneyline"]
                    self.fixtures[id] = current_money_line

    @staticmethod
    def is_good_event(event):
        if event["periods"][0]["status"] != 1:
            return "WRONG_STATUS"
        if "moneyline" not in event["periods"][0]:
            return "EMPTY_MONEYLINE"
        return "GOOD"

    def compare_odds(self, previous: dict[str, float], current: dict[str, float]):
        if (v := (previous["home"] / current["home"])) >= self.p:
            return "home", v
        if (v := (previous["away"] / current["away"])) >= self.p:
            return "away", v
        return ()

    def update_odds(self, skip_live: bool = True):
        if (
            self.status == ChangeStatus.NOTHING_TO_CHANGE
            and time.time() < self.last_time_request + DELAY_IF_NO_FIXTURES_NOW
        ):
            return
        if (
            self.status == ChangeStatus.NO_CHANGE_EXISTS
            and time.time() < self.last_time_request + DELAY_IF_EMPTY_RESPONSE
        ):
            return
        try:
            if self.last is None:
                ans = bets_ps3838.get_odds(sportId=self.sportId)
            else:
                ans = bets_ps3838.get_odds(sportId=self.sportId, since=self.last)
            self.status = ChangeStatus.CHANGE_EXISTS
        except NoFixturesNow as er:
            self.status = ChangeStatus.NOTHING_TO_CHANGE
            self.last_time_request = time.time()
            self.logger.log(er)
            return
        except EmptyResponse as er:
            self.status = ChangeStatus.NO_CHANGE_EXISTS
            self.last_time_request = time.time()
            return

        if LOG_DUMBS:
            self.logger.log_file(
                dumps(ans),
                time.strftime(f"sport-{self.sportId}-%Y%m%d-%H%M%S-updated.json"),
            )
        if DEBUG:
            bets_ps3838.save_answer(
                ans,
                time.strftime(f"sport-{self.sportId}-%Y%m%d-%H%M%S-updated.json"),
                "logs",
            )

        leagues = 0
        events = 0
        self.last = ans["last"]
        for league in ans["leagues"]:
            leagues += 1
            for event in league["events"]:
                events += 1
                id = event["id"]
                if self.is_good_event(event) == "GOOD":
                    current_money_line = event["periods"][0]["moneyline"]

                    try:
                        fixture = bets_ps3838.get_separated_fixture(
                            self.sportId, eventId=id, leagueId=league["id"]
                        )
                    except KeyError:
                        continue

                    if (
                        skip_live
                        and "liveStatus" in fixture
                        and fixture["liveStatus"] == 1
                    ):
                        continue

                    if id in self.history.inv:
                        for ancient_time in tuple(self.history.keys()):
                            if (
                                time.time()
                                > ancient_time + DELAY_FOR_DELETENIG_ANCIENT_EVENTS_ID
                            ):
                                self.logger.log(f"id {id} deleted")
                                del self.history[ancient_time]
                            else:
                                break
                        continue

                    elif id not in self.fixtures:
                        self.fixtures[id] = current_money_line
                        self.history[int(time.time())] = id
                        yield {
                            "sportId": self.sportId,
                            "new": True,
                            "id": id,
                            "league_id": league["id"],
                            "previous_money_line": {"home": None, "away": None},
                            "current_money_line": current_money_line,
                            "fixture": fixture,
                            "type": "NEW",
                        }
                    else:
                        previous_money_line = self.fixtures[id]

                        compare = self.compare_odds(
                            previous_money_line, current_money_line
                        )
                        self.fixtures[id] = current_money_line

                        if compare:
                            yield {
                                "sportId": self.sportId,
                                compare[0]: compare[1],
                                "id": id,
                                "league_id": league["id"],
                                "previous_money_line": previous_money_line,
                                "current_money_line": current_money_line,
                                "fixture": fixture,
                                "type": "CHANGE",
                            }
                elif self.is_good_event(event) == "EMPTY_MONEYLINE":
                    try:
                        fixture = bets_ps3838.get_separated_fixture(
                            self.sportId, eventId=id, leagueId=league["id"]
                        )
                    except KeyError:
                        continue

                    if id not in self.fixtures:
                        continue
                    previous_money_line = self.fixtures[id]

                    self.logger.log(f"Odd of event id {id} are not available")

                    yield {
                        "sportId": self.sportId,
                        "id": id,
                        "league_id": league["id"],
                        "previous_money_line": previous_money_line,
                        "current_money_line": {"home": None, "away": None},
                        "fixture": fixture,
                        "type": "LAST",
                    }
                    del self.fixtures[id]

        self.logger.log(
            f"Analized response for {SPORTS[self.sportId]} (id {self.sportId})\n"
            f"Found {events} events from {leagues} leagues"
        )

    def update_future_odds(self) -> tuple[list[ZippedLeague], dict[int, HistoryNote]] | None:
        if not hasattr(self, 'history_set'):
            self.history_set: set[HistoryNote] = set()
 
        
        if (
            self.status_special == ChangeStatus.NOTHING_TO_CHANGE
            and time.time() < self.last_time_request + DELAY_IF_NO_FIXTURES_NOW
        ):
            return
        if (
            self.status_special == ChangeStatus.NO_CHANGE_EXISTS
            and time.time() < self.last_time_request_special + DELAY_IF_EMPTY_RESPONSE
        ):
            return
        try:
            if self.last_special is None:
                odds = bets_ps3838.get_odds(sportId=self.sportId, special=True)
                fixtures = bets_ps3838.get_special_fixtures(sportId=self.sportId)  
                leagues = None              
            else:
                odds = bets_ps3838.get_odds(
                    sportId=self.sportId, special=True, since=self.last_special
                )
                fixtures = bets_ps3838.get_special_fixtures(
                    sportId=self.sportId
                )
                leagues = bets_ps3838.get_leagues(sportId=self.sportId)["leagues"]
            self.status_special = ChangeStatus.CHANGE_EXISTS
        except NoFixturesNow as er:
            self.status_special = ChangeStatus.NOTHING_TO_CHANGE
            self.last_time_request_special = time.time()
            self.logger.log(er)
            return
        except EmptyResponse as er:
            self.status_special = ChangeStatus.NO_CHANGE_EXISTS
            self.last_time_request_special = time.time()
            return

        zipped = zip_json_files(fixtures, odds, leagues)

        if self.last_special is None:
            traverse_zipped_data(zipped, self.history_set, self.p)

            self.last_special = odds["last"]
            return

        self.last_special = odds["last"]
        
        remove_ancient_notes(self.history_set, DELAY_FOR_DELETENIG_ANCIENT_EVENTS_ID)
        
        return traverse_zipped_data(zipped, self.history_set, self.p)


def main():
    cyclingTracker = OddsTracker(45)

    while True:
        for result in cyclingTracker.update_odds():
            print(result)


def test_olympics():
    olympTracker = OddsTracker(SPORTS["Olympics"])

    olympTracker.last_special = int(time.time()*1000)-1000*60*60 # all odds for last 1 hour

    for result in olympTracker.update_future_odds():
        print(result)


if __name__ == "__main__":
    logger.init_logger(logger.Console_colored_logger())
    print = bets_ps3838.colored_logger_print()
    test_olympics()
```