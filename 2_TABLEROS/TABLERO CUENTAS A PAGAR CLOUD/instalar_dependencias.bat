@echo off
REM ============================================================
REM   Instala las librerias de Python necesarias.
REM   Correr UNA SOLA VEZ al principio (o si te falta alguna).
REM ============================================================
echo Instalando librerias...
pip install pandas openpyxl pdfplumber
echo.
echo ============================================================
echo   Si decia "OK" o "Successfully installed", listo!
echo   Ahora podes correr actualizar.bat
echo ============================================================
echo.
pause
