import re
import time
from datetime import datetime
from pathlib import Path

from textual.app import ComposeResult
from textual.containers import Horizontal, ScrollableContainer
from textual.screen import Screen
from textual.widgets import Footer, Header, RichLog, TextArea
from watchdog.events import FileSystemEventHandler
from watchdog.observers import Observer

from tcode.config import SessionConfig
from tcode.llm import check_complexity, get_hint
from tcode.problems import load_problem_by_id
from tcode.profile import (
    load_profile,
    mark_problem_seen,
    record_hint,
    record_test_run,
    save_profile,
)
from tcode.runner import format_results, run_tests
from tcode.solution_file import write_starter_code_if_needed

PANE_IDS = ("#left-scroll", "#right-scroll")


class _file_handler(FileSystemEventHandler):
    def __init__(self, file: Path, callback):
        self.file = file.resolve()
        self.callback = callback
        self.last_fired = 0

    def on_modified(self, event):
        if getattr(event, "is_directory", False):
            return
        if Path(event.src_path).resolve() == self.file:
            now = time.time()
            if now - self.last_fired < 0.5:
                return
            self.last_fired = now
            self.callback()

    def on_created(self, event):
        self.on_modified(event)


class SessionApp(Screen):
    CSS_PATH = str(Path(__file__).with_name("assets") / "tcode.tcss")

    BINDINGS = [
        ("h", "hint", "Hint"),
        ("c", "complexity", "Complexity"),
        ("r", "reset_hints", "Reset Hints"),
        ("tab", "toggle_focus", "Switch Pane"),
        ("enter", "run", "Run"),
        ("n", "next_problem", "Next"),
        ("p", "prev_problem", "Previous"),
        ("q", "quit", "Quit"),
    ]

    def __init__(
        self,
        watch_path: Path,
        config: SessionConfig,
        problem_ids: list[str] | None = None,
    ) -> None:
        super().__init__()
        if config.problem_id is None:
            raise RuntimeError("No problem selected.")
        self.config = config
        self.watch_path = watch_path
        self.problem_ids = problem_ids or [config.problem_id]
        if config.problem_id not in self.problem_ids:
            self.problem_ids.insert(0, config.problem_id)
        self.current_problem_index = self.problem_ids.index(config.problem_id)
        self._llm_loading = False
        self._complexity_running = False
        self._test_running = False
        self.hints_used = 0
        self._last_failing_cases: set[int] = set()
        self._session_attempts: set[str] = set()
        self._session_passes: set[str] = set()
        self._session_complete = False
        self._ignore_file_events_until = 0.0
        self.code_snapshot = ""
        self._focused_pane = 1
        self._startup_warning: str | None = None
        try:
            self.active_problem = load_problem_by_id(config.problem_id)
        except FileNotFoundError:
            self._startup_warning = f"Problem {config.problem_id} not found."
            raise

    def compose(self) -> ComposeResult:
        yield Header()
        yield Horizontal(
            ScrollableContainer(
                TextArea("", id="left", read_only=True), id="left-scroll"
            ),
            ScrollableContainer(
                RichLog(id="right", markup=True, wrap=True), id="right-scroll"
            ),
        )
        yield Footer()

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

    def action_run(self) -> None:
        if self._test_running:
            return
        self._test_running = True
        self._update_right("Running tests...")
        self.run_worker(self._execute_tests, thread=True)

    def _fetch_hint(self) -> None:
        try:
            result = get_hint(
                code=self.code_snapshot,
                problem=self.active_problem,
                hints_used=self.hints_used,
            )
            self.hints_used += 1
            self._record_hint_used()
            self.app.call_from_thread(self._refresh_coach_title)
            self.app.call_from_thread(
                self._update_right,
                f"Hint {self.hints_used}/4\n{'─' * 45}\n\n{result.message}",
            )
        except Exception as e:
            self.app.call_from_thread(self._update_right, f"Error getting hint: {e}")
        finally:
            self._llm_loading = False

    def _execute_tests(self) -> None:
        try:
            if not self.active_problem.test_cases:
                self.app.call_from_thread(
                    self._update_right,
                    "No test cases available for this problem.",
                )
                return

            results = run_tests(self.code_snapshot, self.active_problem)
            passed = all(r.passed for r in results)
            self._session_attempts.add(self.active_problem.id)
            if passed:
                self._session_passes.add(self.active_problem.id)
            self._record_test_results(passed)
            summary = format_results(results)
            self.app.call_from_thread(self._update_right, summary)
        except Exception as e:
            self.app.call_from_thread(self._update_right, f"Error: {e}")
        finally:
            self._test_running = False

    def action_complexity(self) -> None:
        if self._complexity_running:
            return
        self._refresh_code_snapshot()
        self._complexity_running = True
        self._update_right("Checking complexity...")
        self.run_worker(self._check_complexity, thread=True)

    def action_reset_hints(self) -> None:
        self.hints_used = 0
        self._refresh_coach_title()
        self._update_right("Hint history reset. You have 4 hints available.")

    def action_toggle_focus(self) -> None:
        self._focused_pane = 1 - self._focused_pane
        self.query_one(PANE_IDS[self._focused_pane]).focus()

    def action_next_problem(self) -> None:
        self._switch_problem(1)

    def action_prev_problem(self) -> None:
        self._switch_problem(-1)

    def action_quit(self) -> None:
        self.app.pop_screen()

    def on_mount(self) -> None:
        p = self.active_problem
        for pane_id in PANE_IDS:
            self.query_one(pane_id).can_focus = True
        self.query_one("#left-scroll").border_title = f" {p.title} · {p.difficulty} "
        archived_path = self._prepare_initial_solution_file()
        self._refresh_coach_title()
        self._update_left()
        self._mark_current_problem_seen()
        self._refresh_code_snapshot()
        if self.watch_path.exists():
            message = (
                "Ready. Press Enter to run tests, c for complexity, "
                "or h for a hint.\n\n"
                "Your file is being watched, so every time you save, "
                "your code's time complexity will be analyzed to help you "
                "find the fastest solution."
            )
            if archived_path:
                message += f"\n\nPrevious file saved to:\n{archived_path}"
            self._update_right(message)
        else:
            self._update_right("Save your file to begin.")
        self._start_watching()

    def _refresh_coach_title(self) -> None:
        remaining = 4 - self.hints_used
        self.query_one(
            "#right-scroll"
        ).border_title = (
            f" Coach  ·  {remaining} hint{'s' if remaining != 1 else ''} remaining "
        )

    def _mark_current_problem_seen(self) -> None:
        profile = load_profile()
        mark_problem_seen(profile, self.active_problem.id)
        save_profile(profile)

    def _record_hint_used(self) -> None:
        profile = load_profile()
        record_hint(profile, self.active_problem.topics)
        save_profile(profile)

    def _record_test_results(self, passed: bool) -> None:
        profile = load_profile()
        record_test_run(profile, self.active_problem.topics, passed)
        mark_problem_seen(profile, self.active_problem.id)
        save_profile(profile)

    def _prepare_initial_solution_file(self) -> Path | None:
        if len(self.problem_ids) <= 1:
            write_starter_code_if_needed(
                self.watch_path, self.active_problem.starter_code
            )
            return None

        archived_path = self._archive_current_solution()
        self._write_active_starter(overwrite=True)
        return archived_path

    def _start_watching(self) -> None:
        if not self.watch_path.parent.exists():
            self._update_right(f"Cannot watch missing folder: {self.watch_path.parent}")
            return
        handler = _file_handler(self.watch_path, self._on_file_saved)
        self.observer = Observer()
        self.observer.schedule(handler, str(self.watch_path.parent), recursive=False)
        self.observer.start()

    def _on_file_saved(self) -> None:
        if time.time() < self._ignore_file_events_until:
            return
        self._refresh_code_snapshot()
        self.app.call_from_thread(
            self._update_right, "File saved! Checking complexity..."
        )
        self.app.call_from_thread(self.run_worker, self._check_complexity, thread=True)

    def _refresh_code_snapshot(self) -> None:
        try:
            self.code_snapshot = self.watch_path.read_text(encoding="utf-8")
        except FileNotFoundError:
            self.code_snapshot = ""
        except OSError:
            self.code_snapshot = ""

    def _check_complexity(self) -> None:
        try:
            result = check_complexity(
                code=self.code_snapshot, problem=self.active_problem
            )
            prefix = "⚠ " if result.risk_flag else "✓ "
            self.app.call_from_thread(
                self._update_right,
                f"Complexity: {prefix}{result.complexity_estimate}\n{'─' * 45}\n\n{result.explanation}",
            )
        except Exception as e:
            self.app.call_from_thread(
                self._update_right, f"Error checking complexity: {e}"
            )
        finally:
            self._complexity_running = False

    def _switch_problem(self, step: int) -> None:
        if len(self.problem_ids) <= 1:
            self._update_right("No other problems in this session.")
            return

        next_index = self.current_problem_index + step
        if next_index >= len(self.problem_ids):
            self._complete_session()
            return
        if next_index < 0:
            self._update_right("No more problems in that direction.")
            return

        archived_path = self._archive_current_solution()
        self.current_problem_index = next_index
        problem_id = self.problem_ids[self.current_problem_index]
        self.config.problem_id = problem_id
        self.active_problem = load_problem_by_id(problem_id)
        self.hints_used = 0
        self._refresh_coach_title()
        self.query_one(
            "#left-scroll"
        ).border_title = (
            f" {self.active_problem.title} · {self.active_problem.difficulty} "
        )
        self._write_active_starter(overwrite=True)
        self._refresh_code_snapshot()
        self._update_left()
        self._mark_current_problem_seen()
        message = f"Switched to {self.active_problem.title}."
        if archived_path:
            message += f"\n\nPrevious solution saved to:\n{archived_path}"
        message += "\n\nThe watched file now contains the new starter code."
        self._update_right(message)

    def _write_active_starter(self, overwrite: bool) -> bool:
        starter_code = self.active_problem.starter_code
        content = starter_code.rstrip() + "\n" if starter_code.strip() else ""
        self.watch_path.parent.mkdir(parents=True, exist_ok=True)
        if not overwrite:
            return write_starter_code_if_needed(self.watch_path, starter_code)
        self._ignore_file_events_until = time.time() + 1.0
        self.watch_path.write_text(content, encoding="utf-8")
        return True

    def _archive_current_solution(self) -> Path | None:
        self._refresh_code_snapshot()
        if not self.code_snapshot.strip():
            return None

        submissions_dir = Path.home() / ".tcode" / "submissions"
        submissions_dir.mkdir(parents=True, exist_ok=True)
        timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
        archive_path = (
            submissions_dir
            / f"{timestamp}-{self.active_problem.id}-{self.active_problem.slug}.py"
        )
        archive_path.write_text(self.code_snapshot, encoding="utf-8")
        return archive_path

    def _complete_session(self) -> None:
        if self._session_complete:
            self._update_right("Session already complete. Press q to return home.")
            return

        archived_path = self._archive_current_solution()
        self._session_complete = True
        attempted = len(self._session_attempts)
        passed = len(self._session_passes)
        total = len(self.problem_ids)
        message = (
            "Session complete.\n"
            f"You attempted {attempted}/{total} problems.\n"
            f"You passed {passed}/{total} problems.\n"
            "Your profile has been updated.\n"
            "Press q to return home."
        )
        if archived_path:
            message += f"\n\nFinal solution saved to:\n{archived_path}"
        self._update_right(message)

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
        sep = f"\n{'─' * 45}\n"
        text = self._format_session_plan()
        text += f"{sep}\nTopics: {', '.join(p.topics)}\n{sep}\n{description}\n"
        if p.examples:
            text += f"{sep}\nExamples\n\n"
            for ex in p.examples:
                text += f"{ex['example_text']}\n\n"
        if p.constraints:
            text += f"{sep}\nConstraints\n\n"
            for c in p.constraints:
                text += f"  · {self._clean_constraint(c)}\n"
        if p.starter_code:
            text += f"{sep}\nStarter code\n\n{p.starter_code}\n"
        self.query_one("#left", TextArea).load_text(text)

    def _format_session_plan(self) -> str:
        if len(self.problem_ids) <= 1:
            return ""

        lines = ["Today's Session", ""]
        for i, problem_id in enumerate(self.problem_ids):
            marker = "►" if i == self.current_problem_index else "○"
            problem = load_problem_by_id(problem_id)
            lines.append(f"{marker} {problem.title} · {problem.difficulty}")
        return "\n".join(lines)

    def _update_right(self, text: str) -> None:
        log = self.query_one("#right", RichLog)
        log.write(text)
        self.query_one("#right-scroll", ScrollableContainer).scroll_end(animate=False)
