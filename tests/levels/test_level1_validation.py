from pathlib import Path

from src.validation.runner import validate_level


def test_example_team_level1_basic():
    fixture = Path("tests/fixtures/level1/case_basic.yaml")
    passed, message = validate_level("example_team", "level1", fixture)
    assert passed, message
