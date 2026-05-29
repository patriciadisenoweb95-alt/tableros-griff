# -*- coding: utf-8 -*-
"""
Configuracion central del Tablero Estado de Resultado.
Si cambia el listado de OS, las categorias de costos o se agrega algo,
se modifica solo aca.
"""

# Anio por defecto cuando el nombre del archivo no lo incluye
ANIO_DEFAULT = 2026

# Obras sociales que se muestran en el tablero (en este orden)
OS_LIST = ["OSPEVIC", "OSPIF", "OSPLYFC", "OSPM", "OSSURRBAC", "AMSURRBAC", "UOM"]

# Sub-segmentos de OSPIF (solo para la tabla de detalle)
OSPIF_SUBS = ["OSPIF_Cordoba", "OSPIF_SantaFe", "OSPIF_BahBlanca"]

# Colores por obra social (identidad Griff)
OS_COLOR = {
    "OSPEVIC": "#0A1F8C", "OSPIF": "#0BC8FA", "OSPLYFC": "#7A52F4",
    "OSPM": "#0E9F6E", "OSSURRBAC": "#F2B705", "AMSURRBAC": "#E74C3C",
    "UOM": "#6B7691",
}

# --- ESTADO DE RESULTADO: mapeo de columnas del Excel ---
# (indice 0-based dentro de la fila, despues de la columna A=concepto)
ER_COLS = {
    "OSPEVIC": 1, "OSPIF": 2, "OSPIF_Cordoba": 3, "OSPIF_SantaFe": 4,
    "OSPIF_BahBlanca": 5, "OSPLYFC": 6, "OSPM": 7, "OSSURRBAC": 8,
    "AMSURRBAC": 9, "UOM": 10, "OTRAS_FC": 11, "TOTAL": 12,
}

# Conceptos del Estado de Resultado: clave interna -> texto a buscar en col A
ER_CONCEPTOS = {
    "afiliados": "Cantidad de Afiliados",
    "costo_capita": "Costo de la C",            # "Costo de la Capita"
    "subtotal_capita": "Subtotal C",            # "Subtotal Capita"
    "refuerzo_capita": "Refuerzo capita",
    "notas_credito": "Notas de Cr",             # "Notas de Credito / Debito"
    "ingresos_extras": "Otros Servicios",
    "ingresos_netos": "INGRESOS NETOS",
    "total_directos": "TOTAL EGRESOS DIRECTOS",
    "total_fijos": "TOTAL COSTOS FIJOS",
}

# Lineas de costos fijos a sumar por OS (texto a buscar). MUSCARELO es directo.
ER_LINEAS_FIJAS = [
    "Sueldos", "Centro Medico Russito", "Alquiler", "Servicios (luz",
    "Honorarios administraci", "Otros gastos fijos", "MARKETING",
]
ER_LINEA_MUSCARELO = "MUSCARELO"

# --- COSTOS PRESTACIONALES: normalizacion ---
OS_NORMAL = {
    "OSPEVIC": "OSPEVIC",
    "OSPIF": "OSPIF",
    "OSPLYFC": "OSPLYFC",
    "OSPM": "OSPM",
    "OSSURRBAC": "OSSURRBAC", "OSSURBAC": "OSSURRBAC",
    "OSSURBACC": "OSSURRBAC", "OSSRRBAC": "OSSURRBAC",
    "AMSURRBAC": "AMSURRBAC",
    "UOM": "UOM",
}

# Categorias de prestacion: variante -> forma consolidada
CAT_NORMAL = {
    "AMBULATORIO": "Ambulatorio", "AMBULARTORIO": "Ambulatorio",
    "AREA PROTEGIDA": "Ambulatorio",
    "INTERNADO": "Internado",
    "CAPITAS": "Capitado", "CAPITADO": "Capitado",
    "TRASLADO": "Traslado", "TRASLADOS": "Traslado", "AJUSTE": "Traslado",
    "INTERESES": "Intereses",
    "REFACTURACION": "Refacturacion",
    "PROTESIS": "Protesis",
}
CAT_DEFAULT = "Sin Clasificacion"

# Meses en espaniol (para detectar periodo desde nombre de archivo)
MESES_ES = {
    "enero": 1, "ene": 1, "febrero": 2, "feb": 2, "marzo": 3, "mar": 3,
    "abril": 4, "abr": 4, "mayo": 5, "may": 5, "junio": 6, "jun": 6,
    "julio": 7, "jul": 7, "agosto": 8, "ago": 8,
    "septiembre": 9, "sept": 9, "sep": 9, "set": 9,
    "octubre": 10, "oct": 10, "noviembre": 11, "nov": 11,
    "diciembre": 12, "dic": 12,
}

NOMBRE_MES = {
    1: "Enero", 2: "Febrero", 3: "Marzo", 4: "Abril", 5: "Mayo", 6: "Junio",
    7: "Julio", 8: "Agosto", 9: "Septiembre", 10: "Octubre", 11: "Noviembre",
    12: "Diciembre",
}
