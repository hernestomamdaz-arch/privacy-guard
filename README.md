# 🛡 Privacy Guard (v0.1.0)

Agente de seguridad (EDR ligero) y cortafuegos de privacidad de código abierto. Diseñado para proteger tu ordenador (Linux y Windows) sin enviar datos a la nube. Esta es la primera versión oficial (Alpha).

## ✨ Características Principales
- **Interfaz Gráfica Moderna:** Panel de control (Dashboard) con diseño Cyberpunk y temas Claro/Oscuro.
- **Soporte Multi-idioma:** Español (LatAm/España), Inglés (US/UK), Portugués (Brasil) y Ruso.
- **Escaneo de Malware:** Detección por firmas (YARA) y hashes SHA-256.
- **Anti-Ransomware (Heurístico):** Detección de ráfagas de cifrado y entropía alta (Shannon).
- **Análisis de Binarios:** Detecta ejecutables con funciones inseguras en C/C++ (ej. strcpy).
- **Gestión de Cuarentena:** Aísla amenazas y permite restaurar falsos positivos desde la interfaz.
- **Instaladores Automáticos:** Scripts para systemd (Linux) y .bat (Windows).

## ⚙ Instalación en Linux
git clone https://github.com/hernestomamdaz-arch/privacy-guard.git
cd privacy-guard
./platforms/linux/install.sh

Ejecuta la interfaz buscando "Privacy Guard" en tu menú de aplicaciones o con:
python gui.py

## 🧪 Laboratorio Educativo
Incluye una carpeta labs/ con código en C (vulnerable.c y seguro.c) para aprender sobre vulnerabilidades de Buffer Overflow y cómo mitigarlas.

## 📜 Licencia
Licencia MIT. Libre para usar, modificar y compartir.
