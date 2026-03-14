from textual.app import App, ComposeResult
from textual.containers import Horizontal
from textual.widgets import Static

class TCodeApp(App):
    def compose(self) -> ComposeResult:
        yield Horizontal(
            Static("left pane", id="left"),
            Static("right pane", id="right"),
        )

    def on_mount(self) -> None:
        self.query_one("#left", Static).update("new text")


if __name__ == "__main__":
    app = TCodeApp()
    app.run()
