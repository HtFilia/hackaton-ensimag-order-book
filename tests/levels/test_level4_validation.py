from pathlib import Path

import pytest

from src.validation.runner import validate_level, validate_level_csv

PUBLIC_FIXTURES = sorted(Path("tests/fixtures/level4").glob("*.yaml"))
PRIVATE_CSV = Path("Hackathon Ensimag \u2014 Flash Trading Challenge - Palier 4.csv")
PRIVATE_EXPECTED = Path("tests/fixtures_private/level4/palier_expected.json")


@pytest.mark.parametrize("fixture", PUBLIC_FIXTURES, ids=lambda p: p.stem)
def test_example_team_level4_public(fixture):
    passed, message = validate_level("example_team", "level4", fixture)
    assert passed, message


@pytest.mark.skipif(
    not PRIVATE_CSV.exists() or not PRIVATE_EXPECTED.exists(),
    reason="Private CSV fixture not available",
)
def test_example_team_level4_private():
    passed, message = validate_level_csv("example_team", "level4", PRIVATE_CSV, PRIVATE_EXPECTED)
    assert passed, message
