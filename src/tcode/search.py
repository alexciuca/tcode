from textual.app import ComposeResult
from textual.containers import Grid, Horizontal
from textual.events import Click
from textual.screen import Screen
from textual.widgets import Button, Footer, Input, Label, Select, Static

from tcode.config import SessionConfig
from tcode.problems import load_index
from tcode.session import SessionApp

PAGE_SIZE = 20

DIFFICULTIES = [
    ("All Difficulties", "all"),
    ("Easy", "easy"),
    ("Medium", "medium"),
    ("Hard", "hard"),
]


class SearchProblems(Screen):
    CSS_PATH = "assets/search.tcss"

    BINDINGS = [
        ("s", "focus_search", "Search"),
        ("d", "difficulty_filter", "Filter by Difficulty"),
        ("down", "next_problem", "Next Problem"),
        ("up", "prev_problem", "Previous Problem"),
        ("right", "next_page", "Next Page"),
        ("left", "prev_page", "Previous Page"),
        ("enter", "select_problem", "Select Problem"),
        ("q", "quit", "Quit"),
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

    def on_mount(self) -> None:
        cards = self.query(".card")
        if cards:
            cards.first().focus()

    def compose(self) -> ComposeResult:
        with Horizontal(id="search-bar-container"):
            yield Input(placeholder="Search problems...", id="search-bar")
            yield Select(options=DIFFICULTIES, id="difficulty-filter", value="all")
        with Grid(id="problems-grid"):
            for p in self.get_page():
                content = (
                    f"[b] #{p.id} · {p.title}[/b] · {p.difficulty}\n"
                    f"Topics: {', '.join(p.topics)}"
                )
                card = Static(content, classes="card", id=f"problem-{p.id}")
                card.can_focus = True
                yield card
        with Horizontal(id="pagination"):
            yield Button("← Prev", id="prev", disabled=True)
            yield Label(f"Page 1 / {self.total_pages()}", id="page-label")
            yield Button("Next →", id="next")
        yield Footer()

    def on_click(self, event: Click) -> None:
        widget = event.widget
        if isinstance(widget, Static) and widget.has_class("card"):
            problem_id = widget.id.split("-")[1]
            self.app.push_screen(
                SessionApp(
                    watch_path=self.app.watch_path,
                    config=SessionConfig(problem_id=problem_id),
                )
            )

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "next" and self.page < self.total_pages() - 1:
            self.page += 1
            self.rebuild_grid()
        elif event.button.id == "prev" and self.page > 0:
            self.page -= 1
            self.rebuild_grid()

    def on_key(self, event) -> None:
        if event.key == "escape":
            cards = self.query(".card")
            if cards:
                cards.first().focus()

    def on_select_changed(self, event: Select.Changed) -> None:
        if event.select.id == "difficulty-filter":
            all_problems = load_index()
            if event.value == "all":
                self.problems = all_problems
            else:
                self.problems = [
                    p for p in all_problems if p.difficulty.lower() == event.value
                ]
            self.page = 0
            self.rebuild_grid()

    def rebuild_grid(self):
        grid = self.query_one("#problems-grid", Grid)
        for card in grid.query(".card"):
            card.remove()

        def mount_cards():
            for p in self.get_page():
                content = (
                    f"[b] #{p.id} · {p.title}[/b] · {p.difficulty}\n"
                    f"Topics: {', '.join(p.topics)}"
                )
                card = Static(content, classes="card", id=f"problem-{p.id}")
                card.can_focus = True
                grid.mount(card)
            self.query_one("#page-label", Label).update(
                f"Page {self.page + 1} / {self.total_pages()}"
            )
            self.query_one("#prev", Button).disabled = self.page == 0
            self.query_one("#next", Button).disabled = (
                self.page >= self.total_pages() - 1
            )
            cards = self.query(".card")
            if cards:
                cards.first().focus()

        self.call_after_refresh(mount_cards)
