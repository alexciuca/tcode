import json
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class Problem:
    id: str
    slug: str
    title: str
    difficulty: str
    topics: list
    description: str
    constraints: list
    examples: list
    hints: list
    starter_code: str
    test_cases: list


@dataclass(frozen=True)
class ProblemMeta:
    id: str
    slug: str
    title: str
    difficulty: str
    topics: list
    file: str


def load_index() -> list[ProblemMeta]:
    here = Path(__file__).resolve()
    repo_root = here.parents[2]
    path = repo_root / "data" / "index.json"
    raw = json.loads(path.read_text(encoding="utf-8"))
    return [ProblemMeta(**item) for item in raw]


def load_problem_by_id(problem_id: str) -> Problem:
    """Load full problem only when needed."""
    here = Path(__file__).resolve()
    repo_root = here.parents[2]
    problems_dir = repo_root / "data" / "problems"
    matches = list(problems_dir.glob(f"{problem_id}-*.json"))
    if not matches:
        raise FileNotFoundError(f"Problem {problem_id} not found")
    raw = json.loads(matches[0].read_text(encoding="utf-8"))
    return Problem(**raw)
