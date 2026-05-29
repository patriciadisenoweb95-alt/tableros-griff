# -*- coding: utf-8 -*-
"""
Imputacion de cheques a obras sociales con dos modos:

1. CRUCE POR OP (preferido): cuando el cheque aparece en una OP, se imputa
   usando los comprobantes de esa OP.
   - Cada FAC se busca en la planilla por (CUIT, Nro Factura). Si esta,
     se imputa a la OS de esa factura.
   - FACs sin match en planilla y NDs (notas de debito): se imputan a la
     OS principal del prestador (la OS con mayor facturacion en planilla).
   - Las retenciones (ej. Ganancias) se restan proporcionalmente.
   - Si la OP tiene varios cheques, cada cheque toma la fraccion correspondiente.

2. MODO ESTRICTO (fallback): para cheques sin OP, se usan shares por
   planilla por CUIT como antes. Lo que excede la planilla va a SIN_ASIGNACION.

3. CUIT FUERA de planilla y sin OP: 100% SIN_ASIGNACION.

Logica de A_VENCER (estado banco):
   El cheque esta pendiente si el banco NO lo cerro
   (estado != Pagado/Rechazado/Anulado/Repudiado), sin importar la fecha.
   Un cheque "Emitido" o "Aceptado" cuya fecha vencio sigue siendo pendiente.
"""

from datetime import date
import pandas as pd

from .config import OS_LIST, ESTADOS_CERRADOS
from .utils import fecha_str


# ------------------------------------------------------------------ helpers

def _norm_nro(s):
    """Normaliza un numero de cheque o factura: quita ceros adelante."""
    s = str(s or "").strip().lstrip("0")
    return s if s else "0"


def _construir_mapa_cheque_op(df_ops_cheques):
    """Devuelve {nro_cheque_normalizado: op_numero}."""
    if df_ops_cheques is None or df_ops_cheques.empty:
        return {}
    mapa = {}
    for _, r in df_ops_cheques.iterrows():
        nro = _norm_nro(r.get("NRO", ""))
        op = str(r.get("OP_NUMERO", "")).strip()
        if nro and op:
            mapa[nro] = op
    return mapa


def _saldos_por_cuit(df_facturas):
    """{cuit: {OS: saldo_a_pagar}} solo OS validas."""
    df_v = df_facturas[df_facturas["OBRA_SOCIAL"].isin(OS_LIST)].copy()
    grp = df_v.groupby(["CUIT", "OBRA_SOCIAL"])["A_PAGAR"].sum()
    saldo = {}
    for (cuit, os_), m in grp.items():
        if not cuit:
            continue
        saldo.setdefault(cuit, {os: 0.0 for os in OS_LIST})
        saldo[cuit][os_] = float(m)
    return saldo


def _os_principal_por_cuit(df_facturas):
    """{cuit: OS con mayor A_PAGAR}."""
    df_v = df_facturas[df_facturas["OBRA_SOCIAL"].isin(OS_LIST)].copy()
    if df_v.empty:
        return {}
    grp = df_v.groupby(["CUIT", "OBRA_SOCIAL"])["A_PAGAR"].sum().reset_index()
    out = {}
    for cuit in grp["CUIT"].unique():
        sub = grp[grp["CUIT"] == cuit].sort_values("A_PAGAR", ascending=False)
        if not sub.empty:
            out[cuit] = sub.iloc[0]["OBRA_SOCIAL"]
    return out


def _index_facturas_os(df_facturas):
    """Devuelve {(cuit, nro_factura_norm): OS}."""
    idx = {}
    for _, r in df_facturas.iterrows():
        cuit = str(r.get("CUIT", "")).strip()
        nro = str(r.get("Numero de Factura", "")).strip().replace(" ", "")
        os_ = str(r.get("OBRA_SOCIAL", "")).strip()
        if not cuit or not nro:
            continue
        if os_ in OS_LIST:
            idx[(cuit, nro)] = os_
    return idx


# ------------------------------------------------------------------ core

def _imputar_cheque_por_op(importe_cheque, comprobantes_op, retenciones_op,
                             monto_chq_op_total, idx_facturas_os,
                             os_principal_cuit, cuit):
    """Imputa UN cheque usando los comprobantes de su OP.

    Logica:
      - El cheque toma una fraccion (proporcion) de la OP completa,
        igual a importe_cheque / total_cheques_de_la_OP.
      - Para cada comprobante de la OP, esa fraccion se imputa a la OS
        que corresponda (FAC -> OS de planilla; FAC sin match o ND -> OS
        principal del CUIT).
      - Las retenciones se descuentan en la misma proporcion.
    """
    imp = {os: 0.0 for os in OS_LIST}
    sin_asignar = 0.0

    if monto_chq_op_total <= 0:
        return imp, importe_cheque

    proporcion = importe_cheque / monto_chq_op_total

    total_bruto = sum(float(c.get("ESTE_PAGO", 0) or 0)
                      for c in comprobantes_op)
    total_ret = sum(float(r.get("MONTO", 0) or 0)
                    for r in retenciones_op)

    if total_bruto <= 0:
        # OP sin comprobantes parseables: cheque cae a sin asignar
        return imp, importe_cheque

    # Para cada comprobante: imputar su porcion neto-de-retenciones a la OS
    for c in comprobantes_op:
        este_pago = float(c.get("ESTE_PAGO", 0) or 0)
        if este_pago <= 0:
            continue

        # Porcion bruta de este comprobante para este cheque
        bruto = este_pago * proporcion
        # Retencion proporcional al peso de este comprobante
        ret = (total_ret * (este_pago / total_bruto)) * proporcion
        neto = bruto - ret

        tipo = str(c.get("TIPO", "")).upper()
        nro_comp = str(c.get("NRO_COMP", "")).strip().replace(" ", "")

        os_destino = None
        if tipo in ("FAC", "FA", "FCE"):
            os_destino = idx_facturas_os.get((cuit, nro_comp))
        # NDs y FACs sin match en planilla: usar OS principal
        if not os_destino:
            os_destino = os_principal_cuit.get(cuit)

        if os_destino and os_destino in OS_LIST:
            imp[os_destino] += neto
        else:
            sin_asignar += neto

    return imp, sin_asignar


def imputar_cheques(df_cheques, df_facturas, df_ops_cheques=None,
                     df_ops_comprobantes=None, df_ops_retenciones=None):
    """Imputa cada cheque a OS. Devuelve DataFrame con columnas:
        N_CHEQUE, BENEFICIARIO, CUIT, FECHA_EMISION, FECHA_VENCIMIENTO,
        IMPORTE, ESTADO, MATCH_PLANILLA, OP_NUMERO, MODO_IMPUTACION,
        A_VENCER, MES_VENC, IMP_<OS>..., IMP_SIN_ASIGNACION.

    MODO_IMPUTACION puede ser:
      - "OP": cruzado con OP, usa comprobantes (mejor caso)
      - "ESTRICTO": cheque sin OP pero CUIT en planilla, usa shares
      - "FUERA": CUIT no esta en ninguna planilla, todo a sin asignar
    """
    mapa_chq_op = _construir_mapa_cheque_op(df_ops_cheques)
    saldos = _saldos_por_cuit(df_facturas)
    os_princ = _os_principal_por_cuit(df_facturas)
    idx_fact = _index_facturas_os(df_facturas)

    # Comprobantes y retenciones por OP
    comp_por_op = {}
    if df_ops_comprobantes is not None and not df_ops_comprobantes.empty:
        for op_nro, sub in df_ops_comprobantes.groupby("OP_NUMERO"):
            comp_por_op[op_nro] = sub.to_dict(orient="records")

    ret_por_op = {}
    if df_ops_retenciones is not None and not df_ops_retenciones.empty:
        for op_nro, sub in df_ops_retenciones.groupby("OP_NUMERO"):
            ret_por_op[op_nro] = sub.to_dict(orient="records")

    chq_total_por_op = {}
    if df_ops_cheques is not None and not df_ops_cheques.empty:
        for op_nro, sub in df_ops_cheques.groupby("OP_NUMERO"):
            chq_total_por_op[op_nro] = float(sub["IMPORTE"].sum())

    rows = []

    for _, c in df_cheques.iterrows():
        cuit = str(c.get("CUIT", "")).strip()
        nro_chq = _norm_nro(c.get("N_CHEQUE", ""))
        importe = float(c.get("IMPORTE", 0) or 0)
        fecha_pago = c.get("FECHA_PAGO")
        fecha_emision = c.get("FECHA_EMISION")
        estado = str(c.get("ESTADO", "")).strip()

        match = "SI" if cuit and cuit in saldos else "NO"
        op_numero = mapa_chq_op.get(nro_chq, "")

        imp = {os: 0.0 for os in OS_LIST}
        sin_asignar = 0.0
        modo = ""

        if op_numero and op_numero in comp_por_op and cuit:
            comprobantes = comp_por_op.get(op_numero, [])
            retenciones = ret_por_op.get(op_numero, [])
            monto_chq_op = chq_total_por_op.get(op_numero, 0.0)
            imp, sin_asignar = _imputar_cheque_por_op(
                importe, comprobantes, retenciones, monto_chq_op,
                idx_fact, os_princ, cuit)
            modo = "OP"
        elif match == "SI":
            saldos_cuit = saldos.get(cuit, {})
            saldo_total = sum(saldos_cuit.values())
            if saldo_total <= 0:
                sin_asignar = importe
            else:
                a_imputar = min(importe, saldo_total)
                shrs = {os: saldos_cuit[os] / saldo_total for os in OS_LIST}
                for os_ in OS_LIST:
                    imp[os_] = a_imputar * shrs[os_]
                sin_asignar = importe - a_imputar
            modo = "ESTRICTO"
        else:
            sin_asignar = importe
            modo = "FUERA"

        # Estado banco: pendiente si el banco no lo cerro,
        # sin importar la fecha.
        a_vencer = estado not in ESTADOS_CERRADOS

        rows.append({
            "N_CHEQUE": c.get("N_CHEQUE", ""),
            "BENEFICIARIO": c.get("BENEFICIARIO", ""),
            "CUIT": cuit,
            "FECHA_EMISION": fecha_str(fecha_emision),
            "FECHA_VENCIMIENTO": fecha_str(fecha_pago),
            "IMPORTE": importe,
            "ESTADO": estado,
            "MATCH_PLANILLA": match,
            "OP_NUMERO": op_numero,
            "MODO_IMPUTACION": modo,
            "A_VENCER": "SI" if a_vencer else "NO",
            "MES_VENC": fecha_pago.strftime("%Y-%m") if fecha_pago else "",
            **{f"IMP_{os}": imp[os] for os in OS_LIST},
            "IMP_SIN_ASIGNACION": sin_asignar,
        })

    return pd.DataFrame(rows)


# ------------------------------------------------------------------ pivots

def calcular_pivot_mes_os(df_cheques_imputados):
    df = df_cheques_imputados[df_cheques_imputados["A_VENCER"] == "SI"].copy()
    cols_imp = [f"IMP_{os}" for os in OS_LIST] + ["IMP_SIN_ASIGNACION"]
    if df.empty:
        return pd.DataFrame([{"MES_VENC": "TOTAL",
                               **{c: 0.0 for c in cols_imp}}])
    pivot = df.groupby("MES_VENC")[cols_imp].sum().reset_index()
    pivot = pivot.sort_values("MES_VENC")
    total = pivot[cols_imp].sum().to_dict()
    pivot = pd.concat([pivot, pd.DataFrame([{"MES_VENC": "TOTAL", **total}])],
                       ignore_index=True)
    return pivot


def resumen_por_prestador(df_cheques_imputados):
    df = df_cheques_imputados[df_cheques_imputados["A_VENCER"] == "SI"].copy()
    cols_imp = [f"IMP_{os}" for os in OS_LIST] + ["IMP_SIN_ASIGNACION"]
    if df.empty:
        return pd.DataFrame(columns=["BENEFICIARIO", "CUIT", "N_CHEQUES",
                                       "IMPORTE", *cols_imp])
    g = df.groupby(["BENEFICIARIO", "CUIT"], as_index=False).agg(
        N_CHEQUES=("N_CHEQUE", "count"),
        IMPORTE=("IMPORTE", "sum"),
        **{c: (c, "sum") for c in cols_imp}
    ).sort_values("IMPORTE", ascending=False)
    return g
