# -*- coding: utf-8 -*-
"""
Lectura de PDFs de Ordenes de Pago.

Extrae para cada OP:
  - Numero de OP, fecha, prestador, CUIT, concepto
  - Comprobantes pagados (FAC, NDC, NDA, etc.)
  - Retenciones (Ganancias, IIBB)
  - Cheques entregados (numero, banco, fecha vencimiento, importe)
  - Cuadre: facturas + NDs - retenciones = total OP

Filtros:
  - OPs de gastos generales (REINTEGROS, EXPENSAS, AGUA, ALQUILER, INSUMOS,
    HONORARIOS internos, etc.) NO se incluyen en las salidas.
"""

import os
import re
import glob
import pandas as pd

from .utils import num, parse_fecha, fecha_str


# Palabras clave que indican que NO es una OP a prestador medico.
# Si aparece en el nombre de archivo o concepto, la OP se descarta.
KEYWORDS_GASTOS = [
    "REINTEGRO", "REINTEGROS",
    "EXPENSAS",
    "AGUA GRIFF",
    "INSUMOS GRIFF",
    "ALQUILER",
    "TAXI",
    "HONORARIOS DANIEL MENDEZ",
    "REUNION",
    "BCO SUPERVIELLE", "BANCO SUPERVIELLE",
    "PAGO A OSPIF",
    "OTROPAGOS",
]


def _es_op_de_gasto(filename, concepto=""):
    """Devuelve True si el filename o concepto contiene una palabra clave
    de gastos generales (no prestador medico)."""
    blob = (filename + " " + concepto).upper()
    for kw in KEYWORDS_GASTOS:
        if kw in blob:
            return True
    return False


def _split_lines(text):
    return [l.strip() for l in (text or "").split("\n") if l.strip()]


def _limpiar_prestador(s):
    """Saca metadata pegada al nombre: 'Nro.: 1-XXXX', 'Fecha: ...', etc."""
    if not s:
        return ""
    # Cortar en marcadores conocidos
    for marker in (" Nro.:", " Nro:", " Fecha:", "  Fecha", "\nFecha"):
        idx = s.find(marker)
        if idx > 0:
            s = s[:idx]
    # Sacar referencias a numeros de OP/CUIT al final
    s = re.sub(r"\s+1-\d{3,5}\s*$", "", s)
    s = re.sub(r"\s+\d{2}-\d{8}-\d\s*$", "", s)
    # Sacar direcciones tipo "AV ", "AVENIDA ", "BARRIO ", "M:", "BIS"
    # solo si vienen despues de un nombre
    s = re.sub(r"\s+(AV\.|AVENIDA|BARRIO|CALLE|RUTA|PISO|M:|BIS\b).*$", "",
               s, flags=re.IGNORECASE)
    # Sacar numeros de calle al final
    s = re.sub(r"\s+\d{2,5}\s*$", "", s)
    return re.sub(r"\s+", " ", s).strip()


def extraer_op_de_pdf(pdf_path):
    """Procesa un solo PDF de OP. Devuelve dict."""
    try:
        import pdfplumber
    except ImportError:
        raise RuntimeError("Falta pdfplumber. Instalar con: pip install pdfplumber")

    fname = os.path.basename(pdf_path)
    out = {
        "ARCHIVO": fname,
        "OP_NUMERO": "",
        "OP_FECHA": "",
        "PRESTADOR": "",
        "CUIT": "",
        "CONCEPTO": "",
        "TOTAL_OP": 0.0,
        "comprobantes": [],
        "retenciones": [],
        "cheques": [],
    }

    with pdfplumber.open(pdf_path) as pdf:
        text = "\n".join((p.extract_text() or "") for p in pdf.pages)

    # OP numero
    m = re.search(r"Nro\.?:\s*([\d\-]+)", text)
    if m:
        out["OP_NUMERO"] = m.group(1).strip()

    # OP fecha
    m = re.search(r"Fecha:\s*(\d{2}-\d{2}-\d{4})", text)
    if m:
        f = parse_fecha(m.group(1))
        out["OP_FECHA"] = fecha_str(f) if f else m.group(1)

    # CUIT prestador (no Griff)
    cuits = re.findall(r"CUIT:?\s*(\d{2}-?\d{8}-?\d)", text)
    for c in cuits:
        c_clean = re.sub(r"\D", "", c)
        if c_clean and c_clean != "30717134180" and len(c_clean) == 11:
            out["CUIT"] = c_clean
            break

    # Prestador y Concepto
    m = re.search(r"Datos del Proveedor.*?Orden de Pago(.*?)(?:Por medio de la presente|Comprobantes Pagados)",
                  text, re.DOTALL)
    if m:
        block = m.group(1)
        lines = _split_lines(block)
        nombre_partes = []
        concepto = ""
        for l in lines:
            lu = l.upper()
            if lu.startswith("NRO.:") or lu.startswith("FECHA:") \
                    or lu.startswith("CUIT:") or lu.startswith("IVA:"):
                continue
            es_direccion = bool(re.search(
                r"^\s*\d|^AV\.|^AVENIDA|^BARRIO|^BIS\b|^M:|^CALLE|^RUTA",
                lu)) or "PISO" in lu
            es_concepto = lu.startswith("PRESTACIONES") or "MEDICAS" in lu \
                or "HONORARIOS" in lu or "PERIODO" in lu \
                or "/2025" in lu or "/2026" in lu
            if es_concepto and not concepto:
                concepto = l
                continue
            if not es_direccion and len(nombre_partes) < 1 and not concepto:
                nombre_partes.append(l)
        if nombre_partes:
            out["PRESTADOR"] = _limpiar_prestador(nombre_partes[0])
        if concepto:
            out["CONCEPTO"] = concepto.strip()

    # Total OP
    m = re.search(r"Total a Pagar:\s*([\d.,]+)", text)
    if m:
        out["TOTAL_OP"] = num(m.group(1))

    # ---- Comprobantes ----
    m = re.search(r"Comprobantes Pagados.*?\n(.*?)(?:Retenciones Realizadas|Intereses)",
                  text, re.DOTALL)
    if m:
        block = m.group(1)
        for line in block.split("\n"):
            line = line.strip()
            if not line or line.startswith("Nro.") or "Total Original" in line:
                continue
            if line.upper().startswith("A CUENTA"):
                nums = re.findall(r"\(?[\d.,]+\)?", line)
                este_pago = num(nums[-1]) if nums else 0
                out["comprobantes"].append({
                    "NRO_COMP": "A CUENTA", "TIPO": "AC", "FECHA": "",
                    "TOTAL_ORIGINAL": 0, "SALDO": 0, "ESTE_PAGO": este_pago,
                })
                continue
            mm = re.match(
                r"^([\d\-]+)\s+(FAC|NDC|NDA|NCC|FA|REC|TIK|FCE|NCA)\s+"
                r"(\d{4}-\d{2}-\d{2})\s+([\d.,]+)\s+(?:[A-Z]+\s+)?"
                r"\(?([\d.,()-]+)\)?\s+\(?([\d.,()-]+)\)?$", line)
            if mm:
                f = parse_fecha(mm.group(3))
                out["comprobantes"].append({
                    "NRO_COMP": mm.group(1),
                    "TIPO": mm.group(2),
                    "FECHA": fecha_str(f) if f else mm.group(3),
                    "TOTAL_ORIGINAL": num(mm.group(4)),
                    "SALDO": num(mm.group(5)),
                    "ESTE_PAGO": num(mm.group(6)),
                })

    # ---- Retenciones ----
    m = re.search(r"Retenciones Realizadas.*?\n(.*?)(?:Intereses / Anticipos)",
                  text, re.DOTALL)
    if m:
        block = m.group(1)
        for line in block.split("\n"):
            line = line.strip()
            if not line or line.startswith("Nro. Docum") \
                    or "Régimen" in line or "Regimen" in line:
                continue
            mm = re.match(
                r"^(\S+)\s+([A-Z]{2,3})\s+(.+?)\s+(\d+)\s+\(?([\d.,()-]+)\)?$",
                line)
            if mm:
                monto_raw = mm.group(5)
                monto = num(monto_raw)
                out["retenciones"].append({
                    "NRO_DOC": mm.group(1),
                    "TIPO": mm.group(2),
                    "REGIMEN": mm.group(3).strip(),
                    "NRO_CERT": mm.group(4),
                    "MONTO": abs(monto),
                })

    # ---- Cheques entregados ----
    pattern_chq = re.compile(
        r"Echeq\s+Emitido\s+(\d+)\s*"
        r"(?:Cta\s+Cte\s+)?Banco\s+(\S+(?:\s+\S+)*?)\s+"
        r"(\d{2}-\d{2}-\d{4})\s+([\d.,]+)"
    )
    for mm in pattern_chq.finditer(text):
        nro = mm.group(1).lstrip("0") or mm.group(1)
        f = parse_fecha(mm.group(3))
        out["cheques"].append({
            "TIPO": "Echeq",
            "NRO": nro,
            "BANCO": mm.group(2).strip(),
            "FECHA_VENC": fecha_str(f) if f else mm.group(3),
            "IMPORTE": num(mm.group(4)),
        })

    return out


def procesar_carpeta_ops(carpeta_ops, df_planilla=None):
    """Procesa todos los PDFs y devuelve 4 DataFrames + log de problemas.
    Filtra OPs de gastos generales (no prestador medico).
    """
    pdfs = sorted(glob.glob(os.path.join(carpeta_ops, "*.pdf")))
    pdfs = [p for p in pdfs if not os.path.basename(p).startswith(".")]

    cabeceras, comprobantes, retenciones, cheques = [], [], [], []
    descartadas = []
    problemas = []

    for path in pdfs:
        fname = os.path.basename(path)

        # Pre-filtro por nombre de archivo
        if _es_op_de_gasto(fname):
            descartadas.append({"archivo": fname,
                                 "motivo": "OP de gastos generales (filename)"})
            continue

        try:
            op = extraer_op_de_pdf(path)
        except Exception as e:
            problemas.append({"archivo": fname, "error": str(e)})
            continue

        # Post-filtro por concepto
        if _es_op_de_gasto(fname, op.get("CONCEPTO", "")):
            descartadas.append({"archivo": fname,
                                 "motivo": "OP de gastos generales (concepto)"})
            continue

        n_fact = sum(1 for c in op["comprobantes"]
                     if c["TIPO"] in ("FAC", "FA", "FCE"))
        n_nd = sum(1 for c in op["comprobantes"]
                   if c["TIPO"].startswith("ND"))
        monto_fact = sum(c["ESTE_PAGO"] for c in op["comprobantes"]
                          if c["TIPO"] in ("FAC", "FA", "FCE"))
        monto_nd = sum(c["ESTE_PAGO"] for c in op["comprobantes"]
                        if c["TIPO"].startswith("ND"))
        monto_ret = sum(r["MONTO"] for r in op["retenciones"])
        monto_chq = sum(c["IMPORTE"] for c in op["cheques"])

        cuadre = monto_fact + monto_nd - monto_ret
        diff_cuadre = round(op["TOTAL_OP"] - cuadre, 2)
        diff_cheques = round(op["TOTAL_OP"] - monto_chq, 2)

        cabeceras.append({
            "ARCHIVO": op["ARCHIVO"],
            "OP_NUMERO": op["OP_NUMERO"],
            "OP_FECHA": op["OP_FECHA"],
            "PRESTADOR": op["PRESTADOR"],
            "CUIT": op["CUIT"],
            "CONCEPTO": op["CONCEPTO"],
            "TOTAL_OP": op["TOTAL_OP"],
            "N_FACTURAS": n_fact,
            "N_NDS": n_nd,
            "MONTO_FACT": monto_fact,
            "MONTO_ND": monto_nd,
            "MONTO_RETENCIONES": monto_ret,
            "N_CHEQUES": len(op["cheques"]),
            "MONTO_CHEQUES": monto_chq,
            "DIFF_CUADRE": diff_cuadre,
            "DIFF_CHEQUES": diff_cheques,
        })
        for c in op["comprobantes"]:
            comprobantes.append({"OP_NUMERO": op["OP_NUMERO"], "CUIT": op["CUIT"],
                                 "PRESTADOR": op["PRESTADOR"], **c})
        for r in op["retenciones"]:
            retenciones.append({"OP_NUMERO": op["OP_NUMERO"], "CUIT": op["CUIT"],
                                "PRESTADOR": op["PRESTADOR"], **r})
        for ch in op["cheques"]:
            cheques.append({"OP_NUMERO": op["OP_NUMERO"], "CUIT": op["CUIT"],
                            "PRESTADOR": op["PRESTADOR"], **ch})

    df_cab = pd.DataFrame(cabeceras)
    df_comp = pd.DataFrame(comprobantes)
    df_ret = pd.DataFrame(retenciones)
    df_chq_op = pd.DataFrame(cheques)

    return {
        "cabecera": df_cab,
        "comprobantes": df_comp,
        "retenciones": df_ret,
        "cheques": df_chq_op,
        "problemas": problemas,
        "descartadas": descartadas,
        "total_pdfs": len(pdfs),
    }
