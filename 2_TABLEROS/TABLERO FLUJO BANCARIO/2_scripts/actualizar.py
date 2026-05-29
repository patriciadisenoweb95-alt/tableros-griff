# -*- coding: utf-8 -*-
"""
actualizar.py
=============
Script maestro del Tablero de Flujo Bancario - Griff Salud.

Lee TODO de 1_inputs/ y regenera TODO en 3_outputs/.

Flujo:
  1. Saldos diarios (CSV/XLSX en 1_inputs/saldos/)
  2. Cheques emitidos (XLSX/CSV de Galicia en 1_inputs/cheques/)
  3. Gastos (CSV/XLSX en 1_inputs/gastos/)
  4. Inversiones (CSV/XLSX en 1_inputs/inversiones/)
  5. Movimientos proyectados (CSV/XLSX en 1_inputs/movimientos/)
  6. Proyeccion 30 / 90 dias + alertas
  7. Salidas (CSVs + xlsx + html)

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
DIR_FB = os.path.join(DIR_DATOS, "flujo_bancario")
DIR_SALDOS = os.path.join(DIR_FB, "saldos")
DIR_CHEQUES = os.path.join(DIR_DATOS, "cheques")
DIR_GASTOS = os.path.join(DIR_FB, "gastos")
DIR_INVERSIONES = os.path.join(DIR_FB, "inversiones")
DIR_MOVIMIENTOS = os.path.join(DIR_FB, "movimientos")
DIR_OUTPUTS = os.path.join(HUB, "3_RESULTADOS", "flujo_bancario")

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
        print("FALTA pandas. Correr instalar_dependencias.bat")
        sys.exit(1)
    try:
        import openpyxl  # noqa: F401
    except ImportError:
        print("ATENCION: falta openpyxl. Correr instalar_dependencias.bat")

    from lib.saldos import leer_carpeta_saldos
    from lib.cheques import leer_carpeta_cheques
    from lib.gastos import leer_carpeta_gastos
    from lib.inversiones import leer_carpeta_inversiones
    from lib.movimientos import leer_carpeta_movimientos
    from lib.proyeccion import (build_eventos_func, project_daily,
                                 detect_shortfalls, detect_surplus_windows,
                                 get_min_balance_total)
    from lib.html_tablero import generar_html

    # ----- 1. SALDOS -----
    banner("1) SALDOS DE APERTURA")
    df_saldos, info_s = leer_carpeta_saldos(DIR_SALDOS)
    print(f"  Procesados: {len(info_s['procesados'])}")
    for p in info_s["procesados"]:
        print(f"    OK   {p['archivo']:<55} {p['saldos']} saldos")
        log_lineas.append(f"SALDOS OK: {p['archivo']} ({p['saldos']} regs)")
    if info_s["ignorados"]:
        for ig in info_s["ignorados"]:
            print(f"    --   {ig['archivo']}: {ig['motivo']}")
            log_lineas.append(f"SALDOS IGNORADO: {ig['archivo']} ({ig['motivo']})")
    if df_saldos.empty:
        print("  ATENCION: no hay saldos. Pega un CSV en 1_inputs/saldos/")
        print("           Ver plantilla en 1_inputs/saldos/LEEME.txt")

    # ----- 2. CHEQUES -----
    banner("2) CHEQUES EMITIDOS (Galicia)")
    df_cheques, info_c = leer_carpeta_cheques(DIR_CHEQUES)
    print(f"  Procesados: {len(info_c['procesados'])}")
    for p in info_c["procesados"]:
        print(f"    OK   {p['archivo']:<55} {p['cheques']} cheq  "
              f"$ {p['monto']:>15,.2f}")
        log_lineas.append(f"CHEQUES OK: {p['archivo']} ({p['cheques']} cheq, "
                          f"$ {p['monto']:,.2f})")
    if info_c["ignorados"]:
        for ig in info_c["ignorados"]:
            print(f"    --   {ig['archivo']}: {ig['motivo']}")
            log_lineas.append(f"CHEQUES IGNORADO: {ig['archivo']}")
    if df_cheques.empty:
        print("  ATENCION: no hay cheques. Pega el XLSX de Galicia en "
              "1_inputs/cheques/")
    else:
        # Conteo por estado
        estados = df_cheques["ESTADO"].value_counts().to_dict()
        print(f"  Por estado: {estados}")
        log_lineas.append(f"  Estados: {estados}")

    # ----- 3. GASTOS -----
    banner("3) GASTOS (transferencias, debitos, etc)")
    df_gastos, info_g = leer_carpeta_gastos(DIR_GASTOS)
    print(f"  Procesados: {len(info_g['procesados'])}")
    for p in info_g["procesados"]:
        print(f"    OK   {p['archivo']:<55} {p['gastos']} gastos  "
              f"$ {p['monto']:>15,.2f}")
        log_lineas.append(f"GASTOS OK: {p['archivo']}")
    if info_g["ignorados"]:
        for ig in info_g["ignorados"]:
            print(f"    --   {ig['archivo']}: {ig['motivo']}")
    if df_gastos.empty:
        print("  Sin gastos cargados (opcional).")

    # ----- 4. INVERSIONES -----
    banner("4) INVERSIONES")
    df_inv, info_i = leer_carpeta_inversiones(DIR_INVERSIONES)
    print(f"  Procesados: {len(info_i['procesados'])}")
    for p in info_i["procesados"]:
        print(f"    OK   {p['archivo']:<55} {p['inversiones']} inv  "
              f"$ {p['monto']:>15,.2f}")
        log_lineas.append(f"INVERSIONES OK: {p['archivo']}")
    if info_i["ignorados"]:
        for ig in info_i["ignorados"]:
            print(f"    --   {ig['archivo']}: {ig['motivo']}")
    if df_inv.empty:
        print("  Sin inversiones cargadas (opcional).")

    # ----- 5. MOVIMIENTOS -----
    banner("5) MOVIMIENTOS PROYECTADOS")
    df_mov, info_m = leer_carpeta_movimientos(DIR_MOVIMIENTOS)
    print(f"  Procesados: {len(info_m['procesados'])}")
    for p in info_m["procesados"]:
        print(f"    OK   {p['archivo']:<55} {p['movimientos']} mov")
        log_lineas.append(f"MOVIMIENTOS OK: {p['archivo']}")
    if info_m["ignorados"]:
        for ig in info_m["ignorados"]:
            print(f"    --   {ig['archivo']}: {ig['motivo']}")
    if df_mov.empty:
        print("  Sin movimientos cargados (opcional).")

    # ----- 6. PROYECCION -----
    banner("6) PROYECCION DE FLUJO")
    eventos = build_eventos_func(df_cheques, df_gastos, df_inv, df_mov)
    points30 = project_daily(30, df_saldos, eventos)
    points90 = project_daily(90, df_saldos, eventos)
    shortfalls = detect_shortfalls(points30)
    surplus = detect_surplus_windows(points30)

    if df_saldos.empty:
        print("  Sin saldo de apertura: la proyeccion arranca en 0.")
    else:
        last_p = points30[-1] if points30 else None
        if last_p:
            print(f"  Saldo proyectado a {last_p['date']}: "
                  f"$ {last_p['balance']:,.2f}")
        print(f"  Dias con deficit en 30d: {len(shortfalls)}")
        if shortfalls:
            print(f"    Primer deficit: {shortfalls[0]['date']} "
                  f"(faltarian $ {shortfalls[0]['deficit']:,.2f})")
            log_lineas.append(f"  Deficit primero: {shortfalls[0]['date']} "
                              f"$ {shortfalls[0]['deficit']:,.2f}")
        print(f"  Ventanas de excedente: {len(surplus)}")
        for w in surplus[:3]:
            print(f"    {w['start']} a {w['end']} ({w['days']}d): "
                  f"$ {w['min_surplus']:,.2f} disponibles")
        log_lineas.append(f"  Ventanas excedente: {len(surplus)}")

    # ----- 7. SALIDAS -----
    banner("7) SALIDAS")

    # CSVs maestros
    if not df_cheques.empty:
        # Convert dates to ISO for CSV
        df_export = df_cheques.copy()
        for col in ["FECHA_PAGO", "FECHA_EMISION"]:
            if col in df_export.columns:
                df_export[col] = df_export[col].apply(
                    lambda x: x.strftime("%Y-%m-%d") if x else "")
        df_export.to_csv(os.path.join(DIR_OUTPUTS, "TABLERO_Cheques.csv"),
                          sep=";", index=False, decimal=",", encoding="utf-8-sig")

    if not df_saldos.empty:
        df_s_exp = df_saldos.copy()
        df_s_exp["FECHA"] = df_s_exp["FECHA"].apply(
            lambda x: x.strftime("%Y-%m-%d") if x else "")
        df_s_exp.to_csv(os.path.join(DIR_OUTPUTS, "TABLERO_Saldos.csv"),
                         sep=";", index=False, decimal=",", encoding="utf-8-sig")

    if not df_gastos.empty:
        df_g_exp = df_gastos.copy()
        df_g_exp["FECHA"] = df_g_exp["FECHA"].apply(
            lambda x: x.strftime("%Y-%m-%d") if x else "")
        df_g_exp.to_csv(os.path.join(DIR_OUTPUTS, "TABLERO_Gastos.csv"),
                         sep=";", index=False, decimal=",", encoding="utf-8-sig")

    if not df_inv.empty:
        df_i_exp = df_inv.copy()
        for col in ["FECHA_INICIO", "FECHA_VTO"]:
            df_i_exp[col] = df_i_exp[col].apply(
                lambda x: x.strftime("%Y-%m-%d") if x else "")
        df_i_exp.to_csv(os.path.join(DIR_OUTPUTS, "TABLERO_Inversiones.csv"),
                         sep=";", index=False, decimal=",", encoding="utf-8-sig")

    if not df_mov.empty:
        df_m_exp = df_mov.copy()
        df_m_exp["FECHA"] = df_m_exp["FECHA"].apply(
            lambda x: x.strftime("%Y-%m-%d") if x else "")
        df_m_exp.to_csv(os.path.join(DIR_OUTPUTS, "TABLERO_Movimientos.csv"),
                         sep=";", index=False, decimal=",", encoding="utf-8-sig")

    # Proyeccion como CSV
    df_proy = pd.DataFrame([
        {"fecha": p["date"], "saldo_cierre": p["balance"],
         "ingresos_dia": p["inflow"], "egresos_dia": p["outflow"],
         "n_eventos": len(p["events"])}
        for p in points30
    ])
    df_proy.to_csv(os.path.join(DIR_OUTPUTS, "TABLERO_Proyeccion_30d.csv"),
                    sep=";", index=False, decimal=",", encoding="utf-8-sig")

    print(f"  CSVs guardados en {DIR_OUTPUTS}")

    # Excel consolidado
    try:
        out_xlsx = os.path.join(DIR_OUTPUTS, "TABLERO_Resumen.xlsx")
        with pd.ExcelWriter(out_xlsx, engine="openpyxl") as w:
            df_proy.to_excel(w, sheet_name="Proyeccion_30d", index=False)
            if not df_cheques.empty:
                df_export.to_excel(w, sheet_name="Cheques", index=False)
            if not df_saldos.empty:
                df_s_exp.to_excel(w, sheet_name="Saldos", index=False)
            if not df_gastos.empty:
                df_g_exp.to_excel(w, sheet_name="Gastos", index=False)
            if not df_inv.empty:
                df_i_exp.to_excel(w, sheet_name="Inversiones", index=False)
            if not df_mov.empty:
                df_m_exp.to_excel(w, sheet_name="Movimientos", index=False)
        print(f"  Excel: {out_xlsx}")
    except Exception as e:
        print(f"  No pude generar el xlsx: {e}")

    # HTML
    info_corrida = {
        "fecha": inicio.strftime("%d/%m/%Y %H:%M"),
        "saldos": len(df_saldos),
        "cheques": len(df_cheques),
        "gastos": len(df_gastos),
        "inversiones": len(df_inv),
        "movimientos": len(df_mov),
        "shortfalls": len(shortfalls),
        "surplus_windows": len(surplus),
    }
    html_path = generar_html(
        df_cheques=df_cheques, df_saldos=df_saldos, df_gastos=df_gastos,
        df_inversiones=df_inv, df_movimientos=df_mov,
        points30=points30, points90=points90,
        shortfalls=shortfalls, surplus_windows=surplus,
        info_corrida=info_corrida,
        output_path=os.path.join(DIR_OUTPUTS, "tablero.html"),
    )
    print(f"  HTML: {html_path}")

    # Log
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
