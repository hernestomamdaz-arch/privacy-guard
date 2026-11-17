import sqlite3
import os
import datetime

DIRECTORIO_ACTUAL = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DB_PATH = os.path.join(DIRECTORIO_ACTUAL, "privacy_guard.db")

def init_db():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS eventos (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            fecha TEXT,
            tipo TEXT,
            titulo TEXT,
            detalle TEXT,
            color TEXT,
            pid TEXT
        )
    ''')
    conn.commit()
    conn.close()

def guardar_evento(tipo, titulo, detalle, color, pid="0"):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    fecha = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    cursor.execute('''
        INSERT INTO eventos (fecha, tipo, titulo, detalle, color, pid)
        VALUES (?, ?, ?, ?, ?, ?)
    ''', (fecha, tipo, titulo, detalle, color, pid))
    conn.commit()
    conn.close()

def obtener_eventos(limite=50):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute('SELECT fecha, tipo, titulo, detalle, color, pid FROM eventos ORDER BY id DESC LIMIT ?', (limite,))
    filas = cursor.fetchall()
    conn.close()
    
    eventos = []
    for f in filas:
        eventos.append({
            "fecha": f[0], "tipo": f[1], "titulo": f[2], 
            "detalle": f[3], "color": f[4], "pid": f[5]
        })
    return eventos

# Inicializar la base de datos al importar
init_db()
