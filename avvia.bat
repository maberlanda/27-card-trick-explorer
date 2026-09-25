@echo off
REM Avvia il Gioco delle 27 Carte (Windows, doppio clic).
REM Eseguire dalla cartella che contiene questo file e la cartella gioco27\
REM
REM Interprete: prima il Python Launcher ufficiale (py -3), poi "python".
REM Ogni candidato deve eseguire davvero un controllo di versione (>= 3.10):
REM l'alias "python" del Microsoft Store, che apre lo Store invece di
REM eseguire codice, fallisce il controllo e viene scartato.

setlocal
cd /d "%~dp0"

set "GIOCO27_PY="
set "GIOCO27_CHECK=import sys; sys.exit(0 if sys.version_info >= (3, 10) else 1)"

py -3 -c "%GIOCO27_CHECK%" >nul 2>nul
if not errorlevel 1 set "GIOCO27_PY=py -3"

if not defined GIOCO27_PY (
    python -c "%GIOCO27_CHECK%" >nul 2>nul
    if not errorlevel 1 set "GIOCO27_PY=python"
)

if not defined GIOCO27_PY goto :senza_python

%GIOCO27_PY% gioco27.py %*
if errorlevel 1 goto :errore
exit /b 0

:senza_python
echo.
echo Errore: non trovo Python 3.10 o superiore.
echo  - Installa Python da https://www.python.org/downloads/ (con "tcl/tk" e il
echo    Python Launcher "py"), poi riprova.
echo  - Se "python" apre il Microsoft Store, disattiva l'alias in
echo    Impostazioni ^> App ^> Alias di esecuzione delle app.
echo.
pause
exit /b 1

:errore
echo.
echo Il programma si e' chiuso con un errore. Controllo delle dipendenze:
echo.
%GIOCO27_PY% controlla_requisiti.py
echo.
echo Dettagli nel log: %USERPROFILE%\.gioco27\gioco27.log
pause
exit /b 1
