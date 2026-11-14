@echo off
cd /d "%~dp0"
set "PYTHONUTF8=1"
where py >nul 2>nul
if not errorlevel 1 (set "DW2_PY=py -3") else (set "DW2_PY=python")
%DW2_PY% -c "import PyQt6.QtWebEngineWidgets, PyQt6.QtWebChannel, vtkmodules.vtkIOImport, PIL, numpy, trimesh, pyqtgraph, OpenGL" >nul 2>nul
if errorlevel 1 (
    echo Benoetigte Python-Pakete werden installiert ...
    %DW2_PY% -m pip install -r requirements.txt
    if errorlevel 1 (echo Installation fehlgeschlagen. Python 3.11 bis 3.13 installieren. & pause & exit /b 1)
)
%DW2_PY% main.py
if errorlevel 1 (echo Programmfehler - bitte Fehlermeldung aufbewahren. & pause)
