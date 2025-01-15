@echo off

REM Change to the project directory
cd /d "C:\path\to\your\project\directory"

REM Start Mosquitto broker
start "" "C:\Program Files\mosquitto\mosquitto.exe"

REM Run the Python program
"C:\path\to\python.exe" src\main.py

pause