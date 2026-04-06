import re
import time
from pathlib import Path

from textual.app import ComposeResult
from textual.containers import Horizontal
from textual.screen import Screen
from textual.widgets import Button, Footer, Header, Static
from watchdog.events import FileSystemEventHandler
from watchdog.observers import Observer

from tcode.config import SessionConfig
from tcode.llm import check_complexity, explain_failure, get_hint
from tcode.problems import load_problem_by_id


class _file_handler(FileSystemEventHandler):
    def __init__(self, file: Path, callback):
        self.file = file.resolve()
        self.callback = callback
        self.last_fired = 0

    def on_modified(self, event):
        if Path(event.src_path).resolve() == self.file:
            now = time.time()
            if now - self.last_fired < 0.5:
                return
            self.last_fired = now
            self.callback()


class SessionApp(Screen):
    CSS_PATH = "assets/tcode.tcss"

    BINDINGS = [
        ("h", "hint", "Hint"),
        ("enter", "run", "Run"),
        ("q", "quit", "Quit"),
    ]

    def __init__(self, watch_path: Path, config: SessionConfig) -> None:
        super().__init__()
        self.config = config
        self.watch_path = watch_path
        self._right_content = ""
        self._llm_loading = False
        self.hints_used = 0
        # HARDCODED! code_snapshot, replace when watchdog impletemented
        self.code_snapshot = ""
        self._startup_warning: str | None = None
        if config.problem_id is None:
            raise RuntimeError("No problem selected.")
        try:
            self.active_problem = load_problem_by_id(config.problem_id)
        except FileNotFoundError:
            self._startup_warning = f"Problem {config.problem_id} not found."
            raise

    def compose(self) -> ComposeResult:
        yield Header()
        yield Horizontal(
            Static("", id="left"),
            Static("", id="right"),
        )
        yield Footer()
        yield Button("Test", id="test-button")
        yield Button("Back", id="back-button")

    def action_hint(self) -> None:
        if self._llm_loading:
            return
        if self.hints_used >= 4:
            self._update_right(
                "Maximum hints reached.\n\n"
                "Try working through it — you have all the information you need."
            )
            return
        self._llm_loading = True
        self._update_right("Thinking...")
        self.run_worker(self._fetch_hint, thread=True)

    def _fetch_hint(self) -> None:
        try:
            result = get_hint(
                code=self.code_snapshot,
                problem=self.active_problem,
                hints_used=self.hints_used,
            )
            self.hints_used += 1
            self.app.call_from_thread(
                self._update_right,
                f"Hint {self.hints_used}/4\n{'─' * 45}\n\n{result.message}",
            )
        except Exception as e:
            self.app.call_from_thread(self._update_right, f"Error getting hint: {e}")
        finally:
            self._llm_loading = False

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "back-button":
            self.app.pop_screen()
        elif event.button.id == "test-button":
            print("Run tests (not implemented)")

    def on_mount(self) -> None:
        self._update_left()
        self._update_right(
            "Ready. Save your file to begin.\n\n"
            + "Keys:\n"
            + "  h      → hint\n"
            + "  enter  → run tests\n"
            + "  q      → back"
        )
        self._start_watching()

    # setup watchdog file watcher
    def _start_watching(self) -> None:
        handler = _file_handler(self.watch_path, self._on_file_saved)
        self.observer = Observer()
        self.observer.schedule(handler, str(self.watch_path.parent), recursive=False)
        self.observer.start()

    # impoleemnt ai

    def _on_file_saved(self) -> None:
        self.code_snapshot = self.watch_path.read_text()
        self.app.call_from_thread(
            self._update_right,
            "File saved! Checking code with AI for any major issues ...",
        )
        # self.app.call_from_thread(self.run_worker, self._analyze_code, thread=True)
        self.app.call_from_thread(self.run_worker, self._check_complexity, thread=True)

    # def _analyze_code(self) -> None:
    #     try:
    #         result = explain_failure(
    #             code=self.code_snapshot,
    #             problem=self.active_problem,
    #             test_output=self._test_output if hasattr(self, "_test_output") else "",
    #         )
    #         self.app.call_from_thread(
    #             self._update_right,
    #             f"AI Code Analysis:\n{'─' * 45}\n\n{result.message}",
    #         )
    #     except Exception as e:
    #         self.app.call_from_thread(self._update_right, f"Error analyzing code: {e}")

    def _check_complexity(self) -> None:
        try:
            result = check_complexity(
                code=self.code_snapshot, problem=self.active_problem
            )
            self.app.call_from_thread(
                self._update_right,
                f"AI Complexity Analysis:\n{'─' * 45}\n\n{result.complexity_estimate}",
            )
        except Exception as e:
            self.app.call_from_thread(
                self._update_right, f"Error checking complexity: {e}"
            )

    def on_unmount(self) -> None:
        if hasattr(self, "observer"):
            self.observer.stop()
            self.observer.join()

    def _clean_description(self, description: str) -> str:
        for marker in ["Example 1:", "Example 2:", "Examples:", "Constraints:"]:
            if marker in description:
                description = description[: description.index(marker)].strip()
                break
        return description

    def _clean_constraint(self, constraint: str) -> str:
        return re.sub(r"10(\d+)", lambda m: f"10^{m.group(1)}", constraint)

    def _update_left(self) -> None:
        p = self.active_problem
        description = self._clean_description(p.description)
        text = (
            f"{p.title}   #{p.id} · {p.difficulty}\n"
            f"{'─' * 45}\n"
            f"Topics: {', '.join(p.topics)}\n\n"
            f"Description:\n{description}\n\n"
        )
        if p.examples:
            text += "Examples:\n"
            for ex in p.examples:
                text += f"{ex['example_text']}\n\n"
        if p.constraints:
            text += "Constraints:\n"
            for c in p.constraints:
                text += f"  · {self._clean_constraint(c)}\n"
        self.query_one("#left", Static).update(text)

    def _update_right(self, text: str) -> None:
        self._right_content += f"\n\n{text}" if self._right_content else text
        self.query_one("#right", Static).update(self._right_content)
