# -*- coding: utf-8 -*-
"""
actualizar.py
=============
Script maestro del Tablero Estado de Resultado.

Lee TODO de 1_inputs/ y regenera TODO en 3_outputs/.

Flujo:
  1. Estado de Resultado  (xlsx en 1_inputs/estado_resultado/)
  2. Costos Prestacionales (xlsx en 1_inputs/costos_prestacionales/)
  3. Impuestos            (1_inputs/impuestos.xlsx)
  4. Calculos             (combina todo, distribuye impuestos por OS)
  5. Salidas              (dashboard.html + TABLERO_Resumen.xlsx + log)

Uso:
    python actualizar.py
  o doble clic en actualizar.bat (carpeta raiz)
"""

import os
import sys
import shutil
from datetime import datetime

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, SCRIPT_DIR)

ROOT = os.path.dirname(SCRIPT_DIR)
# HUB unificado: dos niveles arriba (ROOT esta en HUB/2_TABLEROS/TABLERO X)
HUB = os.path.dirname(os.path.dirname(ROOT))
DIR_DATOS = os.path.join(HUB, "1_DATOS")
DIR_OUTPUTS = os.path.join(HUB, "3_RESULTADOS", "estado_resultado")
DIR_ARCHIVO = os.path.join(ROOT, "9_archivo")
DIR_ER = os.path.join(DIR_DATOS, "estado_resultado")
DIR_CP = os.path.join(DIR_DATOS, "prestadores")
FILE_IMP = os.path.join(DIR_DATOS, "impuestos", "impuestos.xlsx")

os.makedirs(DIR_OUTPUTS, exist_ok=True)
os.makedirs(os.path.join(DIR_ARCHIVO, "respaldo"), exist_ok=True)


def banner(t):
    print("\n" + "=" * 70)
    print(f" {t}")
    print("=" * 70)


def main():
    inicio = datetime.now()
    log = [f"Corrida: {inicio.strftime('%d/%m/%Y %H:%M:%S')}", ""]

    # Chequeo de dependencias
    try:
        import openpyxl  # noqa: F401
    except ImportError:
        print("FALTA openpyxl. Corre primero: instalar_dependencias.bat")
        sys.exit(1)

    from lib.estado_resultado import leer_carpeta_estado_resultado
    from lib.costos_prestacionales import leer_carpeta_costos
    from lib.impuestos import leer_impuestos
    from lib.calculos import construir_estado_resultado, periodos_ordenados, \
        construir_payload
    from lib.html_tablero import generar_html
    from lib.excel_resumen import generar_excel

    # ----- 1. ESTADO DE RESULTADO -----
    banner("1) ESTADO DE RESULTADO")
    er_raw, info_er = leer_carpeta_estado_resultado(DIR_ER)
    print(f"  Procesados: {len(info_er['procesados'])}")
    for p in info_er["procesados"]:
        print(f"    OK   {p['archivo']:<45} {p['periodo']:<18} "
              f"{p['afiliados']} afil  $ {p['ingresos']:>16,.2f}")
        log.append(f"ER OK: {p['archivo']} -> {p['periodo']} "
                   f"({p['afiliados']} afil, $ {p['ingresos']:,.2f})")
    for ig in info_er["ignorados"]:
        print(f"    --   IGNORADO {ig['archivo']}: {ig['motivo']}")
        log.append(f"ER IGNORADO: {ig['archivo']} ({ig['motivo']})")
    if not er_raw:
        print("  ATENCION: no hay archivos de Estado de Resultado validos.")
        print("  Pega los Excel en 1_inputs/estado_resultado/ y volve a correr.")

    # ----- 2. COSTOS PRESTACIONALES -----
    banner("2) COSTOS PRESTACIONALES")
    cp_data, info_cp = leer_carpeta_costos(DIR_CP)
    print(f"  Procesados: {len(info_cp['procesados'])}")
    for p in info_cp["procesados"]:
        print(f"    OK   {p['archivo']:<45} {p['periodo']:<18} "
              f"{p['facturas']} fact  $ {p['a_pagar']:>16,.2f}")
        log.append(f"CP OK: {p['archivo']} -> {p['periodo']} "
                   f"({p['facturas']} fact, $ {p['a_pagar']:,.2f})")
    for ig in info_cp["ignorados"]:
        print(f"    --   IGNORADO {ig['archivo']}: {ig['motivo']}")
        log.append(f"CP IGNORADO: {ig['archivo']} ({ig['motivo']})")

    # ----- 3. IMPUESTOS -----
    banner("3) IMPUESTOS")
    imp_data, info_imp = leer_impuestos(FILE_IMP)
    if info_imp["procesados"]:
        for p in info_imp["procesados"]:
            print(f"    {p['periodo']}:  $ {p['total']:,.2f}")
            log.append(f"IMPUESTOS {p['periodo']}: $ {p['total']:,.2f}")
    for ig in info_imp["ignorados"]:
        print(f"    --   {ig['archivo']}: {ig['motivo']}")
        log.append(f"IMPUESTOS: {ig['motivo']}")
    if not imp_data:
        print("  Sin impuestos cargados (se asume 0 para todos los meses).")

    # ----- 4. CALCULOS -----
    banner("4) CALCULOS")
    estado_resultado = construir_estado_resultado(er_raw, imp_data)
    periodos = periodos_ordenados(estado_resultado, cp_data)
    payload = construir_payload(estado_resultado, cp_data, periodos)
    print(f"  Periodos en el tablero: {len(periodos)}")
    for p in periodos:
        m = estado_resultado.get(p)
        c = cp_data.get(p)
        er_txt = (f"ER ${m['totals']['resultado_neto']:,.0f}"
                  if m else "ER --")
        cp_txt = (f"CP ${c['totals']['ap_total']:,.0f}"
                  if c else "CP --")
        print(f"    {p}:  {er_txt:<28} {cp_txt}")
        log.append(f"PERIODO {p}: {er_txt} | {cp_txt}")

    if not periodos:
        print("\n  No hay datos para generar el tablero. Cargar inputs primero.")
        _guardar_log(log, inicio)
        return

    # ----- 5. SALIDAS -----
    banner("5) SALIDAS")
    # Respaldo del dashboard anterior
    dash_path = os.path.join(DIR_OUTPUTS, "dashboard.html")
    if os.path.isfile(dash_path):
        stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        try:
            shutil.copy2(dash_path, os.path.join(
                DIR_ARCHIVO, "respaldo", f"dashboard_{stamp}.html"))
        except Exception:
            pass

    info_corrida = {
        "fecha": inicio.strftime("%d/%m/%Y %H:%M"),
        "er_ok": len(info_er["procesados"]),
        "cp_ok": len(info_cp["procesados"]),
        "periodos": len(periodos),
    }
    html_path = generar_html(payload, info_corrida, dash_path)
    print(f"  HTML:  {html_path}")

    try:
        xlsx_path = os.path.join(DIR_OUTPUTS, "TABLERO_Resumen.xlsx")
        generar_excel(payload, xlsx_path)
        print(f"  Excel: {xlsx_path}")
        log.append(f"\nExcel generado: TABLERO_Resumen.xlsx")
    except Exception as e:
        print(f"  No pude generar el Excel: {e}")
        log.append(f"\nERROR Excel: {e}")

    _guardar_log(log, inicio)

    duracion = (datetime.now() - inicio).total_seconds()
    banner(f"LISTO en {duracion:.1f}s")
    print(f"\nAbri el tablero:  {html_path}\n")


def _guardar_log(log, inicio):
    duracion = (datetime.now() - inicio).total_seconds()
    log.append(f"\nDuracion: {duracion:.1f}s")
    try:
        with open(os.path.join(DIR_OUTPUTS, "log_ultima_corrida.txt"),
                  "w", encoding="utf-8") as f:
            f.write("\n".join(log))
    except Exception:
        pass


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        import traceback
        print("\n!! ERROR !!")
        traceback.print_exc()
        try:
            input("\nPresiona Enter para cerrar...")
        except EOFError:
            pass
        sys.exit(1)
