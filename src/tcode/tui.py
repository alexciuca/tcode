from pathlib import Path

from textual.app import App, ComposeResult
from textual.binding import Binding
from textual.containers import Center, Horizontal, Vertical
from textual.widgets import Button, Static

from tcode.config import SessionConfig
from tcode.planner import build_session_plan
from tcode.profile import load_profile
from tcode.search import SearchProblems
from tcode.session import SessionApp

TITLE_ART = """\
 ████████╗ ██████╗ ██████╗ ██████╗ ███████╗
    ██╔══╝██╔════╝██╔═══██╗██╔══██╗██╔════╝
    ██║   ██║     ██║   ██║██║  ██║█████╗  
    ██║   ██║     ██║   ██║██║  ██║██╔══╝  
    ██║   ╚██████╗╚██████╔╝██████╔╝███████╗
    ╚═╝    ╚═════╝ ╚═════╝ ╚═════╝ ╚══════╝"""

SUBTITLE = "Your terminal coding coach"


class TCodeApp(App):
    BINDINGS = [
        Binding("left", "move_left", "Left"),
        Binding("right", "move_right", "Right"),
        Binding("enter", "select", "Select"),
        Binding("q", "quit", "Quit"),
    ]

    def __init__(self, watch_path: Path) -> None:
        super().__init__()
        self.watch_path = watch_path
        self.selected_index = 0

    SCREENS = {"search": SearchProblems}

    CSS = """
    Screen {
        align: center middle;
        background: #1a1a1a;
    }

    #home-container {
        align: center middle;
        width: 100%;
        height: 100%;
        background: #1a1a1a;
    }

    #title-block {
        align: center middle;
        width: 100%;
        height: auto;
        padding: 2 0 1 0;
    }

    #ascii-title {
        text-align: center;
        color: cyan;
        width: 100%;
        height: auto;
        padding: 0 0 1 0;
    }

    #subtitle {
        text-align: center;
        color: #ff8c00;
        width: 100%;
        height: auto;
        padding: 0 0 2 0;
    }

    #buttons-row {
        align: center middle;
        height: auto;
        width: 100%;
        padding: 2 0;
    }

    Button {
        width: 24;
        margin: 0 3;
        background: #2e2e2e;
        border: tall #3e3e3e;
    }

    #search-btn {
        color: cyan;
    }

    #select-btn {
        color: #ff8c00;
    }

    Button:focus {
        background: #3e3e3e;
        border: tall white;
    }

    #search-btn:focus {
        border: tall cyan;
    }

    #select-btn:focus {
        border: tall #ff8c00;
    }

    #footer-credit {
        text-align: center;
        color: #555555;
        width: 100%;
        height: auto;
        padding: 2 0 1 0;
    }
    """

    def compose(self) -> ComposeResult:
        with Vertical(id="home-container"):
            with Center(id="title-block"):
                yield Static(TITLE_ART, id="ascii-title")
                yield Static(SUBTITLE, id="subtitle")

            with Horizontal(id="buttons-row"):
                yield Button("🔍  Search Problems", id="search-btn")
                yield Button("▶   Start Session", id="select-btn")

            with Center():
                yield Static(
                    "Developed by: Alexandru Ciuca & Andrei Cretu",
                    id="footer-credit",
                )

    def on_mount(self) -> None:
        self.buttons = [
            self.query_one("#search-btn", Button),
            self.query_one("#select-btn", Button),
        ]

        self.buttons[self.selected_index].focus()

    def action_move_left(self) -> None:
        self.selected_index = (self.selected_index - 1) % len(self.buttons)
        self.buttons[self.selected_index].focus()

    def action_move_right(self) -> None:
        self.selected_index = (self.selected_index + 1) % len(self.buttons)
        self.buttons[self.selected_index].focus()

    def action_select(self) -> None:
        self.buttons[self.selected_index].press()

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "search-btn":
            self.push_screen(SearchProblems())

        elif event.button.id == "select-btn":
            plan = build_session_plan(load_profile())
            first_problem_id = plan.problem_ids[0]

            self.push_screen(
                SessionApp(
                    watch_path=self.watch_path,
                    config=SessionConfig(problem_id=first_problem_id),
                    problem_ids=plan.problem_ids,
                )
            )
