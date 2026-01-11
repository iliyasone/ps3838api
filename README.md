# Modern PS3838 API

A lightweight Python library to interact with the PS3838 (Pinnacle) API and place bets.

## 🔑 Key Idea

This project aims to keep all method names and behavior as close as possible to the official [PS3838 API documentation](https://ps3838api.github.io/docs/). No abstraction layers that get in your way — just a clean, Pythonic functional interface to the raw API.

If you need assistance, contact me directly on Telegram: [@iliyasone](https://t.me/iliyasone) 💬

If you have any questions or need additional tools, join Betting API PS3838 & Pinnacle Telegram Group Chat: [@ps3838api](https://t.me/ps3838api/77/78) 

If you don’t have access to the PS3838 API (Pinnacle) yet, feel free to reach out — I can help you get started with obtaining access.

## ✨ Features

### `ps3838api.api` — Minimalist, Typed API Wrapper

- **PinnacleClient-First:** Instantiate `ps3838api.api.client.PinnacleClient` with credentials supplied via environment variables and call methods directly. Legacy module-level helpers still work for backwards compatibility, but marked as deprecated.
- **Type-Safe:** Responses are structured using precise `TypedDict` definitions based directly on the official docs.
- **Clean Data:** Say goodbye to messy, undocumented JSON blobs.
- **Lightweight:** No bloated ORMs or clunky third-party wrappers — just clean, readable code.

### Bet Placement

- Place bets with simple functions that eliminate unnecessary overhead.

## 🚀 Setup

> You can also check out the [📓 examples.ipynb](https://github.com/iliyasone/ps3838api/blob/release/1.0.1/examples/examples.ipynb) for a quick start!

This project has been created and tested on the Python 3.13.7, however it should work also on Python>=3.12

### 1. Create PinnacleClient

```python
from ps3838api.api.client import PinnacleClient
from ps3838api.models.sports import Sport

client = PinnacleClient(
    login='YOUR_LOGIN',
    password='YOUR_PASSWORD',
    api_base_url='https://api.ps3838.com', # default
    default_sport=Sport.SOCCER_SPORT_ID # default
)
```

`PinnacleClient` could also use `PS3838_LOGIN`, `PS3838_PASSWORD` environment variables.
It is also possible to change default `PS3838_API_BASE_URL` from https://api.ps3838.com/ to a different Pinnacle mirror

> Pinnacle888 is yet another one popular Pinnacle mirror, and its documentation and endpoints are identical to the PS3838  
>
> Docs: https://pinny888.github.io/  
>
> API Base URL: https://api.pinnacle888.com  

### 2. Check PinnacleClient Balance

Quickly check your account balance by calling the API:

```python
from ps3838api.api.client import PinnacleClient

client = PinnacleClient()
balance = client.get_client_balance()
print("PinnacleClient Balance:", balance)
```

Expected output:

```json
{
    "availableBalance": 200.0,
    "outstandingTransactions": 0.0,
    "givenCredit": 0.0,
    "currency": "USD"
}
```

## 🎯 Retrieve Events and Fixtures Place Bet

Find and use events with ease:

```python
fixtures = client.get_fixtures()
odds = client.get_odds()
```

Using fixtures and odds, find events according to the method interfaces and [official Pinnacle API Response schemas](https://ps3838api.github.io/docs/#tag/Odds/operation/Odds_Straight_V3_Get)

### V4 API Endpoints

For enhanced odds responses with alternative team total lines, use the V4 client:

```python
# Get V4 odds with array-based team totals
v4_odds = client.v4.get_odds(sport_id=1)

# Get V4 parlay odds
v4_parlay_odds = client.v4.get_parlay_odds(sport_id=1)
```

V4 endpoints provide the same parameters as V3 but return enhanced response structures where team totals are arrays, allowing multiple alternative lines per team.

> note: in a future version the package will include `magic_find_event` function which would make finding events more
straightforward 

## 💸 Place a Bet

Once you have your event and total line, place your bet:

```python
event_id: int
line_id: int
alt_line_id: int | None 
total_line_points: float

stake_usdt = 1.0

place_bet_response = client.place_straight_bet(
    stake=stake_usdt,
    event_id=event['eventId'],
    bet_type='TOTAL_POINTS',
    line_id=total_line.get('lineId', None),
    alt_line_id=total_line.get('altLineId', None),
    side='OVER',
    handicap=total_line['points']
)
print("Unique Request ID:", place_bet_response['uniqueRequestId'])
```

You can also check your bet status:

```python
bets = client.get_bets(unique_request_ids=[place_bet_response['uniqueRequestId']])
# Verify the bet status
```

## 🛠️ Local Installation

To install the library locally, install `uv` and run the following commands:

```bash
git clone https://github.com/iliyasone/ps3838api.git
cd ps3838api
uv sync --all-groups
```

## Run checkers

```bash
uv run ruff check
uv run ruff format
uv run pyright
```

Happy coding
