@echo off
setlocal
cd /d "%~dp0"

if not exist ".venv\Scripts\python.exe" (
    py -m venv .venv
    if errorlevel 1 exit /b 1
)

if not exist ".env" if exist ".env.example" copy ".env.example" ".env" >nul

".venv\Scripts\python.exe" -m pip install --no-compile -r requirements.txt
if errorlevel 1 exit /b 1

".venv\Scripts\python.exe" -m streamlit run app.py
