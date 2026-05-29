# -*- coding: utf-8 -*-
"""
Lectura de saldos de apertura diarios.
Formato esperado del archivo (CSV o XLSX) con columnas:
  fecha, cuenta, saldo_apertura, notas
Donde 'cuenta' es el id interno definido en config.CUENTAS (ej: principal).
"""

import os
import glob
import pandas as pd

from .utils import num, parse_fecha
from .config import CUENTAS


def _read_any(path):
    ext = os.path.splitext(path)[1].lower()
    if ext in (".xlsx", ".xls"):
        return pd.read_excel(path, dtype=object, engine="openpyxl")
    # csv: probar varios encodings y separadores
    for enc in ("utf-8-sig", "utf-8", "latin-1"):
        for sep in (",", ";"):
            try:
                df = pd.read_csv(path, sep=sep, dtype=str, encoding=enc,
                                  keep_default_na=False)
                if len(df.columns) >= 2:
                    return df
            except Exception:
                continue
    raise ValueError(f"No pude leer: {path}")


def _norm_col(c):
    return str(c).strip().lower().replace(" ", "_").replace("á","a").replace(
        "é","e").replace("í","i").replace("ó","o").replace("ú","u")


def leer_saldos(path):
    df = _read_any(path)
    df.columns = [_norm_col(c) for c in df.columns]
    out = pd.DataFrame()
    # Aliases tolerantes
    col_fecha = next((c for c in df.columns if c in
                      ("fecha", "date", "dia")), None)
    col_cuenta = next((c for c in df.columns if c in
                       ("cuenta", "cuenta_id", "account")), None)
    col_saldo = next((c for c in df.columns if c in
                      ("saldo_apertura", "saldo", "apertura", "balance",
                       "amount", "monto")), None)
    col_notas = next((c for c in df.columns if c in
                      ("notas", "nota", "notes", "detalle")), None)

    if not col_fecha or not col_saldo:
        raise ValueError(f"Faltan columnas obligatorias (fecha y "
                         f"saldo_apertura) en {os.path.basename(path)}. "
                         f"Encontradas: {list(df.columns)}")

    out["FECHA"] = df[col_fecha].apply(parse_fecha)
    out["CUENTA"] = df[col_cuenta].astype(str).str.strip() if col_cuenta \
        else CUENTAS[0]["id"]
    out["SALDO"] = df[col_saldo].apply(num)
    out["NOTAS"] = df[col_notas].astype(str).str.strip() if col_notas else ""
    out["ARCHIVO_ORIGEN"] = os.path.basename(path)
    out = out.dropna(subset=["FECHA"])
    return out


def leer_carpeta_saldos(carpeta):
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
            df = leer_saldos(path)
            if df.empty:
                ignorados.append({"archivo": os.path.basename(path),
                                   "motivo": "sin filas validas"})
                continue
            dfs.append(df)
            procesados.append({"archivo": os.path.basename(path),
                                "saldos": len(df)})
        except Exception as e:
            ignorados.append({"archivo": os.path.basename(path),
                               "motivo": str(e)})

    if dfs:
        df_total = pd.concat(dfs, ignore_index=True)
        df_total = df_total.sort_values(["CUENTA", "FECHA"]).drop_duplicates(
            subset=["CUENTA", "FECHA"], keep="last").reset_index(drop=True)
    else:
        df_total = pd.DataFrame(columns=["FECHA", "CUENTA", "SALDO", "NOTAS",
                                          "ARCHIVO_ORIGEN"])
    info = {"procesados": procesados, "ignorados": ignorados}
    return df_total, info
