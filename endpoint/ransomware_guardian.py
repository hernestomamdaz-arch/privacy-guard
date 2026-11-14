import time
import math
import os
from collections import Counter, defaultdict
from watchdog.events import FileSystemEventHandler

# Umbrales ajustados
BURST_THRESHOLD_COUNT = 15      # Bajamos a 15 para que sea más fácil de probar
BURST_THRESHOLD_WINDOW = 10
ENTROPY_THRESHOLD = 7.5
SUSPICIOUS_EXTENSIONS = {'.locked', '.encrypted', '.crypto', '.crypt', '.enc'}
RANSOM_NOTE_KEYWORDS = ['decrypt', 'ransom', 'bitcoin', 'restore', 'recover']

class RansomwareEventHandler(FileSystemEventHandler):
    def __init__(self, on_ransomware_detected):
        self.on_ransomware_detected = on_ransomware_detected
        self.modification_events = defaultdict(list)
        # Ahora guardamos un diccionario de tiempo por archivo, no un set
        self.processed_files = {} 

    def _shannon_entropy(self, data):
        if not data: return 0.0
        entropy = 0
        length = len(data)
        for count in Counter(data).values():
            p_x = count / length
            entropy += - p_x * math.log2(p_x)
        return entropy

    def _is_high_entropy(self, filepath):
        try:
            with open(filepath, 'rb') as f:
                chunk = f.read(1024)
            if not chunk: return False
            return self._shannon_entropy(chunk) > ENTROPY_THRESHOLD
        except (IOError, OSError):
            return False

    def on_modified(self, event):
        if event.is_directory: return
        filepath = event.src_path
        now = time.time()
        
        # Si el archivo se modificó hace menos de 2 segundos, lo ignoramos (evita spam)
        if filepath in self.processed_files and now - self.processed_files[filepath] < 2:
            return
            
        self.processed_files[filepath] = now
        directory = os.path.dirname(filepath)
        
        # Registrar evento de ráfaga
        self.modification_events[directory].append(now)
        self.modification_events[directory] = [
            t for t in self.modification_events[directory] if now - t <= BURST_THRESHOLD_WINDOW
        ]
        
        score = 0
        reasons = []

        # 1. Ráfaga
        if len(self.modification_events[directory]) > BURST_THRESHOLD_COUNT:
            score += 40 # Subimos el peso a 40
            reasons.append(f"Rafaga de modificaciones: {len(self.modification_events[directory])} archivos en {BURST_THRESHOLD_WINDOW}s")

        filename, ext = os.path.splitext(filepath)
        ext_lower = ext.lower()
        
        # 2. Extensión
        if ext_lower in SUSPICIOUS_EXTENSIONS:
            score += 30
            reasons.append(f"Extension sospechosa: '{ext_lower}'")

        # 3. Nombre de nota
        for keyword in RANSOM_NOTE_KEYWORDS:
            if keyword in filename.lower():
                score += 30
                reasons.append(f"Posible nota de rescate: contiene '{keyword}'")
                break
        
        # 4. Entropía
        text_exts = {'.txt', '.md', '.csv', '.json', '.log'}
        if ext_lower in text_exts and self._is_high_entropy(filepath):
            score += 40 # Subimos el peso a 40
            reasons.append(f"Entropia alta en: {os.path.basename(filepath)}")

        if score >= 50:
            self.on_ransomware_detected({
                "filepath": filepath,
                "score": score,
                "reasons": reasons
            })

    def on_created(self, event):
        if not event.is_directory:
            filename = os.path.basename(event.src_path).lower()
            for keyword in RANSOM_NOTE_KEYWORDS:
                if keyword in filename:
                    self.on_ransomware_detected({
                        "filepath": event.src_path,
                        "score": 100,
                        "reasons": [f"Creacion de posible nota de rescate: '{filename}'"]
                    })
                    break
