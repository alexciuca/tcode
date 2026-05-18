from dataclasses import dataclass

from tcode.problems import ProblemMeta, load_index
from tcode.profile import UserProfile

DEFAULT_SESSION_IDS = ["0001", "0020", "0042"]


@dataclass(frozen=True)
class SessionPlan:
    problem_ids: list[str]


def _score_topic(stats) -> float:
    attempts = max(stats.attempts, 1)
    failure_rate = stats.failures / attempts
    hint_pressure = stats.hints_used / attempts
    return failure_rate + (0.25 * hint_pressure)


def _problem_has_topic(problem: ProblemMeta, topic: str) -> bool:
    return any(t.lower() == topic.lower() for t in problem.topics)


def _first_unseen_problem(
    problems: list[ProblemMeta], seen: set[str], difficulties: set[str]
) -> ProblemMeta | None:
    for problem in problems:
        if problem.id not in seen and problem.difficulty in difficulties:
            return problem
    for problem in problems:
        if problem.difficulty in difficulties:
            return problem
    return None


def _first_by_topic(
    problems: list[ProblemMeta], topic: str, seen: set[str], difficulties: set[str]
) -> ProblemMeta | None:
    for problem in problems:
        if (
            problem.id not in seen
            and problem.difficulty in difficulties
            and _problem_has_topic(problem, topic)
        ):
            return problem
    for problem in problems:
        if problem.difficulty in difficulties and _problem_has_topic(problem, topic):
            return problem
    return None


def build_session_plan(profile: UserProfile) -> SessionPlan:
    problems = load_index()
    by_id = {problem.id: problem for problem in problems}
    seen = set(profile.seen_problem_ids)

    if not profile.topic_stats:
        return SessionPlan([pid for pid in DEFAULT_SESSION_IDS if pid in by_id])

    ranked_topics = sorted(
        profile.topic_stats.items(),
        key=lambda item: _score_topic(item[1]),
    )
    strongest_topic = ranked_topics[0][0]
    weakest_topic = ranked_topics[-1][0]

    selected: list[str] = []

    warmup = _first_by_topic(problems, strongest_topic, seen, {"Easy", "Medium"})
    if warmup:
        selected.append(warmup.id)

    focus = _first_by_topic(problems, weakest_topic, seen, {"Easy", "Medium"})
    if focus and focus.id not in selected:
        selected.append(focus.id)

    stretch = _first_unseen_problem(problems, seen | set(selected), {"Medium", "Hard"})
    if stretch and stretch.id not in selected:
        selected.append(stretch.id)

    for fallback_id in DEFAULT_SESSION_IDS:
        if len(selected) >= 3:
            break
        if fallback_id in by_id and fallback_id not in selected:
            selected.append(fallback_id)

    return SessionPlan(selected[:3])
