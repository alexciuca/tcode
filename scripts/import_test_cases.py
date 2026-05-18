"""Import test cases from chrisxue815/leetcode_test_cases."""

import json
import urllib.request
from pathlib import Path

REPO_API = "https://api.github.com/repos/chrisxue815/leetcode_test_cases/contents/"
RAW_BASE = "https://raw.githubusercontent.com/chrisxue815/leetcode_test_cases/master/"

PROBLEMS_DIR = Path(__file__).resolve().parents[1] / "data" / "problems"
INDEX_PATH = Path(__file__).resolve().parents[1] / "data" / "index.json"


def fetch_json(url: str) -> dict | list:
    req = urllib.request.Request(url, headers={"User-Agent": "tcode-importer"})
    with urllib.request.urlopen(req) as resp:
        return json.loads(resp.read())


def get_available_test_ids() -> list[str]:
    """Fetch the list of test case file IDs from the GitHub repo."""
    items = fetch_json(REPO_API)
    ids = []
    for item in items:
        name = item["name"]
        if name.startswith("test_") and name.endswith(".json"):
            ids.append(name.replace("test_", "").replace(".json", ""))
    return sorted(ids)


def load_our_index() -> dict[str, str]:
    """Return a mapping of problem ID to filename from our index."""
    raw = json.loads(INDEX_PATH.read_text(encoding="utf-8"))
    return {entry["id"]: entry["file"] for entry in raw}


def import_test_cases() -> None:
    print("Fetching list of available test cases...")
    remote_ids = get_available_test_ids()
    print(f"Found {len(remote_ids)} test case files in remote repo.")

    our_index = load_our_index()
    matching_ids = [pid for pid in remote_ids if pid in our_index]
    print(f"{len(matching_ids)} match our problem index.\n")

    imported = 0
    skipped = 0
    errors = 0

    for i, pid in enumerate(matching_ids, 1):
        filename = our_index[pid]
        problem_path = PROBLEMS_DIR / filename

        if not problem_path.exists():
            print(
                f"  [{i}/{len(matching_ids)}] SKIP {pid} - file not found: {filename}"
            )
            skipped += 1
            continue

        # Load our problem JSON
        problem = json.loads(problem_path.read_text(encoding="utf-8"))

        # Skip if already has test cases
        if problem.get("test_cases"):
            case_count = len(problem["test_cases"])
            print(
                f"  [{i}/{len(matching_ids)}] SKIP {pid} - "
                f"already has {case_count} test cases"
            )
            skipped += 1
            continue

        # Fetch remote test cases
        try:
            url = f"{RAW_BASE}test_{pid}.json"
            remote_data = fetch_json(url)
            cases = remote_data.get("test_cases", [])

            if not cases:
                print(
                    f"  [{i}/{len(matching_ids)}] SKIP {pid} - "
                    "remote file has no test cases"
                )
                skipped += 1
                continue

            # Merge into our problem JSON
            problem["test_cases"] = cases
            problem_path.write_text(
                json.dumps(problem, indent=2, ensure_ascii=False) + "\n",
                encoding="utf-8",
            )
            print(
                f"  [{i}/{len(matching_ids)}] OK   {pid} - "
                f"{len(cases)} test cases imported"
            )
            imported += 1

        except Exception as e:
            print(f"  [{i}/{len(matching_ids)}] ERR  {pid} — {e}")
            errors += 1

    print(f"\nDone. Imported: {imported}, Skipped: {skipped}, Errors: {errors}")


if __name__ == "__main__":
    import_test_cases()
