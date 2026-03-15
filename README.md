# tcode

tcode is a terminal-based AI training engine for CS students learning data structures and algorithms.

## Dev setup

```bash
git clone https://github.com/alexandru356/tcode.git
cd tcode
uv sync
```
## Running the app
```bash
uv run tcode start --file path/to/solution.py
```
## Running tests
```bash
uv run pytest
```

## Formatting and linting
```bash
# check for issues
uv run ruff check .

# fix automatically
uv run ruff check --fix .

# format code
uv run ruff format .
```


## Notes

- Flow: `tcode start` → menu (`TCodeApp`) → select a problem → session view (`SessionApp`).
- `--file` is the path to the student's solution file (used by the session UI; file watching is planned).

