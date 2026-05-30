# Casper Node - Windows Installation Script
# PowerShell script for Windows platform

param(
    [switch]$SkipPrerequisites = $false,
    [switch]$Help = $false
)

if ($Help) {
    Write-Host "Casper Node Installation Script for Windows"
    Write-Host ""
    Write-Host "Usage: .\install.ps1 [options]"
    Write-Host ""
    Write-Host "Options:"
    Write-Host "  -SkipPrerequisites  Skip installation of Python and Node.js"
    Write-Host "  -Help             Show this help message"
    exit 0
}

function Write-Info { param($message) Write-Host "[INFO] $message" }
function Write-Success { param($message) Write-Host "[SUCCESS] $message" -ForegroundColor Green }
function Write-Warning { param($message) Write-Host "[WARNING] $message" -ForegroundColor Yellow }
function Write-Error { param($message) Write-Host "[ERROR] $message" -ForegroundColor Red }

function Test-PythonInstallation {
    try {
        $python = py -3 --version 2>$null
        if ($LASTEXITCODE -eq 0) {
            $version = ($python -split " ")[1]
            $major = [int]($version -split '\.' | Select-Object -First 1)
            $minor = [int]($version -split '\.' | Select-Object -Index 1)
            if ($major -ge 3 -and $minor -ge 11) {
                return @{ Installed = $true; Version = $version; Executable = "py" }
            } else {
                return @{ Installed = $true; Version = $version; Executable = "py"; VersionOk = $false }
            }
        }
    } catch {}
    try {
        $python = python --version 2>$null
        if ($LASTEXITCODE -eq 0) {
            $version = ($python -split " ")[1]
            $major = [int]($version -split '\.' | Select-Object -First 1)
            $minor = [int]($version -split '\.' | Select-Object -Index 1)
            if ($major -ge 3 -and $minor -ge 11) {
                return @{ Installed = $true; Version = $version; Executable = "python" }
            } else {
                return @{ Installed = $true; Version = $version; Executable = "python"; VersionOk = $false }
            }
        }
    } catch {}
    return @{ Installed = $false }
}

function Test-NodeInstallation {
    try {
        $node = node --version 2>$null
        if ($LASTEXITCODE -eq 0) {
            $version = $node.Trim("v")
            $major = [int]($version -split '\.' | Select-Object -First 1)
            if ($major -ge 18) {
                return @{ Installed = $true; Version = $version; Executable = "node" }
            } else {
                return @{ Installed = $true; Version = $version; Executable = "node"; VersionOk = $false }
            }
        }
    } catch {}
    return @{ Installed = $false }
}

function Install-Python {
    Write-Info "Installing Python 3.11+ using winget..."
    try {
        winget install Python.Python.3 --accept-package-agreements --accept-source-agreements 2>&1 | Out-Null
        if ($LASTEXITCODE -eq 0) {
            Write-Success "Python installed successfully"
            return $true
        }
        Write-Warning "Python installation may have failed"
        return $false
    } catch {
        Write-Error "Failed to install Python: $_"
        return $false
    }
}

function Install-NodeJS {
    Write-Info "Installing Node.js 18+ using winget..."
    try {
        winget install OpenJS.NodeJS --accept-package-agreements --accept-source-agreements 2>&1 | Out-Null
        if ($LASTEXITCODE -eq 0) {
            Write-Success "Node.js installed successfully"
            return $true
        }
        Write-Warning "Node.js installation may have failed"
        return $false
    } catch {
        Write-Error "Failed to install Node.js: $_"
        return $false
    }
}

function Install-Git {
    Write-Info "Installing Git using winget..."
    try {
        winget install Git.Git --accept-package-agreements --accept-source-agreements 2>&1 | Out-Null
        if ($LASTEXITCODE -eq 0) {
            Write-Success "Git installed successfully"
            return $true
        }
        Write-Warning "Git installation may have failed"
        return $false
    } catch {
        Write-Error "Failed to install Git: $_"
        return $false
    }
}

function New-VirtualEnvironment {
    param([string]$Name = ".venv")
    if (Test-Path $Name) {
        Write-Info "Virtual environment already exists"
        return $true
    }
    Write-Info "Creating Python virtual environment..."
    $pythonExe = if (Test-PythonInstallation.Installed) { "py" } else { "python" }
    try {
        & $pythonExe -m venv $Name | Out-Null
        Write-Success "Virtual environment created"
        return $true
    } catch {
        Write-Error "Failed to create virtual environment: $_"
        return $false
    }
}

function Install-PythonDependencies {
    if (-not (Test-Path "requirements.txt")) {
        Write-Error "requirements.txt not found"
        return $false
    }
    Write-Info "Installing Python dependencies..."
    $venvPath = ".venv\Scripts\python.exe"
    if (-not (Test-Path $venvPath)) {
        $venvPath = ".venv\bin\python"
    }
    try {
        & $venvPath -m pip install --upgrade pip | Out-Null
        & $venvPath -m pip install -r requirements.txt | Out-Null
        Write-Success "Python dependencies installed"
        return $true
    } catch {
        Write-Error "Failed to install Python dependencies: $_"
        return $false
    }
}

function Install-NodeDependencies {
    if (-not (Test-Path "package.json")) {
        Write-Info "package.json not found. Skipping Node.js dependencies."
        return $true
    }
    Write-Info "Installing Node.js dependencies..."
    try {
        npm install --no-audit --no-fund | Out-Null
        Write-Success "Node.js dependencies installed"
        return $true
    } catch {
        Write-Error "Failed to install Node.js dependencies: $_"
        return $false
    }
}

function Setup-EnvironmentFile {
    if (-not (Test-Path ".env") -and (Test-Path ".env.example")) {
        Write-Info "Creating .env from .env.example..."
        Copy-Item ".env.example" ".env"
        Write-Warning "Please edit .env and add your API keys before running Casper."
        return $true
    }
    return $false
}

Write-Host "========================================="
Write-Host "Casper Node Installation Script for Windows"
Write-Host "========================================="
Write-Host ""

$pythonInfo = Test-PythonInstallation
$nodeInfo = Test-NodeInstallation

if (-not $SkipPrerequisites) {
    if (-not $pythonInfo.Installed) {
        Write-Info "Python not detected. Installing..."
        $pythonInstalled = Install-Python
        if (-not $pythonInstalled) {
            Write-Error "Python installation failed. Please install Python 3.11+ manually from https://www.python.org/downloads/"
            exit 1
        }
        $pythonInfo = Test-PythonInstallation
    } elseif (-not $pythonInfo.VersionOk) {
        Write-Warning "Python version $($pythonInfo.Version) detected. Casper requires Python 3.11 or later."
        $response = Read-Host "Continue anyway? (y/N)"
        if ($response -notmatch "^[yY]$") {
            exit 1
        }
    } else {
        Write-Info "Python $($pythonInfo.Version) detected"
    }

    if (-not $nodeInfo.Installed) {
        Write-Info "Node.js not detected. Installing..."
        $nodeInstalled = Install-NodeJS
        if (-not $nodeInstalled) {
            Write-Error "Node.js installation failed. Please install Node.js 18+ manually from https://nodejs.org/"
            exit 1
        }
        $nodeInfo = Test-NodeInstallation
    } elseif (-not $nodeInfo.VersionOk) {
        Write-Warning "Node.js version $($nodeInfo.Version) detected. Casper requires Node.js 18 or later."
        $response = Read-Host "Continue anyway? (y/N)"
        if ($response -notmatch "^[yY]$") {
            exit 1
        }
    } else {
        Write-Info "Node.js $($nodeInfo.Version) detected"
    }

    if (-not (Get-Command git -ErrorAction SilentlyContinue)) {
        Write-Info "Git not detected. Installing..."
        $gitInstalled = Install-Git
        if (-not $gitInstalled) {
            Write-Error "Git installation failed. Please install Git manually from https://git-scm.com/download/win"
            exit 1
        }
    } else {
        Write-Info "Git detected"
    }
}

Write-Host ""
$venvCreated = New-VirtualEnvironment
if (-not $venvCreated) {
    Write-Error "Failed to create virtual environment"
    exit 1
}

Write-Host ""
$pythonDepsInstalled = Install-PythonDependencies
if (-not $pythonDepsInstalled) {
    Write-Error "Failed to install Python dependencies"
    exit 1
}

Write-Host ""
$nodeDepsInstalled = Install-NodeDependencies
if (-not $nodeDepsInstalled) {
    Write-Warning "Node.js dependencies installation may have failed"
}

Write-Host ""
Setup-EnvironmentFile

Write-Host ""
Write-Success "Casper Node installation completed successfully!"
Write-Host ""
Write-Info "To get started:"
Write-Info "  1. Activate the virtual environment: .\.venv\Scripts\activate"
Write-Info "  2. Edit .env and add your API keys"
Write-Info "  3. Run: python cli.py --help"
Write-Info "  4. Or run: node index.js --help"
