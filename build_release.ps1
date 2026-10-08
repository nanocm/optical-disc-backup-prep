# Build a standalone Windows x64 executable and its SHA-256 checksum.
param(
    [string]$Python = '.\.venv\Scripts\python.exe',
    [string]$OutputDir = 'release'
)

$ErrorActionPreference = 'Stop'
Push-Location $PSScriptRoot
try {
    if (-not (Test-Path -LiteralPath $Python)) {
        throw "Python not found: $Python. Create .venv and install requirements-build.txt first."
    }
    & $Python tools\make_icon.py
    if ($LASTEXITCODE -ne 0) { throw 'Icon generation failed.' }

    & $Python -m PyInstaller --noconfirm --clean --onefile --windowed `
        --name OpticalDiscBackupPrep `
        --icon assets\app.ico `
        --add-data 'read_disc.ps1;.' `
        --add-data 'assets\app.ico;assets' `
        backup_gui.py
    if ($LASTEXITCODE -ne 0) { throw 'PyInstaller build failed.' }

    New-Item -ItemType Directory -Path $OutputDir -Force | Out-Null
    $filename = 'OpticalDiscBackupPrep-v0.1.2-windows-x64.exe'
    $target = Join-Path $OutputDir $filename
    Copy-Item -LiteralPath dist\OpticalDiscBackupPrep.exe -Destination $target -Force
    $digest = (Get-FileHash -Algorithm SHA256 -LiteralPath $target).Hash.ToLowerInvariant()
    "$digest  $filename" | Set-Content -Path (Join-Path $OutputDir 'SHA256SUMS.txt') -Encoding ascii
    Write-Host "Release: $target"
    Write-Host "SHA-256: $digest"
}
finally {
    Pop-Location
}
