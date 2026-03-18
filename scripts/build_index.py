"""Build index.json from all problems in data/problems/."""
import json
from pathlib import Path

PROBLEMS_DIR = Path("data/problems")
INDEX_FILE = Path("data/index.json")

index = []

for file in sorted(PROBLEMS_DIR.glob("*.json")):
    raw = json.loads(file.read_text(encoding="utf-8"))
    index.append(
        {
            "id": raw["id"],
            "slug": raw["slug"],
            "title": raw["title"],
            "difficulty": raw["difficulty"],
            "topics": raw["topics"],
            "file": file.name,
        }
    )

INDEX_FILE.write_text(json.dumps(index, indent=2, ensure_ascii=False))
print(f"Built index with {len(index)} problems")
