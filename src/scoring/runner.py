"""Notation CLI pour le Hackathon Flash Trading.

Usage :
    python3 -m src.scoring.runner [--private] [--team <nom>] [--output <chemin>]

Flags :
    --private           Inclure les fixtures CSV privées
    --team <nom>        Noter une seule équipe
    --output <chemin>   Chemin de sortie JSON (défaut : results/scores.json)

Système de classement :
    1. Palier le plus élevé réussi (consécutivement depuis le palier 1)
    2. Départage : première équipe à avoir validé ce palier (horodatage machine organisateur)
    3. Deuxième départage : nombre total de fixtures réussies
"""
from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional

from src.validation.runner import validate_level, validate_level_csv

LEVELS = [f"level{i}" for i in range(1, 7)]
PUBLIC_FIXTURES = Path("tests/fixtures")
PRIVATE_FIXTURES = Path("tests/fixtures_private")

# Fichiers CSV privés fournis par l'organisateur (un par palier)
PRIVATE_CSVS = {
    f"level{i}": Path(
        f"Hackathon Ensimag \u2014 Flash Trading Challenge - Palier {i}.csv"
    )
    for i in range(1, 7)
}

# Fichier d'horodatage : enregistre quand chaque équipe a validé chaque palier pour la première fois
TIMESTAMPS_FILE = Path("results/timestamps.json")


# ── Gestion des horodatages ──────────────────────────────────────────────────

def load_timestamps() -> Dict[str, Dict[str, str]]:
    """Charge les horodatages de première validation depuis le disque."""
    if TIMESTAMPS_FILE.exists():
        try:
            return json.loads(TIMESTAMPS_FILE.read_text())
        except Exception:
            return {}
    return {}


def save_timestamps(timestamps: Dict[str, Dict[str, str]]) -> None:
    """Persiste les horodatages sur le disque."""
    TIMESTAMPS_FILE.parent.mkdir(parents=True, exist_ok=True)
    TIMESTAMPS_FILE.write_text(json.dumps(timestamps, indent=2))


# ── Notation ─────────────────────────────────────────────────────────────────

def discover_teams(target_team: Optional[str] = None) -> List[str]:
    submissions_dir = Path("submissions")
    teams = []
    for d in sorted(submissions_dir.iterdir()):
        if d.is_dir() and d.name not in ("_template", "__pycache__"):
            if (d / "__init__.py").exists():
                if target_team is None or d.name == target_team:
                    teams.append(d.name)
    return teams


def _score_level(team: str, level: str, include_private: bool) -> Dict:
    fixture_results: List[Dict] = []
    level_pass = True

    # ── Fixtures YAML publiques ──────────────────────────────────────────────
    pub_dir = PUBLIC_FIXTURES / level
    for fixture in sorted(pub_dir.glob("*.yaml")) if pub_dir.exists() else []:
        try:
            passed, message = validate_level(team, level, fixture)
        except ImportError:
            passed, message = False, f"Module introuvable pour {team}/{level}"
        except Exception as exc:
            passed, message = False, f"{type(exc).__name__}: {exc}"

        fixture_results.append({
            "fixture": fixture.name,
            "source": "public",
            "passed": passed,
            "message": message if not passed else "OK",
        })
        if not passed:
            level_pass = False

    # ── Fixture CSV privée ───────────────────────────────────────────────────
    if include_private:
        csv_path = PRIVATE_CSVS.get(level)
        expected_path = PRIVATE_FIXTURES / level / "palier_expected.json"

        if csv_path and csv_path.exists() and expected_path.exists():
            try:
                passed, message = validate_level_csv(team, level, csv_path, expected_path)
            except ImportError:
                passed, message = False, f"Module introuvable pour {team}/{level}"
            except Exception as exc:
                passed, message = False, f"{type(exc).__name__}: {exc}"

            fixture_results.append({
                "fixture": csv_path.name,
                "source": "private",
                "passed": passed,
                "message": message if not passed else "OK",
            })
            if not passed:
                level_pass = False

    if not fixture_results:
        return {
            "passed": False,
            "fixtures_passed": 0,
            "fixtures_total": 0,
            "fixtures": [],
            "error": "Aucune fixture trouvée",
        }

    return {
        "passed": level_pass,
        "fixtures_passed": sum(1 for f in fixture_results if f["passed"]),
        "fixtures_total": len(fixture_results),
        "fixtures": fixture_results,
    }


def score_team(team: str, include_private: bool, timestamps: Dict[str, Dict[str, str]]) -> Dict:
    """Note une équipe sur tous les paliers et met à jour les horodatages de première validation."""
    levels_result: Dict[str, Dict] = {}
    highest_level_passed = 0
    streak = True

    # Horodatages déjà enregistrés pour cette équipe (immuables une fois fixés)
    team_times: Dict[str, str] = dict(timestamps.get(team, {}))
    now = datetime.now().isoformat(timespec="seconds")

    for level in LEVELS:
        result = _score_level(team, level, include_private)
        levels_result[level] = result

        if streak and result.get("passed"):
            highest_level_passed = int(level.replace("level", ""))
            # Enregistrer le premier passage : horodatage machine organisateur
            if level not in team_times:
                team_times[level] = now
                print(
                    f"    [NOUVEAU] {team} valide {level} à {now}",
                    file=sys.stderr,
                )
        else:
            streak = False

    # Persister les nouveaux horodatages
    timestamps[team] = team_times

    return {
        "team": team,
        "highest_level_passed": highest_level_passed,
        "first_pass_times": team_times,
        "total_fixtures_passed": sum(
            r.get("fixtures_passed", 0) for r in levels_result.values()
        ),
        "levels": levels_result,
    }


def rank_teams(results: List[Dict]) -> List[Dict]:
    """Classe les équipes par : palier le plus élevé → premier à valider → fixtures totales."""
    def sort_key(r):
        hlp = r["highest_level_passed"]
        # Heure de première validation du palier le plus élevé (ISO → ordre chronologique naturel)
        # Les équipes sans validation remontent à la fin (chaîne "9999…")
        fpt = r["first_pass_times"].get(f"level{hlp}", "9999") if hlp > 0 else "9999"
        return (
            -hlp,                          # palier le plus élevé = meilleur
            fpt,                           # heure la plus ancienne = meilleur
            -r["total_fixtures_passed"],   # plus de fixtures = meilleur
            r["team"],                     # ordre alphabétique en dernier recours
        )

    return sorted(results, key=sort_key)


# ── Entrée CLI ────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(description="Notation Hackathon Flash Trading")
    parser.add_argument("--private", action="store_true", help="Inclure les fixtures CSV privées")
    parser.add_argument("--team", type=str, default=None, help="Noter une seule équipe")
    parser.add_argument(
        "--output", type=str, default="results/scores.json", help="Chemin de sortie JSON"
    )
    args = parser.parse_args()

    teams = discover_teams(args.team)
    if not teams:
        print(
            f"Aucune équipe trouvée{' correspondant à ' + args.team if args.team else ''}.",
            file=sys.stderr,
        )
        sys.exit(1)

    # Charger les horodatages existants (persistants entre les runs)
    timestamps = load_timestamps()

    print(f"Notation de {len(teams)} équipe(s)...", file=sys.stderr)
    results = []
    for team in teams:
        print(f"  {team}...", file=sys.stderr)
        result = score_team(team, args.private, timestamps)
        results.append(result)
        fpt = result["first_pass_times"].get(f"level{result['highest_level_passed']}", "—")
        print(
            f"    palier={result['highest_level_passed']} "
            f"fixtures={result['total_fixtures_passed']} "
            f"premier_passage={fpt}",
            file=sys.stderr,
        )

    # Sauvegarder les horodatages mis à jour
    save_timestamps(timestamps)

    ranked = rank_teams(results)
    output = {
        "rankings": ranked,
        "metadata": {
            "total_teams": len(teams),
            "include_private": args.private,
            "total_levels": len(LEVELS),
            "scored_at": datetime.now().isoformat(timespec="seconds"),
        },
    }

    out_path = Path(args.output)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(output, indent=2, ensure_ascii=False))
    print(f"\nRésultats écrits dans {out_path}", file=sys.stderr)

    # Affichage terminal
    print("\n=== CLASSEMENT ===", file=sys.stderr)
    print(f"{'#':<4}{'Équipe':<22}{'Palier':<8}{'Validé à':<12}{'Fixtures'}", file=sys.stderr)
    print("-" * 55, file=sys.stderr)
    for i, r in enumerate(ranked, 1):
        hlp = r["highest_level_passed"]
        fpt = r["first_pass_times"].get(f"level{hlp}", "—") if hlp > 0 else "—"
        # Afficher uniquement l'heure (HH:MM:SS) si c'est un ISO timestamp
        display_time = fpt[11:19] if len(fpt) >= 19 else fpt
        print(
            f"{i:<4}{r['team']:<22}{hlp:<8}{display_time:<12}{r['total_fixtures_passed']}",
            file=sys.stderr,
        )


if __name__ == "__main__":
    main()
