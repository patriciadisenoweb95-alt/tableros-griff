@echo off
REM ============================================================
REM   ACTUALIZAR TABLERO FLUJO BANCARIO
REM   Doble clic para regenerar todo el tablero
REM ============================================================
cd /d "%~dp0"
python "2_scripts\actualizar.py"
echo.
echo ============================================================
echo   Si todo salio OK, abri:  3_outputs\tablero.html
echo ============================================================
echo.
pause
