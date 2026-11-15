import shutil
import os
import datetime
import hashlib

class Quarantine:
    def __init__(self, quarantine_dir="quarantine"):
        os.makedirs(quarantine_dir, exist_ok=True)
        self.quarantine_dir = quarantine_dir

    def move_to_quarantine(self, filepath, reason="malware_match"):
        if not os.path.exists(filepath):
            return None
        base = os.path.basename(filepath)
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        dest_name = f"{timestamp}_{reason}_{base}"
        dest_path = os.path.join(self.quarantine_dir, dest_name)
        try:
            shutil.move(filepath, dest_path)
            with open(dest_path, "rb") as f:
                sha = hashlib.sha256(f.read()).hexdigest()
            with open(dest_path + ".meta", "w", encoding="utf-8") as m:
                m.write(f"original_path={filepath}\nsha256={sha}\nreason={reason}\n")
            return dest_path
        except FileNotFoundError:
            # Si el archivo ya fue movido por otro hilo, lo ignoramos silenciosamente
            return None
        except Exception as e:
            print(f"[!] No se pudo poner en cuarentena {filepath}: {e}")
            return None
