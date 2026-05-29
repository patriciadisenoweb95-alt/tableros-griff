# -*- coding: utf-8 -*-
"""
Configuracion central del tablero.
Si en algun momento cambia el listado de OS o se agrega una nueva,
se modifica solo aca.
"""

# Obras sociales validas (cualquier otra cosa va a SIN_ASIGNACION)
OS_LIST = ["OSPEVIC", "OSPIF", "OSPLYFC", "OSSURRBAC", "OSPM"]

# Mapeo de variantes a la forma normalizada
OS_NORMAL = {
    "OSSURBAC": "OSSURRBAC",
    "OSSURBACC": "OSSURRBAC",
    "OSSRRBAC": "OSSURRBAC",
    "OSSURRBAC": "OSSURRBAC",
    "OSPEVIC": "OSPEVIC",
    "OSPIF": "OSPIF",
    "OSPLYFC": "OSPLYFC",
    "OSPM": "OSPM",
}

# Estados de cheque que se consideran "cerrados" (no a vencer)
ESTADOS_CERRADOS = {"Pagado", "Rechazado", "Anulado", "Repudiado"}

# Meses en español (para detectar periodo desde nombre de archivo)
MESES_ES = {
    "enero": 1, "ene": 1,
    "febrero": 2, "feb": 2,
    "marzo": 3, "mar": 3,
    "abril": 4, "abr": 4,
    "mayo": 5, "may": 5,
    "junio": 6, "jun": 6,
    "julio": 7, "jul": 7,
    "agosto": 8, "ago": 8,
    "septiembre": 9, "sept": 9, "sep": 9, "set": 9,
    "octubre": 10, "oct": 10,
    "noviembre": 11, "nov": 11,
    "diciembre": 12, "dic": 12,
}

NOMBRE_MES = {
    1: "Enero", 2: "Febrero", 3: "Marzo", 4: "Abril", 5: "Mayo", 6: "Junio",
    7: "Julio", 8: "Agosto", 9: "Septiembre", 10: "Octubre", 11: "Noviembre",
    12: "Diciembre"
}
