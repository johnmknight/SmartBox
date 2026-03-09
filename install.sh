#!/usr/bin/env bash
# SmartToolbox — Server Install Script
# Run once after cloning: bash install.sh
# Tested on Ubuntu 22.04+ / Debian 12+ / WSL2

set -e
CYAN='\033[0;36m'; GREEN='\033[0;32m'; YELLOW='\033[1;33m'; RED='\033[0;31m'; NC='\033[0m'
info()    { echo -e "${CYAN}[STB]${NC} $*"; }
success() { echo -e "${GREEN}[OK]${NC}  $*"; }
warn()    { echo -e "${YELLOW}[WARN]${NC} $*"; }
die()     { echo -e "${RED}[ERR]${NC}  $*"; exit 1; }

echo ""
echo "  ╔══════════════════════════════════════╗"
echo "  ║   SmartToolbox — Server Installer    ║"
echo "  ╚══════════════════════════════════════╝"
echo ""

# ── Python version check ──────────────────────────────────────────────────
info "Checking Python version..."
PY=$(python3 --version 2>&1 | awk '{print $2}')
PYMAJ=$(echo "$PY" | cut -d. -f1)
PYMIN=$(echo "$PY" | cut -d. -f2)
[[ "$PYMAJ" -ge 3 && "$PYMIN" -ge 11 ]] || die "Python 3.11+ required (found $PY)"
success "Python $PY"

# ── Virtual environment ───────────────────────────────────────────────────
info "Setting up virtual environment..."
if [ ! -d ".venv" ]; then
  python3 -m venv .venv
  success "Created .venv"
else
  warn ".venv already exists — skipping creation"
fi

source .venv/bin/activate
success "Activated .venv"

# ── Dependencies ──────────────────────────────────────────────────────────
info "Installing Python dependencies..."
pip install --quiet --upgrade pip
pip install --quiet -r requirements.txt
success "Dependencies installed"

# ── .env setup ───────────────────────────────────────────────────────────
if [ ! -f ".env" ]; then
  cp .env.example .env
  success ".env created from .env.example"
  warn "IMPORTANT: Edit .env and set NFC_HOST to your server's LAN IP before running"
else
  warn ".env already exists — not overwriting"
fi

# ── Data directory ────────────────────────────────────────────────────────
info "Creating data directories..."
mkdir -p data/photos
success "data/photos ready"

# ── Mosquitto check ───────────────────────────────────────────────────────
info "Checking for Mosquitto MQTT broker..."
if command -v mosquitto &>/dev/null; then
  success "Mosquitto found: $(mosquitto -h 2>&1 | head -1)"
else
  warn "Mosquitto not found. Install with:"
  warn "  sudo apt install mosquitto mosquitto-clients   # Ubuntu/Debian"
  warn "  brew install mosquitto                         # macOS"
  warn "Then: sudo systemctl enable --now mosquitto"
fi

# ── DB init ───────────────────────────────────────────────────────────────
info "Initialising database..."
python3 -c "
import asyncio, sys
sys.path.insert(0, '.')
from server.database import init_db
asyncio.run(init_db())
print('[db] Done')
" && success "Database initialised" || warn "DB init failed — will retry on first server start"

# ── Done ──────────────────────────────────────────────────────────────────
echo ""
echo -e "${GREEN}  ╔══════════════════════════════════════╗${NC}"
echo -e "${GREEN}  ║        Installation complete!        ║${NC}"
echo -e "${GREEN}  ╚══════════════════════════════════════╝${NC}"
echo ""
echo "  Next steps:"
echo "  1. Edit .env — set NFC_HOST to your server LAN IP (e.g. 192.168.4.47)"
echo "  2. Start Mosquitto: sudo systemctl start mosquitto"
echo "  3. Start server:    source .venv/bin/activate && uvicorn server.main:app --host 0.0.0.0 --port 8091 --reload"
echo "  4. Open dashboard:  http://localhost:8091"
echo "  5. Flash firmware to Feather — see docs/FIRMWARE_SETUP.md"
echo ""
