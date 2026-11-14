@echo off
powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0DW2-Windows-Test.ps1"
echo.
echo Test beendet. Ergebnisse: %~dp0results
pause
