import pytest

from tcode.config import SessionConfig
from tcode.session import SessionApp


def test_session_requires_problem_id(tmp_path):
    with pytest.raises(RuntimeError):
        SessionApp(
            watch_path=tmp_path / "solution.py", config=SessionConfig(problem_id=None)
        )


def test_session_loads_problem_from_config(tmp_path):
    app = SessionApp(
        watch_path=tmp_path / "solution.py", config=SessionConfig(problem_id="0001")
    )
    assert app.active_problem.id == "0001"
