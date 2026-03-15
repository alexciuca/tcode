import pytest

from tcode.problems import load_problem_by_id


def test_load_problem_by_id_two_sum():
    problem = load_problem_by_id("0001")
    assert problem.id == "0001"
    assert problem.slug == "two-sum"
    assert "Two Sum" in problem.title


def test_load_problem_by_id_missing_raises():
    with pytest.raises(FileNotFoundError):
        load_problem_by_id("9999")
