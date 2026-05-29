#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
ACTUALIZAR.PY - Tablero Griff Salud
Procesa PDFs nuevos en 'PDFs Emitidas', los carga al Excel, genera datos.js
para el dashboard y archiva los procesados en 'PDFs Procesados/AAAA-MM/'.

Uso: doble-click en actualizar.bat (Windows) o `python3 actualizar.py`
"""
import os, sys, re, json, shutil
from datetime import datetime, date
from collections import defaultdict

# Permitir ejecución desde cualquier directorio
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
os.chdir(SCRIPT_DIR)

# HUB unificado: dos niveles arriba (SCRIPT_DIR en HUB/2_TABLEROS/TABLERO X)
HUB = os.path.dirname(os.path.dirname(SCRIPT_DIR))
DIR_FAC = os.path.join(HUB, "1_DATOS", "facturacion")
DIR_OUT = os.path.join(HUB, "3_RESULTADOS", "facturacion")
os.makedirs(DIR_OUT, exist_ok=True)
PDF_PENDIENTES = os.path.join(DIR_FAC, "PDFs Emitidas")
PDF_PROCESADOS = os.path.join(DIR_FAC, "PDFs Procesados")
EXCEL_PATH = os.path.join(DIR_FAC, "Tablero_Facturacion_Impuestos.xlsx")
DATOS_JS = os.path.join(DIR_OUT, "datos.js")
COBRANZAS_UPDATES = os.path.join(DIR_FAC, "cobranzas_updates.json")

# Auto-instalar dependencias si faltan
def ensure(pkg, import_name=None):
    try:
        __import__(import_name or pkg)
    except ImportError:
        print(f"Instalando {pkg}...")
        import subprocess
        subprocess.check_call([sys.executable, "-m", "pip", "install", pkg, "--quiet"])

ensure("pdfplumber")
ensure("openpyxl")

import pdfplumber
import openpyxl
from openpyxl.styles import Font, PatternFill, Border, Side

# ============================================================================
# MAPEO CUIT → CLIENTE CORTO (editable acá si agregás clientes nuevos)
# ============================================================================
CUIT_A_CLIENTE = {
    "30661691707": "OSPIF",       # OSP Industria Fideera (alias OSPIF)
    "30710660995": "AMSURRBAC",   # Mutual Sindicato Recolectores
    "30606579906": "OSPEVIC",     # OSP Vigilancia y Seguridad Comercial
    "30714341746": "OSSURRBAC",   # OSP Sindicato Recolectores Residuos
    "30565846538": "OSPLYF",      # OSP Personal Luz y Fuerza Córdoba
    "30585207760": "UOM",         # OSP Unión Obrera Metalúrgica
    # Agregar nuevos clientes acá
}

CODIGOS_AFIP = {
    "001": "A",   "002": "NDA", "003": "NCA",
    "006": "B",   "007": "NDB", "008": "NCB",
    "011": "C",   "012": "NDC", "013": "NCC",
    "019": "E",   "020": "NDE", "021": "NCE",
}

CUIT_GRIFF = "30717134180"

# ============================================================================
# PARSER
# ============================================================================
def parse_money(s):
    if not s: return 0.0
    s = s.replace("$", "").strip().replace(".", "").replace(",", ".")
    try: return float(s)
    except: return 0.0

def quitar_tildes(s):
    """Normaliza texto: quita tildes para que el SUMIFS del Excel matchee bien."""
    if not s: return s
    import unicodedata
    return ''.join(c for c in unicodedata.normalize('NFD', s) if unicodedata.category(c) != 'Mn')

def parse_pdf(path):
    nombre = os.path.basename(path)
    m = re.match(r"(\d+)_(\d+)_(\d+)_(\d+)", nombre)
    cod_doc = m.group(2) if m else None
    pv_n = int(m.group(3)) if m else None
    num_n = int(m.group(4)) if m else None
    tipo = CODIGOS_AFIP.get(cod_doc, "?")

    with pdfplumber.open(path) as pdf:
        txt = pdf.pages[0].extract_text() or ""

    m_pv = re.search(r"Punto de Venta:\s*(\d+)\s+Comp\.?\s*Nro\.?:\s*(\d+)", txt)
    pv = int(m_pv.group(1)) if m_pv else pv_n
    num = int(m_pv.group(2)) if m_pv else num_n

    m_f = re.search(r"Fecha de Emisi[oó]n:\s*(\d{2}/\d{2}/\d{4})", txt)
    fecha = datetime.strptime(m_f.group(1), "%d/%m/%Y").date() if m_f else None

    m_per = re.search(r"Per[ií]odo Facturado Desde:\s*(\d{2}/\d{2}/\d{4})\s+Hasta:\s*(\d{2}/\d{2}/\d{4})", txt)
    per_desde = datetime.strptime(m_per.group(1), "%d/%m/%Y").date() if m_per else None
    per_hasta = datetime.strptime(m_per.group(2), "%d/%m/%Y").date() if m_per else None

    cuits = re.findall(r"CUIT:\s*(\d{11})", txt)
    cuit_cliente = next((c for c in cuits if c != CUIT_GRIFF), None)

    m_rs = re.search(r"Apellido y Nombre / Raz[oó]n Social:\s*(.+?)(?:Condici[oó]n frente al IVA|Domicilio:|$)", txt, re.DOTALL)
    razon_social_full = re.sub(r"\s+", " ", m_rs.group(1).strip()) if m_rs else "?"

    cliente_corto = CUIT_A_CLIENTE.get(cuit_cliente, razon_social_full[:30])

    # Concepto
    lines = txt.split("\n")
    cap_inicio = False
    detalle_lines = []
    SKIP = {"IVA", "Alicuota", "Código", "Codigo", ""}
    for line in lines:
        if "Código Producto" in line or "Codigo Producto" in line:
            cap_inicio = True
            continue
        if cap_inicio:
            if any(x in line for x in ["Subtotal:", "Importe Otros Tributos:", "Importe Exento:", "IVA 21%:", "IVA 10.5%:", "Pág."]):
                break
            ls = line.strip()
            if ls and ls not in SKIP and not ls.startswith("IVA"):
                detalle_lines.append(ls)
    concepto = detalle_lines[0] if detalle_lines else ""
    concepto_limpio = re.sub(r"\s+\d[\d.,]*\s+(unidades|kg|lt|m|m2|m3|hs)\s+.*$", "", concepto, flags=re.IGNORECASE).strip()
    if not concepto_limpio or concepto_limpio == concepto:
        concepto_limpio = re.sub(r"\s+\d[\d.,]{4,}.*$", "", concepto).strip()
    if not concepto_limpio:
        concepto_limpio = concepto
    # Normalizar: quitar tildes para que el SUMIFS del Checklist matchee bien
    concepto_limpio = quitar_tildes(concepto_limpio)

    def fm(pat):
        x = re.search(pat, txt)
        return parse_money(x.group(1)) if x else 0.0
    importe_total = fm(r"Importe Total:\s*\$?\s*([\d.,]+)")
    iva_21 = fm(r"IVA 21%:\s*\$?\s*([\d.,]+)")
    iva_105 = fm(r"IVA 10\.5%:\s*\$?\s*([\d.,]+)")
    importe_exento = fm(r"Importe Exento:\s*\$?\s*([\d.,]+)")
    otros_trib = fm(r"Importe Otros Tributos:\s*\$?\s*([\d.,]+)")

    # Cálculo Neto / NoGrav según tipo
    if tipo in ("A", "NCA", "NDA"):
        if iva_21 > 0:   neto_gravado = round(iva_21 / 0.21, 2)
        elif iva_105 > 0: neto_gravado = round(iva_105 / 0.105, 2)
        else: neto_gravado = 0
        no_gravado = importe_exento + max(0, importe_total - neto_gravado - iva_21 - iva_105 - otros_trib - importe_exento)
    else:
        m_ivac = re.search(r"IVA Contenido:\s*\$?\s*([\d.,]+)", txt)
        iva_contenido = parse_money(m_ivac.group(1)) if m_ivac else 0
        if iva_contenido > 0:
            neto_gravado = round(importe_total / 1.21, 2)
            no_gravado = 0
            iva_21 = round(neto_gravado * 0.21, 2)
        else:
            neto_gravado = 0
            no_gravado = importe_total
            iva_21 = 0
            iva_105 = 0

    return {
        "archivo": nombre, "tipo": tipo, "pto_vta": pv, "numero": num,
        "fecha": fecha, "periodo_desde": per_desde, "periodo_hasta": per_hasta,
        "cuit_cliente": cuit_cliente, "cliente": cliente_corto,
        "cliente_full": razon_social_full,
        "concepto": concepto_limpio, "neto_gravado": neto_gravado,
        "no_gravado": no_gravado, "iva_21": iva_21, "iva_105": iva_105,
        "otros_tributos": otros_trib, "total": importe_total,
    }

# ============================================================================
# CARGA EXCEL
# ============================================================================
def aplicar_cobranzas_updates():
    """Aplica al Excel los cambios de cobranzas que vienen del dashboard (cobranzas_updates.json)."""
    if not os.path.exists(COBRANZAS_UPDATES):
        return 0
    try:
        with open(COBRANZAS_UPDATES, 'r', encoding='utf-8') as f:
            updates = json.load(f)
    except Exception as e:
        print(f"  ATENCION: no se pudo leer cobranzas_updates.json: {e}")
        return 0
    if not updates:
        return 0
    wb = openpyxl.load_workbook(EXCEL_PATH)
    fac = wb["Facturacion"]
    # Indexar filas por clave (tipo + pv + num)
    idx = {}
    for r in range(2, fac.max_row + 1):
        tipo = fac.cell(row=r, column=2).value
        pv = fac.cell(row=r, column=3).value
        num = fac.cell(row=r, column=4).value
        if tipo and pv is not None and num is not None:
            idx[f"{tipo}-{pv}-{num}"] = r
    aplicados = 0
    for clave, datos in updates.items():
        r = idx.get(clave)
        if not r: continue
        if 'estado_cobro' in datos:
            fac.cell(row=r, column=19, value=datos['estado_cobro'])
        if 'fecha_cobro' in datos and datos['fecha_cobro']:
            try:
                fac.cell(row=r, column=20, value=datetime.strptime(datos['fecha_cobro'], "%Y-%m-%d").date())
            except: pass
        if 'monto_cobrado' in datos:
            try:
                fac.cell(row=r, column=21, value=float(datos['monto_cobrado']))
            except: pass
        aplicados += 1
    wb.save(EXCEL_PATH)
    # Renombrar el archivo aplicado para backup
    bak = COBRANZAS_UPDATES.replace('.json', f'_aplicado_{datetime.now().strftime("%Y%m%d_%H%M%S")}.json')
    try:
        os.rename(COBRANZAS_UPDATES, bak)
    except: pass
    return aplicados

def cargar_a_excel(facturas_nuevas):
    if not os.path.exists(EXCEL_PATH):
        print(f"ERROR: No se encontró {EXCEL_PATH}")
        return [], 0
    wb = openpyxl.load_workbook(EXCEL_PATH)
    fac = wb["Facturacion"]

    # Construir set de claves ya cargadas (Tipo + PV + Num)
    cargadas = set()
    primera_libre = 2
    for r in range(2, fac.max_row + 1):
        tipo = fac.cell(row=r, column=2).value
        pv = fac.cell(row=r, column=3).value
        num = fac.cell(row=r, column=4).value
        if tipo and pv is not None and num is not None:
            cargadas.add((tipo, int(pv), int(num)))
            primera_libre = r + 1
        elif not any([tipo, pv, num]):
            if primera_libre < r:
                pass
            else:
                primera_libre = r
                break

    blue_font = Font(name="Calibri", color="0000FF", size=10)
    thin = Side(border_style="thin", color="B0B0B0")
    border = Border(left=thin, right=thin, top=thin, bottom=thin)

    insertadas = []
    duplicadas = 0
    r = primera_libre
    for f in sorted(facturas_nuevas, key=lambda x: (x["fecha"], x["numero"])):
        clave = (f["tipo"], f["pto_vta"], f["numero"])
        if clave in cargadas:
            duplicadas += 1
            continue
        # Cargar fila
        fac.cell(row=r, column=1, value=f["fecha"])
        fac.cell(row=r, column=2, value=f["tipo"])
        fac.cell(row=r, column=3, value=f["pto_vta"])
        fac.cell(row=r, column=4, value=f["numero"])
        fac.cell(row=r, column=5, value=f["cliente"])
        fac.cell(row=r, column=6, value=f["cuit_cliente"])
        fac.cell(row=r, column=7, value=f["concepto"])
        fac.cell(row=r, column=9, value=f["neto_gravado"])
        fac.cell(row=r, column=10, value=f["no_gravado"])
        # IVA 21% se pisa con la fórmula original; si hay valor cargado lo guardamos en col 12 (10.5%) si fuera ese caso
        if f["iva_105"] > 0:
            fac.cell(row=r, column=12, value=f["iva_105"])
        fac.cell(row=r, column=13, value=f["otros_tributos"])
        fac.cell(row=r, column=18, value="Emitida")
        fac.cell(row=r, column=19, value="Pendiente")
        fac.cell(row=r, column=21, value=0)  # Monto Cobrado default 0
        fac.cell(row=r, column=23, value=f"Auto: {f['archivo']} | {f['cliente_full'][:60]}")  # Observaciones
        # Estilo azul (input) para cols cargadas
        for col in [1,2,3,4,5,6,7,9,10,12,13,18,19,21,23]:
            cc = fac.cell(row=r, column=col)
            cc.font = blue_font
            cc.border = border
        insertadas.append((r, f))
        cargadas.add(clave)
        r += 1

    wb.save(EXCEL_PATH)
    return insertadas, duplicadas

# ============================================================================
# ARCHIVADO PDFs
# ============================================================================
def archivar_pdfs(facturas):
    movidos = 0
    for f in facturas:
        if not f["fecha"]: continue
        periodo = f["fecha"].strftime("%Y-%m")
        dest_dir = os.path.join(PDF_PROCESADOS, periodo)
        os.makedirs(dest_dir, exist_ok=True)
        src = os.path.join(PDF_PENDIENTES, f["archivo"])
        dst = os.path.join(dest_dir, f["archivo"])
        if os.path.exists(src) and not os.path.exists(dst):
            shutil.move(src, dst)
            movidos += 1
        elif os.path.exists(src) and os.path.exists(dst):
            # Ya existe en destino - eliminar el de pendientes
            os.remove(src)
            movidos += 1
    return movidos

# ============================================================================
# GENERAR datos.js (para dashboard sin importar manual)
# ============================================================================
def generar_datos_js():
    """Lee el Excel ya recalculado y genera datos.js con todo lo del dashboard."""
    if not os.path.exists(EXCEL_PATH):
        return
    wb = openpyxl.load_workbook(EXCEL_PATH, data_only=True)
    out = {"timestamp": datetime.now().strftime("%Y-%m-%d %H:%M"),
           "facturas": [], "impuestos_mensual": {}, "checklist": [], "kpis": {}}

    # Facturas - calculamos valores efectivos en Python para no depender del recálculo
    # Mapeo concepto → actividad IIBB (igual que en el Excel)
    def detectar_actividad(concepto):
        if not concepto: return None
        c = str(concepto).upper()
        keys_651 = ["CAPITA","REFUERZO","VACUNACION","ENFERMERIA","APORTES"]
        keys_702 = ["HONORARIOS","ADMINISTRACION","GERENCIAMIENTO","ALQUILER","AUDITORIA","PRESTACIONAL"]
        for k in keys_651:
            if k in c: return 651110
        for k in keys_702:
            if k in c: return 702010
        return 702010  # default
    IVA_GENERAL_RATE = 0.21
    fac = wb["Facturacion"]
    for r in range(2, fac.max_row + 1):
        tipo = fac.cell(row=r, column=2).value
        if not tipo: continue
        fecha_val = fac.cell(row=r, column=1).value
        concepto = fac.cell(row=r, column=7).value
        neto = float(fac.cell(row=r, column=9).value or 0)
        no_grav = float(fac.cell(row=r, column=10).value or 0)
        iva105 = float(fac.cell(row=r, column=12).value or 0)
        percep = float(fac.cell(row=r, column=13).value or 0)
        # IVA 21% se calcula si neto > 0
        iva21 = round(neto * IVA_GENERAL_RATE, 2) if neto > 0 else 0
        # Total
        total = neto + no_grav + iva21 + iva105 + percep
        # Signo
        signo = -1 if str(tipo).upper().startswith("NC") else 1
        # Actividad
        actividad_excel = fac.cell(row=r, column=8).value
        # Si la celda tiene fórmula no resuelta, lo calculamos
        if isinstance(actividad_excel, str) and actividad_excel.startswith("="):
            actividad = detectar_actividad(concepto)
        else:
            actividad = actividad_excel or detectar_actividad(concepto)
        # Fecha
        anio = fecha_val.year if hasattr(fecha_val, 'year') else None
        mes = fecha_val.month if hasattr(fecha_val, 'month') else None
        # Estado cobro y monto cobrado
        monto_cobrado = float(fac.cell(row=r, column=21).value or 0)
        saldo_pendiente = total - monto_cobrado

        fila = {
            "fecha": str(fecha_val or ""),
            "tipo": tipo,
            "pto_vta": fac.cell(row=r, column=3).value,
            "numero": fac.cell(row=r, column=4).value,
            "cliente": fac.cell(row=r, column=5).value,
            "concepto": concepto,
            "actividad": actividad,
            "neto": neto,
            "no_grav": no_grav,
            "iva21": iva21,
            "iva105": iva105,
            "total": total,
            "anio": anio,
            "mes": mes,
            "estado_afip": fac.cell(row=r, column=18).value,
            "estado_cobro": fac.cell(row=r, column=19).value,
            "fecha_cobro": str(fac.cell(row=r, column=20).value) if fac.cell(row=r, column=20).value else "",
            "monto_cobrado": monto_cobrado,
            "saldo_pendiente": saldo_pendiente,
            "signo": signo,
            "neto_efec": neto * signo,
            "no_grav_efec": no_grav * signo,
            "iva21_efec": iva21 * signo,
            "total_efec": total * signo,
        }
        out["facturas"].append(fila)

    # Impuestos mensuales: calculamos en Python para no depender del recálculo del Excel
    # Leer parámetros de Reglas
    reglas = wb["Reglas"]
    coef_caba = 0.0433
    coef_cba = 0.9567
    alic_702_caba = 0.030
    alic_651_caba = 0.055
    alic_702_cba = 0.055
    alic_651_cba = 0.030
    tasa_2026 = 0.049
    pct_credito = 0.30
    # Buscar valores reales en hoja Reglas si están
    for r in range(1, reglas.max_row + 1):
        lbl = reglas.cell(row=r, column=2).value
        if not lbl: continue
        l = str(lbl).strip()
        if l == "CABA":
            v = reglas.cell(row=r, column=4).value
            if isinstance(v, (int, float)): coef_caba = v
        elif l == "Córdoba":
            v = reglas.cell(row=r, column=4).value
            if isinstance(v, (int, float)): coef_cba = v
        elif l == "702010":
            v_caba = reglas.cell(row=r, column=4).value
            v_cba = reglas.cell(row=r, column=5).value
            if isinstance(v_caba, (int, float)): alic_702_caba = v_caba
            if isinstance(v_cba, (int, float)): alic_702_cba = v_cba
        elif l == "651110":
            v_caba = reglas.cell(row=r, column=4).value
            v_cba = reglas.cell(row=r, column=5).value
            if isinstance(v_caba, (int, float)): alic_651_caba = v_caba
            if isinstance(v_cba, (int, float)): alic_651_cba = v_cba
        elif l == 2026 or str(l) == "2026":
            v = reglas.cell(row=r, column=3).value
            if isinstance(v, (int, float)): tasa_2026 = v
        elif "% Crédito" in l:
            v = reglas.cell(row=r, column=3).value
            if isinstance(v, (int, float)): pct_credito = v

    # Inicializar arrays por mes
    def empty_meses(): return {f"m{m}":0.0 for m in range(1,13)}
    base_total = empty_meses(); base_702 = empty_meses(); base_651 = empty_meses()
    neto_grav = empty_meses(); iva_debito = empty_meses()
    # Para cada factura no anulada del año 2026
    for f in out["facturas"]:
        if f["anio"] != 2026 or f["estado_afip"] == "Anulada": continue
        m = f["mes"]
        if not m: continue
        mk = f"m{m}"
        # Suma efectiva (con signo) de neto + nograv
        suma = (f["neto"] + f["no_grav"]) * f["signo"]
        base_total[mk] += suma
        if f["actividad"] == 702010:
            base_702[mk] += suma
        elif f["actividad"] == 651110:
            base_651[mk] += suma
        # Neto Gravado (para IVA Débito)
        neto_grav[mk] += f["neto"] * f["signo"]
        iva_debito[mk] += (f["iva21"] + f["iva105"]) * f["signo"]

    def add_anio(d):
        d["anio"] = sum(d[f"m{m}"] for m in range(1,13))
        return d
    def fila(label, d):
        out["impuestos_mensual"][label] = {"label": label, **add_anio({**d})}

    fila("Total Facturado (Neto + Exento)", base_total)
    fila("  → Actividad 702010 (Gerenciamiento)", base_702)
    fila("  → Actividad 651110 (Seguros)", base_651)
    fila("Neto Gravado 21%", neto_grav)
    fila("IVA Débito Fiscal (21%)", iva_debito)

    iva_credito = {f"m{m}": iva_debito[f"m{m}"]*pct_credito for m in range(1,13)}
    fila("IVA Crédito Fiscal estimado (prorrateo)", iva_credito)
    iva_saldo = {f"m{m}": max(0, iva_debito[f"m{m}"]-iva_credito[f"m{m}"]) for m in range(1,13)}
    fila("IVA Saldo a pagar (estimado)", iva_saldo)

    # IIBB CABA
    base_caba_702 = {f"m{m}": base_702[f"m{m}"]*coef_caba for m in range(1,13)}
    base_caba_651 = {f"m{m}": base_651[f"m{m}"]*coef_caba for m in range(1,13)}
    fila("Base distribuida CABA - 702010", base_caba_702)
    fila("Base distribuida CABA - 651110", base_caba_651)
    imp_caba_702 = {f"m{m}": base_caba_702[f"m{m}"]*alic_702_caba for m in range(1,13)}
    imp_caba_651 = {f"m{m}": base_caba_651[f"m{m}"]*alic_651_caba for m in range(1,13)}
    fila("Impuesto IIBB CABA - 702010 (3%)", imp_caba_702)
    fila("Impuesto IIBB CABA - 651110 (5,5%)", imp_caba_651)
    iibb_caba = {f"m{m}": imp_caba_702[f"m{m}"]+imp_caba_651[f"m{m}"] for m in range(1,13)}
    fila("IIBB CABA - Total Determinado", iibb_caba)
    fila("IIBB CABA - A pagar (estimado)", iibb_caba)

    # IIBB Cordoba
    base_cba_702 = {f"m{m}": base_702[f"m{m}"]*coef_cba for m in range(1,13)}
    base_cba_651 = {f"m{m}": base_651[f"m{m}"]*coef_cba for m in range(1,13)}
    fila("Base distribuida Córdoba - 702010", base_cba_702)
    fila("Base distribuida Córdoba - 651110", base_cba_651)
    imp_cba_702 = {f"m{m}": base_cba_702[f"m{m}"]*alic_702_cba for m in range(1,13)}
    imp_cba_651 = {f"m{m}": base_cba_651[f"m{m}"]*alic_651_cba for m in range(1,13)}
    fila("Impuesto IIBB Cba - 702010 (5,5%)", imp_cba_702)
    fila("Impuesto IIBB Cba - 651110 (3%)", imp_cba_651)
    iibb_cba = {f"m{m}": imp_cba_702[f"m{m}"]+imp_cba_651[f"m{m}"] for m in range(1,13)}
    fila("IIBB Cba - Total Determinado", iibb_cba)
    fila("IIBB Cba - A pagar (estimado)", iibb_cba)
    fila("IIBB Córdoba", iibb_cba)  # alias compat

    # Tasa Comercio Cba
    base_tasa = {f"m{m}": base_cba_702[f"m{m}"]+base_cba_651[f"m{m}"] for m in range(1,13)}
    fila("Base imponible (Facturación Cba)", base_tasa)
    tasa_det = {f"m{m}": base_tasa[f"m{m}"]*tasa_2026 for m in range(1,13)}
    fila("Tasa Comercio - Determinado", tasa_det)
    fila("Tasa Comercio - A pagar (estimado)", tasa_det)

    # Resumen mensual
    fila("IVA", iva_saldo)
    fila("IIBB CABA", iibb_caba)
    fila("Tasa Comercio Cba", tasa_det)
    total_imp = {f"m{m}": iva_saldo[f"m{m}"]+iibb_caba[f"m{m}"]+iibb_cba[f"m{m}"]+tasa_det[f"m{m}"] for m in range(1,13)}
    fila("TOTAL IMPUESTOS DEL MES", total_imp)

    # Checklist - calculamos en Python por cliente
    chk = wb["Checklist"]
    clientes_check = []
    for r in range(3, chk.max_row + 1):
        cli = chk.cell(row=r, column=1).value
        conc = chk.cell(row=r, column=2).value
        if not cli or "TOTAL" in str(cli).upper() or "EVENT" in str(cli).upper() or "CLIENTES EVENTUAL" in str(cli).upper():
            continue
        clientes_check.append((str(cli).strip(), conc))
    for cli, conc in clientes_check:
        fila = {"cliente": cli, "concepto": conc, "actividad": "multi"}
        for m in range(1, 13):
            total_mes = sum(
                f["total_efec"]
                for f in out["facturas"]
                if f["cliente"] == cli and f["mes"] == m and f["anio"] == 2026 and f["estado_afip"] != "Anulada"
            )
            fila[f"m{m}"] = total_mes
        fila["total"] = sum(fila[f"m{m}"] for m in range(1,13))
        out["checklist"].append(fila)

    # Hojas de detalle por impuesto - construidos en Python
    out["detalle_impuestos"] = {}
    def mk_num(d): return [{"v": d.get(f"m{m}",0), "tipo":"num"} for m in range(1,13)]
    def mk_total_num(d): return {"v": sum(d.get(f"m{m}",0) for m in range(1,13)), "tipo":"num"}
    def mk_const(v, tipo="num"): return [{"v": v, "tipo": tipo} for _ in range(12)]
    def mk_fecha_venc(dia):
        return [{"v": f"2026-{(m+1):02d}-{dia:02d}" if m<12 else f"2027-01-{dia:02d}", "tipo":"fecha"} for m in range(0,12)]

    no_grav_total = {f"m{m}": 0.0 for m in range(1,13)}
    for f in out["facturas"]:
        if f["anio"]==2026 and f["estado_afip"]!="Anulada" and f["mes"]:
            no_grav_total[f"m{f['mes']}"] += f["no_grav"] * f["signo"]

    iva_filas = [
        {"label":"Operaciones del período","meses":mk_const(None,"texto"),"total":{"v":None,"tipo":"texto"}},
        {"label":"Neto Gravado 21%","meses":mk_num(neto_grav),"total":mk_total_num(neto_grav)},
        {"label":"No Gravado / Exento","meses":mk_num(no_grav_total),"total":mk_total_num(no_grav_total)},
        {"label":"Total Facturado (neto)","meses":mk_num(base_total),"total":mk_total_num(base_total)},
        {"label":"IVA Débito Fiscal","meses":mk_const(None,"texto"),"total":{"v":None,"tipo":"texto"}},
        {"label":"IVA Débito 21%","meses":mk_num(iva_debito),"total":mk_total_num(iva_debito)},
        {"label":"Total IVA Débito","meses":mk_num(iva_debito),"total":mk_total_num(iva_debito)},
        {"label":"IVA Crédito Fiscal","meses":mk_const(None,"texto"),"total":{"v":None,"tipo":"texto"}},
        {"label":"% Crédito estimado (prorrateo) (Reglas)","meses":mk_const(pct_credito),"total":{"v":pct_credito,"tipo":"num"}},
        {"label":"IVA Crédito estimado (Débito × %)","meses":mk_num(iva_credito),"total":mk_total_num(iva_credito)},
        {"label":"Total IVA Crédito","meses":mk_num(iva_credito),"total":mk_total_num(iva_credito)},
        {"label":"Liquidación","meses":mk_const(None,"texto"),"total":{"v":None,"tipo":"texto"}},
        {"label":"Saldo Técnico (Débito - Crédito)","meses":mk_num({f"m{m}":iva_debito[f"m{m}"]-iva_credito[f"m{m}"] for m in range(1,13)}),"total":{"v":sum(iva_debito[f"m{m}"]-iva_credito[f"m{m}"] for m in range(1,13)),"tipo":"num"}},
        {"label":"A pagar (si saldo positivo)","meses":mk_num(iva_saldo),"total":mk_total_num(iva_saldo)},
        {"label":"Vencimientos y pagos","meses":mk_const(None,"texto"),"total":{"v":None,"tipo":"texto"}},
        {"label":"Vencimiento DDJJ + pago","meses":mk_fecha_venc(20),"total":{"v":None,"tipo":"texto"}},
    ]
    out["detalle_impuestos"]["Detalle IVA"] = iva_filas

    tasa_filas = [
        {"label":"Alícuota aplicable","meses":mk_const(None,"texto"),"total":{"v":None,"tipo":"texto"}},
        {"label":"Alícuota 2026","meses":mk_const(tasa_2026),"total":{"v":tasa_2026,"tipo":"num"}},
        {"label":"Liquidación mensual","meses":mk_const(None,"texto"),"total":{"v":None,"tipo":"texto"}},
        {"label":"1. Base Imponible (Facturación Cba)","meses":mk_num(base_tasa),"total":mk_total_num(base_tasa)},
        {"label":"2. Impuesto Determinado (Base × Alícuota)","meses":mk_num(tasa_det),"total":mk_total_num(tasa_det)},
        {"label":"6. A pagar (estimado)","meses":mk_num(tasa_det),"total":mk_total_num(tasa_det)},
        {"label":"8. Total a pagar (con intereses)","meses":mk_num(tasa_det),"total":mk_total_num(tasa_det)},
        {"label":"Vencimientos y pagos","meses":mk_const(None,"texto"),"total":{"v":None,"tipo":"texto"}},
        {"label":"Vencimiento (15 del mes siguiente)","meses":mk_fecha_venc(15),"total":{"v":None,"tipo":"texto"}},
    ]
    out["detalle_impuestos"]["Detalle Tasa Cba"] = tasa_filas

    iibb_caba_filas = [
        {"label":"Coeficiente Unificado","meses":mk_const(None,"texto"),"total":{"v":None,"tipo":"texto"}},
        {"label":"Coeficiente Unificado ","meses":mk_const(coef_caba),"total":{"v":coef_caba,"tipo":"num"}},
        {"label":"Bases Imponibles TOTALES (toda la actividad)","meses":mk_const(None,"texto"),"total":{"v":None,"tipo":"texto"}},
        {"label":"702010 - Servicios Gerenciamiento (total)","meses":mk_num(base_702),"total":mk_total_num(base_702)},
        {"label":"651110 - Servicios Seguros (total)","meses":mk_num(base_651),"total":mk_total_num(base_651)},
        {"label":"Bases Imponibles DISTRIBUIDAS a CABA (× coef)","meses":mk_const(None,"texto"),"total":{"v":None,"tipo":"texto"}},
        {"label":"702010 - Servicios Gerenciamiento","meses":mk_num(base_caba_702),"total":mk_total_num(base_caba_702)},
        {"label":"651110 - Servicios Seguros","meses":mk_num(base_caba_651),"total":mk_total_num(base_caba_651)},
        {"label":"TOTAL Base Imponible Jurisdiccional","meses":mk_num({f"m{m}":base_caba_702[f"m{m}"]+base_caba_651[f"m{m}"] for m in range(1,13)}),"total":{"v":sum(base_caba_702[f"m{m}"]+base_caba_651[f"m{m}"] for m in range(1,13)),"tipo":"num"}},
        {"label":"Alícuotas","meses":mk_const(None,"texto"),"total":{"v":None,"tipo":"texto"}},
        {"label":"702010 - Servicios Gerenciamiento ","meses":mk_const(alic_702_caba),"total":{"v":alic_702_caba,"tipo":"num"}},
        {"label":"651110 - Servicios Seguros ","meses":mk_const(alic_651_caba),"total":{"v":alic_651_caba,"tipo":"num"}},
        {"label":"Impuesto Determinado","meses":mk_const(None,"texto"),"total":{"v":None,"tipo":"texto"}},
        {"label":"Impuesto 702010 (= base × alícuota)","meses":mk_num(imp_caba_702),"total":mk_total_num(imp_caba_702)},
        {"label":"Impuesto 651110 (= base × alícuota)","meses":mk_num(imp_caba_651),"total":mk_total_num(imp_caba_651)},
        {"label":"Sub-total Impuesto","meses":mk_num(iibb_caba),"total":mk_total_num(iibb_caba)},
        {"label":"Total Determinado","meses":mk_num(iibb_caba),"total":mk_total_num(iibb_caba)},
        {"label":"A pagar (si saldo positivo)","meses":mk_num(iibb_caba),"total":mk_total_num(iibb_caba)},
        {"label":"Vencimientos y pagos","meses":mk_const(None,"texto"),"total":{"v":None,"tipo":"texto"}},
        {"label":"Vencimiento (cronograma CM)","meses":mk_fecha_venc(18),"total":{"v":None,"tipo":"texto"}},
    ]
    out["detalle_impuestos"]["Detalle IIBB CABA"] = iibb_caba_filas

    iibb_cba_filas = [
        {"label":"Coeficiente Unificado","meses":mk_const(None,"texto"),"total":{"v":None,"tipo":"texto"}},
        {"label":"Coeficiente Unificado ","meses":mk_const(coef_cba),"total":{"v":coef_cba,"tipo":"num"}},
        {"label":"Bases Imponibles TOTALES (toda la actividad)","meses":mk_const(None,"texto"),"total":{"v":None,"tipo":"texto"}},
        {"label":"702010 - Servicios Gerenciamiento (total)","meses":mk_num(base_702),"total":mk_total_num(base_702)},
        {"label":"651110 - Servicios Seguros (total)","meses":mk_num(base_651),"total":mk_total_num(base_651)},
        {"label":"Bases Imponibles DISTRIBUIDAS a Cordoba (× coef)","meses":mk_const(None,"texto"),"total":{"v":None,"tipo":"texto"}},
        {"label":"702010 - Servicios Gerenciamiento","meses":mk_num(base_cba_702),"total":mk_total_num(base_cba_702)},
        {"label":"651110 - Servicios Seguros","meses":mk_num(base_cba_651),"total":mk_total_num(base_cba_651)},
        {"label":"TOTAL Base Imponible Jurisdiccional","meses":mk_num({f"m{m}":base_cba_702[f"m{m}"]+base_cba_651[f"m{m}"] for m in range(1,13)}),"total":{"v":sum(base_cba_702[f"m{m}"]+base_cba_651[f"m{m}"] for m in range(1,13)),"tipo":"num"}},
        {"label":"Alícuotas","meses":mk_const(None,"texto"),"total":{"v":None,"tipo":"texto"}},
        {"label":"702010 - Servicios Gerenciamiento ","meses":mk_const(alic_702_cba),"total":{"v":alic_702_cba,"tipo":"num"}},
        {"label":"651110 - Servicios Seguros ","meses":mk_const(alic_651_cba),"total":{"v":alic_651_cba,"tipo":"num"}},
        {"label":"Impuesto Determinado","meses":mk_const(None,"texto"),"total":{"v":None,"tipo":"texto"}},
        {"label":"Impuesto 702010 (= base × alícuota)","meses":mk_num(imp_cba_702),"total":mk_total_num(imp_cba_702)},
        {"label":"Impuesto 651110 (= base × alícuota)","meses":mk_num(imp_cba_651),"total":mk_total_num(imp_cba_651)},
        {"label":"Sub-total Impuesto","meses":mk_num(iibb_cba),"total":mk_total_num(iibb_cba)},
        {"label":"Total Determinado","meses":mk_num(iibb_cba),"total":mk_total_num(iibb_cba)},
        {"label":"A pagar (si saldo positivo)","meses":mk_num(iibb_cba),"total":mk_total_num(iibb_cba)},
        {"label":"Vencimientos y pagos","meses":mk_const(None,"texto"),"total":{"v":None,"tipo":"texto"}},
        {"label":"Vencimiento (cronograma CM)","meses":mk_fecha_venc(18),"total":{"v":None,"tipo":"texto"}},
    ]
    out["detalle_impuestos"]["Detalle IIBB Cba"] = iibb_cba_filas

    # Resumen (KPIs)
    res = wb["Resumen"]
    out["kpis"] = {
        "total_facturado": sum(f["total_efec"] for f in out["facturas"] if f["anio"]==2026 and f["estado_afip"]!="Anulada"),
        "total_iva": sum(f["iva21_efec"] for f in out["facturas"] if f["anio"]==2026 and f["estado_afip"]!="Anulada"),
        "total_con_iva": sum(f["total_efec"] for f in out["facturas"] if f["anio"]==2026 and f["estado_afip"]!="Anulada"),
        "cant_facturas": len([f for f in out["facturas"] if f["anio"]==2026 and f["estado_afip"]!="Anulada"]),
        "iva_anio": sum(iva_saldo[f"m{m}"] for m in range(1,13)),
        "iibb_caba": sum(iibb_caba[f"m{m}"] for m in range(1,13)),
        "iibb_cba": sum(iibb_cba[f"m{m}"] for m in range(1,13)),
        "tasa_cba": sum(tasa_det[f"m{m}"] for m in range(1,13)),
        "total_impuestos": sum(total_imp[f"m{m}"] for m in range(1,13)),
        "cobrado": 0, "pendiente": 0, "vencido": 0, "pct_cobrado": 0,
    }

    with open(DATOS_JS, "w", encoding="utf-8") as f:
        f.write("// Auto-generado por actualizar.py - No editar manualmente\n")
        f.write("window.DATOS = " + json.dumps(out, ensure_ascii=False, default=str, indent=2) + ";\n")

def recalc_excel():
    """Intenta recalcular formulas usando libreoffice headless."""
    import subprocess
    soffice_paths = [
        r"C:\Program Files\LibreOffice\program\soffice.exe",
        r"C:\Program Files (x86)\LibreOffice\program\soffice.exe",
        "/usr/bin/soffice", "/usr/bin/libreoffice",
        "soffice", "libreoffice"
    ]
    for sp in soffice_paths:
        try:
            subprocess.run([sp, "--headless", "--calc", "--convert-to", "xlsx",
                          "--outdir", os.path.dirname(EXCEL_PATH), EXCEL_PATH],
                          timeout=30, capture_output=True, check=False)
            return True
        except (FileNotFoundError, OSError, subprocess.TimeoutExpired):
            continue
    return False

def main():
    print("=" * 60)
    print("  TABLERO GRIFF SALUD - Actualización automática")
    print("=" * 60)

    if not os.path.isdir(PDF_PENDIENTES):
        os.makedirs(PDF_PENDIENTES, exist_ok=True)

    pdfs = sorted([os.path.join(PDF_PENDIENTES, f) for f in os.listdir(PDF_PENDIENTES)
                   if f.lower().endswith(".pdf")])
    print(f"\nPDFs encontrados en 'PDFs Emitidas': {len(pdfs)}")

    print("\nAplicando cobranzas pendientes del dashboard (si las hay)...")
    cobranzas_aplicadas = aplicar_cobranzas_updates()
    print(f"  Aplicadas: {cobranzas_aplicadas}")

    if not pdfs:
        print("No hay PDFs nuevos para procesar.")
        print("\nGenerando datos.js (calculado en Python, no depende del cache del Excel)...")
        generar_datos_js()
        print(f"OK: datos.js actualizado")
        return

    print("\nParseando PDFs...")
    facturas = []
    errores = 0
    for p in pdfs:
        try:
            r = parse_pdf(p)
            facturas.append(r)
            print(f"  OK  {r['tipo']:5} {r['pto_vta']:05d}-{r['numero']:08d}  {(r['fecha'] or '').strftime('%d/%m/%Y') if r['fecha'] else 'sin fecha':<11}  {r['cliente']:<12}  ${r['total']:>14,.2f}")
        except Exception as e:
            errores += 1
            print(f"  ERROR {os.path.basename(p)}: {e}")

    print(f"\nCargando al Excel...")
    insertadas, duplicadas = cargar_a_excel(facturas)
    print(f"  Insertadas: {len(insertadas)}")
    print(f"  Duplicadas (ya estaban):  {duplicadas}")

    print(f"\nArchivando PDFs en 'PDFs Procesados'...")
    movidos = archivar_pdfs(facturas)
    print(f"  Movidos:    {movidos}")

    print(f"\nGenerando datos.js (calculado en Python)...")
    generar_datos_js()
    print(f"  OK: {DATOS_JS}")

    print("\n" + "=" * 60)
    print("RESUMEN POR CLIENTE (período actual procesado)")
    print("=" * 60)
    por_cli = defaultdict(lambda: {"f": 0, "n": 0, "total": 0})
    for f in facturas:
        signo = -1 if f["tipo"].startswith("NC") else 1
        por_cli[f["cliente"]]["total"] += f["total"] * signo
        if f["tipo"].startswith("NC"):
            por_cli[f["cliente"]]["n"] += 1
        else:
            por_cli[f["cliente"]]["f"] += 1
    for cli, d in sorted(por_cli.items(), key=lambda x: -x[1]["total"]):
        print(f"  {cli:<12}  Fc: {d['f']:>2}  NC: {d['n']:>2}  Total: ${d['total']:>15,.2f}")
    print("=" * 60)
    print("\nLISTO. Abrí dashboard.html para ver los números actualizados.\n")

if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        import traceback
        print(f"\nERROR: {e}")
        traceback.print_exc()
    if os.name == "nt":
        input("\nPresioná ENTER para cerrar...")
