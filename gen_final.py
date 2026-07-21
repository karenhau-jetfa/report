import json, re

with open('years_data_v8.json') as f:
    ALL_DATA = json.load(f)
with open('tipo_codes.json') as f:
    TIPO_CODES = json.load(f)

COLOR_MAP = {
    # Paleta validada: las 36 parejas del conjunto superan los umbrales de separacion
    # (normal>=15, deuteranopia>=8, protanopia>=8) y todas contrastan con el fondo crema.
    # Los 7 tonos cromaticos van a las 7 empresas que reaparecen en el top-6 de algun anio,
    # asi el color sigue a la entidad y no al puesto: cambiar de anio no repinta a nadie.
    "Ling Long":"#2a78d6",                      # azul de marca, fijo
    "Auto Centro S.A.":"#9c470d",               # oxido
    "Central Lubricantes S.A.":"#319d64",       # verde
    "Tambor S.A.":"#edb154",                    # ambar
    "Dist. Rali S.A.":"#834791",                # violeta
    "Prod. Superiores S.A.":"#cd76b1",          # rosa
    "Multi Serv. American Wheels":"#38d2f3",    # cian
    # Segunda linea: comparten un solo tono. No caben mas colores separables junto a los
    # 7 anteriores (medido: con 2 neutros el conjunto puntua 1.13; con 3 cae a 0.83).
    # Como la grafica mensual solo muestra 6 series, rara vez coinciden dos de estos.
    "Dipsa S.A.":"#40242d","Grupo Daher S.A.":"#40242d",
    "King Wong S.A.":"#40242d","Durallanta S.A.":"#40242d",
    "Feng Di Zhuo Chong":"#40242d","Dk Tires, S.A.":"#40242d",
    "Cia. Chiricana de Automoviles":"#40242d","General Life Panama S.A.":"#40242d",
    "DK Speed S.A.":"#40242d","Reconstructora en Frio S.A.":"#40242d",
    "Auto Ser. 88 Internacional":"#40242d","Kenbroth Corp.":"#40242d",
    "Movilidad Internacional S.A.":"#40242d","PriceSmart Panama S.A.":"#40242d",
    "Montacargas y Repuestos S.A.":"#40242d","Panama Forklift Co. Inc.":"#40242d",
    "Montacargas Serv Iman S.A.":"#40242d","Ginsa Motors S.A.":"#40242d",
    "Empresas Melo S.A.":"#40242d","Minera Panama S.A.":"#40242d",
    "Matco Internacional S.A.":"#40242d","Grupo Hongfa S.A.":"#40242d",
    "Motor Group Latam S.A.":"#40242d","Benserca 18 S.A.":"#40242d",
    "Forkliftec Parts S.A.":"#40242d",
    "Otros":"#385e56",                          # agregado del resto
}

# Escape for safe embedding
data_js   = json.dumps(ALL_DATA,   ensure_ascii=False)
color_js  = json.dumps(COLOR_MAP,  ensure_ascii=False)
tcodes_js = json.dumps(TIPO_CODES, ensure_ascii=False)

# Build HTML as string concatenation to avoid f-string brace issues
parts = []
parts.append('''<!DOCTYPE html>
<html lang="es">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width,initial-scale=1.0">
<title>Analisis de Mercado — Neumaticos Panama 2019-2026</title>
<script src="https://cdnjs.cloudflare.com/ajax/libs/Chart.js/4.4.1/chart.umd.js"></script>
<style>
*{box-sizing:border-box;margin:0;padding:0}
body{font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',Arial,sans-serif;background:#f4f3f0;color:#0b0b0b;font-size:14px;line-height:1.6}
.page{max-width:1100px;margin:0 auto;padding:40px 32px}
.header{margin-bottom:36px;border-bottom:1px solid #d3d1c7;padding-bottom:22px}
.header-top{display:flex;justify-content:space-between;align-items:flex-start}
.brand-name{font-size:15px;font-weight:600;color:#2a78d6}
.brand-sub{font-size:12px;color:#888780;margin-top:2px}
.report-meta{text-align:right;font-size:12px;color:#888780}
h1{font-size:26px;font-weight:700;margin-top:18px;color:#0b0b0b;letter-spacing:-0.3px}
.subtitle{font-size:12px;color:#888780;margin-top:6px}
.year-selector{display:flex;gap:6px;margin-top:16px}
.year-btn{padding:6px 18px;border-radius:20px;border:1.5px solid #d3d1c7;background:#fff;color:#52514e;font-size:13px;font-weight:600;cursor:pointer;transition:all .15s}
.year-btn:hover{border-color:#2a78d6;color:#2a78d6}
.year-btn.active{background:#2a78d6;border-color:#2a78d6;color:#fff}
.kpi-row{display:grid;grid-template-columns:repeat(4,1fr);gap:12px;margin-bottom:32px}
.kpi{background:#fff;border-radius:10px;border:0.5px solid #d3d1c7;padding:16px 18px}
.kpi-label{font-size:11px;color:#888780;text-transform:uppercase;letter-spacing:0.5px;margin-bottom:6px}
.kpi-value{font-size:24px;font-weight:700;line-height:1}
.kpi-value.blue{color:#2a78d6}
.delta{display:inline-flex;align-items:center;gap:3px;font-size:11px;font-weight:600;font-variant-numeric:tabular-nums;margin-top:5px}
.delta.up{color:#0d7a52}
.delta.down{color:#b8322f}
.delta.flat{color:#888780}
.delta.block{display:flex;margin-top:3px}
.delta-ctx{font-size:10px;color:#b4b2a9;font-weight:400;margin-top:1px;white-space:nowrap}
td .delta{margin-top:0}
.cmp-banner{margin-top:10px;padding:8px 14px;border-radius:8px;font-size:12px;background:#e6f1fb;border:1px solid #a9cdf0;color:#185fa5}
.kpi-sub{font-size:11px;color:#888780;margin-top:5px}
.badge{display:inline-block;background:#e6f1fb;color:#185fa5;font-size:10px;font-weight:600;padding:2px 8px;border-radius:20px;margin-top:5px}
.badge-code{display:inline-block;background:#f4f3f0;color:#52514e;font-size:9px;font-weight:600;padding:1px 6px;border-radius:4px;font-family:monospace;letter-spacing:0.3px}
.section{background:#fff;border-radius:12px;border:0.5px solid #d3d1c7;padding:26px 26px 22px;margin-bottom:24px}
.section-title{font-size:15px;font-weight:700;margin-bottom:3px}
.section-desc{font-size:11px;color:#888780;margin-bottom:18px}
.legend{display:flex;flex-wrap:wrap;gap:6px 14px;margin-bottom:14px}
.legend-item{display:flex;align-items:center;gap:5px;font-size:11px;color:#52514e}
.legend-swatch{width:10px;height:10px;border-radius:2px;flex-shrink:0}
.chart-wrap-donut{position:relative;width:100%;height:320px}
.chart-wrap-rank{position:relative;width:100%;height:470px}
.chart-wrap-bar{position:relative;width:100%;height:980px}
.chart-wrap-line{position:relative;width:100%;height:400px}
.insight{background:#e6f1fb;border-left:3px solid #2a78d6;border-radius:0 8px 8px 0;padding:12px 16px;margin-top:16px;font-size:12.5px;line-height:1.6}
.insight strong{color:#185fa5}
.table-wrap{overflow-x:auto;margin-top:12px}
table{width:100%;border-collapse:collapse;font-size:12px}
thead th{background:#f4f3f0;color:#52514e;font-weight:600;padding:8px 12px;text-align:left;border-bottom:1px solid #d3d1c7}
tbody tr:nth-child(even){background:#fafaf8}
tbody td{padding:7px 12px;border-bottom:0.5px solid #e1e0d9}
tbody tr.ling-long td{font-weight:700;color:#185fa5;background:#edf4fc}
.bar-bg{height:7px;background:#e1e0d9;border-radius:4px;overflow:hidden;width:110px}
.bar-fill{height:100%;border-radius:4px}
.footer{margin-top:32px;padding-top:16px;border-top:0.5px solid #d3d1c7;display:flex;justify-content:space-between}
.filter-tab{padding:6px 16px;border-radius:20px;border:1.5px solid #d3d1c7;background:#fff;color:#52514e;font-size:12px;font-weight:600;cursor:pointer;transition:all .15s}
.filter-tab:hover{border-color:#2a78d6;color:#2a78d6}
.filter-tab.active{background:#2a78d6;border-color:#2a78d6;color:#fff}
.filter-select{padding:7px 12px;border-radius:8px;border:1.5px solid #d3d1c7;font-size:13px;color:#0b0b0b;background:#fff;min-width:260px;cursor:pointer}
.profile-kpi{display:grid;grid-template-columns:repeat(3,1fr);gap:10px;margin:14px 0}
.profile-chart-row{display:grid;grid-template-columns:1fr 1fr;gap:20px;margin-top:14px}
.footer p{font-size:11px;color:#b4b2a9}
.seg-card{background:#fff;border-radius:10px;border:0.5px solid #d3d1c7;padding:14px 16px}

/* --- Herramientas de tabla ---------------------------------------------- */
.tbl-tools{display:flex;gap:8px;align-items:center;justify-content:flex-end;margin:12px 0 0;flex-wrap:wrap}
.tbl-search{flex:0 1 200px;padding:5px 10px;border:1px solid #d3d1c7;border-radius:7px;
  font-size:12px;color:#0b0b0b;background:#fff;font-family:inherit}
.tbl-search:focus{outline:2px solid #2a78d6;outline-offset:1px;border-color:#2a78d6}
.tbl-csv{padding:5px 11px;border:1px solid #d3d1c7;border-radius:7px;background:#fff;
  color:#52514e;font-size:11.5px;font-weight:600;cursor:pointer;font-family:inherit;
  transition:border-color .15s,color .15s}
.tbl-csv:hover{border-color:#2a78d6;color:#2a78d6}
table[data-tools*="sort"] thead th{cursor:pointer;user-select:none;position:relative;padding-right:18px!important}
table[data-tools*="sort"] thead th:hover{color:#2a78d6}
table[data-tools*="sort"] thead th::after{content:"\2195";position:absolute;right:6px;opacity:.25;font-size:10px}
th.sorted-asc::after{content:"\2191";opacity:1;color:#2a78d6}
th.sorted-desc::after{content:"\2193";opacity:1;color:#2a78d6}
@media (max-width:620px){.tbl-tools{justify-content:stretch}.tbl-search{flex:1 1 auto}}

/* --- Navegacion pegajosa ------------------------------------------------ */
html{scroll-behavior:smooth}
.secnav{position:sticky;top:0;z-index:30;margin:0 -32px 24px;padding:0 32px;
  background:rgba(244,243,240,.93);backdrop-filter:saturate(150%) blur(8px);
  border-bottom:1px solid #d3d1c7}
.secnav-inner{display:flex;gap:2px;overflow-x:auto;scrollbar-width:none}
.secnav-inner::-webkit-scrollbar{display:none}
.secnav a{flex:0 0 auto;padding:11px 12px;font-size:12px;font-weight:600;color:#888780;
  text-decoration:none;border-bottom:2px solid transparent;white-space:nowrap;
  transition:color .15s ease,border-color .15s ease}
.secnav a:hover{color:#2a78d6}
.secnav a.active{color:#185fa5;border-bottom-color:#2a78d6}
.section,.kpi-row{scroll-margin-top:64px}

/* --- Contenedores de grafica de altura variable -------------------------- */
.cwrap{position:relative;width:100%;height:var(--h)}
.grid-2{display:grid;grid-template-columns:1fr 1fr;gap:24px}
/* Sin min-width:0 los hijos de una rejilla se niegan a encogerse por debajo de su
   contenido y desbordan la pagina en movil. */
.grid-2>*,.profile-chart-row>*,.kpi-row>*,.profile-kpi>*{min-width:0}
.table-wrap{max-width:100%}
canvas{max-width:100%}

/* --- Estados: antes no habia ni un solo :focus --------------------------- */
a:focus-visible,button:focus-visible,select:focus-visible{outline:2px solid #2a78d6;
  outline-offset:2px;border-radius:6px}
tbody tr:hover td{background:#efeee8}
tbody tr.ling-long:hover td{background:#e2edfb}
.year-btn:active,.filter-tab:active{transform:translateY(1px)}

/* --- Pantallas medianas -------------------------------------------------- */
@media (max-width:900px){
  .page{padding:26px 18px}
  .secnav{margin:0 -18px 20px;padding:0 18px}
  h1{font-size:22px}
  .kpi-row{grid-template-columns:repeat(2,1fr)}
  .grid-2,.profile-chart-row{grid-template-columns:1fr}
  .profile-kpi{grid-template-columns:repeat(2,1fr)}
  .chart-wrap-bar{height:820px}
}

/* --- Telefono ------------------------------------------------------------ */
@media (max-width:620px){
  body{font-size:13px}
  .page{padding:16px 12px}
  .secnav{margin:0 -12px 16px;padding:0 12px}
  .secnav a{padding:10px 9px;font-size:11px}
  .header-top{flex-direction:column;gap:8px}
  .report-meta{text-align:left}
  h1{font-size:20px;line-height:1.25}
  .section{padding:18px 14px 16px;border-radius:10px}
  .kpi-row{grid-template-columns:1fr;gap:10px;margin-bottom:22px}
  .profile-kpi{grid-template-columns:1fr}
  .kpi-value{font-size:22px}
  .year-selector{overflow-x:auto;scrollbar-width:none;padding-bottom:2px}
  .year-selector::-webkit-scrollbar{display:none}
  .year-btn{flex:0 0 auto}
  .cwrap{height:min(var(--h),58vw)}
  .chart-wrap-donut{height:250px}
  .chart-wrap-line{height:280px}
  .chart-wrap-rank{height:400px}
  .chart-wrap-bar{height:560px}
  table{font-size:11px}
  thead th{padding:7px 8px}
  tbody td{padding:6px 8px}
  .table-wrap{-webkit-overflow-scrolling:touch}
  /* La tabla mensual tiene 14 columnas: el nombre queda fijo al hacer scroll */
  #monthly-table th:nth-child(1),#monthly-table td:nth-child(1){position:sticky;left:0;z-index:2;width:20px}
  #monthly-table th:nth-child(2),#monthly-table td:nth-child(2){position:sticky;left:20px;z-index:2;
    min-width:104px;box-shadow:1px 0 0 #e1e0d9}
  #monthly-table thead th:nth-child(-n+2){background:#f4f3f0}
  #monthly-table tbody td:nth-child(-n+2){background:#fff}
  #monthly-table tbody tr:nth-child(even) td:nth-child(-n+2){background:#fafaf8}
  #monthly-table tbody tr.ling-long td:nth-child(-n+2){background:#edf4fc}
  /* La nomenclatura usa columnas fijas de 130px+160px: no caben en un telefono */
  /* Especificidad por id: .sp-row se redefine mas abajo en un <style> local */
  #sec-nomenclatura .sp-row{grid-template-columns:1fr;gap:5px;padding:10px 12px}
  #sec-nomenclatura .sp-pill{justify-self:start}
  .sp-group-lbl{margin-top:16px}
}
@media (prefers-reduced-motion:reduce){
  html{scroll-behavior:auto}
  *{transition-duration:.01ms!important;animation-duration:.01ms!important}
}
@media print{body{background:#fff}.page{padding:20px}.section{break-inside:avoid}.year-selector{display:none}}
</style>
</head>
<body>
<div class="page">
<header class="header">
  <div class="header-top">
    <div><div class="brand-name">Distribuidora Ling Long, S.A.</div><div class="brand-sub">Analisis de Mercado — Uso Interno</div></div>
    <div class="report-meta"><div style="font-weight:600;color:#0b0b0b">Desarrollado por Karen Hau</div><div>Generado el 17 de julio de 2026</div><div>Fuente: Veritrade — Aduana Panama</div></div>
  </div>
  <h1 id="report-title">Mercado de Neumaticos en Panama 2025</h1>
  <p class="subtitle" id="report-subtitle">Partida arancelaria 4011 &middot; Importaciones enero&ndash;diciembre 2025 &middot; Fuente: Veritrade</p>
  <div id="partial-banner" class="cmp-banner" style="display:none"></div>
  <div class="year-selector">
    <button class="year-btn" onclick="switchYear(2019)">2019</button>
    <button class="year-btn" onclick="switchYear(2020)">2020</button>
    <button class="year-btn" onclick="switchYear(2021)">2021</button>
    <button class="year-btn" onclick="switchYear(2022)">2022</button>
    <button class="year-btn" onclick="switchYear(2023)">2023</button>
    <button class="year-btn" onclick="switchYear(2024)">2024</button>
    <button class="year-btn active" onclick="switchYear(2025)">2025</button>
    <button class="year-btn" onclick="switchYear(2026)" style="border-style:dashed">2026 <span style="font-size:10px;font-weight:400">ene&ndash;may</span></button>
  </div>
</header>
<nav class="secnav" id="secnav" aria-label="Secciones del reporte"><div class="secnav-inner"><a href="#sec-mercado">Mercado</a><a href="#sec-importadores">Importadores</a><a href="#sec-mensual">Mensual</a><a href="#sec-exportadores">Exportadores</a><a href="#sec-precios">Precios</a><a href="#sec-segmentos">Segmentos</a><a href="#sec-origenes">Origenes</a><a href="#sec-hk">HK Tiancheng</a><a href="#sec-proveedores">Proveedores LL</a><a href="#sec-posicion">Posicion LL</a><a href="#sec-nomenclatura">Nomenclatura</a></div></nav>
<main id="report-main">
<div class="kpi-row">
  <div class="kpi"><div class="kpi-label">Total mercado</div><div class="kpi-value" id="kpi-total">&#8212;</div><div class="kpi-sub">unidades importadas</div><div id="kpi-total-delta"></div></div>
  <div class="kpi"><div class="kpi-label">Dist. Ling Long</div><div class="kpi-value blue" id="kpi-ll">&#8212;</div><div class="kpi-sub">unidades importadas</div><div class="badge" id="kpi-share">&#8212;</div><div id="kpi-ll-delta"></div></div>
  <div class="kpi"><div class="kpi-label">Posicion en mercado</div><div class="kpi-value blue" id="kpi-rank">&#8212;</div><div class="kpi-sub">de todos los importadores</div><div id="kpi-rank-delta"></div></div>
  <div class="kpi"><div class="kpi-label">Diferencia vs. lider</div><div class="kpi-value" id="kpi-diff">&#8212;</div><div class="kpi-sub" id="kpi-diff-sub">&#8212;</div></div>
</div>
<div class="section" id="filter-section">
  <div class="section-title">Filtros de Analisis</div>
  <div class="section-desc">Selecciona un filtro para explorar el mercado desde una perspectiva especifica.</div>
  <div style="display:flex;gap:8px;flex-wrap:wrap;align-items:center;margin-bottom:14px">
    <button class="filter-tab" id="ftab-imp" onclick="setFilterMode('imp')">Por Importador</button>
    <button class="filter-tab" id="ftab-exp" onclick="setFilterMode('exp')">Por Exportador</button>
    <button class="filter-tab" id="ftab-seg" onclick="setFilterMode('seg')">Por Sub-partida</button>
    <button class="filter-tab" id="ftab-clear" onclick="clearFilterMode()" style="margin-left:auto;border-color:#e34948;color:#e34948">&#10005; Quitar filtro</button>
  </div>
  <div id="filter-controls" style="display:none;margin-bottom:16px">
    <select class="filter-select" id="filter-select" onchange="applyFilter()">
      <option value="">-- Seleccionar --</option>
    </select>
  </div>
  <div id="filter-result" style="display:none">
    <div class="profile-kpi" id="prof-kpis"></div>
    <div class="profile-chart-row">
      <div>
        <p id="prof-bar-label" style="font-size:11px;color:#888780;margin-bottom:6px"></p>
        <div class="cwrap" style="--h:280px"><canvas id="profBarChart"></canvas></div>
      </div>
      <div>
        <p style="font-size:11px;color:#888780;margin-bottom:6px">Distribucion por segmento</p>
        <div class="cwrap" style="--h:280px"><canvas id="profDonutChart"></canvas></div>
      </div>
    </div>
    <div style="margin-top:16px">
      <p style="font-size:11px;color:#888780;margin-bottom:6px">Evolucion mensual de unidades</p>
      <div class="cwrap" style="--h:200px"><canvas id="profLineChart"></canvas></div>
    </div>
    <div class="table-wrap" style="margin-top:14px"><table data-tools="sort,search,csv" data-name="perfil-filtrado"><thead id="prof-thead"></thead><tbody id="prof-tbody"></tbody></table></div>
  </div>
</div>
<div class="section" id="sec-mercado">
  <div class="section-title">Market share por importador</div>
  <div class="section-desc">Top 15 importadores por cantidad de unidades. Distribuidora Ling Long en azul.</div>
  <div class="chart-wrap-rank"><canvas id="pieChart"></canvas></div>
  <div class="insight" id="insight-pie"></div>
</div>
<div class="section" id="sec-importadores">
  <div class="section-title">Ranking de importadores por cantidad</div>
  <div class="section-desc">Top 15 importadores ordenados por volumen. &#9733; = Distribuidora Ling Long.</div>
  <div class="table-wrap"><table data-tools="sort,search,csv" data-name="importadores"><thead><tr><th style="width:36px">#</th><th>Importador</th><th style="text-align:right">Unidades</th><th style="text-align:right" id="imp-th-delta">Variacion</th><th style="text-align:right">Market Share</th><th style="width:130px">Volumen relativo</th></tr></thead><tbody id="imp-table"></tbody></table></div>
</div>
<div class="section" id="sec-mensual">
  <div class="section-title">Evolucion mensual &#8212; Top 10 importadores</div>
  <div class="section-desc">Unidades importadas por mes.</div>
  <div class="legend" id="legend-line"></div>
  <div class="chart-wrap-line"><canvas id="lineChart"></canvas></div>
  <div class="table-wrap" style="margin-top:20px">
    <table id="monthly-table" data-tools="sort,search,csv" data-name="evolucion-mensual"><thead><tr><th>#</th><th>Importador</th><th style="text-align:right">Ene</th><th style="text-align:right">Feb</th><th style="text-align:right">Mar</th><th style="text-align:right">Abr</th><th style="text-align:right">May</th><th style="text-align:right">Jun</th><th style="text-align:right">Jul</th><th style="text-align:right">Ago</th><th style="text-align:right">Sep</th><th style="text-align:right">Oct</th><th style="text-align:right">Nov</th><th style="text-align:right">Dic</th><th style="text-align:right;font-weight:700">Total</th></tr></thead>
    <tbody id="monthly-tbody"></tbody></table>
  </div>
</div>
<div class="section" id="sec-exportadores">
  <div class="section-title">Top 20 exportadores por cantidad de unidades</div>
  <div class="section-desc">Proveedores con mayor volumen de exportacion hacia Panama.</div>
  <div class="chart-wrap-bar"><canvas id="barChart"></canvas></div>
  <div class="table-wrap" style="margin-top:20px"><table data-tools="sort,search,csv" data-name="exportadores"><thead><tr><th>#</th><th>Exportador</th><th style="text-align:right">Unidades</th></tr></thead><tbody id="exp-tbody"></tbody></table></div>
</div>
<div class="section" id="sec-precios">
  <div class="section-title">Evolucion mensual del precio promedio (U$ CIF/unidad)</div>
  <div class="section-desc">Precio promedio por unidad mes a mes &#8212; mercado total vs Distribuidora Ling Long.</div>
  <div class="cwrap" style="--h:320px"><canvas id="priceMonthChart"></canvas></div>
</div>
<div class="section" id="sec-segmentos">
  <div class="section-title">Segmentacion por tipo de neumatico</div>
  <div class="section-desc">Distribucion segun partida arancelaria. Izquierda: por cantidad. Derecha: por valor CIF.</div>
  <div class="grid-2">
    <div><p style="font-size:11px;color:#888780;margin-bottom:8px">Por unidades</p><div class="cwrap" style="--h:280px"><canvas id="tipoQtyChart"></canvas></div></div>
    <div><p style="font-size:11px;color:#888780;margin-bottom:8px">Por valor CIF</p><div class="cwrap" style="--h:280px"><canvas id="tipoCifChart"></canvas></div></div>
  </div>
  <div class="table-wrap" style="margin-top:16px">
    <table data-tools="sort,csv" data-name="segmentos"><thead><tr><th>Segmento</th><th>Codigo arancelario</th><th style="text-align:right">Unidades</th><th style="text-align:right">% Mercado</th><th style="text-align:right">Valor CIF</th><th style="text-align:right">$/ud CIF</th></tr></thead>
    <tbody id="tipo-tbody"></tbody></table>
  </div>
  <div class="insight" id="insight-tipo"></div>
</div>
<div class="section" id="sec-origenes">
  <div class="section-title">Pais de origen</div>
  <div class="section-desc">Principales paises de origen de los neumaticos importados a Panama.</div>
  <div class="cwrap" style="--h:420px"><canvas id="paisChart"></canvas></div>
</div>
<div class="section" id="sec-hk">
  <div class="section-title">Analisis HK Tiancheng &#8212; Clientes en Panama</div>
  <div class="section-desc">Distribucion de las importaciones de HK Tiancheng por empresa compradora.</div>
  <div class="grid-2" style=";align-items:center">
    <div class="cwrap" style="--h:260px"><canvas id="hkChart"></canvas></div>
    <div class="table-wrap"><table data-tools="sort,csv" data-name="hk-tiancheng-clientes"><thead><tr><th>#</th><th>Importador</th><th style="text-align:right">Unidades</th><th style="text-align:right">%</th></tr></thead><tbody id="hk-tbody"></tbody><tfoot><tr style="border-top:1.5px solid #d3d1c7"><td colspan="2" style="padding:7px 12px;font-weight:700;font-size:12px">Total</td><td id="hk-total" style="text-align:right;padding:7px 12px;font-weight:700;font-size:12px"></td><td style="text-align:right;padding:7px 12px;font-weight:700;font-size:12px">100%</td></tr></tfoot></table></div>
  </div>
  <div class="insight"><strong>Distribuidora Ling Long representa la mayor parte del volumen exportado por HK Tiancheng hacia Panama.</strong> Los otros compradores son en su mayoria clientes de Ling Long que adquieren contenedores directos, por lo que la operacion de HK Tiancheng en Panama esta integramente canalizada a traves de Ling Long.</div>
</div><div class="section" id="sec-proveedores">
  <div class="section-title">Analisis Ling Long &#8212; Suppliers / Exportadores</div>
  <div class="section-desc">Proveedores de Distribuidora Ling Long consolidados por nombre.</div>
  <div class="grid-2" style=";align-items:center">
    <div class="cwrap" style="--h:300px"><canvas id="llSupChart"></canvas></div>
    <div class="table-wrap"><table data-tools="sort,csv" data-name="ling-long-proveedores"><thead><tr><th>#</th><th>Supplier</th><th style="text-align:right">Uds</th><th style="text-align:right">%</th><th style="text-align:right">$/ud</th></tr></thead><tbody id="llsup-tbody"></tbody></table></div>
  </div>
  <div class="insight" id="insight-sup"></div>
</div>
<div class="section" id="sec-posicion">
  <div class="section-title">Dist. Ling Long &#8212; Posicionamiento por segmento</div>
  <div class="section-desc">Participacion de Ling Long en cada segmento del mercado segun partida arancelaria.</div>
  <p style="font-size:12px;font-weight:600;margin-bottom:12px">Importaciones de Ling Long por tipo de neumatico</p>
  <div class="grid-2" style=";align-items:center;margin-bottom:28px">
    <div class="cwrap" style="--h:300px"><canvas id="llSubChart"></canvas></div>
    <div class="table-wrap"><table data-tools="sort,csv" data-name="ling-long-por-segmento"><thead><tr><th>Segmento</th><th>Codigo</th><th style="text-align:right">Uds</th><th style="text-align:right">%</th><th style="text-align:right">$/ud</th></tr></thead><tbody id="llsub-tbody"></tbody></table></div>
  </div>
  <p style="font-size:12px;font-weight:600;margin-bottom:4px">Market share de Ling Long por segmento</p>
  <p style="font-size:11px;color:#888780;margin-bottom:12px">Comparacion vs. el resto del mercado.</p>
  <div class="cwrap" style="--h:340px;margin-bottom:24px"><canvas id="llShareChart"></canvas></div>
  <div class="table-wrap" style="margin-bottom:20px">
    <table data-tools="sort,csv" data-name="posicionamiento-por-segmento"><thead><tr><th>Segmento</th><th>Codigo</th><th style="text-align:right">Mercado total</th><th style="text-align:right">Ling Long</th><th style="text-align:right">Share LL</th><th style="text-align:right">$/ud mercado</th><th style="text-align:right">$/ud LL</th></tr></thead><tbody id="llpos-tbody"></tbody></table>
  </div>
  <p style="font-size:12px;font-weight:600;margin-bottom:12px">Competidores por segmento de oportunidad</p>
  <div class="grid-2" id="comp-cards"></div>
</div>
<div class="section" id="sec-nomenclatura">
  <div class="section-title">Nomenclatura arancelaria &#8212; Partida 4011</div>
  <div class="section-desc">Sub-partidas de neumaticos de caucho nuevos segun la Aduana de Panama.</div>
  <style>
  .sp-group-lbl{font-size:10px;font-weight:600;text-transform:uppercase;letter-spacing:.6px;color:#888780;margin:14px 0 4px 2px}
  .sp-row{display:grid;grid-template-columns:130px 1fr 160px;align-items:start;gap:0;background:#fff;border:0.5px solid #d3d1c7;border-bottom:none;padding:8px 12px}
  .sp-row:first-of-type{border-radius:8px 8px 0 0}
  .sp-row:last-of-type{border-bottom:0.5px solid #d3d1c7;border-radius:0 0 8px 8px}
  .sp-row:nth-of-type(even){background:#fafaf8}
  .sp-code{font-family:monospace;font-size:11.5px;font-weight:600;color:#0b0b0b;padding-top:1px}
  .sp-desc{font-size:11.5px;color:#0b0b0b;line-height:1.45}
  .sp-desc small{display:block;font-size:10.5px;color:#888780;margin-top:2px}
  .sp-pill{font-size:9.5px;font-weight:600;padding:2px 8px;border-radius:20px;white-space:nowrap;justify-self:end;margin-top:1px}
  .pill-tur{background:#e6f1fb;color:#0c447c}
  .pill-bus{background:#faeeda;color:#633806}
  .pill-moto{background:#eeedfe;color:#3c3489}
  .pill-bici{background:#eaf3de;color:#27500a}
  .pill-agri{background:#e1f5ee;color:#085041}
  .pill-fork{background:#faeeda;color:#854f0b}
  .pill-const{background:#fcebeb;color:#791f1f}
  .pill-aero{background:#fbeaf0;color:#72243e}
  .pill-otros{background:#f4f3f0;color:#52514e;border:0.5px solid #d3d1c7}
  </style>

  <div class="sp-group-lbl">Vehiculos livianos y de pasajeros</div>
  <div class="sp-row"><span class="sp-code">4011.10.00</span><span class="sp-desc">De los tipos utilizados en automoviles de turismo<small>Incluidos vehiculos familiares (SUV, sedan, hatchback) y autos de carrera</small></span><span class="sp-pill pill-tur">Turismo / Racing</span></div>
  <div class="sp-row"><span class="sp-code">4011.40.00</span><span class="sp-desc">De los tipos utilizados en motocicletas<small>Incluye motos, scooters y similares</small></span><span class="sp-pill pill-moto">Motocicletas</span></div>
  <div class="sp-row"><span class="sp-code">4011.50.00</span><span class="sp-desc">De los tipos utilizados en bicicletas<small>Bicicletas de pedal de todo tipo</small></span><span class="sp-pill pill-bici">Bicicletas</span></div>

  <div class="sp-group-lbl">Transporte de carga y pasajeros</div>
  <div class="sp-row"><span class="sp-code">4011.20.00</span><span class="sp-desc">De los tipos utilizados en autobuses o camiones<small>Buses, camiones de reparto, cabezales y similares</small></span><span class="sp-pill pill-bus">Autobus / Camion</span></div>
  <div class="sp-row"><span class="sp-code">4011.30.00</span><span class="sp-desc">De los tipos utilizados en aeronaves<small>Aviacion comercial y privada</small></span><span class="sp-pill pill-aero">Aeronaves</span></div>

  <div class="sp-group-lbl">Agricola y forestal</div>
  <div class="sp-row"><span class="sp-code">4011.70.10</span><span class="sp-desc">Neumaticos nuevos de caucho para tractores y maquinaria agricola<small>Neumaticos con altos relieves tipo espina de pez o similares</small></span><span class="sp-pill pill-agri">Agricola / Forestal</span></div>
  <div class="sp-row"><span class="sp-code">4011.70.90</span><span class="sp-desc">Los demas neumaticos para tractores y maquinaria agricola o forestal<small>Otros perfiles para maquinaria del campo y explotacion forestal</small></span><span class="sp-pill pill-agri">Agricola / Forestal</span></div>

  <div class="sp-group-lbl">Manejo de materiales y construccion (sub-partida 4011.80)</div>
  <div class="sp-row"><span class="sp-code">4011.80.11</span><span class="sp-desc">Neumaticos nuevos para montacargas &#8212; neumaticos inflables<small>Llantas neumaticas para carretillas elevadoras (forklifts)</small></span><span class="sp-pill pill-fork">Montacargas</span></div>
  <div class="sp-row"><span class="sp-code">4011.80.91</span><span class="sp-desc">Neumaticos nuevos para montacargas &#8212; otros neumaticos inflables<small>Variantes de llanta neumatica para montacargas industriales</small></span><span class="sp-pill pill-fork">Montacargas</span></div>
  <div class="sp-row"><span class="sp-code">4011.80.12</span><span class="sp-desc">Bandajes solidos o huecos para vehiculos industriales<small>Ruedas macizas de caucho para carretillas de mano y transpaletas (~$2&#8211;8/ud)</small></span><span class="sp-pill pill-otros">Otros</span></div>
  <div class="sp-row"><span class="sp-code">4011.80.19</span><span class="sp-desc">Los demas neumaticos para vehiculos de construccion o mineria<small>Gruas, cargadores, retroexcavadoras, equipos OTR</small></span><span class="sp-pill pill-const">Construccion / Industrial</span></div>
  <div class="sp-row"><span class="sp-code">4011.80.99</span><span class="sp-desc">Los demas neumaticos para vehiculos industriales y de obra<small>Otros equipos pesados de construccion y mineria</small></span><span class="sp-pill pill-const">Construccion / Industrial</span></div>

  <div class="sp-group-lbl">Otros (sub-partida 4011.90)</div>
  <div class="sp-row"><span class="sp-code">4011.90.10</span><span class="sp-desc">Neumaticos nuevos con altos relieves en forma de V o similar<small>Equipos de movimiento de tierra y obras publicas</small></span><span class="sp-pill pill-const">Construccion / Industrial</span></div>
  <div class="sp-row"><span class="sp-code">4011.90.90</span><span class="sp-desc">Los demas neumaticos nuevos de caucho no clasificados anteriormente<small>Carretillas de mano, ATV, cuatrimotos y usos miscelaneos</small></span><span class="sp-pill pill-otros">Otros</span></div>
</div>
</main>
<footer class="footer">
  <p>Distribuidora Ling Long, S.A. &middot; Analisis Competitivo 2019&#8211;2026 &middot; Confidencial &middot; Karen Hau</p>
  <p>Fuente: Veritrade &#8212; Aduana Nacional de Panama &middot; Partida 4011</p>
</div>
</div>
''')

parts.append('<script>\n')
parts.append('const ALL_DATA = ')
parts.append(data_js)
parts.append(';\nconst COLOR_MAP = ')
parts.append(color_js)
parts.append(';\nconst TIPO_CODES = ')
parts.append(tcodes_js)
parts.append(''';\nconst MONTHS=["Ene","Feb","Mar","Abr","May","Jun","Jul","Ago","Sep","Oct","Nov","Dic"];
const TIPO_COLORS={
  "Turismo / Racing":"#2a78d6",
  "Autobus / Camion":"#eb6834",
  "Autob\\u00fas / Cami\\u00f3n":"#eb6834",
  "Motocicletas":"#4a3aa7",
  "Bicicletas":"#1baf7a",
  "Montacargas":"#eda100",
  "Construcci\\u00f3n / Industrial":"#e34948",
  "Construccion / Industrial":"#e34948",
  "Agr\\u00edcola / Forestal":"#008300",
  "Agricola / Forestal":"#008300",
  "Aeronaves":"#888780",
  "Otros":"#d3d1c7"
};
const OPP_SEGS=["Turismo / Racing","Autob\\u00fas / Cami\\u00f3n","Motocicletas","Montacargas","Construcci\\u00f3n / Industrial","Agr\\u00edcola / Forestal"];
const FALLBACK_COLORS=["#40242d"];
let fallbackIdx=0;
function getColor(name){if(/^Otros/.test(name))return COLOR_MAP["Otros"];if(!COLOR_MAP[name]){COLOR_MAP[name]=FALLBACK_COLORS[fallbackIdx++%FALLBACK_COLORS.length];}return COLOR_MAP[name];}
function getTipoColor(name){return TIPO_COLORS[name]||TIPO_COLORS[Object.keys(TIPO_COLORS).find(k=>k.normalize("NFD").replace(/[\\u0300-\\u036f]/g,"")===name.normalize("NFD").replace(/[\\u0300-\\u036f]/g,""))]||"#b4b2a9";}
function isLL(n){return /ling.?long/i.test(n);}
function fmt(n){return Math.round(n).toLocaleString("es-PA");}
function fmtK(n){return n>=1000000?"$"+(n/1000000).toFixed(1)+"M":n>=1000?"$"+(n/1000).toFixed(0)+"k":"$"+Math.round(n);}
function yTick(v,ctx){const l=ctx.getLabelForValue?ctx.getLabelForValue(v):v;const s=String(l);
  return innerWidth<620&&s.length>15?s.slice(0,14)+"\u2026":s;}
function sl(n){return n.length>30?n.substring(0,28)+"\\u2026":n;}
let charts={};
// Reutiliza la instancia viva de Chart.js para que los datos transicionen en vez de parpadear.
// Solo recrea si el canvas es nuevo o cambio el tipo de grafica.
function upsert(key,id,cfg){
  const el=document.getElementById(id);if(!el)return null;
  const c=charts[key];
  if(!c||c.config.type!==cfg.type||c.canvas!==el){
    if(c){try{c.destroy();}catch(e){}}
    return charts[key]=new Chart(el,cfg);
  }
  c.data.labels=cfg.data.labels;
  const nd=cfg.data.datasets;
  c.data.datasets.length=nd.length;
  nd.forEach((ds,i)=>{c.data.datasets[i]=Object.assign(c.data.datasets[i]||{},ds);});
  c.config.options=cfg.options;
  c.update();
  return c;
}
function ce(id){const el=document.getElementById(id);if(el)el.innerHTML="";}

// --- Comparacion like-for-like -------------------------------------------
// Un anio parcial no se compara contra un anio completo: se recorta la ventana
// del anio anterior a los mismos meses. Las sumas mensuales cuadran exacto con
// los totales, asi que el recorte es exacto.
function lastMonthWithData(d){let last=-1;d.monthly_mkt_qty.forEach((v,i)=>{if(v>0)last=i;});return last<0?11:last;}
function winSum(a,m0,m1){let t=0;for(let i=m0;i<=m1;i++)t+=a[i]||0;return t;}
function impWindowMap(y,m0,m1,full){
  const o={};
  for(const [n,pr] of Object.entries(y.imp_profiles||{})) o[n]=full?pr.total_qty:winSum(pr.monthly,m0,m1);
  return o;
}
function comparable(yr){
  const d=ALL_DATA[String(yr)],pv=ALL_DATA[String(yr-1)];
  if(!d||!pv)return null;
  const m1=d.partial?lastMonthWithData(d):11,m0=0,full=(m1===11);
  const win=full?"":MONTHS[m0]+"–"+MONTHS[m1]+" ";
  const map=impWindowMap(pv,m0,m1,full);
  let rank=null;
  if(full){rank=pv.ll_rank;}
  else{const arr=Object.entries(map).sort((a,b)=>b[1]-a[1]);const i=arr.findIndex(e=>isLL(e[0]));rank=i<0?null:i+1;}
  return {full,m0,m1,label:win+(yr-1),
    mkt:full?pv.total_qty:winSum(pv.monthly_mkt_qty,m0,m1),
    ll:full?pv.ll_qty:winSum(pv.monthly_ll_qty,m0,m1),
    rank:rank,impMap:map};
}
function deltaHtml(cur,prev,ctx){
  if(prev==null||prev===0)return '<span class="delta flat">&#8212;</span>';
  const pct=(cur-prev)/prev*100;
  const cls=pct>0.05?"up":(pct<-0.05?"down":"flat");
  const ar=cls==="up"?"▲":(cls==="down"?"▼":"=");
  return `<span class="delta ${cls}">${ar} ${pct>0?"+":""}${pct.toFixed(1)}%</span>${ctx?`<div class="delta-ctx">${ctx}</div>`:""}`;
}
function rankDeltaHtml(cur,prev){
  if(prev==null)return "";
  const mv=prev-cur; // subir de puesto = numero mas bajo
  if(mv===0)return '<span class="delta flat">= sin cambio</span>';
  const ar=mv>0?"▲":"▼";
  return `<span class="delta ${mv>0?"up":"down"}">${ar} ${Math.abs(mv)} puesto${Math.abs(mv)>1?"s":""}</span>`;
}

function renderAll(yr){
  const d=ALL_DATA[String(yr)];if(!d)return;
  const isPartial=!!d.partial;
  const partialLabel=d.partial_label||"parcial";
  document.getElementById("report-title").textContent="Mercado de Neum\\u00e1ticos en Panam\\u00e1 "+yr+(isPartial?" \u00b7 parcial":"");
  document.getElementById("report-subtitle").textContent="Partida arancelaria 4011 \\u00b7 Importaciones "+(isPartial?partialLabel:"enero\\u2013diciembre "+yr)+" \\u00b7 Fuente: Veritrade";
  const total=d.total_qty,llQty=d.ll_qty,share=(llQty/total*100).toFixed(2);
  const CMP=comparable(yr);
  const banner=document.getElementById("partial-banner");
  if(banner){
    if(isPartial&&CMP){
      banner.style.display="block";
      banner.innerHTML=`<strong>Año parcial, comparado contra el mismo período.</strong> ${partialLabel} frente a ${CMP.label.toLowerCase()}. Los totales no son comparables con un año completo, pero las variaciones sí: miden exactamente los mismos meses.`;
    } else if(isPartial){
      banner.style.display="block";
      banner.innerHTML=`<strong>Año parcial:</strong> los datos corresponden a ${partialLabel}.`;
    } else banner.style.display="none";
  }
  document.getElementById("kpi-total").textContent=fmt(total);
  document.getElementById("kpi-ll").textContent=fmt(llQty);
  document.getElementById("kpi-share").textContent=share+"% market share";
  document.getElementById("kpi-rank").textContent="#"+d.ll_rank;
  const ctxLbl=CMP?"vs "+CMP.label:"";
  document.getElementById("kpi-total-delta").innerHTML=CMP?deltaHtml(total,CMP.mkt,ctxLbl):"";
  const shPrev=CMP&&CMP.mkt?CMP.ll/CMP.mkt*100:null;
  const shDiff=shPrev!=null?(llQty/total*100-shPrev):null;
  document.getElementById("kpi-ll-delta").innerHTML=CMP
    ?deltaHtml(llQty,CMP.ll,ctxLbl)+(shDiff!=null?`<div class="delta block ${shDiff>0.01?"up":(shDiff<-0.01?"down":"flat")}">${shDiff>0?"+":""}${shDiff.toFixed(2)} pp de share</div>`:"")
    :"";
  document.getElementById("kpi-rank-delta").innerHTML=CMP?rankDeltaHtml(d.ll_rank,CMP.rank):"";
  const thD=document.getElementById("imp-th-delta");if(thD)thD.textContent=CMP?"vs "+CMP.label:"Variacion";
  const leader=d.top_imp[0];
  if(d.ll_rank===1){document.getElementById("kpi-diff").textContent=fmt(llQty-(d.top_imp[1]||[0,0])[1]);document.getElementById("kpi-diff-sub").textContent="uds. sobre el #2";}
  else{document.getElementById("kpi-diff").textContent=fmt(leader[1]-llQty);document.getElementById("kpi-diff-sub").textContent="uds. vs. "+leader[0];}

  // Ranking por cantidad. Barras en vez de dona: comparar longitudes es fiable,
  // comparar angulos no, y con 16 series una dona no transmite nada.
  const top15=d.top_imp.slice(0,15);
  const pieLabels=[...top15.map(r=>r[0]),"Otros"];
  const pieQty=[...top15.map(r=>r[1]),Math.max(0,total-top15.reduce((s,r)=>s+r[1],0))];
  const pieColors=[...top15.map(r=>isLL(r[0])?"#2a78d6":"#aab6c2"),"#d8d6cf"];
  upsert("pie","pieChart",{type:"bar",data:{labels:pieLabels,datasets:[{label:"Unidades",data:pieQty,backgroundColor:pieColors,borderWidth:0,borderRadius:{topRight:4,bottomRight:4},borderSkipped:"left"}]},options:{indexAxis:"y",responsive:true,maintainAspectRatio:false,plugins:{legend:{display:false},tooltip:{callbacks:{label:ctx=>` ${fmt(ctx.parsed.x)} uds (${(ctx.parsed.x/total*100).toFixed(1)}%)`}}},scales:{x:{grid:{color:"#e1e0d9"},ticks:{color:"#888780",font:{size:11},callback:v=>(v/1000).toFixed(0)+"k"}},y:{grid:{display:false},ticks:{color:"#52514e",font:{size:11},callback:function(v){return yTick(v,this);}}}}}});
  const top3Share=((d.top_imp[0][1]+(d.top_imp[1]||[0,0])[1]+(d.top_imp[2]||[0,0])[1])/total*100).toFixed(1);
  document.getElementById("insight-pie").innerHTML=`<strong>Distribuidora Ling Long ocupa el #${d.ll_rank} del mercado</strong> con ${fmt(llQty)} unidades (${share}%). Los tres primeros importadores acaparan el <strong>${top3Share}% del mercado total</strong>.`;

  // Ranking table
  ce("imp-table");const maxQ=d.top_imp[0][1];
  d.top_imp.slice(0,15).forEach((r,i)=>{const pct=(r[1]/total*100).toFixed(2),bw=Math.round(r[1]/maxQ*100),ll=isLL(r[0]),color=getColor(r[0]);const tr=document.createElement("tr");if(ll)tr.className="ling-long";tr.innerHTML=`<td style="color:#888780">${i+1}</td><td>${r[0]}${ll?" &#9733;":""}</td><td style="text-align:right;font-variant-numeric:tabular-nums">${fmt(r[1])}</td><td style="text-align:right">${CMP?deltaHtml(r[1],CMP.impMap[r[0]]):""}</td><td style="text-align:right">${pct}%</td><td><div class="bar-bg"><div class="bar-fill" style="width:${bw}%;background:${color}"></div></div></td>`;document.getElementById("imp-table").appendChild(tr);});

  // Line chart
  ce("legend-line");ce("monthly-tbody");
  const top10=d.top10||[];
  const allEntries=top10.map(name=>[name,d.monthly_top10[name]||Array(12).fill(0)]);
  // Diez lineas superpuestas no se distinguen. La grafica muestra 6 y agrupa el
  // resto; el detalle completo sigue en la tabla de abajo. Ling Long nunca se agrupa.
  const rankedE=allEntries.map(e=>({e,t:e[1].reduce((a,b)=>a+b,0)})).sort((a,b)=>b.t-a.t);
  let keep=rankedE.slice(0,6).map(o=>o.e);
  if(!keep.some(e=>isLL(e[0]))){const llo=rankedE.find(o=>isLL(o.e[0]));if(llo)keep=keep.slice(0,5).concat([llo.e]);}
  const keptN=new Set(keep.map(e=>e[0]));
  const restE=allEntries.filter(e=>!keptN.has(e[0]));
  const restVals=MONTHS.map((_,m)=>restE.reduce((t,e)=>t+(e[1][m]||0),0));
  const lineEntries=keep.concat(restE.length?[["Otros ("+restE.length+" importadores)",restVals]]:[]);
  const legLine=document.getElementById("legend-line");
  lineEntries.forEach(([name])=>{const el=document.createElement("span");el.className="legend-item";el.innerHTML=`<span class="legend-swatch" style="background:${getColor(name)}"></span>${sl(name)}`;legLine.appendChild(el);});
    upsert("line","lineChart",{type:"line",data:{labels:MONTHS,datasets:(()=>{const used={};return lineEntries.map(([name,vals])=>{const c=getColor(name);const rep=(used[c]=(used[c]||0)+1);return{label:name,data:vals,borderColor:c,backgroundColor:c+"18",borderWidth:isLL(name)?3:1.8,pointRadius:isLL(name)?5:3,tension:0.35,fill:false,borderDash:rep>1?[6,4]:[]};});})()},options:{responsive:true,maintainAspectRatio:false,interaction:{mode:"index",intersect:false},plugins:{legend:{display:false},tooltip:{itemSort:(a,b)=>b.parsed.y-a.parsed.y,callbacks:{label:ctx=>` ${ctx.dataset.label}: ${fmt(ctx.parsed.y)} uds`}}},scales:{x:{grid:{display:false},ticks:{color:"#888780",font:{size:11}}},y:{grid:{color:"#e1e0d9"},ticks:{color:"#888780",font:{size:11},callback:v=>(v/1000).toFixed(0)+"k"}}}}});
  const sortedLines=allEntries.map(([name,vals])=>({name,vals,total:vals.reduce((a,b)=>a+b,0)})).sort((a,b)=>b.total-a.total);
  const mTbody=document.getElementById("monthly-tbody");
  sortedLines.forEach((row,rank)=>{const ll=/ling.?long/i.test(row.name),tr=document.createElement("tr");if(ll)tr.className="ling-long";const cells=row.vals.map(v=>`<td style="text-align:right;font-variant-numeric:tabular-nums;font-size:11px">${v>0?fmt(v):"\\u2014"}</td>`).join("");tr.innerHTML=`<td style="color:#888780;font-size:11px">${rank+1}</td><td style="font-size:11px"><span style="display:inline-block;width:8px;height:8px;border-radius:2px;background:${getColor(row.name)};margin-right:5px;vertical-align:middle"></span>${row.name}${ll?" &#9733;":""}</td>${cells}<td style="text-align:right;font-weight:700;font-size:11px">${fmt(row.total)}</td>`;mTbody.appendChild(tr);});

  // Exporters
  ce("exp-tbody");
  const topExp=(d.top_exp||[]).slice(0,20);
  topExp.forEach((r,i)=>{const tr=document.createElement("tr");tr.innerHTML=`<td style="color:#888780">${i+1}</td><td>${r[0]}</td><td style="text-align:right;font-variant-numeric:tabular-nums">${fmt(r[1])}</td>`;document.getElementById("exp-tbody").appendChild(tr);});
    upsert("bar","barChart",{type:"bar",data:{labels:topExp.map(r=>r[0]),datasets:[{label:"Unidades",data:topExp.map(r=>r[1]),backgroundColor:topExp.map((_,i)=>i<2?"#2a78d6":i<4?"#3987e5":"#85b7eb"),borderWidth:0,borderRadius:{topRight:4,bottomRight:4},borderSkipped:"left"}]},options:{indexAxis:"y",responsive:true,maintainAspectRatio:false,plugins:{legend:{display:false},tooltip:{callbacks:{label:ctx=>` ${fmt(ctx.parsed.x)} unidades`}}},scales:{x:{grid:{color:"#e1e0d9"},ticks:{color:"#888780",font:{size:11},callback:v=>(v/1000).toFixed(0)+"k"}},y:{grid:{display:false},ticks:{color:"#52514e",font:{size:11}}}}}});

  // Monthly price
  const mktQty=d.monthly_mkt_qty||Array(12).fill(0),mktCif=d.monthly_mkt_cif||Array(12).fill(0);
  const llMonQty=d.monthly_ll_qty||Array(12).fill(0),llMonCif=d.monthly_ll_cif||Array(12).fill(0);
    upsert("price","priceMonthChart",{type:"line",data:{labels:MONTHS,datasets:[{label:"Mercado total",data:mktQty.map((q,i)=>q>0?+(mktCif[i]/q).toFixed(2):null),borderColor:"#888780",backgroundColor:"#88878018",borderWidth:2,pointRadius:3,tension:0.35,fill:false,spanGaps:true},{label:"Ling Long",data:llMonQty.map((q,i)=>q>0?+(llMonCif[i]/q).toFixed(2):null),borderColor:"#2a78d6",backgroundColor:"#2a78d618",borderWidth:3,pointRadius:5,tension:0.35,fill:false,spanGaps:true}]},options:{responsive:true,maintainAspectRatio:false,interaction:{mode:"index",intersect:false},plugins:{legend:{display:true,position:"top",labels:{usePointStyle:true,font:{size:11}}},tooltip:{callbacks:{label:ctx=>ctx.parsed.y!=null?` ${ctx.dataset.label}: $${ctx.parsed.y.toFixed(2)}/ud`:""}}},scales:{x:{grid:{display:false},ticks:{color:"#888780",font:{size:11}}},y:{grid:{color:"#e1e0d9"},ticks:{color:"#888780",font:{size:11},callback:v=>"$"+v}}}}});

  // Tipo donuts + tabla
  const tipoQ=d.tipo_qty||{},tipoC=d.tipo_cif||{};
  const tipoKeysAll=Object.keys(tipoQ).sort((a,b)=>tipoQ[b]-tipoQ[a]);
  const totalQall=Object.values(tipoQ).reduce((a,b)=>a+b,0);
  const totalCall=Object.values(tipoC).reduce((a,b)=>a+b,0);
  const tColors=tipoKeysAll.map(k=>getTipoColor(k));
    upsert("tipoQty","tipoQtyChart",{type:"doughnut",data:{labels:tipoKeysAll,datasets:[{data:tipoKeysAll.map(k=>tipoQ[k]),backgroundColor:tColors,borderWidth:2,borderColor:"#fff"}]},options:{responsive:true,maintainAspectRatio:false,cutout:"50%",plugins:{legend:{display:true,position:"bottom",labels:{font:{size:9},boxWidth:10}},tooltip:{callbacks:{label:ctx=>` ${ctx.label}: ${fmt(ctx.parsed)} uds (${(ctx.parsed/totalQall*100).toFixed(1)}%)`}}}}});
    upsert("tipoCif","tipoCifChart",{type:"doughnut",data:{labels:tipoKeysAll,datasets:[{data:tipoKeysAll.map(k=>tipoC[k]||0),backgroundColor:tColors,borderWidth:2,borderColor:"#fff"}]},options:{responsive:true,maintainAspectRatio:false,cutout:"50%",plugins:{legend:{display:true,position:"bottom",labels:{font:{size:9},boxWidth:10}},tooltip:{callbacks:{label:ctx=>` ${ctx.label}: ${fmtK(ctx.parsed)}`}}}}});
  ce("tipo-tbody");const tipoTbody=document.getElementById("tipo-tbody");
  tipoKeysAll.forEach(k=>{const q=tipoQ[k]||0,c=tipoC[k]||0,avg=q>0?c/q:0;const tr=document.createElement("tr");const codeHtml=TIPO_CODES[k]?`<span class="badge-code">${TIPO_CODES[k]}</span>`:"\\u2014";tr.innerHTML=`<td style="font-size:11px"><span style="display:inline-block;width:8px;height:8px;border-radius:2px;background:${getTipoColor(k)};margin-right:5px;vertical-align:middle"></span><strong>${k}</strong></td><td style="font-size:10px">${codeHtml}</td><td style="text-align:right;font-size:11px;font-variant-numeric:tabular-nums">${fmt(q)}</td><td style="text-align:right;font-size:11px">${(q/totalQall*100).toFixed(1)}%</td><td style="text-align:right;font-size:11px">${fmtK(c)}</td><td style="text-align:right;font-size:11px;font-weight:600">$${avg.toFixed(2)}</td>`;tipoTbody.appendChild(tr);});
  const turQ=tipoQ["Turismo / Racing"]||0,mcarQ=tipoQ["Montacargas"]||0;
  document.getElementById("insight-tipo").innerHTML=`<strong>Turismo/Racing</strong> domina en volumen (${(turQ/totalQall*100).toFixed(0)}%). <strong>Montacargas</strong> (4011.80.11 / 4011.80.91) es un segmento independiente con ${fmt(mcarQ)} uds separado ahora de Construcci\\u00f3n/Industrial. <strong>Agr\\u00edcola/Forestal</strong> (4011.70.10/90) incluye solo llantas para tractores y maquinaria agr\\u00edcola a ~$${tipoQ["Agr\\u00edcola / Forestal"]>0?(tipoC["Agr\\u00edcola / Forestal"]/tipoQ["Agr\\u00edcola / Forestal"]).toFixed(0):"\\u2014"}/ud.`;

  // Pais
  const topCountry=(d.top_country||[]).slice(0,12);
    upsert("pais","paisChart",{type:"bar",data:{labels:topCountry.map(r=>r[0]),datasets:[{label:"Unidades",data:topCountry.map(r=>r[1]),backgroundColor:topCountry.map((_,i)=>i===0?"#e34948":i===1?"#eda100":i<4?"#3987e5":"#85b7eb"),borderWidth:0,borderRadius:{topRight:4,bottomRight:4},borderSkipped:"left"}]},options:{indexAxis:"y",responsive:true,maintainAspectRatio:false,plugins:{legend:{display:false},tooltip:{callbacks:{label:ctx=>` ${fmt(ctx.parsed.x)} uds`}}},scales:{x:{grid:{color:"#e1e0d9"},ticks:{color:"#888780",font:{size:11},callback:v=>(v/1000).toFixed(0)+"k"}},y:{grid:{display:false},ticks:{color:"#52514e",font:{size:11}}}}}});

  // HK Tiancheng
  ce("hk-tbody");
  const hkClients=d.hk_clients||[],hkTotal=hkClients.reduce((s,r)=>s+r[1],0);
  const hkColors=["#2a78d6","#85b7eb","#b4b2a9","#d3d1c7","#eda100","#1baf7a"];
    upsert("hk","hkChart",{type:"doughnut",data:{labels:hkClients.map(r=>r[0]),datasets:[{data:hkClients.map(r=>r[1]),backgroundColor:hkColors.slice(0,hkClients.length),borderWidth:2,borderColor:"#fff"}]},options:{responsive:true,maintainAspectRatio:false,cutout:"52%",plugins:{legend:{display:false},tooltip:{callbacks:{label:ctx=>` ${ctx.label}: ${fmt(ctx.parsed)} uds (${(ctx.parsed/hkTotal*100).toFixed(1)}%)`}}}}});
  const hkTbody=document.getElementById("hk-tbody");
  hkClients.forEach((r,i)=>{const ll=isLL(r[0]),tr=document.createElement("tr");if(ll)tr.className="ling-long";tr.innerHTML=`<td style="color:#888780">${i+1}</td><td><span style="display:inline-block;width:8px;height:8px;border-radius:2px;background:${hkColors[i]};margin-right:5px;vertical-align:middle"></span>${r[0]}${ll?" &#9733;":""}</td><td style="text-align:right;font-variant-numeric:tabular-nums">${fmt(r[1])}</td><td style="text-align:right">${(r[1]/hkTotal*100).toFixed(1)}%</td>`;hkTbody.appendChild(tr);});
  const hkTotalEl=document.getElementById("hk-total");if(hkTotalEl)hkTotalEl.textContent=fmt(hkTotal);

  // LL Suppliers
  ce("llsup-tbody");
  const llSup=d.ll_sup||[],llSupTotal=llSup.reduce((s,r)=>s+r[1],0);
  const llSupColors=["#2a78d6","#eb6834","#1baf7a","#eda100","#4a3aa7","#e34948","#e87ba4","#008300","#888780","#5f5e5a","#b4b2a9","#3987e5"];
    upsert("llSup","llSupChart",{type:"doughnut",data:{labels:llSup.map(r=>r[0]),datasets:[{data:llSup.map(r=>r[1]),backgroundColor:llSupColors.slice(0,llSup.length),borderWidth:2,borderColor:"#fff"}]},options:{responsive:true,maintainAspectRatio:false,cutout:"52%",plugins:{legend:{display:false},tooltip:{callbacks:{label:ctx=>` ${ctx.label}: ${fmt(ctx.parsed)} uds (${(ctx.parsed/llSupTotal*100).toFixed(1)}%)`}}}}});
  const llSupTbody=document.getElementById("llsup-tbody");
  llSup.forEach((r,i)=>{const avg=(r[1]>0?r[2]/r[1]:0).toFixed(2),tr=document.createElement("tr");if(i===0)tr.className="ling-long";tr.innerHTML=`<td style="color:#888780">${i+1}</td><td style="font-size:11px"><span style="display:inline-block;width:8px;height:8px;border-radius:2px;background:${llSupColors[i]};margin-right:5px;vertical-align:middle"></span>${r[0]}</td><td style="text-align:right;font-variant-numeric:tabular-nums;font-size:11px">${fmt(r[1])}</td><td style="text-align:right;font-size:11px">${(r[1]/llSupTotal*100).toFixed(1)}%</td><td style="text-align:right;font-size:11px">$${avg}</td>`;llSupTbody.appendChild(tr);});
  const mainSup=llSup[0]||["\\u2014",0,0],mainPct=(llSupTotal>0?mainSup[1]/llSupTotal*100:0).toFixed(1);
  document.getElementById("insight-sup").innerHTML=`<strong>${mainSup[0]} representa el ${mainPct}% del abastecimiento de Ling Long</strong> en ${yr}. Los dem\\u00e1s ${llSup.length-1} proveedores suman el ${(100-parseFloat(mainPct)).toFixed(1)}% restante.`;

  // LL sub
  ce("llsub-tbody");
  const llSub=d.ll_sub||{},llSubKeys=Object.keys(llSub).sort((a,b)=>llSub[b].qty-llSub[a].qty);
  const llSubTotal2=llSubKeys.reduce((s,k)=>s+llSub[k].qty,0);
    upsert("llSub","llSubChart",{type:"doughnut",data:{labels:llSubKeys,datasets:[{data:llSubKeys.map(k=>llSub[k].qty),backgroundColor:llSubKeys.map(k=>getTipoColor(k)),borderWidth:2,borderColor:"#fff"}]},options:{responsive:true,maintainAspectRatio:false,cutout:"52%",plugins:{legend:{display:true,position:"bottom",labels:{font:{size:10},boxWidth:10}},tooltip:{callbacks:{label:ctx=>` ${ctx.label}: ${fmt(ctx.parsed)} uds (${(ctx.parsed/llSubTotal2*100).toFixed(1)}%)`}}}}});
  const llSubTbody=document.getElementById("llsub-tbody");
  llSubKeys.forEach(k=>{const v=llSub[k],avg=v.qty>0?v.cif/v.qty:0,code=TIPO_CODES[k]||"";const tr=document.createElement("tr");tr.innerHTML=`<td style="font-size:11px"><span style="display:inline-block;width:8px;height:8px;border-radius:2px;background:${getTipoColor(k)};margin-right:5px;vertical-align:middle"></span>${k}</td><td style="font-size:9px;color:#888780;font-family:monospace">${code}</td><td style="text-align:right;font-size:11px;font-variant-numeric:tabular-nums">${fmt(v.qty)}</td><td style="text-align:right;font-size:11px">${(v.qty/llSubTotal2*100).toFixed(1)}%</td><td style="text-align:right;font-size:11px">$${avg.toFixed(2)}</td>`;llSubTbody.appendChild(tr);});

  // LL share stacked bar
  const segMkt=d.seg_mkt||{},segLL2=d.seg_ll||{};
  const segFiltered=OPP_SEGS.filter(s=>segMkt[s]&&segMkt[s].qty>0);
    upsert("llShare","llShareChart",{type:"bar",data:{labels:segFiltered,datasets:[{label:"Ling Long",data:segFiltered.map(s=>(segLL2[s]||{qty:0}).qty),backgroundColor:"#2a78d6",borderWidth:0},{label:"Resto mercado",data:segFiltered.map(s=>segMkt[s].qty-((segLL2[s]||{qty:0}).qty)),backgroundColor:"#e1e0d9",borderWidth:0,borderRadius:{topRight:4,bottomRight:4}}]},options:{indexAxis:"y",responsive:true,maintainAspectRatio:false,plugins:{legend:{position:"top",labels:{usePointStyle:true,font:{size:11}}},tooltip:{callbacks:{label:ctx=>{const s=segFiltered[ctx.dataIndex];const llV=(segLL2[s]||{qty:0}).qty,mktV=segMkt[s].qty;return ctx.datasetIndex===0?` Ling Long: ${fmt(llV)} uds (${(llV/mktV*100).toFixed(1)}%)`:`Resto: ${fmt(mktV-llV)} uds`;}}}},scales:{x:{stacked:true,grid:{color:"#e1e0d9"},ticks:{color:"#888780",font:{size:10},callback:v=>(v/1000).toFixed(0)+"k"}},y:{stacked:true,grid:{display:false},ticks:{color:"#52514e",font:{size:11}}}}}});

  // LL pos table
  ce("llpos-tbody");
  const llPosTbody=document.getElementById("llpos-tbody");
  segFiltered.forEach(s=>{const mktV=segMkt[s].qty,mktC=segMkt[s].cif;const llV=(segLL2[s]||{qty:0,cif:0}).qty,llC=(segLL2[s]||{qty:0,cif:0}).cif;const share=(mktV>0?llV/mktV*100:0).toFixed(1);const code=TIPO_CODES[s]||"";const tr=document.createElement("tr");if(/turismo/i.test(s))tr.className="ling-long";tr.innerHTML=`<td style="font-size:11px"><span style="display:inline-block;width:8px;height:8px;border-radius:2px;background:${getTipoColor(s)};margin-right:4px;vertical-align:middle"></span>${s}</td><td style="font-size:9px;color:#888780;font-family:monospace">${code}</td><td style="text-align:right;font-size:11px;font-variant-numeric:tabular-nums">${fmt(mktV)}</td><td style="text-align:right;font-size:11px;font-variant-numeric:tabular-nums">${fmt(llV)}</td><td style="text-align:right;font-size:11px;font-weight:600">${share}%</td><td style="text-align:right;font-size:11px">$${mktV>0?(mktC/mktV).toFixed(2):"\\u2014"}</td><td style="text-align:right;font-size:11px">$${llV>0?(llC/llV).toFixed(2):"\\u2014"}</td>`;llPosTbody.appendChild(tr);});

  // Competitive cards
  ce("comp-cards");
  const segTop=d.seg_top||{},compCards=document.getElementById("comp-cards");
  OPP_SEGS.filter(seg=>segTop[seg]&&segTop[seg].length>0).forEach(seg=>{
    const players=segTop[seg],mktData=segMkt[seg]||{qty:0,cif:0},llData=segLL2[seg]||{qty:0,cif:0};
    const mktAvg=mktData.qty>0?mktData.cif/mktData.qty:0,llAvg=llData.qty>0?llData.cif/llData.qty:0;
    const priceDiff=mktAvg>0?Math.abs((llAvg-mktAvg)/mktAvg*100).toFixed(0):0;
    const llBelow=llAvg>0&&llAvg<mktAvg;
    const priceTag=llAvg>0?(llBelow?`<span style="color:#1baf7a;font-weight:700">${priceDiff}% por debajo &#8595;</span>`:`<span style="color:#e34948;font-weight:700">${priceDiff}% por encima &#8593;</span>`):`<span style="color:#888780">sin datos LL</span>`;
    const maxP=players[0]?players[0][1]:1;
    const rows=players.map((p,i)=>{const ll2=isLL(p[0]),bw=Math.round(p[1]/maxP*100),pAvg=p[1]>0?p[2]/p[1]:0;return `<div style="margin-bottom:8px"><div style="display:flex;justify-content:space-between;align-items:baseline;font-size:10px;color:${ll2?"#2a78d6":"#52514e"};font-weight:${ll2?700:400};margin-bottom:2px"><span>${ll2?"&#9733; ":""}#${i+1} ${p[0]}</span><span style="display:flex;gap:10px;font-variant-numeric:tabular-nums"><span style="color:#888780;font-weight:400">${pAvg>0?"$"+pAvg.toFixed(2)+"/ud":""}</span><span>${fmt(p[1])}</span></span></div><div style="height:5px;background:#e1e0d9;border-radius:3px"><div style="height:100%;width:${bw}%;background:${ll2?"#2a78d6":"#b4b2a9"};border-radius:3px"></div></div></div>`;}).join("");
    const codeHtml=TIPO_CODES[seg]?`<div style="font-size:9px;color:#888780;font-family:monospace;margin-bottom:6px">${TIPO_CODES[seg]}</div>`:"";
    const warnNote=(seg==="Construcci\\u00f3n / Industrial"&&(yr===2022||yr===2023))?`<div style="font-size:9px;color:#8a6200;margin-top:6px;padding:4px 6px;background:#fff8e6;border-radius:4px">&#9888; Precio ${yr} elevado por llantas OTR de Minera Panam\\u00e1 (Cobre Panam\\u00e1, cerr\\u00f3 nov 2023)</div>`:"";
    const card=document.createElement("div");card.className="seg-card";
    card.innerHTML=`<div style="font-size:12px;font-weight:700;color:${getTipoColor(seg)||"#0b0b0b"};margin-bottom:2px">${seg}</div>${codeHtml}<div style="display:grid;grid-template-columns:1fr 1fr;gap:6px;margin-bottom:10px;background:#f4f3f0;border-radius:6px;padding:8px 10px"><div><div style="font-size:9px;color:#888780;margin-bottom:1px">Precio mercado</div><div style="font-size:13px;font-weight:700;color:#0b0b0b">$${mktAvg.toFixed(2)}/ud</div></div><div><div style="font-size:9px;color:#888780;margin-bottom:1px">Precio Ling Long</div><div style="font-size:13px;font-weight:700;color:#2a78d6">${llAvg>0?"$"+llAvg.toFixed(2)+"/ud":"sin datos"}</div></div><div style="grid-column:1/-1;font-size:9px;margin-top:2px">LL est\\u00e1 ${priceTag} del mercado</div></div>${rows}${warnNote}`;
    compCards.appendChild(card);
  });
}

function switchYear(yr){
  document.querySelectorAll(".year-btn").forEach(b=>b.classList.toggle("active",parseInt(b.textContent)===yr));
  renderAll(yr);
  // Reset filter select options when year changes
  rebuildFilterSelect();
}

// ── FILTER LOGIC ────────────────────────────────────────────────
let currentFilterMode = null;
let filterCharts = {};

function destroyFilterCharts(){
  Object.values(filterCharts).forEach(c=>{try{c.destroy();}catch(e){}});
  filterCharts={};
}

function rcf(id){const o=document.getElementById(id);if(!o)return;const p=o.parentNode,n=document.createElement("canvas");n.id=id;p.replaceChild(n,o);}

function setFilterMode(mode){
  currentFilterMode=mode;
  document.querySelectorAll(".filter-tab").forEach(b=>b.classList.remove("active"));
  document.getElementById("ftab-"+mode).classList.add("active");
  document.getElementById("filter-controls").style.display="block";
  document.getElementById("filter-result").style.display="none";
  rebuildFilterSelect();
}

function clearFilterMode(){
  currentFilterMode=null;
  document.querySelectorAll(".filter-tab").forEach(b=>b.classList.remove("active"));
  document.getElementById("filter-controls").style.display="none";
  document.getElementById("filter-result").style.display="none";
  destroyFilterCharts();
}

function getActiveYear(){
  const ab=document.querySelector(".year-btn.active");
  return ab?parseInt(ab.textContent):2025;
}

function rebuildFilterSelect(){
  if(!currentFilterMode)return;
  const yr=getActiveYear();
  const d=ALL_DATA[String(yr)];if(!d)return;
  const sel=document.getElementById("filter-select");
  sel.innerHTML="<option value=''>-- Seleccionar --</option>";
  let items=[];
  if(currentFilterMode==="imp") items=Object.keys(d.imp_profiles||{}).sort();
  else if(currentFilterMode==="exp") items=Object.keys(d.exp_profiles||{}).sort();
  else if(currentFilterMode==="seg") items=Object.keys(d.tipo_qty||{}).filter(k=>d.tipo_qty[k]>0).sort((a,b)=>d.tipo_qty[b]-d.tipo_qty[a]);
  items.forEach(name=>{const o=document.createElement("option");o.value=name;o.textContent=name;sel.appendChild(o);});
  sel.value="";
  document.getElementById("filter-result").style.display="none";
  destroyFilterCharts();
}

function applyFilter(){
  const val=document.getElementById("filter-select").value;
  if(!val){document.getElementById("filter-result").style.display="none";return;}
  destroyFilterCharts();
  document.getElementById("filter-result").style.display="block";
  if(currentFilterMode==="imp") renderImpProfile(val);
  else if(currentFilterMode==="exp") renderExpProfile(val);
  else if(currentFilterMode==="seg") renderSegProfile(val);
  markSortableThs();
}

const PROF_COLORS=["#2a78d6","#eb6834","#1baf7a","#eda100","#4a3aa7","#e34948","#e87ba4","#008300","#888780","#5f5e5a"];

function profKpi(label,value,sub,blue){
  return `<div class="kpi"><div class="kpi-label">${label}</div><div class="kpi-value${blue?" blue":""}">${value}</div><div class="kpi-sub">${sub}</div></div>`;
}

function renderImpProfile(name){
  const yr=getActiveYear();
  const d=ALL_DATA[String(yr)];
  const prof=d.imp_profiles[name];if(!prof)return;
  const total=d.total_qty;
  const share=(prof.total_qty/total*100).toFixed(1);
  const avg=prof.total_cif/prof.total_qty;
  const rank=d.top_imp.findIndex(r=>r[0]===name)+1;
  document.getElementById("prof-kpis").innerHTML=
    profKpi("Importador","","")+ // placeholder overwrite below
    profKpi("Total importado",fmt(prof.total_qty)+" uds","en "+yr,false)+
    profKpi("Market share",share+"%","posicion #"+rank,true)+
    profKpi("Precio prom. CIF","$"+avg.toFixed(2)+"/ud","valor total: "+fmtK(prof.total_cif),false);
  document.getElementById("prof-kpis").innerHTML=
    `<div class="kpi" style="grid-column:1/-1"><div class="kpi-label">Importador analizado</div><div style="font-size:18px;font-weight:700;color:#2a78d6;margin-top:4px">${name}</div></div>`+
    profKpi("Total importado",fmt(prof.total_qty)+" uds","en "+yr+(d.partial?" ("+d.partial_label+")":""),false)+
    profKpi("Market share",share+"%","posicion #"+rank+" en el mercado",true)+
    profKpi("Precio prom. CIF","$"+avg.toFixed(2)+"/ud","CIF total: "+fmtK(prof.total_cif),false);
  // Bar chart — top suppliers
  document.getElementById("prof-bar-label").textContent="Principales proveedores (exportadores)";
  const supData=prof.top_exp.slice(0,10);
  rcf("profBarChart");
  filterCharts.bar=new Chart(document.getElementById("profBarChart"),{type:"bar",data:{labels:supData.map(r=>r[0]),datasets:[{label:"Unidades",data:supData.map(r=>r[1]),backgroundColor:PROF_COLORS.slice(0,supData.length),borderWidth:0,borderRadius:{topRight:4,bottomRight:4},borderSkipped:"left"}]},options:{indexAxis:"y",responsive:true,maintainAspectRatio:false,plugins:{legend:{display:false},tooltip:{callbacks:{label:ctx=>` ${fmt(ctx.parsed.x)} uds ($${supData[ctx.dataIndex][2]>0?(supData[ctx.dataIndex][2]/supData[ctx.dataIndex][1]).toFixed(2):0}/ud)`}}},scales:{x:{grid:{color:"#e1e0d9"},ticks:{color:"#888780",font:{size:10},callback:v=>(v/1000).toFixed(0)+"k"}},y:{grid:{display:false},ticks:{color:"#52514e",font:{size:10}}}}}});
  // Donut — segments
  const segKeys=Object.keys(prof.seg).sort((a,b)=>prof.seg[b][0]-prof.seg[a][0]);
  rcf("profDonutChart");
  filterCharts.donut=new Chart(document.getElementById("profDonutChart"),{type:"doughnut",data:{labels:segKeys,datasets:[{data:segKeys.map(k=>prof.seg[k][0]),backgroundColor:segKeys.map(k=>getTipoColor(k)),borderWidth:2,borderColor:"#fff"}]},options:{responsive:true,maintainAspectRatio:false,cutout:"50%",plugins:{legend:{display:true,position:"bottom",labels:{font:{size:9},boxWidth:10}},tooltip:{callbacks:{label:ctx=>` ${ctx.label}: ${fmt(ctx.parsed)} uds (${(ctx.parsed/prof.total_qty*100).toFixed(1)}%)`}}}}});
  // Line chart — monthly
  rcf("profLineChart");
  filterCharts.line=new Chart(document.getElementById("profLineChart"),{type:"line",data:{labels:MONTHS,datasets:[{label:name,data:prof.monthly,borderColor:"#2a78d6",backgroundColor:"#2a78d618",borderWidth:2.5,pointRadius:4,tension:0.35,fill:true}]},options:{responsive:true,maintainAspectRatio:false,plugins:{legend:{display:false},tooltip:{callbacks:{label:ctx=>` ${fmt(ctx.parsed.y)} uds`}}},scales:{x:{grid:{display:false},ticks:{color:"#888780",font:{size:10}}},y:{grid:{color:"#e1e0d9"},ticks:{color:"#888780",font:{size:10},callback:v=>v>=1000?(v/1000).toFixed(0)+"k":v}}}}});
  // Table
  document.getElementById("prof-thead").innerHTML="<tr><th>#</th><th>Proveedor / Exportador</th><th style='text-align:right'>Unidades</th><th style='text-align:right'>% del total</th><th style='text-align:right'>$/ud CIF</th></tr>";
  const tb=document.getElementById("prof-tbody");tb.innerHTML="";
  supData.forEach((r,i)=>{const avg2=r[1]>0?r[2]/r[1]:0;const tr=document.createElement("tr");tr.innerHTML=`<td style="color:#888780">${i+1}</td><td style="font-size:11px"><span style="display:inline-block;width:8px;height:8px;border-radius:2px;background:${PROF_COLORS[i]};margin-right:5px;vertical-align:middle"></span>${r[0]}</td><td style="text-align:right;font-variant-numeric:tabular-nums">${fmt(r[1])}</td><td style="text-align:right">${(r[1]/prof.total_qty*100).toFixed(1)}%</td><td style="text-align:right;font-weight:600">$${avg2.toFixed(2)}</td>`;tb.appendChild(tr);});
}

function renderExpProfile(name){
  const yr=getActiveYear();
  const d=ALL_DATA[String(yr)];
  const prof=d.exp_profiles[name];if(!prof)return;
  const avg=prof.total_cif/prof.total_qty;
  const rank=d.top_exp.findIndex(r=>r[0]===name)+1;
  document.getElementById("prof-kpis").innerHTML=
    `<div class="kpi" style="grid-column:1/-1"><div class="kpi-label">Exportador analizado</div><div style="font-size:18px;font-weight:700;color:#eb6834;margin-top:4px">${name}</div></div>`+
    profKpi("Total exportado a Panama",fmt(prof.total_qty)+" uds","en "+yr+(d.partial?" ("+d.partial_label+")":""),false)+
    profKpi("Ranking exportador","#"+rank,"por volumen de unidades",true)+
    profKpi("Precio prom. CIF","$"+avg.toFixed(2)+"/ud","CIF total: "+fmtK(prof.total_cif),false);
  document.getElementById("prof-bar-label").textContent="Principales compradores en Panama (importadores)";
  const impData=prof.top_imp.slice(0,10);
  rcf("profBarChart");
  filterCharts.bar=new Chart(document.getElementById("profBarChart"),{type:"bar",data:{labels:impData.map(r=>r[0]),datasets:[{label:"Unidades",data:impData.map(r=>r[1]),backgroundColor:impData.map(r=>getColor(r[0])),borderWidth:0,borderRadius:{topRight:4,bottomRight:4},borderSkipped:"left"}]},options:{indexAxis:"y",responsive:true,maintainAspectRatio:false,plugins:{legend:{display:false},tooltip:{callbacks:{label:ctx=>` ${fmt(ctx.parsed.x)} uds`}}},scales:{x:{grid:{color:"#e1e0d9"},ticks:{color:"#888780",font:{size:10},callback:v=>(v/1000).toFixed(0)+"k"}},y:{grid:{display:false},ticks:{color:"#52514e",font:{size:10}}}}}});
  const segKeys=Object.keys(prof.seg).sort((a,b)=>prof.seg[b][0]-prof.seg[a][0]);
  rcf("profDonutChart");
  filterCharts.donut=new Chart(document.getElementById("profDonutChart"),{type:"doughnut",data:{labels:segKeys,datasets:[{data:segKeys.map(k=>prof.seg[k][0]),backgroundColor:segKeys.map(k=>getTipoColor(k)),borderWidth:2,borderColor:"#fff"}]},options:{responsive:true,maintainAspectRatio:false,cutout:"50%",plugins:{legend:{display:true,position:"bottom",labels:{font:{size:9},boxWidth:10}},tooltip:{callbacks:{label:ctx=>` ${ctx.label}: ${fmt(ctx.parsed)} uds (${(ctx.parsed/prof.total_qty*100).toFixed(1)}%)`}}}}});
  rcf("profLineChart");
  filterCharts.line=new Chart(document.getElementById("profLineChart"),{type:"line",data:{labels:MONTHS,datasets:[{label:name,data:prof.monthly,borderColor:"#eb6834",backgroundColor:"#eb683418",borderWidth:2.5,pointRadius:4,tension:0.35,fill:true}]},options:{responsive:true,maintainAspectRatio:false,plugins:{legend:{display:false},tooltip:{callbacks:{label:ctx=>` ${fmt(ctx.parsed.y)} uds`}}},scales:{x:{grid:{display:false},ticks:{color:"#888780",font:{size:10}}},y:{grid:{color:"#e1e0d9"},ticks:{color:"#888780",font:{size:10},callback:v=>v>=1000?(v/1000).toFixed(0)+"k":v}}}}});
  document.getElementById("prof-thead").innerHTML="<tr><th>#</th><th>Importador en Panama</th><th style='text-align:right'>Unidades</th><th style='text-align:right'>%</th><th style='text-align:right'>$/ud CIF</th></tr>";
  const tb=document.getElementById("prof-tbody");tb.innerHTML="";
  impData.forEach((r,i)=>{const avg2=r[1]>0?r[2]/r[1]:0;const ll=isLL(r[0]);const tr=document.createElement("tr");if(ll)tr.className="ling-long";tr.innerHTML=`<td style="color:#888780">${i+1}</td><td style="font-size:11px"><span style="display:inline-block;width:8px;height:8px;border-radius:2px;background:${getColor(r[0])};margin-right:5px;vertical-align:middle"></span>${r[0]}${ll?" &#9733;":""}</td><td style="text-align:right;font-variant-numeric:tabular-nums">${fmt(r[1])}</td><td style="text-align:right">${(r[1]/prof.total_qty*100).toFixed(1)}%</td><td style="text-align:right;font-weight:600">$${avg2.toFixed(2)}</td>`;tb.appendChild(tr);});
}

function renderSegProfile(seg){
  const yr=getActiveYear();
  const d=ALL_DATA[String(yr)];
  const qty=d.tipo_qty[seg]||0,cif=d.tipo_cif[seg]||0;
  const totalMkt=d.total_qty;
  const avg=qty>0?cif/qty:0;
  const llSeg=d.seg_ll[seg]||{qty:0,cif:0};
  const llShare=qty>0?(llSeg.qty/qty*100).toFixed(1):0;
  document.getElementById("prof-kpis").innerHTML=
    `<div class="kpi" style="grid-column:1/-1"><div class="kpi-label">Sub-partida analizada</div><div style="font-size:18px;font-weight:700;margin-top:4px" ${`style="color:${getTipoColor(seg)}"`}>${seg}</div></div>`+
    profKpi("Mercado total segmento",fmt(qty)+" uds","${(qty/totalMkt*100).toFixed(1)}% del mercado",false)+
    profKpi("Valor CIF total",fmtK(cif),"precio prom: $"+avg.toFixed(2)+"/ud",false)+
    profKpi("Share Ling Long",llShare+"%",fmt(llSeg.qty)+" uds",true);
  // Replace macro with real values
  const share2=(qty/totalMkt*100).toFixed(1);
  document.getElementById("prof-kpis").innerHTML=
    `<div class="kpi" style="grid-column:1/-1"><div class="kpi-label">Sub-partida analizada</div><div style="font-size:18px;font-weight:700;color:${getTipoColor(seg)||"#0b0b0b"};margin-top:4px">${seg}</div></div>`+
    profKpi("Mercado total segmento",fmt(qty)+" uds",share2+"% del total de neumaticos",false)+
    profKpi("Valor CIF total",fmtK(cif),"precio prom: $"+avg.toFixed(2)+"/ud",false)+
    profKpi("Share Ling Long",llShare+"%",fmt(llSeg.qty)+" uds",true);
  // Top importers
  document.getElementById("prof-bar-label").textContent="Ranking importadores en este segmento";
  const segTopData=(d.seg_top[seg]||[]).slice(0,10);
  rcf("profBarChart");
  filterCharts.bar=new Chart(document.getElementById("profBarChart"),{type:"bar",data:{labels:segTopData.map(r=>r[0]),datasets:[{label:"Unidades",data:segTopData.map(r=>r[1]),backgroundColor:segTopData.map(r=>getColor(r[0])),borderWidth:0,borderRadius:{topRight:4,bottomRight:4},borderSkipped:"left"}]},options:{indexAxis:"y",responsive:true,maintainAspectRatio:false,plugins:{legend:{display:false},tooltip:{callbacks:{label:ctx=>` ${fmt(ctx.parsed.x)} uds`}}},scales:{x:{grid:{color:"#e1e0d9"},ticks:{color:"#888780",font:{size:10},callback:v=>(v/1000).toFixed(0)+"k"}},y:{grid:{display:false},ticks:{color:"#52514e",font:{size:10}}}}}});
  // Top exporters in segment
  const segExpData=(d.seg_exp[seg]||[]).slice(0,10);
  rcf("profDonutChart");
  filterCharts.donut=new Chart(document.getElementById("profDonutChart"),{type:"doughnut",data:{labels:segExpData.map(r=>r[0]),datasets:[{data:segExpData.map(r=>r[1]),backgroundColor:PROF_COLORS.slice(0,segExpData.length),borderWidth:2,borderColor:"#fff"}]},options:{responsive:true,maintainAspectRatio:false,cutout:"50%",plugins:{legend:{display:true,position:"bottom",labels:{font:{size:9},boxWidth:10}},tooltip:{callbacks:{label:ctx=>` ${ctx.label}: ${fmt(ctx.parsed)} uds`}}}}});
  // Monthly from mkt (approximate from all importers in seg_top)
  rcf("profLineChart");
  filterCharts.line=new Chart(document.getElementById("profLineChart"),{type:"line",data:{labels:MONTHS,datasets:[{label:"Mercado "+seg,data:MONTHS.map((_,m)=>{const mQty=d.monthly_mkt_qty[m]||0;return 0;}),borderColor:getTipoColor(seg)||"#888780",backgroundColor:"#88878018",borderWidth:2,pointRadius:3,tension:0.35,fill:true,spanGaps:true}]},options:{responsive:true,maintainAspectRatio:false,plugins:{legend:{display:false}},scales:{x:{grid:{display:false},ticks:{color:"#888780",font:{size:10}}},y:{grid:{color:"#e1e0d9"},ticks:{color:"#888780",font:{size:10},callback:v=>v>=1000?(v/1000).toFixed(0)+"k":v}}}}});
  document.getElementById("prof-thead").innerHTML="<tr><th>#</th><th>Importador</th><th style='text-align:right'>Unidades</th><th style='text-align:right'>% del seg.</th><th style='text-align:right'>$/ud CIF</th></tr>";
  const tb=document.getElementById("prof-tbody");tb.innerHTML="";
  segTopData.forEach((r,i)=>{const ll=isLL(r[0]);const avg2=r[1]>0?r[2]/r[1]:0;const tr=document.createElement("tr");if(ll)tr.className="ling-long";tr.innerHTML=`<td style="color:#888780">${i+1}</td><td style="font-size:11px"><span style="display:inline-block;width:8px;height:8px;border-radius:2px;background:${getColor(r[0])};margin-right:5px;vertical-align:middle"></span>${r[0]}${ll?" &#9733;":""}</td><td style="text-align:right;font-variant-numeric:tabular-nums">${fmt(r[1])}</td><td style="text-align:right">${qty>0?(r[1]/qty*100).toFixed(1):0}%</td><td style="text-align:right;font-weight:600">$${avg2.toFixed(2)}</td>`;tb.appendChild(tr);});
}

// --- Herramientas de tabla: ordenar, buscar, exportar --------------------
// Trabaja sobre el DOM actual, asi que sigue funcionando cuando renderAll()
// reconstruye los tbody al cambiar de anio.
function cellNum(td){
  const t=(td.textContent||"").replace(/−/g,"-");
  if(/^\\s*[—-]\\s*$/.test(t))return null;              // guion = sin dato
  const m=t.replace(/[^0-9.,+-]/g,"").replace(/,/g,"");
  if(m===""||m==="-"||m==="+")return null;
  const v=parseFloat(m);
  return isNaN(v)?null:v;
}
function rowsOf(tb){return [...tb.querySelectorAll("tr")];}
function sortTable(table,idx,dir){
  const tb=table.tBodies[0];if(!tb)return;
  const rows=rowsOf(tb);
  const nums=rows.map(r=>cellNum(r.cells[idx]));
  const numeric=nums.filter(v=>v!==null).length>=Math.max(2,rows.length*0.6);
  rows.sort((a,b)=>{
    if(numeric){
      const x=cellNum(a.cells[idx]),y=cellNum(b.cells[idx]);
      if(x===null&&y===null)return 0;
      if(x===null)return 1;            // sin dato siempre al final
      if(y===null)return -1;
      return dir*(x-y);
    }
    return dir*(a.cells[idx].textContent||"").localeCompare((b.cells[idx].textContent||""),"es");
  });
  rows.forEach(r=>tb.appendChild(r));
}
function tableCSV(table){
  const out=[];
  const hr=table.tHead&&table.tHead.rows[0];
  if(hr)out.push([...hr.cells].map(th=>th.textContent.trim()));
  rowsOf(table.tBodies[0]).forEach(r=>{
    if(r.style.display==="none")return;                     // respeta el filtro
    out.push([...r.cells].map(td=>td.textContent.replace(/\\s+/g," ").trim()));
  });
  return out.map(r=>r.map(c=>/[",;\\n]/.test(c)?'"'+c.replace(/"/g,'""')+'"':c).join(",")).join("\\n");
}
function downloadCSV(table){
  const name=(table.dataset.name||"tabla")+"-"+getActiveYear()+".csv";
  const blob=new Blob(["\\uFEFF"+tableCSV(table)],{type:"text/csv;charset=utf-8"});
  const a=document.createElement("a");
  a.href=URL.createObjectURL(blob);a.download=name;document.body.appendChild(a);a.click();
  setTimeout(()=>{URL.revokeObjectURL(a.href);a.remove();},0);
}
function filterTable(table,q){
  const t=q.trim().toLowerCase();
  rowsOf(table.tBodies[0]).forEach(r=>{
    r.style.display=(!t||r.textContent.toLowerCase().includes(t))?"":"none";
  });
}
function markSortableThs(){
  document.querySelectorAll('table[data-tools*="sort"] thead th').forEach(th=>{
    th.tabIndex=0;th.setAttribute("role","button");
  });
}
function setupTableTools(){
  document.querySelectorAll("table[data-tools]").forEach(table=>{
    const tools=(table.dataset.tools||"").split(",");
    const wrap=table.closest(".table-wrap")||table;
    const bar=document.createElement("div");bar.className="tbl-tools";
    if(tools.includes("search")){
      const inp=document.createElement("input");
      inp.type="search";inp.className="tbl-search";inp.placeholder="Buscar…";
      inp.setAttribute("aria-label","Buscar en la tabla");
      inp.addEventListener("input",()=>filterTable(table,inp.value));
      bar.appendChild(inp);
    }
    if(tools.includes("csv")){
      const b=document.createElement("button");
      b.type="button";b.className="tbl-csv";b.textContent="Exportar CSV";
      b.addEventListener("click",()=>downloadCSV(table));
      bar.appendChild(b);
    }
    if(bar.children.length)wrap.parentNode.insertBefore(bar,wrap);
    if(tools.includes("sort")){
      // Delegado: la cabecera del panel de filtros se reconstruye en cada consulta,
      // asi que no sirve enganchar listeners a los th que existen al cargar.
      table.addEventListener("click",e=>{
        const th=e.target.closest("th");
        if(!th||!table.tHead||!table.tHead.contains(th))return;
        const ths=[...th.parentNode.cells],idx=ths.indexOf(th);
        const dir=th.dataset.dir==="1"?-1:1;
        ths.forEach(o=>{delete o.dataset.dir;o.classList.remove("sorted-asc","sorted-desc");});
        th.dataset.dir=String(dir);
        th.classList.add(dir===1?"sorted-asc":"sorted-desc");
        sortTable(table,idx,dir);
      });
      table.addEventListener("keydown",e=>{
        if((e.key==="Enter"||e.key===" ")&&e.target.tagName==="TH"){e.preventDefault();e.target.click();}
      });
    }
  });
  markSortableThs();
}

renderAll(2025);
setupTableTools();

// --- Scroll-spy de la navegacion ---------------------------------------
(function(){
  const nav=document.getElementById("secnav");if(!nav)return;
  const inner=nav.querySelector(".secnav-inner");
  const links=[...nav.querySelectorAll("a")];
  const secs=links.map(a=>document.getElementById(a.getAttribute("href").slice(1))).filter(Boolean);
  let tick=false;
  function spy(){
    tick=false;
    let cur=null;
    for(const sc of secs){if(sc.getBoundingClientRect().top<=90)cur=sc;}
    links.forEach(a=>{
      const on=!!cur&&a.getAttribute("href")==="#"+cur.id;
      if(on&&!a.classList.contains("active")){
        a.classList.add("active");
        const nb=inner.getBoundingClientRect(),ab=a.getBoundingClientRect();
        if(ab.left<nb.left||ab.right>nb.right)a.scrollIntoView({block:"nearest",inline:"center"});
      }else if(!on){a.classList.remove("active");}
    });
  }
  addEventListener("scroll",()=>{if(!tick){tick=true;requestAnimationFrame(spy);}},{passive:true});
  spy();
})();


</script>
</body>
</html>''')

HTML = ''.join(parts)
out = "index.html"
with open(out, 'w', encoding='utf-8') as f:
    f.write(HTML)
print(f"Done. {len(HTML):,} chars → {out}")
