Write-Host "=============================================="
Write-Host "      Solana Wallet Tracker Windows Builder     "
Write-Host "=============================================="
Write-Host ""

# Check if Python is installed
python --version 2>$null
if ($LASTEXITCODE -ne 0) {
    Write-Host "[ERROR] Python is not installed or not in PATH."
    Write-Host "Please install Python 3.8+ on Windows and try again."
    Exit 1
}

# Create virtual environment if it doesn't exist
if (-not (Test-Path ".venv_win")) {
    Write-Host "Creating virtual environment (.venv_win)..."
    python -m venv .venv_win
}

# Activate virtual environment and run pip installs
Write-Host "Installing dependencies and PyInstaller..."
.\.venv_win\Scripts\python.exe -m pip install -r requirements.txt
.\.venv_win\Scripts\python.exe -m pip install pyinstaller

# Compile tracker.py
Write-Host ""
Write-Host "Compiling tracker.py..."
.\.venv_win\Scripts\pyinstaller.exe --onefile --noconsole tracker.py
if ($LASTEXITCODE -ne 0) {
    Write-Host "[ERROR] Failed to compile tracker.py"
    Exit 1
}

# Compile configurator.py
Write-Host ""
Write-Host "Compiling configurator.py..."
.\.venv_win\Scripts\pyinstaller.exe --onefile --noconsole --add-data ".venv_win\Lib\site-packages\flet\controls\material\icons.json;flet\controls\material" configurator.py
if ($LASTEXITCODE -ne 0) {
    Write-Host "[ERROR] Failed to compile configurator.py"
    Exit 1
}

# Create release directory structure
Write-Host ""
Write-Host "Creating release directory..."
if (-not (Test-Path "release")) {
    New-Item -ItemType Directory -Path "release" | Out-Null
}
if (-not (Test-Path "release\secrets")) {
    New-Item -ItemType Directory -Path "release\secrets" | Out-Null
}

# Move executables to release directory
Write-Host ""
Write-Host "Moving executables to release directory..."
if (Test-Path "dist\tracker.exe") {
    Move-Item -Force "dist\tracker.exe" "release\tracker.exe"
}
if (Test-Path "dist\configurator.exe") {
    Move-Item -Force "dist\configurator.exe" "release\configurator.exe"
}

# Copy env template to release\secrets
if (Test-Path "example.env") {
    Copy-Item -Force "example.env" "release\secrets\example.env"
}

# Cleanup build files
Write-Host ""
Write-Host "Cleaning up build files..."
if (Test-Path "build") {
    Remove-Item -Recurse -Force "build"
}
if (Test-Path "dist") {
    Remove-Item -Recurse -Force "dist"
}
if (Test-Path "tracker.spec") {
    Remove-Item -Force "tracker.spec"
}
if (Test-Path "configurator.spec") {
    Remove-Item -Force "configurator.spec"
}

# Delete Linux binary leftovers if they exist to keep Windows ZIP clean
if (Test-Path "release\tracker") {
    Remove-Item -Force "release\tracker"
}
if (Test-Path "release\configurator") {
    Remove-Item -Force "release\configurator"
}

# Create ZIP archive using PowerShell
Write-Host ""
Write-Host "Creating release ZIP archive..."
Compress-Archive -Path 'release' -DestinationPath 'solana-wallet-tracker-windows.zip' -Force

Write-Host ""
Write-Host "=============================================="
Write-Host "   Build Successful!"
Write-Host "   Generated release archive:"
Write-Host "   - solana-wallet-tracker-windows.zip"
Write-Host "=============================================="
Write-Host ""
