import os

def scan(filepath):
    """
    Función requerida por Privacy Guard.
    Si retorna un texto (string), se considera una amenaza.
    Si retorna None, el archivo está limpio.
    """
    # Solo analizamos archivos de texto o scripts
    if filepath.endswith(('.txt', '.ps1', '.sh', '.py', '.bat')):
        try:
            with open(filepath, "r", encoding="utf-8", errors="ignore") as f:
                contenido = f.read().lower()
                
            if "password" in contenido and "net user" in contenido:
                return "El script intenta extraer contraseñas de usuarios locales."
            if "contraseña" in contenido and "correo" in contenido:
                return "Posible robo de credenciales de correo."
        except Exception:
            pass
    return None
