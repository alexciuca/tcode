from dataclasses import dataclass


@dataclass
class SessionConfig:
    mode: str = "adaptive"
    topic: str | None = None
    difficulty: str = "mixed"
    problem_id: str | None = None
