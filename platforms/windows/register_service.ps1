$ProjectDir = Resolve-Path "$PSScriptRoot\..\.."
$Nssm       = "$PSScriptRoot\nssm.exe"
$Python     = "$ProjectDir\.venv\Scripts\python.exe"
$ServiceName = "PrivacyGuard"

if (-not (Test-Path $Nssm)) {
    Write-Host "[!] Falta nssm.exe en $PSScriptRoot" -ForegroundColor Red
    exit 1
}

if (Get-Service $ServiceName -ErrorAction SilentlyContinue) {
    & $Nssm stop $ServiceName
    & $Nssm remove $ServiceName confirm
}

& $Nssm install $ServiceName $Python "$ProjectDir\main.py" --guard
& $Nssm set $ServiceName AppDirectory $ProjectDir
& $Nssm set $ServiceName AppStdout "$ProjectDir\logs\service_out.log"
& $Nssm set $ServiceName AppStderr "$ProjectDir\logs\service_err.log"
& $Nssm set $ServiceName Start SERVICE_AUTO_START
& $Nssm start $ServiceName

Write-Host "[OK] Servicio '$ServiceName' instalado."
