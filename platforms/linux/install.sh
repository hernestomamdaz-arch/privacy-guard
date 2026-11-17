#!/usr/bin/env bash
set -euo pipefail

PROJECT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
VENV_DIR="$PROJECT_DIR/.venv"

echo "========================================================"
echo "   🛡️ Instalador Automático de Privacy Guard (Linux)   "
echo "========================================================"

echo "[*] Instalando dependencias del sistema..."
if command -v apt &>/dev/null; then
    sudo apt update && sudo apt install -y python3 python3-pip python3-venv libyara-dev gcc g++ cmake zenity
elif command -v dnf &>/dev/null; then
    sudo dnf install -y python3 python3-pip yara-devel gcc gcc-c++ cmake zenity
elif command -v pacman &>/dev/null; then
    sudo pacman -S --noconfirm python python-pip yara gcc cmake zenity
fi

echo "[*] Creando entorno virtual..."
python3 -m venv "$VENV_DIR"
source "$VENV_DIR/bin/activate"
pip install --upgrade pip
pip install -r "$PROJECT_DIR/requirements.txt"
pip install pybind11

echo "[*] Compilando motores nativos (C y C++)..."
cd "$PROJECT_DIR"
c++ -O3 -Wall -shared -std=c++11 -fPIC $(python -m pybind11 --includes) native_engine/engine_core.cpp -o native_engine/engine_core$(python-config --extension-suffix)
gcc -O3 -shared -fPIC native_engine/file_parser.c -o native_engine/libparser.so

echo "[*] Registrando servicio en segundo plano..."
mkdir -p "$HOME/.config/systemd/user"
cat > "$HOME/.config/systemd/user/privacy-guard.service" << UNIT
[Unit]
Description=Privacy Guard Endpoint Agent
After=network.target

[Service]
Type=simple
WorkingDirectory=$PROJECT_DIR
ExecStart=$VENV_DIR/bin/python -u $PROJECT_DIR/main.py --guard
Restart=on-failure
RestartSec=10
Environment=PYTHONUNBUFFERED=1

[Install]
WantedBy=default.target
UNIT

systemctl --user daemon-reload
systemctl --user enable --now privacy-guard.service

echo "[*] Creando icono en el menú de aplicaciones..."
mkdir -p "$HOME/.local/share/applications"
cat > "$HOME/.local/share/applications/privacy-guard.desktop" << DESKTOP
[Desktop Entry]
Name=Privacy Guard
Comment=Panel de control de seguridad
Exec=$VENV_DIR/bin/python $PROJECT_DIR/gui.py
Icon=$PROJECT_DIR/logo.png
Terminal=false
Type=Application
Categories=System;Security;
DESKTOP

echo ""
echo "✅ ¡Instalación completada con éxito!"
echo "👉 Busca 'Privacy Guard' en el menú de aplicaciones de tu sistema."
echo "👉 El antivirus ya está protegiendo tu equipo en segundo plano."
