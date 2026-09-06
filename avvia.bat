@echo off
REM Avvia il Gioco delle 27 Carte
REM Eseguire dalla cartella che contiene questo file e la cartella gioco27\

cd /d "%~dp0"
python gioco27.py
if errorlevel 1 (
    echo.
    echo Errore: assicurarsi che Python sia installato e nel PATH.
    pause
)
