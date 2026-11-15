import os
import time
import yara
import threading
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
from endpoint.hash_db import HashDB
from endpoint.quarantine import Quarantine
from core.notifier import Notifier
from core.plugin_loader import cargar_plugins
from endpoint.ransomware_guardian import RansomwareEventHandler
from endpoint.binary_analyzer import analyze_binary

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
        
        directorio_actual = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        ruta_plugins = os.path.join(directorio_actual, "plugins")
        self.plugins = cargar_plugins(ruta_plugins)
        print(f"[*] Se cargaron {len(self.plugins)} plugins de seguridad.")

        # Sistema para evitar procesar el mismo archivo dos veces seguidas
        self.archivos_en_proceso = set()
        self.lock = threading.Lock()

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
                
        for plugin in self.plugins:
            try:
                resultado = plugin.scan(filepath)
                if resultado:
                    return {"malicious": True, "reason": f"plugin:{plugin.__name__} - {resultado}"}
            except Exception as e:
                print(f"[!] Error en plugin {plugin.__name__}: {e}")
                
        return {"malicious": False, "reason": None}

    def on_created(self, event):
        if not event.is_directory:
            threading.Thread(target=self._handle, args=(event.src_path,), daemon=True).start()

    def on_modified(self, event):
        if not event.is_directory:
            threading.Thread(target=self._handle, args=(event.src_path,), daemon=True).start()

    def _handle(self, filepath):
        # Verificar si el archivo ya está siendo procesado
        with self.lock:
            if filepath in self.archivos_en_proceso:
                return
            self.archivos_en_proceso.add(filepath)

        try:
            time.sleep(0.5)
            if not os.path.exists(filepath): 
                return
                
            if filepath.endswith(('.exe', '.elf', '.so', '.bin')) or os.access(filepath, os.X_OK):
                dangers = analyze_binary(filepath)
                if dangers:
                    print(f"[ALERTA BINARIO] {filepath} usa funciones inseguras: {', '.join(dangers)}")
            
            verdict = self._scan_file(filepath)
            if verdict["malicious"]:
                print(f"[ALERTA] {filepath} -> {verdict['reason']}")
                qpath = self.quarantine.move_to_quarantine(filepath, reason="plugin_yara")
                if qpath: 
                    print(f"   Movido a cuarentena: {qpath}")
                if self.on_detection: 
                    self.on_detection(filepath, verdict)
        finally:
            # Liberar el archivo de la lista de procesamiento
            with self.lock:
                if filepath in self.archivos_en_proceso:
                    self.archivos_en_proceso.remove(filepath)

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
            print(f"[*] Vigilando (Malware + Ransomware + Plugins): {path}")
            
    observer.start()
    try:
        while True: time.sleep(1)
    except KeyboardInterrupt:
        observer.stop()
    observer.join()
