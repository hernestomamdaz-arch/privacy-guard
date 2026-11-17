import os
import time
import yara
import threading
import ctypes
import sys
import hashlib
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
from endpoint.hash_db import HashDB
from endpoint.quarantine import Quarantine
from core.notifier import Notifier
from core.plugin_loader import cargar_plugins
from core.database import guardar_evento
from endpoint.ransomware_guardian import RansomwareEventHandler
from endpoint.binary_analyzer import analyze_binary

# Rutas del sistema críticas (FIM)
ARCHIVOS_CRITICOS = ["/etc/passwd", "/etc/hosts", "/etc/sudoers"]

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
NATIVE_DIR = os.path.join(BASE_DIR, "native_engine")
sys.path.insert(0, NATIVE_DIR)

try:
    import engine_core
    C_PLUS_PLUS_DISPONIBLE = True
except ImportError:
    C_PLUS_PLUS_DISPONIBLE = False

try:
    libparser_path = os.path.join(NATIVE_DIR, "libparser.so")
    lib_c = ctypes.CDLL(libparser_path)
    C_DISPONIBLE = True
except OSError:
    C_DISPONIBLE = False
    lib_c = None

def calcular_hash(filepath):
    try:
        with open(filepath, "rb") as f:
            return hashlib.sha256(f.read()).hexdigest()
    except:
        return None

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
        
        self.plugins = cargar_plugins(os.path.join(BASE_DIR, "plugins"))
        
        self.archivos_en_proceso = set()
        self.lock = threading.Lock()
        
        # Guardar hashes iniciales de archivos críticos
        self.hashes_criticos = {}
        for archivo in ARCHIVOS_CRITICOS:
            if os.path.exists(archivo):
                self.hashes_criticos[archivo] = calcular_hash(archivo)

    def _analisis_nativo(self, filepath):
        if C_DISPONIBLE:
            try:
                resultado_c = lib_c.verificar_cabecera_segura(filepath.encode('utf-8'))
                if resultado_c in (1, 2):
                    tipo = "Windows PE" if resultado_c == 1 else "Linux ELF"
                    print(f"[C-Engine] Ejecutable {tipo} detectado: {os.path.basename(filepath)}")
                    guardar_evento("Nativo", "Análisis Nativo", f"Ejecutable {tipo} detectado: {os.path.basename(filepath)}", "#9D4EDD")
                    
                    if C_PLUS_PLUS_DISPONIBLE:
                        reporte_cpp = engine_core.analizar_rostro(1024)
                        guardar_evento("Nativo", "Motor C++", reporte_cpp, "#9D4EDD")
            except Exception as e:
                pass

    def _scan_file(self, filepath):
        if self.hash_db.is_known_malicious(filepath):
            return {"malicious": True, "reason": "hash_malicioso_conocido"}
            
        if self.rules:
            try:
                matches = self.rules.match(filepath=filepath, timeout=10)
                if matches:
                    return {"malicious": True, "reason": f"yara:{matches[0].rule}"}
            except Exception as e:
                pass
                
        for plugin in self.plugins:
            try:
                resultado = plugin.scan(filepath)
                if resultado:
                    return {"malicious": True, "reason": f"plugin:{plugin.__name__} - {resultado}"}
            except Exception as e:
                pass
                
        return {"malicious": False, "reason": None}

    def on_modified(self, event):
        if not event.is_directory:
            # Chequeo FIM
            if event.src_path in ARCHIVOS_CRITICOS:
                nuevo_hash = calcular_hash(event.src_path)
                if nuevo_hash and nuevo_hash != self.hashes_criticos.get(event.src_path):
                    print(f"\n[ALERTA FIM] ¡Archivo crítico modificado!: {event.src_path}")
                    guardar_evento("FIM", "Archivo del Sistema Modificado", f"¡Cuidado! Se modificó {event.src_path}", "#DC2626")
                    self.hashes_criticos[event.src_path] = nuevo_hash
                    return

            threading.Thread(target=self._handle, args=(event.src_path,), daemon=True).start()

    def on_created(self, event):
        if not event.is_directory:
            threading.Thread(target=self._handle, args=(event.src_path,), daemon=True).start()

    def _handle(self, filepath):
        with self.lock:
            if filepath in self.archivos_en_proceso: return
            self.archivos_en_proceso.add(filepath)

        try:
            time.sleep(0.5)
            if not os.path.exists(filepath): return
            
            self._analisis_nativo(filepath)
                
            if filepath.endswith(('.exe', '.elf', '.so', '.bin')) or os.access(filepath, os.X_OK):
                dangers = analyze_binary(filepath)
                if dangers:
                    msg = f"{os.path.basename(filepath)} usa funciones inseguras: {', '.join(dangers)}"
                    print(f"[ALERTA BINARIO] {msg}")
                    guardar_evento("Binario", "Archivo Inseguro", msg, "#FFD166")
            
            verdict = self._scan_file(filepath)
            if verdict["malicious"]:
                print(f"[ALERTA] {filepath} -> {verdict['reason']}")
                guardar_evento("Amenaza", "Amenaza Neutralizada", f"{verdict['reason']} (Archivo: {os.path.basename(filepath)})", "#DC2626")
                
                qpath = self.quarantine.move_to_quarantine(filepath, reason="plugin_yara")
                if self.on_detection: 
                    self.on_detection(filepath, verdict)
        finally:
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
        guardar_evento("Ransomware", "Ataque de Ransomware", f"Se bloqueó {details['filepath']}", "#DC2626")
        notifier.send_notification(title, message)

    ransomware_handler = RansomwareEventHandler(on_ransomware_detected=alert_ransomware)
    observer = Observer()
    
    # Rutas normales
    for path in paths_to_watch:
        if os.path.exists(path):
            observer.schedule(event_handler, path, recursive=True)
            observer.schedule(ransomware_handler, path, recursive=True)
            print(f"[*] Vigilando: {path}")
            guardar_evento("Sistema", "Protección Activa", f"Protegiendo la carpeta: {os.path.basename(path) or path}", "#059669")

    # Rutas del sistema (FIM) - Solo si tenemos permisos
    for archivo in ARCHIVOS_CRITICOS:
        if os.path.exists(archivo):
            try:
                # Watchdog vigila directorios, asi que vigilamos el dir del archivo
                dir_archivo = os.path.dirname(archivo)
                observer.schedule(event_handler, dir_archivo, recursive=False)
                print(f"[*] FIM Activo en: {archivo}")
            except Exception as e:
                print(f"[!] No se pudo vigilar {archivo}: {e}")
            
    observer.start()
    try:
        while True: time.sleep(1)
    except KeyboardInterrupt:
        observer.stop()
    observer.join()
