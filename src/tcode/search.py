from textual.app import ComposeResult
from textual.screen import Screen
from textual.widgets import Label, Button

class SearchProblems(Screen):
    def compose(self) -> ComposeResult:
        yield Label("Search Problems")
        yield Button("Back", id="back-button")
        
    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "back-button":
            self.app.pop_screen()