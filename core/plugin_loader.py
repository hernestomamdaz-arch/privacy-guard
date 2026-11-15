import os
import importlib.util

def cargar_plugins(directorio="plugins"):
    """Busca archivos .py en la carpeta de plugins y los carga."""
    plugins = []
    
    if not os.path.exists(directorio):
        os.makedirs(directorio)
        return plugins

    for archivo in os.listdir(directorio):
        if archivo.endswith(".py") and not archivo.startswith("__"):
            ruta = os.path.join(directorio, archivo)
            nombre_modulo = archivo[:-3]
            
            try:
                spec = importlib.util.spec_from_file_location(nombre_modulo, ruta)
                modulo = importlib.util.module_from_spec(spec)
                spec.loader.exec_module(modulo)
                
                # Verificamos que el plugin tenga la función 'scan'
                if hasattr(modulo, "scan"):
                    plugins.append(modulo)
                    print(f"[*] Plugin cargado: {nombre_modulo}")
                else:
                    print(f"[!] El plugin {archivo} no tiene la función 'scan()' y fue ignorado.")
            except Exception as e:
                print(f"[!] Error cargando el plugin {archivo}: {e}")
                
    return plugins
