# -*- coding: utf-8 -*-
"""
Utilidades comunes: parseo de fechas, importes, normalizacion de strings.
"""

import re
import unicodedata
from datetime import datetime, date, timedelta


def num(x):
    """Convierte representacion AR/intl de numero a float."""
    if x is None:
        return 0.0
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
    # Si ya es datetime/date
    if isinstance(x, datetime):
        return x.date()
    if isinstance(x, date):
        return x
    s = str(x).strip()
    if not s or s.lower() in ("nan", "none", "nat"):
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
    """Devuelve fecha como YYYY-MM-DD, o None."""
    if not d:
        return None
    if isinstance(d, str):
        d = parse_fecha(d)
        if not d:
            return None
    return d.strftime("%Y-%m-%d")


def fecha_str(d):
    """Devuelve fecha como DD/MM/YYYY, o ''."""
    if not d:
        return ""
    if isinstance(d, str):
        d = parse_fecha(d)
        if not d:
            return ""
    return d.strftime("%d/%m/%Y")


def add_days(d, n):
    """Suma n días a una fecha (date o YYYY-MM-DD)."""
    if isinstance(d, str):
        d = parse_fecha(d)
    if not d:
        return None
    return d + timedelta(days=n)


def excel_serial_to_date(serial):
    """Convierte serial de Excel (numero) a date."""
    try:
        n = float(serial)
    except (ValueError, TypeError):
        return None
    if n <= 0:
        return None
    # Excel epoch: 1899-12-30 (compensa bug del año bisiesto 1900)
    base = date(1899, 12, 30)
    return base + timedelta(days=int(n))


def norm_text(s):
    if not isinstance(s, str):
        return ""
    s = s.strip().upper()
    s = "".join(c for c in unicodedata.normalize("NFKD", s)
                if not unicodedata.combining(c))
    return re.sub(r"\s+", " ", s)


def norm_nombre(s):
    if not isinstance(s, str):
        return ""
    return re.sub(r"\s+", " ", s.strip())
