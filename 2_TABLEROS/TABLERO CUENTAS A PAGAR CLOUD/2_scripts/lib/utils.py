# -*- coding: utf-8 -*-
"""
Utilidades comunes: parseo de fechas, importes, normalizacion de strings.
"""

import re
import unicodedata
from datetime import datetime, date

from .config import OS_NORMAL, MESES_ES


def num(x):
    """Convierte cualquier representacion de numero (AR o intl) a float.
    Maneja parentesis como negativo, miles con punto, decimal con coma."""
    if x is None:
        return 0.0
    s = str(x).strip()
    if not s or s.lower() in ("nan", "none", ""):
        return 0.0
    neg = s.startswith("(") and s.endswith(")")
    s = s.strip("()").replace("$", "").replace(" ", "")
    if "," in s and "." in s:
        # Formato AR: 1.234.567,89
        s = s.replace(".", "").replace(",", ".")
    elif "," in s:
        # Solo coma -> es decimal
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
    s = str(x).strip()
    if not s or s.lower() in ("nan", "none"):
        return None
    # YYYY-MM-DD HH:MM:SS  o YYYY-MM-DD
    m = re.match(r"^(\d{4})-(\d{2})-(\d{2})", s)
    if m:
        try:
            return date(int(m.group(1)), int(m.group(2)), int(m.group(3)))
        except ValueError:
            return None
    # DD/MM/YYYY o D/M/YYYY
    m = re.match(r"^(\d{1,2})/(\d{1,2})/(\d{4})", s)
    if m:
        try:
            return date(int(m.group(3)), int(m.group(2)), int(m.group(1)))
        except ValueError:
            return None
    # DD-MM-YYYY
    m = re.match(r"^(\d{1,2})-(\d{1,2})-(\d{4})", s)
    if m:
        try:
            return date(int(m.group(3)), int(m.group(2)), int(m.group(1)))
        except ValueError:
            return None
    return None


def fecha_str(d):
    """Devuelve la fecha como DD/MM/YYYY, o '' si es None."""
    if not d:
        return ""
    if isinstance(d, str):
        d = parse_fecha(d)
        if not d:
            return ""
    return d.strftime("%d/%m/%Y")


def norm_text(s):
    """Quita acentos, espacios extra y mayusculiza."""
    if not isinstance(s, str):
        return ""
    s = s.strip().upper()
    s = "".join(c for c in unicodedata.normalize("NFKD", s)
                if not unicodedata.combining(c))
    return re.sub(r"\s+", " ", s)


def norm_nombre(s):
    """Normaliza un nombre de prestador conservando mayusculas."""
    if not isinstance(s, str):
        return ""
    return re.sub(r"\s+", " ", s.strip())


def norm_os(x):
    """Normaliza nombre de obra social. Devuelve la OS conocida o None."""
    if not isinstance(x, str):
        return None
    s = norm_text(x)
    return OS_NORMAL.get(s)


def norm_cuit(x):
    """Devuelve el CUIT como string de 11 digitos, o '' si invalido."""
    if x is None:
        return ""
    digits = re.sub(r"\D", "", str(x))
    return digits if len(digits) == 11 else ""


def detectar_periodo(nombre_archivo):
    """Detecta MM-YYYY desde un nombre de archivo. Devuelve None si no lo encuentra."""
    s = nombre_archivo.lower()
    # Buscar el ano (4 digitos entre 2020 y 2099)
    m_ano = re.search(r"(20\d{2})", s)
    ano = int(m_ano.group(1)) if m_ano else None
    # Buscar el mes en palabras
    mes = None
    for nombre, num_mes in MESES_ES.items():
        if re.search(r"\b" + nombre + r"\b", s):
            mes = num_mes
            break
    # Si no encuentra mes en palabras, buscar formato MM-YYYY o YYYY-MM
    if mes is None:
        m = re.search(r"\b(0?[1-9]|1[0-2])[-_/](20\d{2})\b", s)
        if m:
            mes = int(m.group(1))
            ano = int(m.group(2))
    if mes and ano:
        return f"{mes:02d}-{ano}"
    return None


def periodo_label(periodo_codigo):
    """Convierte '02-2026' en '02-2026 (Febrero)'."""
    from .config import NOMBRE_MES
    if not periodo_codigo:
        return ""
    try:
        mes = int(periodo_codigo[:2])
        return f"{periodo_codigo} ({NOMBRE_MES.get(mes, '?')})"
    except (ValueError, IndexError):
        return periodo_codigo
