## Tools

### Rules

#### Prefer deep methods — avoid shallow private methods

Avoid creating shallow helper or dunder methods. Just do the job inline.

You may use existing helpers, but be very cautious about introducing new ones.

#### Avoid substantial architectural changes without explicit approval

All major architectural changes should be discussed in advance.

#### Stick to the existing code style


## Execution

You definitely **can**:

* use `git diff` (it is my responsibility to ensure a clean git state; you will see only your changes from the current or previous session)
* use local credentials from `.env` if provided

You definitely **should**:

* run linters and type checks:

```bash
uv run pyright
```

```bash
uv run ruff check
uv run ruff format
```

* run tests if provided