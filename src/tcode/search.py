from pathlib import Path

from textual.app import ComposeResult
from textual.containers import Horizontal, Vertical
from textual.events import Click
from textual.screen import Screen
from textual.widgets import Footer, Input, Label, Select, Static

from tcode.config import SessionConfig
from tcode.problems import load_index, load_problem_by_id
from tcode.session import SessionApp
from tcode.solution_file import write_starter_code_if_needed

PAGE_SIZE = 20

DIFFICULTIES = [
    ("All Difficulties", "all"),
    ("Easy", "easy"),
    ("Medium", "medium"),
    ("Hard", "hard"),
]

DIFFICULTY_TAG = {
    "easy": "[green]● Easy[/green]",
    "medium": "[yellow]● Medium[/yellow]",
    "hard": "[red]● Hard[/red]",
}


class SearchProblems(Screen):
    CSS_PATH = str(Path(__file__).with_name("assets") / "search.tcss")

    BINDINGS = [
        ("s", "focus_search", "Search"),
        ("d", "difficulty_filter", "Filter"),
        ("down", "next_problem", "Next"),
        ("up", "prev_problem", "Prev"),
        ("right", "next_page", "Next Page"),
        ("left", "prev_page", "Prev Page"),
        ("enter", "select_problem", "Open"),
        ("q", "quit", "Back"),
    ]

    def action_next_problem(self) -> None:
        self.focus_next()

    def action_prev_problem(self) -> None:
        self.focus_previous()

    def action_next_page(self) -> None:
        if self.page < self.total_pages() - 1:
            self.page += 1
            self.rebuild_grid()

    def action_prev_page(self) -> None:
        if self.page > 0:
            self.page -= 1
            self.rebuild_grid()

    def action_focus_search(self) -> None:
        self.query_one("#search-bar", Input).focus()

    def action_difficulty_filter(self) -> None:
        self.query_one("#difficulty-filter", Select).focus()

    def action_select_problem(self) -> None:
        focused = self.focused
        if isinstance(focused, Static) and focused.has_class("card"):
            problem_id = focused.id.split("-")[1]
            problem = load_problem_by_id(problem_id)
            write_starter_code_if_needed(self.app.watch_path, problem.starter_code)
            self.app.push_screen(
                SessionApp(
                    watch_path=self.app.watch_path,
                    config=SessionConfig(problem_id=problem_id),
                )
            )

    def action_quit(self) -> None:
        self.app.pop_screen()

    def __init__(self) -> None:
        super().__init__()
        self.problems = load_index()
        self.page = 0

    def get_page(self):
        start = self.page * PAGE_SIZE
        return self.problems[start : start + PAGE_SIZE]

    def total_pages(self):
        return (len(self.problems) + PAGE_SIZE - 1) // PAGE_SIZE

    def _make_card(self, p) -> Static:
        diff_tag = DIFFICULTY_TAG.get(p.difficulty.lower(), p.difficulty)
        topics_short = ", ".join(p.topics[:3])
        if len(p.topics) > 3:
            topics_short += f" +{len(p.topics) - 3}"
        content = (
            f"[bold cyan]#{p.id}[/bold cyan]  [bold]{p.title}[/bold]\n"
            f"{diff_tag}\n"
            f"[dim]{topics_short}[/dim]"
        )
        card = Static(content, classes="card", id=f"problem-{p.id}")
        card.can_focus = True
        return card

    def compose(self) -> ComposeResult:
        yield Static(
            "[bold cyan]  SEARCH PROBLEMS[/bold cyan]",
            id="page-header",
        )
        with Horizontal(id="search-bar-container"):
            yield Input(
                placeholder="  🔍  Filter by title or topic...", id="search-bar"
            )
            yield Select(options=DIFFICULTIES, id="difficulty-filter", value="all")
        yield Static("", id="results-info")
        with Vertical(id="problems-grid-wrapper"):
            with Horizontal(id="problems-grid"):
                for p in self.get_page():
                    yield self._make_card(p)
        with Horizontal(id="pagination"):
            yield Static("◀", id="prev-page-btn", classes="page-btn")
            yield Label(
                f"  {self.page + 1} / {self.total_pages()}  ",
                id="page-label",
            )
            yield Static("▶", id="next-page-btn", classes="page-btn")
        yield Footer()

    def on_mount(self) -> None:
        self._update_results_info()
        cards = self.query(".card")
        if cards:
            cards.first().focus()

    def _update_results_info(self) -> None:
        start = self.page * PAGE_SIZE + 1
        end = min((self.page + 1) * PAGE_SIZE, len(self.problems))
        total = len(self.problems)
        self.query_one("#results-info", Static).update(
            f"[dim]Showing [bold]{start}–{end}[/bold] of [bold]{total}[/bold] problems[/dim]"
        )

    def on_click(self, event: Click) -> None:
        widget = event.widget
        if isinstance(widget, Static) and widget.has_class("card"):
            problem_id = widget.id.split("-")[1]
            problem = load_problem_by_id(problem_id)
            write_starter_code_if_needed(self.app.watch_path, problem.starter_code)
            self.app.push_screen(
                SessionApp(
                    watch_path=self.app.watch_path,
                    config=SessionConfig(problem_id=problem_id),
                )
            )
        elif isinstance(widget, Static) and widget.id == "prev-page-btn":
            self.action_prev_page()
        elif isinstance(widget, Static) and widget.id == "next-page-btn":
            self.action_next_page()

    def on_key(self, event) -> None:
        if event.key == "escape":
            cards = self.query(".card")
            if cards:
                cards.first().focus()

    def on_input_changed(self, event: Input.Changed) -> None:
        if event.input.id == "search-bar":
            query = event.value.lower().strip()
            all_problems = load_index()
            diff_widget = self.query_one("#difficulty-filter", Select)
            diff_val = diff_widget.value

            filtered = all_problems
            if diff_val != "all":
                filtered = [p for p in filtered if p.difficulty.lower() == diff_val]
            if query:
                filtered = [
                    p
                    for p in filtered
                    if query in p.title.lower()
                    or any(query in t.lower() for t in p.topics)
                ]
            self.problems = filtered
            self.page = 0
            self.rebuild_grid()

    def on_select_changed(self, event: Select.Changed) -> None:
        if event.select.id == "difficulty-filter":
            all_problems = load_index()
            query = self.query_one("#search-bar", Input).value.lower().strip()

            filtered = all_problems
            if event.value != "all":
                filtered = [p for p in filtered if p.difficulty.lower() == event.value]
            if query:
                filtered = [
                    p
                    for p in filtered
                    if query in p.title.lower()
                    or any(query in t.lower() for t in p.topics)
                ]
            self.problems = filtered
            self.page = 0
            self.rebuild_grid()

    def rebuild_grid(self):
        grid = self.query_one("#problems-grid", Horizontal)
        for card in grid.query(".card"):
            card.remove()

        def mount_cards():
            for p in self.get_page():
                grid.mount(self._make_card(p))
            self.query_one("#page-label", Label).update(
                f"  {self.page + 1} / {self.total_pages()}  "
            )
            self._update_results_info()
            cards = self.query(".card")
            if cards:
                cards.first().focus()

        self.call_after_refresh(mount_cards)
