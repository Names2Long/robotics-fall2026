$ErrorActionPreference = "Stop"
$LabRoot = $PSScriptRoot
$VenvPython = Join-Path $LabRoot ".venv\Scripts\python.exe"
if (-not (Test-Path -LiteralPath $VenvPython)) {
    if (Get-Command py -ErrorAction SilentlyContinue) {
        foreach ($version in @('3.14', '3.13', '3.12')) {
            & py "-$version" -c "import sys" 2>$null
            if ($LASTEXITCODE -eq 0) {
                & py "-$version" -m venv (Join-Path $LabRoot ".venv")
                break
            }
        }
    }
    if (-not (Test-Path -LiteralPath $VenvPython) -and (Get-Command python -ErrorAction SilentlyContinue)) {
        & python -m venv (Join-Path $LabRoot ".venv")
    }
    if (-not (Test-Path -LiteralPath $VenvPython)) { throw "Install Python 3.12 or newer and reopen PowerShell. student_submission was not changed." }
}
& $VenvPython -c "import sys; sys.exit(0 if sys.version_info >= (3, 12) else 'Lab 5 requires Python 3.12 or newer. Install it and recreate this lab virtual environment after preserving your work.')"
if ($LASTEXITCODE -ne 0) { throw "The Lab 5 virtual environment uses an unsupported Python version." }
& $VenvPython --version
& $VenvPython -m pip install -r (Join-Path $LabRoot "requirements.txt")
if ($LASTEXITCODE -ne 0) { throw "Dependency installation failed. Check Python version and network access." }
& $VenvPython (Join-Path $LabRoot "app.py") --preflight
if ($LASTEXITCODE -ne 0) { throw "Resolve the failed preflight checks before launching." }
& $VenvPython -m streamlit run (Join-Path $LabRoot "app.py") --browser.gatherUsageStats=false
if ($LASTEXITCODE -ne 0) { throw "Streamlit stopped with an error." }
