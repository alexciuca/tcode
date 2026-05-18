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
    # Find first method inside Solution, skipping commented helper classes.
    solution_match = re.search(r"^class Solution", starter_code, re.MULTILINE)
    if solution_match:
        after_solution = starter_code[solution_match.start() :]
        method_match = re.search(r"def (\w+)\(self", after_solution)
        if method_match:
            return method_match.group(1)
    # Fallback: first def with self anywhere
    match = re.search(r"def (\w+)\(self", starter_code)
    return match.group(1) if match else "solve"


_NODE_HELPERS = """\
class TreeNode:
    def __init__(self, val=0, left=None, right=None):
        self.val = val
        self.left = left
        self.right = right

class ListNode:
    def __init__(self, val=0, next=None):
        self.val = val
        self.next = next

class Node:
    def __init__(self, val=0, neighbors=None, left=None, right=None,
                 next=None, children=None, random=None):
        self.val = val
        self.neighbors = neighbors if neighbors is not None else []
        self.left = left
        self.right = right
        self.next = next
        self.children = children if children is not None else []
        self.random = random

def _list_to_tree(arr):
    if not arr or arr[0] is None:
        return None
    root = TreeNode(arr[0])
    queue = [root]
    i = 1
    while queue and i < len(arr):
        node = queue.pop(0)
        if i < len(arr) and arr[i] is not None:
            node.left = TreeNode(arr[i])
            queue.append(node.left)
        i += 1
        if i < len(arr) and arr[i] is not None:
            node.right = TreeNode(arr[i])
            queue.append(node.right)
        i += 1
    return root

def _tree_to_list(root):
    if not root:
        return []
    result = []
    queue = [root]
    while queue:
        node = queue.pop(0)
        if node:
            result.append(node.val)
            queue.append(node.left)
            queue.append(node.right)
        else:
            result.append(None)
    while result and result[-1] is None:
        result.pop()
    return result

def _list_to_linked(arr):
    if not arr:
        return None
    head = ListNode(arr[0])
    current = head
    for val in arr[1:]:
        current.next = ListNode(val)
        current = current.next
    return head

def _linked_to_list(head):
    result = []
    while head:
        result.append(head.val)
        head = head.next
    return result

def _convert_arg(name, value, type_hint):
    if value is None:
        return None
    if "TreeNode" in type_hint and isinstance(value, list):
        return _list_to_tree(value)
    if "ListNode" in type_hint and isinstance(value, list):
        return _list_to_linked(value)
    return value

def _convert_result(value):
    if isinstance(value, TreeNode):
        return _tree_to_list(value)
    if isinstance(value, ListNode):
        return _linked_to_list(value)
    if isinstance(value, (list, tuple)):
        return [_convert_result(v) for v in value]
    return value
"""


_BASIC_HELPERS = """\
def _convert_result(value):
    if isinstance(value, (list, tuple)):
        return [_convert_result(v) for v in value]
    return value
"""


def _needs_node_helpers(starter_code: str) -> bool:
    return any(kw in starter_code for kw in ("TreeNode", "ListNode", "Node"))


def _extract_param_types(starter_code: str) -> dict[str, str]:
    """Extract parameter name -> type hint string from the Solution method."""
    # Only inspect Solution, not commented TreeNode/ListNode helpers.
    solution_match = re.search(r"^class Solution", starter_code, re.MULTILINE)
    search_text = (
        starter_code[solution_match.start() :] if solution_match else starter_code
    )
    match = re.search(r"def \w+\(self,?\s*(.*?)\)", search_text, re.DOTALL)
    if not match:
        return {}
    params_str = match.group(1)
    result = {}
    for param in params_str.split(","):
        param = param.strip()
        if ":" in param:
            name, type_hint = param.split(":", 1)
            result[name.strip()] = type_hint.strip()
        elif param:
            result[param.strip()] = ""
    return result


def _build_harness(
    code: str, method_name: str, test_cases: list, starter_code: str = ""
) -> str:
    uses_nodes = _needs_node_helpers(starter_code)
    param_types = _extract_param_types(starter_code) if uses_nodes else {}

    helper_block = _NODE_HELPERS if uses_nodes else _BASIC_HELPERS
    param_types_json = json.dumps(param_types)

    if uses_nodes:
        convert_block = f"""\
        param_types = {param_types_json}
        converted = {{}}
        for k, v in args.items():
            hint = param_types.get(k, '')
            converted[k] = _convert_arg(k, v, hint)
        actual = solution.{method_name}(**converted)"""
    else:
        convert_block = f"        actual = solution.{method_name}(**args)"

    return f"""\
from typing import Dict, List, Optional, Set, Tuple

{helper_block}
{code}

import json

null = None
true = True
false = False

results = []
test_cases = {json.dumps(test_cases)}
solution = Solution()

for i, tc in enumerate(test_cases):
    args = tc["args"]
    expected = tc["expected"]
    try:
{convert_block}
        actual = _convert_result(actual)
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
    harness = _build_harness(
        code,
        method_name,
        problem.test_cases,
        problem.starter_code,
    )

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
