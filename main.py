import argparse
import sys
import threading
import os
import platform
import subprocess
from endpoint.file_guardian import start_file_guardian
from endpoint.process_guardian import start_process_guardian


def default_paths():
    """Devuelve carpetas tipicas del usuario, respetando el idioma del sistema."""
    home = os.path.expanduser("~")
    paths = []

    # 1) Intentar con xdg-user-dir (respeta el escritorio y el idioma)
    for key in ["DOWNLOAD", "DESKTOP", "DOCUMENTS"]:
        try:
            p = subprocess.check_output(
                ["xdg-user-dir", key], text=True, stderr=subprocess.DEVNULL
            ).strip()
            if p and os.path.isdir(p) and p != home and p not in paths:
                paths.append(p)
        except (FileNotFoundError, subprocess.CalledProcessError):
            pass

    # 2) Fallback: probar nombres en ingles y espanol
    if not paths:
        for name in ["Downloads", "Descargas", "Desktop", "Escritorio",
                     "Documents", "Documentos"]:
            p = os.path.join(home, name)
            if os.path.isdir(p) and p not in paths:
                paths.append(p)

    # 3) Ultimo recurso: vigilar el home
    if not paths:
        paths.append(home)

    return paths


def main():
    parser = argparse.ArgumentParser(description="Privacy Guard - Endpoint Agent")
    parser.add_argument("--guard", action="store_true",
                        help="Activa el agente de archivos y procesos")
    parser.add_argument("--paths", nargs="+", default=None,
                        help="Carpetas a vigilar (por defecto: autodetectadas)")
    parser.add_argument("--yara", default="yara_rules/malware.yar",
                        help="Ruta al archivo de reglas YARA")
    args = parser.parse_args()

    if not args.guard:
        parser.print_help()
        return

    paths = args.paths or default_paths()
    yara_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), args.yara)

    print(f"[*] Sistema: {platform.system()} {platform.release()}")
    print(f"[*] Reglas YARA: {yara_path}")

    t1 = threading.Thread(target=start_file_guardian,
                          args=(paths, yara_path), daemon=True)
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
