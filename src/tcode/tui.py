from pathlib import Path

from textual.app import App, ComposeResult
from textual.containers import Center, Horizontal
from textual.widgets import Button, Static

from tcode.config import SessionConfig
from tcode.planner import build_session_plan
from tcode.profile import load_profile
from tcode.search import SearchProblems
from tcode.session import SessionApp


class TCodeApp(App):
    def __init__(self, watch_path: Path) -> None:
        super().__init__()
        self.watch_path = watch_path

    SCREENS = {"search": SearchProblems}

    CSS = """
    Screen {
        align: center top;
    }

    #top-options {
        align: center top;
        margin-top: 2;
        height: auto;
    }

    #top-options Static {
        width: 30;
        height: 5;
        margin: 0 2;
        content-align: center middle;
    }

    #top-options Static:hover {
        color: cyan;
    }

    #middle-inner {
        align: center middle;
        height: auto;
        width: 60%;
    }

    RadioSet {
        layout: horizontal;
        align: center middle;
        width: 100%;
        margin-bottom: 1;
    }

    Select {
        width: 100%;
        align: center middle;
    }

    Select {
        width: 30;
        align: center middle;
    }

    #bottom {
        align: center bottom;
        margin-top: 2;
        margin-bottom: 2;
        height: auto;
        width: 100%;
    }

    #select-btn {
        width: 20;
    }
    """

    def compose(self) -> ComposeResult:
        with Horizontal(id="top-options"):
            yield Static("[b][u]Search Problems[/u][/b]", id="search")

        with Center(id="bottom"):
            yield Button("Start Session", id="select-btn", variant="primary")

    def on_mount(self) -> None:
        self.query_one("#search").can_focus = True

    def on_click(self, event) -> None:
        if event.widget.id == "search":
            self.push_screen(SearchProblems())

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id != "select-btn":
            return
        plan = build_session_plan(load_profile())
        first_problem_id = plan.problem_ids[0]
        self.push_screen(
            SessionApp(
                watch_path=self.watch_path,
                config=SessionConfig(problem_id=first_problem_id),
                problem_ids=plan.problem_ids,
            )
        )
