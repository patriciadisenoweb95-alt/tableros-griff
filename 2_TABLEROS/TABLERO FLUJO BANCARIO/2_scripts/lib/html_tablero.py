# -*- coding: utf-8 -*-
"""
Genera tablero.html autocontenido con identidad visual Griff Salud.
Embebe el state como JSON dentro del HTML para que el dashboard sea
completamente offline.
"""

import json
from datetime import date, datetime

from .config import CUENTAS, BUFFER_SEGURIDAD, TNA_FCI, TNA_CAUCION, \
    STATUS_LABELS, BRAND


def _serialize(obj):
    """JSON encoder que maneja date/datetime/NaN."""
    if isinstance(obj, (date, datetime)):
        return obj.strftime("%Y-%m-%d")
    if hasattr(obj, "isoformat"):
        return obj.isoformat()
    try:
        import math
        if isinstance(obj, float) and (math.isnan(obj) or math.isinf(obj)):
            return None
    except Exception:
        pass
    return str(obj)


def _df_to_records(df, date_cols=None):
    if df is None or df.empty:
        return []
    df2 = df.copy()
    if date_cols:
        for c in date_cols:
            if c in df2.columns:
                df2[c] = df2[c].apply(
                    lambda x: x.strftime("%Y-%m-%d") if x else None)
    return df2.where(df2.notna(), None).to_dict(orient="records")


def generar_html(df_cheques, df_saldos, df_gastos, df_inversiones,
                  df_movimientos, points30, points90,
                  shortfalls, surplus_windows, info_corrida=None,
                  output_path=None):
    """Escribe tablero.html en output_path."""

    state = {
        "cuentas": CUENTAS,
        "params": {
            "buffer": BUFFER_SEGURIDAD,
            "fciRate": TNA_FCI,
            "caucionRate": TNA_CAUCION,
        },
        "cheques": _df_to_records(df_cheques,
                                    date_cols=["FECHA_PAGO", "FECHA_EMISION"]),
        "saldos": _df_to_records(df_saldos, date_cols=["FECHA"]),
        "gastos": _df_to_records(df_gastos, date_cols=["FECHA"]),
        "inversiones": _df_to_records(df_inversiones,
                                        date_cols=["FECHA_INICIO", "FECHA_VTO"]),
        "movimientos": _df_to_records(df_movimientos, date_cols=["FECHA"]),
        "points30": points30,
        "points90": points90,
        "shortfalls": shortfalls,
        "surplus_windows": surplus_windows,
        "info_corrida": info_corrida or {},
        "today": date.today().strftime("%Y-%m-%d"),
        "status_labels": STATUS_LABELS,
    }

    state_json = json.dumps(state, default=_serialize, ensure_ascii=False)
    html = HTML_TEMPLATE.replace("__STATE_JSON__", state_json)

    if output_path:
        with open(output_path, "w", encoding="utf-8") as f:
            f.write(html)
    return output_path


HTML_TEMPLATE = r"""<!DOCTYPE html>
<html lang="es">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Griff Salud · Flujo Bancario</title>
<script src="https://cdn.jsdelivr.net/npm/chart.js@4.5.0/dist/chart.umd.js"></script>
<style>
:root {
  --bg: #f5f7fb; --surface: #ffffff; --border: #e0e4ed;
  --text: #11163d; --muted: #5b6385;
  --primary: #1A2D9C; --primary-strong: #15246E; --primary-soft: #e6e7fa;
  --accent: #29ABE2; --accent-strong: #1E8BBA; --accent-soft: #def5fc;
  --success: #0a8a5e; --success-soft: #e6f6ef;
  --warn: #b25500; --warn-soft: #fff2e0;
  --danger: #c0392b; --danger-soft: #fdecea;
  --chip: #eef0f7;
  --shadow: 0 1px 2px rgba(17,22,61,.05), 0 1px 3px rgba(17,22,61,.08);
}
* { box-sizing: border-box; }
body { margin: 0; font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif; background: var(--bg); color: var(--text); font-size: 14px; line-height: 1.5; }
header { background: var(--surface); border-bottom: 1px solid var(--border); padding: 14px 24px 0; position: sticky; top: 0; z-index: 10; }
.title-row { display: flex; align-items: center; justify-content: space-between; margin-bottom: 12px; gap: 12px; flex-wrap: wrap; }
.brand { display: flex; align-items: center; gap: 12px; }
.brand-mark { display: inline-flex; align-items: center; justify-content: center; width: 36px; height: 36px; border-radius: 8px; background: linear-gradient(135deg, var(--primary), var(--accent)); color: white; font-weight: 800; font-size: 18px; }
.brand-text { line-height: 1.1; }
.brand-name { font-weight: 700; font-size: 15px; color: var(--primary); }
.brand-name .accent { color: var(--accent-strong); }
.brand-sub { font-size: 11px; color: var(--muted); text-transform: uppercase; letter-spacing: .08em; font-weight: 500; }
.title-row .meta { color: var(--muted); font-size: 12px; }
nav.tabs { display: flex; gap: 4px; flex-wrap: wrap; }
.tab { padding: 8px 14px; border: none; background: transparent; cursor: pointer; font-size: 13px; color: var(--muted); border-bottom: 2px solid transparent; margin-bottom: -1px; font-weight: 500; }
.tab:hover { color: var(--text); }
.tab.active { color: var(--primary); border-bottom-color: var(--primary); }
main { padding: 20px 24px 60px; max-width: 1400px; margin: 0 auto; }
section { display: none; }
section.active { display: block; }
.cards { display: grid; grid-template-columns: repeat(auto-fit, minmax(220px, 1fr)); gap: 12px; margin-bottom: 20px; }
.card { background: var(--surface); border: 1px solid var(--border); border-radius: 10px; padding: 14px 16px; box-shadow: var(--shadow); position: relative; overflow: hidden; }
.card::before { content: ""; position: absolute; left: 0; top: 0; bottom: 0; width: 3px; background: var(--primary); }
.card.accent::before { background: var(--accent); }
.card.warn::before { background: var(--warn); }
.card.danger::before { background: var(--danger); }
.card.success::before { background: var(--success); }
.card .label { color: var(--muted); font-size: 11px; text-transform: uppercase; letter-spacing: .06em; margin-bottom: 4px; font-weight: 600; }
.card .value { font-size: 22px; font-weight: 700; color: var(--text); }
.card .sub { color: var(--muted); font-size: 12px; margin-top: 2px; }
.panel { background: var(--surface); border: 1px solid var(--border); border-radius: 10px; padding: 18px 20px; margin-bottom: 16px; box-shadow: var(--shadow); }
.panel h2 { font-size: 14px; margin: 0 0 12px; font-weight: 600; }
.panel h2 .hint { font-weight: 400; color: var(--muted); font-size: 12px; margin-left: 8px; }
.panel-collapsible h2 { display: flex; align-items: center; gap: 8px; cursor: pointer; user-select: none; margin-bottom: 0; }
.panel-collapsible.expanded h2 { margin-bottom: 12px; }
.panel-collapsible .toggle { margin-left: auto; color: var(--muted); font-size: 16px; transition: transform .15s ease; }
.panel-collapsible.expanded .toggle { transform: rotate(90deg); }
.panel-collapsible .panel-body { display: none; }
.panel-collapsible.expanded .panel-body { display: block; }
.alert-summary { display: flex; gap: 8px; align-items: center; font-size: 12px; }
.badge { display: inline-flex; padding: 2px 8px; border-radius: 999px; font-size: 11px; font-weight: 600; }
.badge.danger { background: var(--danger-soft); color: var(--danger); }
.badge.warn { background: var(--warn-soft); color: var(--warn); }
.badge.success { background: var(--success-soft); color: var(--success); }
.badge.info { background: var(--accent-soft); color: var(--accent-strong); }
.toolbar { display: flex; gap: 8px; align-items: center; margin-bottom: 12px; flex-wrap: wrap; }
.toolbar .spacer { flex: 1; }
input, select { font: inherit; padding: 6px 10px; border: 1px solid var(--border); border-radius: 6px; background: var(--surface); color: var(--text); font-size: 12px; }
input:focus, select:focus { outline: 2px solid var(--primary-soft); border-color: var(--primary); }
button { font: inherit; padding: 6px 12px; border-radius: 6px; border: 1px solid var(--border); background: var(--surface); color: var(--text); cursor: pointer; font-weight: 500; font-size: 12px; }
button:hover { background: var(--chip); }
table { width: 100%; border-collapse: collapse; font-size: 13px; }
th, td { text-align: left; padding: 8px 10px; border-bottom: 1px solid var(--border); vertical-align: middle; }
th { color: var(--muted); font-weight: 600; font-size: 11px; text-transform: uppercase; letter-spacing: .04em; background: var(--bg); }
td.num, th.num { text-align: right; font-variant-numeric: tabular-nums; }
.chip { display: inline-block; padding: 2px 8px; border-radius: 999px; font-size: 11px; font-weight: 500; background: var(--chip); }
.chip.success { background: var(--success-soft); color: var(--success); }
.chip.warn { background: var(--warn-soft); color: var(--warn); }
.chip.danger { background: var(--danger-soft); color: var(--danger); }
.chip.primary { background: var(--primary-soft); color: var(--primary); }
.chip.accent { background: var(--accent-soft); color: var(--accent-strong); }
.alert { display: flex; gap: 10px; padding: 12px 14px; border-radius: 8px; margin-bottom: 8px; border: 1px solid; font-size: 13px; }
.alert.danger { background: var(--danger-soft); border-color: #f5b7b1; color: #7a1d12; }
.alert.warn { background: var(--warn-soft); border-color: #ffd6a8; color: #6e3500; }
.alert.success { background: var(--success-soft); border-color: #b7e0ce; color: #064d36; }
.alert.info { background: var(--accent-soft); border-color: #b7e6f4; color: #0a4d63; }
.alert .icon { font-weight: 700; }
.empty { color: var(--muted); font-style: italic; padding: 16px; text-align: center; }
.muted { color: var(--muted); }
.chart-wrap { position: relative; height: 320px; }
.scroll-x { overflow-x: auto; }
.totalbar { display: flex; gap: 12px; padding: 10px 14px; border-radius: 8px; background: var(--primary-soft); border: 1px solid #c8d4ff; margin-bottom: 12px; flex-wrap: wrap; align-items: center; font-size: 13px; }
.totalbar .item .lbl { color: var(--muted); font-size: 11px; font-weight: 500; text-transform: uppercase; letter-spacing: .04em; }
.totalbar .item .val { font-weight: 700; font-variant-numeric: tabular-nums; color: var(--primary); }
.totalbar .item .val.danger { color: var(--danger); }
.totalbar .item .val.success { color: var(--success); }
.totalbar .item .val.accent { color: var(--accent-strong); }
.totalbar .sep { width: 1px; align-self: stretch; background: #c8d4ff; }
.mini-cards { display: grid; grid-template-columns: repeat(auto-fit, minmax(150px, 1fr)); gap: 8px; margin-bottom: 12px; }
.mini-card { background: var(--bg); border: 1px solid var(--border); border-radius: 8px; padding: 8px 10px; }
.mini-card .label { color: var(--muted); font-size: 11px; }
.mini-card .value { font-weight: 700; font-size: 14px; font-variant-numeric: tabular-nums; color: var(--primary); }
.mini-card.danger .value { color: var(--danger); }
.legend { display: flex; gap: 16px; flex-wrap: wrap; font-size: 12px; color: var(--muted); margin-bottom: 8px; }
.dot { display: inline-block; width: 8px; height: 8px; border-radius: 50%; margin-right: 4px; vertical-align: middle; }
.form-grid { display: grid; grid-template-columns: repeat(auto-fit,minmax(140px,1fr)); gap: 10px; align-items: end; }
.form-grid label { display: flex; flex-direction: column; font-size: 12px; color: var(--muted); gap: 4px; }
.form-grid input, .form-grid select { font-size: 13px; padding: 8px 10px; }
.primary-btn { background: var(--primary); border-color: var(--primary); color: white; font-weight: 500; padding: 8px 14px; }
.primary-btn:hover { background: var(--primary-strong); }
.accent-btn { background: var(--accent); border-color: var(--accent); color: white; font-weight: 500; padding: 8px 14px; }
@media (max-width: 700px) { main { padding: 16px; } header { padding: 12px 16px 0; } }
</style>
</head>
<body>
<header>
  <div class="title-row">
    <div class="brand">
      <div class="brand-mark">g</div>
      <div class="brand-text">
        <div class="brand-name">griff <span class="accent">salud</span></div>
        <div class="brand-sub">Tesorería · Flujo Bancario</div>
      </div>
    </div>
    <div class="meta" id="last-update"></div>
  </div>
  <nav class="tabs">
    <button class="tab active" data-tab="dashboard">Dashboard</button>
    <button class="tab" data-tab="cheques">Cheques</button>
    <button class="tab" data-tab="gastos">Gastos</button>
    <button class="tab" data-tab="inversiones">Inversiones</button>
    <button class="tab" data-tab="movimientos">Movimientos</button>
    <button class="tab" data-tab="saldos">Saldos</button>
  </nav>
</header>
<main>

<section id="dashboard" class="active">
  <div class="cards">
    <div class="card"><div class="label">Saldo bancario apertura</div><div class="value" id="kpi-balance">—</div><div class="sub" id="kpi-balance-sub">—</div></div>
    <div class="card accent"><div class="label">Inversiones activas</div><div class="value" id="kpi-invest">—</div><div class="sub" id="kpi-invest-sub">—</div></div>
    <div class="card"><div class="label">Cheques pendientes (neto)</div><div class="value" id="kpi-checks">—</div><div class="sub" id="kpi-checks-sub">—</div></div>
    <div class="card warn"><div class="label">Gastos próx. 30 días</div><div class="value" id="kpi-expenses">—</div><div class="sub" id="kpi-expenses-sub">—</div></div>
    <div class="card success"><div class="label">Total disponible + proyectado</div><div class="value" id="kpi-total">—</div><div class="sub">Saldo + cheques netos + inversiones</div></div>
  </div>
  <div class="panel">
    <h2>Proyección de saldo bancario <span class="hint" id="projection-hint"></span></h2>
    <div class="legend">
      <span><span class="dot" style="background:#1a1ac7"></span>Saldo proyectado (cierre día)</span>
      <span><span class="dot" style="background:#c0392b"></span>Saldo mínimo</span>
      <span><span class="dot" style="background:#0a8a5e"></span>Excedente invertible</span>
    </div>
    <div class="chart-wrap"><canvas id="chart-30"></canvas></div>
  </div>
  <div class="panel panel-collapsible" id="alerts-panel">
    <h2 onclick="toggleCollapse('alerts-panel')">
      <span>Alertas y oportunidades</span>
      <span class="alert-summary" id="alerts-summary"></span>
      <span class="toggle">▶</span>
    </h2>
    <div class="panel-body"><div id="alerts-container"></div></div>
  </div>
  <div class="panel"><h2>Resumen 90 días <span class="hint">Por semana</span></h2><div class="chart-wrap"><canvas id="chart-90"></canvas></div></div>
  <div class="panel">
    <h2>Próximos eventos <span class="hint" id="upcoming-hint">próximos 30 días</span></h2>
    <div class="toolbar">
      <input type="date" id="upcoming-from" style="max-width:150px">
      <input type="date" id="upcoming-to" style="max-width:150px">
      <select id="upcoming-type" style="max-width:200px">
        <option value="all">Todos los tipos</option>
        <option value="ingresos">Solo ingresos</option>
        <option value="egresos">Solo egresos</option>
        <option value="cheque">Solo cheques</option>
        <option value="gasto">Solo gastos</option>
        <option value="movimiento">Solo movimientos</option>
        <option value="inversion">Solo vtos. de inversión</option>
      </select>
      <input type="text" id="upcoming-search" placeholder="Buscar..." style="max-width:220px">
      <span class="muted" id="upcoming-count"></span>
      <span class="spacer"></span>
      <button id="btn-upcoming-reset">Limpiar</button>
    </div>
    <div class="scroll-x"><table id="upcoming-table"><thead><tr><th>Fecha</th><th>Tipo</th><th>Concepto</th><th class="num">Monto</th><th class="num">Saldo proy.</th></tr></thead><tbody></tbody></table></div>
  </div>
</section>

<section id="cheques">
  <div class="panel">
    <h2>Listado de cheques</h2>
    <div class="toolbar">
      <select id="check-filter" style="max-width:240px">
        <option value="all">Todos</option>
        <option value="pendiente">Pendientes</option>
        <option value="en_proceso_deposito">En proceso de depósito</option>
        <option value="acreditado">Acreditados</option>
        <option value="rechazado">Rechazados</option>
        <option value="anulado">Anulados</option>
      </select>
      <input type="text" id="check-search" placeholder="Buscar contraparte, nº o banco..." style="min-width:240px;flex:1">
      <button id="btn-check-reset">×</button>
    </div>
    <div class="totalbar" id="check-totalbar"></div>
    <div class="scroll-x"><table id="check-table"><thead><tr><th>Nº</th><th>Banco</th><th>Beneficiario</th><th>Pago</th><th class="num">Importe</th><th>Estado</th><th>Estado banco</th></tr></thead><tbody></tbody></table></div>
  </div>
</section>

<section id="gastos">
  <div class="panel">
    <h2>Listado de gastos</h2>
    <div class="toolbar">
      <select id="expense-filter-method" style="max-width:200px"><option value="all">Todos los métodos</option></select>
      <select id="expense-filter-status" style="max-width:160px">
        <option value="all">Todos</option>
        <option value="proyectado">Proyectado</option>
        <option value="pagado">Pagado</option>
      </select>
      <span class="muted" id="expense-count"></span>
    </div>
    <div class="mini-cards" id="expense-summary"></div>
    <div class="scroll-x"><table id="expense-table"><thead><tr><th>Fecha</th><th>Concepto</th><th>Método</th><th>Categoría</th><th class="num">Monto</th><th>Estado</th></tr></thead><tbody></tbody></table></div>
  </div>
</section>

<section id="inversiones">
  <div class="panel">
    <h2>Inversiones</h2>
    <div class="toolbar"><span class="muted" id="invest-count"></span></div>
    <div class="scroll-x"><table id="invest-table"><thead><tr><th>Tipo</th><th>Plataforma</th><th>Inicio</th><th>Vto</th><th class="num">Monto</th><th class="num">TNA</th><th class="num">Estimado</th><th>Estado</th></tr></thead><tbody></tbody></table></div>
  </div>
</section>

<section id="movimientos">
  <div class="panel">
    <h2>Movimientos proyectados</h2>
    <div class="toolbar"><span class="muted" id="movement-count"></span></div>
    <div class="scroll-x"><table id="movement-table"><thead><tr><th>Fecha</th><th>Tipo</th><th>Concepto</th><th class="num">Monto</th></tr></thead><tbody></tbody></table></div>
  </div>
</section>

<section id="saldos">
  <div class="panel" style="background:var(--accent-soft);border-color:#c4ebf6">
    <h2>Agregar / editar saldo de apertura</h2>
    <p class="muted" style="font-size:12px;margin:0 0 12px">
      Cargás el saldo acá, hacés clic en <strong>"Descargar saldos.csv actualizado"</strong>,
      reemplazás el archivo en <code>1_inputs/saldos/</code> y corrés <code>actualizar.bat</code>.
      Si la fecha + cuenta ya existe, se sobreescribe.
    </p>
    <form id="form-saldo" class="form-grid">
      <label>Fecha<input type="date" id="saldo-fecha" required></label>
      <label>Cuenta<select id="saldo-cuenta" required></select></label>
      <label>Saldo apertura (ARS)<input type="number" id="saldo-monto" step="0.01" required placeholder="Ej: 8500000"></label>
      <label>Notas (opcional)<input type="text" id="saldo-notas" placeholder="Ej: post pago AFIP"></label>
      <button type="submit" class="primary-btn">Agregar a la lista</button>
    </form>
    <div id="saldo-pending" style="margin-top:12px;display:none">
      <div style="background:var(--surface);border:1px solid var(--border);border-radius:8px;padding:10px 14px;font-size:13px">
        <strong id="saldo-pending-count">0</strong> cambios pendientes (sin guardar al CSV).
        <button id="btn-descargar-saldos" class="accent-btn" style="margin-left:8px">⬇ Descargar saldos.csv actualizado</button>
        <button id="btn-descartar-cambios" style="margin-left:4px">Descartar</button>
      </div>
    </div>
  </div>
  <div class="panel">
    <h2>Histórico de saldos de apertura</h2>
    <div class="toolbar"><span class="muted" id="balance-count"></span></div>
    <div class="scroll-x"><table id="balance-table"><thead><tr><th>Fecha</th><th>Cuenta</th><th class="num">Saldo apertura</th><th>Notas</th><th>Origen</th></tr></thead><tbody></tbody></table></div>
  </div>
</section>

</main>

<script id="state-data" type="application/json">__STATE_JSON__</script>
<script>
const STATE = JSON.parse(document.getElementById("state-data").textContent);
const STATUS_LABELS = STATE.status_labels;
const ACTIVE = ["pendiente", "en_proceso_deposito"];
const BRAND = { primary: "#1a1ac7", accent: "#22c4ec", danger: "#c0392b", success: "#0a8a5e" };
const fmtARS = new Intl.NumberFormat("es-AR", {style:"currency", currency:"ARS", maximumFractionDigits:0});
const fmtN = new Intl.NumberFormat("es-AR", {maximumFractionDigits:0});
const fmtPct = (n) => (n==null||isNaN(n))?"—":new Intl.NumberFormat("es-AR",{minimumFractionDigits:2,maximumFractionDigits:2}).format(n)+"%";
function fmtDate(iso) { if(!iso) return "—"; const [y,m,d]=iso.split("-"); return `${d}/${m}/${y}`; }
function fmtDateShort(iso) { if(!iso) return "—"; const [,m,d]=iso.split("-"); return `${d}/${m}`; }
function escapeHtml(s) { if(s==null) return ""; return String(s).replace(/[&<>"']/g,c=>({"&":"&amp;","<":"&lt;",">":"&gt;",'"':"&quot;","'":"&#39;"}[c])); }
function todayISO() { return STATE.today; }
function addDays(iso, n) { const d=new Date(iso+"T12:00:00"); d.setDate(d.getDate()+n); return d.toISOString().slice(0,10); }
function diffDays(a,b) { return Math.round((new Date(b+"T12:00:00")-new Date(a+"T12:00:00"))/86400000); }
window.toggleCollapse = (id) => document.getElementById(id).classList.toggle("expanded");
document.querySelectorAll(".tab").forEach(t => t.addEventListener("click", () => {
  document.querySelectorAll(".tab").forEach(x => x.classList.remove("active"));
  document.querySelectorAll("section").forEach(x => x.classList.remove("active"));
  t.classList.add("active");
  document.getElementById(t.dataset.tab).classList.add("active");
}));

function statusChipClass(s) {
  if (s==="acreditado") return "success";
  if (s==="rechazado") return "danger";
  if (s==="anulado") return "warn";
  if (s==="en_proceso_deposito") return "accent";
  return "primary";
}

function renderCheques() {
  const filter = document.getElementById("check-filter").value;
  const search = document.getElementById("check-search").value.toLowerCase().trim();
  let list = STATE.cheques.slice();
  if (filter !== "all") list = list.filter(c => c.ESTADO === filter);
  if (search) list = list.filter(c =>
    (c.BENEFICIARIO||"").toLowerCase().includes(search) ||
    (c.N_CHEQUE||"").toLowerCase().includes(search) ||
    (c.BANCO||"").toLowerCase().includes(search));
  list.sort((a,b) => (a.FECHA_PAGO||"").localeCompare(b.FECHA_PAGO||""));
  const tb = document.getElementById("check-totalbar");
  if (!list.length) {
    tb.innerHTML = `<div class="item"><div class="lbl">Sin resultados</div></div>`;
  } else {
    const total = list.reduce((s,c) => s+(+c.IMPORTE||0), 0);
    const pend = list.filter(c => c.ESTADO==="pendiente");
    const ep = list.filter(c => c.ESTADO==="en_proceso_deposito");
    const acr = list.filter(c => c.ESTADO==="acreditado");
    let parts = [`<div class="item"><div class="lbl">${list.length} cheques</div><div class="val">${fmtARS.format(total)}</div></div>`];
    if (pend.length) parts.push(`<div class="sep"></div><div class="item"><div class="lbl">Pendientes</div><div class="val danger">${pend.length} · ${fmtARS.format(pend.reduce((s,c)=>s+(+c.IMPORTE||0),0))}</div></div>`);
    if (ep.length) parts.push(`<div class="sep"></div><div class="item"><div class="lbl">En depósito</div><div class="val accent">${ep.length} · ${fmtARS.format(ep.reduce((s,c)=>s+(+c.IMPORTE||0),0))}</div></div>`);
    if (acr.length) parts.push(`<div class="sep"></div><div class="item"><div class="lbl">Acreditados</div><div class="val success">${acr.length} · ${fmtARS.format(acr.reduce((s,c)=>s+(+c.IMPORTE||0),0))}</div></div>`);
    tb.innerHTML = parts.join("");
  }
  const tbody = document.querySelector("#check-table tbody");
  if (!list.length) { tbody.innerHTML = `<tr><td colspan="7" class="empty">Sin cheques.</td></tr>`; return; }
  tbody.innerHTML = list.map(c => {
    const sCl = statusChipClass(c.ESTADO);
    return `<tr><td>${escapeHtml(c.N_CHEQUE)}</td><td>${escapeHtml(c.BANCO||"—")}</td><td>${escapeHtml(c.BENEFICIARIO||"—")}</td><td>${fmtDate(c.FECHA_PAGO)}</td><td class="num">${fmtARS.format(+c.IMPORTE||0)}</td><td><span class="chip ${sCl}">${STATUS_LABELS[c.ESTADO]||c.ESTADO}</span></td><td><span class="chip">${escapeHtml(c.ESTADO_BANCO||"")}</span></td></tr>`;
  }).join("");
}
document.getElementById("check-filter").addEventListener("change", renderCheques);
document.getElementById("check-search").addEventListener("input", renderCheques);
document.getElementById("btn-check-reset").addEventListener("click", () => {
  document.getElementById("check-filter").value = "all";
  document.getElementById("check-search").value = "";
  renderCheques();
});

function renderGastos() {
  const fM = document.getElementById("expense-filter-method").value;
  const fS = document.getElementById("expense-filter-status").value;
  let list = STATE.gastos.slice();
  if (fM !== "all") list = list.filter(x => x.METODO === fM);
  if (fS !== "all") list = list.filter(x => x.ESTADO === fS);
  list.sort((a,b) => (a.FECHA||"").localeCompare(b.FECHA||""));
  document.getElementById("expense-count").textContent = `${list.length} gastos`;
  const tbody = document.querySelector("#expense-table tbody");
  if (!list.length) { tbody.innerHTML = `<tr><td colspan="6" class="empty">Sin gastos.</td></tr>`; return; }
  tbody.innerHTML = list.map(x => {
    const sCh = x.ESTADO === "pagado" ? `<span class="chip success">Pagado</span>` : `<span class="chip warn">Proyectado</span>`;
    return `<tr><td>${fmtDate(x.FECHA)}</td><td>${escapeHtml(x.CONCEPTO)}</td><td><span class="chip">${escapeHtml(x.METODO)}</span></td><td><span class="chip">${escapeHtml(x.CATEGORIA)}</span></td><td class="num" style="color:var(--danger)">−${fmtARS.format(+x.MONTO||0)}</td><td>${sCh}</td></tr>`;
  }).join("");
  const today = todayISO(); const horizon = addDays(today, 30);
  const upc = STATE.gastos.filter(x => x.ESTADO==="proyectado" && x.FECHA>=today && x.FECHA<=horizon);
  const byMethod = {}; let totalUpc = 0;
  upc.forEach(x => { byMethod[x.METODO] = (byMethod[x.METODO]||0)+(+x.MONTO||0); totalUpc += (+x.MONTO||0); });
  const cs = document.getElementById("expense-summary");
  if (!upc.length) { cs.innerHTML = `<div class="mini-card"><div class="label">Sin gastos próximos</div><div class="value">—</div></div>`; }
  else {
    const t = `<div class="mini-card danger"><div class="label">Total 30 días</div><div class="value">${fmtARS.format(totalUpc)}</div></div>`;
    cs.innerHTML = t + Object.entries(byMethod).map(([m,v]) => `<div class="mini-card"><div class="label">${escapeHtml(m)}</div><div class="value">${fmtARS.format(v)}</div></div>`).join("");
  }
}
function buildExpenseFilterOptions() {
  const sel = document.getElementById("expense-filter-method");
  const metodos = [...new Set(STATE.gastos.map(g => g.METODO))].filter(Boolean).sort();
  sel.innerHTML = `<option value="all">Todos los métodos</option>` + metodos.map(m => `<option value="${escapeHtml(m)}">${escapeHtml(m)}</option>`).join("");
}
document.getElementById("expense-filter-method").addEventListener("change", renderGastos);
document.getElementById("expense-filter-status").addEventListener("change", renderGastos);

function renderInversiones() {
  const today = todayISO();
  const list = STATE.inversiones.slice().sort((a,b) => (a.FECHA_VTO||"").localeCompare(b.FECHA_VTO||""));
  const active = list.filter(i => i.FECHA_VTO >= today).length;
  document.getElementById("invest-count").textContent = `${active} activas / ${list.length} total`;
  const tbody = document.querySelector("#invest-table tbody");
  if (!list.length) { tbody.innerHTML = `<tr><td colspan="8" class="empty">Sin inversiones.</td></tr>`; return; }
  tbody.innerHTML = list.map(inv => {
    const isActive = inv.FECHA_VTO >= today;
    const dias = inv.FECHA_INICIO ? diffDays(inv.FECHA_INICIO, inv.FECHA_VTO) : 0;
    const monto = +inv.MONTO || 0;
    const tna = +inv.TNA || 0;
    const est = (tna>0 && dias>0) ? monto * (1 + (tna/100)*(dias/365)) : monto;
    return `<tr><td><span class="chip accent">${escapeHtml(inv.TIPO)}</span></td><td>${escapeHtml(inv.PLATAFORMA||"—")}</td><td>${fmtDate(inv.FECHA_INICIO)}</td><td>${fmtDate(inv.FECHA_VTO)}</td><td class="num">${fmtARS.format(monto)}</td><td class="num">${tna?fmtPct(tna):"—"}</td><td class="num">${fmtARS.format(est)}</td><td><span class="chip ${isActive?"success":""}">${isActive?"Activa":"Vencida"}</span></td></tr>`;
  }).join("");
}

function renderMovimientos() {
  const list = STATE.movimientos.slice().sort((a,b) => (a.FECHA||"").localeCompare(b.FECHA||""));
  document.getElementById("movement-count").textContent = `${list.length} movimientos`;
  const tbody = document.querySelector("#movement-table tbody");
  if (!list.length) { tbody.innerHTML = `<tr><td colspan="4" class="empty">Sin movimientos.</td></tr>`; return; }
  tbody.innerHTML = list.map(m => {
    const ch = m.TIPO === "ingreso" ? `<span class="chip success">Ingreso</span>` : `<span class="chip warn">Egreso</span>`;
    return `<tr><td>${fmtDate(m.FECHA)}</td><td>${ch}</td><td>${escapeHtml(m.CONCEPTO)}</td><td class="num">${fmtARS.format(+m.MONTO||0)}</td></tr>`;
  }).join("");
}

// === Buffer de saldos pendientes (cambios in-memory que aun no se guardaron al CSV) ===
let saldosPendientes = [];

function renderSaldos() {
  const combined = STATE.saldos.slice();
  saldosPendientes.forEach(p => {
    const idx = combined.findIndex(s => s.FECHA === p.FECHA && s.CUENTA === p.CUENTA);
    if (idx >= 0) combined[idx] = { ...combined[idx], ...p, _pendiente: true };
    else combined.push({ ...p, _pendiente: true });
  });
  combined.sort((a,b) => (b.FECHA||"").localeCompare(a.FECHA||""));
  document.getElementById("balance-count").textContent = `${combined.length} registros`;
  const tbody = document.querySelector("#balance-table tbody");
  if (!combined.length) { tbody.innerHTML = `<tr><td colspan="5" class="empty">Sin saldos cargados. Usá el formulario de arriba.</td></tr>`; return; }
  tbody.innerHTML = combined.slice(0,100).map(b => {
    const origen = b._pendiente
      ? `<span class="chip warn">Pendiente</span>`
      : `<span class="chip">${escapeHtml(b.ARCHIVO_ORIGEN||"csv")}</span>`;
    return `<tr><td>${fmtDate(b.FECHA)}</td><td>${escapeHtml(b.CUENTA)}</td><td class="num">${fmtARS.format(+b.SALDO||0)}</td><td>${escapeHtml(b.NOTAS||"")}</td><td>${origen}</td></tr>`;
  }).join("");
  const pendBlock = document.getElementById("saldo-pending");
  if (saldosPendientes.length > 0) {
    pendBlock.style.display = "block";
    document.getElementById("saldo-pending-count").textContent = saldosPendientes.length;
  } else {
    pendBlock.style.display = "none";
  }
}

function buildSaldoCuentas() {
  const sel = document.getElementById("saldo-cuenta");
  sel.innerHTML = STATE.cuentas.map(c =>
    `<option value="${escapeHtml(c.id)}">${escapeHtml(c.nombre)}${c.banco ? " - " + escapeHtml(c.banco) : ""}</option>`
  ).join("");
  document.getElementById("saldo-fecha").value = STATE.today;
}

document.getElementById("form-saldo").addEventListener("submit", (e) => {
  e.preventDefault();
  const fecha = document.getElementById("saldo-fecha").value;
  const cuenta = document.getElementById("saldo-cuenta").value;
  const monto = parseFloat(document.getElementById("saldo-monto").value);
  const notas = document.getElementById("saldo-notas").value.trim();
  if (!fecha || isNaN(monto)) { alert("Falta fecha o monto"); return; }
  saldosPendientes = saldosPendientes.filter(p => !(p.FECHA === fecha && p.CUENTA === cuenta));
  saldosPendientes.push({ FECHA: fecha, CUENTA: cuenta, SALDO: monto, NOTAS: notas });
  document.getElementById("form-saldo").reset();
  document.getElementById("saldo-fecha").value = STATE.today;
  renderSaldos();
});

document.getElementById("btn-descartar-cambios").addEventListener("click", () => {
  if (!confirm("¿Descartar los cambios pendientes?")) return;
  saldosPendientes = [];
  renderSaldos();
});

document.getElementById("btn-descargar-saldos").addEventListener("click", () => {
  const map = {};
  STATE.saldos.forEach(s => { map[`${s.FECHA}|${s.CUENTA}`] = s; });
  saldosPendientes.forEach(p => { map[`${p.FECHA}|${p.CUENTA}`] = p; });
  const all = Object.values(map).sort((a,b) => (a.FECHA||"").localeCompare(b.FECHA||""));
  const lines = ["fecha,cuenta,saldo_apertura,notas"];
  all.forEach(s => {
    const fecha = s.FECHA || "";
    const cuenta = (s.CUENTA || "").replace(/,/g, " ");
    const saldo = (+s.SALDO || 0);
    const notas = (s.NOTAS || "").replace(/,/g, " ").replace(/\r?\n/g, " ");
    lines.push(`${fecha},${cuenta},${saldo},${notas}`);
  });
  const csv = lines.join("\n");
  const blob = new Blob([csv], { type: "text/csv;charset=utf-8" });
  const url = URL.createObjectURL(blob);
  const a = document.createElement("a");
  a.href = url;
  a.download = "saldos.csv";
  a.click();
  URL.revokeObjectURL(url);
  alert("Descargado.\n\n1) Movelo a 1_inputs/saldos/ (reemplaza el viejo).\n2) Doble clic en actualizar.bat.");
});

let chart30, chart90;
function getMinBalanceTotal() { return STATE.cuentas.reduce((s,a) => s + (a.min_balance||0), 0); }
function suggestInvestment(days, amount) {
  if (days<=0) return null;
  let s = "Caución 1-7 días";
  if (days>=180) s = "LECAP larga o bono corto";
  else if (days>=90) s = "LECAP corta o plazo fijo pre-cancelable";
  else if (days>=30) s = "Plazo fijo 30 días o caución renovable";
  else if (days>=7) s = "Caución 7-30 días";
  const diff = ((STATE.params.caucionRate||0)-(STATE.params.fciRate||0))/100;
  return { suggestion: s, extra: amount*diff*(days/365) };
}

function renderDashboard() {
  const today = todayISO();
  const apertura = STATE.points30.length ? STATE.points30[0].balance - (STATE.points30[0].inflow||0) + (STATE.points30[0].outflow||0) : 0;
  const sortedB = STATE.saldos.slice().sort((a,b) => (b.FECHA||"").localeCompare(a.FECHA||""));
  const latestDate = sortedB.length ? sortedB[0].FECHA : null;
  document.getElementById("kpi-balance").textContent = fmtARS.format(apertura);
  document.getElementById("kpi-balance-sub").textContent = latestDate ? `Apertura desde ${fmtDate(latestDate)}` : "Sin saldos";
  document.getElementById("projection-hint").textContent = latestDate ? `Última carga: ${fmtDate(latestDate)}` : "Cargá un saldo en la pestaña Saldos";

  const activeInv = STATE.inversiones.filter(i => i.FECHA_VTO >= today);
  const invTotal = activeInv.reduce((s,i) => s+(+i.MONTO||0), 0);
  document.getElementById("kpi-invest").textContent = fmtARS.format(invTotal);
  document.getElementById("kpi-invest-sub").textContent = `${activeInv.length} posiciones`;

  const active = STATE.cheques.filter(c => ACTIVE.includes(c.ESTADO));
  const cR = active.filter(c => c.TIPO==="recibido").reduce((s,c) => s+(+c.IMPORTE||0), 0);
  const cE = active.filter(c => c.TIPO==="emitido").reduce((s,c) => s+(+c.IMPORTE||0), 0);
  document.getElementById("kpi-checks").textContent = fmtARS.format(cR-cE);
  document.getElementById("kpi-checks-sub").textContent = `+${fmtARS.format(cR)} / −${fmtARS.format(cE)}`;

  const horizon = addDays(today, 30);
  const upcExp = STATE.gastos.filter(x => x.ESTADO==="proyectado" && x.FECHA>=today && x.FECHA<=horizon);
  const eT = upcExp.reduce((s,x) => s+(+x.MONTO||0), 0);
  document.getElementById("kpi-expenses").textContent = fmtARS.format(eT);
  document.getElementById("kpi-expenses-sub").textContent = `${upcExp.length} gastos`;
  document.getElementById("kpi-total").textContent = fmtARS.format(apertura + invTotal + (cR-cE));

  drawChart30();
  drawChart90();
  renderAlerts();
  renderUpcoming();

  document.getElementById("last-update").textContent = STATE.info_corrida.fecha ? `Generado: ${STATE.info_corrida.fecha}` : "";
}

function drawChart30() {
  const ctx = document.getElementById("chart-30");
  const labels = STATE.points30.map(p => fmtDateShort(p.date));
  const min = getMinBalanceTotal();
  const buffer = STATE.params.buffer || 0;
  if (chart30) chart30.destroy();
  const cctx = ctx.getContext("2d");
  const grad = cctx.createLinearGradient(0,0,0,320);
  grad.addColorStop(0,"rgba(26,26,199,0.20)"); grad.addColorStop(1,"rgba(34,196,236,0.05)");
  chart30 = new Chart(ctx, { type:"line", data: {
    labels,
    datasets: [
      { label:"Saldo cierre", data: STATE.points30.map(p => p.balance), borderColor: BRAND.primary, backgroundColor: grad, fill:true, tension:0.25, pointRadius:2, pointBackgroundColor: BRAND.primary, borderWidth:2.5 },
      { label:"Mínimo", data: STATE.points30.map(() => min), borderColor: BRAND.danger, borderDash:[4,4], pointRadius:0, borderWidth:1.5, fill:false },
      { label:"Umbral", data: STATE.points30.map(() => min+buffer), borderColor: BRAND.success, borderDash:[2,4], pointRadius:0, borderWidth:1.5, fill:false }
    ]
  }, options: { responsive:true, maintainAspectRatio:false,
    plugins: { legend:{display:false}, tooltip:{callbacks:{label:c=>c.dataset.label+": "+fmtARS.format(c.raw)}} },
    scales: { y:{ticks:{callback:v=>fmtN.format(v),color:"#5b6385"},grid:{color:"rgba(17,22,61,0.06)"}}, x:{ticks:{maxRotation:0,autoSkip:true,maxTicksLimit:12,color:"#5b6385"},grid:{display:false}} }
  }});
}
function drawChart90() {
  const weeks = [];
  for (let i=0;i<STATE.points90.length;i+=7) {
    const slice = STATE.points90.slice(i, i+7); if (!slice.length) continue;
    weeks.push({ label: fmtDateShort(slice[0].date), avg: slice.reduce((s,p) => s+p.balance, 0)/slice.length, min: Math.min(...slice.map(p=>p.balance)), max: Math.max(...slice.map(p=>p.balance)) });
  }
  const ctx = document.getElementById("chart-90"); if (chart90) chart90.destroy();
  const min = getMinBalanceTotal();
  chart90 = new Chart(ctx, { type:"bar", data: {
    labels: weeks.map(w => w.label),
    datasets: [
      { type:"line", label:"Mín. ref", data: weeks.map(() => min), borderColor: BRAND.danger, borderDash:[4,4], pointRadius:0, borderWidth:1.5, fill:false },
      { label:"Mín semana", data: weeks.map(w => w.min), backgroundColor:"rgba(192,57,43,0.55)", borderRadius:3 },
      { label:"Promedio", data: weeks.map(w => w.avg), backgroundColor:"rgba(26,26,199,0.75)", borderRadius:3 },
      { label:"Máx semana", data: weeks.map(w => w.max), backgroundColor:"rgba(34,196,236,0.75)", borderRadius:3 }
    ]
  }, options: { responsive:true, maintainAspectRatio:false,
    plugins: { legend:{position:"bottom", labels:{boxWidth:10,font:{size:11},color:"#5b6385"}}, tooltip:{callbacks:{label:c=>c.dataset.label+": "+fmtARS.format(c.raw)}} },
    scales: { y:{ticks:{callback:v=>fmtN.format(v),color:"#5b6385"},grid:{color:"rgba(17,22,61,0.06)"}}, x:{ticks:{color:"#5b6385"},grid:{display:false}} }
  }});
}

function renderAlerts() {
  const c = document.getElementById("alerts-container");
  const summary = document.getElementById("alerts-summary");
  const panel = document.getElementById("alerts-panel");
  if (!STATE.saldos.length) {
    c.innerHTML = `<div class="alert info"><span class="icon">i</span><div>No hay saldos cargados. Cargá uno en la pestaña <strong>Saldos</strong> o pegá un CSV en <code>1_inputs/saldos/</code>.</div></div>`;
    summary.innerHTML = `<span class="badge info">setup pendiente</span>`;
    panel.classList.add("expanded"); return;
  }
  const items = []; let dangerCount=0, warnCount=0, successCount=0, infoCount=0;
  if (STATE.shortfalls && STATE.shortfalls.length) {
    const first = STATE.shortfalls[0]; const tot = Math.max(...STATE.shortfalls.map(s => s.deficit)); dangerCount++;
    items.push(`<div class="alert danger"><span class="icon">▼</span><div><strong>Necesidad de fondeo</strong> el ${fmtDate(first.date)}: faltarían <strong>${fmtARS.format(tot)}</strong>. ${STATE.shortfalls.length>1?`(${STATE.shortfalls.length} días con déficit)`:""}</div></div>`);
  }
  (STATE.surplus_windows||[]).forEach(w => {
    if (w.days < 2) return; successCount++;
    const sug = suggestInvestment(w.days, w.min_surplus);
    const extra = sug && sug.extra > 0 ? ` Sobre FCI ~<strong>${fmtARS.format(sug.extra)}</strong> extra.` : "";
    items.push(`<div class="alert success"><span class="icon">▲</span><div><strong>Excedente</strong> ${fmtDate(w.start)} a ${fmtDate(w.end)} (<strong>${w.days}d</strong>): <strong>${fmtARS.format(w.min_surplus)}</strong> → <strong>${sug.suggestion}</strong>.${extra}</div></div>`);
  });
  const today = todayISO();
  STATE.inversiones.filter(i => i.FECHA_VTO >= today && i.FECHA_VTO <= addDays(today,7)).forEach(inv => {
    infoCount++;
    items.push(`<div class="alert info"><span class="icon">●</span><div><strong>Vence ${escapeHtml(inv.TIPO)}</strong> el ${fmtDate(inv.FECHA_VTO)} por ${fmtARS.format(+inv.MONTO||0)}.</div></div>`);
  });
  STATE.cheques.filter(c => ACTIVE.includes(c.ESTADO) && c.FECHA_PAGO >= today && c.FECHA_PAGO <= addDays(today,3) && c.TIPO==="emitido").forEach(c => {
    warnCount++;
    items.push(`<div class="alert warn"><span class="icon">✎</span><div><strong>Cheque ${c.ESTADO==="en_proceso_deposito"?"en depósito":"emitido"}</strong> a ${escapeHtml(c.BENEFICIARIO||c.N_CHEQUE)} se debita el ${fmtDate(c.FECHA_PAGO)} por ${fmtARS.format(+c.IMPORTE||0)}.</div></div>`);
  });
  STATE.gastos.filter(x => x.ESTADO==="proyectado" && x.FECHA >= today && x.FECHA <= addDays(today,7)).sort((a,b) => (+b.MONTO||0)-(+a.MONTO||0)).slice(0,3).forEach(x => {
    warnCount++;
    items.push(`<div class="alert warn"><span class="icon">↓</span><div><strong>Gasto próximo</strong>: ${escapeHtml(x.CONCEPTO)} (${escapeHtml(x.METODO)}) el ${fmtDate(x.FECHA)} por ${fmtARS.format(+x.MONTO||0)}.</div></div>`);
  });
  if (!items.length) { items.push(`<div class="alert success"><span class="icon">✓</span><div>Sin alertas.</div></div>`); successCount++; }
  c.innerHTML = items.join("");
  const chips = [];
  if (dangerCount) chips.push(`<span class="badge danger">${dangerCount} crítica${dangerCount>1?"s":""}</span>`);
  if (warnCount) chips.push(`<span class="badge warn">${warnCount} aviso${warnCount>1?"s":""}</span>`);
  if (successCount && !dangerCount) chips.push(`<span class="badge success">${successCount} oportunidad${successCount>1?"es":""}</span>`);
  if (infoCount) chips.push(`<span class="badge info">${infoCount} info</span>`);
  if (!chips.length) chips.push(`<span class="badge success">todo OK</span>`);
  summary.innerHTML = chips.join(" ");
  if (dangerCount > 0) panel.classList.add("expanded");
}

function renderUpcoming() {
  const fromDate = document.getElementById("upcoming-from").value;
  const toDate = document.getElementById("upcoming-to").value;
  const typeF = document.getElementById("upcoming-type").value;
  const search = document.getElementById("upcoming-search").value.toLowerCase().trim();
  const rows = [];
  STATE.points30.forEach(p => p.events.forEach(ev => rows.push({date:p.date, kind:ev.kind, type:ev.type, concept:ev.concept, amount:ev.sign*ev.amount, balance:p.balance})));
  let filtered = rows;
  if (fromDate) filtered = filtered.filter(r => r.date >= fromDate);
  if (toDate) filtered = filtered.filter(r => r.date <= toDate);
  if (typeF !== "all") {
    if (typeF === "ingresos") filtered = filtered.filter(r => r.amount > 0);
    else if (typeF === "egresos") filtered = filtered.filter(r => r.amount < 0);
    else filtered = filtered.filter(r => r.kind === typeF);
  }
  if (search) filtered = filtered.filter(r => (r.concept||"").toLowerCase().includes(search) || (r.type||"").toLowerCase().includes(search));
  document.getElementById("upcoming-count").textContent = `${filtered.length} eventos`;
  document.getElementById("upcoming-hint").textContent = (fromDate||toDate) ? `${fromDate?fmtDate(fromDate):"—"} a ${toDate?fmtDate(toDate):"—"}` : "próximos 30 días";
  const tbody = document.querySelector("#upcoming-table tbody");
  if (!filtered.length) { tbody.innerHTML = `<tr><td colspan="5" class="empty">Sin eventos.</td></tr>`; return; }
  tbody.innerHTML = filtered.map(r => {
    const cl = r.amount >= 0 ? "success" : "danger"; const sg = r.amount >= 0 ? "+" : "";
    return `<tr><td>${fmtDate(r.date)}</td><td><span class="chip ${cl}">${escapeHtml(r.type)}</span></td><td>${escapeHtml(r.concept)}</td><td class="num" style="color:${r.amount>=0?'var(--success)':'var(--danger)'}">${sg}${fmtARS.format(r.amount)}</td><td class="num">${fmtARS.format(r.balance)}</td></tr>`;
  }).join("");
}
["upcoming-from","upcoming-to","upcoming-type","upcoming-search"].forEach(id => {
  document.getElementById(id).addEventListener("input", renderUpcoming);
  document.getElementById(id).addEventListener("change", renderUpcoming);
});
document.getElementById("btn-upcoming-reset").addEventListener("click", () => {
  document.getElementById("upcoming-from").value = "";
  document.getElementById("upcoming-to").value = "";
  document.getElementById("upcoming-type").value = "all";
  document.getElementById("upcoming-search").value = "";
  renderUpcoming();
});

buildExpenseFilterOptions();
buildSaldoCuentas();
renderCheques();
renderGastos();
renderInversiones();
renderMovimientos();
renderSaldos();
renderDashboard();
</script>
</body>
</html>"""
