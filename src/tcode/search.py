from textual.app import ComposeResult
from textual.screen import Screen
from textual.widgets import Label, Button, Static, Input, Select
from textual.containers import Grid, Horizontal
from tcode.problems import load_index

PAGE_SIZE = 20

DIFFICULTIES = [
    ("All Difficulties", "all"),
    ("Easy", "easy"),
    ("Medium", "medium"),
    ("Hard", "hard"),
]

class SearchProblems(Screen):
    CSS_PATH = "assets/search.tcss"

    def __init__(self) -> None:
        super().__init__()
        self.problems = load_index()
        self.page = 0

    def get_page(self):
        start = self.page * PAGE_SIZE
        return self.problems[start:start + PAGE_SIZE]

    def total_pages(self):
        return (len(self.problems) + PAGE_SIZE - 1) // PAGE_SIZE

    def compose(self) -> ComposeResult:
        yield Label("Search Problems", id="title")
        with Horizontal(id="search-bar-container"):
            yield Input(placeholder="Search problems...", id="search-bar")
            yield Select(
                options=DIFFICULTIES,
                id="difficulty-filter",
                value="all"
             )
        with Grid(id="problems-grid"):
            for p in self.get_page():
                yield Static(f"[b] #{p.id} · {p.title}[/b] · {p.difficulty}\nTopics: {', '.join(p.topics)}", classes="card", id=f"problem-{p.id}")
        with Horizontal(id="pagination"):
            yield Button("← Prev", id="prev", disabled=True)
            yield Label(f"Page 1 / {self.total_pages()}", id="page-label")
            yield Button("Next →", id="next")
        yield Button("Back", id="back-button")

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "back-button":
            self.app.pop_screen()
        elif event.button.id == "next" and self.page < self.total_pages() - 1:
            self.page += 1
            self.rebuild_grid()
        elif event.button.id == "prev" and self.page > 0:
            self.page -= 1
            self.rebuild_grid()

    def rebuild_grid(self):
        grid = self.query_one("#problems-grid", Grid)
        grid.remove_children()
        for p in self.get_page():
            grid.mount(Static(f"[b] #{p.id} · {p.title}[/b] · {p.difficulty}\nTopics: {', '.join(p.topics)}", classes="card", id=f"problem-{p.id}"))
        self.query_one("#page-label", Label).update(f"Page {self.page + 1} / {self.total_pages()}")
        self.query_one("#prev", Button).disabled = self.page == 0
        self.query_one("#next", Button).disabled = self.page >= self.total_pages() - 1
