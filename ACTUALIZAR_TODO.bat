@echo off
chcp 65001 >nul
cd /d "%~dp0"
echo ============================================================
echo    ACTUALIZAR TODOS LOS TABLEROS - GRIFF SALUD
echo ============================================================
echo.

echo [1/5] Cuentas a Pagar...
cd /d "%~dp0\2_TABLEROS\TABLERO CUENTAS A PAGAR CLOUD"
python "2_scripts\actualizar.py"
echo.

echo [2/5] Estado de Resultado...
cd /d "%~dp0\2_TABLEROS\TABLERO ESTADO DE RESULTADO"
python "2_scripts\actualizar.py"
echo.

echo [3/5] Facturacion...
cd /d "%~dp0\2_TABLEROS\TABLERO FACTURACION"
python "actualizar.py"
echo.

echo [4/5] Flujo Bancario...
cd /d "%~dp0\2_TABLEROS\TABLERO FLUJO BANCARIO"
python "2_scripts\actualizar.py"
echo.

echo [5/5] Proyeccion de Pagos...
cd /d "%~dp0\2_TABLEROS\TABLERO PROYECCION DE PAGOS"
python "2_scripts\actualizar.py"
echo.

echo ============================================================
echo    LISTO - Abri:  3_RESULTADOS\INICIO.html
echo ============================================================
pause
