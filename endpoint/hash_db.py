import hashlib
import os

class HashDB:
    def __init__(self, db_path="data/malicious_hashes.txt"):
        self.hashes = set()
        if os.path.exists(db_path):
            with open(db_path, "r", encoding="utf-8") as f:
                for line in f:
                    h = line.strip().lower()
                    if h and len(h) == 64:
                        self.hashes.add(h)

    def file_sha256(self, filepath):
        sha = hashlib.sha256()
        try:
            with open(filepath, "rb") as f:
                for chunk in iter(lambda: f.read(8192), b""):
                    sha.update(chunk)
            return sha.hexdigest()
        except (PermissionError, FileNotFoundError, OSError):
            return None

    def is_known_malicious(self, filepath):
        h = self.file_sha256(filepath)
        return h is not None and h in self.hashes
