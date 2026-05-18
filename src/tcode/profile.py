import json
from dataclasses import asdict, dataclass, field
from pathlib import Path

PROFILE_FILE = Path.home() / ".tcode" / "profile.json"


@dataclass
class TopicStats:
    attempts: int = 0
    passes: int = 0
    failures: int = 0
    hints_used: int = 0


@dataclass
class UserProfile:
    topic_stats: dict[str, TopicStats] = field(default_factory=dict)
    seen_problem_ids: list[str] = field(default_factory=list)


def _topic_stats_from_dict(raw: dict) -> TopicStats:
    return TopicStats(
        attempts=int(raw.get("attempts", 0)),
        passes=int(raw.get("passes", 0)),
        failures=int(raw.get("failures", 0)),
        hints_used=int(raw.get("hints_used", 0)),
    )


def load_profile(path: Path = PROFILE_FILE) -> UserProfile:
    if not path.exists():
        return UserProfile()

    raw = json.loads(path.read_text(encoding="utf-8"))
    return UserProfile(
        topic_stats={
            topic: _topic_stats_from_dict(stats)
            for topic, stats in raw.get("topic_stats", {}).items()
        },
        seen_problem_ids=list(raw.get("seen_problem_ids", [])),
    )


def save_profile(profile: UserProfile, path: Path = PROFILE_FILE) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    data = {
        "topic_stats": {
            topic: asdict(stats) for topic, stats in profile.topic_stats.items()
        },
        "seen_problem_ids": profile.seen_problem_ids,
    }
    path.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")


def mark_problem_seen(profile: UserProfile, problem_id: str) -> None:
    if problem_id not in profile.seen_problem_ids:
        profile.seen_problem_ids.append(problem_id)


def record_hint(profile: UserProfile, topics: list[str]) -> None:
    for topic in topics:
        profile.topic_stats.setdefault(topic, TopicStats()).hints_used += 1


def record_test_run(profile: UserProfile, topics: list[str], passed: bool) -> None:
    for topic in topics:
        stats = profile.topic_stats.setdefault(topic, TopicStats())
        stats.attempts += 1
        if passed:
            stats.passes += 1
        else:
            stats.failures += 1
