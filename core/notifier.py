import platform
import subprocess

class Notifier:
    def __init__(self):
        self.system = platform.system()

    def send_notification(self, title, message, urgency="critical"):
        if self.system == "Linux":
            try:
                subprocess.run(
                    ["notify-send", "-u", urgency, "-a", "Privacy Guard", title, message],
                    check=True, timeout=5
                )
            except (FileNotFoundError, subprocess.CalledProcessError) as e:
                print(f"[!] No se pudo enviar la notificacion: {e}")
        elif self.system == "Windows":
            print(f"[NOTIFICACION WINDOWS] {title}: {message}")
        else:
            print(f"[NOTIFICACION] {title}: {message}")
