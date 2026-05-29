# -*- coding: utf-8 -*-
"""
Lectura de gastos (transferencias, debitos automaticos, tarjeta, etc).
Formato esperado (CSV o XLSX) con columnas:
  fecha, concepto, monto, metodo, categoria, cuenta, estado, notas
Estados validos: proyectado | pagado.
"""

import os
import glob
import pandas as pd

from .utils import num, parse_fecha


METODOS_VALIDOS = ["Transferencia", "Débito automático", "Debito automatico",
                   "Tarjeta de crédito", "Tarjeta de credito",
                   "Tarjeta de débito", "Tarjeta de debito",
                   "Efectivo", "Otro"]


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


def leer_gastos(path):
    df = _read_any(path)
    df.columns = [_norm_col(c) for c in df.columns]
    out = pd.DataFrame()
    col_fecha = next((c for c in df.columns if c in
                      ("fecha", "date")), None)
    col_concepto = next((c for c in df.columns if c in
                         ("concepto", "descripcion", "detalle")), None)
    col_monto = next((c for c in df.columns if c in
                      ("monto", "importe", "amount")), None)
    col_metodo = next((c for c in df.columns if c in
                       ("metodo", "metodo_pago", "tipo")), None)
    col_cat = next((c for c in df.columns if c in
                    ("categoria", "rubro")), None)
    col_cuenta = next((c for c in df.columns if c in
                       ("cuenta", "account")), None)
    col_estado = next((c for c in df.columns if c in
                       ("estado", "status")), None)
    col_notas = next((c for c in df.columns if c in
                      ("notas", "notes", "observacion")), None)

    if not col_fecha or not col_concepto or not col_monto:
        raise ValueError(
            f"Faltan columnas obligatorias (fecha, concepto, monto) en "
            f"{os.path.basename(path)}. Encontradas: {list(df.columns)}")

    out["FECHA"] = df[col_fecha].apply(parse_fecha)
    out["CONCEPTO"] = df[col_concepto].astype(str).str.strip()
    out["MONTO"] = df[col_monto].apply(num)
    out["METODO"] = df[col_metodo].astype(str).str.strip() if col_metodo \
        else "Otro"
    out["CATEGORIA"] = df[col_cat].astype(str).str.strip() if col_cat else "Otro"
    out["CUENTA"] = df[col_cuenta].astype(str).str.strip() if col_cuenta \
        else ""
    out["ESTADO"] = df[col_estado].astype(str).str.strip().str.lower() \
        if col_estado else "proyectado"
    out["NOTAS"] = df[col_notas].astype(str).str.strip() if col_notas else ""
    out["ARCHIVO_ORIGEN"] = os.path.basename(path)

    # Normalizar estado
    out["ESTADO"] = out["ESTADO"].apply(
        lambda s: "pagado" if s in ("pagado", "paid") else "proyectado")
    # Filtrar filas sin fecha o sin concepto
    out = out.dropna(subset=["FECHA"])
    out = out[out["CONCEPTO"] != ""]
    out = out[out["MONTO"] > 0]
    return out.reset_index(drop=True)


def leer_carpeta_gastos(carpeta):
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
            df = leer_gastos(path)
            if df.empty:
                ignorados.append({"archivo": os.path.basename(path),
                                   "motivo": "sin filas validas"})
                continue
            dfs.append(df)
            procesados.append({
                "archivo": os.path.basename(path),
                "gastos": len(df),
                "monto": float(df["MONTO"].sum()),
            })
        except Exception as e:
            ignorados.append({"archivo": os.path.basename(path),
                               "motivo": str(e)})

    if dfs:
        df_total = pd.concat(dfs, ignore_index=True)
        df_total = df_total.sort_values("FECHA").reset_index(drop=True)
    else:
        df_total = pd.DataFrame(columns=["FECHA", "CONCEPTO", "MONTO", "METODO",
                                          "CATEGORIA", "CUENTA", "ESTADO",
                                          "NOTAS", "ARCHIVO_ORIGEN"])
    info = {"procesados": procesados, "ignorados": ignorados}
    return df_total, info
