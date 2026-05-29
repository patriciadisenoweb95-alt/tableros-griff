@echo off
chcp 65001 >nul
cd /d "%~dp0"
echo ============================================================
echo    ACTUALIZAR TABLERO DE PROYECCION DE PAGOS
echo ============================================================
python "2_scripts\actualizar.py"
echo.
echo Si todo salio OK, abri:  3_RESULTADOS\proyeccion\proyeccion.html
pause
