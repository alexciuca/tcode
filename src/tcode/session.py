from textual.app import App, ComposeResult
from textual.containers import Horizontal
from textual.widgets import Header, Footer, Static
from pathlib import Path
from tcode.config import SessionConfig
from tcode.problems import load_index, load_problem_by_id
import re


class SessionApp(App):
    CSS_PATH = "assets/tcode.tcss"
    TITLE = "tcode"

    BINDINGS = [
        ("h", "hint", "Hint"),
        ("enter", "run", "Run"),
        ("q", "quit", "Quit"),
    ]

    def __init__(self, watch_path: Path, config: SessionConfig) -> None:
        super().__init__()
        self.watch_path = watch_path
        self.config = config
        self.problems = load_index()
        self.active_problem = load_problem_by_id(self.problems[0].id)

    def compose(self) -> ComposeResult:
        yield Header()
        yield Horizontal(
            Static("", id="left"),
            Static("", id="right"),
        )
        yield Footer()

    def on_mount(self) -> None:
        self._update_left()
        self._update_right(
        f"Watching: {self.watch_path}\n"
        f"{'─' * 45}\n\n"
        "Ready. Save your file to begin.\n\n"
        "Keys:\n"
        "  h      → hint\n"
        "  enter  → run tests\n"
        "  q      → quit"
    )

    def _clean_description(self, description: str) -> str:
        for marker in ["Example 1:", "Example 2:", "Examples:", "Constraints:"]:
            if marker in description:
                description = description[:description.index(marker)].strip()
                break
        return description

    def _clean_constraint(self, constraint: str) -> str:
        return re.sub(r'10(\d+)', lambda m: f"10^{m.group(1)}", constraint)

    def _update_left(self) -> None:
        p = self.active_problem
        description = self._clean_description(p.description)
        text = (
            f"{p.title}   #{p.id} · {p.difficulty}\n"
            f"{'─' * 45}\n"
            f"Topics: {', '.join(p.topics)}\n\n"
            f"Description:\n{description}\n\n"
        )
        if p.examples:
            text += "Examples:\n"
            for ex in p.examples:
                text += f"{ex['example_text']}\n\n"
        if p.constraints:
            text += "Constraints:\n"
            for c in p.constraints:
                text += f"  · {self._clean_constraint(c)}\n"
        self.query_one("#left", Static).update(text)

    def _update_right(self, text: str) -> None:
        self.query_one("#right", Static).update(text)


if __name__ == "__main__":
    app = SessionApp(
        watch_path=Path("solution.py"),
        config=SessionConfig()
    )
    app.run()
