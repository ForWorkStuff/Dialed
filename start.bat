@echo off
cd /d "%~dp0"
where python >nul 2>nul
if %errorlevel%==0 goto usepython
where py >nul 2>nul
if %errorlevel%==0 goto usepy
echo Python wasn't found. Install it from python.org, or run "npx serve -l 8765" in this folder.
pause
exit /b 1
:usepython
echo Dialed is running at http://localhost:8765  (open it in Brave; close this window to stop)
python serve.py
pause
exit /b
:usepy
echo Dialed is running at http://localhost:8765  (open it in Brave; close this window to stop)
py serve.py
pause
exit /b
