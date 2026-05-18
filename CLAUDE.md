# CLAUDE.md — tcode

This file is for AI agents (Claude Code, Cursor, etc.) working in this repo.
Read this before touching any file.

---

## What tcode is

tcode is a terminal-based AI training engine for CS students learning data structures and algorithms.

It is a **CLI companion** — not a code editor. The student writes code in their own editor (VS Code, Cursor, whatever). tcode watches their file, coaches them through DSA problems in the terminal, and adapts to their weaknesses over time.

**The one-liner:** you code in your editor. tcode trains you in your terminal.

---

## What tcode is NOT

- Not a code editor. Never add an in-TUI editor.
- Not a problem solver. The AI must never give the answer directly.
- Not a web app. This is a local CLI tool. No server, no auth, no database.
- Not multi-user. Single user, local machine, local JSON storage.

---

## Core architecture

```
src/tcode/
  cli.py          # Click entrypoint — tcode start --file <path>
  tui.py          # Textual menu app (TCodeApp)
  search.py       # Problem picker screen (SearchProblems)
  session.py      # Textual session app (SessionApp) — two panes
  problems.py     # load problems via data/index.json + data/problems/*.json
  config.py       # SessionConfig dataclass

data/
  index.json      # problem metadata index
  problems/*.json # full problem payloads (one file per problem)

scripts/
  import_problems.py
  build_index.py

tests/
  (to be added)

CLAUDE.md         # this file
README.md
pyproject.toml
.env.example
.gitignore
```

---

## Runtime flow

The CLI always starts in the menu.

1. `tcode start --file solution.py`
2. `TCodeApp` (menu) opens
3. User selects a problem (via `SearchProblems`)
4. Menu exits, returning the selected `problem_id`
5. CLI launches `SessionApp(watch_path=..., config.problem_id=...)`

---

## TUI layout

The **session view** is two panes only. No exceptions.

```
┌─────────────────────────┬─────────────────────────┐
│  LEFT                   │  RIGHT                  │
│                         │                         │
│  Session plan           │  AI coach output        │
│  (today's 3 problems)   │  Complexity warnings    │
│                         │  Hints                  │
│  Active problem         │  Test results           │
│  statement              │  Concept explanations   │
│  + constraints          │                         │
│  + examples             │                         │
└─────────────────────────┴─────────────────────────┘
         Footer: keybind reference
```

**Keybinds:**
- `h` — Socratic hint (informed by current saved code)
- `?` — explain the relevant concept in plain English
- `Enter` — run tests, show pass/fail + AI explanation of failures
- `n / p` — next / previous problem in session
- `c` — show explicit complexity analysis of current code
- `r` — reset hint history for current problem
- `Tab` — switch scroll focus between panes
- `q` — quit, save session, update weakness profile

---

## The file watcher (planned)

- Watches a single file passed via `--file` flag
- Uses `watchdog` with a 3 second debounce (prevents API spam on auto-save)
- On every save: read file contents, update internal code snapshot, trigger complexity analysis silently
- The AI reads the student's actual code on every hint request — hints are never generic
- If the file doesn't exist yet: show a prompt in the TUI and watch for creation

---

## The adaptive engine

After every session, tcode updates `~/.tcode/profile.json` with performance per topic.

Session plan (3 problems):
1. **Warm-up** — topic the student is solid on (low hints, low failures)
2. **Focus** — weakest topic (highest hints used + failures)
3. **Stretch** — topic not seen recently or not seen at all

First session (no profile yet) defaults:
1. Warm-up: Two Sum (Easy, Arrays)
2. Focus: Valid Anagram (Easy, Hash Maps)
3. Stretch: Best Time to Buy Stock (Easy, Arrays)

---

## AI behavior — critical rules

The AI must follow these rules in every prompt. Never relax them.

1. **Never give the answer.** Not as code, not as a complete algorithm description.
2. **Socratic method always.** Answer questions with guiding questions.
3. **Hint ladder — 4 levels max:**
   - Hint 1: Conceptual — challenges mental model, no code reference
   - Hint 2: Code-aware — references their actual variable names / approach
   - Hint 3: Directional — narrows to the specific missing insight
   - Hint 4: Pseudocode only — never actual runnable code
4. **If student pastes a complete solution on first save:** ask them to explain it line by line. Turn it into a learning moment.
5. **If student asks for the answer directly:** refuse, offer a stronger hint.
6. **Complexity analysis is automatic on save** — not a user-requested feature.

---

## Prompt contracts (planned)

### Complexity check (on every save)
```
System: You are a complexity analyzer. Given code and a problem constraint, 
        output ONLY valid JSON — no markdown, no explanation outside the JSON.

Output schema:
{
  "complexity_estimate": "O(n²)",
  "risk_flag": true,
  "explanation": "Nested loop detected. At n=10,000 this is ~100M operations and will likely timeout."
}

If code is too short to analyze, return:
{
  "complexity_estimate": "unknown",
  "risk_flag": false,
  "explanation": "Not enough code to analyze yet."
}
```

### Hint request
```
System: You are a Socratic coding tutor. You never give answers. 
        You guide students to discover solutions themselves.
        Output ONLY valid JSON.

Output schema:
{
  "hint_level": 2,
  "message": "Your outer loop variable is i — what could you store about nums[i] as you pass through it?"
}
```

Always pass: current code snapshot, problem statement, constraint_n, expected_complexity, hints_used_so_far.

---

## Data schemas

### Problem (data/problems/<id>-<slug>.json)
```json
{
  "id": "0001",
  "slug": "two-sum",
  "title": "Two Sum",
  "difficulty": "Easy",
  "topics": ["Array", "Hash Table"],
  "description": "…",
  "constraints": ["…"],
  "examples": [{"example_text": "…"}],
  "hints": ["…"],
  "starter_code": "…",
  "test_cases": []
}
```

### Index entry (data/index.json)
```json
{
  "id": "0001",
  "slug": "two-sum",
  "title": "Two Sum",
  "difficulty": "Easy",
  "topics": ["Array", "Hash Table"],
  "file": "0001-two-sum.json"
}
```

### Profile (~/.tcode/profile.json)
```json
{
  "topic_stats": {
    "Hash Maps": {
      "hints_used": 8,
      "failures": 3,
      "time_spent_seconds": 1240,
      "last_seen": "2026-03-11"
    }
  }
}
```

### Session (~/.tcode/sessions/<timestamp>.json)
```json
{
  "session_id": "20260311_152600",
  "started_at": "2026-03-11T15:26:00",
  "problems": [
    {
      "problem_id": "001",
      "hints_used": 2,
      "time_spent_seconds": 420,
      "test_failures": 1,
      "completed": true
    }
  ]
}
```

---

## Code execution (planned)

- MVP: Python only. No other languages.
- Uses `subprocess.run` with `timeout=5`
- `capture_output=True` — stdout/stderr never leak into TUI directly
- A small test harness is generated on the fly, written to a temp file, executed, then deleted
- Do NOT use `eval()` or `exec()` — always subprocess
- This is a local tool on the user's machine. The user running malicious code affects only themselves. Document this clearly in README.

```python
# correct pattern
result = subprocess.run(
    [sys.executable, temp_harness_path],
    capture_output=True,
    text=True,
    timeout=5,
)
```

---

## Environment variables (planned)

```bash
TCODE_API_KEY=        # Anthropic API key — required
TCODE_MODEL=          # default: claude-haiku-4-5-20251001
TCODE_DATA_DIR=       # default: ~/.tcode
```

Never hardcode API keys. Never commit `.env`. Only `.env.example` is committed.

---

## What's in scope for MVP

- `tcode start --file <path>` only. No other CLI commands.
- Python solutions only
- macOS + Linux only
- Local JSON storage only
- 10 seed problems
- No auth, no cloud, no sync
- No in-TUI settings UI — config via env vars only

## What's explicitly out of scope for MVP

- Mock interview mode (`tcode interview`) — Phase 2
- Multi-language support — Phase 2
- Windows support — Phase 2
- Cloud sync / cross-device profile — Phase 3
- VS Code extension — not planned
- Web dashboard — not planned

---

## Dev setup

```bash
uv sync
uv run tcode start --file solution.py
```

## Running tests

```bash
uv run pytest tests/
```

---

## Coding conventions

- Type hints on all function signatures
- Docstrings on all public functions
- No print statements in production code — use Textual's logging
- All AI responses parsed as JSON — never parse free text from the AI
- Debounce logic must be tested — it's the most failure-prone component
- Keep `llm.py` stateless — pass all context in, get structured output back

---

## What good looks like

A student opens their terminal, runs `tcode start --file solution.py`, opens VS Code, writes a brute force Two Sum with a nested loop, saves — and immediately sees in the right pane:

```
⚠ Complexity warning: O(n²) detected.
  Constraint: n <= 10,000
  This will likely timeout.
```

They press `h`:

```
✦ You have two loops iterating over the same array.
  What if you only needed to loop once?
  What could you remember about each element as you pass it?
```

That's the product. Every decision in this codebase should serve that moment.
