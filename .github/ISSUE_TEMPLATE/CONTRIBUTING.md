# Contributing to tcode

## Setup
```bash
git clone https://github.com/alexandru356/tcode.git
cd tcode
uv sync
```

## Workflow
1. Branch off `dev` — never commit directly to `main` or `dev`
2. Name your branch `feat/your-feature` or `fix/your-fix`
3. Write tests for new logic
4. Run `uv run pytest` before pushing
5. Run `uv run ruff format .` before pushing
6. Open a PR into `dev`

## Project structure
See README.md for architecture overview.

## Questions
Open an issue or start a discussion on GitHub.
