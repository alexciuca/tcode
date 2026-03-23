import json
import os
from dataclasses import dataclass

from anthropic import Anthropic

from tcode.problems import Problem

DEFAULT_ANTHROPIC_MODEL = "claude-3-5-haiku-latest"


class MissingAnthropicAPIKeyError(Exception):
    """Exception raised when the API key for anthropic is missing"""


class InvalidModelResponseError(Exception):
    """Exception raised when the model's response is invalid or is not valid JSON"""


@dataclass(frozen=True)
class ComplexityResult:
    complexity_estimate: str
    risk_flag: bool
    explanation: str


@dataclass(frozen=True)
class HintResult:
    hint_level: int
    message: str


@dataclass(frozen=True)
class FailureResult:
    message: str


def _build_client() -> Anthropic:
    api_key = os.getenv("ANTHROPIC_API_KEY")
    if api_key is None:
        raise MissingAnthropicAPIKeyError("The ANTHROPIC_API_KEY variable must be set.")
    return Anthropic(api_key=api_key)


def _call_llm(system: str, user: str) -> dict:
    client = _build_client()
    response = client.messages.create(
        model=DEFAULT_ANTHROPIC_MODEL,
        max_tokens=512,
        system=system,
        messages=[{"role": "user", "content": user}],
    )

    response_text = response.content[0].text

    try:
        return json.loads(response_text)
    except json.JSONDecodeError:
        raise InvalidModelResponseError(
            f"Model returned invalid JSON: {response_text!r}"
        )


def check_complexity(code: str, problem: Problem) -> ComplexityResult:
    system = """
            You are a code complexity analyzer. Given student code and a problem constraint, analyze the time complexity and output ONLY valid JSON with no markdown, no explanation outside the JSON.
            Output schema:{"complexity_estimate": "O(n²)", "risk_flag": true, "explanation": "Nested loop detected. At n=10,000 this is ~100M operations and will likely timeout."}
            If the code is too short or empty to analyze:{"complexity_estimate": "unknown", "risk_flag": false, "explanation": "Not enough code to analyze yet."}
            Never output anything outside the JSON object.
            """
    user = f"Problem: {problem.title}\nConstraints: {', '.join(problem.constraints)}\n\nStudent code:\n{code}"

    data = _call_llm(system, user)

    try:
        return ComplexityResult(
            complexity_estimate=data["complexity_estimate"],
            risk_flag=data["risk_flag"],
            explanation=data["explanation"],
        )
    except KeyError as e:
        raise InvalidModelResponseError(f"Missing key in response: {e}")


def get_hint(code: str, problem: Problem, hints_used: int) -> HintResult:
    system = """
        You are a Socratic coding tutor. You never give the answer directly. You guide students to discover solutions themselves. Output ONLY valid JSON with no markdown.

        Hint ladder:
        - Level 1: Conceptual — challenge their mental model, no code reference
        - Level 2: Code-aware — reference their actual variable names or approach
        - Level 3: Directional — narrow to the specific missing insight
        - Level 4: Pseudocode only — never actual runnable code

        Never exceed level 4. Never give the answer directly.

        Output schema:
        {"hint_level": 2, "message": "Your outer loop variable is i — what could you store about nums[i] as you iterate?"}

        Never output anything outside the JSON object.
        """
    user = f"Problem: {problem.title}\nConstraints: {', '.join(problem.constraints)}\nHints already given: {hints_used}\n\nStudent code:\n{code}\n\nGive hint number {min(hints_used + 1, 4)}."

    data = _call_llm(system, user)

    try:
        return HintResult(
            hint_level=data["hint_level"],
            message=data["message"],
        )
    except KeyError as e:
        raise InvalidModelResponseError(f"Missing key in response: {e}")


def explain_failure(code: str, problem: Problem, test_output: str) -> FailureResult:
    system = """
        You are a Socratic coding tutor. You never give the answer directly. You help students understand why their code failed and guide them toward the fix. Output ONLY valid JSON with no markdown.
        Output schema:
        {"message": "Your function returns None when the list has duplicate values. What happens to your loop when nums[i] equals nums[j]?"}

        Never output anything outside the JSON object. Never give the solution directly.
    """
    user = f"Problem: {problem.title}\nConstraints: {', '.join(problem.constraints)}\nStudent code:\n{code}\nTest output: {test_output}."

    data = _call_llm(system, user)

    try:
        return FailureResult(message=data["message"])
    except KeyError as e:
        raise InvalidModelResponseError(f"Missing key in response: {e}")
