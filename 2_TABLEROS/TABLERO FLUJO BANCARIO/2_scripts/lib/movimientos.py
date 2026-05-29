# -*- coding: utf-8 -*-
"""
Lectura de movimientos proyectados (ingresos/egresos genericos).
Formato esperado:
  fecha, tipo (ingreso|egreso), concepto, monto
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


def leer_movimientos(path):
    df = _read_any(path)
    df.columns = [_norm_col(c) for c in df.columns]
    out = pd.DataFrame()
    col_fecha = next((c for c in df.columns if c in ("fecha", "date")), None)
    col_tipo = next((c for c in df.columns if c in ("tipo", "type")), None)
    col_concepto = next((c for c in df.columns if c in
                         ("concepto", "descripcion", "detalle")), None)
    col_monto = next((c for c in df.columns if c in
                      ("monto", "importe", "amount")), None)

    if not col_fecha or not col_tipo or not col_concepto or not col_monto:
        raise ValueError(
            f"Faltan columnas (fecha, tipo, concepto, monto) en "
            f"{os.path.basename(path)}. Encontradas: {list(df.columns)}")

    out["FECHA"] = df[col_fecha].apply(parse_fecha)
    out["TIPO"] = df[col_tipo].astype(str).str.strip().str.lower()
    out["CONCEPTO"] = df[col_concepto].astype(str).str.strip()
    out["MONTO"] = df[col_monto].apply(num)
    out["ARCHIVO_ORIGEN"] = os.path.basename(path)

    # Normalizar tipo
    out["TIPO"] = out["TIPO"].apply(
        lambda s: "ingreso" if s in ("ingreso", "in", "credito", "credit",
                                      "cobro", "cobranza") else "egreso")
    out = out.dropna(subset=["FECHA"])
    out = out[out["CONCEPTO"] != ""]
    out = out[out["MONTO"] > 0]
    return out.reset_index(drop=True)


def leer_carpeta_movimientos(carpeta):
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
            df = leer_movimientos(path)
            if df.empty:
                ignorados.append({"archivo": os.path.basename(path),
                                   "motivo": "sin filas validas"})
                continue
            dfs.append(df)
            procesados.append({
                "archivo": os.path.basename(path),
                "movimientos": len(df),
                "monto": float(df["MONTO"].sum()),
            })
        except Exception as e:
            ignorados.append({"archivo": os.path.basename(path),
                               "motivo": str(e)})

    if dfs:
        df_total = pd.concat(dfs, ignore_index=True)
        df_total = df_total.sort_values("FECHA").reset_index(drop=True)
    else:
        df_total = pd.DataFrame(columns=["FECHA", "TIPO", "CONCEPTO", "MONTO",
                                          "ARCHIVO_ORIGEN"])
    info = {"procesados": procesados, "ignorados": ignorados}
    return df_total, info
