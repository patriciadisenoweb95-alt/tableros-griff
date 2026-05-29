# -*- coding: utf-8 -*-
"""
Genera tablero.html autocontenido con identidad visual Griff Salud.
"""

import json
import os
from datetime import date

from .config import OS_LIST


def generar_html(df_cheques, df_facturas, df_pivot, df_por_prest,
                 df_ops_cab=None, info_corrida=None, output_path=None):
    """Escribe tablero.html en output_path."""

    cheques_dict = df_cheques.to_dict(orient="records")
    facturas_dict = df_facturas.to_dict(orient="records")
    pivot_dict = df_pivot.to_dict(orient="records")
    por_prest_dict = df_por_prest.to_dict(orient="records")
    ops_cab_dict = df_ops_cab.to_dict(orient="records") if df_ops_cab is not None \
        and not df_ops_cab.empty else []

    df_av = df_cheques[df_cheques["A_VENCER"] == "SI"]
    df_sm = df_cheques[df_cheques["MATCH_PLANILLA"] == "NO"]

    # Modos de imputacion (solo si la columna existe)
    modos = {}
    if "MODO_IMPUTACION" in df_av.columns:
        modos = df_av["MODO_IMPUTACION"].value_counts().to_dict()

    kpis = {
        "total_cheques": int(len(df_cheques)),
        "cheques_a_vencer": int(len(df_av)),
        "monto_a_vencer": float(df_av["IMPORTE"].sum()),
        "monto_total_emitido": float(df_cheques["IMPORTE"].sum()),
        "cheques_sin_match": int(len(df_sm)),
        "monto_sm": float(df_sm["IMPORTE"].sum()),
        "facturas": int(len(df_facturas)),
        "prestadores": int(df_facturas["CUIT"].nunique()) if len(df_facturas) else 0,
        "monto_planilla": float(df_facturas["A_PAGAR"].sum()),
        "monto_sin_asignar": float(df_av["IMP_SIN_ASIGNACION"].sum()),
        "monto_imputado": float(sum(df_av[f"IMP_{os}"].sum() for os in OS_LIST)),
        "fecha_generacion": date.today().strftime("%d/%m/%Y"),
        "n_periodos": int(df_facturas["PERIODO"].nunique()) if len(df_facturas) else 0,
        "n_ops": len(ops_cab_dict),
        "modos_imputacion": modos,
    }

    totales_os = {os_: float(df_av[f"IMP_{os_}"].sum()) for os_ in OS_LIST}
    totales_os["SIN_ASIGNACION"] = float(df_av["IMP_SIN_ASIGNACION"].sum())

    periodos = sorted(df_facturas["PERIODO"].dropna().unique().tolist()) \
        if len(df_facturas) else []

    info_dict = info_corrida or {}

    data = {
        "kpis": kpis,
        "totales_os": totales_os,
        "pivot": pivot_dict,
        "cheques": cheques_dict,
        "facturas": facturas_dict,
        "por_prestador": por_prest_dict,
        "ops_cabecera": ops_cab_dict,
        "os_list": OS_LIST,
        "os_list_html": OS_LIST + ["SIN_ASIGNACION"],
        "periodos": periodos,
        "info": info_dict,
    }

    html = HTML_TEMPLATE.replace(
        "__DATA__",
        json.dumps(data, ensure_ascii=False, default=str)
    )

    output_path = output_path or "tablero.html"
    with open(output_path, "w", encoding="utf-8") as f:
        f.write(html)
    return output_path


# Logo Griff inline como SVG.
# Reproduce el lockup: "griff" azul + bolita cyan + "salud" cyan.
LOGO_SVG = r"""<svg viewBox="0 0 220 80" xmlns="http://www.w3.org/2000/svg" aria-label="Griff Salud">
  <defs>
    <style>
      .griff { font: 900 56px -apple-system, "Segoe UI", Roboto, sans-serif;
               fill: #001AE5; letter-spacing: -3px; }
      .salud { font: 800 22px -apple-system, "Segoe UI", Roboto, sans-serif;
               fill: #1DD9F0; letter-spacing: 0.5px; }
    </style>
  </defs>
  <text x="0" y="55" class="griff">griff</text>
  <circle cx="13" cy="68" r="6" fill="#1DD9F0"/>
  <text x="118" y="73" class="salud">salud</text>
</svg>"""


HTML_TEMPLATE = r"""<!DOCTYPE html>
<html lang="es">
<head>
<meta charset="UTF-8">
<title>Tablero Cuentas a Pagar | Griff Salud</title>
<style>
:root {
  --griff-blue: #1A2D9C;
  --griff-blue-dark: #15246E;
  --griff-cyan: #29ABE2;
  --griff-cyan-light: #E6FBFE;
  --griff-bg: #F5F7FB;
  --griff-card: #FFFFFF;
  --griff-text: #0B1220;
  --griff-text-soft: #5C6573;
  --griff-border: #E4E8F1;
  --warn: #D97706;
  --alert: #DC2626;
  --ok: #059669;
}
* { box-sizing: border-box; margin: 0; padding: 0; }
body { font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
       background: var(--griff-bg); color: var(--griff-text); line-height: 1.5; }

/* ---- Header con logo Griff ---- */
header.griff-header {
  background: white;
  border-bottom: 4px solid var(--griff-blue);
  padding: 18px 30px;
  display: flex;
  align-items: center;
  gap: 28px;
  box-shadow: 0 2px 12px rgba(0, 26, 229, 0.08);
}
header.griff-header .logo { width: 150px; flex-shrink: 0; }
header.griff-header .titulo h1 {
  font-size: 20px; font-weight: 700; color: var(--griff-text);
  margin-bottom: 2px;
}
header.griff-header .titulo .subtitle {
  font-size: 12px; color: var(--griff-text-soft);
}
header.griff-header .titulo .meta {
  font-size: 11px; color: var(--griff-text-soft); margin-top: 6px;
  font-style: italic;
}

.container { max-width: 1500px; margin: 0 auto; padding: 24px; }

/* ---- KPIs ---- */
.kpi-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(220px, 1fr));
            gap: 16px; margin-bottom: 24px; }
.kpi { background: var(--griff-card); border-radius: 10px; padding: 18px 20px;
       box-shadow: 0 1px 4px rgba(0, 0, 0, 0.05); border-left: 4px solid var(--griff-blue);
       transition: transform 0.15s ease; }
.kpi:hover { transform: translateY(-2px); }
.kpi.cyan { border-left-color: var(--griff-cyan); }
.kpi.warn { border-left-color: var(--warn); }
.kpi.ok { border-left-color: var(--ok); }
.kpi.alert { border-left-color: var(--alert); }
.kpi .label { font-size: 11px; color: var(--griff-text-soft); text-transform: uppercase;
              letter-spacing: 0.6px; font-weight: 600; }
.kpi .value { font-size: 22px; font-weight: 700; margin-top: 6px; color: var(--griff-text); }
.kpi .sub { font-size: 12px; color: var(--griff-text-soft); margin-top: 4px; }

/* ---- Tabs ---- */
.tabs { display: flex; gap: 2px; margin-bottom: 16px;
        border-bottom: 2px solid var(--griff-border); flex-wrap: wrap; }
.tab { padding: 10px 18px; background: transparent; border: none; cursor: pointer;
       font-size: 13px; font-weight: 500; color: var(--griff-text-soft);
       border-bottom: 3px solid transparent; margin-bottom: -2px;
       transition: all 0.15s; font-family: inherit; }
.tab:hover { color: var(--griff-blue); background: var(--griff-cyan-light); }
.tab.active { color: var(--griff-blue); border-bottom-color: var(--griff-blue);
              font-weight: 600; }
.tab.special { color: var(--warn); font-weight: 600; }
.tab.special.active { border-bottom-color: var(--warn); color: var(--warn); }

.panel { display: none; }
.panel.active { display: block; }

/* ---- Cards ---- */
.card { background: var(--griff-card); border-radius: 10px; padding: 20px;
        box-shadow: 0 1px 4px rgba(0, 0, 0, 0.05); margin-bottom: 18px;
        border: 1px solid var(--griff-border); }
.card h2 { font-size: 15px; font-weight: 700; margin-bottom: 14px;
           color: var(--griff-blue); text-transform: uppercase;
           letter-spacing: 0.4px; }
.card .desc { color: var(--griff-text-soft); font-size: 13px;
              margin-bottom: 12px; line-height: 1.55; }

/* ---- Filters ---- */
.filters { display: flex; gap: 10px; margin-bottom: 14px; flex-wrap: wrap;
           align-items: center; }
.filters input, .filters select {
  padding: 8px 12px; border: 1px solid var(--griff-border);
  border-radius: 6px; font-size: 13px; min-width: 150px;
  font-family: inherit; background: white; color: var(--griff-text);
  transition: border-color 0.15s, box-shadow 0.15s;
}
.filters input { min-width: 240px; }
.filters input:focus, .filters select:focus {
  outline: none; border-color: var(--griff-blue);
  box-shadow: 0 0 0 3px rgba(0, 26, 229, 0.1);
}
.filters .count { font-size: 12px; color: var(--griff-text-soft);
                  margin-left: auto; font-weight: 600; }

/* ---- Tablas ---- */
table { width: 100%; border-collapse: collapse; font-size: 12.5px; }
thead { background: var(--griff-cyan-light); position: sticky; top: 0; z-index: 1; }
th { padding: 10px 10px; text-align: left; font-weight: 700;
     color: var(--griff-blue-dark); border-bottom: 2px solid var(--griff-blue);
     white-space: nowrap; font-size: 11.5px; text-transform: uppercase;
     letter-spacing: 0.3px; }
th.num { text-align: right; }
td { padding: 8px 10px; border-bottom: 1px solid var(--griff-border); }
td.num { text-align: right; font-variant-numeric: tabular-nums; }
tr:hover { background: rgba(29, 217, 240, 0.06); }
tbody tr.totals { background: var(--griff-cyan-light); font-weight: 700; }
.scroll-x { overflow-x: auto; }
.scroll-y { max-height: 600px; overflow-y: auto; }

/* ---- Badges ---- */
.badge { display: inline-block; padding: 3px 9px; border-radius: 12px;
         font-size: 11px; font-weight: 600; }
.badge.ok { background: #D1FAE5; color: #065F46; }
.badge.warn { background: #FEF3C7; color: #92400E; }
.badge.alert { background: #FEE2E2; color: #991B1B; }
.badge.info { background: rgba(0, 26, 229, 0.1); color: var(--griff-blue-dark); }
.badge.cyan { background: var(--griff-cyan-light); color: var(--griff-blue-dark); }
.badge.gray { background: #F3F4F6; color: #4B5563; }

/* ---- Bar rows ---- */
.bar-row { display: grid; grid-template-columns: 220px 1fr 130px;
           gap: 10px; align-items: center; margin-bottom: 7px; }
.bar-row .name { font-size: 12px; font-weight: 500; color: var(--griff-text); }
.bar-row .bar-bg { height: 22px; background: var(--griff-cyan-light);
                   border-radius: 4px; overflow: hidden; }
.bar-row .bar { height: 100%;
                background: linear-gradient(90deg, var(--griff-blue), var(--griff-cyan)); }
.bar-row .val { text-align: right; font-size: 12px;
                font-variant-numeric: tabular-nums; font-weight: 600; }

/* ---- OS cards ---- */
.os-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(170px, 1fr));
           gap: 12px; }
.os-card { background: var(--griff-card); border-radius: 8px;
           padding: 14px 16px; border-top: 4px solid var(--griff-blue);
           border: 1px solid var(--griff-border); border-top: 4px solid var(--griff-blue); }
.os-card .name { font-size: 11px; color: var(--griff-text-soft); font-weight: 700;
                 letter-spacing: 0.5px; text-transform: uppercase; }
.os-card .val { font-size: 18px; font-weight: 700; margin-top: 4px;
                color: var(--griff-text); }
.os-card .pct { font-size: 11px; color: var(--griff-text-soft); margin-top: 2px; }

/* ---- Footer ---- */
footer { text-align: center; padding: 24px; color: var(--griff-text-soft);
         font-size: 11px; border-top: 1px solid var(--griff-border);
         margin-top: 30px; }
footer .logo-mini { width: 60px; opacity: 0.5; margin-bottom: 6px; }

@media (max-width: 768px) {
    .container { padding: 12px; }
    .kpi-grid { grid-template-columns: 1fr 1fr; }
    table { font-size: 11px; }
    th, td { padding: 6px 5px; }
    header.griff-header { flex-direction: column; align-items: flex-start; gap: 10px; }
}
</style>
</head>
<body>

<header class="griff-header">
    <div class="logo">__LOGO__</div>
    <div class="titulo">
        <h1>Tablero de Cuentas a Pagar</h1>
        <div class="subtitle">Cheques Galicia · Planillas de prestadores · Órdenes de Pago</div>
        <div class="meta" id="meta"></div>
    </div>
</header>

<div class="container">

    <div id="kpis" class="kpi-grid"></div>

    <div class="tabs">
        <button class="tab active" data-panel="resumen">Resumen</button>
        <button class="tab special" data-panel="sinasignar">Sin Asignar</button>
        <button class="tab" data-panel="vencer">Cheques pendientes</button>
        <button class="tab" data-panel="prestador">Por prestador</button>
        <button class="tab" data-panel="sinmatch">Fuera de planilla</button>
        <button class="tab" data-panel="todos">Todos los cheques</button>
        <button class="tab" data-panel="planilla">Planilla</button>
        <button class="tab" data-panel="ops">Órdenes de Pago</button>
    </div>

    <!-- Resumen -->
    <div class="panel active" id="panel-resumen">
        <div class="card" id="card-cuadre">
            <h2>Validación de cuadre</h2>
            <div id="cuadre-cheques"></div>
            <div id="cuadre-planilla" style="margin-top:14px"></div>
        </div>
        <div class="card">
            <h2>Distribución por obra social (cheques pendientes)</h2>
            <div id="os-grid" class="os-grid"></div>
        </div>
        <div class="card">
            <h2>Pivot mensual</h2>
            <div class="scroll-x">
                <table id="tabla-pivot"></table>
            </div>
        </div>
        <div class="card">
            <h2>Top 15 prestadores con más cheques pendientes</h2>
            <div id="top-prest"></div>
        </div>
    </div>

    <!-- Sin asignar -->
    <div class="panel" id="panel-sinasignar">
        <div class="card">
            <h2>Auditoría de Cheques Sin Asignar</h2>
            <p class="desc">
                Cheques (o tramos de cheques) pendientes que <strong>no se pudieron imputar</strong> a
                una obra social. Pueden ser por: el cheque no aparece en ninguna OP cargada,
                la OP tiene comprobantes que no están en planilla, o el CUIT no figura en
                ninguna planilla. Cargando más planillas u OPs el monto debería bajar.
            </p>
            <div class="filters">
                <input id="f-sa-q" placeholder="Buscar prestador, CUIT, cheque...">
                <select id="f-sa-mes"><option value="">Todos los meses</option></select>
                <select id="f-sa-modo">
                    <option value="">Todos los modos</option>
                    <option value="OP">Imputado por OP</option>
                    <option value="ESTRICTO">Estricto (sin OP)</option>
                    <option value="FUERA">CUIT fuera de planilla</option>
                </select>
                <span class="count" id="c-sa"></span>
            </div>
            <div class="scroll-x scroll-y">
                <table id="tabla-sa"></table>
            </div>
        </div>
    </div>

    <!-- Cheques pendientes -->
    <div class="panel" id="panel-vencer">
        <div class="card">
            <h2>Cheques pendientes</h2>
            <p class="desc">
                Cheques cuyo estado en el banco NO es Pagado / Rechazado / Anulado / Repudiado,
                independientemente de la fecha (un cheque "Emitido" o "Aceptado" cuya fecha
                ya pasó pero el banco no lo cerró sigue siendo pendiente).
            </p>
            <div class="filters">
                <input id="f-v-q" placeholder="Buscar prestador, CUIT, N° cheque...">
                <select id="f-v-mes"><option value="">Todos los meses</option></select>
                <select id="f-v-estado"><option value="">Todos los estados</option></select>
                <select id="f-v-modo">
                    <option value="">Todos los modos</option>
                    <option value="OP">Imputado por OP</option>
                    <option value="ESTRICTO">Estricto (sin OP)</option>
                    <option value="FUERA">CUIT fuera de planilla</option>
                </select>
                <span class="count" id="c-v"></span>
            </div>
            <div class="scroll-x scroll-y">
                <table id="tabla-v"></table>
            </div>
        </div>
    </div>

    <!-- Por prestador -->
    <div class="panel" id="panel-prestador">
        <div class="card">
            <h2>Cheques pendientes por prestador</h2>
            <div class="filters">
                <input id="f-p-q" placeholder="Buscar prestador o CUIT...">
                <span class="count" id="c-p"></span>
            </div>
            <div class="scroll-x scroll-y">
                <table id="tabla-p"></table>
            </div>
        </div>
    </div>

    <!-- Sin match -->
    <div class="panel" id="panel-sinmatch">
        <div class="card">
            <h2>Cheques de CUITs fuera de planilla</h2>
            <p class="desc">
                CUITs que no aparecen en ninguna planilla cargada (otros proveedores, no
                relacionados con obras sociales). Su monto va 100% a Sin Asignar.
            </p>
            <div class="filters">
                <input id="f-sm-q" placeholder="Buscar...">
                <span class="count" id="c-sm"></span>
            </div>
            <div class="scroll-x scroll-y">
                <table id="tabla-sm"></table>
            </div>
        </div>
    </div>

    <!-- Todos -->
    <div class="panel" id="panel-todos">
        <div class="card">
            <h2>Maestro de cheques</h2>
            <div class="filters">
                <input id="f-t-q" placeholder="Buscar...">
                <select id="f-t-vencer">
                    <option value="">Todos</option>
                    <option value="SI">Solo pendientes</option>
                    <option value="NO">Solo cerrados</option>
                </select>
                <span class="count" id="c-t"></span>
            </div>
            <div class="scroll-x scroll-y">
                <table id="tabla-t"></table>
            </div>
        </div>
    </div>

    <!-- Planilla -->
    <div class="panel" id="panel-planilla">
        <div class="card">
            <h2>Maestro de facturas (planilla)</h2>
            <div class="filters">
                <input id="f-f-q" placeholder="Buscar prestador, factura, OS...">
                <select id="f-f-periodo"><option value="">Todos los períodos</option></select>
                <select id="f-f-os"><option value="">Todas las OS</option></select>
                <span class="count" id="c-f"></span>
            </div>
            <div class="scroll-x scroll-y">
                <table id="tabla-f"></table>
            </div>
        </div>
    </div>

    <!-- OPs -->
    <div class="panel" id="panel-ops">
        <div class="card">
            <h2>Órdenes de Pago procesadas</h2>
            <p class="desc">
                Cabecera de cada OP a prestador médico (las OPs de gastos generales —
                reintegros, expensas, alquileres, etc. — se descartan automáticamente).
                <strong>DIFF_CUADRE</strong> debería ser 0; si no, revisar el PDF.
            </p>
            <div class="filters">
                <input id="f-o-q" placeholder="Buscar OP, prestador, CUIT...">
                <select id="f-o-cuadre">
                    <option value="">Todas las OPs</option>
                    <option value="no">Solo NO cuadran (DIFF ≠ 0)</option>
                    <option value="si">Solo cuadran (DIFF = 0)</option>
                </select>
                <select id="f-o-concepto"><option value="">Todos los conceptos</option></select>
                <span class="count" id="c-o"></span>
            </div>
            <div class="scroll-x scroll-y">
                <table id="tabla-o"></table>
            </div>
        </div>
    </div>

</div>

<footer>
    <div class="logo-mini">__LOGO__</div>
    Tablero generado automáticamente · Griff Salud
</footer>

<script>
const DATA = __DATA__;
const fmt = n => (Number(n)||0).toLocaleString("es-AR",
                                                {minimumFractionDigits: 0, maximumFractionDigits: 0});
const fmt2 = n => (Number(n)||0).toLocaleString("es-AR",
                                                 {minimumFractionDigits: 2, maximumFractionDigits: 2});

document.getElementById("meta").textContent =
    `Generado ${DATA.kpis.fecha_generacion} · ${DATA.kpis.facturas} facturas en ${DATA.kpis.n_periodos} períodos · ${DATA.kpis.total_cheques} cheques · ${DATA.kpis.n_ops} OPs`;

function renderKPIs() {
    const k = DATA.kpis;
    document.getElementById("kpis").innerHTML = `
        <div class="kpi"><div class="label">Cheques pendientes</div>
            <div class="value">${k.cheques_a_vencer}</div>
            <div class="sub">de ${k.total_cheques} totales · $ ${fmt(k.monto_a_vencer)}</div></div>
        <div class="kpi ok"><div class="label">Imputado a OS</div>
            <div class="value">$ ${fmt(k.monto_imputado)}</div>
            <div class="sub">deuda comprobada en planillas y OPs</div></div>
        <div class="kpi warn"><div class="label">Sin Asignar (pendientes)</div>
            <div class="value" style="color:var(--warn)">$ ${fmt(k.monto_sin_asignar)}</div>
            <div class="sub">${(k.monto_a_vencer ? (k.monto_sin_asignar/k.monto_a_vencer*100).toFixed(1) : 0)}% del total pendiente</div></div>
        <div class="kpi cyan"><div class="label">Planilla cargada</div>
            <div class="value">$ ${fmt(k.monto_planilla)}</div>
            <div class="sub">${k.facturas} fact · ${k.prestadores} prest · ${k.n_periodos} períodos</div></div>
    `;
}

function renderCuadre() {
    const k = DATA.kpis;
    const t = DATA.totales_os;
    const imputado = (t.OSPEVIC||0)+(t.OSPIF||0)+(t.OSPLYFC||0)+(t.OSSURRBAC||0)+(t.OSPM||0);
    const sinAsig = t.SIN_ASIGNACION || 0;
    const suma = imputado + sinAsig;
    const diff = k.monto_a_vencer - suma;
    const ok = Math.abs(diff) < 1;

    document.getElementById("cuadre-cheques").innerHTML = `
        <div style="display:grid; grid-template-columns: repeat(3, 1fr); gap:14px;">
            <div><div style="font-size:11px; color:var(--griff-text-soft); text-transform:uppercase; letter-spacing:0.4px; font-weight:600;">Cheques pendientes (Total)</div>
                <div style="font-size:20px; font-weight:700; margin-top:4px;">$ ${fmt(k.monto_a_vencer)}</div></div>
            <div><div style="font-size:11px; color:var(--griff-text-soft); text-transform:uppercase; letter-spacing:0.4px; font-weight:600;">Imputado a OS</div>
                <div style="font-size:20px; font-weight:700; margin-top:4px; color:var(--ok)">$ ${fmt(imputado)}</div></div>
            <div><div style="font-size:11px; color:var(--griff-text-soft); text-transform:uppercase; letter-spacing:0.4px; font-weight:600;">Sin Asignar</div>
                <div style="font-size:20px; font-weight:700; margin-top:4px; color:var(--warn)">$ ${fmt(sinAsig)}</div></div>
        </div>
        <div style="margin-top:12px; padding-top:10px; border-top:1px dashed var(--griff-border); font-size:13px;">
            Imputado + Sin Asignar = <strong>$ ${fmt(suma)}</strong>
            ${ok ? '<span class="badge ok" style="margin-left:10px">CUADRA</span>'
                 : `<span class="badge alert" style="margin-left:10px">DIFF: $ ${fmt2(diff)}</span>`}
        </div>
    `;

    // Planilla por periodo
    const facturas = DATA.facturas;
    const totales = {};
    facturas.forEach(f => {
        const p = f.PERIODO || "(sin periodo)";
        totales[p] = (totales[p]||0) + Number(f.A_PAGAR||0);
    });
    const totalGral = Object.values(totales).reduce((a,b)=>a+b, 0);
    const periodos = Object.keys(totales).sort();

    document.getElementById("cuadre-planilla").innerHTML = `
        <div style="font-size:11px; color:var(--griff-text-soft); text-transform:uppercase; letter-spacing:0.4px; font-weight:600; margin-bottom:8px;">Planilla cargada por período</div>
        <div style="display:grid; grid-template-columns: repeat(auto-fit, minmax(170px, 1fr)); gap:10px;">
            ${periodos.map(p => `
                <div style="background:var(--griff-cyan-light); padding:10px 14px; border-radius:6px; border:1px solid var(--griff-border);">
                    <div style="font-size:11px; font-weight:600; color:var(--griff-blue-dark); text-transform:uppercase; letter-spacing:0.3px;">${p}</div>
                    <div style="font-size:16px; font-weight:700; margin-top:3px;">$ ${fmt(totales[p])}</div>
                </div>
            `).join("")}
            <div style="background:var(--griff-blue); color:white; padding:10px 14px; border-radius:6px;">
                <div style="font-size:11px; font-weight:700; text-transform:uppercase; letter-spacing:0.3px;">TOTAL GENERAL</div>
                <div style="font-size:16px; font-weight:700; margin-top:3px;">$ ${fmt(totalGral)}</div>
            </div>
        </div>
    `;
}

function renderOSGrid() {
    const t = DATA.totales_os;
    const colores = { OSPEVIC: "#001AE5", OSPIF: "#7C3AED", OSPLYFC: "#059669",
                       OSSURRBAC: "#D97706", OSPM: "#DC2626", SIN_ASIGNACION: "#64748B" };
    const total = Object.values(t).reduce((a,b) => a+b, 0);
    document.getElementById("os-grid").innerHTML = DATA.os_list_html.map(os => {
        const v = t[os] || 0;
        const pct = total ? (v/total*100).toFixed(1) : 0;
        return `<div class="os-card" style="border-top-color: ${colores[os] || '#000'}">
            <div class="name">${os.replace('_', ' ')}</div>
            <div class="val">$ ${fmt(v)}</div>
            <div class="pct">${pct}% del total</div></div>`;
    }).join("");
}

function renderPivot() {
    const cols = DATA.os_list_html;
    const head = `<thead><tr><th>Mes</th>
        ${cols.map(o => `<th class="num">${o.replace('_', ' ')}</th>`).join("")}
        <th class="num">Total</th></tr></thead>`;
    const body = DATA.pivot.map(r => {
        const total = cols.reduce((s,o) => s + (Number(r["IMP_"+o])||0), 0);
        const cls = r.MES_VENC === "TOTAL" ? "totals" : "";
        return `<tr class="${cls}"><td><strong>${r.MES_VENC}</strong></td>
            ${cols.map(o => `<td class="num">$ ${fmt(r["IMP_"+o])}</td>`).join("")}
            <td class="num"><strong>$ ${fmt(total)}</strong></td></tr>`;
    }).join("");
    document.getElementById("tabla-pivot").innerHTML = head + `<tbody>${body}</tbody>`;
}

function renderTopPrest() {
    const top = DATA.por_prestador.slice(0, 15);
    if (!top.length) { document.getElementById("top-prest").innerHTML = "<em>Sin datos</em>"; return; }
    const max = Math.max(...top.map(p => Number(p.IMPORTE)));
    document.getElementById("top-prest").innerHTML = top.map(p => `
        <div class="bar-row">
            <div class="name" title="${p.BENEFICIARIO}">${(p.BENEFICIARIO||"").slice(0,45)}</div>
            <div class="bar-bg"><div class="bar" style="width: ${(Number(p.IMPORTE)/max*100)}%"></div></div>
            <div class="val">$ ${fmt(p.IMPORTE)}</div>
        </div>`).join("");
}

function renderSinAsignar() {
    const data = DATA.cheques.filter(c => c.A_VENCER === "SI"
                                            && Number(c.IMP_SIN_ASIGNACION) > 0);
    data.sort((a,b) => Number(b.IMP_SIN_ASIGNACION) - Number(a.IMP_SIN_ASIGNACION));

    const meses = [...new Set(data.map(c => c.MES_VENC))].sort();
    const fM = document.getElementById("f-sa-mes");
    fM.innerHTML = '<option value="">Todos los meses</option>' +
        meses.map(m => `<option>${m}</option>`).join("");

    function paint() {
        const q = document.getElementById("f-sa-q").value.toLowerCase();
        const m = fM.value;
        const md = document.getElementById("f-sa-modo").value;
        const f = data.filter(c => {
            if (m && c.MES_VENC !== m) return false;
            if (md && c.MODO_IMPUTACION !== md) return false;
            if (q && !(`${c.BENEFICIARIO} ${c.CUIT} ${c.N_CHEQUE}`
                .toLowerCase().includes(q))) return false;
            return true;
        });
        const tot = f.reduce((s,c) => s + Number(c.IMP_SIN_ASIGNACION), 0);
        document.getElementById("c-sa").textContent =
            `${f.length} cheques · $ ${fmt(tot)} sin asignar`;
        const head = `<thead><tr><th>Cheque</th><th>OP</th><th>Beneficiario</th><th>CUIT</th>
            <th>Mes Venc.</th><th>Modo</th><th class="num">Importe</th>
            <th class="num" style="color:var(--warn)">Sin Asignar</th></tr></thead>`;
        const body = f.map(c => {
            const modoBadge = c.MODO_IMPUTACION === "OP" ? "info"
                            : c.MODO_IMPUTACION === "ESTRICTO" ? "cyan" : "alert";
            return `<tr>
            <td><strong>${c.N_CHEQUE}</strong></td>
            <td>${c.OP_NUMERO || '<span class="badge gray">sin OP</span>'}</td>
            <td>${c.BENEFICIARIO}</td><td>${c.CUIT||""}</td>
            <td><span class="badge cyan">${c.MES_VENC}</span></td>
            <td><span class="badge ${modoBadge}">${c.MODO_IMPUTACION || "-"}</span></td>
            <td class="num">$ ${fmt(c.IMPORTE)}</td>
            <td class="num" style="color:var(--warn); font-weight:700">$ ${fmt(c.IMP_SIN_ASIGNACION)}</td>
        </tr>`;
        }).join("");
        document.getElementById("tabla-sa").innerHTML = head + `<tbody>${body}</tbody>`;
    }
    document.getElementById("f-sa-q").addEventListener("input", paint);
    fM.addEventListener("change", paint);
    document.getElementById("f-sa-modo").addEventListener("change", paint);
    paint();
}

function renderVencer() {
    const data = DATA.cheques.filter(c => c.A_VENCER === "SI");
    const meses = [...new Set(data.map(c => c.MES_VENC))].sort();
    const estados = [...new Set(data.map(c => c.ESTADO))].sort();
    const fM = document.getElementById("f-v-mes");
    const fE = document.getElementById("f-v-estado");
    fM.innerHTML = '<option value="">Todos los meses</option>' +
        meses.map(m => `<option>${m}</option>`).join("");
    fE.innerHTML = '<option value="">Todos los estados</option>' +
        estados.map(e => `<option>${e}</option>`).join("");

    const fMod = document.getElementById("f-v-modo");
    function paint() {
        const q = document.getElementById("f-v-q").value.toLowerCase();
        const m = fM.value; const e = fE.value; const md = fMod.value;
        const f = data.filter(c => {
            if (m && c.MES_VENC !== m) return false;
            if (e && c.ESTADO !== e) return false;
            if (md && c.MODO_IMPUTACION !== md) return false;
            if (q && !(`${c.BENEFICIARIO} ${c.CUIT} ${c.N_CHEQUE}`
                .toLowerCase().includes(q))) return false;
            return true;
        });
        document.getElementById("c-v").textContent =
            `${f.length} cheques · $ ${fmt(f.reduce((s,c)=>s+Number(c.IMPORTE),0))}`;
        const head = `<thead><tr><th>Cheque</th><th>OP</th><th>Beneficiario</th>
            <th>Vencimiento</th><th>Estado</th><th>Match</th>
            <th class="num">Importe</th>
            ${DATA.os_list.map(o => `<th class="num">${o}</th>`).join("")}
            <th class="num" style="color:var(--warn)">Sin Asignar</th></tr></thead>`;
        const body = f.map(c => `<tr>
            <td><strong>${c.N_CHEQUE}</strong></td>
            <td>${c.OP_NUMERO || ""}</td>
            <td>${c.BENEFICIARIO}</td>
            <td>${c.FECHA_VENCIMIENTO}</td>
            <td><span class="badge info">${c.ESTADO}</span></td>
            <td>${c.MATCH_PLANILLA === "SI"
                ? '<span class="badge ok">SI</span>'
                : '<span class="badge alert">NO</span>'}</td>
            <td class="num"><strong>$ ${fmt(c.IMPORTE)}</strong></td>
            ${DATA.os_list.map(o => `<td class="num">$ ${fmt(c["IMP_"+o])}</td>`).join("")}
            <td class="num" style="color:var(--warn)">$ ${fmt(c.IMP_SIN_ASIGNACION)}</td>
        </tr>`).join("");
        document.getElementById("tabla-v").innerHTML = head + `<tbody>${body}</tbody>`;
    }
    document.getElementById("f-v-q").addEventListener("input", paint);
    fM.addEventListener("change", paint); fE.addEventListener("change", paint);
    fMod.addEventListener("change", paint);
    paint();
}

function renderPrest() {
    const data = DATA.por_prestador;
    function paint() {
        const q = document.getElementById("f-p-q").value.toLowerCase();
        const f = data.filter(p => !q || `${p.BENEFICIARIO} ${p.CUIT}`
            .toLowerCase().includes(q));
        document.getElementById("c-p").textContent =
            `${f.length} prestadores · $ ${fmt(f.reduce((s,p)=>s+Number(p.IMPORTE),0))}`;
        const head = `<thead><tr><th>Prestador</th><th>CUIT</th>
            <th class="num">Cheques</th>
            ${DATA.os_list.map(o => `<th class="num">${o}</th>`).join("")}
            <th class="num" style="color:var(--warn)">Sin Asignar</th>
            <th class="num">Total</th></tr></thead>`;
        const body = f.map(p => `<tr>
            <td>${p.BENEFICIARIO}</td><td>${p.CUIT||""}</td>
            <td class="num">${p.N_CHEQUES}</td>
            ${DATA.os_list.map(o => `<td class="num">$ ${fmt(p["IMP_"+o])}</td>`).join("")}
            <td class="num" style="color:var(--warn)">$ ${fmt(p.IMP_SIN_ASIGNACION)}</td>
            <td class="num"><strong>$ ${fmt(p.IMPORTE)}</strong></td>
        </tr>`).join("");
        document.getElementById("tabla-p").innerHTML = head + `<tbody>${body}</tbody>`;
    }
    document.getElementById("f-p-q").addEventListener("input", paint);
    paint();
}

function renderSinMatch() {
    const data = DATA.cheques.filter(c => c.MATCH_PLANILLA === "NO");
    function paint() {
        const q = document.getElementById("f-sm-q").value.toLowerCase();
        const f = data.filter(c => !q ||
            `${c.BENEFICIARIO} ${c.CUIT} ${c.N_CHEQUE}`.toLowerCase().includes(q));
        const tot = f.reduce((s,c) => s + Number(c.IMPORTE), 0);
        document.getElementById("c-sm").textContent =
            `${f.length} cheques · $ ${fmt(tot)}`;
        const head = `<thead><tr><th>Cheque</th><th>Beneficiario</th><th>CUIT</th>
            <th>Vencimiento</th><th>Estado</th><th>Pendiente</th>
            <th class="num">Importe</th></tr></thead>`;
        const body = f.map(c => `<tr>
            <td><strong>${c.N_CHEQUE}</strong></td>
            <td>${c.BENEFICIARIO}</td><td>${c.CUIT||""}</td>
            <td>${c.FECHA_VENCIMIENTO}</td>
            <td><span class="badge info">${c.ESTADO}</span></td>
            <td>${c.A_VENCER === "SI" ? '<span class="badge warn">SI</span>'
                : '<span class="badge gray">NO</span>'}</td>
            <td class="num" style="color:var(--warn)">$ ${fmt(c.IMPORTE)}</td>
        </tr>`).join("");
        document.getElementById("tabla-sm").innerHTML = head + `<tbody>${body}</tbody>`;
    }
    document.getElementById("f-sm-q").addEventListener("input", paint);
    paint();
}

function renderTodos() {
    const data = DATA.cheques;
    function paint() {
        const q = document.getElementById("f-t-q").value.toLowerCase();
        const v = document.getElementById("f-t-vencer").value;
        const f = data.filter(c => {
            if (v && c.A_VENCER !== v) return false;
            if (q && !(`${c.BENEFICIARIO} ${c.CUIT} ${c.N_CHEQUE} ${c.ESTADO}`
                .toLowerCase().includes(q))) return false;
            return true;
        });
        document.getElementById("c-t").textContent =
            `${f.length} cheques · $ ${fmt(f.reduce((s,c)=>s+Number(c.IMPORTE),0))}`;
        const head = `<thead><tr><th>Cheque</th><th>Beneficiario</th>
            <th>Emisión</th><th>Vencimiento</th><th>Estado</th><th>Pendiente</th>
            <th>Match</th><th class="num">Importe</th></tr></thead>`;
        const body = f.map(c => `<tr>
            <td><strong>${c.N_CHEQUE}</strong></td><td>${c.BENEFICIARIO}</td>
            <td>${c.FECHA_EMISION}</td><td>${c.FECHA_VENCIMIENTO}</td>
            <td>${c.ESTADO}</td>
            <td>${c.A_VENCER === "SI" ? '<span class="badge warn">SI</span>'
                : '<span class="badge gray">NO</span>'}</td>
            <td>${c.MATCH_PLANILLA === "SI" ? '<span class="badge ok">SI</span>'
                : '<span class="badge alert">NO</span>'}</td>
            <td class="num">$ ${fmt(c.IMPORTE)}</td>
        </tr>`).join("");
        document.getElementById("tabla-t").innerHTML = head + `<tbody>${body}</tbody>`;
    }
    document.getElementById("f-t-q").addEventListener("input", paint);
    document.getElementById("f-t-vencer").addEventListener("change", paint);
    paint();
}

function renderFact() {
    const data = DATA.facturas;
    const fP = document.getElementById("f-f-periodo");
    const fOs = document.getElementById("f-f-os");
    fP.innerHTML = '<option value="">Todos los períodos</option>' +
        DATA.periodos.map(p => `<option>${p}</option>`).join("");
    const oss = [...new Set(data.map(f => f.OBRA_SOCIAL).filter(Boolean))].sort();
    fOs.innerHTML = '<option value="">Todas las OS</option>' +
        oss.map(o => `<option>${o}</option>`).join("");
    function paint() {
        const q = document.getElementById("f-f-q").value.toLowerCase();
        const p = fP.value;
        const o = fOs.value;
        const f = data.filter(r => {
            if (p && r.PERIODO !== p) return false;
            if (o && r.OBRA_SOCIAL !== o) return false;
            const blob = `${r.PRESTADOR} ${r.CUIT} ${r["Numero de Factura"]} ${r.OBRA_SOCIAL}`;
            if (q && !blob.toLowerCase().includes(q)) return false;
            return true;
        });
        const tot = f.reduce((s,r) => s + Number(r.A_PAGAR || 0), 0);
        document.getElementById("c-f").textContent =
            `${f.length} facturas · $ ${fmt(tot)}`;
        const head = `<thead><tr><th>Período</th><th>Prestador</th><th>CUIT</th>
            <th>Factura</th><th>Fecha</th><th>OS</th><th class="num">A pagar</th></tr></thead>`;
        const body = f.map(r => `<tr>
            <td><span class="badge cyan">${r.PERIODO||""}</span></td>
            <td>${r.PRESTADOR}</td><td>${r.CUIT||""}</td>
            <td>${r["Numero de Factura"]||""}</td>
            <td>${r.FECHA_FACT||""}</td>
            <td><span class="badge info">${r.OBRA_SOCIAL || r.OBRA_SOCIAL_RAW || "?"}</span></td>
            <td class="num">$ ${fmt2(Number(r.A_PAGAR||0))}</td>
        </tr>`).join("");
        document.getElementById("tabla-f").innerHTML = head + `<tbody>${body}</tbody>`;
    }
    document.getElementById("f-f-q").addEventListener("input", paint);
    fP.addEventListener("change", paint);
    fOs.addEventListener("change", paint);
    paint();
}

function renderOps() {
    const data = DATA.ops_cabecera;
    if (!data.length) {
        document.getElementById("tabla-o").innerHTML =
            "<tbody><tr><td><em>No hay PDFs de OPs procesados.</em></td></tr></tbody>";
        document.getElementById("c-o").textContent = "0 OPs";
        return;
    }
    // Cargar lista de conceptos unicos
    const conceptos = [...new Set(data.map(o => (o.CONCEPTO||"").trim()).filter(Boolean))].sort();
    const fC = document.getElementById("f-o-concepto");
    fC.innerHTML = '<option value="">Todos los conceptos</option>' +
        conceptos.map(c => `<option value="${c}">${c.length>50?c.slice(0,50)+"...":c}</option>`).join("");
    const fCuadre = document.getElementById("f-o-cuadre");

    function paint() {
        const q = document.getElementById("f-o-q").value.toLowerCase();
        const cu = fCuadre.value;
        const co = fC.value;
        const f = data.filter(o => {
            const diff = Math.abs(Number(o.DIFF_CUADRE || 0));
            if (cu === "no" && diff <= 1) return false;
            if (cu === "si" && diff > 1) return false;
            if (co && (o.CONCEPTO||"").trim() !== co) return false;
            if (q && !(`${o.OP_NUMERO} ${o.PRESTADOR} ${o.CUIT}`.toLowerCase().includes(q))) return false;
            return true;
        });
        document.getElementById("c-o").textContent =
            `${f.length} OPs · $ ${fmt(f.reduce((s,o)=>s+Number(o.TOTAL_OP||0),0))}`;
        const head = `<thead><tr><th>OP</th><th>Fecha</th><th>Prestador</th>
            <th>CUIT</th><th>Concepto</th>
            <th class="num">Fact / NDs</th>
            <th class="num">Retenciones</th><th class="num">Total OP</th>
            <th class="num">Cheques</th><th class="num">Diff</th></tr></thead>`;
        const body = f.map(o => {
            const diff = Math.abs(Number(o.DIFF_CUADRE || 0));
            const diffClass = diff > 1 ? "alert" : "ok";
            return `<tr>
                <td><strong>${o.OP_NUMERO}</strong></td>
                <td>${o.OP_FECHA}</td>
                <td>${o.PRESTADOR}</td><td>${o.CUIT}</td>
                <td style="font-size:11px">${o.CONCEPTO}</td>
                <td class="num">${o.N_FACTURAS}/${o.N_NDS}<br>
                    <span style="color:var(--griff-text-soft); font-size:10px">$ ${fmt(o.MONTO_FACT)} / $ ${fmt(o.MONTO_ND)}</span></td>
                <td class="num">$ ${fmt(o.MONTO_RETENCIONES)}</td>
                <td class="num"><strong>$ ${fmt(o.TOTAL_OP)}</strong></td>
                <td class="num">${o.N_CHEQUES} ($ ${fmt(o.MONTO_CHEQUES)})</td>
                <td class="num"><span class="badge ${diffClass}">$ ${fmt2(o.DIFF_CUADRE)}</span></td>
            </tr>`;
        }).join("");
        document.getElementById("tabla-o").innerHTML = head + `<tbody>${body}</tbody>`;
    }
    document.getElementById("f-o-q").addEventListener("input", paint);
    fCuadre.addEventListener("change", paint);
    fC.addEventListener("change", paint);
    paint();
}

document.querySelectorAll(".tab").forEach(t => {
    t.addEventListener("click", () => {
        document.querySelectorAll(".tab").forEach(x => x.classList.remove("active"));
        document.querySelectorAll(".panel").forEach(x => x.classList.remove("active"));
        t.classList.add("active");
        document.getElementById("panel-" + t.dataset.panel).classList.add("active");
    });
});

renderKPIs(); renderCuadre(); renderOSGrid(); renderPivot(); renderTopPrest();
renderSinAsignar(); renderVencer(); renderPrest(); renderSinMatch();
renderTodos(); renderFact(); renderOps();
</script>

</body>
</html>
"""


# Inyectar logo despues de definir HTML_TEMPLATE
HTML_TEMPLATE = HTML_TEMPLATE.replace("__LOGO__", LOGO_SVG)
