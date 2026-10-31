@echo off
setlocal
cd /d "%~dp0"
if not exist ".venv\Scripts\python.exe" (
    echo Creating project virtual environment...
    py -3 -m venv .venv
    if errorlevel 1 ( echo Install Python 3.10 or newer and try again. & pause & exit /b 1 )
)
call ".venv\Scripts\activate.bat"
python -m pip install --upgrade pip
python -m pip install -r requirements.txt uvicorn requests pytest
if errorlevel 1 ( echo Dependency installation failed. & pause & exit /b 1 )
echo Open http://localhost:8000 in your browser.
python -m uvicorn api.index:app --port 8000
pause
endlocal
