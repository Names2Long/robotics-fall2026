$ErrorActionPreference = "Stop"

$LabRoot = $PSScriptRoot
$VenvRoot = Join-Path $LabRoot ".venv"
$VenvPython = Join-Path $VenvRoot "Scripts\python.exe"

if (-not (Test-Path -LiteralPath $VenvPython)) {
    if (Get-Command py -ErrorAction SilentlyContinue) {
        foreach ($version in @('3.14', '3.13', '3.12')) {
            & py "-$version" -c "import sys" 2>$null
            if ($LASTEXITCODE -eq 0) {
                & py "-$version" -m venv $VenvRoot
                break
            }
        }
    }
    if (-not (Test-Path -LiteralPath $VenvPython) -and (Get-Command python -ErrorAction SilentlyContinue)) {
        & python -m venv $VenvRoot
    }
    if (-not (Test-Path -LiteralPath $VenvPython)) { throw "Lab 4 needs Python 3.12 or newer. Install it and retry. student_submission was not changed." }
}

& $VenvPython -c "import sys; sys.exit(0 if sys.version_info >= (3, 12) else 1)"
if ($LASTEXITCODE -ne 0) { throw "This Lab 4 .venv uses Python older than 3.12. Preserve student_submission, then recreate only week04_pid_odometry/.venv using Python 3.12 or newer." }
& $VenvPython --version
& $VenvPython -m pip install --upgrade pip
if ($LASTEXITCODE -ne 0) { throw "Could not update pip in the Lab 4 environment." }
& $VenvPython -m pip install -r (Join-Path $LabRoot "requirements.txt")
if ($LASTEXITCODE -ne 0) { throw "Lab 4 dependency installation failed. Check the interpreter version and network access." }
& $VenvPython (Join-Path $LabRoot "app.py") --preflight
if ($LASTEXITCODE -ne 0) { throw "Lab 4 preflight failed; the app was not started." }
& $VenvPython -m streamlit run (Join-Path $LabRoot "app.py") --browser.gatherUsageStats=false
if ($LASTEXITCODE -ne 0) { throw "Lab 4 Streamlit stopped with an error." }
