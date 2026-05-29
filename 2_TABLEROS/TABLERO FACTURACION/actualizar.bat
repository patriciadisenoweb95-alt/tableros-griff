@echo off
REM ============================================================
REM   TABLERO GRIFF SALUD - Actualizar (doble-click)
REM ============================================================
REM   1) Toma los PDFs nuevos de "PDFs Emitidas"
REM   2) Los carga al Excel (saltea duplicados)
REM   3) Mueve los PDFs a "PDFs Procesados\AAAA-MM\"
REM   4) Genera datos.js para que el dashboard se actualice solo
REM ============================================================
cd /d "%~dp0"
chcp 65001 >nul

REM Intentar varios nombres de Python (Windows)
where py >nul 2>&1
if %errorlevel%==0 (
    py -3 actualizar.py
    goto :fin
)
where python >nul 2>&1
if %errorlevel%==0 (
    python actualizar.py
    goto :fin
)
where python3 >nul 2>&1
if %errorlevel%==0 (
    python3 actualizar.py
    goto :fin
)

echo.
echo ERROR: No se encontró Python instalado.
echo.
echo Instalación rápida:
echo   1) Bajá Python 3.11+ desde https://python.org
echo   2) Al instalar, tildá "Add Python to PATH"
echo   3) Reiniciá la PC
echo   4) Volvé a ejecutar este .bat
echo.
pause
exit /b 1

:fin
pause
