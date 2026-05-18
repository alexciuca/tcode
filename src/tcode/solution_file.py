from pathlib import Path


def write_starter_code_if_needed(file: Path, starter_code: str) -> bool:
    """Create an empty solution file with starter code without overwriting work."""
    file.parent.mkdir(parents=True, exist_ok=True)
    if file.exists() and file.read_text(encoding="utf-8").strip():
        return False

    content = starter_code.rstrip() + "\n" if starter_code.strip() else ""
    file.write_text(content, encoding="utf-8")
    return True
