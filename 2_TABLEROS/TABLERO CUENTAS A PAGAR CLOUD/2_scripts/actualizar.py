# -*- coding: utf-8 -*-
"""
actualizar.py
=============
Script maestro del Tablero de Cuentas a Pagar.

Lee TODO de 1_inputs/ y regenera TODO en 3_outputs/.

Flujo:
  1. Planillas (xlsx/csv en 1_inputs/planillas/)
  2. Cheques (csv en 1_inputs/cheques/)
  3. OPs (pdf en 1_inputs/ops/) -- se hace antes de imputar
  4. Imputacion: cruce cheque -> OP -> comprobantes -> planilla
  5. Salidas (CSVs + xlsx + html)

Uso:
    python actualizar.py
"""

import os
import sys
from datetime import datetime

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, SCRIPT_DIR)

ROOT = os.path.dirname(SCRIPT_DIR)
# HUB unificado: dos niveles arriba (ROOT esta en HUB/2_TABLEROS/TABLERO X)
HUB = os.path.dirname(os.path.dirname(ROOT))
DIR_DATOS = os.path.join(HUB, "1_DATOS")
DIR_PLANILLAS = os.path.join(DIR_DATOS, "prestadores")
DIR_CHEQUES = os.path.join(DIR_DATOS, "cheques")
DIR_OPS = os.path.join(DIR_DATOS, "ordenes_pago")
DIR_OUTPUTS = os.path.join(HUB, "3_RESULTADOS", "cuentas_a_pagar")

os.makedirs(DIR_OUTPUTS, exist_ok=True)


def banner(t):
    print("\n" + "=" * 70)
    print(f" {t}")
    print("=" * 70)


def main():
    inicio = datetime.now()
    log_lineas = [f"Corrida: {inicio.strftime('%d/%m/%Y %H:%M:%S')}", ""]

    try:
        import pandas as pd
    except ImportError:
        print("FALTA pandas. Instalar con:  pip install pandas openpyxl pdfplumber")
        sys.exit(1)
    try:
        import openpyxl  # noqa: F401
    except ImportError:
        print("ATENCION: falta openpyxl (pip install openpyxl).")

    from lib.planillas import leer_carpeta_planillas
    from lib.cheques import leer_carpeta_cheques
    from lib.imputacion import imputar_cheques, calcular_pivot_mes_os, \
        resumen_por_prestador
    from lib.html_tablero import generar_html

    # ----- 1. PLANILLAS -----
    banner("1) PLANILLAS")
    df_planilla, info_pl = leer_carpeta_planillas(DIR_PLANILLAS)
    print(f"  Procesadas: {len(info_pl['procesados'])}")
    for p in info_pl["procesados"]:
        print(f"    OK   {p['archivo']:<55} {p['periodo']:<25} "
              f"{p['facturas']} fact  $ {p['monto']:>15,.2f}")
        log_lineas.append(f"PLANILLA OK: {p['archivo']} -> {p['periodo']} "
                          f"({p['facturas']} fact, $ {p['monto']:,.2f})")
    if info_pl["ignorados"]:
        print(f"  IGNORADAS: {len(info_pl['ignorados'])}")
        for ig in info_pl["ignorados"]:
            print(f"    --   {ig['archivo']}: {ig['motivo']}")
            log_lineas.append(f"PLANILLA IGNORADA: {ig['archivo']} ({ig['motivo']})")
    if df_planilla.empty:
        print("  ATENCION: no hay planillas. Pega xlsx/csv en 1_inputs/planillas/")

    # ----- 2. CHEQUES -----
    banner("2) CHEQUES")
    df_cheques_raw, info_chq = leer_carpeta_cheques(DIR_CHEQUES)
    print(f"  Procesados: {len(info_chq['procesados'])}")
    for p in info_chq["procesados"]:
        print(f"    OK   {p['archivo']:<55} {p['cheques']} cheq  "
              f"$ {p['monto']:>15,.2f}")
        log_lineas.append(f"CHEQUES OK: {p['archivo']} ({p['cheques']} cheq, "
                          f"$ {p['monto']:,.2f})")
    if df_cheques_raw.empty:
        print("  ATENCION: no hay cheques. Pega CSV en 1_inputs/cheques/")

    # ----- 3. OPs (ANTES de imputar) -----
    banner("3) ORDENES DE PAGO")
    ops_data = None
    pdfs_count = len([f for f in os.listdir(DIR_OPS)
                      if f.lower().endswith(".pdf")]) \
        if os.path.isdir(DIR_OPS) else 0
    if pdfs_count > 0:
        try:
            from lib.ops import procesar_carpeta_ops
            ops_data = procesar_carpeta_ops(DIR_OPS, df_planilla)
            df_ops_cab = ops_data["cabecera"]
            print(f"  PDFs en carpeta: {ops_data['total_pdfs']}")
            print(f"  Procesadas como prestador: {len(df_ops_cab)}")
            print(f"  Descartadas (gastos generales): {len(ops_data['descartadas'])}")
            if df_ops_cab is not None and not df_ops_cab.empty:
                print(f"  Total OPs: $ {df_ops_cab['TOTAL_OP'].sum():,.2f}")
                no_cuadran = df_ops_cab[df_ops_cab["DIFF_CUADRE"].abs() > 1]
                print(f"  No cuadran (diff > $1): {len(no_cuadran)}")
                log_lineas.append(f"\nOPs: {len(df_ops_cab)} prestador, "
                                  f"{len(ops_data['descartadas'])} descartadas, "
                                  f"{len(no_cuadran)} no cuadran")
            if ops_data["problemas"]:
                print(f"  PDFs con error: {len(ops_data['problemas'])}")
                for p in ops_data["problemas"]:
                    print(f"     -- {p['archivo']}: {p['error']}")
        except RuntimeError as e:
            print(f"  ATENCION: {e}")
            ops_data = None
    else:
        print("  No hay PDFs en 1_inputs/ops/")

    # ----- 4. IMPUTACION (con OPs si las hay) -----
    banner("4) IMPUTACION")
    if ops_data is not None:
        df_cheques_imp = imputar_cheques(
            df_cheques_raw, df_planilla,
            df_ops_cheques=ops_data["cheques"],
            df_ops_comprobantes=ops_data["comprobantes"],
            df_ops_retenciones=ops_data["retenciones"],
        )
    else:
        df_cheques_imp = imputar_cheques(df_cheques_raw, df_planilla)

    df_pivot = calcular_pivot_mes_os(df_cheques_imp)
    df_por_prest = resumen_por_prestador(df_cheques_imp)

    df_av = df_cheques_imp[df_cheques_imp["A_VENCER"] == "SI"]
    monto_av = df_av["IMPORTE"].sum()
    monto_imp_av = sum(df_av[f"IMP_{os}"].sum() for os in
                       ["OSPEVIC", "OSPIF", "OSPLYFC", "OSSURRBAC", "OSPM"])
    monto_sa_av = df_av["IMP_SIN_ASIGNACION"].sum()

    # Modos de imputacion
    modos = df_av["MODO_IMPUTACION"].value_counts().to_dict()
    print(f"  A vencer: {len(df_av)} cheques · $ {monto_av:,.2f}")
    print(f"    Imputado a OS:  $ {monto_imp_av:,.2f}")
    print(f"    Sin asignar:    $ {monto_sa_av:,.2f} "
          f"({(monto_sa_av/monto_av*100 if monto_av else 0):.1f}%)")
    print(f"  Modos: {modos}")
    log_lineas.append(f"\nA VENCER: {len(df_av)} cheques · $ {monto_av:,.2f}")
    log_lineas.append(f"  Imputado: $ {monto_imp_av:,.2f}")
    log_lineas.append(f"  Sin asignar: $ {monto_sa_av:,.2f} "
                      f"({(monto_sa_av/monto_av*100 if monto_av else 0):.1f}%)")
    log_lineas.append(f"  Modos imputacion: {modos}")

    # ----- 5. GUARDAR CSVs -----
    banner("5) SALIDAS")
    df_cheques_imp.to_csv(os.path.join(DIR_OUTPUTS, "TABLERO_Maestro_Cheques.csv"),
                           sep=";", index=False, decimal=",", encoding="utf-8-sig")
    df_planilla.to_csv(os.path.join(DIR_OUTPUTS, "TABLERO_Maestro_Facturas.csv"),
                        sep=";", index=False, decimal=",", encoding="utf-8-sig")
    df_pivot.to_csv(os.path.join(DIR_OUTPUTS, "TABLERO_A_Vencer_x_OS.csv"),
                     sep=";", index=False, decimal=",", encoding="utf-8-sig")
    df_por_prest.to_csv(os.path.join(DIR_OUTPUTS, "TABLERO_Por_Prestador.csv"),
                         sep=";", index=False, decimal=",", encoding="utf-8-sig")

    if ops_data is not None:
        ops_data["cabecera"].to_csv(
            os.path.join(DIR_OUTPUTS, "TABLERO_OPs_Cabecera.csv"),
            sep=";", index=False, decimal=",", encoding="utf-8-sig")
        ops_data["comprobantes"].to_csv(
            os.path.join(DIR_OUTPUTS, "TABLERO_OPs_Comprobantes.csv"),
            sep=";", index=False, decimal=",", encoding="utf-8-sig")
        ops_data["retenciones"].to_csv(
            os.path.join(DIR_OUTPUTS, "TABLERO_OPs_Retenciones.csv"),
            sep=";", index=False, decimal=",", encoding="utf-8-sig")
        ops_data["cheques"].to_csv(
            os.path.join(DIR_OUTPUTS, "TABLERO_OPs_Cheques.csv"),
            sep=";", index=False, decimal=",", encoding="utf-8-sig")
        if ops_data["problemas"]:
            pd.DataFrame(ops_data["problemas"]).to_csv(
                os.path.join(DIR_OUTPUTS, "ops_con_problemas.csv"),
                sep=";", index=False, encoding="utf-8-sig")
        if ops_data["descartadas"]:
            pd.DataFrame(ops_data["descartadas"]).to_csv(
                os.path.join(DIR_OUTPUTS, "ops_descartadas_gastos.csv"),
                sep=";", index=False, encoding="utf-8-sig")
    print(f"  CSVs guardados en {DIR_OUTPUTS}")

    # ----- 6. Excel consolidado -----
    try:
        out_xlsx = os.path.join(DIR_OUTPUTS, "TABLERO_Resumen.xlsx")
        with pd.ExcelWriter(out_xlsx, engine="openpyxl") as w:
            df_pivot.to_excel(w, sheet_name="A_Vencer_x_OS", index=False)
            df_por_prest.to_excel(w, sheet_name="Por_Prestador", index=False)
            df_cheques_imp.to_excel(w, sheet_name="Maestro_Cheques", index=False)
            df_planilla.to_excel(w, sheet_name="Maestro_Facturas", index=False)
            if ops_data is not None:
                ops_data["cabecera"].to_excel(w, sheet_name="OPs_Cabecera",
                                                index=False)
                ops_data["comprobantes"].to_excel(w, sheet_name="OPs_Comprobantes",
                                                    index=False)
                ops_data["retenciones"].to_excel(w, sheet_name="OPs_Retenciones",
                                                   index=False)
                ops_data["cheques"].to_excel(w, sheet_name="OPs_Cheques",
                                               index=False)
        print(f"  Excel: {out_xlsx}")
    except Exception as e:
        print(f"  No pude generar el xlsx: {e}")

    # ----- 7. HTML -----
    info_corrida = {
        "fecha": inicio.strftime("%d/%m/%Y %H:%M"),
        "planillas_ok": len(info_pl["procesados"]),
        "planillas_ignoradas": len(info_pl["ignorados"]),
        "cheques_files": len(info_chq["procesados"]),
        "ops_pdfs": ops_data["total_pdfs"] if ops_data else 0,
        "ops_ok": len(ops_data["cabecera"]) if ops_data else 0,
        "ops_descartadas": len(ops_data["descartadas"]) if ops_data else 0,
    }
    html_path = generar_html(
        df_cheques_imp, df_planilla, df_pivot, df_por_prest,
        df_ops_cab=ops_data["cabecera"] if ops_data is not None else None,
        info_corrida=info_corrida,
        output_path=os.path.join(DIR_OUTPUTS, "tablero.html"),
    )
    print(f"  HTML: {html_path}")

    # ----- 8. Log -----
    duracion = (datetime.now() - inicio).total_seconds()
    log_lineas.append(f"\nDuracion: {duracion:.1f}s")
    with open(os.path.join(DIR_OUTPUTS, "log_ultima_corrida.txt"),
              "w", encoding="utf-8") as f:
        f.write("\n".join(log_lineas))

    banner(f"LISTO en {duracion:.1f}s")
    print(f"\nAbri el tablero:  {html_path}")
    print()


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        import traceback
        print("\n!! ERROR !!")
        traceback.print_exc()
        input("\nPresiona Enter para cerrar...")
        sys.exit(1)
