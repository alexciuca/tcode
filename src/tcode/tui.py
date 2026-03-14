from textual.app import App, ComposeResult
from textual.containers import Horizontal, Vertical, Center
from textual.widgets import Static, Button, RadioButton, RadioSet, Select, Label
from tcode.search import SearchProblems

TOPICS = [
    ("All Topics", "all"),
    ("Arrays", "arrays"),
    ("Loops", "loops"),
    ("Strings", "strings"),
    ("Recursion", "recursion"),
    ("Sorting", "sorting"),
]

class TCodeApp(App):

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
            yield Static("[b][u]🔍 Search Problems[u][b]", id="search")
            yield Static("[b][u]⚙️  Generate Problem[u][b]", id="generate")

        with Center(id="middle"):
            with Vertical(id="middle-inner"):
                
                with RadioSet():
                    yield RadioButton("Easy", value=True)
                    yield RadioButton("Medium")
                    yield RadioButton("Hard")
                yield Select(
                    options=TOPICS,
                )

        with Center(id="bottom"):
            yield Button("Start Session", id="select-btn", variant="primary")
            
    def on_mount(self) -> None:
        self.query_one("#search").can_focus = True
        self.query_one("#generate").can_focus = True

    def on_click(self, event) -> None:
        if event.widget.id == "search":
            self.push_screen(SearchProblems())
        elif event.widget.id == "generate":
            pass
