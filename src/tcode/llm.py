import json
import os
import re
import subprocess
import sys
import tempfile
from dataclasses import dataclass
from pathlib import Path

from anthropic import Anthropic

from tcode.problems import Problem

DEFAULT_ANTHROPIC_MODEL = "claude-haiku-4-5-20251001"


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

    response_text = response.content[0].text.strip()
    if response_text.startswith("```"):
        response_text = response_text.split("\n", 1)[1]
        response_text = response_text.rsplit("```", 1)[0]
    response_text = response_text.strip()

    try:
        return json.loads(response_text)
    except json.JSONDecodeError:
        raise InvalidModelResponseError(
            f"Model returned invalid JSON: {response_text!r}"
        )


def check_complexity(code: str, problem: Problem) -> ComplexityResult:
    system = """
            You are a code complexity analyzer. Given student code
            and a problem constraint, analyze the time complexity 
            and output ONLY valid JSON with no markdown, 
            no explanation outside the JSON.
            Output schema:{"complexity_estimate": "O(n²)", "risk_flag"
            : true, "explanation": "Nested loop detected. 
            At n=10,000 this is ~100M operations and will likely timeout."}
            If the code is too short or empty to analyze:
            {"complexity_estimate": "unknown", "risk_flag": 
            false, "explanation": "Not enough code to analyze yet."}
            Never output anything outside the JSON object.
            """
    user = f"Problem: {problem.title}\nConstraints: {
        ', '.join(problem.constraints)
    }\n\nStudent code:\n{code}"

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
        You are a Socratic coding tutor. You never give the answer directly.
        You guide students to discover solutions themselves.
        Output ONLY valid JSON with no markdown.

        Hint ladder:
        - Level 1: Conceptual — challenge their mental model, no code reference
        - Level 2: Code-aware — reference their actual variable names or approach
        - Level 3: Directional — narrow to the specific missing insight
        - Level 4: Pseudocode only — never actual runnable code

        Never exceed level 4. Never give the answer directly.

        Output schema:
        {"hint_level": 2, "message": "Your outer loop variable is i
        — what could you store about nums[i] as you iterate?"}

        Never output anything outside the JSON object.
        """
    user = f"Problem: {problem.title}\nConstraints: {
        ', '.join(problem.constraints)
    }\nHints already given: {hints_used}\n\nStudent code:\n{code}\n\nGive hint number {
        min(hints_used + 1, 4)
    }."

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
        You are a Socratic coding tutor. You never give the answer directly.
        You help students understand why their code failed and guide them 
        toward the fix. Output ONLY valid JSON with no markdown.
        Output schema:
        {"message": "Your function returns None when the list has duplicate
        values. What happens to your loop when nums[i] equals nums[j]?"}

        Never output anything outside the JSON object. Never give the solution directly.
    """
    user = f"Problem: {problem.title}\nConstraints: {
        ', '.join(problem.constraints)
    }\nStudent code:\n{code}\nTest output: {test_output}."

    data = _call_llm(system, user)

    try:
        return FailureResult(message=data["message"])
    except KeyError as e:
        raise InvalidModelResponseError(f"Missing key in response: {e}")


def _generate_reference_solution(problem: Problem) -> str:
    system = """
        You are an expert competitive programmer.
        Write a correct Python Solution class for the given problem.
        Output ONLY raw Python code, no markdown, no explanation, no backticks.
        The class must be named Solution and match the starter code signature exactly.
    """
    user = f"""Problem: {problem.title}\nDescription: {problem.description}\n
        Starter code: {problem.starter_code}"""
    client = _build_client()
    response = client.messages.create(
        model=DEFAULT_ANTHROPIC_MODEL,
        max_tokens=1024,
        system=system,
        messages=[{"role": "user", "content": user}],
    )
    raw = response.content[0].text.strip()

    match = re.search(r"```(?:python)?\n(.*?)```", raw, re.DOTALL)
    if match:
        return match.group(1).strip()
    return raw


def _generate_inputs(problem: Problem) -> list[dict]:
    system = """
        You are a test input generator for coding problems.
        Output ONLY valid JSON with no markdown. No text outside the JSON object.
        Output schema: {"inputs": [{"nums": [2,7,11,15], "target": 9}, ...]}
        Rules:
        - Args must match the parameter names in the starter code exactly
        - Keep arrays small (4-6 elements max)
        - Distribution: 2 basic cases, 2 edge cases (negatives, duplicates, zeros), 
            1 stress case
        - Do NOT include expected outputs
    """
    user = f"""Problem: {problem.title}\nConstraints: {", ".join(problem.constraints)}
        \nStarter code: {problem.starter_code}\nGenerate 5 input cases."""
    data = _call_llm(system, user)
    try:
        return data["inputs"]
    except KeyError as e:
        raise InvalidModelResponseError(f"Missing key in response: {e}")


def _compute_expected(
    reference_code: str, inputs: list[dict], problem: Problem
) -> list[dict]:
    from tcode.runner import _extract_method_name  # reuse what you already have

    method_name = _extract_method_name(problem.starter_code)
    harness = (
        "from typing import Dict, List, Optional, Set, Tuple\n"
        + reference_code
        + "\nimport json\n"
        "inputs = " + json.dumps(inputs) + "\n"
        "solution = Solution()\n"
        "results = []\n"
        "for args in inputs:\n"
        f"    actual = solution.{method_name}(**args)\n"
        '    results.append({"args": args, "expected": actual})\n'
        "print(json.dumps(results))\n"
    )
    with tempfile.NamedTemporaryFile(
        mode="w", suffix=".py", delete=False, encoding="utf-8"
    ) as f:
        f.write(harness)
        path = Path(f.name)
    try:
        result = subprocess.run(
            [sys.executable, str(path)],
            capture_output=True,
            text=True,
            timeout=5,
        )
        if result.returncode != 0:
            raise InvalidModelResponseError(
                f"Reference solution failed:\n{result.stderr}"
            )
        return json.loads(result.stdout)
    finally:
        path.unlink(missing_ok=True)


def generate_test_cases(problem: Problem) -> list[dict]:
    inputs = _generate_inputs(problem)
    reference_code = _generate_reference_solution(problem)
    return _compute_expected(reference_code, inputs, problem)
