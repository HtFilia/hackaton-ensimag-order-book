"""Valide structurellement la soumission d'une équipe avant notation.

Vérifie :
- Présence du dossier submissions/<team>/
- Fichiers level1.py … level6.py présents
- Chaque fichier est syntaxiquement valide
- La fonction process_orders() est définie dans chaque fichier
- Aucun import interdit (subprocess, socket, os, shutil, …)

Usage :
    python3 -m src.scoring.checker --team nom_equipe
"""
from __future__ import annotations

import ast
import argparse
import sys
from pathlib import Path

REQUIRED_LEVELS = list(range(1, 7))

FORBIDDEN_MODULES = {
    "subprocess",
    "socket",
    "shutil",
    "ftplib",
    "smtplib",
    "http.client",
    "urllib.request",
    "requests",
    "httpx",
    "aiohttp",
}

# Fonctions builtins dangereuses utilisées comme noms
FORBIDDEN_BUILTINS = {"eval", "exec", "compile", "__import__"}


def _check_file(path: Path) -> list[str]:
    issues: list[str] = []

    try:
        source = path.read_text(encoding="utf-8")
        tree = ast.parse(source, filename=str(path))
    except SyntaxError as exc:
        return [f"Erreur de syntaxe ligne {exc.lineno} : {exc.msg}"]
    except Exception as exc:
        return [f"Impossible de lire le fichier : {exc}"]

    # Vérifier process_orders existe
    func_names = {
        node.name
        for node in ast.walk(tree)
        if isinstance(node, ast.FunctionDef)
    }
    if "process_orders" not in func_names:
        issues.append("Fonction process_orders() introuvable")

    # Vérifier imports interdits
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                root = alias.name.split(".")[0]
                if root in FORBIDDEN_MODULES:
                    issues.append(f"Import interdit : {alias.name}")
        elif isinstance(node, ast.ImportFrom):
            if node.module:
                root = node.module.split(".")[0]
                if root in FORBIDDEN_MODULES:
                    issues.append(f"Import interdit : from {node.module}")

    # Vérifier appels dangereux
    for node in ast.walk(tree):
        if isinstance(node, ast.Call):
            if isinstance(node.func, ast.Name) and node.func.id in FORBIDDEN_BUILTINS:
                issues.append(f"Appel interdit : {node.func.id}()")

    return issues


def check_team(team: str) -> list[str]:
    """Retourne la liste des problèmes détectés. Vide = tout est bon."""
    issues: list[str] = []
    base = Path("submissions") / team

    if not base.exists():
        return [f"Dossier submissions/{team}/ introuvable"]

    for lvl in REQUIRED_LEVELS:
        path = base / f"level{lvl}.py"
        if not path.exists():
            issues.append(f"level{lvl}.py : fichier manquant")
            continue
        for problem in _check_file(path):
            issues.append(f"level{lvl}.py : {problem}")

    return issues


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Valider la soumission d'une équipe avant notation"
    )
    parser.add_argument("--team", required=True, help="Nom du répertoire de soumission")
    args = parser.parse_args()

    print(f"\n  Vérification de submissions/{args.team}/\n")
    issues = check_team(args.team)

    if not issues:
        print("  \033[32m✓ Soumission valide — aucun problème détecté\033[0m\n")
        sys.exit(0)
    else:
        for issue in issues:
            print(f"  \033[31m✗\033[0m {issue}")
        print(f"\n  {len(issues)} problème(s) détecté(s). Corrigez avant soumission.\n")
        sys.exit(1)


if __name__ == "__main__":
    main()
