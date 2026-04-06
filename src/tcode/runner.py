import json
import re
import subprocess
import sys
import tempfile
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from tcode.problems import Problem


@dataclass(frozen=True)
class TestResult:
    case: int
    passed: bool
    expected: Any
    actual: Any | None = None
    error: str | None = None


def _extract_method_name(starter_code: str) -> str:
    match = re.search(r"def (\w+)\(self", starter_code)
    return match.group(1) if match else "solve"


def _build_harness(code: str, method_name: str, test_cases: list) -> str:
    return f"""\
from typing import Dict, List, Optional, Set, Tuple

{code}

import json

results = []
test_cases = {json.dumps(test_cases)}
solution = Solution()

for i, tc in enumerate(test_cases):
    args = tc["args"]
    expected = tc["expected"]
    try:
        actual = solution.{method_name}(**args)
        if isinstance(expected, list) and isinstance(actual, (list, tuple)):
            passed = sorted(str(x) for x in actual) == sorted(str(x) for x in expected)
        else:
            passed = actual == expected
        results.append({{"case": i + 1, "passed": passed, "actual": actual,
        "expected": expected}})
    except Exception as e:
        results.append({{"case": i + 1, "passed": False, "error": str(e),
        "expected": expected}})

print(json.dumps(results))
"""


def run_tests(code: str, problem: Problem) -> list[TestResult]:
    if not problem.test_cases:
        return []

    method_name = _extract_method_name(problem.starter_code)
    harness = _build_harness(code, method_name, problem.test_cases)

    with tempfile.NamedTemporaryFile(
        mode="w", suffix=".py", delete=False, encoding="utf-8"
    ) as f:
        f.write(harness)
        harness_path = Path(f.name)

    try:
        result = subprocess.run(
            [sys.executable, str(harness_path)],
            capture_output=True,
            text=True,
            timeout=5,
        )
        if result.returncode != 0:
            stderr = result.stderr.strip()
            return [TestResult(case=0, passed=False, expected=None, error=stderr)]
        raw = json.loads(result.stdout)
        return [
            TestResult(
                case=r["case"],
                passed=r["passed"],
                expected=r["expected"],
                actual=r.get("actual"),
                error=r.get("error"),
            )
            for r in raw
        ]
    except subprocess.TimeoutExpired as e:
        e.process.kill() if e.process else None
        return [
            TestResult(
                case=0, passed=False, expected=None, error="Timed out after 5 seconds"
            )
        ]
    except json.JSONDecodeError:
        return [
            TestResult(
                case=0, passed=False, expected=None, error="Could not parse test output"
            )
        ]
    finally:
        harness_path.unlink(missing_ok=True)


def format_results(results: list[TestResult]) -> str:
    if not results:
        return "No test cases available for this problem."

    passed = sum(1 for r in results if r.passed)
    total = len(results)
    header = f"Tests: {passed}/{total} passed\n{'─' * 45}"

    lines = [header]
    for r in results:
        label = "case 0 (runtime error)" if r.case == 0 else f"case {r.case}"
        if r.passed:
            lines.append(f"  [black on green] PASS [/]  {label}")
        elif r.error:
            lines.append(
                f"  [white on red] FAIL [/]  {label}\n        Error: {r.error}"
            )
        else:
            lines.append(
                f"  [white on red] FAIL [/]  {label}\n"
                f"        Expected: {r.expected}\n"
                f"        Got:      {r.actual}"
            )

    return "\n".join(lines)
