"""Convert neenza/leetcode-problems format to tcode format."""

import json
from pathlib import Path

SOURCE = Path("/tmp/leetcode-problems/problems")
DEST = Path("data/problems")
DEST.mkdir(parents=True, exist_ok=True)

converted = 0
skipped = 0

for file in sorted(SOURCE.glob("*.json")):
    raw = json.loads(file.read_text(encoding="utf-8"))

    # skip if missing critical fields
    if not raw.get("title") or not raw.get("description"):
        skipped += 1
        continue

    # extract examples from their format
    examples = []
    for ex in raw.get("examples", []):
        examples.append({"example_text": ex.get("example_text", "")})

    problem = {
        "id": str(raw.get("frontend_id", raw.get("problem_id", ""))).zfill(4),
        "slug": raw.get("problem_slug", ""),
        "title": raw.get("title", ""),
        "difficulty": raw.get("difficulty", ""),
        "topics": raw.get("topics", []),
        "description": raw.get("description", ""),
        "constraints": raw.get("constraints", []),
        "examples": examples,
        "hints": raw.get("hints", []),
        "starter_code": raw.get("code_snippets", {}).get("python3", ""),
        "test_cases": [],  # not in their dataset, you add manually for key problems
    }

    slug = problem["slug"] or file.stem
    out_file = DEST / f"{problem['id']}-{slug}.json"
    out_file.write_text(json.dumps(problem, indent=2, ensure_ascii=False))
    converted += 1

print(f"Converted: {converted}")
print(f"Skipped:   {skipped}")
