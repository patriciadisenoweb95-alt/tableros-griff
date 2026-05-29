@echo off
REM ============================================================
REM   ACTUALIZAR TABLERO ESTADO DE RESULTADO
REM   Doble clic para regenerar todo el tablero
REM ============================================================
cd /d "%~dp0"
python "2_scripts\actualizar.py"
echo.
echo ============================================================
echo   Si todo salio OK, abri:  3_outputs\dashboard.html
echo ============================================================
echo.
pause
