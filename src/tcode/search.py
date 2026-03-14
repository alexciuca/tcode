from textual.app import ComposeResult
from textual.screen import Screen
from textual.widgets import Label, Button

class SearchProblems(Screen):
    # TODO: Add list of all problems with pagination (Late : optimize so it doesnt load all 2000+ problems at once, maybe like 20 per page)
    def compose(self) -> ComposeResult:
        yield Label("Search Problems")
        yield Button("Back", id="back-button")
        
    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "back-button":
            self.app.pop_screen()