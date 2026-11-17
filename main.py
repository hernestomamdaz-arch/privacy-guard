import argparse
import sys
import threading
import os
import platform
import subprocess
import json
from endpoint.file_guardian import start_file_guardian
from endpoint.process_guardian import start_process_guardian

DIRECTORIO_ACTUAL = os.path.dirname(os.path.abspath(__file__))
CONFIG_PATH = os.path.join(DIRECTORIO_ACTUAL, "config.json")

def cargar_rutas():
    """Carga las rutas por defecto y las personalizadas del usuario."""
    home = os.path.expanduser("~")
    paths = []

    # 1. Rutas por defecto (Descargas, Escritorio, Documentos)
    for key in ["DOWNLOAD", "DESKTOP", "DOCUMENTS"]:
        try:
            p = subprocess.check_output(["xdg-user-dir", key], text=True, stderr=subprocess.DEVNULL).strip()
            if p and os.path.isdir(p) and p != home and p not in paths:
                paths.append(p)
        except (FileNotFoundError, subprocess.CalledProcessError):
            pass

    if not paths:
        for name in ["Downloads", "Descargas", "Desktop", "Escritorio", "Documents", "Documentos"]:
            p = os.path.join(home, name)
            if os.path.isdir(p) and p not in paths:
                paths.append(p)

    if not paths:
        paths.append(home)

    # 2. Rutas personalizadas (Añadidas desde la GUI)
    if os.path.exists(CONFIG_PATH):
        try:
            with open(CONFIG_PATH, "r", encoding="utf-8") as f:
                config = json.load(f)
                rutas_extra = config.get("rutas_extra", [])
                for r in rutas_extra:
                    if os.path.isdir(r) and r not in paths:
                        paths.append(r)
        except Exception as e:
            print(f"[!] Error leyendo config.json: {e}")

    return paths

def main():
    parser = argparse.ArgumentParser(description="Privacy Guard - Endpoint Agent")
    parser.add_argument("--guard", action="store_true", help="Activa el agente de archivos y procesos")
    parser.add_argument("--paths", nargs="+", default=None, help="Carpetas a vigilar (sobrescribe la config)")
    parser.add_argument("--yara", default="yara_rules/malware.yar", help="Ruta al archivo de reglas YARA")
    args = parser.parse_args()

    if not args.guard:
        parser.print_help()
        return

    paths = args.paths or cargar_rutas()
    yara_path = os.path.join(DIRECTORIO_ACTUAL, args.yara)

    print(f"[*] Sistema: {platform.system()} {platform.release()}")
    print(f"[*] Reglas YARA: {yara_path}")

    t1 = threading.Thread(target=start_file_guardian, args=(paths, yara_path), daemon=True)
    t2 = threading.Thread(target=start_process_guardian, daemon=True)
    t1.start()
    t2.start()
    print("[*] Agente endpoint activo. Ctrl+C para salir.")
    try:
        while True:
            threading.Event().wait(1)
    except KeyboardInterrupt:
        print("\n[*] Saliendo...")

if __name__ == "__main__":
    main()
