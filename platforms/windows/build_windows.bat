@echo off
echo [*] Instalando dependencias de compilacion...
pip install pyinstaller customtkinter yara-python watchdog psutil

echo [*] Compilando Privacy Guard GUI...
pyinstaller --noconfirm --onedir --windowed --add-data "yara_rules;yara_rules" --add-data "data;data" --name "PrivacyGuard" gui.py

echo [*] Compilando el motor en segundo plano...
pyinstaller --noconfirm --onedir --windowed --add-data "yara_rules;yara_rules" --add-data "data;data" --name "PrivacyGuard_Engine" main.py

echo [OK] Compilacion terminada. Busca la carpeta 'dist'.
pause
