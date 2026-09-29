@echo off
title Grade 3 Learning Mastery Server & Dashboard
color 0B
echo ========================================================
echo   GRADE 3 LEARNING MASTERY & TEACHER DATABASE PORTAL
echo ========================================================
echo.
echo [1/3] Detecting local IP address for students...
set LOCAL_IP=127.0.0.1
for /f "tokens=4" %%a in ('route print^|find " 0.0.0.0"') do (
    set LOCAL_IP=%%a
    goto :found_ip
)
:found_ip
echo.
echo ========================================================
echo   SERVER IS RUNNING AT:
echo   - Teacher Dashboard:  http://localhost:5000/teacher
echo   - Students on Wi-Fi:  http://%LOCAL_IP%:5000/
echo ========================================================
echo.
echo [2/3] Opening Teacher Analytics Dashboard in your browser...
start http://localhost:5000/teacher
echo.
echo [3/3] Starting Python Server with SQLite Database...
cd /d "%~dp0"
python app.py
pause
