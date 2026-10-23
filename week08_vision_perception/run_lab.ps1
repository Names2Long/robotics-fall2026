$ErrorActionPreference = 'Stop'
$Lab7Root = $PSScriptRoot
$Lab7Python = Join-Path $Lab7Root '.venv\Scripts\python.exe'
if (-not (Test-Path -LiteralPath $Lab7Python)) {
    foreach ($version in @('3.14', '3.13', '3.12')) {
        & py "-$version" -m venv (Join-Path $Lab7Root '.venv')
        if ($LASTEXITCODE -eq 0) { break }
    }
}
if (-not (Test-Path -LiteralPath $Lab7Python)) { throw 'Install Python 3.12 or newer.' }
& $Lab7Python -c 'import sys; sys.exit(0 if sys.version_info >= (3,12) else "The lab virtual environment needs Python 3.12 or newer.")'
if ($LASTEXITCODE -ne 0) { throw 'Preserve submissions before replacing only the lab virtual environment.' }
& $Lab7Python -m pip install -r (Join-Path $Lab7Root 'requirements.txt')
if ($LASTEXITCODE -ne 0) { throw 'Dependency installation failed. The guide was not started.' }
& $Lab7Python -m streamlit run (Join-Path $Lab7Root 'app.py') --browser.gatherUsageStats=false
