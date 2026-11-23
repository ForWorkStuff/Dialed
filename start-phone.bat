@echo off
cd /d "%~dp0"
set DIALED_LAN=1
where python >nul 2>nul
if %errorlevel%==0 goto usepython
where py >nul 2>nul
if %errorlevel%==0 goto usepy
echo Python wasn't found. Install it from python.org, or run "npx serve -l 8765" in this folder.
pause
exit /b 1
:usepython
echo Starting Dialed in phone mode...
python serve.py
pause
exit /b
:usepy
echo Starting Dialed in phone mode...
py serve.py
pause
exit /b
