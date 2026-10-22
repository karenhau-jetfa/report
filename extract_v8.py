"""
extract_v8.py — Full re-extraction with cross-tab profiles for filters
Outputs years_data_v8.json with imp_profiles, exp_profiles, seg_exp added
"""

import openpyxl, json, re, os
from collections import defaultdict
from datetime import datetime

# Los xlsx de Veritrade viven en data_veritrade/ (ignorado por git: son datos
# crudos de aduana, confidenciales). Un anio puede venir en varios archivos.
DATA_DIR = os.environ.get('VERITRADE_DIR',
           os.path.join(os.path.dirname(os.path.abspath(__file__)), 'data_veritrade'))
def _f(*names): return [os.path.join(DATA_DIR, n) for n in names]
FILES = {
    2019: _f('Veritrade_2019.xlsx'),
    2020: _f('Veritrade_2020.xlsx'),
    2021: _f('Veritrade_2021.xlsx'),
    2022: _f('Veritrade_2022.xlsx'),
    2023: _f('Veritrade_2023.xlsx'),
    2024: _f('Veritrade_2024.xlsx'),
    2025: _f('Veritrade_2025.xlsx'),
    2026: _f('Veritrade_202605.xlsx', 'Veritrade_20260608.xlsx'),  # ene-may + jun-ago
}

PARTIAL_YEARS = {2026: 'ene–ago 2026'}

NAME_MAP = {
    # Erratas detectadas en oct 2026 (misma empresa, distinta grafia en aduana)
    'COPORACION COSTA ATLANTICA': 'Corporacion Costa Atlantica',
    'CORPORACION COSTA ATLANTICA': 'Corporacion Costa Atlantica',
    'AUTO RESPUESTO UNIVERSAL': 'Auto Repuesto Universal',
    '*AUTO RESPUESTO UNIVERSAL*': 'Auto Repuesto Universal',
    'AUTO REPUESTO UNIVERSAL': 'Auto Repuesto Universal',
    'LLANTERIA BETHANIA': 'Llanteria Betania',
    'LLANTERIA BETANIA': 'Llanteria Betania',
    'GRUPO N/P': 'Grupo N&P S.A.',
    'GRUPO N&P S.A.': 'Grupo N&P S.A.',
    'N&P, S.A.': 'Grupo N&P S.A.',
    'COOPERATIVA DE SERVICIOS DE TRANSPORTE JOAQUINA DE TORRIJOS': 'Coop. de Transporte Joaquina H. de Torrijos R.L.',
    'COOPERATIVA  DE SERVICIOS DE TRANSPORTE JOAQUINA H  DE TORRIJOS RL': 'Coop. de Transporte Joaquina H. de Torrijos R.L.',
    'AUTO CENTRO S A': 'Auto Centro S.A.',
    'DISTRIBUIDORA LING LONG  S A': 'Ling Long',
    'DISTRIBUIDORA LING LONG S A': 'Ling Long',
    'CENTRAL DE LUBRICANTES S A': 'Central Lubricantes S.A.',
    'CENTRAL DE LUBRICANTES  S A': 'Central Lubricantes S.A.',
    'TAMBOR S A': 'Tambor S.A.',
    'PRODUCTOS SUPERIORES S A': 'Prod. Superiores S.A.',
    'MULTI SERVICIOS AMERICAN WHEELS  S A': 'Multi Serv. American Wheels',
    'MULTI SERVICIOS AMERICAN WHEELS S A': 'Multi Serv. American Wheels',
    'COMPAÑIA CHIRICANA DE AUTOMOVILES  S  A': 'Cia. Chiricana de Automoviles',
    'COMPAÑIA CHIRICANA DE AUTOMOVILES S A': 'Cia. Chiricana de Automoviles',
    'CIA  CHIRICANA DE AUTOMOVILES  S  A': 'Cia. Chiricana de Automoviles',
    'DISTRIBUIDORA RALI  S A': 'Dist. Rali S.A.',
    'DISTRIBUIDORA RALI S A': 'Dist. Rali S.A.',
    'COMERCIAL RALI  S A': 'Dist. Rali S.A.',
    'COMERCIAL RALI S A': 'Dist. Rali S.A.',
    'DIPSA S A': 'Dipsa S.A.',
    'GRUPO DAHER S A': 'Grupo Daher S.A.',
    'GRUPO DAHER  S A': 'Grupo Daher S.A.',
    'KING WONG S A': 'King Wong S.A.',
    'KING WONG  S A': 'King Wong S.A.',
    'DURALLANTA S A': 'Durallanta S.A.',
    'DURALLANTA  S A': 'Durallanta S.A.',
    'FENG DI ZHUO CHONG': 'Feng Di Zhuo Chong',
    'GENERAL LIFE PANAMA S A': 'General Life Panama S.A.',
    'GENERAL LIFE PANAMA  S A': 'General Life Panama S.A.',
    'DK SPEED S A': 'DK Speed S.A.',
    'DK RACING S A': 'DK Speed S.A.',
    'RECONSTRUCTORA EN FRIO  S A': 'Reconstructora en Frio S.A.',
    'RECONSTRUCTORA EN FRIO S A': 'Reconstructora en Frio S.A.',
    'AUTO SERVICIOS 88 INTERNACIONAL S A': 'Auto Ser. 88 Internacional',
    'AUTO SER  88 INTERNACIONAL  S A': 'Auto Ser. 88 Internacional',
    'AUTO SER 88 INTERNACIONAL  S A': 'Auto Ser. 88 Internacional',
    'KENBROTH CORP': 'Kenbroth Corp.', 'KENBROTH CORP ': 'Kenbroth Corp.',
    'MOVILIDAD INTERNACIONAL  S A': 'Movilidad Internacional S.A.',
    'MOVILIDAD INTERNACIONAL S A': 'Movilidad Internacional S.A.',
    'MOVILIDAD INTERNACIONAL, S.A.': 'Movilidad Internacional S.A.',
    'PRICESMART PANAMA S A': 'PriceSmart Panama S.A.',
    'PRICESMART PANAMA  S A': 'PriceSmart Panama S.A.',
    'BAC INTERNATIONAL BANK  PANAMA  INC': 'BAC International Bank',
    'BAC INTERNATIONAL BANK (PANAMA) INC': 'BAC International Bank',
    'DECO AUTO S A': 'Deco Auto S.A.', 'DECO AUTO  S A': 'Deco Auto S.A.',
    'MEGA TIRES SALEH S A': 'Mega Tires Saleh S.A.',
    'BENSERCA 18 S A': 'Benserca 18 S.A.', 'BENSERCA 18  S A': 'Benserca 18 S.A.',
    'MOTOR GROUP LATAM  S A': 'Motor Group Latam S.A.',
    'MOTOR GROUP LATAM S A': 'Motor Group Latam S.A.',
    'MOTOR GROUP LATAM, S.A.': 'Motor Group Latam S.A.',
    'MOTOPARTES SPARTON': 'Motopartes Sparton',
    'XTREME MOTORS TRADING INC': 'Xtreme Motors Trading Inc.',
    'PLANET MOTOS  S A': 'Planet Motos S.A.', 'PLANET MOTOS, SA': 'Planet Motos S.A.',
    'SUPER MOTOS SERRANO  S A': 'Super Motos Serrano S.A.',
    'MOTOPARTES MPH S A': 'Motopartes MPH S.A.',
    'MATCO INTERNACIONAL  S A': 'Matco Internacional S.A.',
    'GRUPO HONGFA  S A': 'Grupo Hongfa S.A.',
    'HK TIANCHENG INV  TRADING': 'HK Tiancheng Inv. Trading',
    'HK TIANCHENG INVESTMENT TRADING': 'HK Tiancheng Inv. Trading',
    'MONTACARGAS Y REPUESTOS  S A': 'Montacargas y Repuestos S.A.',
    'PANAMA FORKLIFT COMPANY INC': 'Panama Forklift Co. Inc.',
    'MONTACARGAS SERV IMAN S A': 'Montacargas Serv Iman S.A.',
    'GINSA MOTORS  S  A': 'Ginsa Motors S.A.',
    'GINSA MOTORS S A': 'Ginsa Motors S.A.',
    'EMPRESAS MELO  S A': 'Empresas Melo S.A.',
    'MATECO PANAMA  S A': 'Mateco Panama S.A.',
    'MINERA PANAMA  S  A': 'Minera Panama S.A.',
    'MINERA PANAMA S A': 'Minera Panama S.A.',
    'AUTORIDAD DEL CANAL DE PANAMA': 'Autoridad del Canal de Panama',
    'FORKLIFTEC PARTS  SA': 'Forkliftec Parts S.A.',
    'FORKLIFTEC PARTS, SA': 'Forkliftec Parts S.A.',
}

COUNTRY_MAP = {
    'CHINA': 'China', 'ZONA FRANCA COLÓN': 'Zona Franca Colon',
    'ZONA FRANCA COLON': 'Zona Franca Colon', 'TAILANDIA': 'Tailandia',
    'TAIWÁN, PROVINCIA DE CHINA': 'Taiwan', 'TAIWAN, PROVINCIA DE CHINA': 'Taiwan',
    'KOREA, REPUBLIC OF': 'Corea del Sur', 'COREA DEL SUR': 'Corea del Sur',
    'JAPÓN': 'Japon', 'JAPON': 'Japon', 'MALASIA': 'Malasia',
    'ESTADOS UNIDOS': 'Estados Unidos', 'COSTA RICA': 'Costa Rica',
    'VIETNAM': 'Vietnam', 'BRASIL': 'Brasil', 'INDIA': 'India',
    'INDONESIA': 'Indonesia', 'ALEMANIA': 'Alemania',
}

def canon_exp(name):
    """Comprehensive exporter normalization with regex to catch all typo variants."""
    n = str(name or '').strip()
    nu = n.upper()
    # Erratas recurrentes de marcas/ciudades, corregidas antes de aplicar las reglas
    nu = re.sub(r'\bSHANGDONG\b|\bSHANDON\b', 'SHANDONG', nu)
    nu = re.sub(r'\bQU?IN(?:G)?DAO\b', 'QINGDAO', nu)                 # QINDAO, QUINGDAO
    nu = re.sub(r'HA[NM]?K+OOK|HAKOOK', 'HANKOOK', nu)                  # HANKKOOK, HAKOOK, HAMKOOK
    nu = re.sub(r'GOOD\s*YEAR|GOOYEAR', 'GOODYEAR', nu)
    nu = re.sub(r'\b(BRIDGESTONE|BRIGESTONE|BRIDGETONE|BRISGESTONE)S?\b', 'BRIDGESTONE', nu)
    nu = re.sub(r'\bZHO[NG]*[CG]+E\b', 'ZHONGCE', nu)                 # ZHONCGE, ZHOGCE, ZHONGE
    nu = re.sub(r'\bTIAN[A-Z ]{0,3}CHENG\b|TIANCFHENG|TIANCHE NG', 'TIANCHENG', nu)
    # Erratas y variantes de razon social detectadas por similitud sobre el dataset
    # 2019-2026. Ojo: Shandong Linglong y HK Tiancheng NO se fusionan a proposito.
    if re.search(r'DIS[RT]{2}IBUIDORA RALI|DIST\.? RALI', nu):
        return 'Dist. Rali S.A.'
    if 'DEESTONE' in nu:
        return 'Deestone Corporation Ltd.'
    if re.search(r'INDUSTRIAS? NARVA MAROVIA', nu):
        return 'Industrias Narva Marovia S.A.'
    if re.search(r'IMPORTACIONES Y SERVICIOS GS', nu):
        return 'Importaciones Y Servicios Gs, S.A.'
    if re.search(r'^LEONTEX', nu):
        return 'Leontex'
    if re.search(r'^SABABA IMPORT', nu):
        return 'Sababa Import'
    if re.search(r'SHANDONG WANDA BOTO', nu):
        return 'Shandong Wanda Boto Tyre'
    if re.search(r'SPORTRAK TIRE GROUP', nu):
        return 'Sportrak Tire Group'
    if re.search(r'^ZENA FAST SERVICE', nu):
        return 'Zena Fast Service'
    if re.search(r'ZHON[CG]{2}E RUBBER', nu):
        return 'Zhongce Rubber Group'
    # HK Tiancheng — all variants including special chars
    if re.search(r'TIAN[A-Z}]?[A-Z]?CHENG|TIACHENG|TIANCXHENG|TIA[}]ICHENG|TIANCCHENG|TIANHENG|TGIANCHENG', nu):
        return 'HK Tiancheng Inv. Trading'
    if 'HONG KONG' in nu and re.search(r'TIAN|TIACH|TIANCH', nu):
        return 'HK Tiancheng Inv. Trading'
    if re.search(r'HONGKONG TIA[A-Z]?[A-Z]?CHENG|HONGKONG TIACH', nu):
        return 'HK Tiancheng Inv. Trading'
    if re.search(r'WAN CHAI HONGKONG', nu):
        return 'HK Tiancheng Inv. Trading'
    # LLIT Thailand
    if re.search(r'\bLLIT\b', nu):
        return 'LLIT (Thailand) Co., Ltd'
    # Zhongce Rubber
    if re.search(r'ZHON+GCE|ZHONGCE', nu):
        return 'Zhongce Rubber Group'
    # Wanli / Hefei Wanli
    if re.search(r'WANL[IY]\s*(GROUP|GROUOP)|WANLIN GROUP|HEFEI WANLI|WANLY GROUP', nu):
        return 'Wanli / Hefei Wanli'
    # Kumho
    if re.search(r'\bKUMHO\b', nu):
        return 'Kumho Tire Co.'
    # Sumitomo / Falken / Dunlop
    if re.search(r'SUMITOMO|FALKEN|SUMI RUBBER|PT\.?\s*SUMI', nu):
        return 'Sumitomo / Falken'
    # Hankook
    if re.search(r'HANKOOK|HANKKOK', nu):
        return 'Hankook Tire & Technology'
    # Nankang
    if re.search(r'NANKANG|NANKAN[^G]|NANKNAG|NAMKANG', nu):
        return 'Nankang Rubber Tire Corp.'
    # Maxtrek
    if re.search(r'MAXTREK|MATREK', nu):
        return 'Maxtrek Tyre'
    # Shandong Linglong
    if re.search(r'SHANDONG LINGLONG|SHANDONG LING LONG|SHANDONG LONGLONG', nu):
        return 'Shandong Linglong Tire Co.'
    if nu.strip() == 'SHANDONG':
        return 'Shandong Linglong Tire Co.'
    # Shandong Changfeng
    if re.search(r'CHAN[GF]FENG|CHANFENG|CHAGFENG|CVHANGFENG|CHANFEG|CHANFENG', nu):
        return 'Shandong Changfeng Tyres'
    # Shandong Haohua
    if re.search(r'HAOHUA|HOAHUA|HAOUA', nu):
        return 'Shandong Haohua Tire Co.'
    # Shandong Habilead
    if re.search(r'HABILEAD', nu):
        return 'Shandong Habilead Rubber'
    # Shandong Mirage
    if re.search(r'MIRAGE TYRE|MIRAGE TIRE', nu):
        return 'Shandong Mirage Tyres'
    # Shandong Yongfeng
    if re.search(r'YONG+FENG|YONGGFENG', nu):
        return 'Shandong Yongfeng Tyres'
    # Shandong Yuetongsen
    if re.search(r'YUETONGSEN|YUETONSEN|YUETOGSEN|YUETONSEN', nu):
        return 'Shandong Yuetongsen Intl.'
    # Shandong Cachland
    if re.search(r'CACHLAND', nu):
        return 'Shandong Cachland Tyres'
    # Wendeng Sanfeng
    if re.search(r'SANFENG|SANFEG', nu):
        return 'Wendeng Sanfeng Tyre Co.'
    # Qingdao Awesome
    if re.search(r'AWESOME', nu):
        return 'Qingdao Awesome Intl.'
    # Qingdao Grandstone
    if re.search(r'GRANDSTONE|GRANSTONE', nu):
        return 'Qingdao Grandstone Tyre'
    # Qingdao Shengshitailai
    if re.search(r'SHENGSHITAILAI|SHENGHSITAILAI', nu):
        return 'Qingdao Shengshitailai'
    # Qingdao Ocsen
    if re.search(r'OCSEN|OCESEN|OCEN INDUS', nu):
        return 'Qingdao Ocsen Industrial'
    # Qingdao New Dalun
    if re.search(r'NEW DALUN|DALUN', nu):
        return 'Qingdao New Dalun Intl.'
    # Qingdao Au-Shine
    if re.search(r'AU.?SHINE', nu):
        return 'Qingdao Au-Shine Group'
    # Xuzhou Armour
    if re.search(r'XUZHOU ARMOU?R|ARMOU?R RUBBER', nu):
        return 'Xuzhou Armour Rubber'
    # Weihai Jiahang
    if re.search(r'WEIHAI|JIAHANG|WEIHBAI', nu):
        return 'Weihai Jiahang Rubber Technology'
    # Weifang Huadong
    if re.search(r'WEIFANG|HUADONG|HUANDONG', nu):
        return 'Weifang Huadong Rubber'
    # Zodo Tire
    if re.search(r'\bZODO\b', nu):
        return 'Zodo Tire Co.'
    # Sailun
    if re.search(r'SAILUN', nu):
        return 'Sailun Group'
    # Aeolus
    if re.search(r'AEOLUS|AELOUS', nu):
        return 'Aeolus Tyre'
    # Tianjin Wanda
    if re.search(r'TIANJIN WANDA|WANDA TYRE', nu):
        return 'Tianjin Wanda Tyre Group'
    # Toyo
    if re.search(r'\bTOYO TIRE|\bTOYO TYRE', nu):
        return 'Toyo Tires'
    # Triangle
    if re.search(r'TRIANGLE TYRE|TRIANGLE TIRE', nu):
        return 'Triangle Tyre Co.'
    # Continental
    if re.search(r'CONTINENTAL TIRE', nu):
        return 'Continental'
    # Kowa Tsusho
    if re.search(r'KOWA\s*TSUSHO', nu):
        return 'Kowa Tsusho'
    # Tyrefare
    if re.search(r'TYREFARE|TYREFAIRE', nu):
        return 'Tyrefare International'
    # Tyre Export
    if re.search(r'TYRE EXPORT', nu):
        return 'Tyre Export Inc'
    # Euro Asia
    if re.search(r'EURO.?ASIA.?INVEST', nu):
        return 'Euro Asia Investment Group'
    # Shanghai Jihoo
    if re.search(r'JIHOO', nu):
        return 'Shanghai Jihoo'
    # Muresa
    if re.search(r'MURESA', nu):
        return 'Muresa Intertrade S.A.'
    # Distribuidora Rali (exporter)
    if re.search(r'DISTRIBUIDORA RALI|COMERCIAL RALI', nu):
        return 'Dist. Rali S.A.'
    # BATO
    if re.search(r'BATO SHARED|B\.A\.T\.O', nu):
        return 'BATO Shared Services'
    # TBC
    if re.search(r'\bTBC\b', nu):
        return 'TBC International'
    # Mitsubishi
    if re.search(r'MITSUBISHI CORP', nu):
        return 'Mitsubishi Corporation'
    # Bridgestone
    if re.search(r'BRIDGESTONE', nu):
        return 'Bridgestone'
    # Michelin
    if re.search(r'MICHELIN', nu):
        return 'Michelin'
    # Goodyear
    if re.search(r'GOODYEAR', nu):
        return 'Goodyear'
    base = smart_name(nu) if n else 'Desconocido'   # nu lleva las erratas ya corregidas
    return ALIAS_EXP.get(base, base)


# ---------------------------------------------------------------------------
# Normalizacion sistematica de nombres (oct 2026)
# El fallback anterior era str(raw).title(): "EMPRESAS MELO  S A" y "EMPRESAS MELO S A"
# salian como dos empresas, y "Supro Mundial" llego a tener 37 grafias. Aqui se
# estandarizan espacios, puntuacion, acentos, sufijo legal y la marca "Z.L.", y
# despues se agrupan erratas de forma conservadora (una sola palabra distinta,
# muy parecida y con el mismo arranque) eligiendo la grafia de mayor volumen.
# NAME_MAP y las reglas regex de canon_exp siguen mandando por encima de esto.
# ---------------------------------------------------------------------------
import unicodedata, difflib

_LEGAL = [
    (r"\bSOCIEDAD\s+ANONIMA\b", "SA"),
    (r"\bS\s*\.?\s*A\s*\.?\s*S\b", "SAS"),
    (r"\bS\s*\.?\s*A\s*\.?(?=\s|$|,)", "SA"),
    (r"\bS\s*\.?\s*DE\s*R\s*\.?\s*L\b(\s*DE\s*C\s*\.?\s*V\b)?", "SRL"),
    (r"\bLTDA\b", "LTDA"), (r"\bLIMITED\b|\bLTD\b", "LTD"),
    (r"\bINCORPORATED\b|\bINC\b", "INC"), (r"\bCORPORATION\b|\bCORP\b", "CORP"),
    (r"\bCOMPANY\b|\bCO\b", "CO"), (r"\bCOMPANIA\b|\bCIA\b", "CIA"),
]
_PRETTY = {"SA": "S.A.", "SAS": "S.A.S.", "SRL": "S. de R.L.", "LTDA": "Ltda.", "LTD": "Ltd.",
           "INC": "Inc.", "CORP": "Corp.", "CO": "Co.", "CIA": "Cia."}
_SMALL = {"DE", "DEL", "LA", "LAS", "EL", "LOS", "Y", "E", "&", "AND", "OF", "THE"}
_ZL = r"\b(Z\s*\.?\s*L\s*\.?|ZONA\s+LIBRE(\s+DE\s+COLON)?|ZLC)\b"
_GENERIC = {"TYRE", "TYRES", "TIRE", "TIRES", "RUBBER", "GROUP", "INDUSTRIAL", "INDUSTRY", "INDUSTRIES",
            "INTERNATIONAL", "INTERNACIONAL", "TRADING", "TRADE", "IMPORT", "EXPORT", "IMPORTADORA",
            "EXPORTADORA", "IMPORTACIONES", "EXPORTACIONES", "SERVICIOS", "TECHNOLOGY", "TECNOLOGY",
            "INVESTMENT", "INT", "INTL", "DISTRIBUIDORA", "COMERCIAL", "COMERCIALIZADORA", "GRUPO"}
# Parejas que se parecen pero son empresas distintas: nunca se fusionan.
_NO_FUSIONAR = {frozenset(p) for p in [
    ("SHANDONGCHANGFENGTYRES", "SHANDONGYONGFENGTYRES"),
    ("QUARTINTERNATIONAL", "TBCINTERNATIONAL"),
    ("SHANDONGLINGLONG", "HKTIANCHENGINV"),
]}

def _deacc(t):
    t = unicodedata.normalize("NFD", t)
    return "".join(c for c in t if unicodedata.category(c) != "Mn")

def smart_parts(raw):
    """-> (clave_identidad, nucleo_en_mayusculas, sufijo_legal)"""
    t = _deacc(str(raw or "")).upper().replace("*", " ")
    t = re.sub(r"[,\.;:/()\"'\-]", " ", t)
    t = re.sub(r"&", " & ", t)
    t = re.sub(_ZL, " ", t)
    t = re.sub(r"\s+", " ", t).strip()
    suf = ""
    for pat, tag in _LEGAL:
        if re.search(pat, t):
            t = re.sub(pat, " ", t)
            if not suf: suf = tag
    t = re.sub(r"\s+", " ", t).strip()
    return re.sub(r"[^A-Z0-9&]", "", t), t, suf

def smart_name(raw):
    key, core, suf = smart_parts(raw)
    if not key: return "Desconocido"
    out = []
    for x in core.split():
        if x in _SMALL: out.append(x.lower())
        elif len(x) <= 3 and not re.search(r"[AEIOU]", x): out.append(x)      # GS, DK, TBC, HK
        else: out.append(x.title())
    out[0] = out[0][:1].upper() + out[0][1:]
    name = re.sub(r"\b(\w)\s*&\s*(\w)\b", r"\1&\2", " ".join(out))
    return (name + (" " + _PRETTY[suf] if suf else "")).strip()

def _typo_equal(core_a, core_b):
    """Misma empresa salvo UNA palabra con errata, o una palabra generica de mas."""
    ta, tb = core_a.split(), core_b.split()
    if ta == tb: return True
    if abs(len(ta) - len(tb)) == 1:
        la, lb = (ta, tb) if len(ta) > len(tb) else (tb, ta)
        return any(la[i] in _GENERIC and la[:i] + la[i+1:] == lb for i in range(len(la)))
    if len(ta) != len(tb): return False
    diff = [(x, y) for x, y in zip(ta, tb) if x != y]
    if len(diff) != 1: return False
    x, y = diff[0]
    if min(len(x), len(y)) < 5 or x[:2] != y[:2]: return False
    return difflib.SequenceMatcher(None, x, y).ratio() >= 0.85

def cluster_aliases(volumes):
    """volumes: {nombre_canonico: qty} -> {nombre: nombre_lider}; solo nombres que cambian."""
    ids = {}
    for name, q in volumes.items():
        key, core, suf = smart_parts(name)
        if not key: continue
        d = ids.setdefault(key, {"names": {}, "core": core, "vol": 0.0})
        d["names"][name] = d["names"].get(name, 0) + q; d["vol"] += q
    order = sorted(ids.items(), key=lambda kv: -kv[1]["vol"])
    leaders = []     # (key, core, nombre_lider)
    alias = {}
    # Frecuencia de cada palabra entre identidades distintas: una palabra que solo
    # existe en una identidad ("TRASAMERICAN", "FREIGTH") huele a errata aunque
    # tenga mas volumen que la grafia correcta ("TRANSAMERICA", "FREIGHT").
    from collections import Counter
    df = Counter(t for d in ids.values() for t in set(d["core"].split()))
    import math
    def normalidad(name):
        """Suma de log-frecuencia de las palabras no genericas: "FREIGHT" (frecuente)
        puntua mas que "FREIGTH" (rara aunque se repita en varias erratas)."""
        _, core, _ = smart_parts(name)
        # Las genericas SI puntuan: excluirlas daba ventaja a la errata (INTERNATIONA
        # sumaba algo mientras INTERNATIONAL, generica, sumaba cero).
        return sum(math.log(df.get(t, 1)) for t in core.split() if len(t) >= 4)
    grupos = {}          # key_lider -> {nombre: volumen}
    for key, d in order:
        target = None
        for lk, lcore in leaders:
            if abs(len(lk) - len(key)) > 3 or lk[0] != key[0]: continue
            if frozenset((lk, key)) in _NO_FUSIONAR: continue
            if _typo_equal(d["core"], lcore): target = lk; break
        if target is None:
            leaders.append((key, d["core"])); target = key
        grupos.setdefault(target, {}).update(d["names"])
    for members in grupos.values():
        if len(members) < 2: continue
        # mejor nombre: palabras mas frecuentes en el corpus; a igualdad, mas volumen
        best = max(members, key=lambda n: (round(normalidad(n), 6), members[n]))
        for n in members:
            if n != best: alias[n] = best
    return alias

ALIAS_IMP, ALIAS_EXP = {}, {}

def build_alias_maps():
    """Pre-pasada sobre todos los xlsx: volumen por nombre base, y agrupacion global."""
    vol_imp, vol_exp = {}, {}
    for year, paths in sorted(FILES.items()):
        for path in ([paths] if isinstance(paths, str) else paths):
            wb = openpyxl.load_workbook(path, read_only=True, data_only=True); ws = wb.active
            hdr, cols = None, {}
            for i, row in enumerate(ws.iter_rows(values_only=True)):
                rs = [str(c).upper() if c else "" for c in row]
                if any("QTY" in c for c in rs) and any("IMPORT" in c for c in rs):
                    hdr = i + 1
                    for j, h in enumerate(rs):
                        if "QTY" in h and "qty" not in cols: cols["qty"] = j
                        if ("IMPORT" in h or "CONSIG" in h) and "imp" not in cols: cols["imp"] = j
                        if "CIF" in h and "cif" not in cols: cols["cif"] = j
                        if ("EMBARCADOR" in h or "EXPORTADOR" in h) and "exp" not in cols: cols["exp"] = j
                        if "DESCRIP" in h and "COMERCIAL" in h and "desc" not in cols: cols["desc"] = j
                    break
            for row in ws.iter_rows(min_row=hdr + 1, values_only=True):
                if not row or not row[0]: continue
                sp = str(row[0] or "").replace(".", "").replace(" ", "")
                if not sp.startswith("4011"): continue
                try:
                    qty = float(str(row[cols.get("qty", 0)] or "").replace(",", "")) or 0
                    cif = float(str(row[cols.get("cif", 0)] or "").replace(",", "")) or 0
                except Exception: continue
                if qty <= 0 or is_spurious(sp, qty, cif, row[cols.get("imp", 0)], row[cols.get("desc", 0)]): continue
                bi = normalize_name(row[cols.get("imp", 0)]); be = canon_exp(str(row[cols.get("exp", 0)] or "").strip())
                vol_imp[bi] = vol_imp.get(bi, 0) + qty; vol_exp[be] = vol_exp.get(be, 0) + qty
            wb.close()
    return cluster_aliases(vol_imp), cluster_aliases(vol_exp), vol_imp, vol_exp

def write_alias_report(path, ai, ae, vi, ve):
    def block(title, alias, vol):
        grupos = {}
        for n, t in alias.items(): grupos.setdefault(t, []).append(n)
        lines = ["== %s: %d nombres fusionados en %d identidades ==" % (title, len(alias), len(grupos))]
        for t, ms in sorted(grupos.items(), key=lambda kv: -(vol.get(kv[0], 0) + sum(vol.get(m, 0) for m in kv[1]))):
            tot = vol.get(t, 0) + sum(vol.get(m, 0) for m in ms)
            lines.append("%10s  %s" % (format(int(tot), ","), t))
            for m in sorted(ms, key=lambda m: -vol.get(m, 0)):
                lines.append("              <- %s (%s)" % (m, format(int(vol.get(m, 0)), ",")))
        return lines
    with open(path, "w", encoding="utf-8") as f:
        f.write("\n".join(block("IMPORTADORES", ai, vi) + [""] + block("EXPORTADORES / MARCAS", ae, ve)) + "\n")

def normalize_name(raw):
    key = re.sub(r'\s+', ' ', str(raw or '').strip().upper())
    if key in NAME_MAP: return NAME_MAP[key]
    for k, v in NAME_MAP.items():
        if key.replace(',','').replace('.','') == k.replace(',','').replace('.',''):
            return v
    base = smart_name(raw)
    return ALIAS_IMP.get(base, base)

def normalize_country(raw):
    key = str(raw or '').strip().upper()
    return COUNTRY_MAP.get(key, str(raw or '').strip().title())

def classify_tipo(sp):
    sp = str(sp or '').replace('.','').replace(' ','')
    if sp.startswith('401110'): return 'Turismo / Racing'
    if sp.startswith('401120'): return 'Autobús / Camión'
    if sp.startswith('401130'): return 'Aeronaves'
    if sp.startswith('401140'): return 'Motocicletas'
    if sp.startswith('401150'): return 'Bicicletas'
    if sp.startswith('401160'): return 'Motocicletas'
    if sp.startswith('40117'):  return 'Agrícola / Forestal'
    if sp.startswith('40118011') or sp.startswith('40118091'): return 'Montacargas'
    if sp.startswith('40118012'): return 'Otros'
    if sp.startswith('40118'): return 'Construcción / Industrial'
    if sp.startswith('40119010'): return 'Construcción / Industrial'
    if sp.startswith('40119'): return 'Otros'
    return 'Otros'

def is_spurious(sp_clean, qty, cif, imp_raw, desc_raw):
    desc = str(desc_raw or '').upper(); imp = str(imp_raw or '').upper()
    if 'BAC INTERNATIONAL' in imp and 'TICKET' in desc: return True
    if 'TICKET' in desc and 'AWB' in desc: return True
    avg = cif/qty if qty>0 else 0
    if (sp_clean.startswith('401140') or sp_clean.startswith('401160')) and avg<1.50 and qty>100: return True
    if sp_clean.startswith('40119') and avg<1.00 and qty>50: return True
    return False

results = {}

print("Pre-pasada: agrupando variantes de nombre en todos los archivos...")
ALIAS_IMP, ALIAS_EXP, _vi, _ve = build_alias_maps()
_rep = os.path.join(DATA_DIR, 'nombres_fusionados.txt')
write_alias_report(_rep, ALIAS_IMP, ALIAS_EXP, _vi, _ve)
print("  importadores: %d nombres -> %d fusionados | exportadores: %d nombres -> %d fusionados | informe: %s"
      % (len(_vi), len(ALIAS_IMP), len(_ve), len(ALIAS_EXP), _rep))

for year, paths in sorted(FILES.items()):
    if isinstance(paths, str): paths = [paths]
    print(f"\n{'='*50} {year}  ({len(paths)} archivo(s))")
    LL = 'Ling Long'
    OPP_SEGS = {'Turismo / Racing','Autobús / Camión','Montacargas','Construcción / Industrial','Agrícola / Forestal','Motocicletas'}

    # Base aggregations (same as before)
    imp_qty = defaultdict(float); imp_cif = defaultdict(float)
    monthly_qty = defaultdict(lambda: defaultdict(float))
    monthly_cif_ll = defaultdict(float)
    monthly_mkt_qty = [0]*12; monthly_mkt_cif = [0]*12
    exp_qty = defaultdict(float); exp_cif = defaultdict(float)
    tipo_qty = defaultdict(float); tipo_cif = defaultdict(float)
    country_qty = defaultdict(float)
    ll_sub = defaultdict(lambda: {'qty':0,'cif':0})
    hk_cli = defaultdict(lambda: {'qty':0,'cif':0})
    ll_sup_d = defaultdict(lambda: {'qty':0,'cif':0})
    seg_top_raw = defaultdict(lambda: defaultdict(lambda: {'qty':0,'cif':0}))
    total_qty = 0.0; total_cif = 0.0

    # NEW: cross-tab for profiles
    # imp_exp[imp][exp] = [qty, cif]
    # imp_seg[imp][seg] = [qty, cif]
    # imp_monthly[imp][month] = qty
    # exp_imp[exp][imp] = [qty, cif]
    # exp_seg[exp][seg] = [qty, cif]
    # exp_monthly[exp][month] = qty
    # seg_exp[seg][exp] = [qty, cif]
    imp_exp = defaultdict(lambda: defaultdict(lambda: [0.0, 0.0]))
    imp_seg = defaultdict(lambda: defaultdict(lambda: [0.0, 0.0]))
    imp_monthly_d = defaultdict(lambda: [0.0]*12)
    exp_imp = defaultdict(lambda: defaultdict(lambda: [0.0, 0.0]))
    exp_seg = defaultdict(lambda: defaultdict(lambda: [0.0, 0.0]))
    exp_monthly_d = defaultdict(lambda: [0.0]*12)
    seg_exp_d = defaultdict(lambda: defaultdict(lambda: [0.0, 0.0]))
    seg_monthly_d = defaultdict(lambda: [0.0]*12)   # NUEVO: mensual por segmento

    for path in paths:
        wb = openpyxl.load_workbook(path, read_only=True, data_only=True)
        ws = wb.active

        hdr_row, cols = None, {}
        for i, row in enumerate(ws.iter_rows(values_only=True)):
            rs = [str(c).upper() if c else '' for c in row]
            if any('QTY' in c for c in rs) and any('IMPORT' in c for c in rs):
                hdr_row = i + 1
                for j, h in enumerate(rs):
                    if 'QTY' in h and 'qty' not in cols: cols['qty'] = j
                    if ('IMPORT' in h or 'CONSIG' in h) and 'imp' not in cols: cols['imp'] = j
                    if ('SUBPART' in h or ('PARTIDA' in h and 'ARANCELARIA' in h)) and 'sp' not in cols: cols['sp'] = j
                    if 'CIF TOT' in h and 'cif' not in cols: cols['cif'] = j
                    if 'CIF' in h and 'cif' not in cols: cols['cif'] = j
                    if ('EMBARCADOR' in h or 'EXPORTADOR' in h) and 'exp' not in cols: cols['exp'] = j
                    if 'PAIS' in h and 'ORIGEN' in h and 'country' not in cols: cols['country'] = j
                    if 'FECHA' in h and 'fecha' not in cols: cols['fecha'] = j
                    if 'DESCRIP' in h and 'COMERCIAL' in h and 'desc' not in cols: cols['desc'] = j
                break

        def parse_month(row):
            fv = row[cols.get('fecha', 0)]
            try:
                if isinstance(fv, (int, float)):
                    from openpyxl.utils.datetime import from_excel
                    return from_excel(fv).month - 1
            except: pass
            try: return datetime.strptime(str(fv)[:10], '%d/%m/%Y').month - 1
            except: pass
            try: return datetime.strptime(str(fv)[:10], '%Y-%m-%d').month - 1
            except: return None

        for row in ws.iter_rows(min_row=hdr_row+1, values_only=True):
            if not row or not row[0]: continue
            sp = str(row[cols.get('sp',0)] or '').replace('.','').replace(' ','')
            if not sp.startswith('4011'): continue
            try:
                qty = float(str(row[cols.get('qty',0)] or '').replace(',','')) or 0
                cif = float(str(row[cols.get('cif',0)] or '').replace(',','')) or 0
            except: qty, cif = 0, 0
            if qty <= 0: continue

            imp_raw = row[cols.get('imp',0)]
            exp_raw = row[cols.get('exp',0)]
            country_raw = row[cols.get('country',0)]
            desc_raw = row[cols.get('desc',0)]

            if is_spurious(sp, qty, cif, imp_raw, desc_raw): continue

            imp = normalize_name(imp_raw)
            exp = canon_exp(str(exp_raw or '').strip())
            country = normalize_country(country_raw)
            tipo = classify_tipo(sp)
            month = parse_month(row)

            imp_qty[imp] += qty; imp_cif[imp] += cif
            if month is not None:
                monthly_qty[imp][month] += qty
                monthly_mkt_qty[month] += qty
                monthly_mkt_cif[month] += cif
                imp_monthly_d[imp][month] += qty
                exp_monthly_d[exp][month] += qty
                seg_monthly_d[tipo][month] += qty
            exp_qty[exp] += qty; exp_cif[exp] += cif
            tipo_qty[tipo] += qty; tipo_cif[tipo] += cif
            country_qty[country] += qty
            total_qty += qty; total_cif += cif

            # Cross-tab
            imp_exp[imp][exp][0] += qty; imp_exp[imp][exp][1] += cif
            imp_seg[imp][tipo][0] += qty; imp_seg[imp][tipo][1] += cif
            exp_imp[exp][imp][0] += qty; exp_imp[exp][imp][1] += cif
            exp_seg[exp][tipo][0] += qty; exp_seg[exp][tipo][1] += cif
            seg_exp_d[tipo][exp][0] += qty; seg_exp_d[tipo][exp][1] += cif

            if imp == LL:
                ll_sub[tipo]['qty'] += qty; ll_sub[tipo]['cif'] += cif
                if month is not None: monthly_cif_ll[month] += cif
            if 'TIANCHENG' in str(exp_raw or '').upper():
                hk_cli[imp]['qty'] += qty; hk_cli[imp]['cif'] += cif
            if imp == LL:
                ll_sup_d[exp]['qty'] += qty; ll_sup_d[exp]['cif'] += cif
            if tipo in OPP_SEGS:
                seg_top_raw[tipo][imp]['qty'] += qty
                seg_top_raw[tipo][imp]['cif'] += cif

        wb.close()

    top_imp = sorted(imp_qty.items(), key=lambda x: -x[1])
    ll_qty = imp_qty.get(LL, 0); ll_cif = imp_cif.get(LL, 0)
    ll_rank = next((i+1 for i,(n,_) in enumerate(top_imp) if n==LL), 0)
    top10 = [n for n,_ in top_imp[:10]]
    ll_monthly_qty = [monthly_qty[LL].get(m,0) for m in range(12)]
    ll_monthly_cif = [monthly_cif_ll.get(m,0) for m in range(12)]

    seg_top = {}
    for tipo, imps in seg_top_raw.items():
        seg_top[tipo] = [[n,v['qty'],v['cif']] for n,v in sorted(imps.items(),key=lambda x:-x[1]['qty'])[:8]]

    # Build imp_profiles for top 30 importers
    top30_imp = [n for n,_ in top_imp[:30]]
    imp_profiles = {}
    for imp in top30_imp:
        top_exp_for_imp = sorted(imp_exp[imp].items(), key=lambda x:-x[1][0])[:10]
        imp_profiles[imp] = {
            'total_qty': imp_qty[imp],
            'total_cif': imp_cif[imp],
            'top_exp': [[n,v[0],v[1]] for n,v in top_exp_for_imp],
            'seg': {seg:[v[0],v[1]] for seg,v in imp_seg[imp].items()},
            'monthly': list(imp_monthly_d[imp]),
        }

    # Build exp_profiles for top 30 exporters
    top_exp_list = sorted(exp_qty.items(), key=lambda x:-x[1])
    top30_exp = [n for n,_ in top_exp_list[:30]]
    exp_profiles = {}
    for exp in top30_exp:
        top_imp_for_exp = sorted(exp_imp[exp].items(), key=lambda x:-x[1][0])[:10]
        exp_profiles[exp] = {
            'total_qty': exp_qty[exp],
            'total_cif': exp_cif[exp],
            'top_imp': [[n,v[0],v[1]] for n,v in top_imp_for_exp],
            'seg': {seg:[v[0],v[1]] for seg,v in exp_seg[exp].items()},
            'monthly': list(exp_monthly_d[exp]),
        }

    # seg_exp: top exporters per segment
    seg_exp_out = {}
    for seg, exps in seg_exp_d.items():
        seg_exp_out[seg] = [[n,v[0],v[1]] for n,v in sorted(exps.items(),key=lambda x:-x[1][0])[:10]]

    yr_result = {
        'total_qty': total_qty, 'total_cif': total_cif,
        'll_qty': ll_qty, 'll_cif': ll_cif, 'll_rank': ll_rank, 'll_name': LL,
        'top_imp':  [[n, imp_qty[n], imp_cif[n]] for n,_ in top_imp[:20]],
        'top10': top10,
        'monthly_top10': {n:[monthly_qty[n].get(m,0) for m in range(12)] for n in top10},
        'monthly_mkt_qty': monthly_mkt_qty, 'monthly_mkt_cif': monthly_mkt_cif,
        'monthly_ll_qty': ll_monthly_qty, 'monthly_ll_cif': ll_monthly_cif,
        'top_exp':  [[n, exp_qty[n], exp_cif[n]] for n,_ in top_exp_list[:20]],
        'tipo_qty': dict(tipo_qty), 'tipo_cif': dict(tipo_cif),
        'top_country': [[n,v] for n,v in sorted(country_qty.items(),key=lambda x:-x[1])[:12]],
        'll_sub': {k:dict(v) for k,v in ll_sub.items()},
        'hk_clients': [[n,v['qty'],v['cif']] for n,v in sorted(hk_cli.items(),key=lambda x:-x[1]['qty'])],
        'll_sup': [[n,v['qty'],v['cif']] for n,v in sorted(ll_sup_d.items(),key=lambda x:-x[1]['qty'])],
        'seg_mkt': {t:{'qty':tipo_qty[t],'cif':tipo_cif[t]} for t in tipo_qty},
        'seg_ll':  {k:dict(v) for k,v in ll_sub.items()},
        'seg_top': seg_top,
        'imp_profiles': imp_profiles,
        'exp_profiles': exp_profiles,
        'seg_exp': seg_exp_out,
        'seg_monthly': {k: list(v) for k, v in seg_monthly_d.items()},
    }

    if year in PARTIAL_YEARS:
        yr_result['partial'] = True
        yr_result['partial_label'] = PARTIAL_YEARS[year]

    results[str(year)] = yr_result
    print(f"  Total: {total_qty:,.0f} uds | LL #{ll_rank} ({ll_qty:,.0f} uds) | {len(imp_profiles)} imp profiles | {len(exp_profiles)} exp profiles")

out = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'years_data_v8.json')
with open(out, 'w', encoding='utf-8') as f:
    json.dump(results, f, ensure_ascii=False, indent=2)
print(f"\nSaved -> {out}")
