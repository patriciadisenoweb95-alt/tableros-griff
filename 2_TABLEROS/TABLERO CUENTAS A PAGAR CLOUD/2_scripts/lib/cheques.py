# -*- coding: utf-8 -*-
"""
Lectura de cheques emitidos (CSV de Galicia).
Soporta varios archivos en la carpeta y elimina duplicados por N_CHEQUE.
"""

import os
import glob
import pandas as pd

from .utils import num, parse_fecha, norm_nombre, norm_cuit, fecha_str


def _leer_csv_galicia(path):
    """El CSV de Galicia tiene 2 filas de header: la primera son grupos.
    Probamos distintos encodings."""
    last_err = None
    for enc in ("latin-1", "utf-8-sig", "utf-8"):
        for sep in (";", ","):
            try:
                df = pd.read_csv(path, sep=sep, dtype=str, encoding=enc,
                                  skiprows=1, keep_default_na=False)
                if len(df.columns) > 5 and "Importe" in " ".join(df.columns):
                    return df
            except Exception as e:
                last_err = e
                continue
    raise ValueError(f"No pude leer cheques: {path}: {last_err}")


def leer_cheques(path):
    """Lee UN archivo de cheques. Devuelve DataFrame normalizado."""
    df = _leer_csv_galicia(path)
    df.columns = [str(c).strip() for c in df.columns]

    out = pd.DataFrame()

    # N de cheque
    col_chq = None
    for c in df.columns:
        if "cheque" in c.lower() and ("n°" in c.lower() or "nro" in c.lower()
                                       or c.lower().startswith("n")):
            col_chq = c
            break
    if col_chq is None:
        col_chq = df.columns[0]
    out["N_CHEQUE"] = df[col_chq].astype(str).str.strip()

    # Beneficiario
    col_ben = "Emitido a" if "Emitido a" in df.columns else None
    out["BENEFICIARIO"] = df[col_ben].apply(norm_nombre) if col_ben else ""

    # CUIT
    col_cuit = None
    for c in df.columns:
        if c.startswith("CUIT") and not c.endswith("2") and not c.endswith("4"):
            col_cuit = c
            break
    out["CUIT"] = df[col_cuit].apply(norm_cuit) if col_cuit else ""

    # Fechas
    out["FECHA_PAGO"] = df["Fecha de pago"].apply(parse_fecha) \
        if "Fecha de pago" in df.columns else None
    out["FECHA_EMISION"] = df["Fecha de emisión"].apply(parse_fecha) \
        if "Fecha de emisión" in df.columns else None

    # Importe
    out["IMPORTE"] = df["Importe"].apply(num) if "Importe" in df.columns \
        else 0.0

    # Estado
    out["ESTADO"] = df["Estado"].astype(str).str.strip() \
        if "Estado" in df.columns else ""

    out["ARCHIVO_ORIGEN"] = os.path.basename(path)
    return out


def leer_carpeta_cheques(carpeta_cheques):
    """Lee TODOS los CSVs de cheques. Une y deduplica por N_CHEQUE.
    Devuelve (df_unificado, info)."""
    archivos = sorted(glob.glob(os.path.join(carpeta_cheques, "*.csv")))
    archivos = [a for a in archivos
                if not os.path.basename(a).startswith(".")]
    dfs = []
    procesados = []
    ignorados = []
    for path in archivos:
        try:
            df = leer_cheques(path)
            dfs.append(df)
            procesados.append({
                "archivo": os.path.basename(path),
                "cheques": len(df),
                "monto": df["IMPORTE"].sum(),
            })
        except Exception as e:
            ignorados.append({"archivo": os.path.basename(path),
                               "motivo": str(e)})
    if dfs:
        df_total = pd.concat(dfs, ignore_index=True)
        # Deduplicar por N_CHEQUE: si aparece varias veces, quedar con el
        # importe mayor (el ultimo estado conocido).
        df_total = df_total.sort_values("IMPORTE",
                                          ascending=False).drop_duplicates(
            subset=["N_CHEQUE"], keep="first")
        df_total = df_total.sort_values("FECHA_EMISION",
                                          na_position="last").reset_index(
            drop=True)
    else:
        df_total = pd.DataFrame(columns=["N_CHEQUE", "BENEFICIARIO", "CUIT",
                                          "FECHA_PAGO", "FECHA_EMISION",
                                          "IMPORTE", "ESTADO", "ARCHIVO_ORIGEN"])
    info = {"procesados": procesados, "ignorados": ignorados}
    return df_total, info
