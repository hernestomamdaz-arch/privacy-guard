import os

# Funciones de C conocidas por ser propensas a Buffer Overflows
DANGEROUS_C_FUNCTIONS = [b"strcpy", b"strcat", b"sprintf", b"gets", b"scanf"]

def analyze_binary(filepath):
    """
    Escanea un archivo binario en busca de funciones inseguras de C.
    Retorna una lista de funciones peligrosas encontradas.
    """
    if not os.path.exists(filepath):
        return []

    found_dangers = set()
    try:
        with open(filepath, "rb") as f:
            content = f.read()
            
        for danger in DANGEROUS_C_FUNCTIONS:
            # Buscamos la firma de la función en el código compilado
            if danger in content:
                found_dangers.add(danger.decode('utf-8'))
                
    except Exception as e:
        print(f"[!] Error analizando binario {filepath}: {e}")
        
    return list(found_dangers)
