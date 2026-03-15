# tcode

tcode is a terminal-based AI training engine for CS students learning data structures and algorithms.

## Dev setup

```bash
uv sync
uv run tcode start --file path/to/solution.py
```

## Notes

- Flow: `tcode start` → menu (`TCodeApp`) → select a problem → session view (`SessionApp`).
- `--file` is the path to the student's solution file (used by the session UI; file watching is planned).
