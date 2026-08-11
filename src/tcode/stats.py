from pathlib import Path

from textual.app import ComposeResult
from textual.binding import Binding
from textual.containers import Horizontal, Vertical
from textual.events import Click
from textual.screen import Screen
from textual.widgets import Footer, Input, Label, Select, Static

class LocalProfileStats(Screen):
    CSS_PATH = str(Path(__file__).with_name("assets") / "stats.tcss")
    
    BINDINGS = [
        Binding("q", "quit", "Back")
    ]
    
    def compose(self) -> ComposeResult:
        yield Static("stats page")