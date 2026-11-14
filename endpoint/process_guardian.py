import psutil
import os
import time

SUSPICIOUS_PATHS = [
    "/tmp/", "/var/tmp/", "/dev/shm/",
]

def is_suspicious_process(proc):
    try:
        exe = proc.exe()
        if not exe:
            return False, None
        exe_lower = exe.lower()
        for sp in SUSPICIOUS_PATHS:
            if sp.lower() in exe_lower:
                return True, f"ejecutable en ruta temporal: {exe}"
        parent = proc.parent()
        if parent:
            pname = parent.name().lower()
            cname = proc.name().lower()
            if pname in ("winword.exe", "excel.exe", "powerpnt.exe") and cname in ("powershell.exe", "cmd.exe", "wscript.exe"):
                return True, f"proceso hijo sospechoso: {pname} -> {cname}"
    except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
        pass
    return False, None

def scan_processes_once():
    findings = []
    for proc in psutil.process_iter(["pid", "name", "exe", "cmdline"]):
        suspicious, reason = is_suspicious_process(proc)
        if suspicious:
            findings.append({
                "pid": proc.pid,
                "name": proc.name(),
                "exe": proc.exe() if proc.exe() else "N/A",
                "reason": reason
            })
    return findings

def start_process_guardian(interval_seconds=30):
    print("[*] Monitor de procesos iniciado (solo alerta, no bloquea).")
    seen = set()
    while True:
        for f in scan_processes_once():
            key = (f["pid"], f["reason"])
            if key not in seen:
                seen.add(key)
                print(f"[ALERTA PROCESO] PID {f['pid']} ({f['name']}) -> {f['reason']}")
        time.sleep(interval_seconds)
