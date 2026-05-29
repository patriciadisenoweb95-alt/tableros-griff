<?php require_once __DIR__ . '/../auth_check.php'; ?>

<!DOCTYPE html>
<html lang="es">
<head>
<meta charset="UTF-8">
<title>Tablero Griff Salud - Dashboard</title>
<script src="https://cdn.jsdelivr.net/npm/chart.js@4.4.1/dist/chart.umd.min.js"></script>
<script>
// Cargar datos.js con cache-buster + esperar DOM antes de init()
window._datosCargado = false;
window._domCargado = false;
function _tryInit(){
  if (window._datosCargado && window._domCargado && typeof init === 'function') init();
}
(function() {
  const s = document.createElement('script');
  s.src = 'datos.js?v=' + Date.now();
  s.onload = () => { window._datosCargado = true; _tryInit(); };
  s.onerror = () => {
    window._datosCargado = true;
    if (document.readyState !== 'loading'){
      const e = document.getElementById('error'); if (e) e.style.display = 'block';
    } else {
      document.addEventListener('DOMContentLoaded', () => { const e = document.getElementById('error'); if (e) e.style.display = 'block'; });
    }
  };
  document.head.appendChild(s);
})();
document.addEventListener('DOMContentLoaded', () => { window._domCargado = true; _tryInit(); });
</script>
<style>
* { box-sizing: border-box; margin: 0; padding: 0; }
body { font-family: 'Segoe UI', Arial, sans-serif; background: #F4F6F8; color: #1F2937; padding: 20px; }
.container { max-width: 1500px; margin: 0 auto; }
header { background: linear-gradient(135deg, #1A2D9C 0%, #29ABE2 100%); color: white; padding: 24px 32px; border-radius: 12px; margin-bottom: 16px; box-shadow: 0 4px 16px rgba(26,45,156,0.2); display: flex; align-items: center; gap: 20px; flex-wrap: wrap; }
.logo-wrap { display:flex; align-items:center; gap:14px; }
.logo { width: 60px; height: 60px; background: white; border-radius: 14px; padding: 8px; box-shadow: 0 2px 8px rgba(0,0,0,0.2); display: flex; align-items: center; justify-content: center; }
header h1 { font-size: 22px; margin-bottom: 2px; }
header .sub { font-size: 13px; opacity: 0.9; }
.controls { display: flex; gap: 12px; align-items: center; flex-wrap: wrap; font-size: 13px; margin-left: auto; }
.controls select { padding: 6px 12px; border-radius: 6px; border: none; font-size: 13px; }
.timestamp { opacity: 0.85; font-size: 11px; }
.tabs { display: flex; gap: 4px; margin-bottom: 16px; background: white; padding: 6px; border-radius: 10px; box-shadow: 0 2px 8px rgba(0,0,0,0.05); flex-wrap: wrap; }
.tab { padding: 10px 18px; border-radius: 8px; cursor: pointer; font-size: 13px; font-weight: 500; color: #6B7280; transition: all 0.15s; border: none; background: transparent; }
.tab:hover { background: #F3F4F6; color: #1F2937; }
.tab.active { background: #1A2D9C; color: white; }
.tab-content { display: none; }
.tab-content.active { display: block; }
.grid { display: grid; grid-template-columns: repeat(4, 1fr); gap: 16px; margin-bottom: 24px; }
.kpi { background: white; padding: 18px 20px; border-radius: 10px; box-shadow: 0 2px 8px rgba(0,0,0,0.05); border-left: 4px solid #1A2D9C; }
.kpi.warn { border-left-color: #F59E0B; }
.kpi.danger { border-left-color: #DC2626; }
.kpi.good { border-left-color: #10B981; }
.kpi .label { font-size: 12px; color: #6B7280; text-transform: uppercase; letter-spacing: 0.5px; margin-bottom: 6px; }
.kpi .value { font-size: 22px; font-weight: 700; color: #1F2937; }
.kpi .sub { font-size: 11px; color: #9CA3AF; margin-top: 4px; }
.row { display: grid; grid-template-columns: 2fr 1fr; gap: 16px; margin-bottom: 24px; }
.card { background: white; padding: 20px; border-radius: 10px; box-shadow: 0 2px 8px rgba(0,0,0,0.05); }
.card h3 { font-size: 15px; color: #1A2D9C; margin-bottom: 14px; padding-bottom: 8px; border-bottom: 2px solid #E5E7EB; }
.alert { padding: 12px 14px; border-radius: 8px; margin-bottom: 8px; display: flex; justify-content: space-between; align-items: center; font-size: 13px; }
.alert.danger { background: #FEE2E2; color: #991B1B; border-left: 3px solid #DC2626; }
.alert.warn { background: #FEF3C7; color: #92400E; border-left: 3px solid #F59E0B; }
.alert.info { background: #DBEAFE; color: #1E40AF; border-left: 3px solid #2563EB; }
table { width: 100%; border-collapse: collapse; font-size: 13px; }
th { background: #F3F4F6; padding: 10px; text-align: left; font-weight: 600; color: #374151; border-bottom: 2px solid #E5E7EB; }
td { padding: 8px 10px; border-bottom: 1px solid #F3F4F6; }
tr:hover { background: #F9FAFB; }
.num { text-align: right; font-variant-numeric: tabular-nums; }
.empty { text-align: center; color: #9CA3AF; padding: 40px 20px; font-style: italic; }
.badge { display: inline-block; padding: 2px 8px; border-radius: 12px; font-size: 11px; font-weight: 600; }
.badge.green { background: #D1FAE5; color: #065F46; }
.badge.amber { background: #FEF3C7; color: #92400E; }
.badge.red { background: #FEE2E2; color: #991B1B; }
.badge.blue { background: #DBEAFE; color: #1E40AF; }
canvas { max-height: 280px; }
.detalle-table th:first-child, .detalle-table td:first-child { text-align: left; min-width: 320px; }
.row-section { background: #1A2D9C !important; color: white; font-weight: 600; cursor: pointer; user-select: none; }
.row-section td { color: white; }
.row-section .chevron { display: inline-block; margin-right: 8px; transition: transform 0.2s; }
.row-section.collapsed .chevron { transform: rotate(-90deg); }
.row-total { background: #D9D9D9; font-weight: 700; }
.row-highlight { background: #C6EFCE; font-weight: 700; }
.row-coef { background: #FFEB9C; }
.row-hidden { display: none; }
.sub-tabs { display: flex; gap: 4px; padding: 12px 20px 0 20px; }
.sub-tab { padding: 8px 14px; border-radius: 6px 6px 0 0; cursor: pointer; font-size: 12px; font-weight: 500; color: #6B7280; border: none; background: #F3F4F6; }
.sub-tab.active { background: white; color: #1A2D9C; border-bottom: 2px solid #1A2D9C; font-weight: 700; }
.sub-tab-content { display: none; }
.sub-tab-content.active { display: block; }
.controls-bar { display: flex; justify-content: space-between; align-items: center; margin-bottom: 16px; gap: 12px; flex-wrap: wrap; }
.btn { padding: 8px 14px; border-radius: 6px; border: 1px solid #D1D5DB; background: white; cursor: pointer; font-size: 12px; color: #374151; font-weight: 500; }
.btn:hover { background: #F3F4F6; }
.btn-primary { background: #1A2D9C; color: white; border-color: #1A2D9C; }
.btn-primary:hover { background: #2D7588; }
.cobranzas-table input[type=number], .cobranzas-table input[type=date], .cobranzas-table select,
.checklist-table input[type=number], .checklist-table select { padding: 4px 6px; border: 1px solid #D1D5DB; border-radius: 4px; font-size: 12px; font-family: inherit; }
.cobranzas-table input[type=number] { width: 120px; text-align: right; }
.cobranzas-table input[type=date] { width: 130px; }
.cobranzas-table select, .checklist-table select { width: 110px; }
.checklist-table input[type=number] { width: 110px; text-align: right; }
.modificado input, .modificado select { background: #FEF3C7; }
.cobranzas-banner { background: #FEF3C7; border: 1px solid #F59E0B; padding: 12px 16px; border-radius: 8px; margin-bottom: 12px; display: flex; justify-content: space-between; align-items: center; font-size: 13px; flex-wrap: wrap; gap: 8px; }
.cobranzas-banner strong { color: #92400E; }
.error-box { background: #FEE2E2; border: 1px solid #DC2626; border-radius: 10px; padding: 24px; text-align: center; color: #991B1B; }
.checklist-table .row-cli { background: #F0F9FF; cursor: pointer; user-select: none; }
.checklist-table .row-cli:hover { background: #E0F2FE; }
.checklist-table .row-fact { background: #FAFAFA; }
.checklist-table .chevron { display: inline-block; margin-right: 6px; width: 12px; }
@media (max-width: 900px) { .grid { grid-template-columns: repeat(2, 1fr); } .row { grid-template-columns: 1fr; } }
</style>
</head>
<body>
<div class="container">
  <header>
    <div class="logo-wrap">
      <div class="logo">
        <svg viewBox="0 0 60 60" width="44" height="44" xmlns="http://www.w3.org/2000/svg">
          <circle cx="30" cy="30" r="28" fill="#1A2D9C"/>
          <path d="M30 14 C25 14, 22 18, 22 23 C22 30, 30 38, 30 38 C30 38, 38 30, 38 23 C38 18, 35 14, 30 14 Z" fill="#FFFFFF"/>
          <rect x="27" y="40" width="6" height="10" fill="#FFFFFF" rx="1"/>
          <rect x="22" y="43" width="16" height="4" fill="#FFFFFF" rx="1"/>
        </svg>
      </div>
      <div>
        <h1>GRIFF SALUD SA</h1>
        <div class="sub">Tablero de Facturación e Impuestos · CUIT 30-71713418-0</div>
      </div>
    </div>
    <div class="controls">
      <label>Año:</label>
      <select id="yearSel"><option value="2026">2026</option><option value="2025">2025</option></select>
      <label>Cliente:</label>
      <select id="cliSel"><option value="">Todos</option></select>
      <span class="timestamp" id="timestamp"></span>
    </div>
  </header>

  <div id="error" style="display:none;" class="error-box">
    <h2>No se pudo cargar <code>datos.js</code></h2>
    <p>Ejecutá <code>actualizar.bat</code> para generar los datos.</p>
  </div>

  <div id="content" style="display:none;">

    <!-- BANNER GLOBAL DE CAMBIOS -->
    <div id="cobBanner" class="cobranzas-banner" style="display:none;">
      <span><strong>⚠️ Tenés cambios sin aplicar al Excel.</strong> Descargá el archivo y ejecutá <code>actualizar.bat</code>.</span>
      <div>
        <button class="btn btn-primary" onclick="descargarCobranzasUpdates()">📥 Descargar para actualizar</button>
        <button class="btn" onclick="descartarCambios()">Descartar</button>
      </div>
    </div>

    <div class="tabs">
      <button class="tab active" data-tab="general">📊 General</button>
      <button class="tab" data-tab="cobranzas">💸 Cobranzas</button>
      <button class="tab" data-tab="iva">💰 IVA</button>
      <button class="tab" data-tab="tasa">🏛️ Tasa Comercio Cba</button>
      <button class="tab" data-tab="iibb">📍 IIBB Convenio Multilateral</button>
    </div>

    <div class="tab-content active" id="tab-general">
      <div class="grid">
        <div class="kpi"><div class="label">Facturado YTD (con IVA y todo)</div><div class="value" id="kpi_facturado">-</div><div class="sub" id="kpi_facturas"></div></div>
        <div class="kpi good"><div class="label">IVA Débito YTD</div><div class="value" id="kpi_iva">-</div><div class="sub">21% + 10,5%</div></div>
        <div class="kpi warn"><div class="label">Impuestos estimados YTD</div><div class="value" id="kpi_impuestos">-</div><div class="sub" id="kpi_pct_imp"></div></div>
        <div class="kpi danger"><div class="label">Cobranzas pendientes</div><div class="value" id="kpi_pendiente">-</div><div class="sub" id="kpi_pct_cob"></div></div>
      </div>
      <div class="row">
        <div class="card"><h3>Facturación e Impuestos por mes</h3><canvas id="chartMensual"></canvas></div>
        <div class="card"><h3>Composición de Impuestos</h3><canvas id="chartImpuestos"></canvas></div>
      </div>
      <div class="row">
        <div class="card"><h3>Próximos vencimientos</h3><div id="vencimientos"></div></div>
        <div class="card"><h3>Alertas</h3><div id="alertas"></div></div>
      </div>
      <div class="card" style="margin-bottom:24px;">
        <h3>Checklist mensual de facturación (clientes fijos) <span style="font-size:11px; color:#9CA3AF; font-weight:normal;">— Click en una fila para ver el detalle por factura y editar estado de cobro</span></h3>
        <div style="overflow-x:auto;"><table class="checklist-table" id="tablaCheck"></table></div>
      </div>
      <div class="card" style="margin-bottom:24px;">
        <h3>Resumen impuestos mensuales</h3>
        <div style="overflow-x:auto;"><table id="tablaImp"></table></div>
      </div>
      <div class="card" style="margin-bottom:24px;">
        <h3>Últimas facturas emitidas</h3>
        <div style="overflow-x:auto;"><table id="tablaFac"></table></div>
      </div>
    </div>

    <div class="tab-content" id="tab-cobranzas">
      <div class="card" style="margin-bottom:24px;">
        <h3>Gestión de Cobranzas</h3>
        <p style="color:#6B7280; font-size:13px; margin-bottom:12px;">Editá estados, montos y fechas. Soporta cobros parciales. Los cambios se guardan en el navegador hasta que descargues el archivo y ejecutes actualizar.bat.</p>
        <div class="grid">
          <div class="kpi"><div class="label">Total facturado</div><div class="value" id="cob_total">-</div></div>
          <div class="kpi good"><div class="label">Cobrado</div><div class="value" id="cob_cobrado">-</div><div class="sub" id="cob_pct_cobrado"></div></div>
          <div class="kpi warn"><div class="label">Pendiente</div><div class="value" id="cob_pendiente">-</div></div>
          <div class="kpi danger"><div class="label">Vencido / Parcial</div><div class="value" id="cob_otros">-</div></div>
        </div>
        <div class="controls-bar">
          <div><label>Filtrar:</label>
            <select id="cobFiltro" onchange="renderCobranzas()">
              <option value="">Todas</option><option value="Pendiente">Pendientes</option><option value="Parcial">Parciales</option>
              <option value="Vencida">Vencidas</option><option value="Cobrada">Cobradas</option>
            </select>
          </div>
          <span id="cantPendientes" style="font-size:12px;color:#6B7280;"></span>
        </div>
        <div style="overflow-x:auto;"><table class="cobranzas-table" id="tablaCobranzas"></table></div>
      </div>
    </div>

    <div class="tab-content" id="tab-iva">
      <div class="card" style="margin-bottom:24px;">
        <h3>IVA · Liquidación mensual</h3>
        <div class="controls-bar"><button class="btn" onclick="toggleAll('tablaDetIVA', false)">📂 Expandir</button><button class="btn" onclick="toggleAll('tablaDetIVA', true)">📁 Comprimir</button></div>
        <div style="overflow-x:auto; max-height:75vh;"><table class="detalle-table" id="tablaDetIVA"></table></div>
      </div>
    </div>

    <div class="tab-content" id="tab-tasa">
      <div class="card" style="margin-bottom:24px;">
        <h3>Tasa Comercio e Industria · Córdoba</h3>
        <div class="controls-bar"><button class="btn" onclick="toggleAll('tablaDetTasa', false)">📂 Expandir</button><button class="btn" onclick="toggleAll('tablaDetTasa', true)">📁 Comprimir</button></div>
        <div style="overflow-x:auto; max-height:75vh;"><table class="detalle-table" id="tablaDetTasa"></table></div>
      </div>
    </div>

    <div class="tab-content" id="tab-iibb">
      <div class="card" style="margin-bottom:24px;">
        <h3>Ingresos Brutos · Convenio Multilateral</h3>
        <div class="sub-tabs">
          <button class="sub-tab active" data-subtab="caba">CABA (901)</button>
          <button class="sub-tab" data-subtab="cordoba">Córdoba (904)</button>
          <button class="sub-tab" data-subtab="resumen">Resumen</button>
        </div>
        <div style="padding: 12px 20px 20px 20px; background: white;">
          <div class="sub-tab-content active" id="subtab-caba">
            <div class="controls-bar"><strong>CABA · Coef 0,0433</strong><div><button class="btn" onclick="toggleAll('tablaDetCABA', false)">📂 Expandir</button><button class="btn" onclick="toggleAll('tablaDetCABA', true)">📁 Comprimir</button></div></div>
            <div style="overflow-x:auto;"><table class="detalle-table" id="tablaDetCABA"></table></div>
          </div>
          <div class="sub-tab-content" id="subtab-cordoba">
            <div class="controls-bar"><strong>Córdoba · Coef 0,9567</strong><div><button class="btn" onclick="toggleAll('tablaDetCba', false)">📂 Expandir</button><button class="btn" onclick="toggleAll('tablaDetCba', true)">📁 Comprimir</button></div></div>
            <div style="overflow-x:auto;"><table class="detalle-table" id="tablaDetCba"></table></div>
          </div>
          <div class="sub-tab-content" id="subtab-resumen">
            <div style="overflow-x:auto;"><table id="tablaIIBBResumen"></table></div>
          </div>
        </div>
      </div>
    </div>

  </div>
</div>

<script>
const MESES = ["Ene","Feb","Mar","Abr","May","Jun","Jul","Ago","Sep","Oct","Nov","Dic"];
let chartMensual, chartImpuestos;
const STORAGE_KEY = 'griff_cobranzas_pendientes_v1';
let cambiosPendientes = {};
const expandedClientes = {};  // {clienteIdx: true/false}

function fmtMoney(v){
  if (v === null || v === undefined || v === "" || typeof v !== 'number') return "-";
  if (Math.abs(v) < 0.01) return "-";
  const s = Math.abs(v).toLocaleString('es-AR', {minimumFractionDigits: 0, maximumFractionDigits: 0});
  return v < 0 ? `($${s})` : `$${s}`;
}
function fmtPct(v){ if (typeof v !== 'number') return "-"; return (v*100).toFixed(2) + "%"; }
function fmtCoef(v){ if (typeof v !== 'number') return "-"; return v.toFixed(4); }
function fmtFecha(v){
  if (!v) return "-";
  if (typeof v !== 'string') return v;
  const m = v.match(/(\d{4})-(\d{2})-(\d{2})/);
  if (m) return `${m[3]}/${m[2]}/${m[1]}`;
  const d = new Date(v);
  if (!isNaN(d)) return d.toLocaleDateString('es-AR');
  return v;
}
function parseFecha(v){
  if (!v || typeof v !== 'string') return "";
  const m = v.match(/(\d{4})-(\d{2})-(\d{2})/);
  if (m) return `${m[1]}-${m[2]}-${m[3]}`;
  return "";
}

function cargarCambiosLocales(){
  try { const s = localStorage.getItem(STORAGE_KEY); if (s) cambiosPendientes = JSON.parse(s); }
  catch(e){ cambiosPendientes = {}; }
}
function guardarCambiosLocales(){
  localStorage.setItem(STORAGE_KEY, JSON.stringify(cambiosPendientes));
  actualizarBannerCobranzas();
}
function actualizarBannerCobranzas(){
  document.getElementById('cobBanner').style.display = Object.keys(cambiosPendientes).length > 0 ? 'flex' : 'none';
}
function descartarCambios(){
  if (confirm("¿Descartar todos los cambios sin aplicar al Excel?")){
    cambiosPendientes = {};
    guardarCambiosLocales();
    render();
  }
}
function descargarCobranzasUpdates(){
  const blob = new Blob([JSON.stringify(cambiosPendientes, null, 2)], {type: 'application/json'});
  const url = URL.createObjectURL(blob);
  const a = document.createElement('a');
  a.href = url; a.download = 'cobranzas_updates.json';
  document.body.appendChild(a); a.click(); document.body.removeChild(a);
  URL.revokeObjectURL(url);
  alert("Archivo descargado.\n\nProcedimiento para aplicarlo:\n1) Movelo a la carpeta TABLERO FACTURACION\n2) Ejecutá actualizar.bat (doble-click)\n3) El Excel y el dashboard quedan sincronizados");
}

function getEstadoActual(f){
  const k = `${f.tipo}-${f.pto_vta}-${f.numero}`;
  if (cambiosPendientes[k] && 'estado_cobro' in cambiosPendientes[k]) return cambiosPendientes[k].estado_cobro;
  return f.estado_cobro || 'Pendiente';
}
function getMontoCobrado(f){
  const k = `${f.tipo}-${f.pto_vta}-${f.numero}`;
  if (cambiosPendientes[k] && 'monto_cobrado' in cambiosPendientes[k]) return cambiosPendientes[k].monto_cobrado;
  return f.monto_cobrado || 0;
}
function getFechaCobro(f){
  const k = `${f.tipo}-${f.pto_vta}-${f.numero}`;
  if (cambiosPendientes[k] && 'fecha_cobro' in cambiosPendientes[k]) return cambiosPendientes[k].fecha_cobro;
  return parseFecha(f.fecha_cobro);
}

function onCobranzaChange(facKey, campo, valor){
  const D = window.DATOS;
  const f = D.facturas.find(x => `${x.tipo}-${x.pto_vta}-${x.numero}` === facKey);
  if (!f) return;
  const k = facKey;
  if (!cambiosPendientes[k]) cambiosPendientes[k] = {};
  cambiosPendientes[k][campo] = valor;

  if (campo === 'estado_cobro' && valor === 'Cobrada') cambiosPendientes[k].monto_cobrado = f.total;
  if (campo === 'estado_cobro' && valor === 'Pendiente'){
    cambiosPendientes[k].monto_cobrado = 0;
    cambiosPendientes[k].fecha_cobro = "";
  }
  if (campo === 'monto_cobrado'){
    const monto = parseFloat(valor) || 0;
    if (monto >= f.total) cambiosPendientes[k].estado_cobro = 'Cobrada';
    else if (monto > 0) cambiosPendientes[k].estado_cobro = 'Parcial';
    else cambiosPendientes[k].estado_cobro = 'Pendiente';
  }
  guardarCambiosLocales();
  render();
}

function toggleSection(headerRow){
  let next = headerRow.nextElementSibling;
  const isCollapsed = headerRow.classList.contains('collapsed');
  while (next && !next.classList.contains('row-section')){
    if (isCollapsed) next.classList.remove('row-hidden');
    else next.classList.add('row-hidden');
    next = next.nextElementSibling;
  }
  headerRow.classList.toggle('collapsed');
}
function toggleAll(tableId, collapse){
  const table = document.getElementById(tableId);
  if (!table) return;
  table.querySelectorAll('.row-section').forEach(sec => {
    let next = sec.nextElementSibling;
    while (next && !next.classList.contains('row-section')){
      if (collapse) next.classList.add('row-hidden'); else next.classList.remove('row-hidden');
      next = next.nextElementSibling;
    }
    if (collapse) sec.classList.add('collapsed'); else sec.classList.remove('collapsed');
  });
}
function toggleCliente(idx){
  expandedClientes[idx] = !expandedClientes[idx];
  render();
}

function clasificarFila(label){
  if (!label) return '';
  const l = label.toLowerCase();
  if (l.includes('liquidación mensual') || l.includes('bases imponibles') || l.includes('alícuotas') ||
      l.includes('impuesto determinado') || l.includes('deducciones') || l.includes('resultado') ||
      l.includes('vencimientos y pagos') || l.includes('operaciones del') ||
      l.includes('iva débito fiscal') || l.includes('iva crédito fiscal') ||
      l === 'liquidación' || (l.includes('coeficiente unificado') && !l.includes('702010') && !l.includes('651110'))) return 'row-section';
  if (l.includes('a pagar (si saldo') || l.startsWith('a pagar (') || l.includes('total a pagar')) return 'row-highlight';
  if (l.startsWith('total') || l.includes('sub-total') || l.includes('total determinado')) return 'row-total';
  if ((l.includes('coeficiente') || l.includes('alícuota')) && (l.includes('702010') || l.includes('651110') || l === 'alícuota 2026' || l.includes('% crédito'))) return 'row-coef';
  return '';
}
function fmtCellByLabel(lbl, valObj){
  if (!valObj) return '-';
  if (valObj.tipo === 'fecha') return fmtFecha(valObj.v);
  if (valObj.tipo === 'num'){
    const l = (lbl||'').toLowerCase();
    if ((l.includes('alícuota') || l.includes('% crédito')) && Math.abs(valObj.v) < 1) return fmtPct(valObj.v);
    if (l.includes('coeficiente') && Math.abs(valObj.v) < 1) return fmtCoef(valObj.v);
    return fmtMoney(valObj.v);
  }
  if (valObj.tipo === 'texto' && valObj.v) return valObj.v;
  return '-';
}
function renderDetalle(targetId, hojaNombre){
  const D = window.DATOS;
  const detalle = (D.detalle_impuestos || {})[hojaNombre];
  if (!detalle) { document.getElementById(targetId).innerHTML = '<tbody><tr><td>Sin datos.</td></tr></tbody>'; return; }
  let html = '<thead><tr><th>Concepto</th>';
  MESES.forEach(m => html += `<th class="num">${m}</th>`);
  html += '<th class="num">Total</th></tr></thead><tbody>';
  for (const fila of detalle){
    const lbl = fila.label;
    if (!lbl) continue;
    if (lbl === 'GRIFF SALUD SA' || lbl.startsWith('TASA COMERCIO') || lbl.startsWith('INGRESOS BRUTOS') ||
        lbl.startsWith('IMPUESTO AL VALOR') || lbl === 'Año 2026' || lbl === 'Concepto') continue;
    const cls = clasificarFila(lbl);
    const isSection = cls === 'row-section';
    const labelDisplay = isSection ? `<span class="chevron">▼</span>${lbl}` : lbl;
    html += `<tr class="${cls}"${isSection ? ' onclick="toggleSection(this)"' : ''}><td>${labelDisplay}</td>`;
    for (const m of fila.meses) html += `<td class="num">${fmtCellByLabel(lbl, m)}</td>`;
    html += `<td class="num"><strong>${fmtCellByLabel(lbl, fila.total)}</strong></td></tr>`;
  }
  html += '</tbody>';
  document.getElementById(targetId).innerHTML = html;
  toggleAll(targetId, true);
}
function renderIIBBResumen(){
  const D = window.DATOS;
  const imp = D.impuestos_mensual;
  const caba = imp['IIBB CABA'] || {};
  const cba = imp['IIBB Córdoba'] || {};
  let html = '<thead><tr><th>Concepto</th>';
  MESES.forEach(m => html += `<th class="num">${m}</th>`);
  html += '<th class="num">Total</th></tr></thead><tbody>';
  [['IIBB CABA', caba], ['IIBB Córdoba', cba]].forEach(([lbl, row]) => {
    html += `<tr class="row-total"><td>${lbl}</td>`;
    for (let m = 1; m <= 12; m++) html += `<td class="num">${fmtMoney(row[`m${m}`] || 0)}</td>`;
    html += `<td class="num"><strong>${fmtMoney(row.anio || 0)}</strong></td></tr>`;
  });
  html += '<tr class="row-highlight"><td>TOTAL IIBB CM</td>';
  for (let m = 1; m <= 12; m++) html += `<td class="num">${fmtMoney((caba[`m${m}`]||0)+(cba[`m${m}`]||0))}</td>`;
  html += `<td class="num"><strong>${fmtMoney((caba.anio||0)+(cba.anio||0))}</strong></td></tr></tbody>`;
  document.getElementById('tablaIIBBResumen').innerHTML = html;
}

function renderCobranzas(){
  const D = window.DATOS;
  const anio = parseInt(document.getElementById('yearSel').value);
  const filtro = document.getElementById('cobFiltro').value;
  let totalFact = 0, totalCob = 0, totalPend = 0, totalOtros = 0;
  const facturas = D.facturas.filter(f => f.anio === anio && f.estado_afip !== 'Anulada');
  facturas.forEach(f => {
    const total = f.total_efec || 0;
    const monto = getMontoCobrado(f);
    const estado = getEstadoActual(f);
    totalFact += total;
    if (estado === 'Cobrada') totalCob += monto * (f.signo || 1);
    else if (estado === 'Parcial'){ totalCob += monto * (f.signo || 1); totalOtros += (total - monto * (f.signo || 1)); }
    else if (estado === 'Vencida') totalOtros += total;
    else if (estado === 'Pendiente') totalPend += total;
  });
  document.getElementById('cob_total').textContent = fmtMoney(totalFact);
  document.getElementById('cob_cobrado').textContent = fmtMoney(totalCob);
  document.getElementById('cob_pendiente').textContent = fmtMoney(totalPend);
  document.getElementById('cob_otros').textContent = fmtMoney(totalOtros);
  document.getElementById('cob_pct_cobrado').textContent = totalFact > 0 ? `${fmtPct(totalCob/totalFact)} cobrado` : '';

  const facFiltradas = facturas.filter(f => !filtro || getEstadoActual(f) === filtro);
  document.getElementById('cantPendientes').textContent = `${facFiltradas.length} facturas · ${Object.keys(cambiosPendientes).length} cambios pendientes`;

  let html = '<thead><tr><th>Fecha</th><th>Tipo</th><th>N°</th><th>Cliente</th><th>Concepto</th><th class="num">Total</th><th>Estado</th><th class="num">Monto Cobrado</th><th class="num">Saldo</th><th>Fecha Cobro</th></tr></thead><tbody>';
  facFiltradas.forEach(f => {
    const k = `${f.tipo}-${f.pto_vta}-${f.numero}`;
    const modif = cambiosPendientes[k] ? 'modificado' : '';
    const tipoBadge = f.tipo.startsWith('NC') ? `<span class="badge red">${f.tipo}</span>` : `<span class="badge green">${f.tipo}</span>`;
    const estado = getEstadoActual(f);
    const monto = getMontoCobrado(f);
    const total = f.total || 0;
    const saldo = total - monto;
    const fechaCobro = getFechaCobro(f);
    const selectHTML = `<select onchange="onCobranzaChange('${k}', 'estado_cobro', this.value)">${['Pendiente','Parcial','Cobrada','Vencida','Incobrable'].map(o => `<option value="${o}" ${estado===o?'selected':''}>${o}</option>`).join('')}</select>`;
    html += `<tr class="${modif}"><td>${fmtFecha(f.fecha)}</td><td>${tipoBadge}</td><td>${f.pto_vta||''}-${(f.numero||'').toString().padStart(8,'0')}</td><td><strong>${f.cliente||''}</strong></td><td>${(f.concepto||'').substring(0,40)}</td><td class="num">${fmtMoney(total)}</td><td>${selectHTML}</td><td class="num"><input type="number" step="0.01" value="${monto}" onchange="onCobranzaChange('${k}', 'monto_cobrado', this.value)"/></td><td class="num">${fmtMoney(saldo)}</td><td><input type="date" value="${fechaCobro}" onchange="onCobranzaChange('${k}', 'fecha_cobro', this.value)"/></td></tr>`;
  });
  html += '</tbody>';
  document.getElementById('tablaCobranzas').innerHTML = html;
}

function limpiarCambiosAplicados(){
  // Si un cambio en localStorage ya coincide con lo que está en datos.js, lo borramos
  const D = window.DATOS;
  let removidos = 0;
  for (const key of Object.keys(cambiosPendientes)){
    const cambio = cambiosPendientes[key];
    const f = D.facturas.find(x => `${x.tipo}-${x.pto_vta}-${x.numero}` === key);
    if (!f) continue;
    let yaAplicado = true;
    if ('estado_cobro' in cambio && cambio.estado_cobro !== f.estado_cobro) yaAplicado = false;
    if ('monto_cobrado' in cambio && Math.abs((parseFloat(cambio.monto_cobrado)||0) - (f.monto_cobrado||0)) > 0.01) yaAplicado = false;
    if ('fecha_cobro' in cambio && cambio.fecha_cobro){
      const fcExcel = parseFecha(f.fecha_cobro);
      if (cambio.fecha_cobro !== fcExcel) yaAplicado = false;
    }
    if (yaAplicado) { delete cambiosPendientes[key]; removidos++; }
  }
  if (removidos > 0){
    localStorage.setItem(STORAGE_KEY, JSON.stringify(cambiosPendientes));
    console.log(`[Cobranzas] Se limpiaron ${removidos} cambios ya aplicados al Excel`);
  }
}

function init(){
  if (typeof window.DATOS === 'undefined'){ document.getElementById('error').style.display = 'block'; return; }
  const D = window.DATOS;
  document.getElementById('timestamp').textContent = `Actualizado: ${D.timestamp}`;
  document.getElementById('content').style.display = 'block';
  cargarCambiosLocales();
  limpiarCambiosAplicados();

  const cliSel = document.getElementById('cliSel');
  [...new Set(D.facturas.map(f=>f.cliente).filter(c=>c))].sort().forEach(c => {
    const opt = document.createElement('option'); opt.value = c; opt.textContent = c; cliSel.appendChild(opt);
  });

  document.querySelectorAll('.tab').forEach(btn => {
    btn.addEventListener('click', () => {
      document.querySelectorAll('.tab').forEach(b => b.classList.remove('active'));
      document.querySelectorAll('.tab-content').forEach(c => c.classList.remove('active'));
      btn.classList.add('active');
      document.getElementById('tab-' + btn.dataset.tab).classList.add('active');
    });
  });
  document.querySelectorAll('.sub-tab').forEach(btn => {
    btn.addEventListener('click', () => {
      document.querySelectorAll('.sub-tab').forEach(b => b.classList.remove('active'));
      document.querySelectorAll('.sub-tab-content').forEach(c => c.classList.remove('active'));
      btn.classList.add('active');
      document.getElementById('subtab-' + btn.dataset.subtab).classList.add('active');
    });
  });
  document.getElementById('yearSel').addEventListener('change', render);
  document.getElementById('cliSel').addEventListener('change', render);
  render();
  actualizarBannerCobranzas();
}

function render(){
  const D = window.DATOS;
  const anio = parseInt(document.getElementById('yearSel').value);
  const cliFiltro = document.getElementById('cliSel').value;
  let fac = D.facturas.filter(f => f.anio === anio && f.estado_afip !== 'Anulada');
  if (cliFiltro) fac = fac.filter(f => f.cliente === cliFiltro);

  const totalConIVA = fac.reduce((s,r) => s + (r.total_efec || 0), 0);
  const totalIVA = fac.reduce((s,r) => s + (r.iva21_efec || 0), 0);
  const cantFac = fac.filter(f => !f.tipo.startsWith('NC')).length;
  const cantNC = fac.filter(f => f.tipo.startsWith('NC')).length;
  const imp = D.impuestos_mensual;
  const totalImpAnio = (imp['TOTAL IMPUESTOS DEL MES']||{anio:0}).anio || 0;

  let cob_total = 0, cob_cobrado = 0, cob_pend = 0;
  fac.forEach(f => {
    const total = f.total_efec || 0;
    const monto = getMontoCobrado(f) * (f.signo || 1);
    const estado = getEstadoActual(f);
    cob_total += total;
    if (estado === 'Cobrada') cob_cobrado += monto;
    else if (estado === 'Parcial') { cob_cobrado += monto; cob_pend += (total - monto); }
    else if (estado === 'Pendiente' || estado === 'Vencida') cob_pend += total;
  });

  document.getElementById('kpi_facturado').textContent = fmtMoney(totalConIVA);
  document.getElementById('kpi_facturas').textContent = `${cantFac} facturas · ${cantNC} NC`;
  document.getElementById('kpi_iva').textContent = fmtMoney(totalIVA);
  document.getElementById('kpi_impuestos').textContent = fmtMoney(totalImpAnio);
  document.getElementById('kpi_pct_imp').textContent = totalConIVA > 0 ? `${fmtPct(totalImpAnio/totalConIVA)} de lo facturado` : "";
  document.getElementById('kpi_pendiente').textContent = fmtMoney(cob_pend);
  document.getElementById('kpi_pct_cob').textContent = cob_total > 0 ? `${fmtPct(cob_cobrado/cob_total)} cobrado` : "";

  const facMes = new Array(12).fill(0);
  fac.forEach(f => { if (f.mes) facMes[f.mes-1] += (f.total_efec||0); });
  const impMes = new Array(12).fill(0);
  const totalImpRow = imp['TOTAL IMPUESTOS DEL MES'];
  if (totalImpRow) for (let m=1;m<=12;m++) impMes[m-1] = totalImpRow[`m${m}`] || 0;

  if (chartMensual) chartMensual.destroy();
  chartMensual = new Chart(document.getElementById('chartMensual'), {
    type: 'bar',
    data: { labels: MESES, datasets: [
      { label: 'Facturación total', data: facMes, backgroundColor: '#2D7588', borderRadius: 4 },
      { label: 'Impuestos est.', data: impMes, backgroundColor: '#F59E0B', borderRadius: 4 },
    ]},
    options: { responsive: true, maintainAspectRatio: false,
      plugins: { legend: { position: 'bottom' }, tooltip: { callbacks: { label: ctx => `${ctx.dataset.label}: ${fmtMoney(ctx.raw)}` } } },
      scales: { y: { ticks: { callback: v => '$'+(v/1e6).toFixed(1)+'M' } } } }
  });
  if (chartImpuestos) chartImpuestos.destroy();
  const totIVA = (imp['IVA']||{anio:0}).anio || 0;
  const totCABA = (imp['IIBB CABA']||{anio:0}).anio || 0;
  const totCBA = (imp['IIBB Córdoba']||{anio:0}).anio || 0;
  const totTasa = (imp['Tasa Comercio Cba']||{anio:0}).anio || 0;
  chartImpuestos = new Chart(document.getElementById('chartImpuestos'), {
    type: 'doughnut',
    data: { labels: ['IVA', 'IIBB CABA', 'IIBB Córdoba', 'Tasa Cba'], datasets: [{ data: [totIVA, totCABA, totCBA, totTasa], backgroundColor: ['#1A2D9C','#5DADE2','#F39C12','#E74C3C'] }] },
    options: { responsive: true, maintainAspectRatio: false, plugins: { legend: { position: 'bottom' }, tooltip: { callbacks: { label: ctx => `${ctx.label}: ${fmtMoney(ctx.raw)}` } } } }
  });

  const hoy = new Date();
  const venc = [];
  for (let m = 0; m < 12; m++){
    if (impMes[m] > 0){
      const fechaVenc = new Date(anio, m+1, 20);
      if (fechaVenc >= hoy || (fechaVenc.getMonth() === hoy.getMonth() && fechaVenc.getFullYear() === hoy.getFullYear())){
        const dias = Math.ceil((fechaVenc - hoy) / (1000*60*60*24));
        venc.push({ periodo: MESES[m], fecha: fechaVenc, dias, monto: impMes[m] });
      }
    }
  }
  venc.sort((a,b) => a.fecha - b.fecha);
  document.getElementById('vencimientos').innerHTML = venc.slice(0,4).map(v => {
    const cls = v.dias < 7 ? 'danger' : v.dias < 15 ? 'warn' : 'info';
    return `<div class="alert ${cls}"><span><strong>${v.periodo}</strong> · vence ${v.fecha.toLocaleDateString('es-AR')} (en ${v.dias} días)</span><strong>${fmtMoney(v.monto)}</strong></div>`;
  }).join('') || '<div class="empty">No hay vencimientos próximos.</div>';

  const alertas = [];
  const mesActual = hoy.getMonth() + 1;
  fac.forEach(f => {
    if (f.fecha && getEstadoActual(f) === 'Pendiente'){
      const fechaF = new Date(f.fecha);
      const dias = Math.ceil((hoy - fechaF) / (1000*60*60*24));
      if (dias > 30) alertas.push({nivel:'warn', html:`<span><strong>${f.cliente}</strong> · ${(f.concepto||'').substring(0,50)} · ${dias} días sin cobrar</span><strong>${fmtMoney(f.total_efec)}</strong>`});
    }
  });
  if (hoy.getDate() > 15){
    D.checklist.forEach(c => {
      const v = c[`m${mesActual}`];
      if (!v || v === 0) alertas.push({nivel:'danger', html:`<span>⚠️ Falta facturar este mes: <strong>${c.cliente}</strong></span>`});
    });
  }
  document.getElementById('alertas').innerHTML = alertas.slice(0,8).map(a=>`<div class="alert ${a.nivel}">${a.html}</div>`).join('') || '<div class="alert info">Todo en orden ✓</div>';

  // ============ CHECKLIST EXPANDIBLE ============
  let chk = '<thead><tr><th>Cliente / Factura</th><th>Detalle / Estado</th>';
  MESES.forEach(m => chk += `<th class="num">${m}</th>`);
  chk += '<th class="num">Total año</th><th class="num">Cobrado</th></tr></thead><tbody>';

  D.checklist.forEach((c, idx) => {
    const cli = c.cliente;
    // Encontrar facturas del cliente
    const facsCli = D.facturas.filter(f => f.cliente === cli && f.anio === anio && f.estado_afip !== 'Anulada')
                              .sort((a,b) => (a.mes||0) - (b.mes||0) || (a.numero||0) - (b.numero||0));
    const tieneFacs = facsCli.length > 0;
    const expanded = !!expandedClientes[idx];
    const chev = tieneFacs ? `<span class="chevron">${expanded ? '▼' : '▶'}</span>` : `<span class="chevron"> </span>`;
    const cursor = tieneFacs ? 'cursor:pointer;' : '';
    const onclick = tieneFacs ? `onclick="toggleCliente(${idx})"` : '';

    // Total cobrado de este cliente (con los cambios pendientes)
    let cobradoCli = 0;
    facsCli.forEach(f => { cobradoCli += getMontoCobrado(f) * (f.signo || 1); });

    chk += `<tr class="row-cli" style="${cursor}" ${onclick}>`;
    chk += `<td><strong>${chev}${cli}</strong></td>`;
    chk += `<td style="font-size:11px; color:#6B7280;">${c.concepto||''}</td>`;
    for (let m = 1; m <= 12; m++){
      const v = c[`m${m}`];
      chk += `<td class="num">${(v && v>0) ? `<span class="badge green">${fmtMoney(v)}</span>` : '-'}</td>`;
    }
    chk += `<td class="num"><strong>${fmtMoney(c.total)}</strong></td>`;
    chk += `<td class="num"><span class="badge ${cobradoCli >= c.total && c.total > 0 ? 'green' : cobradoCli > 0 ? 'blue' : 'amber'}">${fmtMoney(cobradoCli)}</span></td>`;
    chk += `</tr>`;

    // Sub-filas: facturas individuales si está expandido
    if (expanded && tieneFacs){
      facsCli.forEach(f => {
        const k = `${f.tipo}-${f.pto_vta}-${f.numero}`;
        const modif = cambiosPendientes[k] ? 'modificado' : '';
        const estado = getEstadoActual(f);
        const monto = getMontoCobrado(f);
        const tipoBadge = f.tipo.startsWith('NC') ? `<span class="badge red">${f.tipo}</span>` : `<span class="badge green">${f.tipo}</span>`;
        const selectHTML = `<select onchange="onCobranzaChange('${k}', 'estado_cobro', this.value); event.stopPropagation();" onclick="event.stopPropagation()">${['Pendiente','Parcial','Cobrada','Vencida','Incobrable'].map(o => `<option value="${o}" ${estado===o?'selected':''}>${o}</option>`).join('')}</select>`;
        chk += `<tr class="row-fact ${modif}">`;
        chk += `<td style="padding-left:36px; font-size:12px;">${tipoBadge} ${f.pto_vta}-${(f.numero||'').toString().padStart(8,'0')} · ${fmtFecha(f.fecha)}</td>`;
        chk += `<td style="font-size:11px; color:#374151;">${(f.concepto||'').substring(0,40)} ${selectHTML} <input type="number" step="0.01" value="${monto}" onchange="onCobranzaChange('${k}', 'monto_cobrado', this.value); event.stopPropagation();" onclick="event.stopPropagation()" placeholder="Monto cobrado"/></td>`;
        for (let m = 1; m <= 12; m++){
          if (m === f.mes) chk += `<td class="num" style="font-size:12px;">${fmtMoney(f.total_efec)}</td>`;
          else chk += `<td class="num" style="font-size:12px; color:#D1D5DB;">·</td>`;
        }
        chk += `<td class="num" style="font-size:12px;"><strong>${fmtMoney(f.total_efec)}</strong></td>`;
        const efectivoCobrado = monto * (f.signo || 1);
        const cls = estado === 'Cobrada' ? 'green' : estado === 'Parcial' ? 'blue' : estado === 'Pendiente' ? 'amber' : 'red';
        chk += `<td class="num" style="font-size:12px;"><span class="badge ${cls}">${fmtMoney(efectivoCobrado)}</span></td>`;
        chk += `</tr>`;
      });
    }
  });
  chk += '</tbody>';
  document.getElementById('tablaCheck').innerHTML = chk;

  // Tabla resumen impuestos
  let impHtml = '<thead><tr><th>Concepto</th>';
  MESES.forEach(m => impHtml += `<th class="num">${m}</th>`);
  impHtml += '<th class="num">Total año</th></tr></thead><tbody>';
  [['IVA Saldo a pagar', imp['IVA']],['IIBB CABA', imp['IIBB CABA']],['IIBB Córdoba', imp['IIBB Córdoba']],
   ['Tasa Comercio Cba', imp['Tasa Comercio Cba']],['TOTAL', imp['TOTAL IMPUESTOS DEL MES']]
  ].forEach(([lbl, row], idx, arr) => {
    const isTotal = idx === arr.length-1;
    impHtml += `<tr style="${isTotal?'background:#F3F4F6;font-weight:700;':''}"><td>${lbl}</td>`;
    for (let m = 1; m <= 12; m++) impHtml += `<td class="num">${fmtMoney(row ? row[`m${m}`] : 0)}</td>`;
    impHtml += `<td class="num"><strong>${fmtMoney(row ? row.anio : 0)}</strong></td></tr>`;
  });
  impHtml += '</tbody>';
  document.getElementById('tablaImp').innerHTML = impHtml;

  // Últimas facturas
  const facOrdenadas = [...fac].sort((a,b) => (b.fecha||'').localeCompare(a.fecha||'')).slice(0, 30);
  let facHtml = '<thead><tr><th>Fecha</th><th>Tipo</th><th>N°</th><th>Cliente</th><th>Concepto</th><th>Activ.</th><th class="num">Neto</th><th class="num">IVA</th><th class="num">Total</th><th>Cobro</th></tr></thead><tbody>';
  facOrdenadas.forEach(f => {
    const tipoBadge = f.tipo.startsWith('NC') ? `<span class="badge red">${f.tipo}</span>` : `<span class="badge green">${f.tipo}</span>`;
    const estado = getEstadoActual(f);
    let cobBadge = '-';
    if (estado === 'Cobrada') cobBadge = '<span class="badge green">Cobrada</span>';
    else if (estado === 'Parcial') cobBadge = '<span class="badge blue">Parcial</span>';
    else if (estado === 'Pendiente') cobBadge = '<span class="badge amber">Pendiente</span>';
    else if (estado === 'Vencida') cobBadge = '<span class="badge red">Vencida</span>';
    else if (estado) cobBadge = estado;
    facHtml += `<tr><td>${fmtFecha(f.fecha)}</td><td>${tipoBadge}</td><td>${f.pto_vta||''}-${(f.numero||'').toString().padStart(8,'0')}</td><td><strong>${f.cliente||''}</strong></td><td>${(f.concepto||'').substring(0,45)}</td><td>${f.actividad||''}</td><td class="num">${fmtMoney(f.neto_efec)}</td><td class="num">${fmtMoney(f.iva21_efec)}</td><td class="num"><strong>${fmtMoney(f.total_efec)}</strong></td><td>${cobBadge}</td></tr>`;
  });
  facHtml += '</tbody>';
  document.getElementById('tablaFac').innerHTML = facHtml;

  renderDetalle('tablaDetIVA', 'Detalle IVA');
  renderDetalle('tablaDetTasa', 'Detalle Tasa Cba');
  renderDetalle('tablaDetCABA', 'Detalle IIBB CABA');
  renderDetalle('tablaDetCba', 'Detalle IIBB Cba');
  renderIIBBResumen();
  renderCobranzas();
}
// init() se invoca desde _tryInit() del header cuando datos.js + DOM están listos
</script>
</body>
</html>
