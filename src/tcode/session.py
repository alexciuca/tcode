from textual.app import App, ComposeResult
from textual.containers import Horizontal
from textual.widgets import Header, Footer, Static
from pathlib import Path
from tcode.config import SessionConfig
from tcode.problems import load_index, load_problem_by_id


class SessionApp(App):
    CSS_PATH = "assets/tcode.tcss"

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
            "Watching: " + str(self.watch_path) + "\n\nSave your file to start."
        )

    def _update_left(self) -> None:
        p = self.active_problem
        text = (
            f"{p.title}   #{p.id} · {p.difficulty}\n"
            f"{'─' * 45}\n"
            f"Topics: {', '.join(p.topics)}\n\n"
            f"Description:\n{p.description}\n\n"
        )
        if p.examples:
            text += "Examples:\n"
            for ex in p.examples:
                text += f"{ex['example_text']}\n\n"
        if p.constraints:
            text += "Constraints:\n"
            for c in p.constraints:
                text += f"  · {c}\n"
        self.query_one("#left", Static).update(text)

    def _update_right(self, text: str) -> None:
        self.query_one("#right", Static).update(text)


if __name__ == "__main__":
    app = SessionApp(
        watch_path=Path("solution.py"),
        config=SessionConfig()
    )
    app.run()
