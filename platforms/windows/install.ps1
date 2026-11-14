$ProjectDir = Resolve-Path "$PSScriptRoot\..\.."
$VenvDir    = "$ProjectDir\.venv"

Write-Host "[*] Creando entorno virtual en $VenvDir"
python -m venv $VenvDir
& "$VenvDir\Scripts\Activate.ps1"

Write-Host "[*] Instalando dependencias..."
pip install --upgrade pip

$wheel = Get-ChildItem "$PSScriptRoot\yara_python-*.whl" -ErrorAction SilentlyContinue | Select-Object -First 1
if ($wheel) {
    Write-Host "[*] Instalando wheel de YARA: $($wheel.Name)"
    pip install $wheel.FullName
}

pip install -r "$ProjectDir\requirements.txt"

Write-Host "[OK] Dependencias instaladas."
