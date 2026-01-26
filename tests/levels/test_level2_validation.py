from pathlib import Path
from src.validation.runner import validate_level

def test_example_team_level2_market():
    fixture = Path("tests/fixtures/level2/case_market.yaml")
    passed, message = validate_level("example_team", "level2", fixture)
    assert passed, message
