#!/data/data/com.termux/files/usr/bin/bash
set -euo pipefail

REPO_URL_DEFAULT="https://github.com/your-org/casper-node.git"
INSTALL_DIR_DEFAULT="$HOME/Casper/casper-node"

REPO_URL="${1:-$REPO_URL_DEFAULT}"
INSTALL_DIR="${2:-$INSTALL_DIR_DEFAULT}"

cat <<MSG
[casper-node] Starting Termux bootstrap...
  REPO_URL:   $REPO_URL
  INSTALL_DIR:$INSTALL_DIR
MSG

pkg update -y
pkg upgrade -y
pkg install -y git python nodejs openssh

mkdir -p "$(dirname "$INSTALL_DIR")"
if [ -d "$INSTALL_DIR/.git" ]; then
  echo "[casper-node] Existing repo detected; pulling latest changes..."
  git -C "$INSTALL_DIR" pull --ff-only
else
  echo "[casper-node] Cloning repository..."
  git clone "$REPO_URL" "$INSTALL_DIR"
fi

cd "$INSTALL_DIR"

python -m venv .venv
# shellcheck disable=SC1091
source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -r requirements.txt

if [ -f package.json ]; then
  npm install --no-audit --no-fund
fi

if [ ! -f .env ]; then
  cp .env.example .env
  cat <<'EON'
[casper-node] Created .env from .env.example.
Add your keys before running generate:
  OPENAI_API_KEY=...
  ANTHROPIC_API_KEY=...
EON
fi

mkdir -p memory/logs memory/sessions

cat <<'DONE'
[casper-node] Install complete.

Run commands:
  source .venv/bin/activate
  python cli.py --help
  node index.js --help
  python cli.py build local
DONE
