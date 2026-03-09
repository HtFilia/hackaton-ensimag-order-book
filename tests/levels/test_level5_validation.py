from pathlib import Path

import pytest

from src.validation.runner import validate_level, validate_level_csv

PUBLIC_FIXTURES = sorted(Path("tests/fixtures/level5").glob("*.yaml"))
PRIVATE_CSV = Path("Hackathon Ensimag \u2014 Flash Trading Challenge - Palier 5.csv")
PRIVATE_EXPECTED = Path("tests/fixtures_private/level5/palier_expected.json")


@pytest.mark.parametrize("fixture", PUBLIC_FIXTURES, ids=lambda p: p.stem)
def test_example_team_level5_public(fixture):
    passed, message = validate_level("example_team", "level5", fixture)
    assert passed, message


@pytest.mark.skipif(
    not PRIVATE_CSV.exists() or not PRIVATE_EXPECTED.exists(),
    reason="Private CSV fixture not available",
)
def test_example_team_level5_private():
    passed, message = validate_level_csv("example_team", "level5", PRIVATE_CSV, PRIVATE_EXPECTED)
    assert passed, message
