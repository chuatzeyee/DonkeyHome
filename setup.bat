@echo off
rem Starts the Home Assistant starter wizard (Windows).
cd /d "%~dp0"
where py >nul 2>nul
if %errorlevel%==0 (
  py -3 wizard\wizard.py %*
) else (
  where python >nul 2>nul
  if errorlevel 1 (
    echo Python is needed. Install it from https://www.python.org/downloads/
    echo and tick "Add python.exe to PATH" on the first screen.
  ) else (
    python wizard\wizard.py %*
  )
)
pause
