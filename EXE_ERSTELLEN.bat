@echo off
setlocal
cd /d "%~dp0"
set "PYTHONUTF8=1"
title DW2 3D Viewer - EXE erstellen

echo [1/3] Python-Abhaengigkeiten installieren ...
py -3 -m pip install -r requirements.txt
if errorlevel 1 goto :fehler
echo [2/3] PyInstaller installieren ...
py -3 -m pip install "pyinstaller>=6.12,<7"
if errorlevel 1 goto :fehler
echo [3/3] Windows-EXE erstellen (3D Viewer, Konverter, Icon und Version 0.14b) ...
if not exist "windows_version_info.txt" goto :fehler
py -3 -m PyInstaller --noconfirm --clean DW2_3D_Viewer_Studio.spec
if errorlevel 1 goto :fehler
if not exist "dist\DW2_3D_Viewer_Studio\DW2_3D_Viewer_Studio.exe" goto :fehler
powershell -NoProfile -Command "$v = (Get-Item 'dist\DW2_3D_Viewer_Studio\DW2_3D_Viewer_Studio.exe').VersionInfo; Write-Host ('Dateiversion: ' + $v.FileVersion + '; Produkt: ' + $v.ProductName); if ($v.FileVersion -ne '0.14.0.2' -or $v.ProductName -ne 'DW2 DW3 Viewer') { throw 'Windows-Versionsinformationen fehlen oder sind falsch' }"
if errorlevel 1 goto :fehler
echo.
echo FERTIG (0.14b): dist\DW2_3D_Viewer_Studio\DW2_3D_Viewer_Studio.exe
echo WICHTIG: Den kompletten Ordner dist\DW2_3D_Viewer_Studio kopieren.
explorer "dist\DW2_3D_Viewer_Studio"
pause
exit /b 0
:fehler
echo.
echo FEHLER: Build fehlgeschlagen. Bitte die Meldungen oben senden.
pause
exit /b 1
