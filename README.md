# 🛡️ Privacy Guard

Agente de seguridad ligero y de código abierto para Linux (y preparado para Windows). 
Diseñado para proteger la privacidad y detectar amenazas locales sin enviar datos a la nube.

## 🚀 Características
- **Escaneo de Malware:** Detección por firmas (YARA) y hashes SHA-256 conocidos.
- **Cuarentena Automática:** Mueve archivos maliciosos a un entorno seguro de forma automática.
- **Anti-Ransomware:** Detección heurística basada en comportamiento (ráfagas de modificaciones y alta entropía).
- **Monitor de Procesos:** Alerta sobre ejecutables en rutas temporales sospechosas.
- **Notificaciones:** Alertas de escritorio en tiempo real.

## ⚙️ Instalación en Linux (Fedora, Arch, Ubuntu, Debian)
1. Clona este repositorio: `git clone https://github.com/TU_USUARIO/privacy-guard.git`
2. Entra al directorio: `cd privacy-guard`
3. Ejecuta el instalador: `./platforms/linux/install.sh`

## 📱 Uso
El agente se ejecuta automáticamente como un servicio de usuario (`systemctl --user status privacy-guard`).
Para ver los eventos en tiempo real: `journalctl --user -u privacy-guard -f`

## 📜 Licencia
Este proyecto está bajo la Licencia MIT.
