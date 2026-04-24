.PHONY: help install server frontend demo test test-unit test-slow test-integration test-all eval demo-story reset-db clean lint

# ── Default target ────────────────────────────────────────────────────────────
help:
	@echo ""
	@echo "  Smart City Dynamic Dispatch Grid"
	@echo ""
	@echo "  Setup"
	@echo "    make install          Install Python + Node dependencies"
	@echo ""
	@echo "  Servers"
	@echo "    make server           Start FastAPI backend (localhost:8000)"
	@echo "    make frontend         Start Vite dev server (localhost:5173)"
	@echo "    make demo             Start both backend + frontend together"
	@echo ""
	@echo "  Testing"
	@echo "    make test             Unit tests (no LLM, fast)"
	@echo "    make test-slow        Unit tests including embedding model tests"
	@echo "    make test-integration Integration tests (real LLM — needs API key)"
	@echo "    make test-all         All tests"
	@echo ""
	@echo "  Evaluation"
	@echo "    make eval             Run golden dataset eval (--limit 10 by default)"
	@echo "    make eval-full        Run full 50-case golden dataset eval"
	@echo ""
	@echo "  Demo"
	@echo "    make demo-story       Run scripted 90-second narrated demo"
	@echo ""
	@echo "  Maintenance"
	@echo "    make reset-db         Delete SQLite database and all scenario DBs"
	@echo "    make lint             Run ruff linter"
	@echo "    make clean            Remove __pycache__, *.pyc, reports/, *.db"
	@echo ""

# ── Setup ──────────────────────────────────────────────────────────────────────
install:
	uv sync
	cd frontend && npm install

# ── Servers ────────────────────────────────────────────────────────────────────
server:
	uv run python scripts/run_server.py

frontend:
	cd frontend && npm run dev

demo:
	@bash scripts/quick_start.sh

# ── Testing ────────────────────────────────────────────────────────────────────
test:
	uv run pytest tests/unit/ -v -m "not slow and not integration" --tb=short

test-slow:
	uv run pytest tests/unit/ -v --tb=short

test-integration:
	uv run pytest tests/integration/ -v -m integration --tb=short

test-all:
	uv run pytest tests/ -v --tb=short

# ── Evaluation ─────────────────────────────────────────────────────────────────
eval:
	uv run python -m evaluation.run_eval --limit 10 --output reports/

eval-full:
	uv run python -m evaluation.run_eval --output reports/

# ── Demo story ─────────────────────────────────────────────────────────────────
demo-story:
	uv run python scripts/demo_story.py

# ── Maintenance ────────────────────────────────────────────────────────────────
reset-db:
	@echo "Deleting SQLite databases..."
	@find . -name "*.db" -not -path "./frontend/*" -not -path "./.git/*" -delete
	@echo "Done."

lint:
	uv run ruff check src/ tests/ evaluation/ scripts/ --fix

clean:
	@find . -type d -name "__pycache__" -not -path "./.git/*" -exec rm -rf {} + 2>/dev/null || true
	@find . -name "*.pyc" -not -path "./.git/*" -delete 2>/dev/null || true
	@rm -rf reports/
	@find . -name "*.db" -not -path "./frontend/*" -not -path "./.git/*" -delete 2>/dev/null || true
	@echo "Cleaned."
