@echo off

REM Change to the project directory
cd /d "%~dp0"

SET VENV_DIR=%HOMEPATH%\venv_filling_system

IF NOT EXIST "%VENV_DIR%" (
    echo Virtual environment not found. Creating one...
    python -m venv "%VENV_DIR%"
)

IF EXIST "%VENV_DIR%" (
    call "%VENV_DIR%\Scripts\activate"
) ELSE (
    echo Failed to create virtual environment.
    exit /b 1
)

IF EXIST "%VENV_DIR%\Scripts\pip.exe" (
    pip install -r requirements.txt
) ELSE (
    echo pip not found in the virtual environment.
    exit /b 1
)

REM Start Mosquitto broker
start "" "C:\Program Files\mosquitto\mosquitto.exe"

REM Run the Python program
IF EXIST "src\main.py" (
    python src\main.py
) ELSE (
    echo src\main.py not found.
    exit /b 1
)

pause