import os
import time
import yara
import threading
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
from endpoint.hash_db import HashDB
from endpoint.quarantine import Quarantine
from core.notifier import Notifier
from endpoint.ransomware_guardian import RansomwareEventHandler

class MalwareEventHandler(FileSystemEventHandler):
    def __init__(self, yara_rules_path, on_detection=None):
        self.rules = None
        try:
            self.rules = yara.compile(filepath=yara_rules_path)
        except Exception as e:
            print(f"[!] Error cargando YARA: {e}")
        self.hash_db = HashDB()
        self.quarantine = Quarantine()
        self.on_detection = on_detection

    def _scan_file(self, filepath):
        if self.hash_db.is_known_malicious(filepath):
            return {"malicious": True, "reason": "hash_malicioso_conocido"}
        if self.rules:
            try:
                matches = self.rules.match(filepath=filepath, timeout=10)
                if matches:
                    return {"malicious": True, "reason": f"yara:{matches[0].rule}"}
            except Exception as e:
                print(f"[!] YARA fallo en {filepath}: {e}")
        return {"malicious": False, "reason": None}

    def on_created(self, event):
        if not event.is_directory:
            threading.Thread(target=self._handle, args=(event.src_path,), daemon=True).start()

    def on_modified(self, event):
        if not event.is_directory:
            threading.Thread(target=self._handle, args=(event.src_path,), daemon=True).start()

    def _handle(self, filepath):
        # El análisis YARA corre en paralelo, sin bloquear el flujo de eventos
        time.sleep(0.5)
        if not os.path.exists(filepath): return
        verdict = self._scan_file(filepath)
        if verdict["malicious"]:
            print(f"[ALERTA] {filepath} -> {verdict['reason']}")
            qpath = self.quarantine.move_to_quarantine(filepath, reason=verdict["reason"])
            if qpath: print(f"   Movido a cuarentena: {qpath}")
            if self.on_detection: self.on_detection(filepath, verdict)

def start_file_guardian(paths_to_watch, yara_rules_path, on_detection=None):
    event_handler = MalwareEventHandler(yara_rules_path, on_detection)
    notifier = Notifier()

    def alert_ransomware(details):
        title = "ALERTA DE RANSOMWARE DETECTADO"
        reasons = "\n- ".join(details["reasons"])
        message = f"Archivo: {details['filepath']}\nRiesgo: {details['score']}/100\nMotivos:\n- {reasons}"
        print(f"\n[!!!] {title} [!!!]\n{message}\n")
        notifier.send_notification(title, message)

    ransomware_handler = RansomwareEventHandler(on_ransomware_detected=alert_ransomware)
    observer = Observer()
    
    for path in paths_to_watch:
        if os.path.exists(path):
            observer.schedule(event_handler, path, recursive=True)
            observer.schedule(ransomware_handler, path, recursive=True)
            print(f"[*] Vigilando (Malware + Ransomware): {path}")
            
    observer.start()
    try:
        while True: time.sleep(1)
    except KeyboardInterrupt:
        observer.stop()
    observer.join()
