# Modern PS3838 API

## 🔑 Key Idea

This project aims to keep all method names and behavior as close as possible to the official [PS3838 API documentation](https://ps3838api.github.io/docs/). No abstraction layers that get in your way — just a clean, Pythonic interface to the raw API.

## ✨ Features

### `api.py` — Minimalist, Typed API Wrapper

- All commonly used endpoints are exposed as simple Python functions.
- Responses are structured using precise `TypedDict` definitions based directly on the official docs.
- Say goodbye to messy, undocumented JSON blobs.
- No bloated ORMs or clunky third-party wrappers — just clean, readable code.

## 🎁 Bonus: `tank.py`

- A small utility module that enables you to fetch odds by just providing the league name, home team, and away team.
- Probably not useful for everyone — this was built for a specific use case, but it might come in handy.

## Local installation

```bash
pip install -e . -r dev-requirements.txt
```