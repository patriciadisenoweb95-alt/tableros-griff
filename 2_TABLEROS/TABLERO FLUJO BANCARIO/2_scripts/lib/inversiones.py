# -*- coding: utf-8 -*-
"""
Lectura de inversiones activas/vencidas.
Formato esperado (CSV o XLSX):
  tipo, monto, tna, fecha_inicio, fecha_vencimiento, plataforma, notas
Tipos sugeridos: Caucion, LECAP, Plazo fijo, FCI Money Market, Bono, Otro.
"""

import os
import glob
import pandas as pd

from .utils import num, parse_fecha


def _norm_col(c):
    return str(c).strip().lower().replace(" ", "_").replace("á","a").replace(
        "é","e").replace("í","i").replace("ó","o").replace("ú","u")


def _read_any(path):
    ext = os.path.splitext(path)[1].lower()
    if ext in (".xlsx", ".xls"):
        return pd.read_excel(path, dtype=object, engine="openpyxl")
    for enc in ("utf-8-sig", "utf-8", "latin-1"):
        for sep in (",", ";"):
            try:
                df = pd.read_csv(path, sep=sep, dtype=str, encoding=enc,
                                  keep_default_na=False)
                if len(df.columns) >= 3:
                    return df
            except Exception:
                continue
    raise ValueError(f"No pude leer: {path}")


def leer_inversiones(path):
    df = _read_any(path)
    df.columns = [_norm_col(c) for c in df.columns]
    out = pd.DataFrame()
    col_tipo = next((c for c in df.columns if c in
                     ("tipo", "instrumento")), None)
    col_monto = next((c for c in df.columns if c in
                      ("monto", "importe", "amount", "capital")), None)
    col_tna = next((c for c in df.columns if c in
                    ("tna", "tasa", "tna_%", "rate")), None)
    col_inicio = next((c for c in df.columns if c in
                       ("fecha_inicio", "inicio", "start_date", "alta")), None)
    col_vto = next((c for c in df.columns if c in
                    ("fecha_vencimiento", "vencimiento", "vto",
                     "fecha_vto", "maturity_date")), None)
    col_plat = next((c for c in df.columns if c in
                     ("plataforma", "banco", "broker")), None)
    col_notas = next((c for c in df.columns if c in
                      ("notas", "notes")), None)

    if not col_monto or not col_inicio or not col_vto:
        raise ValueError(
            f"Faltan columnas (monto, fecha_inicio, fecha_vencimiento) en "
            f"{os.path.basename(path)}. Encontradas: {list(df.columns)}")

    out["TIPO"] = df[col_tipo].astype(str).str.strip() if col_tipo else "Otro"
    out["MONTO"] = df[col_monto].apply(num)
    out["TNA"] = df[col_tna].apply(num) if col_tna else 0.0
    out["FECHA_INICIO"] = df[col_inicio].apply(parse_fecha)
    out["FECHA_VTO"] = df[col_vto].apply(parse_fecha)
    out["PLATAFORMA"] = df[col_plat].astype(str).str.strip() if col_plat else ""
    out["NOTAS"] = df[col_notas].astype(str).str.strip() if col_notas else ""
    out["ARCHIVO_ORIGEN"] = os.path.basename(path)

    out = out.dropna(subset=["FECHA_VTO"])
    out = out[out["MONTO"] > 0]
    return out.reset_index(drop=True)


def leer_carpeta_inversiones(carpeta):
    archivos = sorted(
        glob.glob(os.path.join(carpeta, "*.xlsx")) +
        glob.glob(os.path.join(carpeta, "*.xls")) +
        glob.glob(os.path.join(carpeta, "*.csv"))
    )
    archivos = [a for a in archivos
                if not os.path.basename(a).startswith(".")
                and not os.path.basename(a).startswith("~$")]
    dfs = []
    procesados = []
    ignorados = []
    for path in archivos:
        try:
            df = leer_inversiones(path)
            if df.empty:
                ignorados.append({"archivo": os.path.basename(path),
                                   "motivo": "sin filas validas"})
                continue
            dfs.append(df)
            procesados.append({
                "archivo": os.path.basename(path),
                "inversiones": len(df),
                "monto": float(df["MONTO"].sum()),
            })
        except Exception as e:
            ignorados.append({"archivo": os.path.basename(path),
                               "motivo": str(e)})

    if dfs:
        df_total = pd.concat(dfs, ignore_index=True)
        df_total = df_total.sort_values("FECHA_VTO").reset_index(drop=True)
    else:
        df_total = pd.DataFrame(columns=["TIPO", "MONTO", "TNA", "FECHA_INICIO",
                                          "FECHA_VTO", "PLATAFORMA", "NOTAS",
                                          "ARCHIVO_ORIGEN"])
    info = {"procesados": procesados, "ignorados": ignorados}
    return df_total, info
