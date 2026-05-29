# -*- coding: utf-8 -*-
"""
Lectura de cheques emitidos desde XLSX de Galicia.
Estructura del archivo:
  Fila 1: encabezados de grupo (ignorar)
  Fila 2: encabezados de columna
  Fila 3+: datos
Columnas relevantes:
  A: N de cheque
  B: Emitido a (beneficiario)
  C: Cuenta libradora
  E: Fecha de pago (acreditacion)
  F: Fecha de emision
  G: Importe
  H: Estado (Aceptado, Emitido, Pagado, Anulado, Repudiado, ...)
  J: Banco emisor
  K: ID del cheque (clave unica)
"""

import os
import glob
import pandas as pd

from .utils import num, parse_fecha, norm_nombre, fecha_iso
from .config import GALICIA_STATUS_MAP


def map_galicia_status(status_str):
    """Mapea el estado de Galicia al modelo interno.
    1. Match exacto en GALICIA_STATUS_MAP
    2. Fallback por palabras clave (case-insensitive)
    3. Default: 'pendiente'
    """
    if not status_str:
        return "pendiente"
    s = str(status_str).strip()
    # Match exacto
    if s in GALICIA_STATUS_MAP:
        return GALICIA_STATUS_MAP[s]
    # Fallback por palabras clave
    lower = s.lower()
    if "rechaz" in lower or "devuelt" in lower or "repud" in lower:
        return "rechazado"
    if "anul" in lower:
        return "anulado"
    if "pag" in lower or "acredit" in lower:
        return "acreditado"
    if "depo" in lower or "proceso" in lower or "tránsito" in lower \
            or "transito" in lower or "cámara" in lower or "camara" in lower:
        return "en_proceso_deposito"
    if "emit" in lower or "acept" in lower:
        return "pendiente"
    # No matcheo nada -> default conservador a pendiente, pero avisar
    print(f"  [AVISO] Estado de Galicia no reconocido: '{s}' -> "
          f"mapeado como 'pendiente'. Considera agregarlo a "
          f"GALICIA_STATUS_MAP en config.py")
    return "pendiente"


def _read_galicia_xlsx(path):
    """Lee XLSX de Galicia. Header en fila 2 (skiprows=1)."""
    df = pd.read_excel(path, header=1, dtype=object, engine="openpyxl")
    df.columns = [str(c).strip() for c in df.columns]
    return df


def _read_galicia_csv(path):
    """Lee CSV de Galicia (alternativa). Header en fila 2."""
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
    """Lee UN archivo (XLSX o CSV) y devuelve DataFrame normalizado."""
    ext = os.path.splitext(path)[1].lower()
    if ext in (".xlsx", ".xls"):
        df = _read_galicia_xlsx(path)
    elif ext == ".csv":
        df = _read_galicia_csv(path)
    else:
        raise ValueError(f"Extension no soportada: {ext}")

    df.columns = [str(c).strip() for c in df.columns]

    out = pd.DataFrame()

    # N de cheque
    col_chq = None
    for c in df.columns:
        cl = c.lower()
        if "cheque" in cl and ("nº" in cl or "n°" in cl or "nro" in cl
                                or cl.startswith("n")):
            col_chq = c
            break
    if col_chq is None:
        col_chq = df.columns[0]
    out["N_CHEQUE"] = df[col_chq].astype(str).str.strip().str.replace(
        r"\.0$", "", regex=True)

    # Beneficiario
    col_ben = "Emitido a" if "Emitido a" in df.columns else None
    out["BENEFICIARIO"] = df[col_ben].apply(norm_nombre) if col_ben else ""

    # Fechas
    out["FECHA_PAGO"] = df["Fecha de pago"].apply(parse_fecha) \
        if "Fecha de pago" in df.columns else None
    out["FECHA_EMISION"] = df["Fecha de emisión"].apply(parse_fecha) \
        if "Fecha de emisión" in df.columns else None

    # Importe
    out["IMPORTE"] = df["Importe"].apply(num) if "Importe" in df.columns \
        else 0.0

    # Estado original Galicia
    out["ESTADO_BANCO"] = df["Estado"].astype(str).str.strip() \
        if "Estado" in df.columns else ""
    # Estado normalizado al modelo interno (con fallback por keywords)
    out["ESTADO"] = out["ESTADO_BANCO"].apply(map_galicia_status)

    # Banco emisor
    out["BANCO"] = df["Banco emisor"].astype(str).str.strip().str.rstrip() \
        if "Banco emisor" in df.columns else ""

    # ID del cheque (clave unica de Galicia)
    col_id = None
    for candidate in ["ID del cheque", "ID Cheque", "ID"]:
        if candidate in df.columns:
            col_id = candidate
            break
    out["ID_CHEQUE"] = df[col_id].astype(str).str.strip() if col_id else ""

    out["CUENTA_LIBRADORA"] = df["Cuenta libradora"].astype(str).str.strip() \
        if "Cuenta libradora" in df.columns else ""

    out["ARCHIVO_ORIGEN"] = os.path.basename(path)
    out["TIPO"] = "emitido"

    # Filtrar filas vacias (sin N_CHEQUE)
    out = out[out["N_CHEQUE"].astype(str).str.strip() != ""]
    out = out[out["N_CHEQUE"].astype(str).str.lower() != "nan"]
    return out.reset_index(drop=True)


def leer_carpeta_cheques(carpeta):
    """Lee TODOS los archivos de cheques de la carpeta. Une y deduplica
    por ID_CHEQUE (fallback a N_CHEQUE+BANCO)."""
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
            df = leer_cheques(path)
            if df.empty:
                ignorados.append({"archivo": os.path.basename(path),
                                   "motivo": "sin filas"})
                continue
            dfs.append(df)
            procesados.append({
                "archivo": os.path.basename(path),
                "cheques": len(df),
                "monto": float(df["IMPORTE"].sum()),
            })
        except Exception as e:
            ignorados.append({"archivo": os.path.basename(path),
                               "motivo": str(e)})

    if dfs:
        df_total = pd.concat(dfs, ignore_index=True)
        # Clave de deduplicacion: ID_CHEQUE si existe, sino N_CHEQUE+BANCO
        def dedup_key(row):
            if row.get("ID_CHEQUE"):
                return ("ID", row["ID_CHEQUE"])
            return ("NUM", str(row.get("N_CHEQUE", "")),
                    str(row.get("BANCO", "")))
        df_total["__KEY"] = df_total.apply(dedup_key, axis=1)
        df_total = df_total.drop_duplicates(subset=["__KEY"], keep="last")
        df_total = df_total.drop(columns=["__KEY"])
        df_total = df_total.sort_values(
            "FECHA_PAGO", na_position="last").reset_index(drop=True)
    else:
        df_total = pd.DataFrame(columns=[
            "N_CHEQUE", "BENEFICIARIO", "FECHA_PAGO", "FECHA_EMISION",
            "IMPORTE", "ESTADO_BANCO", "ESTADO", "BANCO", "ID_CHEQUE",
            "CUENTA_LIBRADORA", "ARCHIVO_ORIGEN", "TIPO",
        ])

    info = {"procesados": procesados, "ignorados": ignorados}
    return df_total, info
