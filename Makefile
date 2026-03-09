.PHONY: help setup install test test-level dev dev-score student-watch \
        score score-private score-team dashboard score-dashboard \
        dashboard-install dashboard-build watch clean \
        scaffold check-team install-hook

.DEFAULT_GOAL := help

# ══════════════════════════════════════════════════════════════════════════════
#  AIDE
# ══════════════════════════════════════════════════════════════════════════════

help:
	@echo ""
	@echo "  ┌─────────────────────────────────────────────────────────────┐"
	@echo "  │          Hackathon Flash Trading — Carnet d'Ordres          │"
	@echo "  └─────────────────────────────────────────────────────────────┘"
	@echo ""
	@printf "  \033[1;34m▸ COMMANDES ÉTUDIANTS\033[0m\n"
	@echo ""
	@printf "    \033[36m%-34s\033[0m %s\n" "make test" "Lancer tous les tests publics"
	@printf "    \033[36m%-34s\033[0m %s\n" "make test-level LEVEL=N" "Tester un palier spécifique (N = 1..6)"
	@printf "    \033[36m%-34s\033[0m %s\n" "make dev-score TEAM=nom" "Calculer les résultats → dashboard"
	@printf "    \033[36m%-34s\033[0m %s\n" "make dev TEAM=nom" "Résultats + ouvrir le dashboard étudiant"
	@printf "    \033[36m%-34s\033[0m %s\n" "make student-watch TEAM=nom" "Relancer les tests toutes les 5s (continu)"
	@printf "    \033[36m%-34s\033[0m %s\n" "make install-hook" "Installer le hook git pre-commit"
	@echo ""
	@printf "  \033[1;33m▸ COMMANDES ADMIN (organisateur)\033[0m\n"
	@echo ""
	@printf "    \033[33m%-34s\033[0m %s\n" "make setup" "Créer le venv et installer les dépendances"
	@printf "    \033[33m%-34s\033[0m %s\n" "make score" "Notation de toutes les équipes (tests publics)"
	@printf "    \033[33m%-34s\033[0m %s\n" "make score-private" "Notation avec les tests privés"
	@printf "    \033[33m%-34s\033[0m %s\n" "make score-team TEAM=nom" "Notation d'une équipe spécifique"
	@printf "    \033[33m%-34s\033[0m %s\n" "make score-dashboard" "Générer le JSON des scores"
	@printf "    \033[33m%-34s\033[0m %s\n" "make dashboard" "Générer les scores + lancer le dashboard"
	@printf "    \033[33m%-34s\033[0m %s\n" "make watch" "Surveillance temps réel (pull + notation 60s)"
	@printf "    \033[33m%-34s\033[0m %s\n" "make dashboard-install" "Installer les dépendances du dashboard"
	@printf "    \033[33m%-34s\033[0m %s\n" "make dashboard-build" "Compiler le dashboard pour la production"
	@printf "    \033[33m%-34s\033[0m %s\n" "make scaffold TEAM=nom" "Créer un dossier de soumission depuis le template"
	@printf "    \033[33m%-34s\033[0m %s\n" "make check-team TEAM=nom" "Valider la soumission d'une équipe (AST)"
	@printf "    \033[33m%-34s\033[0m %s\n" "make clean" "Nettoyer les artefacts de build et caches"
	@echo ""

# ══════════════════════════════════════════════════════════════════════════════
#  ÉTUDIANTS
# ══════════════════════════════════════════════════════════════════════════════

test: ## Lancer tous les tests publics
	python3 -m pytest tests/levels/ -v

test-level: ## Tester un palier spécifique (usage : make test-level LEVEL=3)
	python3 -m pytest tests/levels/test_level$(LEVEL)_validation.py -v

dev-score: ## Calculer les résultats et mettre à jour le dashboard (usage : make dev-score TEAM=mon_equipe)
	python3 -m src.student.runner --team $(TEAM)

dev: ## Lancer les tests une fois et ouvrir le dashboard étudiant (usage : make dev TEAM=mon_equipe)
	python3 -m src.student.runner --team $(TEAM)
	cd frontend && npm run dev -- --open /

student-watch: ## Relancer les tests toutes les 5s (usage : make student-watch TEAM=mon_equipe)
	@echo ""
	@echo "  Surveillance active — les résultats sont écrits dans frontend/public/student-results.json"
	@echo "  Ouvrez http://localhost:5173 dans votre navigateur."
	@echo "  Appuyez sur Ctrl+C pour arrêter."
	@echo ""
	@while true; do \
		python3 -m src.student.runner --team $(TEAM); \
		sleep 5; \
	done

# ══════════════════════════════════════════════════════════════════════════════
#  ADMIN — Installation
# ══════════════════════════════════════════════════════════════════════════════

setup: ## Créer l'environnement virtuel et installer les dépendances
	python3 -m venv venv
	. venv/bin/activate && pip install -r requirements.txt

install: ## Installer les dépendances Python (venv déjà activé)
	pip install -r requirements.txt

# ══════════════════════════════════════════════════════════════════════════════
#  ADMIN — Notation
# ══════════════════════════════════════════════════════════════════════════════

score: ## Notation de toutes les équipes (tests publics uniquement)
	python3 -m src.scoring.runner

score-private: ## Notation avec les tests privés (CSV requis sur cette machine)
	python3 -m src.scoring.runner --private

score-team: ## Notation d'une équipe spécifique (usage : make score-team TEAM=exemple)
	python3 -m src.scoring.runner --private --team $(TEAM)

# ══════════════════════════════════════════════════════════════════════════════
#  ADMIN — Dashboard
# ══════════════════════════════════════════════════════════════════════════════

score-dashboard: ## Générer le JSON des scores pour le dashboard admin
	python3 -m src.scoring.runner --private --output frontend/public/scores.json

dashboard: score-dashboard ## Générer les scores et lancer le serveur de développement
	cd frontend && npm run dev -- --open /admin.html

dashboard-install: ## Installer les dépendances du dashboard (Node.js requis)
	cd frontend && npm install

dashboard-build: ## Compiler le dashboard pour la production
	cd frontend && npm run build

# ══════════════════════════════════════════════════════════════════════════════
#  ADMIN — Surveillance temps réel
# ══════════════════════════════════════════════════════════════════════════════

watch: ## Surveillance temps réel : git pull + notation privée toutes les 60s
	@echo ""
	@echo "  Démarrage de la surveillance en temps réel..."
	@echo "  Le dashboard sera mis à jour dans frontend/public/scores.json"
	@echo "  Appuyez sur Ctrl+C pour arrêter."
	@echo ""
	@while true; do \
		git pull --quiet; \
		python3 -m src.scoring.runner --private --output frontend/public/scores.json; \
		printf "  [%s] Scores mis à jour\n" "$$(date '+%H:%M:%S')"; \
		sleep 60; \
	done

# ══════════════════════════════════════════════════════════════════════════════
#  UTILITAIRES
# ══════════════════════════════════════════════════════════════════════════════

scaffold: ## Créer un dossier de soumission depuis le template (usage: make scaffold TEAM=nom)
	@if [ -z "$(TEAM)" ]; then echo "  Usage : make scaffold TEAM=nom_equipe"; exit 1; fi
	@if [ -d "submissions/$(TEAM)" ]; then echo "  ⚠ Dossier submissions/$(TEAM) existe déjà"; exit 1; fi
	@cp -r submissions/_template submissions/$(TEAM)
	@echo "  ✓ submissions/$(TEAM)/ créé depuis le template"
	@echo "  Les étudiants peuvent maintenant implémenter level1.py … level6.py"

check-team: ## Valider structurellement la soumission d'une équipe (usage: make check-team TEAM=nom)
	python3 -m src.scoring.checker --team $(TEAM)

install-hook: ## Installer le hook git pre-commit (lance les tests publics avant chaque commit)
	@cp scripts/pre-commit .git/hooks/pre-commit
	@chmod +x .git/hooks/pre-commit
	@echo "  ✓ Hook pre-commit installé — les tests publics s'exécuteront avant chaque commit"

clean: ## Nettoyer les artefacts de build et les caches
	find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
	rm -rf .pytest_cache results/ frontend/dist
