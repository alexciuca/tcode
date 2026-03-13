# tcode

tcode is a terminal-based AI training engine for CS students learning data structures and algorithms.

## Dev setup

```bash
uv sync
cp .env.example .env
# set TCODE_API_KEY in .env (optional for now)
uv run tcode start --file path/to/solution.py
```

## Notes

- `tcode start --file <path>` launches the Textual TUI and watches the file for changes.
- If `TCODE_API_KEY` is not set, hint/complexity features run in a stubbed mode.
