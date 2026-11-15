# 🛡 Privacy Guard (v0.1.0)

Agente de seguridad (EDR ligero) de código abierto. Diseñado para proteger tu ordenador (Linux y Windows) sin enviar datos a la nube. Esta es la primera versión oficial (Alpha).

## ✨ Características Principales
- **Interfaz Gráfica Moderna:** Panel de control con diseño Cyberpunk y temas Claro/Oscuro.
- **Soporte Multi-idioma:** Español (LatAm/España), Inglés (US/UK), Portugués (Brasil) y Ruso.
- **Escaneo de Malware:** Detección por firmas (YARA) y hashes SHA-256.
- **Anti-Ransomware (Heurístico):** Detección de ráfagas de cifrado y entropía alta.
- **Análisis de Binarios:** Detecta ejecutables con funciones inseguras en C/C++ (ej. strcpy).
- **Gestión de Cuarentena:** Aísla amenazas y permite restaurar falsos positivos desde la interfaz.

---

## 🚀 Instalación Fácil en Linux (Fedora, Ubuntu, Debian, Arch)

### Opción 1: Instalación Visual (Recomendada para principiantes)
1. Ve a la parte superior de esta página y haz clic en el botón verde **"Code"** -> **"Download ZIP"**.
2. Descomprime el archivo ZIP que se descargó.
3. Abre la carpeta descomprimida, entra a `platforms/linux/` y haz **doble clic** en el archivo `install.sh`.
4. Si tu sistema te pregunta si quieres "Ejecutar" o "Ejecutar en Terminal", acepta. (Si no pasa nada, haz clic derecho sobre `install.sh` -> "Ejecutar como programa").
5. ¡Listo! Busca "Privacy Guard" en tu menú de aplicaciones.

### Opción 2: Instalación por Terminal (Rápida)
Abre tu terminal y copia y pega este comando. Él solo descargará el proyecto, instalará las dependencias y configurará la interfaz en tu menú:
git clone https://github.com/hernestomamdaz-arch/privacy-guard.git && cd privacy-guard && ./platforms/linux/install.sh

---

## 🧪 Laboratorio Educativo
Incluye una carpeta labs/ con código en C (vulnerable.c y seguro.c) para aprender sobre vulnerabilidades de Buffer Overflow y cómo mitigarlas.

## 📜 Licencia
Licencia MIT. Libre para usar, modificar y compartir.
