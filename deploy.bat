@echo off
REM ========================================================================
REM 🍖 Nepal Meat Shop - Windows Deployment Script
REM One-click deployment for Windows systems
REM ========================================================================

setlocal enabledelayedexpansion

REM Set colors for output
set "GREEN=[92m"
set "RED=[91m"
set "YELLOW=[93m"
set "BLUE=[94m"
set "NC=[0m"

echo %BLUE%========================================================================%NC%
echo %BLUE%🍖 Nepal Meat Shop - Windows Deployment Script%NC%
echo %BLUE%========================================================================%NC%
echo.

REM Check if Python is installed
echo %BLUE%🔍 Checking Python installation...%NC%
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo %RED%❌ Python is not installed or not in PATH%NC%
    echo %YELLOW%💡 Please install Python from: https://www.python.org/downloads/%NC%
    echo %YELLOW%   Make sure to check "Add Python to PATH" during installation%NC%
    pause
    exit /b 1
)

REM Get Python version
for /f "tokens=2" %%i in ('python --version 2^>^&1') do set PYTHON_VERSION=%%i
echo %GREEN%✅ Python %PYTHON_VERSION% found%NC%

REM Check if pip is available
echo %BLUE%🔍 Checking pip installation...%NC%
python -m pip --version >nul 2>&1
if %errorlevel% neq 0 (
    echo %RED%❌ pip is not available%NC%
    echo %YELLOW%💡 Please reinstall Python with pip included%NC%
    pause
    exit /b 1
)
echo %GREEN%✅ pip is available%NC%

REM Set project directory and virtual environment path
set "PROJECT_DIR=%~dp0"
set "VENV_DIR=%PROJECT_DIR%venv"
set "REQUIREMENTS_FILE=%PROJECT_DIR%requirements.txt"
set "MAIN_FILE=%PROJECT_DIR%run_mongo.py"

REM Check if requirements.txt exists
if not exist "%REQUIREMENTS_FILE%" (
    echo %RED%❌ requirements.txt not found in project directory%NC%
    echo %YELLOW%💡 Please ensure requirements.txt exists in: %PROJECT_DIR%%NC%
    pause
    exit /b 1
)

REM Create virtual environment if it doesn't exist
if not exist "%VENV_DIR%" (
    echo %BLUE%🔧 Creating virtual environment...%NC%
    python -m venv "%VENV_DIR%"
    if %errorlevel% neq 0 (
        echo %RED%❌ Failed to create virtual environment%NC%
        pause
        exit /b 1
    )
    echo %GREEN%✅ Virtual environment created%NC%
    set "FRESH_VENV=1"
) else (
    echo %GREEN%✅ Virtual environment already exists%NC%
    set "FRESH_VENV=0"
)

REM Activate virtual environment
echo %BLUE%🔄 Activating virtual environment...%NC%
call "%VENV_DIR%\Scripts\activate.bat"
if %errorlevel% neq 0 (
    echo %RED%❌ Failed to activate virtual environment%NC%
    pause
    exit /b 1
)
echo %GREEN%✅ Virtual environment activated%NC%

REM Check if we need to install/update dependencies
set "INSTALL_DEPS=0"
if "%FRESH_VENV%"=="1" (
    set "INSTALL_DEPS=1"
    echo %YELLOW%📦 Fresh virtual environment - installing dependencies...%NC%
) else (
    REM Check if requirements have changed
    if exist "%VENV_DIR%\requirements_hash.txt" (
        REM Calculate current requirements hash
        for /f %%i in ('certutil -hashfile "%REQUIREMENTS_FILE%" MD5 ^| find /v ":" ^| find /v "CertUtil"') do set "CURRENT_HASH=%%i"
        
        REM Read stored hash
        set /p STORED_HASH=<"%VENV_DIR%\requirements_hash.txt"
        
        if "!CURRENT_HASH!" neq "!STORED_HASH!" (
            set "INSTALL_DEPS=1"
            echo %YELLOW%📦 Requirements changed - updating dependencies...%NC%
        ) else (
            echo %GREEN%✅ Dependencies are up to date%NC%
        )
    ) else (
        set "INSTALL_DEPS=1"
        echo %YELLOW%📦 No dependency cache found - installing dependencies...%NC%
    )
)

REM Install/update dependencies if needed
if "%INSTALL_DEPS%"=="1" (
    echo %BLUE%📦 Installing dependencies from requirements.txt...%NC%
    python -m pip install --upgrade pip
    python -m pip install -r "%REQUIREMENTS_FILE%"
    if %errorlevel% neq 0 (
        echo %RED%❌ Failed to install dependencies%NC%
        pause
        exit /b 1
    )
    
    REM Store requirements hash for future checks
    for /f %%i in ('certutil -hashfile "%REQUIREMENTS_FILE%" MD5 ^| find /v ":" ^| find /v "CertUtil"') do echo %%i > "%VENV_DIR%\requirements_hash.txt"
    
    echo %GREEN%✅ Dependencies installed successfully%NC%
)

REM Check if main application file exists
if not exist "%MAIN_FILE%" (
    echo %RED%❌ Main application file not found: %MAIN_FILE%%NC%
    echo %YELLOW%💡 Available Python files in project:%NC%
    dir /b *.py 2>nul
    pause
    exit /b 1
)

REM Load environment variables if .env.mongo exists
if exist "%PROJECT_DIR%.env.mongo" (
    echo %BLUE%📄 Loading environment variables from .env.mongo...%NC%
    for /f "usebackq tokens=1,2 delims==" %%a in ("%PROJECT_DIR%.env.mongo") do (
        if not "%%a"=="" if not "%%a:~0,1%"=="#" (
            set "%%a=%%b"
        )
    )
    echo %GREEN%✅ Environment variables loaded%NC%
)

REM Final checks before starting
echo.
echo %BLUE%🚀 Starting Nepal Meat Shop Application...%NC%
echo %BLUE%========================================================================%NC%
echo %GREEN%📁 Project Directory: %PROJECT_DIR%%NC%
echo %GREEN%🐍 Python Version: %PYTHON_VERSION%%NC%
echo %GREEN%📦 Virtual Environment: %VENV_DIR%%NC%
echo %GREEN%🌐 Application will be available at: http://127.0.0.1:5000%NC%
echo %BLUE%========================================================================%NC%
echo %YELLOW%💡 Press Ctrl+C to stop the server%NC%
echo.

REM Start the application
python "%MAIN_FILE%"

REM Handle application exit
if %errorlevel% neq 0 (
    echo.
    echo %RED%❌ Application exited with error code: %errorlevel%%NC%
    echo %YELLOW%💡 Check the error messages above for troubleshooting%NC%
) else (
    echo.
    echo %GREEN%✅ Application stopped successfully%NC%
)

echo.
echo %BLUE%🛑 Deployment script finished%NC%
pause