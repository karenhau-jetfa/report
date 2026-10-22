# Handover — Análisis de Mercado Neumáticos Panamá 2019–2026
**Proyecto:** Distribuidora Ling Long, S.A. — Partida arancelaria 4011  
**Archivos principales:** ver sección "Archivos" abajo  
**Reporte en vivo:** https://karenhau-jetfa.github.io/report

---

## Contexto del proyecto

Reporte de análisis competitivo de importaciones de neumáticos en Panamá (partida 4011), basado en datos de Veritrade (aduana panameña). Cubre 2019–2026, donde 2026 es parcial (ene–may). El cliente es Distribuidora Ling Long, S.A., que importa bajo la marca Ling Long (proveedor principal: HK Tiancheng Inv. Trading, antes llamado Shandong Linglong Tire Co.).

---

## Archivos

| Archivo | Descripción |
|---|---|
| `Analisis_Mercado_Neumaticos_Panama_2025.html` | Reporte final (single-file HTML, ~412 KB) |
| `extract_v8.py` | Script de extracción de datos desde los xlsx de Veritrade |
| `years_data_v8.json` | JSON con todos los datos (~0.8 MB, 2019–2026) |
| `data_veritrade/` | Los xlsx de Veritrade, uno por año (2026 en dos: `_202605` ene–may y `_20260608` jun–ago). **Ignorado por git**: datos crudos de aduana, confidenciales. Copia maestra en Drive, carpeta `Veritrade_*`. |
| `gen_final.py` | Script Python que genera el HTML a partir del JSON |

Todo vive en el repo `karenhau-jetfa/report` (menos `data_veritrade/`). Se publica con `git push`: GitHub Pages sirve `index.html`.

---

## Datos de origen (Veritrade)

Archivos xlsx de aduana panameña. `FILES` en `extract_v8.py` mapea cada año a una **lista** de archivos, así que un año puede venir en varias descargas (2026 = ene–may + jun–ago) y se suman en los mismos acumuladores. Columnas relevantes:
- `Importador` — empresa que importa en Panamá
- `Embarcador / Exportador` — fábrica o trader de origen
- `Sub Partida Arancelaria` — código HS (4011.10, 4011.20, etc.)
- `Cantidad` — unidades
- `Valor CIF USD` — valor CIF en USD
- `Fecha` — fecha de la importación
- `País de Origen`

**Problema conocido:** los nombres de exportadores tienen typos severos (OCR/digitación). Se resuelven con `canon_exp()` en `extract_v8.py` usando regex.

---

## Segmentos (clasificación `classify_tipo` en extract_v8.py)

| Sub-partida | Segmento |
|---|---|
| 4011.10 | Turismo / Racing |
| 4011.20 | Autobús / Camión |
| 4011.40 | Motocicletas |
| 4011.70 | Agrícola / Forestal |
| 4011.80.11, 4011.80.91 | Montacargas |
| 4011.80.19, 4011.80.99, 4011.90.10 | Construcción / Industrial |
| 4011.50 | Bicicletas |
| demás | Otros / Aeronaves |

---

## Estructura de `years_data_v8.json`

```json
{
  "2025": {
    "partial": false,
    "partial_label": null,
    "total_qty": 1234567,
    "total_cif": 45678901.23,
    "ll_qty": 173135,
    "ll_cif": 6392187.99,
    "ll_rank": 2,
    "ll_name": "Ling Long",
    "top_imp": [["Auto Centro S.A.", 175703, 8388533], ...],
    "top10": [...],                         // top 10 importadores para gráfica de barras
    "monthly_top10": {...},                  // qty mensual por importador
    "monthly_mkt_qty": [0,0,...],           // qty mensual total (12 valores)
    "monthly_mkt_cif": [...],
    "monthly_ll_qty": [...],
    "monthly_ll_cif": [...],
    "top_exp": [["HK Tiancheng Inv. Trading", 450000, 15000000], ...],
    "tipo_qty": {"Turismo / Racing": 800000, ...},
    "tipo_cif": {...},
    "top_country": [["China", 900000, 30000000], ...],
    "ll_sub": {"4011.10": [qty, cif], ...}, // Ling Long por sub-partida
    "hk_clients": [["Ling Long", qty, cif, pct], ...],  // clientes de HK Tiancheng
    "ll_sup": {"HK Tiancheng Inv. Trading": [qty, cif], ...},  // proveedores de Ling Long
    "seg_mkt": {"Turismo / Racing": [qty, cif], ...},
    "seg_ll":  {"Turismo / Racing": {"qty": 173135, "cif": 6392187}, ...},
    "seg_top": {"Turismo / Racing": [["Auto Centro", qty, cif], ...], ...},
    "imp_profiles": {
      "Ling Long": {
        "total_qty": 173135,
        "total_cif": 6392187,
        "top_exp": [["HK Tiancheng", qty, cif], ...],  // top 10
        "seg": {"Turismo / Racing": [qty, cif], ...},
        "monthly": [0, 12000, ...]  // 12 valores
      }, ...
    },
    "exp_profiles": {
      "HK Tiancheng Inv. Trading": {
        "total_qty": ...,
        "total_cif": ...,
        "top_imp": [["Ling Long", qty, cif], ...],
        "seg": {...},
        "monthly": [...]
      }, ...
    },
    "seg_exp": {
      "Turismo / Racing": [["HK Tiancheng", qty, cif], ...],
      ...
    },
    "seg_monthly": {"Turismo / Racing": [12 valores qty], ...}   // nuevo oct 2026
  },
  "2026": {
    "partial": true,
    "partial_label": "ene–ago 2026",
    ...
  }
}
```

---

## Normalización de nombres

### Importadores — `NAME_MAP` (dict exacto en extract_v8.py)
Mapea variantes de nombre de empresas panameñas al nombre canónico. Por ejemplo: `"LING LONG S.A."` → `"Ling Long"`.

### Exportadores — `canon_exp()` (regex en extract_v8.py)
Función con ~30 patrones regex. Ejemplos clave:
- `TIAN[A-Z]*CHENG|TIACHENG|...` → `"HK Tiancheng Inv. Trading"`
- `SHANDONG LINGLONG|SHANDONG LING LONG` → `"Shandong Linglong Tire Co."` (**separado de HK Tiancheng**, son entidades distintas aunque misma empresa)
- `LLIT` → `"LLIT (Thailand) Co., Ltd"`

**IMPORTANTE:** Shandong Linglong y HK Tiancheng NO se deben fusionar. SDL fue el nombre hasta ~2019–2020; HKT es la entidad actual. Son el mismo fabricante pero el cliente quiere ver la transición en los datos.

### Normalización sistemática y fusión de erratas (oct 2026)

Antes, un nombre sin entrada en `NAME_MAP` salía con `str(raw).title()`, así que
`EMPRESAS MELO  S A` y `EMPRESAS MELO S A` eran dos importadores, y «Supro Mundial»
llegó a tener 37 grafías entre los exportadores. Ahora hay tres capas, en este orden:

1. **Reglas explícitas** — `NAME_MAP` (importadores) y las regex de `canon_exp()` (marcas).
   Mandan siempre. Al principio de `canon_exp` se corrigen erratas recurrentes de marca o
   ciudad (`SHANGDONG→SHANDONG`, `QINDAO/QUINGDAO→QINGDAO`, `HAKOOK/HANKKOOK→HANKOOK`,
   `GOOD YEAR→GOODYEAR`, `ZHOGCE/ZHONGE→ZHONGCE`, variantes de Bridgestone y Tiancheng).
2. **`smart_name()`** — fallback determinista: quita acentos, puntuación y espacios dobles,
   estandariza el sufijo legal (`S A`, `S.A`, `, S.A.`, `SOCIEDAD ANONIMA` → `S.A.`;
   `CO., LTD` → `Ltd.`…) y elimina la marca de zona libre (`Z.L.`, `ZL`, `ZONA LIBRE`).
3. **`cluster_aliases()`** — pre-pasada sobre todos los xlsx que agrupa erratas de forma
   conservadora: misma empresa si solo difiere **una** palabra, de ≥5 letras, con el mismo
   arranque y similitud ≥0.85 (o si sobra una palabra genérica como INT/TRADING). Como nombre
   del grupo elige la grafía con menos palabras «raras» (que no aparecen en ninguna otra
   empresa) y, a igualdad, la de más volumen. Así `Transamerica` gana a `Trasamerican`
   aunque esta tenga más unidades.

Parejas parecidas que son empresas distintas van en `_NO_FUSIONAR` y nunca se juntan:
Shandong Changfeng / Shandong Yongfeng, Quart International / TBC International,
Shandong Linglong / HK Tiancheng.

Cada extracción escribe **`data_veritrade/nombres_fusionados.txt`** (fuera del repo) con
todos los grupos y sus volúmenes para auditarlos. Si una fusión es incorrecta: añadir la
pareja a `_NO_FUSIONAR`; si falta una, añadirla a `NAME_MAP` o a `canon_exp()`.
Las fusiones no cambian ningún total: solo redistribuyen volumen entre nombres.

### Filtro de datos espurios — `is_spurious()`
Excluye registros:
- Nombre `"BAC TICKETS AWB"` — registros de pago, no mercancía
- Motocicletas con precio < $1.50/ud
- Agrícola con precio < $1.00/ud

---

## Estructura del HTML (`gen_final.py`)

El HTML es un único archivo autocontenido con Chart.js 4.4.1 desde CDN.

### Datos embebidos
```javascript
const ALL_DATA = { "2019": {...}, "2020": {...}, ..., "2026": {...} };
```
Se genera en `gen_final.py` haciendo `json.dumps(data)` e insertándolo como literal JS.

### Secciones del reporte (en orden)

1. **Header** — título, selector de año (botones), banner de año parcial
2. **KPIs globales** — total mercado, Ling Long qty/cif/share/rank
3. **Evolución del mercado** — gráfica de línea multi-año (qty y cif)
4. **Top importadores** — gráfica de barras apiladas + tabla top 20
5. **Market share por importador** — dona + tabla share
6. **Filtros de Análisis** — *(sección nueva)* panel con 3 modos
7. **Análisis Ling Long** — evolución share, tabla proveedores, gráfica mensual
8. **Análisis HK Tiancheng** — clientes en Panamá con fila de total
9. **Distribución por segmento** — dona de tipo_qty + tabla + precio/ud
10. **Top exportadores** — barras + tabla top 20
11. **País de origen** — tabla top países
12. **Footer**

### Variables JS globales importantes
```javascript
const MONTHS = ['Ene','Feb','Mar','Abr','May','Jun','Jul','Ago','Sep','Oct','Nov','Dic'];
const TIPO_COLORS = {'Turismo / Racing': '#2a78d6', 'Autobús / Camión': '#eb6834', ...};
const IMP_COLORS = {...};  // color fijo por importador
function getColor(name) {...}
function getTipoColor(seg) {...}
function isLL(name) {...}   // true si es Ling Long o entidad del grupo
function fmt(n) {...}        // formatea número con comas
function fmtK(n) {...}       // formatea en miles/millones
```

### Chart instances (no destruir sin destroy() primero)
```javascript
let barChart, donutChart, lineChart, shareDonut, // gráficas principales
    trendLine, llMonthlyChart, segDonut;
// Filtros:
let filterCharts = {};  // {bar, donut, line} — se destruyen con destroyFilterCharts()
```

---

## Panel de Filtros (sección nueva añadida en esta sesión)

### HTML (dentro de `<div class="section" id="filter-section">`)
- 3 botones `.filter-tab`: Por Importador, Por Exportador, Por Sub-partida
- Botón "✕ Quitar filtro"
- `<select id="filter-select">` — se puebla dinámicamente
- `<div id="filter-result">` con:
  - `<div id="prof-kpis">` — 4 KPI cards
  - `<canvas id="profBarChart">` — barras horizontales
  - `<canvas id="profDonutChart">` — dona de segmentos
  - `<canvas id="profLineChart">` — línea mensual
  - `<table>` con `<thead id="prof-thead">` y `<tbody id="prof-tbody">`

### Funciones JS del panel
```javascript
setFilterMode(mode)      // 'imp' | 'exp' | 'seg' — activa tab, puebla select
clearFilterMode()        // oculta todo, destruye gráficas de filtro
rebuildFilterSelect()    // regenera opciones del select para el año activo
applyFilter()            // lee select, llama renderImpProfile / renderExpProfile / renderSegProfile
destroyFilterCharts()    // destruye filterCharts.bar/.donut/.line
rcf(id)                  // reemplaza canvas por uno nuevo (evita error "Canvas already in use")

renderImpProfile(name)   // usa d.imp_profiles[name]
renderExpProfile(name)   // usa d.exp_profiles[name]
renderSegProfile(seg)    // usa d.seg_top[seg], d.seg_exp[seg], d.seg_ll[seg]
```

`switchYear()` llama `rebuildFilterSelect()` para resetear el panel al cambiar de año.

---

## CSS classes relevantes

```css
.filter-tab          /* botones de modo de filtro */
.filter-tab.active   /* tab seleccionado — fondo azul */
.filter-select       /* dropdown de selección */
.profile-kpi         /* grid 3 columnas de KPI cards */
.profile-chart-row   /* grid 2 columnas para bar + donut */
.kpi                 /* card individual */
.kpi-value.blue      /* valor en azul */
.ling-long           /* fila resaltada en tablas */
.section             /* contenedor de cada sección */
.section-title
.section-desc
.table-wrap          /* scroll horizontal en tablas */
.year-btn            /* botones de selector de año */
.year-btn.active
```

---

## Hosting (GitHub Pages)

- Repo: `karenhau-jetfa/report` (público)
- Branch: `main`
- Archivo raíz: `index.html` (= `Analisis_Mercado_Neumaticos_Panama_2025.html` renombrado)
- URL: https://karenhau-jetfa.github.io/report
- Para actualizar: subir el nuevo HTML como `index.html` al repo

---

## Pendientes / mejoras posibles

- ~~Gráfico mensual por segmento plano~~ **Resuelto (oct 2026)**: `seg_monthly` sale de `extract_v8.py` y `renderSegProfile` lo usa; si faltara en un año, el gráfico se oculta con una nota en vez de pintar ceros.
- **Para incorporar una nueva descarga de Veritrade:** 1) bajar el xlsx de Drive a `data_veritrade/`; 2) añadirlo a la lista del año en `FILES` (o crear el año) y, si el año queda incompleto, ajustar `PARTIAL_YEARS`; 3) `python3 extract_v8.py` (necesita `openpyxl`); 4) `python3 gen_final.py`; 5) commit + push. El comparativo like-for-like, el resumen y los movimientos se adaptan solos a los meses con datos.
- El reporte no tiene buscador de texto dentro de las tablas — se podría agregar con un `<input>` y filtrado JS sobre `tbody`.
- Las tablas de top importadores/exportadores muestran top 20; se podría hacer paginable.
