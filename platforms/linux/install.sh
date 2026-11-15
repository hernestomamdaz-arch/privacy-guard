#!/usr/bin/env bash
set -e

echo "========================================================"
echo "   🛡️ Instalador Automático de Privacy Guard (Linux)   "
echo "========================================================"

# 1. Instalar dependencias del sistema
echo "[*] Instalando dependencias base..."
if command -v apt &>/dev/null; then
    sudo apt update -y && sudo apt install -y python3 python3-pip python3-venv libyara-dev git
elif command -v dnf &>/dev/null; then
    sudo dnf install -y python3 python3-pip yara-devel gcc make git
elif command -v pacman &>/dev/null; then
    sudo pacman -S --noconfirm python python-pip yara git
fi

# 2. Descargar el proyecto a una carpeta oculta del sistema
INSTALL_DIR="$HOME/.local/share/privacy_guard"
echo "[*] Descargando Privacy Guard en $INSTALL_DIR..."
rm -rf "$INSTALL_DIR"
git clone https://github.com/hernestomamdaz-arch/privacy-guard.git "$INSTALL_DIR"
cd "$INSTALL_DIR"

# 3. Configurar entorno virtual
echo "[*] Configurando entorno Python..."
python3 -m venv .venv
source .venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt

# 4. Configurar el servicio en segundo plano
echo "[*] Configurando servicio de protección..."
mkdir -p "$HOME/.config/systemd/user"
cat > "$HOME/.config/systemd/user/privacy-guard.service" << UNIT
[Unit]
Description=Privacy Guard Endpoint Agent
After=network.target

[Service]
Type=simple
WorkingDirectory=$INSTALL_DIR
ExecStart=$INSTALL_DIR/.venv/bin/python -u $INSTALL_DIR/main.py --guard
Restart=on-failure
RestartSec=10
Environment=PYTHONUNBUFFERED=1

[Install]
WantedBy=default.target
UNIT

systemctl --user daemon-reload
systemctl --user enable --now privacy-guard.service

# 5. Crear el acceso directo (Menú de aplicaciones)
echo "[*] Creando acceso directo en el menú..."
cat > "$HOME/.local/share/applications/privacy-guard.desktop" << DESKTOP
[Desktop Entry]
Name=Privacy Guard
Comment=Panel de control de seguridad
Exec=$INSTALL_DIR/.venv/bin/python $INSTALL_DIR/gui.py
Icon=security-high
Terminal=false
Type=Application
Categories=System;Security;
DESKTOP

echo ""
echo "✅ ¡Instalación completada con éxito!"
echo "👉 Ya puedes buscar 'Privacy Guard' en tu menú de aplicaciones."
echo "👉 El antivirus ya está protegiendo tu equipo en segundo plano."
