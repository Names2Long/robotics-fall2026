$ErrorActionPreference = "Stop"

$LabRoot = $PSScriptRoot
$VenvRoot = Join-Path $LabRoot ".venv"
$VenvPython = Join-Path $VenvRoot "Scripts\python.exe"

if (-not (Test-Path -LiteralPath $VenvPython)) {
    if (Get-Command py -ErrorAction SilentlyContinue) {
        & py -3 -m venv $VenvRoot
    }
    elseif (Get-Command python -ErrorAction SilentlyContinue) {
        & python -m venv $VenvRoot
    }
    else {
        throw "Python 3.12 is required. Install Python, reopen PowerShell, and run this command again."
    }
}

& $VenvPython -m pip install --upgrade pip
& $VenvPython -m pip install -r (Join-Path $LabRoot "requirements.txt")
& $VenvPython (Join-Path $LabRoot "app.py") --preflight
& $VenvPython -m streamlit run (Join-Path $LabRoot "app.py")
