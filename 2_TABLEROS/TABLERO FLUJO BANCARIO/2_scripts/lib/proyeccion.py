# -*- coding: utf-8 -*-
"""
Motor de proyeccion del cash flow.
- Saldo apertura -> rolea desde la ultima carga aplicando eventos intermedios.
- Para cada dia (0..N), suma cheques + gastos + movimientos + vtos inversion.
- Detecta: deficit de fondeo, ventanas de excedente invertibles.
"""

from datetime import date, timedelta

from .config import CUENTAS, ACTIVE_STATUSES, BUFFER_SEGURIDAD, \
    TNA_FCI, TNA_CAUCION


def _today():
    return date.today()


def estimate_maturity_value(monto, tna, dias):
    """Estimacion lineal: monto * (1 + (tna/100) * dias/365)."""
    if not tna or tna <= 0 or dias <= 0:
        return monto
    return monto * (1 + (tna / 100.0) * (dias / 365.0))


def get_opening_on_date(target_date, df_saldos, eventos_func):
    """Saldo de apertura proyectado para target_date.
    1) Toma el saldo cargado mas reciente <= target_date para cada cuenta
    2) Rolea hacia adelante aplicando eventos intermedios."""
    if df_saldos.empty:
        return 0.0
    opening_sum = 0.0
    opening_base_date = None
    for cuenta in CUENTAS:
        cid = cuenta["id"]
        sub = df_saldos[(df_saldos["CUENTA"] == cid) &
                        (df_saldos["FECHA"] <= target_date)]
        if sub.empty:
            # tolerante: si no hay match exacto del id, agarra todos
            sub = df_saldos[df_saldos["FECHA"] <= target_date]
        if sub.empty:
            continue
        latest = sub.sort_values("FECHA").iloc[-1]
        opening_sum += float(latest["SALDO"])
        if opening_base_date is None or latest["FECHA"] > opening_base_date:
            opening_base_date = latest["FECHA"]
    if opening_base_date is None:
        return 0.0
    bal = opening_sum
    d = opening_base_date
    while d < target_date:
        bal += eventos_func(d)["net"]
        d += timedelta(days=1)
    return bal


def build_eventos_func(df_cheques, df_gastos, df_inversiones, df_movimientos):
    """Devuelve una funcion eventos(date) -> {net, events}."""
    # Pre-indexar por fecha
    cheques_idx = {}
    for _, r in df_cheques.iterrows():
        if r.get("ESTADO") not in ACTIVE_STATUSES:
            continue
        fp = r.get("FECHA_PAGO")
        if not fp:
            continue
        cheques_idx.setdefault(fp, []).append(r)

    gastos_idx = {}
    for _, r in df_gastos.iterrows():
        if r.get("ESTADO") != "proyectado":
            continue
        f = r.get("FECHA")
        if not f:
            continue
        gastos_idx.setdefault(f, []).append(r)

    inv_idx = {}
    for _, r in df_inversiones.iterrows():
        f = r.get("FECHA_VTO")
        if not f:
            continue
        inv_idx.setdefault(f, []).append(r)

    mov_idx = {}
    for _, r in df_movimientos.iterrows():
        f = r.get("FECHA")
        if not f:
            continue
        mov_idx.setdefault(f, []).append(r)

    def eventos(d):
        events = []
        net = 0.0
        for c in cheques_idx.get(d, []):
            sign = 1 if c.get("TIPO") == "recibido" else -1
            amt = float(c.get("IMPORTE", 0))
            estado = c.get("ESTADO", "")
            tipo_lbl = "Cheque recibido" if c.get("TIPO") == "recibido" else (
                "Cheque en deposito" if estado == "en_proceso_deposito"
                else "Cheque emitido")
            events.append({
                "kind": "cheque", "type": tipo_lbl,
                "concept": c.get("BENEFICIARIO") or c.get("N_CHEQUE", ""),
                "amount": amt, "sign": sign,
            })
            net += sign * amt
        for x in gastos_idx.get(d, []):
            amt = float(x.get("MONTO", 0))
            events.append({
                "kind": "gasto", "type": x.get("METODO", ""),
                "concept": x.get("CONCEPTO", ""),
                "amount": amt, "sign": -1,
            })
            net -= amt
        for m in mov_idx.get(d, []):
            amt = float(m.get("MONTO", 0))
            sign = 1 if m.get("TIPO") == "ingreso" else -1
            events.append({
                "kind": "movimiento",
                "type": "Ingreso" if sign > 0 else "Egreso",
                "concept": m.get("CONCEPTO", ""),
                "amount": amt, "sign": sign,
            })
            net += sign * amt
        for inv in inv_idx.get(d, []):
            monto = float(inv.get("MONTO", 0))
            tna = float(inv.get("TNA", 0) or 0)
            ini = inv.get("FECHA_INICIO")
            dias = (d - ini).days if ini else 0
            est = estimate_maturity_value(monto, tna, max(dias, 0))
            events.append({
                "kind": "inversion", "type": "Vto inversión",
                "concept": f"{inv.get('TIPO', '')} ({inv.get('PLATAFORMA', '')})",
                "amount": est, "sign": 1,
            })
            net += est
        return {"net": net, "events": events}

    return eventos


def project_daily(days, df_saldos, eventos_func):
    """Proyecta dia a dia desde hoy. Devuelve lista de puntos {date, balance,
    inflow, outflow, events}."""
    start = _today()
    bal = get_opening_on_date(start, df_saldos, eventos_func)
    points = []
    for i in range(days + 1):
        d = start + timedelta(days=i)
        ev = eventos_func(d)
        events = ev["events"]
        inflow = sum(e["amount"] for e in events if e["sign"] > 0)
        outflow = sum(e["amount"] for e in events if e["sign"] < 0)
        bal = bal + inflow - outflow
        points.append({
            "date": d.strftime("%Y-%m-%d"),
            "balance": bal,
            "inflow": inflow,
            "outflow": outflow,
            "events": events,
        })
    return points


def get_min_balance_total():
    return sum(c.get("min_balance", 0) for c in CUENTAS)


def detect_shortfalls(points):
    minb = get_min_balance_total()
    return [{"date": p["date"], "deficit": minb - p["balance"],
             "balance": p["balance"]}
            for p in points if p["balance"] < minb]


def detect_surplus_windows(points):
    minb = get_min_balance_total()
    threshold = minb + BUFFER_SEGURIDAD
    windows = []
    cur = None
    for i, p in enumerate(points):
        if i == 0:
            continue
        s = p["balance"] - threshold
        if s > 0:
            if cur is None:
                cur = {"start": p["date"], "end": p["date"],
                       "min_surplus": s, "days": 1}
            else:
                cur["end"] = p["date"]
                cur["min_surplus"] = min(cur["min_surplus"], s)
                cur["days"] += 1
        else:
            if cur is not None:
                windows.append(cur)
                cur = None
    if cur is not None:
        windows.append(cur)
    return windows


def suggest_investment(days, amount):
    if days <= 0:
        return None
    if days < 7:
        s = "Caución 1-7 días"
    elif days < 30:
        s = "Caución 7-30 días"
    elif days < 90:
        s = "Plazo fijo 30 días o caución renovable"
    elif days < 180:
        s = "LECAP corta o plazo fijo pre-cancelable"
    else:
        s = "LECAP larga o bono corto en pesos"
    diff = (TNA_CAUCION - TNA_FCI) / 100.0
    extra = amount * diff * (days / 365.0)
    return {"suggestion": s, "extra": extra}
