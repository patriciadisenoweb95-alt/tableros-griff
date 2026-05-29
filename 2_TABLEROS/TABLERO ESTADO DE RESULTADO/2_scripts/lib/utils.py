# -*- coding: utf-8 -*-
"""
Utilidades comunes: parseo de numeros, fechas, normalizacion de texto,
deteccion de periodo desde nombre de archivo.
"""

import re
import unicodedata
from datetime import datetime, date

from .config import MESES_ES, NOMBRE_MES, ANIO_DEFAULT, OS_NORMAL, CAT_NORMAL, \
                    CAT_DEFAULT


def num(x):
    """Convierte cualquier representacion de numero a float.
    Tolera formato AR (1.234.567,89), parentesis como negativo, signos $."""
    if x is None:
        return 0.0
    if isinstance(x, (int, float)):
        return float(x)
    s = str(x).strip()
    if not s or s.lower() in ("nan", "none", ""):
        return 0.0
    neg = s.startswith("(") and s.endswith(")")
    s = s.strip("()").replace("$", "").replace(" ", "")
    if "," in s and "." in s:
        s = s.replace(".", "").replace(",", ".")
    elif "," in s:
        s = s.replace(",", ".")
    try:
        v = float(s)
    except (ValueError, TypeError):
        return 0.0
    return -v if neg else v


def parse_fecha(x):
    """Devuelve un objeto date o None."""
    if x is None:
        return None
    if isinstance(x, datetime):
        return x.date()
    if isinstance(x, date):
        return x
    s = str(x).strip()
    if not s or s.lower() in ("nan", "none"):
        return None
    m = re.match(r"^(\d{4})-(\d{2})-(\d{2})", s)
    if m:
        try:
            return date(int(m.group(1)), int(m.group(2)), int(m.group(3)))
        except ValueError:
            return None
    m = re.match(r"^(\d{1,2})/(\d{1,2})/(\d{4})", s)
    if m:
        try:
            return date(int(m.group(3)), int(m.group(2)), int(m.group(1)))
        except ValueError:
            return None
    m = re.match(r"^(\d{1,2})-(\d{1,2})-(\d{4})", s)
    if m:
        try:
            return date(int(m.group(3)), int(m.group(2)), int(m.group(1)))
        except ValueError:
            return None
    return None


def fecha_iso(d):
    """Devuelve la fecha como YYYY-MM-DD, o None."""
    d = parse_fecha(d)
    return d.strftime("%Y-%m-%d") if d else None


def norm_text(s):
    """Quita acentos, espacios extra y mayusculiza."""
    if not isinstance(s, str):
        s = str(s) if s is not None else ""
    s = s.strip().upper()
    s = "".join(c for c in unicodedata.normalize("NFKD", s)
                if not unicodedata.combining(c))
    return re.sub(r"\s+", " ", s)


def norm_nombre(s):
    """Normaliza un nombre de prestador conservando mayusculas."""
    if not isinstance(s, str):
        s = str(s) if s is not None else ""
    return re.sub(r"\s+", " ", s.strip()).upper()


def norm_os(x):
    """Normaliza nombre de obra social. Devuelve la forma conocida o el texto
    original limpio si no la reconoce."""
    s = norm_text(x)
    return OS_NORMAL.get(s, s)


def norm_categoria(x):
    """Normaliza categoria de prestacion a la forma consolidada."""
    s = norm_text(x)
    if not s:
        return CAT_DEFAULT
    return CAT_NORMAL.get(s, CAT_DEFAULT)


def norm_cuit(x):
    """Devuelve el CUIT como string de digitos, o '' si invalido."""
    if x is None:
        return ""
    digits = re.sub(r"\D", "", str(x))
    return digits


def detectar_periodo(nombre_archivo):
    """Detecta 'MM-YYYY' desde un nombre de archivo. Si encuentra el mes pero
    no el anio, usa ANIO_DEFAULT. Devuelve None si no encuentra mes."""
    s = nombre_archivo.lower()
    m_ano = re.search(r"(20\d{2})", s)
    ano = int(m_ano.group(1)) if m_ano else None
    mes = None
    # Buscar mes en palabras
    for nombre, num_mes in sorted(MESES_ES.items(), key=lambda x: -len(x[0])):
        if re.search(r"\b" + nombre + r"\b", s):
            mes = num_mes
            break
    # Si no, buscar formato MM-YYYY / MM_YYYY / MM/YYYY
    if mes is None:
        m = re.search(r"\b(0?[1-9]|1[0-2])[-_/](20\d{2})\b", s)
        if m:
            mes = int(m.group(1))
            ano = int(m.group(2))
    if mes is None:
        return None
    if ano is None:
        ano = ANIO_DEFAULT
    return f"{mes:02d}-{ano}"


def periodo_label(periodo_codigo):
    """Convierte '02-2026' en 'Febrero 2026'."""
    if not periodo_codigo:
        return ""
    try:
        mes = int(periodo_codigo[:2])
        anio = periodo_codigo[3:]
        return f"{NOMBRE_MES.get(mes, '?')} {anio}"
    except (ValueError, IndexError):
        return periodo_codigo


def periodo_corto(periodo_codigo):
    """Convierte '02-2026' en 'Feb 26' (para botones)."""
    if not periodo_codigo:
        return ""
    try:
        mes = int(periodo_codigo[:2])
        anio = periodo_codigo[3:]
        return f"{NOMBRE_MES.get(mes, '?')[:3]} {anio[2:]}"
    except (ValueError, IndexError):
        return periodo_codigo


def periodo_sort_key(periodo_codigo):
    """Clave de ordenamiento cronologico para 'MM-YYYY'."""
    try:
        mes = int(periodo_codigo[:2])
        anio = int(periodo_codigo[3:])
        return anio * 100 + mes
    except (ValueError, IndexError):
        return 0
