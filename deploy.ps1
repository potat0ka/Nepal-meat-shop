# ========================================================================
# 🍖 Nepal Meat Shop - PowerShell Deployment Script
# One-click deployment for Windows systems (PowerShell version)
# ========================================================================

param(
    [switch]$Force,
    [switch]$Verbose
)

# Set error action preference
$ErrorActionPreference = "Stop"

# Function to write colored output
function Write-ColorOutput {
    param(
        [string]$Message,
        [string]$Color = "White"
    )
    
    $colorMap = @{
        "Red" = "Red"
        "Green" = "Green"
        "Yellow" = "Yellow"
        "Blue" = "Blue"
        "Cyan" = "Cyan"
        "Magenta" = "Magenta"
        "White" = "White"
    }
    
    Write-Host $Message -ForegroundColor $colorMap[$Color]
}

function Write-Status {
    param([string]$Message)
    Write-ColorOutput "🔄 $Message" "Blue"
}

function Write-Success {
    param([string]$Message)
    Write-ColorOutput "✅ $Message" "Green"
}

function Write-Error {
    param([string]$Message)
    Write-ColorOutput "❌ $Message" "Red"
}

function Write-Warning {
    param([string]$Message)
    Write-ColorOutput "💡 $Message" "Yellow"
}

function Write-Info {
    param([string]$Message)
    Write-ColorOutput "📋 $Message" "Cyan"
}

# Function to test if a command exists
function Test-Command {
    param([string]$Command)
    try {
        Get-Command $Command -ErrorAction Stop | Out-Null
        return $true
    }
    catch {
        return $false
    }
}

# Function to get file hash
function Get-FileHashMD5 {
    param([string]$FilePath)
    try {
        $hash = Get-FileHash -Path $FilePath -Algorithm MD5
        return $hash.Hash
    }
    catch {
        return $null
    }
}

# Function to load environment variables from file
function Import-EnvFile {
    param([string]$FilePath)
    
    if (Test-Path $FilePath) {
        Write-Status "Loading environment variables from $(Split-Path $FilePath -Leaf)..."
        
        Get-Content $FilePath | ForEach-Object {
            if ($_ -match '^([^#][^=]*?)=(.*)$') {
                $name = $matches[1].Trim()
                $value = $matches[2].Trim()
                
                # Remove quotes if present
                if ($value -match '^"(.*)"$') {
                    $value = $matches[1]
                }
                
                [Environment]::SetEnvironmentVariable($name, $value, "Process")
                if ($Verbose) {
                    Write-Info "Set $name = $value"
                }
            }
        }
        Write-Success "Environment variables loaded"
    }
}

# Main deployment function
function Start-Deployment {
    try {
        Write-ColorOutput "========================================================================" "Blue"
        Write-ColorOutput "🍖 Nepal Meat Shop - PowerShell Deployment Script" "Blue"
        Write-ColorOutput "========================================================================" "Blue"
        Write-Host ""

        # Get project paths
        $ProjectDir = Split-Path -Parent $MyInvocation.MyCommand.Path
        $VenvDir = Join-Path $ProjectDir "venv"
        $RequirementsFile = Join-Path $ProjectDir "requirements.txt"
        $MainFile = Join-Path $ProjectDir "run_mongo.py"
        $EnvFile = Join-Path $ProjectDir ".env.mongo"

        Write-Status "Checking Python installation..."
        
        # Check Python installation
        if (-not (Test-Command "python")) {
            Write-Error "Python is not installed or not in PATH"
            Write-Warning "Please install Python from: https://www.python.org/downloads/"
            Write-Warning "Make sure to check 'Add Python to PATH' during installation"
            exit 1
        }

        # Get Python version
        $pythonVersion = python --version 2>&1
        if ($pythonVersion -match "Python (\d+\.\d+\.\d+)") {
            $version = $matches[1]
            Write-Success "Python $version found"
        } else {
            Write-Error "Could not determine Python version"
            exit 1
        }

        # Check Python version (must be 3.6+)
        $versionParts = $version.Split('.')
        $majorVersion = [int]$versionParts[0]
        $minorVersion = [int]$versionParts[1]
        
        if ($majorVersion -lt 3 -or ($majorVersion -eq 3 -and $minorVersion -lt 6)) {
            Write-Error "Python 3.6 or higher is required. Found: $version"
            exit 1
        }

        # Check pip
        Write-Status "Checking pip installation..."
        try {
            python -m pip --version | Out-Null
            Write-Success "pip is available"
        }
        catch {
            Write-Error "pip is not available"
            Write-Warning "Please reinstall Python with pip included"
            exit 1
        }

        # Check requirements.txt
        if (-not (Test-Path $RequirementsFile)) {
            Write-Error "requirements.txt not found in project directory"
            Write-Warning "Please ensure requirements.txt exists in: $ProjectDir"
            exit 1
        }

        # Create virtual environment if it doesn't exist
        $freshVenv = $false
        if (-not (Test-Path $VenvDir)) {
            Write-Status "Creating virtual environment..."
            python -m venv $VenvDir
            if ($LASTEXITCODE -ne 0) {
                Write-Error "Failed to create virtual environment"
                exit 1
            }
            Write-Success "Virtual environment created"
            $freshVenv = $true
        } else {
            Write-Success "Virtual environment already exists"
        }

        # Activate virtual environment
        Write-Status "Activating virtual environment..."
        $activateScript = Join-Path $VenvDir "Scripts\Activate.ps1"
        
        if (Test-Path $activateScript) {
            & $activateScript
            Write-Success "Virtual environment activated"
        } else {
            Write-Error "Failed to find activation script"
            exit 1
        }

        # Check if we need to install/update dependencies
        $installDeps = $false
        $hashFile = Join-Path $VenvDir "requirements_hash.txt"
        
        if ($freshVenv -or $Force) {
            $installDeps = $true
            if ($freshVenv) {
                Write-Info "Fresh virtual environment - installing dependencies..."
            } else {
                Write-Info "Force flag specified - reinstalling dependencies..."
            }
        } else {
            if (Test-Path $hashFile) {
                $currentHash = Get-FileHashMD5 $RequirementsFile
                $storedHash = Get-Content $hashFile -ErrorAction SilentlyContinue
                
                if ($currentHash -ne $storedHash) {
                    $installDeps = $true
                    Write-Info "Requirements changed - updating dependencies..."
                } else {
                    Write-Success "Dependencies are up to date"
                }
            } else {
                $installDeps = $true
                Write-Info "No dependency cache found - installing dependencies..."
            }
        }

        # Install/update dependencies if needed
        if ($installDeps) {
            Write-Status "Installing dependencies from requirements.txt..."
            
            # Upgrade pip first
            python -m pip install --upgrade pip
            
            # Install requirements
            python -m pip install -r $RequirementsFile
            if ($LASTEXITCODE -ne 0) {
                Write-Error "Failed to install dependencies"
                exit 1
            }
            
            # Store requirements hash for future checks
            $currentHash = Get-FileHashMD5 $RequirementsFile
            if ($currentHash) {
                $currentHash | Out-File -FilePath $hashFile -Encoding UTF8
            }
            
            Write-Success "Dependencies installed successfully"
        }

        # Check if main application file exists
        if (-not (Test-Path $MainFile)) {
            Write-Error "Main application file not found: $MainFile"
            Write-Warning "Available Python files in project:"
            Get-ChildItem -Path $ProjectDir -Filter "*.py" | ForEach-Object { Write-Host "  $($_.Name)" }
            exit 1
        }

        # Load environment variables
        Import-EnvFile $EnvFile

        # Set additional environment variables
        [Environment]::SetEnvironmentVariable("FLASK_ENV", "development", "Process")
        [Environment]::SetEnvironmentVariable("PYTHONPATH", $ProjectDir, "Process")

        # Final checks before starting
        Write-Host ""
        Write-Status "Starting Nepal Meat Shop Application..."
        Write-ColorOutput "========================================================================" "Blue"
        Write-Success "📁 Project Directory: $ProjectDir"
        Write-Success "🐍 Python Version: $version"
        Write-Success "📦 Virtual Environment: $VenvDir"
        Write-Success "🌐 Application will be available at: http://127.0.0.1:5000"
        Write-ColorOutput "========================================================================" "Blue"
        Write-Warning "💡 Press Ctrl+C to stop the server"
        Write-Host ""

        # Start the application
        python $MainFile
    }
    catch {
        Write-Error "Deployment failed: $($_.Exception.Message)"
        if ($Verbose) {
            Write-Host $_.Exception.StackTrace -ForegroundColor Red
        }
        exit 1
    }
    finally {
        Write-Host ""
        Write-Status "🛑 Deployment script finished"
    }
}

# Handle Ctrl+C gracefully
$null = Register-EngineEvent PowerShell.Exiting -Action {
    Write-Host ""
    Write-ColorOutput "🛑 Shutting down application..." "Blue"
    Write-ColorOutput "✅ Application stopped successfully" "Green"
}

# Start deployment
Start-Deployment