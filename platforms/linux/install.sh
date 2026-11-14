#!/usr/bin/env bash
set -euo pipefail

PROJECT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
VENV_DIR="$PROJECT_DIR/.venv"

echo "[*] Detectando gestor de paquetes..."
if command -v apt &>/dev/null; then
    sudo apt update
    sudo apt install -y python3 python3-pip python3-venv libyara-dev
elif command -v dnf &>/dev/null; then
    sudo dnf install -y python3 python3-pip yara-devel gcc make
elif command -v pacman &>/dev/null; then
    sudo pacman -S --noconfirm python python-pip yara
else
    echo "[!] Gestor no reconocido. Instala python3, pip y libyara manualmente."
fi

echo "[*] Creando entorno virtual en $VENV_DIR"
python3 -m venv "$VENV_DIR"
source "$VENV_DIR/bin/activate"
pip install --upgrade pip
pip install -r "$PROJECT_DIR/requirements.txt"

echo "[*] Registrando servicio systemd de usuario..."
mkdir -p "$HOME/.config/systemd/user"
cat > "$HOME/.config/systemd/user/privacy-guard.service" << UNIT
[Unit]
Description=Privacy Guard Endpoint Agent
After=network.target

[Service]
Type=simple
WorkingDirectory=$PROJECT_DIR
ExecStart=$VENV_DIR/bin/python $PROJECT_DIR/main.py --guard
Restart=on-failure
RestartSec=10

[Install]
WantedBy=default.target
UNIT

systemctl --user daemon-reload
systemctl --user enable --now privacy-guard.service

echo "[OK] Listo. Estado: systemctl --user status privacy-guard"
