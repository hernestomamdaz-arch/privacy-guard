import os
import sys
import ctypes

sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'native_engine'))

print("--- Probando C++ (pybind11) ---")
try:
    import engine_core
    print(engine_core.analizar_rostro(1500))
except Exception as e:
    print(f"Error en C++: {e}")

print("\n--- Probando C (ctypes) ---")
try:
    lib_path = os.path.join(os.path.dirname(__file__), 'native_engine', 'libparser.so')
    lib = ctypes.CDLL(lib_path)
    resultado = lib.verificar_cabecera_segura(b'/bin/ls')
    print(f"El archivo /bin/ls es de tipo: {resultado} (2 = Ejecutable Linux)")
except Exception as e:
    print(f"Error en C: {e}")
