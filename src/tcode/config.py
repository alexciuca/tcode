import json
from dataclasses import dataclass, asdict
from pathlib import Path

# Set where session will be stored locally
STATE_FILE = Path.home() / ".tcode" / "session.json"

@dataclass
class SessionConfig:
    mode: str = "adaptive"
    topic: str | None = None
    difficulty: str = "mixed"
    problem_id: str | None = None

    def save_session(self) -> None:
        STATE_FILE.parent.mkdir(exist_ok=True)
        # convert dataclass dict to JSON
        STATE_FILE.write_text(json.dumps(asdict(self)))
        
    @classmethod
    def load_session(cls) -> "SessionConfig":
        if not STATE_FILE.exists():
            return cls()
        data = json.loads(STATE_FILE.read_text())
        return cls(**data)