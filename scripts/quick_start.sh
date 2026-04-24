#!/usr/bin/env bash
# quick_start.sh — Start backend + frontend in parallel, clean Ctrl+C shutdown.
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"

# ── Colour helpers ────────────────────────────────────────────────────────────
RED='\033[0;31m'; GREEN='\033[0;32m'; CYAN='\033[0;36m'; BOLD='\033[1m'; NC='\033[0m'
info()  { echo -e "${CYAN}${BOLD}[smart-dispatch]${NC} $*"; }
ok()    { echo -e "${GREEN}✓${NC} $*"; }
err()   { echo -e "${RED}✗${NC} $*" >&2; }

# ── Prereqs check ─────────────────────────────────────────────────────────────
if ! command -v uv &>/dev/null; then
  err "uv not found. Install with: curl -LsSf https://astral.sh/uv/install.sh | sh"
  exit 1
fi
if ! command -v node &>/dev/null; then
  err "node not found. Install Node.js 18+."
  exit 1
fi

# ── Load env ──────────────────────────────────────────────────────────────────
if [ -f .env ]; then
  set -a; source .env; set +a
  ok "Loaded .env"
else
  info "No .env found — using system environment variables."
  info "Copy .env.example to .env and fill in your API key."
fi

# Check for LLM key
if [ -z "${GROQ_API_KEY:-}" ] && [ -z "${ANTHROPIC_API_KEY:-}" ] && [ -z "${OPENAI_API_KEY:-}" ]; then
  err "No LLM API key set. Please set GROQ_API_KEY (or ANTHROPIC_API_KEY / OPENAI_API_KEY) in .env"
  exit 1
fi

# ── PID tracking for clean shutdown ───────────────────────────────────────────
BACKEND_PID=""
FRONTEND_PID=""

cleanup() {
  echo ""
  info "Shutting down..."
  [ -n "$BACKEND_PID" ]  && kill "$BACKEND_PID"  2>/dev/null && ok "Backend stopped"
  [ -n "$FRONTEND_PID" ] && kill "$FRONTEND_PID" 2>/dev/null && ok "Frontend stopped"
  exit 0
}
trap cleanup SIGINT SIGTERM

# ── Backend ───────────────────────────────────────────────────────────────────
info "Starting backend on http://localhost:8000 ..."
uv run python scripts/run_server.py &
BACKEND_PID=$!

# Wait until /health responds
MAX_WAIT=30
for i in $(seq 1 $MAX_WAIT); do
  if curl -sf http://localhost:8000/health &>/dev/null; then
    ok "Backend ready (took ${i}s)"
    break
  fi
  if ! kill -0 "$BACKEND_PID" 2>/dev/null; then
    err "Backend process exited early. Check logs above."
    exit 1
  fi
  sleep 1
done

if ! curl -sf http://localhost:8000/health &>/dev/null; then
  err "Backend didn't respond after ${MAX_WAIT}s."
  kill "$BACKEND_PID" 2>/dev/null
  exit 1
fi

# ── Frontend ──────────────────────────────────────────────────────────────────
info "Starting frontend on http://localhost:5173 ..."
cd frontend
if [ ! -d node_modules ]; then
  info "Installing frontend dependencies..."
  npm install --silent
fi
npm run dev -- --host 0.0.0.0 &
FRONTEND_PID=$!
cd "$ROOT"

ok "Frontend starting..."
echo ""
echo -e "${BOLD}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "  ${GREEN}${BOLD}Dashboard${NC}  →  http://localhost:5173"
echo -e "  ${CYAN}${BOLD}API Docs${NC}   →  http://localhost:8000/docs"
echo -e ""
echo -e "  ${BOLD}Run demo:${NC}  uv run python scripts/demo_story.py"
echo -e "${BOLD}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo ""
info "Press Ctrl+C to stop both servers."

# Wait indefinitely
wait "$BACKEND_PID" "$FRONTEND_PID"
