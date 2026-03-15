from pathlib import Path
import yaml
import pytest

from src.validation.runner import validate_level, validate_level_csv

PUBLIC_FIXTURES = sorted(Path("tests/fixtures/level1").glob("*.yaml"))
PRIVATE_CSV = Path("Hackathon Ensimag \u2014 Flash Trading Challenge - Palier 1.csv")
PRIVATE_EXPECTED = Path("tests/fixtures_private/level1/palier_expected.json")


def get_teams():
    with open("config/teams.yaml") as f:
        config = yaml.safe_load(f)
    return [team["id"] for team in config["teams"]]

@pytest.mark.parametrize("team", get_teams())
@pytest.mark.parametrize("fixture", PUBLIC_FIXTURES, ids=lambda p: p.stem)
def test_team_level1_public(team, fixture):
    passed, message = validate_level(team, "level1", fixture)
    assert passed, message

@pytest.mark.skipif(
    not PRIVATE_CSV.exists() or not PRIVATE_EXPECTED.exists(),
    reason="Private CSV fixture not available",
)
@pytest.mark.parametrize("team", get_teams())
def test_team_level1_private(team):
    passed, message = validate_level_csv(team, "level1", PRIVATE_CSV, PRIVATE_EXPECTED)
    assert passed, message
