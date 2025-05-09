# Modern PS3838 API

A lightweight Python library to interact with the PS3838 (Pinnacle) API and place bets.

## 🔑 Key Idea

This project aims to keep all method names and behavior as close as possible to the official [PS3838 API documentation](https://ps3838api.github.io/docs/). No abstraction layers that get in your way — just a clean, Pythonic functional interface to the raw API.

If you need assistance, contact me directly on Telegram: [@iliyasone](https://t.me/iliyasone) 💬

If you don’t have access to the PS3838 API (Pinnacle) yet, feel free to reach out — I can help you get started with obtaining access.

## ✨ Features

### `ps3838api.api` — Minimalist, Typed API Wrapper

- **Simple & Clear:** All commonly used endpoints are exposed as straightforward Python functions.
- **Type-Safe:** Responses are structured using precise `TypedDict` definitions based directly on the official docs.
- **Clean Data:** Say goodbye to messy, undocumented JSON blobs.
- **Lightweight:** No bloated ORMs or clunky third-party wrappers — just clean, readable code.

### Event & Odds Matching

- Utility functions like `magic_find_event` and `filter_odds` help you match events and filter odds quickly and effortlessly 🔍.

### Bet Placement

- Place bets with simple functions that eliminate unnecessary overhead. Fast and efficient, just as you like it!

## 🚀 Setup

> You can also check out the [📓 examples.ipynb](https://github.com/iliyasone/ps3838api/blob/release/0.1.0/examples/examples.ipynb) for a quick start!

### 1. Set Environment Variables

Before using the library, set your API credentials via environment variables:

```python
import os

os.environ["PS3838_LOGIN"] = "your_username"
os.environ["PS3838_PASSWORD"] = "your_password"
```

> **Note:** After version 1.0, the library will transition to a client-based API instead of just functions.

---

### 2. Check Client Balance

Quickly check your account balance by calling the API:

```python
import ps3838api.api as ps

balance = ps.get_client_balance()
print("Client Balance:", balance)
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

## 🎯 Retrieve Event and Place Bet

Find and use events with ease:

```python
league = 'Russia - Cup'
home = 'Lokomotiv Moscow'
away = 'Akhmat Grozny'

fixtures = ps.get_fixtures()  # sport_id: int = SOCCER_SPORT_ID by default
```

Match the event using utility functions:

```python
from ps3838api.matching import magic_find_event

event = magic_find_event(fixtures, league, home, away)
print(event)
# Example output: {'eventId': 1607937909, 'leagueId': 2409}
```

Make sure to validate the event:

```python
assert isinstance(event, dict)  # also could be Failure
```

Filter odds for the selected event:

```python
from ps3838api.logic import filter_odds

odds_response = ps.get_odds()
odds_eventV3 = filter_odds(odds_response, event_id=event['eventId'])
```

Select the best total line:

```python
from ps3838api.totals import get_best_total_line

total_line = get_best_total_line(odds_eventV3)
print(total_line)
```

An example response:

```json
{
    "points": 4.5,
    "over": 2.08,
    "under": 1.775,
    "lineId": 3058623866,
    "max": 3750.0
}
```

## 💸 Place a Bet

Once you have your event and total line, place your bet:

```python
assert isinstance(event, dict)  # also could be Failure
assert total_line is not None 

import ps3838api.api as ps

stake_usdt = 1.0

place_bet_response = ps.place_straigh_bet(
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
bets = ps.get_bets(unique_request_ids=[place_bet_response['uniqueRequestId']])
# Verify the bet status
```

## ⚠️ Known Issues

- **Logging:** Not implemented yet.
- **Testing:** Still missing.
- **CI/CD:** No GitHub CI/CD integration at the moment.

## 🛠️ Local Installation

To install the library locally, run the following commands:

```bash
git clone https://github.com/iliyasone/ps3838api.git
cd ps3838api
pip install . -r dev-requirements.txt
```

Happy coding