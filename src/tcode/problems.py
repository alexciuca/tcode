import json
from pathlib import Path
from dataclasses import dataclass

@dataclass(frozen=True)
class Problem:
    id: str
    title: str
    difficulty: str
    topic: str
    constraint_n: int
    expected_complexity: str
    description: str
    examples : list
    test_cases: list

def load_problems() -> list[Problem]:
    current = Path(__file__).resolve()
    repo_root = current.parents[2]
    path = repo_root / "data" / "problems.json"
    raw = json.loads(path.read_text(encoding="utf-8"))
    problems = []
    for i in raw:
        problems.append(Problem(
            id=i["id"],
            title=i["title"],
            difficulty=i["difficulty"],
            topic=i["topic"],
            constraint_n=i["constraint_n"],
            expected_complexity=i["expected_complexity"],
            description=i["description"],
            examples=i.get("examples", []),
            test_cases=i.get("test_cases", []),
            ))
    return problems

