# -*- coding: utf-8 -*-
"""
Genera dashboard.html autocontenido con identidad visual Griff Salud.
Soporta N meses dinamicamente (no esta hardcodeado a feb/mar).
"""

import json
import os
from datetime import datetime


def generar_html(payload, info_corrida, output_path):
    """Escribe dashboard.html en output_path a partir del payload."""
    data_json = json.dumps(payload, ensure_ascii=False, separators=(",", ":"),
                           default=str)
    info_json = json.dumps(info_corrida, ensure_ascii=False, default=str)
    html = HTML_TEMPLATE.replace("__PAYLOAD__", data_json)
    html = html.replace("__INFO__", info_json)
    html = html.replace("__GEN_DATE__",
                        datetime.now().strftime("%d/%m/%Y %H:%M"))
    with open(output_path, "w", encoding="utf-8") as f:
        f.write(html)
    return output_path


HTML_TEMPLATE = r"""<!DOCTYPE html>
<html lang="es">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Griff Salud - Dashboard Estado de Resultado</title>
<script src="https://cdn.jsdelivr.net/npm/chart.js@4.4.1/dist/chart.umd.min.js"></script>
<style>
:root{--griff-blue:#1A2D9C;--griff-blue-dark:#15246E;--griff-cyan:#29ABE2;--griff-cyan-soft:#7BE0FA;--bg:#F4F6FB;--card:#FFFFFF;--ink:#0E1B3D;--muted:#6B7691;--border:#E3E8F2;--green:#0E9F6E;--red:#E74C3C;--yellow:#F2B705;--purple:#7A52F4;color-scheme:light}
*{box-sizing:border-box;margin:0;padding:0}
body{font-family:-apple-system,BlinkMacSystemFont,"Segoe UI",Roboto,sans-serif;background:var(--bg);color:var(--ink);line-height:1.4;-webkit-font-smoothing:antialiased}
.header{background:linear-gradient(135deg,var(--griff-blue) 0%,var(--griff-blue-dark) 70%);color:white;padding:18px 32px 0;box-shadow:0 4px 20px rgba(10,31,140,0.15)}
.header-top{max-width:1400px;margin:0 auto;display:flex;align-items:center;justify-content:space-between;gap:24px;flex-wrap:wrap;padding-bottom:14px}
.brand{display:flex;align-items:center;gap:14px}
.logo-svg{height:46px;width:auto}
.brand-text h1{font-size:20px;font-weight:700;letter-spacing:-0.3px}
.brand-text p{font-size:13px;color:var(--griff-cyan-soft);margin-top:2px}
.period-selector{display:flex;gap:6px;background:rgba(255,255,255,0.08);padding:5px;border-radius:10px;flex-wrap:wrap}
.period-btn{padding:8px 15px;border:none;background:transparent;color:#cdd5f0;font-weight:600;font-size:12px;border-radius:7px;cursor:pointer;transition:all 0.2s;font-family:inherit}
.period-btn:hover{color:white}
.period-btn.active{background:var(--griff-cyan);color:var(--griff-blue-dark);box-shadow:0 2px 8px rgba(11,200,250,0.4)}
.main-tabs{max-width:1400px;margin:0 auto;display:flex;gap:0}
.main-tab{padding:13px 28px;border:none;background:transparent;color:#a8b3d8;font-weight:600;font-size:14px;cursor:pointer;font-family:inherit;border-bottom:3px solid transparent;transition:all 0.2s}
.main-tab:hover{color:white}
.main-tab.active{color:white;border-bottom-color:var(--griff-cyan);background:rgba(255,255,255,0.06)}
.container{max-width:1400px;margin:0 auto;padding:24px 32px 60px}
.tab-content{display:none}
.tab-content.active{display:block}
.section-title{font-size:14px;font-weight:700;text-transform:uppercase;letter-spacing:1.2px;color:var(--muted);margin:28px 0 12px;display:flex;align-items:center;gap:10px}
.section-title::before{content:"";width:4px;height:14px;background:var(--griff-cyan);border-radius:2px}
.kpi-grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(220px,1fr));gap:14px;margin-bottom:8px}
.kpi-card{background:var(--card);border-radius:12px;padding:18px 20px;border:1px solid var(--border);position:relative;overflow:hidden;transition:transform 0.15s,box-shadow 0.15s}
.kpi-card:hover{transform:translateY(-2px);box-shadow:0 8px 24px rgba(10,31,140,0.08)}
.kpi-card::before{content:"";position:absolute;top:0;left:0;width:3px;height:100%;background:var(--griff-cyan)}
.kpi-card.primary::before{background:var(--griff-blue)}
.kpi-card.positive::before{background:var(--green)}
.kpi-card.negative::before{background:var(--red)}
.kpi-card.warn::before{background:var(--yellow)}
.kpi-card.purple::before{background:var(--purple)}
.kpi-label{font-size:11px;font-weight:700;text-transform:uppercase;letter-spacing:0.8px;color:var(--muted);margin-bottom:6px}
.kpi-value{font-size:24px;font-weight:700;color:var(--ink);letter-spacing:-0.5px}
.kpi-meta{font-size:12px;color:var(--muted);margin-top:4px}
.delta-pos{color:var(--green);font-weight:600}
.delta-neg{color:var(--red);font-weight:600}
.grid-2{display:grid;grid-template-columns:1fr 1fr;gap:18px;margin-bottom:18px}
@media(max-width:980px){.grid-2{grid-template-columns:1fr}}
.panel{background:var(--card);border-radius:12px;border:1px solid var(--border);padding:18px 20px}
.panel-title{font-size:14px;font-weight:700;color:var(--ink);margin-bottom:14px;display:flex;justify-content:space-between;align-items:center;flex-wrap:wrap;gap:8px}
.panel-subtitle{font-size:11px;color:var(--muted);font-weight:500}
.chart-wrap{position:relative;height:280px}
table{width:100%;border-collapse:collapse;font-size:13px}
thead th{text-align:left;font-size:11px;font-weight:700;text-transform:uppercase;letter-spacing:0.6px;color:var(--muted);padding:10px 12px;border-bottom:1.5px solid var(--border);background:#FAFBFE;position:sticky;top:0;z-index:1}
tbody td{padding:10px 12px;border-bottom:1px solid var(--border);vertical-align:middle}
tbody tr:hover{background:#F8FAFE}
.right{text-align:right;font-variant-numeric:tabular-nums}
.os-tag{display:inline-block;padding:3px 10px;border-radius:6px;font-weight:700;font-size:11px;background:#EEF2FB;color:var(--griff-blue)}
.cat-tag{display:inline-block;padding:3px 9px;border-radius:6px;font-weight:600;font-size:10px;background:#F0F4FB;color:var(--griff-blue)}
.pill-pos{background:#E5F7EE;color:var(--green);padding:3px 8px;border-radius:6px;font-weight:600;font-size:11px}
.pill-neg{background:#FDECEA;color:var(--red);padding:3px 8px;border-radius:6px;font-weight:600;font-size:11px}
.bar-mini{display:inline-block;height:6px;border-radius:3px;background:linear-gradient(90deg,var(--griff-blue),var(--griff-cyan));vertical-align:middle;margin-right:6px}
.os-grid{display:grid;grid-template-columns:repeat(auto-fill,minmax(310px,1fr));gap:14px}
.os-card{background:var(--card);border:1px solid var(--border);border-radius:12px;padding:16px 18px;transition:all 0.15s}
.os-card:hover{box-shadow:0 6px 20px rgba(10,31,140,0.08)}
.os-card-header{display:flex;justify-content:space-between;align-items:center;margin-bottom:14px;padding-bottom:10px;border-bottom:1px solid var(--border)}
.os-name{font-size:18px;font-weight:800;color:var(--griff-blue);letter-spacing:-0.3px}
.os-share{font-size:11px;background:var(--griff-cyan);color:var(--griff-blue-dark);padding:3px 9px;border-radius:6px;font-weight:700}
.os-row{display:flex;justify-content:space-between;align-items:center;padding:5px 0;font-size:13px}
.os-row .lbl{color:var(--muted)}
.os-row .val{font-weight:600;font-variant-numeric:tabular-nums}
.os-row.divider{margin-top:6px;padding-top:8px;border-top:1px dashed var(--border)}
.os-row.result{margin-top:4px;font-size:14px;font-weight:700}
.os-row.tax{padding-left:12px;font-size:12px;font-style:italic;color:var(--muted)}
.note{background:#FFF8E1;border-left:3px solid var(--yellow);padding:12px 16px;border-radius:8px;margin-top:24px;font-size:12px;color:#5C4A0A}
.note strong{color:#3D2F00}
.foot{text-align:center;color:var(--muted);font-size:11px;margin-top:36px;padding-top:18px;border-top:1px solid var(--border)}
.search-box{padding:8px 12px;border:1px solid var(--border);border-radius:7px;font-family:inherit;font-size:13px;width:100%;max-width:300px}
.search-box:focus{outline:none;border-color:var(--griff-cyan);box-shadow:0 0 0 3px rgba(11,200,250,0.15)}
.filter-bar{display:flex;gap:8px;flex-wrap:wrap;margin-bottom:10px;align-items:center}
.filter-select{padding:8px 12px;border:1px solid var(--border);border-radius:7px;font-family:inherit;font-size:12px;background:white}
.btn{padding:8px 16px;border:none;border-radius:8px;font-family:inherit;font-size:12px;font-weight:600;cursor:pointer;background:var(--card);color:var(--ink);border:1px solid var(--border)}
.btn:hover{background:#F4F6FB}
.scrollbox{max-height:520px;overflow:auto;border-radius:8px}
.heatmap{width:100%;border-collapse:collapse;font-size:11px}
.heatmap th{padding:8px 6px;text-align:center;font-size:10px;font-weight:700;color:var(--muted);border-bottom:1px solid var(--border);background:#FAFBFE}
.heatmap td{padding:0;border:1px solid #fff;text-align:center;font-weight:600;font-variant-numeric:tabular-nums;color:white;font-size:11px;height:36px;min-width:70px}
.heatmap td.empty{background:#F4F6FB;color:#C8D0E0}
.heatmap td.label{background:#FAFBFE;color:var(--ink);text-align:left;padding:0 10px;font-weight:700}
.invoice-table th{padding:8px 6px}
.invoice-table td{padding:6px 8px;font-size:11px}
.cmp-table td.metric{font-weight:600;color:var(--ink)}
</style>
</head>
<body>
<header class="header">
  <div class="header-top">
    <div class="brand">
      <svg class="logo-svg" viewBox="0 0 280 100" xmlns="http://www.w3.org/2000/svg">
        <text x="0" y="62" font-family="Arial Black, sans-serif" font-weight="900" font-size="68" fill="#FFFFFF" letter-spacing="-3">griff</text>
        <text x="138" y="92" font-family="Arial Black, sans-serif" font-weight="900" font-size="30" fill="#0BC8FA" letter-spacing="-1">salud</text>
        <circle cx="35" cy="83" r="9" fill="#0BC8FA"/>
      </svg>
      <div class="brand-text"><h1 id="page-title">Estado de Resultado</h1><p>Dashboard por Obra Social</p></div>
    </div>
    <div class="period-selector" id="period-selector"></div>
  </div>
  <div class="main-tabs">
    <button class="main-tab active" data-tab="estado">Estado de Resultado</button>
    <button class="main-tab" data-tab="costos">Costos Prestacionales</button>
  </div>
</header>
<div class="container">

<div class="tab-content active" id="tab-estado">
  <div class="section-title">Resumen <span id="er-period-label" style="text-transform:none;letter-spacing:0;color:var(--ink);font-weight:600"></span></div>
  <div class="kpi-grid" id="er-kpis"></div>
  <div id="er-single">
    <div class="section-title">Analisis por Obra Social</div>
    <div class="grid-2">
      <div class="panel"><div class="panel-title">Participacion en Ingresos por OS</div><div class="chart-wrap"><canvas id="chartShare"></canvas></div></div>
      <div class="panel"><div class="panel-title">Resultado Neto por OS</div><div class="chart-wrap"><canvas id="chartResult"></canvas></div></div>
    </div>
    <div class="grid-2">
      <div class="panel"><div class="panel-title">Estructura Costos vs Ingresos <span class="panel-subtitle">% sobre ingresos netos por OS</span></div><div class="chart-wrap"><canvas id="chartStructure"></canvas></div></div>
      <div class="panel"><div class="panel-title">Costos Fijos vs Prestacionales <span class="panel-subtitle">% sobre ingresos</span></div><div class="chart-wrap"><canvas id="chartCosts"></canvas></div></div>
    </div>
    <div class="section-title">Ranking de Rentabilidad</div>
    <div class="panel" style="padding:0"><table><thead><tr><th>#</th><th>Obra Social</th><th class="right">Ingresos</th><th class="right">% Ing.</th><th class="right">Costos Prest.</th><th class="right">Costos Fijos</th><th class="right">Impuestos</th><th class="right">Resultado Neto</th><th class="right">Margen</th></tr></thead><tbody id="er-ranking"></tbody></table></div>
    <div class="section-title">Detalle por Obra Social</div>
    <div class="os-grid" id="er-os-cards"></div>
    <div class="section-title">OSPIF - Detalle por Sub-segmento</div>
    <div class="panel" style="padding:0"><table id="ospif-table"></table></div>
  </div>
  <div id="er-compare">
    <div class="section-title">Evolucion Mensual</div>
    <div class="grid-2">
      <div class="panel"><div class="panel-title">Ingresos, Costos y Resultado</div><div class="chart-wrap"><canvas id="trendMain"></canvas></div></div>
      <div class="panel"><div class="panel-title">Margen Neto %</div><div class="chart-wrap"><canvas id="trendMargen"></canvas></div></div>
    </div>
    <div class="section-title">Tabla Comparativa</div>
    <div class="panel" style="padding:0;overflow:auto"><table class="cmp-table" id="er-cmp-table"></table></div>
    <div class="section-title">Resultado Neto por OS - Evolucion</div>
    <div class="panel"><div class="chart-wrap"><canvas id="trendOs"></canvas></div></div>
  </div>
  <div class="note"><strong>Notas:</strong> Costos fijos distribuidos por participacion de cada OS sobre los ingresos netos del mes (MUSCARELO directo a OSSURRBAC). Impuestos cargados desde <strong>1_inputs/impuestos.xlsx</strong> y distribuidos por participacion en ingresos. Calculo: Resultado Antes Imp. = Ingresos Netos - Costos Prestac. - Costos Fijos; Resultado Neto = Resultado Antes Imp. - Impuestos.</div>
</div>

<div class="tab-content" id="tab-costos">
  <div class="section-title">Resumen <span id="cp-period-label" style="text-transform:none;letter-spacing:0;color:var(--ink);font-weight:600"></span></div>
  <div class="kpi-grid" id="cp-kpis"></div>
  <div id="cp-single">
    <div class="section-title">Distribucion</div>
    <div class="grid-2">
      <div class="panel"><div class="panel-title">Por Categoria de Prestacion</div><div class="chart-wrap"><canvas id="cpChartCat"></canvas></div></div>
      <div class="panel"><div class="panel-title">Por Obra Social</div><div class="chart-wrap"><canvas id="cpChartOs"></canvas></div></div>
    </div>
    <div class="section-title">Heatmap - Categoria x Obra Social</div>
    <div class="panel"><div class="scrollbox"><table class="heatmap" id="cp-heatmap"></table></div></div>
    <div class="section-title">Top 20 Prestadores</div>
    <div class="panel" style="padding:0"><div class="scrollbox"><table><thead><tr><th>#</th><th>Prestador</th><th class="right"># Fact.</th><th class="right">Facturado</th><th class="right">Debitos %</th><th class="right">A Pagar</th><th class="right">% total</th><th>OS</th></tr></thead><tbody id="cp-top"></tbody></table></div></div>
    <div class="section-title">Analisis de Plazos de Pago</div>
    <div class="panel" id="cp-plazos"></div>
    <div class="section-title">Todas las Facturas <span class="panel-subtitle" id="cp-inv-count" style="text-transform:none;letter-spacing:0"></span></div>
    <div class="panel">
      <div class="filter-bar">
        <input type="text" class="search-box" id="cp-search" placeholder="Buscar prestador o factura...">
        <select class="filter-select" id="cp-filter-os"></select>
        <select class="filter-select" id="cp-filter-cat"></select>
        <button class="btn" id="cp-clear">Limpiar</button>
      </div>
      <div class="scrollbox"><table class="invoice-table"><thead><tr><th>Prestador</th><th>Factura</th><th>Fecha pago</th><th>Periodo</th><th>Categoria</th><th>OS</th><th class="right">Plazo</th><th class="right">Facturado</th><th class="right">Debitos</th><th class="right">A Pagar</th></tr></thead><tbody id="cp-inv-body"></tbody></table></div>
    </div>
  </div>
  <div id="cp-compare">
    <div class="section-title">Evolucion Mensual</div>
    <div class="grid-2">
      <div class="panel"><div class="panel-title">Total a Pagar por Mes</div><div class="chart-wrap"><canvas id="cpTrendTotal"></canvas></div></div>
      <div class="panel"><div class="panel-title">Debitos % por Mes</div><div class="chart-wrap"><canvas id="cpTrendDeb"></canvas></div></div>
    </div>
    <div class="section-title">Tabla Comparativa</div>
    <div class="panel" style="padding:0;overflow:auto"><table class="cmp-table" id="cp-cmp-table"></table></div>
  </div>
  <div class="note"><strong>Limpieza aplicada:</strong> typos de OS consolidados (OSSURBAC/OSSURBACC -> OSSURRBAC); categorias duplicadas unificadas (TRASLADO/TRASLADOS/AJUSTE -> Traslado, CAPITADO/CAPITAS -> Capitado, AMBULARTORIO/AREA PROTEGIDA -> Ambulatorio). Facturas sin clasificar quedan como "Sin Clasificacion".</div>
</div>

<div class="foot">Griff Salud - Dashboard generado automaticamente el __GEN_DATE__ - <span id="foot-info"></span></div>
</div>

<script>
const P = __PAYLOAD__;
const INFO = __INFO__;
const ER = P.estado_resultado;
const CP = P.costos_prestacionales;
const PERIODOS = P.periodos;

const OS_COLOR={OSPEVIC:"#0A1F8C",OSPIF:"#0BC8FA",OSPLYFC:"#7A52F4",OSPM:"#0E9F6E",OSSURRBAC:"#F2B705",AMSURRBAC:"#E74C3C",UOM:"#6B7691"};
const CAT_COLOR={Ambulatorio:"#0BC8FA",Internado:"#0A1F8C",Capitado:"#7A52F4",Traslado:"#F2B705",Refacturacion:"#E74C3C",Protesis:"#0E9F6E",Intereses:"#6B7691","Sin Clasificacion":"#9CA8C0"};

const fmtMoney=v=>"$ "+new Intl.NumberFormat('es-AR',{maximumFractionDigits:0}).format(Math.round(v));
const fmtMoneyShort=v=>{const a=Math.abs(v),s=v<0?"-":"";if(a>=1e9)return s+"$ "+(a/1e9).toFixed(2).replace('.',',')+" B";if(a>=1e6)return s+"$ "+(a/1e6).toFixed(1).replace('.',',')+" M";if(a>=1e3)return s+"$ "+(a/1e3).toFixed(0)+" K";return s+"$ "+a.toFixed(0)};
const fmtMoneyFull=v=>{const s=v<0?"-":"";return s+"$ "+new Intl.NumberFormat('es-AR',{minimumFractionDigits:2,maximumFractionDigits:2}).format(Math.abs(v))};
const fmtPct=v=>(v*100).toFixed(1).replace('.',',')+" %";
const fmtNum=v=>new Intl.NumberFormat('es-AR').format(v);

let currentTab="estado";
let currentView=PERIODOS.length?PERIODOS[PERIODOS.length-1]:"compare";
let charts={};
function destroyChart(k){if(charts[k]){charts[k].destroy();delete charts[k];}}

function buildPeriodButtons(){
  let h="";
  PERIODOS.forEach(p=>{h+=`<button class="period-btn" data-view="${p}">${P.periodos_short[p]}</button>`;});
  if(PERIODOS.length>1) h+=`<button class="period-btn" data-view="compare">Comparativo</button>`;
  document.getElementById("period-selector").innerHTML=h;
  document.querySelectorAll(".period-btn").forEach(b=>b.addEventListener("click",()=>setView(b.dataset.view)));
}

// ===== ESTADO DE RESULTADO =====
function erKpisSingle(periodo){
  const m=ER[periodo];const t=m.totals;
  document.getElementById("er-kpis").innerHTML=`
  <div class="kpi-card primary"><div class="kpi-label">Afiliados</div><div class="kpi-value">${fmtNum(t.afiliados)}</div><div class="kpi-meta">Total cartera</div></div>
  <div class="kpi-card"><div class="kpi-label">Capita Promedio</div><div class="kpi-value">$ ${fmtNum(Math.round(t.capita_promedio_ponderado))}</div><div class="kpi-meta">Ponderado por afiliados</div></div>
  <div class="kpi-card"><div class="kpi-label">Ingresos Netos</div><div class="kpi-value">${fmtMoneyShort(t.ingresos_netos)}</div><div class="kpi-meta">Capita + Refuerzo + Extras - NC/D</div></div>
  <div class="kpi-card"><div class="kpi-label">Ingresos Extras</div><div class="kpi-value">${fmtMoneyShort(t.ingresos_extras)}</div><div class="kpi-meta">${fmtPct(t.ingresos_extras/t.ingresos_netos)} del ingreso</div></div>
  <div class="kpi-card warn"><div class="kpi-label">Costos Prestacionales</div><div class="kpi-value">${fmtMoneyShort(t.costos_prestacionales)}</div><div class="kpi-meta">${fmtPct(t.costos_prestacionales/t.ingresos_netos)} / Ing. netos</div></div>
  <div class="kpi-card purple"><div class="kpi-label">Costos Fijos</div><div class="kpi-value">${fmtMoneyShort(t.costos_fijos)}</div><div class="kpi-meta">${fmtPct(t.costos_fijos/t.ingresos_netos)} / Ing. netos</div></div>
  <div class="kpi-card"><div class="kpi-label">Resultado Antes Imp.</div><div class="kpi-value">${fmtMoneyShort(t.resultado_antes)}</div><div class="kpi-meta">Margen ${fmtPct(t.resultado_antes/t.ingresos_netos)}</div></div>
  <div class="kpi-card negative"><div class="kpi-label">- Impuestos</div><div class="kpi-value">${fmtMoneyShort(-t.impuestos)}</div><div class="kpi-meta">IIBB + IVA + Munic</div></div>
  <div class="kpi-card positive"><div class="kpi-label">Resultado Neto</div><div class="kpi-value">${fmtMoneyShort(t.resultado_neto)}</div><div class="kpi-meta">Margen ${fmtPct(t.margen)}</div></div>`;
}
function erKpisCompare(){
  const last=PERIODOS[PERIODOS.length-1],prev=PERIODOS.length>1?PERIODOS[PERIODOS.length-2]:null;
  const lt=ER[last].totals,pt=prev?ER[prev].totals:null;
  const kpis=[["Afiliados","afiliados",fmtNum,false],["Ingresos Netos","ingresos_netos",fmtMoneyShort,false],["Costos Prestacionales","costos_prestacionales",fmtMoneyShort,true],["Costos Fijos","costos_fijos",fmtMoneyShort,true],["Impuestos","impuestos",fmtMoneyShort,true],["Resultado Neto","resultado_neto",fmtMoneyShort,false]];
  document.getElementById("er-kpis").innerHTML=kpis.map(([lab,k,fmt,inv])=>{
    const lv=lt[k],pv=pt?pt[k]:null;
    let meta=`Ultimo: ${P.periodos_short[last]}`;
    if(pv!==null&&pv!==0){const d=((lv-pv)/Math.abs(pv))*100;const dc=inv?(d>=0?"delta-neg":"delta-pos"):(d>=0?"delta-pos":"delta-neg");meta=`<span class="${dc}">${d>=0?"▲":"▼"} ${Math.abs(d).toFixed(1).replace('.',',')}%</span> vs ${P.periodos_short[prev]}`;}
    return `<div class="kpi-card"><div class="kpi-label">${lab}</div><div class="kpi-value">${fmt(lv)}</div><div class="kpi-meta">${meta}</div></div>`;
  }).join("");
}
function erCharts(periodo){
  const m=ER[periodo];const labels=m.obras_sociales.map(o=>o.code);const colors=labels.map(l=>OS_COLOR[l]||"#999");
  destroyChart("share");
  charts.share=new Chart(document.getElementById("chartShare"),{type:"doughnut",data:{labels,datasets:[{data:m.obras_sociales.map(o=>o.income_share*100),backgroundColor:colors,borderWidth:2,borderColor:"#fff"}]},options:{responsive:true,maintainAspectRatio:false,cutout:"58%",plugins:{legend:{position:"right",labels:{boxWidth:12,font:{size:11}}},tooltip:{callbacks:{label:c=>`${c.label}: ${c.raw.toFixed(1)}%`}}}}});
  destroyChart("result");
  const rdata=m.obras_sociales.map(o=>o.resultado_neto);
  charts.result=new Chart(document.getElementById("chartResult"),{type:"bar",data:{labels,datasets:[{data:rdata,backgroundColor:rdata.map(v=>v>=0?"#0A1F8C":"#E74C3C"),borderRadius:6}]},options:{responsive:true,maintainAspectRatio:false,plugins:{legend:{display:false},tooltip:{callbacks:{label:c=>fmtMoneyShort(c.raw)}}},scales:{y:{ticks:{callback:v=>fmtMoneyShort(v),font:{size:10}},grid:{color:"#EEF2FB"}},x:{grid:{display:false}}}}});
  const prestPct=m.obras_sociales.map(o=>o.ingresos_netos?(o.costos_prestacionales/o.ingresos_netos)*100:0);
  const fijoPct=m.obras_sociales.map(o=>o.ingresos_netos?(o.costos_fijos/o.ingresos_netos)*100:0);
  const taxPct=m.obras_sociales.map(o=>o.ingresos_netos?(o.impuestos/o.ingresos_netos)*100:0);
  const margPct=m.obras_sociales.map(o=>o.margen*100);
  destroyChart("structure");
  charts.structure=new Chart(document.getElementById("chartStructure"),{type:"bar",data:{labels,datasets:[{label:"Costos Prestacionales",data:prestPct,backgroundColor:"#F2B705"},{label:"Costos Fijos",data:fijoPct,backgroundColor:"#7A52F4"},{label:"Impuestos",data:taxPct,backgroundColor:"#E74C3C"},{label:"Margen",data:margPct,backgroundColor:"#0E9F6E"}]},options:{responsive:true,maintainAspectRatio:false,plugins:{legend:{position:"top",labels:{font:{size:11},boxWidth:12}},tooltip:{callbacks:{label:c=>`${c.dataset.label}: ${c.raw.toFixed(1).replace('.',',')}%`}}},scales:{x:{stacked:true,grid:{display:false}},y:{stacked:true,ticks:{callback:v=>v+"%",font:{size:10}},grid:{color:"#EEF2FB"}}}}});
  destroyChart("costs");
  charts.costs=new Chart(document.getElementById("chartCosts"),{type:"bar",data:{labels,datasets:[{label:"% Costos Prestacionales",data:prestPct,backgroundColor:"#0BC8FA"},{label:"% Costos Fijos",data:fijoPct,backgroundColor:"#0A1F8C"}]},options:{responsive:true,maintainAspectRatio:false,plugins:{legend:{position:"top",labels:{font:{size:11},boxWidth:12}},tooltip:{callbacks:{label:c=>`${c.dataset.label}: ${c.raw.toFixed(1).replace('.',',')}%`}}},scales:{y:{ticks:{callback:v=>v+"%",font:{size:10}},grid:{color:"#EEF2FB"}},x:{grid:{display:false}}}}});
}
function erRanking(periodo){
  const m=ER[periodo];const sorted=[...m.obras_sociales].sort((a,b)=>b.resultado_neto-a.resultado_neto);
  document.getElementById("er-ranking").innerHTML=sorted.map((o,i)=>{
    const mc=o.margen>=0?"pill-pos":"pill-neg";const sw=(o.income_share*100).toFixed(1);
    return `<tr><td><strong>${i+1}</strong></td><td><span class="os-tag" style="background:${OS_COLOR[o.code]}22;color:${OS_COLOR[o.code]}">${o.code}</span></td><td class="right">${fmtMoneyShort(o.ingresos_netos)}</td><td class="right"><span class="bar-mini" style="width:${sw*0.7}px"></span>${sw}%</td><td class="right">${fmtMoneyShort(o.costos_prestacionales)}</td><td class="right">${fmtMoneyShort(o.costos_fijos)}</td><td class="right">${fmtMoneyShort(o.impuestos)}</td><td class="right"><strong>${fmtMoneyShort(o.resultado_neto)}</strong></td><td class="right"><span class="${mc}">${fmtPct(o.margen)}</span></td></tr>`;
  }).join("");
}
function erOsCards(periodo){
  const m=ER[periodo];
  document.getElementById("er-os-cards").innerHTML=m.obras_sociales.map(o=>{
    const rc=o.resultado_neto>=0?"pill-pos":"pill-neg";
    return `<div class="os-card"><div class="os-card-header"><div><div class="os-name">${o.code}</div><div style="font-size:11px;color:var(--muted);margin-top:2px">${o.afiliados>0?fmtNum(o.afiliados)+" afiliados":"Sin capita"}</div></div><div class="os-share">${(o.income_share*100).toFixed(1)}% ing.</div></div>
    <div class="os-row"><span class="lbl">Capita unit.</span><span class="val">${o.capita_unit>0?"$ "+fmtNum(Math.round(o.capita_unit)):"-"}</span></div>
    <div class="os-row"><span class="lbl">Subtotal capita</span><span class="val">${fmtMoneyShort(o.subtotal_capita)}</span></div>
    <div class="os-row"><span class="lbl">Ingresos extras</span><span class="val">${fmtMoneyShort(o.ingresos_extras)}</span></div>
    ${o.refuerzo_capita?`<div class="os-row"><span class="lbl">Refuerzo</span><span class="val">${fmtMoneyShort(o.refuerzo_capita)}</span></div>`:''}
    ${o.notas_credito?`<div class="os-row"><span class="lbl">Notas C/D</span><span class="val">${fmtMoneyShort(o.notas_credito)}</span></div>`:''}
    <div class="os-row divider"><span class="lbl"><strong>Ingresos netos</strong></span><span class="val">${fmtMoneyShort(o.ingresos_netos)}</span></div>
    <div class="os-row"><span class="lbl">- Costos prestac.</span><span class="val" style="color:var(--red)">${fmtMoneyShort(-o.costos_prestacionales)}</span></div>
    <div class="os-row"><span class="lbl">- Costos fijos</span><span class="val" style="color:var(--red)">${fmtMoneyShort(-o.costos_fijos)}</span></div>
    <div class="os-row"><span class="lbl">= Resultado antes imp.</span><span class="val" style="font-weight:700">${fmtMoneyShort(o.resultado_antes)}</span></div>
    <div class="os-row tax"><span class="lbl">- Impuestos</span><span class="val">${fmtMoneyShort(-o.impuestos)}</span></div>
    <div class="os-row result"><span class="lbl">Resultado Neto</span><span class="${rc}">${fmtMoneyShort(o.resultado_neto)} - ${fmtPct(o.margen)}</span></div></div>`;
  }).join("");
}
function erOspif(periodo){
  const m=ER[periodo];const subs=m.ospif_breakdown||[];
  if(!subs.length){document.getElementById("ospif-table").innerHTML="<tbody><tr><td style='padding:14px;color:var(--muted)'>Sin detalle de sub-segmentos para este mes.</td></tr></tbody>";return;}
  let h="<thead><tr><th>Sub-segmento</th><th class='right'>Afiliados</th><th class='right'>Capita unit.</th><th class='right'>Ingresos netos</th></tr></thead><tbody>";
  subs.forEach(s=>{const lbl=s.label.replace("BahBlanca","Bahia Blanca").replace("SantaFe","Santa Fe");h+=`<tr><td><span class="os-tag" style="background:#0BC8FA22;color:#0A1F8C">OSPIF - ${lbl}</span></td><td class="right">${fmtNum(s.afiliados)}</td><td class="right">${s.capita_unit>0?"$ "+fmtNum(Math.round(s.capita_unit)):"-"}</td><td class="right">${fmtMoneyShort(s.ingresos_netos)}</td></tr>`;});
  document.getElementById("ospif-table").innerHTML=h+"</tbody>";
}
function erTrends(){
  const labels=PERIODOS.map(p=>P.periodos_short[p]);
  destroyChart("trendMain");
  charts.trendMain=new Chart(document.getElementById("trendMain"),{type:"bar",data:{labels,datasets:[{label:"Ingresos Netos",data:PERIODOS.map(p=>ER[p].totals.ingresos_netos),backgroundColor:"#0BC8FA"},{label:"Costos Prestac.",data:PERIODOS.map(p=>ER[p].totals.costos_prestacionales),backgroundColor:"#F2B705"},{label:"Costos Fijos",data:PERIODOS.map(p=>ER[p].totals.costos_fijos),backgroundColor:"#7A52F4"},{type:"line",label:"Resultado Neto",data:PERIODOS.map(p=>ER[p].totals.resultado_neto),borderColor:"#0E9F6E",backgroundColor:"#0E9F6E",borderWidth:3,tension:0.3}]},options:{responsive:true,maintainAspectRatio:false,plugins:{legend:{position:"top",labels:{font:{size:11},boxWidth:12}},tooltip:{callbacks:{label:c=>`${c.dataset.label}: ${fmtMoneyShort(c.raw)}`}}},scales:{y:{ticks:{callback:v=>fmtMoneyShort(v),font:{size:10}},grid:{color:"#EEF2FB"}},x:{grid:{display:false}}}}});
  destroyChart("trendMargen");
  charts.trendMargen=new Chart(document.getElementById("trendMargen"),{type:"line",data:{labels,datasets:[{label:"Margen Neto %",data:PERIODOS.map(p=>ER[p].totals.margen*100),borderColor:"#0A1F8C",backgroundColor:"rgba(11,200,250,0.15)",borderWidth:3,fill:true,tension:0.3}]},options:{responsive:true,maintainAspectRatio:false,plugins:{legend:{display:false},tooltip:{callbacks:{label:c=>c.raw.toFixed(1).replace('.',',')+"%"}}},scales:{y:{ticks:{callback:v=>v+"%",font:{size:10}},grid:{color:"#EEF2FB"}},x:{grid:{display:false}}}}});
  const osList=ER[PERIODOS[0]].obras_sociales.map(o=>o.code);
  destroyChart("trendOs");
  charts.trendOs=new Chart(document.getElementById("trendOs"),{type:"line",data:{labels,datasets:osList.map(code=>({label:code,data:PERIODOS.map(p=>{const o=ER[p].obras_sociales.find(x=>x.code===code);return o?o.resultado_neto:0;}),borderColor:OS_COLOR[code],backgroundColor:OS_COLOR[code],borderWidth:2,tension:0.3}))},options:{responsive:true,maintainAspectRatio:false,plugins:{legend:{position:"top",labels:{font:{size:11},boxWidth:12}},tooltip:{callbacks:{label:c=>`${c.dataset.label}: ${fmtMoneyShort(c.raw)}`}}},scales:{y:{ticks:{callback:v=>fmtMoneyShort(v),font:{size:10}},grid:{color:"#EEF2FB"}},x:{grid:{display:false}}}}});
}
function erCmpTable(){
  const rows=[["Afiliados","afiliados",fmtNum],["Ingresos Netos","ingresos_netos",fmtMoneyShort],["Ingresos Extras","ingresos_extras",fmtMoneyShort],["Costos Prestacionales","costos_prestacionales",fmtMoneyShort],["Costos Fijos","costos_fijos",fmtMoneyShort],["Resultado Antes Imp.","resultado_antes",fmtMoneyShort],["Impuestos","impuestos",fmtMoneyShort],["Resultado Neto","resultado_neto",fmtMoneyShort],["Margen Neto","margen",fmtPct]];
  let h="<thead><tr><th>Concepto</th>"+PERIODOS.map(p=>`<th class="right">${P.periodos_label[p]}</th>`).join("")+"</tr></thead><tbody>";
  rows.forEach(([lab,k,fmt])=>{h+=`<tr><td class="metric">${lab}</td>`+PERIODOS.map(p=>`<td class="right">${fmt(ER[p].totals[k])}</td>`).join("")+"</tr>";});
  document.getElementById("er-cmp-table").innerHTML=h+"</tbody>";
}

// ===== COSTOS PRESTACIONALES =====
function cpKpisSingle(periodo){
  const t=CP[periodo].totals;
  document.getElementById("cp-kpis").innerHTML=`
  <div class="kpi-card primary"><div class="kpi-label">Total a Pagar</div><div class="kpi-value">${fmtMoneyShort(t.ap_total)}</div><div class="kpi-meta">Costos prestacionales del mes</div></div>
  <div class="kpi-card"><div class="kpi-label">Total Facturado</div><div class="kpi-value">${fmtMoneyShort(t.ft_total)}</div><div class="kpi-meta">Antes de debitos</div></div>
  <div class="kpi-card warn"><div class="kpi-label">Debitos Total</div><div class="kpi-value">${fmtMoneyShort(t.da_total+t.dm_total)}</div><div class="kpi-meta">${fmtPct((t.da_total+t.dm_total)/t.ft_total)} sobre facturado</div></div>
  <div class="kpi-card"><div class="kpi-label"># Facturas</div><div class="kpi-value">${fmtNum(t.n_facturas)}</div><div class="kpi-meta">${fmtNum(t.n_prestadores)} prestadores</div></div>
  <div class="kpi-card purple"><div class="kpi-label">Factura Promedio</div><div class="kpi-value">${fmtMoneyShort(t.factura_promedio)}</div><div class="kpi-meta">A pagar / # facturas</div></div>`;
}
function cpKpisCompare(){
  const last=PERIODOS[PERIODOS.length-1],prev=PERIODOS.length>1?PERIODOS[PERIODOS.length-2]:null;
  const lt=CP[last].totals,pt=prev?CP[prev].totals:null;
  const kpis=[["Total a Pagar","ap_total",fmtMoneyShort],["Total Facturado","ft_total",fmtMoneyShort],["# Facturas","n_facturas",fmtNum],["# Prestadores","n_prestadores",fmtNum],["Factura Promedio","factura_promedio",fmtMoneyShort]];
  document.getElementById("cp-kpis").innerHTML=kpis.map(([lab,k,fmt])=>{
    const lv=lt[k],pv=pt?pt[k]:null;let meta=`Ultimo: ${P.periodos_short[last]}`;
    if(pv!==null&&pv!==0){const d=((lv-pv)/Math.abs(pv))*100;const dc=d>=0?"delta-pos":"delta-neg";meta=`<span class="${dc}">${d>=0?"▲":"▼"} ${Math.abs(d).toFixed(1).replace('.',',')}%</span> vs ${P.periodos_short[prev]}`;}
    return `<div class="kpi-card"><div class="kpi-label">${lab}</div><div class="kpi-value">${fmt(lv)}</div><div class="kpi-meta">${meta}</div></div>`;
  }).join("");
}
function cpCharts(periodo){
  const m=CP[periodo];const cats=m.categorias;
  destroyChart("cpCat");
  charts.cpCat=new Chart(document.getElementById("cpChartCat"),{type:"doughnut",data:{labels:cats.map(c=>c.cat),datasets:[{data:cats.map(c=>c.ap),backgroundColor:cats.map(c=>CAT_COLOR[c.cat]||"#999"),borderWidth:2,borderColor:"#fff"}]},options:{responsive:true,maintainAspectRatio:false,cutout:"58%",plugins:{legend:{position:"right",labels:{boxWidth:12,font:{size:11}}},tooltip:{callbacks:{label:c=>`${c.label}: ${fmtMoneyShort(c.raw)}`}}}}});
  const oss=m.obras_sociales;
  destroyChart("cpOs");
  charts.cpOs=new Chart(document.getElementById("cpChartOs"),{type:"doughnut",data:{labels:oss.map(o=>o.os),datasets:[{data:oss.map(o=>o.ap),backgroundColor:oss.map(o=>OS_COLOR[o.os]||"#999"),borderWidth:2,borderColor:"#fff"}]},options:{responsive:true,maintainAspectRatio:false,cutout:"58%",plugins:{legend:{position:"right",labels:{boxWidth:12,font:{size:11}}},tooltip:{callbacks:{label:c=>`${c.label}: ${fmtMoneyShort(c.raw)}`}}}}});
}
function cpHeatmap(periodo){
  const m=CP[periodo];const cats=m.categorias.map(c=>c.cat);const oss=m.obras_sociales.map(o=>o.os);
  let maxV=0;cats.forEach(c=>oss.forEach(o=>{const v=(m.heatmap[c]||{})[o]||0;if(v>maxV)maxV=v;}));
  const colorFor=v=>{if(!v)return null;const r=v/maxV;return `hsl(${220-r*30}, 75%, ${75-r*40}%)`;};
  let h=`<thead><tr><th style="text-align:left">Categoria</th>${oss.map(o=>`<th>${o}</th>`).join('')}<th>Total</th></tr></thead><tbody>`;
  cats.forEach(c=>{let tot=0;h+=`<tr><td class="label">${c}</td>`;oss.forEach(o=>{const v=(m.heatmap[c]||{})[o]||0;tot+=v;h+=v?`<td style="background:${colorFor(v)}" title="${fmtMoneyFull(v)}">${fmtMoneyShort(v)}</td>`:`<td class="empty">-</td>`;});h+=`<td style="background:#0A1F8C" title="${fmtMoneyFull(tot)}">${fmtMoneyShort(tot)}</td></tr>`;});
  h+=`<tr><td class="label" style="background:#EEF2FB">TOTAL</td>`;let grand=0;
  oss.forEach(o=>{const ct=cats.reduce((s,c)=>s+((m.heatmap[c]||{})[o]||0),0);grand+=ct;h+=`<td style="background:#0A1F8C" title="${fmtMoneyFull(ct)}">${fmtMoneyShort(ct)}</td>`;});
  h+=`<td style="background:#06146A" title="${fmtMoneyFull(grand)}">${fmtMoneyShort(grand)}</td></tr></tbody>`;
  document.getElementById("cp-heatmap").innerHTML=h;
}
function cpTop(periodo){
  const m=CP[periodo];const top=m.prestadores.slice(0,20);const total=m.totals.ap_total;
  document.getElementById("cp-top").innerHTML=top.map((p,i)=>{
    const pct=p.ap/total*100;
    const tags=p.os.map(o=>`<span class="os-tag" style="background:${OS_COLOR[o]||"#999"}22;color:${OS_COLOR[o]||"#666"};margin-right:3px">${o}</span>`).join('');
    return `<tr><td><strong>${i+1}</strong></td><td style="font-weight:600">${p.p}</td><td class="right">${p.facturas}</td><td class="right">${fmtMoneyShort(p.ft)}</td><td class="right">${p.deb_pct.toFixed(1).replace('.',',')}%</td><td class="right"><strong>${fmtMoneyShort(p.ap)}</strong></td><td class="right"><span class="bar-mini" style="width:${pct*2.5}px"></span>${pct.toFixed(1).replace('.',',')}%</td><td>${tags}</td></tr>`;
  }).join("");
}
function cpPlazos(periodo){
  const m=CP[periodo];const p=m.plazos;
  if(!p){document.getElementById("cp-plazos").innerHTML="<p style='color:var(--muted)'>Sin datos de plazo en este mes.</p>";return;}
  document.getElementById("cp-plazos").innerHTML=`<div class="kpi-grid">
  <div class="kpi-card primary"><div class="kpi-label">Plazo Promedio</div><div class="kpi-value">${p.avg.toFixed(1).replace('.',',')} dias</div><div class="kpi-meta">Periodo prestacion -> fecha pago</div></div>
  <div class="kpi-card"><div class="kpi-label">Minimo</div><div class="kpi-value">${p.min} dias</div><div class="kpi-meta">Pago mas rapido</div></div>
  <div class="kpi-card warn"><div class="kpi-label">Maximo</div><div class="kpi-value">${p.max} dias</div><div class="kpi-meta">Pago mas demorado</div></div>
  <div class="kpi-card"><div class="kpi-label">Cubierto</div><div class="kpi-value">${p.n} de ${m.totals.n_facturas}</div><div class="kpi-meta">${p.sin_periodo} sin periodo cargado</div></div></div>`;
}
function cpInvoiceFilters(periodo){
  const m=CP[periodo];
  const oss=[...new Set(m.invoices.map(i=>i.os))].sort();
  const cats=[...new Set(m.invoices.map(i=>i.cat))].sort();
  document.getElementById("cp-filter-os").innerHTML=`<option value="">Todas las OS</option>`+oss.map(o=>`<option value="${o}">${o}</option>`).join('');
  document.getElementById("cp-filter-cat").innerHTML=`<option value="">Todas las categorias</option>`+cats.map(c=>`<option value="${c}">${c}</option>`).join('');
}
function cpInvoiceTable(periodo){
  const m=CP[periodo];
  const s=(document.getElementById("cp-search").value||"").toLowerCase();
  const fo=document.getElementById("cp-filter-os").value;
  const fc=document.getElementById("cp-filter-cat").value;
  const filt=m.invoices.filter(i=>{if(fo&&i.os!==fo)return false;if(fc&&i.cat!==fc)return false;if(s&&!(`${i.p} ${i.f}`.toLowerCase().includes(s)))return false;return true;});
  document.getElementById("cp-inv-count").textContent=`- ${filt.length} de ${m.invoices.length} facturas`;
  document.getElementById("cp-inv-body").innerHTML=filt.slice(0,500).map(i=>{const dt=i.da+i.dm;return `<tr><td style="font-weight:600">${i.p}</td><td>${i.f}</td><td>${i.fp||"-"}</td><td>${i.pe||"-"}</td><td><span class="cat-tag" style="background:${(CAT_COLOR[i.cat]||"#999")}22;color:${CAT_COLOR[i.cat]||"#666"}">${i.cat}</span></td><td><span class="os-tag" style="background:${OS_COLOR[i.os]||"#999"}22;color:${OS_COLOR[i.os]||"#666"}">${i.os||"-"}</span></td><td class="right">${i.plr!==null?i.plr+"d":"-"}</td><td class="right">${fmtMoneyShort(i.ft)}</td><td class="right">${dt>0?fmtMoneyShort(dt):"-"}</td><td class="right"><strong>${fmtMoneyShort(i.ap)}</strong></td></tr>`;}).join("");
}
function cpTrends(){
  const labels=PERIODOS.map(p=>P.periodos_short[p]);
  destroyChart("cpTrendTotal");
  charts.cpTrendTotal=new Chart(document.getElementById("cpTrendTotal"),{type:"bar",data:{labels,datasets:[{label:"Total a Pagar",data:PERIODOS.map(p=>CP[p].totals.ap_total),backgroundColor:"#0A1F8C",borderRadius:6}]},options:{responsive:true,maintainAspectRatio:false,plugins:{legend:{display:false},tooltip:{callbacks:{label:c=>fmtMoneyShort(c.raw)}}},scales:{y:{ticks:{callback:v=>fmtMoneyShort(v),font:{size:10}},grid:{color:"#EEF2FB"}},x:{grid:{display:false}}}}});
  destroyChart("cpTrendDeb");
  charts.cpTrendDeb=new Chart(document.getElementById("cpTrendDeb"),{type:"line",data:{labels,datasets:[{label:"Debitos %",data:PERIODOS.map(p=>{const t=CP[p].totals;return t.ft_total?((t.da_total+t.dm_total)/t.ft_total)*100:0;}),borderColor:"#F2B705",backgroundColor:"rgba(242,183,5,0.15)",borderWidth:3,fill:true,tension:0.3}]},options:{responsive:true,maintainAspectRatio:false,plugins:{legend:{display:false},tooltip:{callbacks:{label:c=>c.raw.toFixed(1).replace('.',',')+"%"}}},scales:{y:{ticks:{callback:v=>v+"%",font:{size:10}},grid:{color:"#EEF2FB"}},x:{grid:{display:false}}}}});
}
function cpCmpTable(){
  const rows=[["Total a Pagar","ap_total",fmtMoneyShort],["Total Facturado","ft_total",fmtMoneyShort],["Debitos Adm.","da_total",fmtMoneyShort],["Debitos Med.","dm_total",fmtMoneyShort],["# Facturas","n_facturas",fmtNum],["# Prestadores","n_prestadores",fmtNum],["Factura Promedio","factura_promedio",fmtMoneyShort]];
  let h="<thead><tr><th>Concepto</th>"+PERIODOS.map(p=>`<th class="right">${P.periodos_label[p]}</th>`).join("")+"</tr></thead><tbody>";
  rows.forEach(([lab,k,fmt])=>{h+=`<tr><td class="metric">${lab}</td>`+PERIODOS.map(p=>`<td class="right">${CP[p]?fmt(CP[p].totals[k]):"-"}</td>`).join("")+"</tr>";});
  document.getElementById("cp-cmp-table").innerHTML=h+"</tbody>";
}

// ===== ORCHESTRATION =====
function setTab(tab){
  currentTab=tab;
  document.querySelectorAll(".main-tab").forEach(b=>b.classList.toggle("active",b.dataset.tab===tab));
  document.querySelectorAll(".tab-content").forEach(el=>el.classList.toggle("active",el.id===`tab-${tab}`));
  document.getElementById("page-title").textContent=tab==="estado"?"Estado de Resultado":"Costos Prestacionales";
  render();
}
function setView(view){
  currentView=view;
  document.querySelectorAll(".period-btn").forEach(b=>b.classList.toggle("active",b.dataset.view===view));
  render();
}
function render(){
  const isCompare=currentView==="compare";
  const lbl=isCompare?"- Comparativo ("+PERIODOS.length+" meses)":"- "+(P.periodos_label[currentView]||"");
  document.getElementById("er-period-label").textContent=lbl;
  document.getElementById("cp-period-label").textContent=lbl;
  if(currentTab==="estado"){
    document.getElementById("er-single").style.display=isCompare?"none":"block";
    document.getElementById("er-compare").style.display=isCompare?"block":"none";
    if(isCompare){erKpisCompare();erTrends();erCmpTable();}
    else{const pv=ER[currentView]?currentView:PERIODOS[PERIODOS.length-1];erKpisSingle(pv);erCharts(pv);erRanking(pv);erOsCards(pv);erOspif(pv);}
  } else {
    document.getElementById("cp-single").style.display=isCompare?"none":"block";
    document.getElementById("cp-compare").style.display=isCompare?"block":"none";
    if(isCompare){cpKpisCompare();cpTrends();cpCmpTable();}
    else{
      const pv=CP[currentView]?currentView:PERIODOS[PERIODOS.length-1];
      if(!CP[pv]){document.getElementById("cp-kpis").innerHTML="<p style='color:var(--muted);padding:14px'>No hay planilla de costos prestacionales cargada para este mes.</p>";document.getElementById("cp-single").style.display="none";return;}
      cpKpisSingle(pv);cpCharts(pv);cpHeatmap(pv);cpTop(pv);cpPlazos(pv);cpInvoiceFilters(pv);cpInvoiceTable(pv);
    }
  }
}

document.querySelectorAll(".main-tab").forEach(b=>b.addEventListener("click",()=>setTab(b.dataset.tab)));
document.getElementById("cp-search").addEventListener("input",()=>{if(CP[currentView])cpInvoiceTable(currentView);});
document.getElementById("cp-filter-os").addEventListener("change",()=>{if(CP[currentView])cpInvoiceTable(currentView);});
document.getElementById("cp-filter-cat").addEventListener("change",()=>{if(CP[currentView])cpInvoiceTable(currentView);});
document.getElementById("cp-clear").addEventListener("click",()=>{document.getElementById("cp-search").value="";document.getElementById("cp-filter-os").value="";document.getElementById("cp-filter-cat").value="";if(CP[currentView])cpInvoiceTable(currentView);});

document.getElementById("foot-info").textContent=`${INFO.er_ok||0} meses de Estado de Resultado, ${INFO.cp_ok||0} de Costos Prestacionales`;
buildPeriodButtons();
setView(currentView);
</script>
</body>
</html>"""
