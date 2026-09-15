import streamlit as st
import numpy as np
import pandas as pd
from scipy.stats import poisson
import difflib

# Mobil öncelikli sayfa ayarı ve Sol Menü Kapalı / Gizli
st.set_page_config(
    page_title="Poisson Tahmin", 
    page_icon="⚽", 
    layout="wide",
    initial_sidebar_state="collapsed"
)

# Mobil uyumlu CSS
st.markdown("""
<style>
    .block-container {
        padding-top: 1rem !important;
        padding-bottom: 2rem !important;
        padding-left: 0.8rem !important;
        padding-right: 0.8rem !important;
    }
    div[data-testid="stMetric"] {
        background-color: rgba(128, 128, 128, 0.08);
        border: 1px solid rgba(128, 128, 128, 0.2);
        padding: 8px 12px;
        border-radius: 8px;
        margin-bottom: 6px;
    }
    div[data-testid="stMetricLabel"] p {
        font-size: 0.85rem !important;
        font-weight: 600;
    }
    div[data-testid="stMetricValue"] div {
        font-size: 1.25rem !important;
    }
    div.stButton > button {
        height: 3em;
        font-size: 1rem;
        font-weight: bold;
    }
    .kombine-box {
        background: linear-gradient(135deg, #1b4d3e 0%, #0d2818 100%);
        border: 1px solid #2ecc71;
        border-radius: 12px;
        padding: 14px;
        margin-bottom: 15px;
        color: white;
    }
</style>
""", unsafe_allow_html=True)

TAKIM_PROFILLERI = {
    # ==================== TRENDYOL SÜPER LİG ====================
    "galatasaray": {"hucum": 2.25, "savunma": 1.00, "seviye": 1.40},
    "fenerbahce": {"hucum": 2.20, "savunma": 1.00, "seviye": 1.35},
    "besiktas": {"hucum": 1.75, "savunma": 1.15, "seviye": 1.20},
    "trabzonspor": {"hucum": 1.60, "savunma": 1.15, "seviye": 1.10},
    "basaksehir": {"hucum": 1.45, "savunma": 1.40, "seviye": 0.95},
    "amed": {"hucum": 1.60, "savunma": 1.15, "seviye": 1.10},
    "samsunspor": {"hucum": 1.45, "savunma": 1.10, "seviye": 1.10},
    "eyupspor": {"hucum": 1.40, "savunma": 1.20, "seviye": 1.00},
    "goztepe": {"hucum": 1.35, "savunma": 1.15, "seviye": 1.00},
    "sivasspor": {"hucum": 1.30, "savunma": 1.35, "seviye": 0.90},
    "antalyaspor": {"hucum": 1.25, "savunma": 1.35, "seviye": 0.90},
    "alanyaspor": {"hucum": 1.25, "savunma": 1.30, "seviye": 0.90},
    "kasimpasa": {"hucum": 1.45, "savunma": 1.50, "seviye": 0.95},
    "rizespor": {"hucum": 1.25, "savunma": 1.35, "seviye": 0.90},
    "gaziantep": {"hucum": 1.20, "savunma": 1.40, "seviye": 0.85},
    "konyaspor": {"hucum": 1.15, "savunma": 1.35, "seviye": 0.85},
    "kayserispor": {"hucum": 1.15, "savunma": 1.45, "seviye": 0.85},
    "bodrum fk": {"hucum": 1.00, "savunma": 1.30, "seviye": 0.80},
    "hatayspor": {"hucum": 1.05, "savunma": 1.45, "seviye": 0.80},
    "adana demirspor": {"hucum": 1.00, "savunma": 1.70, "seviye": 0.70},

    # ==================== TÜRKİYE 1. LİG ====================
    "kocaelispor": {"hucum": 1.25, "savunma": 1.20, "seviye": 0.80},
    "fatih karagumruk": {"hucum": 1.30, "savunma": 1.25, "seviye": 0.80},
    "ankaragucu": {"hucum": 1.30, "savunma": 1.25, "seviye": 0.80},
    "istanbulspor": {"hucum": 1.20, "savunma": 1.30, "seviye": 0.75},
    "pendikspor": {"hucum": 1.20, "savunma": 1.30, "seviye": 0.75},
    "sakaryaspor": {"hucum": 1.15, "savunma": 1.25, "seviye": 0.75},
    "bandirmaspor": {"hucum": 1.20, "savunma": 1.25, "seviye": 0.75},
    "corum fk": {"hucum": 1.20, "savunma": 1.25, "seviye": 0.75},
    "erzurumspor": {"hucum": 1.15, "savunma": 1.20, "seviye": 0.75},
    "boluspor": {"hucum": 1.10, "savunma": 1.20, "seviye": 0.70},
    "umraniyespor": {"hucum": 1.15, "savunma": 1.30, "seviye": 0.70},
    "manisa fk": {"hucum": 1.15, "savunma": 1.30, "seviye": 0.70},
    "genclerbirligi": {"hucum": 1.15, "savunma": 1.25, "seviye": 0.70},
    "keciorengucu": {"hucum": 1.10, "savunma": 1.30, "seviye": 0.70},
    "igdir fk": {"hucum": 1.15, "savunma": 1.25, "seviye": 0.70},
    "esenler erokspor": {"hucum": 1.15, "savunma": 1.35, "seviye": 0.70},
    "sanliurfaspor": {"hucum": 1.05, "savunma": 1.35, "seviye": 0.65},
    "adanaspor": {"hucum": 1.00, "savunma": 1.45, "seviye": 0.65},
    "yeni malatyaspor": {"hucum": 0.70, "savunma": 1.90, "seviye": 0.50},

    # ==================== PREMIER LEAGUE & İNGİLTERE ====================
    "man city": {"hucum": 2.25, "savunma": 0.95, "seviye": 1.45},
    "liverpool": {"hucum": 2.15, "savunma": 1.00, "seviye": 1.40},
    "arsenal": {"hucum": 2.05, "savunma": 0.90, "seviye": 1.40},
    "chelsea": {"hucum": 1.85, "savunma": 1.25, "seviye": 1.20},
    "aston villa": {"hucum": 1.80, "savunma": 1.25, "seviye": 1.20},
    "tottenham": {"hucum": 1.90, "savunma": 1.35, "seviye": 1.20},
    "newcastle": {"hucum": 1.75, "savunma": 1.20, "seviye": 1.20},
    "man united": {"hucum": 1.65, "savunma": 1.30, "seviye": 1.15},
    "brighton": {"hucum": 1.70, "savunma": 1.30, "seviye": 1.15},
    "nottingham forest": {"hucum": 1.35, "savunma": 1.15, "seviye": 1.05},
    "fulham": {"hucum": 1.35, "savunma": 1.25, "seviye": 1.05},
    "brentford": {"hucum": 1.55, "savunma": 1.40, "seviye": 1.05},
    "bournemouth": {"hucum": 1.45, "savunma": 1.35, "seviye": 1.05},
    "west ham": {"hucum": 1.40, "savunma": 1.45, "seviye": 1.05},
    "crystal palace": {"hucum": 1.30, "savunma": 1.25, "seviye": 1.00},
    "everton": {"hucum": 1.20, "savunma": 1.25, "seviye": 1.00},
    "wolves": {"hucum": 1.30, "savunma": 1.55, "seviye": 0.95},
    "leicester": {"hucum": 1.25, "savunma": 1.55, "seviye": 0.90},
    "ipswich": {"hucum": 1.15, "savunma": 1.60, "seviye": 0.85},
    "southampton": {"hucum": 1.10, "savunma": 1.65, "seviye": 0.85},
    "leeds": {"hucum": 1.55, "savunma": 1.35, "seviye": 1.05},
    "middlesbrough": {"hucum": 1.55, "savunma": 1.25, "seviye": 1.05},
    "millwall": {"hucum": 1.25, "savunma": 1.20, "seviye": 0.95},

    # ==================== LA LIGA & DİĞER İSPANYA ====================
    "real madrid": {"hucum": 2.35, "savunma": 1.00, "seviye": 1.45},
    "barcelona": {"hucum": 2.45, "savunma": 1.10, "seviye": 1.45},
    "atletico madrid": {"hucum": 1.75, "savunma": 0.95, "seviye": 1.35},
    "athletic bilbao": {"hucum": 1.65, "savunma": 1.05, "seviye": 1.20},
    "real sociedad": {"hucum": 1.45, "savunma": 1.05, "seviye": 1.15},
    "villareal": {"hucum": 1.85, "savunma": 1.35, "seviye": 1.15},
    "real betis": {"hucum": 1.45, "savunma": 1.15, "seviye": 1.15},
    "girona": {"hucum": 1.65, "savunma": 1.30, "seviye": 1.15},
    "mallorca": {"hucum": 1.15, "savunma": 1.10, "seviye": 1.05},
    "osasuna": {"hucum": 1.30, "savunma": 1.30, "seviye": 1.00},
    "celta vigo": {"hucum": 1.50, "savunma": 1.45, "seviye": 1.00},
    "sevilla": {"hucum": 1.35, "savunma": 1.30, "seviye": 1.00},
    "rayo vallecano": {"hucum": 1.20, "savunma": 1.25, "seviye": 0.95},
    "alaves": {"hucum": 1.20, "savunma": 1.35, "seviye": 0.95},
    "getafe": {"hucum": 0.95, "savunma": 1.10, "seviye": 0.95},
    "espanyol": {"hucum": 1.15, "savunma": 1.40, "seviye": 0.90},
    "las palmas": {"hucum": 1.20, "savunma": 1.45, "seviye": 0.90},
    "leganes": {"hucum": 1.05, "savunma": 1.25, "seviye": 0.85},
    "valladolid": {"hucum": 1.00, "savunma": 1.60, "seviye": 0.85},
    "valencia": {"hucum": 1.10, "savunma": 1.45, "seviye": 0.90},
    "malaga": {"hucum": 1.25, "savunma": 1.25, "seviye": 0.80},
    "elche": {"hucum": 1.10, "savunma": 1.30, "seviye": 0.85},

    # ==================== SERIE A ====================
    "inter": {"hucum": 2.20, "savunma": 0.95, "seviye": 1.40},
    "atalanta": {"hucum": 2.15, "savunma": 1.15, "seviye": 1.30},
    "juventus": {"hucum": 1.70, "savunma": 1.10, "seviye": 1.20},
    "napoli": {"hucum": 1.75, "savunma": 0.95, "seviye": 1.30},
    "milan": {"hucum": 1.85, "savunma": 1.25, "seviye": 1.25},
    "lazio": {"hucum": 1.80, "savunma": 1.25, "seviye": 1.20},
    "fiorentina": {"hucum": 1.75, "savunma": 1.20, "seviye": 1.20},
    "roma": {"hucum": 1.60, "savunma": 1.20, "seviye": 1.15},
    "bologna": {"hucum": 1.45, "savunma": 1.15, "seviye": 1.15},
    "torino": {"hucum": 1.25, "savunma": 1.20, "seviye": 1.00},
    "sassuolo": {"hucum": 1.40, "savunma": 1.45, "seviye": 0.90},
    "udinese": {"hucum": 1.30, "savunma": 1.35, "seviye": 0.95},
    "empoli": {"hucum": 1.05, "savunma": 1.25, "seviye": 0.90},
    "parma": {"hucum": 1.35, "savunma": 1.45, "seviye": 0.90},
    "como": {"hucum": 1.25, "savunma": 1.40, "seviye": 0.90},
    "verona": {"hucum": 1.25, "savunma": 1.55, "seviye": 0.90},
    "cagliari": {"hucum": 1.20, "savunma": 1.45, "seviye": 0.90},
    "genoa": {"hucum": 1.15, "savunma": 1.35, "seviye": 0.90},
    "lecce": {"hucum": 1.00, "savunma": 1.40, "seviye": 0.85},
    "monza": {"hucum": 1.05, "savunma": 1.35, "seviye": 0.85},
    "venezia": {"hucum": 1.05, "savunma": 1.55, "seviye": 0.80},
    "sudtirol": {"hucum": 1.10, "savunma": 1.35, "seviye": 0.80},
    "pisa": {"hucum": 1.25, "savunma": 1.30, "seviye": 0.85},

    # ==================== BUNDESLIGA ====================
    "bayern munih": {"hucum": 2.55, "savunma": 1.05, "seviye": 1.45},
    "bayer leverkusen": {"hucum": 2.30, "savunma": 1.15, "seviye": 1.35},
    "dortmund": {"hucum": 2.15, "savunma": 1.25, "seviye": 1.30},
    "leipzig": {"hucum": 1.95, "savunma": 1.10, "seviye": 1.30},
    "eintracht frankfurt": {"hucum": 2.05, "savunma": 1.30, "seviye": 1.20},
    "stuttgart": {"hucum": 1.90, "savunma": 1.30, "seviye": 1.20},
    "freiburg": {"hucum": 1.55, "savunma": 1.25, "seviye": 1.10},
    "union berlin": {"hucum": 1.25, "savunma": 1.15, "seviye": 1.05},
    "werder bremen": {"hucum": 1.50, "savunma": 1.40, "seviye": 1.05},
    "borussia monchengladbach": {"hucum": 1.55, "savunma": 1.40, "seviye": 1.05},
    "augsburg": {"hucum": 1.40, "savunma": 1.45, "seviye": 1.00},
    "wolfsburg": {"hucum": 1.50, "savunma": 1.45, "seviye": 1.00},
    "mainz": {"hucum": 1.45, "savunma": 1.35, "seviye": 1.00},
    "heidenheim": {"hucum": 1.35, "savunma": 1.40, "seviye": 0.95},
    "hoffenheim": {"hucum": 1.55, "savunma": 1.60, "seviye": 0.95},
    "st pauli": {"hucum": 1.05, "savunma": 1.30, "seviye": 0.85},
    "holstein kiel": {"hucum": 1.25, "savunma": 1.75, "seviye": 0.80},
    "bochum": {"hucum": 1.15, "savunma": 1.75, "seviye": 0.80},

    # ==================== LIGUE 1 ====================
    "psg": {"hucum": 2.10, "savunma": 1.15, "seviye": 1.30},
    "monaco": {"hucum": 1.95, "savunma": 1.15, "seviye": 1.25},
    "marsilya": {"hucum": 1.95, "savunma": 1.25, "seviye": 1.25},
    "lille": {"hucum": 1.70, "savunma": 1.10, "seviye": 1.20},
    "lyon": {"hucum": 1.75, "savunma": 1.30, "seviye": 1.15},
    "lens": {"hucum": 1.45, "savunma": 1.05, "seviye": 1.15},
    "nice": {"hucum": 1.60, "savunma": 1.15, "seviye": 1.15},
    "brest": {"hucum": 1.50, "savunma": 1.25, "seviye": 1.10},
    "rennes": {"hucum": 1.45, "savunma": 1.30, "seviye": 1.05},
    "strasbourg": {"hucum": 1.55, "savunma": 1.45, "seviye": 1.00},
    "reims": {"hucum": 1.40, "savunma": 1.35, "seviye": 1.00},
    "toulouse": {"hucum": 1.35, "savunma": 1.25, "seviye": 0.95},
    "auxerre": {"hucum": 1.40, "savunma": 1.45, "seviye": 0.95},
    "nantes": {"hucum": 1.25, "savunma": 1.35, "seviye": 0.90},
    "angers": {"hucum": 1.20, "savunma": 1.40, "seviye": 0.85},
    "saint-etienne": {"hucum": 1.15, "savunma": 1.65, "seviye": 0.85},
    "le havre": {"hucum": 1.05, "savunma": 1.45, "seviye": 0.85},
    "montpellier": {"hucum": 1.25, "savunma": 1.75, "seviye": 0.80},

    # ==================== DİĞER LİGLER & DİĞERLERİ ====================
    "psv": {"hucum": 2.50, "savunma": 1.15, "seviye": 1.35},
    "sparta rotterdam": {"hucum": 1.15, "savunma": 1.55, "seviye": 0.85},
    "tenerife": {"hucum": 0.85, "savunma": 1.45, "seviye": 0.75},
    "elversberg": {"hucum": 1.25, "savunma": 1.35, "seviye": 0.80},
    "troyes": {"hucum": 1.10, "savunma": 1.45, "seviye": 0.75},
    "sparta prag": {"hucum": 1.60, "savunma": 1.15, "seviye": 1.05},
    "slavia prag": {"hucum": 1.65, "savunma": 1.10, "seviye": 1.05},
    "shakhtar donetsk": {"hucum": 1.75, "savunma": 1.10, "seviye": 1.10},
    "aek atina": {"hucum": 1.75, "savunma": 1.10, "seviye": 1.20},
    "panathinaikos": {"hucum": 1.70, "savunma": 1.10, "seviye": 1.20},
    "djurgardens": {"hucum": 1.65, "savunma": 1.10, "seviye": 1.15},
    "gais": {"hucum": 1.30, "savunma": 1.35, "seviye": 0.90},
    "vancouver whitecaps": {"hucum": 1.70, "savunma": 1.20, "seviye": 1.10},
    "austin fc": {"hucum": 1.35, "savunma": 1.35, "seviye": 0.95},
    "bodo glimt": {"hucum": 2.10, "savunma": 1.00, "seviye": 1.30},
    "sandefjord": {"hucum": 1.20, "savunma": 1.60, "seviye": 0.85},
    "san diego fc": {"hucum": 1.50, "savunma": 1.30, "seviye": 1.00},
    "philadelphia union": {"hucum": 1.60, "savunma": 1.25, "seviye": 1.10},
    "braga": {"hucum": 1.80, "savunma": 1.10, "seviye": 1.20},
    "estoril praia": {"hucum": 1.30, "savunma": 1.40, "seviye": 0.90},
    "falkrik": {"hucum": 1.35, "savunma": 1.25, "seviye": 0.85},
    "hearts": {"hucum": 1.50, "savunma": 1.20, "seviye": 1.05},
    "grasshoppers": {"hucum": 1.30, "savunma": 1.40, "seviye": 0.95},
    "sion": {"hucum": 1.35, "savunma": 1.35, "seviye": 0.95}
}

TAKMA_ADLAR = {
    "fb": "fenerbahce", "fener": "fenerbahce",
    "gs": "galatasaray", "cimbom": "galatasaray",
    "bjk": "besiktas", "besik": "besiktas",
    "ts": "trabzonspor", "trabzon": "trabzonspor",
    "ibfk": "basaksehir", "basak": "basaksehir",
    "amed": "amed", "amedspor": "amed",
    "samsun": "samsunspor", "eyup": "eyupspor",
    "gozgoz": "goztepe", "sivas": "sivasspor",
    "antalya": "antalyaspor", "alanya": "alanyaspor",
    "pasa": "kasimpasa", "rize": "rizespor",
    "antep": "gaziantep", "gfk": "gaziantep",
    "konya": "konyaspor", "kayseri": "kayserispor",
    "bodrum": "bodrum fk", "hatay": "hatayspor",
    "adana": "adana demirspor", "ads": "adana demirspor",
    "kocaeli": "kocaelispor", "istanbul": "istanbulspor",
    "karagumruk": "fatih karagumruk", "ankaragucu": "ankaragucu",
    "sakarya": "sakaryaspor", "bandirma": "bandirmaspor",
    "corum": "corum fk", "erzurum": "erzurumspor",
    "bolu": "boluspor", "umraniye": "umraniyespor",
    "manisa": "manisa fk", "gencler": "genclerbirligi",
    "keciorengucu": "keciorengucu", "igdir": "igdir fk",
    "erokspor": "esenler erokspor", "urfaspor": "sanliurfaspor",
    "malatya": "yeni malatyaspor",
    "city": "man city", "manc": "man city", "manchester city": "man city",
    "united": "man united", "manu": "man united", "manchester united": "man united",
    "pool": "liverpool", "villa": "aston villa", "palace": "crystal palace",
    "spurs": "tottenham", "newcastle united": "newcastle",
    "wolves": "wolves", "wolverhampton": "wolves",
    "nottingham": "nottingham forest", "forest": "nottingham forest",
    "leicester city": "leicester",
    "middlesbrough": "middlesbrough", "boro": "middlesbrough",
    "millwall": "millwall",
    "leeds": "leeds", "leeds united": "leeds",
    "real": "real madrid", "barca": "barcelona", "barça": "barcelona",
    "atletico": "atletico madrid", "atm": "atletico madrid",
    "sociedad": "real sociedad", "socciedad": "real sociedad",
    "bilbao": "athletic bilbao", "betis": "real betis", "celta": "celta vigo",
    "rayo": "rayo vallecano", "espanyol": "espanyol", "tenerife": "tenerife",
    "malaga": "malaga",
    "elche": "elche",
    "alaves": "alaves",
    "juve": "juventus", "inter milan": "inter", "ac milan": "milan",
    "viola": "fiorentina", "toro": "torino", "hellas": "verona",
    "hellas verona": "verona", "sassuolo": "sassuolo", "sas": "sassuolo",
    "pisa": "pisa",
    "sudtirol": "sudtirol", "sudtriol": "sudtirol",
    "udinesse": "udinese", "udinese": "udinese",
    "bayern": "bayern munih", "munih": "bayern munih", "fc bayern": "bayern munih",
    "leverkusen": "bayer leverkusen", "bayer": "bayer leverkusen",
    "bvb": "dortmund", "borussia dortmund": "dortmund",
    "rbl": "leipzig", "rb leipzig": "leipzig",
    "frankfurt": "eintracht frankfurt", "bremen": "werder bremen",
    "gladbach": "borussia monchengladbach", "monchengladbach": "borussia monchengladbach",
    "elversberg": "elversberg", "elvers": "elversberg",
    "psg": "psg", "paris": "psg", "paris saint germain": "psg",
    "om": "marsilya", "ol": "lyon", "asm": "monaco",
    "st etienne": "saint-etienne", "saint etienne": "saint-etienne",
    "troyes": "troyes",
    "psv": "psv", "sparta": "sparta rotterdam", "rotterdam": "sparta rotterdam",
    "prag": "sparta prag", "sparta prag": "sparta prag", "slavia prag": "slavia prag",
    "shakhtar": "shakhtar donetsk", "shakhtar donetsk": "shakhtar donetsk",
    "aek": "aek atina", "aek atina": "aek atina", "athena": "aek atina",
    "pao": "panathinaikos", "panathinaikos": "panathinaikos",
    "falkirk": "falkrik", "falkrik": "falkrik",
    "hearts": "hearts",
    "grasshoppers": "grasshoppers", "gc": "grasshoppers",
    "sion": "sion",
    "djurgardens": "djurgardens", "gais": "gais",
    "vancouver": "vancouver whitecaps", "austin": "austin fc",
    "bodo": "bodo glimt", "sandefjord": "sandefjord",
    "san diego": "san diego fc", "philadelphia": "philadelphia union",
    "braga": "braga", "estoril": "estoril praia"
}

def takim_bul(girdi):
    g = girdi.strip().lower().replace("ı", "i").replace("ğ", "g").replace("ü", "u").replace("ş", "s").replace("ö", "o").replace("ç", "c")
    if g in TAKIM_PROFILLERI: return g
    if g in TAKMA_ADLAR: return TAKMA_ADLAR[g]
    for k in TAKIM_PROFILLERI:
        if g in k or k in g: return k
    yakin = difflib.get_close_matches(g, list(TAKIM_PROFILLERI.keys()) + list(TAKMA_ADLAR.keys()), n=1, cutoff=0.55)
    if yakin:
        return TAKMA_ADLAR.get(yakin[0], yakin[0])
    return None

def mac_hesapla(ev_key, dep_key):
    ep = TAKIM_PROFILLERI[ev_key]
    dp = TAKIM_PROFILLERI[dep_key]

    exp_h = (ep["hucum"] * dp["savunma"] / 1.35) * 1.10
    exp_a = (dp["hucum"] * ep["savunma"] / 1.35) * 0.90

    seviye = (ep["seviye"] / dp["seviye"]) ** 0.45
    exp_h *= min(1.25, max(0.80, seviye))
    exp_a /= min(1.25, max(0.80, seviye))

    matrix = np.zeros((6, 6))
    for h in range(6):
        for a in range(6):
            matrix[h, a] = poisson.pmf(h, exp_h) * poisson.pmf(a, exp_a)
    matrix = (matrix / np.sum(matrix)) * 100

    p_ev = float(np.sum(np.tril(matrix, -1)))
    p_ber = float(np.sum(np.diag(matrix)))
    p_dep = float(np.sum(np.triu(matrix, 1)))

    p_15_ust = float(100 - (matrix[0,0] + matrix[1,0] + matrix[0,1]))
    p_25_ust = float(100 - (matrix[0,0] + matrix[1,0] + matrix[0,1] + matrix[1,1] + matrix[2,0] + matrix[0,2]))
    p_25_alt = float(100 - p_25_ust)

    p_kg_yok = float(np.sum(matrix[0, :]) + np.sum(matrix[:, 0]) - matrix[0, 0])
    p_kg_var = float(100 - p_kg_yok)

    p_1x = float(p_ev + p_ber)
    p_x2 = float(p_dep + p_ber)

    durum = "SARI"
    aksiyon = "PAS GEÇ / RİSKLİ"
    guven_orani = 0.0

    if p_ev >= 65.0:
        durum = "YESIL"
        aksiyon = f"MS 1 ({ev_key.title()})"
        guven_orani = p_ev
    elif p_dep >= 65.0:
        durum = "YESIL"
        aksiyon = f"MS 2 ({dep_key.title()})"
        guven_orani = p_dep
    elif p_15_ust >= 78.0:
        durum = "YESIL"
        aksiyon = "1.5 ÜST"
        guven_orani = p_15_ust
    elif p_25_ust >= 58.0:
        durum = "YESIL"
        aksiyon = "2.5 ÜST"
        guven_orani = p_25_ust
    elif p_x2 >= 75.0:
        durum = "YESIL"
        aksiyon = "X2 Çifte Şans"
        guven_orani = p_x2
    elif p_1x >= 75.0:
        durum = "YESIL"
        aksiyon = "1X Çifte Şans"
        guven_orani = p_1x
    elif p_kg_var >= 62.0:
        durum = "YESIL"
        aksiyon = "KG VAR"
        guven_orani = p_kg_var
    elif p_25_alt >= 60.0:
        durum = "YESIL"
        aksiyon = "2.5 ALT"
        guven_orani = p_25_alt
    elif p_kg_yok >= 62.0:
        durum = "YESIL"
        aksiyon = "KG YOK"
        guven_orani = p_kg_yok

    return {
        "exp_h": exp_h, "exp_a": exp_a, "matrix": matrix,
        "p_ev": p_ev, "p_ber": p_ber, "p_dep": p_dep,
        "p_15_ust": p_15_ust,
        "p_25_ust": p_25_ust, "p_25_alt": p_25_alt,
        "p_kg_var": p_kg_var, "p_kg_yok": p_kg_yok,
        "p_1x": p_1x, "p_x2": p_x2,
        "durum": durum, "aksiyon": aksiyon, "guven_orani": guven_orani
    }

st.markdown(f"### ⚽ Poisson Tahmin Motoru ({len(TAKIM_PROFILLERI)} Takım)")

# ================= SEKMELER (TABS) =================
tab1, tab2, tab3 = st.tabs(["🔍 Tekli Analiz", "⚡ Bülten & Kombine", "📈 Kâr / Zarar Tablosu"])

with tab1:
    takim_listesi = sorted(list(TAKIM_PROFILLERI.keys()))
    
    c1, c2 = st.columns(2)
    with c1:
        ev = st.selectbox("🏠 Ev Sahibi", takim_listesi, index=takim_listesi.index("galatasaray") if "galatasaray" in takim_listesi else 0)
    with c2:
        dep = st.selectbox("✈️ Deplasman", takim_listesi, index=takim_listesi.index("fenerbahce") if "fenerbahce" in takim_listesi else 1)

    if st.button("🚀 Analiz Et", use_container_width=True):
        res = mac_hesapla(ev, dep)
        matrix = res["matrix"]

        st.divider()
        
        if res["durum"] == "YESIL":
            st.success(f"🎯 **EN OLASI SONUÇ / TAHMİN:** {res['aksiyon']} (%{res['guven_orani']:.1f})")
        else:
            st.warning("⚠️ **EN OLASI SONUÇ / TAHMİN:** PAS GEÇ / BELİRSİZ MAÇ")

        skorlar = {f"{h}-{a}": matrix[h, a] for h in range(6) for a in range(6)}
        sirali = sorted(skorlar.items(), key=lambda x: x[1], reverse=True)[:3]

        st.caption("🎯 En Olası Skorlar")
        s1, s2, s3 = st.columns(3)
        s1.metric("1. Skor", sirali[0][0], f"%{sirali[0][1]:.1f}")
        s2.metric("2. Skor", sirali[1][0], f"%{sirali[1][1]:.1f}")
        s3.metric("3. Skor", sirali[2][0], f"%{sirali[2][1]:.1f}")

        st.caption("🏆 Maç Sonu & Çifte Şans")
        t1, t2 = st.columns(2)
        t1.metric(f"MS 1 ({ev[:7].title()}..)", f"%{res['p_ev']:.1f}")
        t2.metric(f"MS 2 ({dep[:7].title()}..)", f"%{res['p_dep']:.1f}")
        
        t3, t4 = st.columns(2)
        t3.metric("1X Çifte Şans", f"%{res['p_1x']:.1f}")
        t4.metric("X2 Çifte Şans", f"%{res['p_x2']:.1f}")

        st.caption("⚽ Gol ve KG Baremleri")
        g1, g2 = st.columns(2)
        g1.metric("1.5 ÜST", f"%{res['p_15_ust']:.1f}")
        g2.metric("2.5 ÜST", f"%{res['p_25_ust']:.1f}")

        k1, k2 = st.columns(2)
        k1.metric("KG VAR", f"%{res['p_kg_var']:.1f}")
        k2.metric("KG YOK", f"%{res['p_kg_yok']:.1f}")

        with st.expander("📊 Skor Olasılık Matrisini Gör"):
            df_matrix = pd.DataFrame(
                np.round(matrix, 1),
                index=[f"{ev[:4]}. {i}" for i in range(6)],
                columns=[f"{dep[:4]}. {j}" for j in range(6)]
            )
            st.dataframe(df_matrix, use_container_width=True)

with tab2:
    st.caption("📋 Maçları alt alta yapıştırıp bülteni tara ve otomatik kombine al:")
    ornek_bulten = (
        "Gaziantep - Fenerbahce\n"
        "Kayserispor - Istanbulspor\n"
        "Torino - Roma\n"
        "Inter - Udinesse\n"
        "Como - Parma\n"
        "Braga - Estoril Praia\n"
        "Villarreal - Real Betis\n"
        "Djurgardens - Gais\n"
        "Leeds United - Newcastle United\n"
        "Vancouver Whitecaps - Austin FC\n"
        "Bodo - Sandefjord\n"
        "San Diego FC - Philadelphia Union\n"
        "alaves - valencia\n"
        "elche - real madrid\n"
        "ipswich - arsenal\n"
        "liverpool - tottenham\n"
        "falkrik - hearts\n"
        "grasshoppers - sion\n"
        "middlesbrough - millwall\n"
        "vallecano - espanyol\n"
        "fiorentina - pisa\n"
        "betis - getafe"
    )
    bulten_metni = st.text_area("Maçlar", value=ornek_bulten, height=220, label_visibility="collapsed")

    c_b1, c_b2 = st.columns(2)
    with c_b1:
        tara_btn = st.button("🔥 Bülteni Tara", use_container_width=True)
    with c_b2:
        kombine_btn = st.button("🎯 Günün Banko Kombinesi", use_container_width=True)

    if tara_btn or kombine_btn:
        satirlar = bulten_metni.strip().split("\n")
        yesil_maclar = []
        sari_maclar = []

        for satir in satirlar:
            if not satir.strip(): continue
            if "-" in satir: parcalar = satir.split("-")
            elif "vs" in satir.lower(): parcalar = satir.lower().split("vs")
            else: continue

            ev_in, dep_in = parcalar[0].strip(), parcalar[1].strip()
            ev_k, dep_k = takim_bul(ev_in), takim_bul(dep_in)
            if not ev_k or not dep_k: continue

            sonuc = mac_hesapla(ev_k, dep_k)
            bilgi = {
                "Maç": f"{ev_k.title()} vs {dep_k.title()}",
                "Öneri": f"{sonuc['aksiyon']} (%{sonuc['guven_orani']:.0f})" if sonuc["durum"] == "YESIL" else "PAS",
                "MS 1": f"%{sonuc['p_ev']:.0f}",
                "MS 2": f"%{sonuc['p_dep']:.0f}",
                "1.5Ü": f"%{sonuc['p_15_ust']:.0f}",
                "2.5Ü": f"%{sonuc['p_25_ust']:.0f}",
                "KG Var": f"%{sonuc['p_kg_var']:.0f}",
                "guven_raw": sonuc["guven_orani"],
                "aksiyon_raw": sonuc["aksiyon"]
            }

            if sonuc["durum"] == "YESIL": yesil_maclar.append(bilgi)
            else: sari_maclar.append(bilgi)

        st.divider()

        if kombine_btn or (tara_btn and len(yesil_maclar) >= 2):
            if len(yesil_maclar) >= 2:
                sirali_yesiller = sorted(yesil_maclar, key=lambda x: x["guven_raw"], reverse=True)
                secilenler = sirali_yesiller[:2]
                toplam_guven = (secilenler[0]["guven_raw"] / 100) * (secilenler[1]["guven_raw"] / 100) * 100

                st.markdown("### 🎫 GÜNÜN 2'Lİ BANKO KOMBİNESİ")
                st.markdown(f"""
                <div class="kombine-box">
                    <h4 style="margin:0; color:#2ecc71;">⚡ Modelin Seçtiği İdeal Kupon</h4>
                    <p style="font-size:0.9rem; opacity:0.85; margin-bottom:10px;">En yüksek olasılıklı ve riski en düşük 2 maç birleştirildi.</p>
                    <hr style="border:0.5px solid rgba(255,255,255,0.2); margin:8px 0;">
                    <b>1. Maç:</b> {secilenler[0]['Maç']} ➔ <b>{secilenler[0]['aksiyon_raw']}</b> (%{secilenler[0]['guven_raw']:.1f})<br>
                    <b>2. Maç:</b> {secilenler[1]['Maç']} ➔ <b>{secilenler[1]['aksiyon_raw']}</b> (%{secilenler[1]['guven_raw']:.1f})
                    <hr style="border:0.5px solid rgba(255,255,255,0.2); margin:8px 0;">
                    <b>Ortak Olasılık Başarısı:</b> %{toplam_guven:.1f}
                </div>
                """, unsafe_allow_html=True)
            else:
                st.warning("⚠️ Kombine için bültende en az 2 adet oynanabilir (yeşil) maç bulunmalıdır.")

        st.markdown(f"**🟢 Oynanabilir Yeşil Maçlar ({len(yesil_maclar)})**")
        if yesil_maclar:
            df_gosterim = pd.DataFrame(yesil_maclar).drop(columns=["guven_raw", "aksiyon_raw"])
            st.dataframe(df_gosterim, use_container_width=True, hide_index=True)
        else:
            st.info("Bültende doğrudan eşiği aşan yeşil maç bulunamadı.")

        with st.expander(f"🟡 Pas Geçilen / Sarı Maçlar ({len(sari_maclar)})"):
            if sari_maclar:
                df_sari = pd.DataFrame(sari_maclar).drop(columns=["guven_raw", "aksiyon_raw"])
                st.dataframe(df_sari, use_container_width=True, hide_index=True)

# ================= TAB 3: KÂR / ZARAR TABLOSU =================
with tab3:
    st.markdown("### 📊 Günlük Kasa ve Kâr/Zarar Takibi")
    st.caption("Buradan günlük kupon yatırımlarını ve aldığın tutarları girerek kasanın durumunu takip edebilirsin.")

    # Oturumda (Session State) veri tutma altyapısı
    if "kasa_gecmisi" not in st.session_state:
        st.session_state.kasa_gecmisi = pd.DataFrame(columns=["Tarih", "Açıklama", "Yatırılan (TL)", "Alınan (TL)", "Net Durum (TL)"])

    with st.form("kasa_form", clear_on_submit=True):
        col_f1, col_f2, col_f3 = st.columns(3)
        with col_f1:
            tarih_input = st.date_input("📅 Tarih")
        with col_f2:
            aciklama_input = st.text_input("📝 Kupon / İşlem Açıklaması", value="Günün Kombinesi")
        with col_f3:
            durum_tipi = st.selectbox("Durum", ["Kazandı ✅", "Yattı ❌", "Nakit Yatırma/Çekme 💵"])

        col_f4, col_f5 = st.columns(2)
        with col_f4:
            yatirilan = st.number_input("Yatırılan Tutar (TL)", min_value=0.0, value=66.0, step=5.0)
        with col_f5:
            alinan = st.number_input("Alınan / Geri Gelen Tutar (TL)", min_value=0.0, value=0.0, step=5.0)

        kaydet_btn = st.form_submit_button("💾 İşlemi Kasaya Ekle", use_container_width=True)

        if kaydet_btn:
            net = alinan - yatirilan
            yeni_veri = pd.DataFrame({
                "Tarih": [str(tarih_input)],
                "Açıklama": [f"{aciklama_input} ({durum_tipi})"],
                "Yatırılan (TL)": [yatirilan],
                "Alınan (TL)": [alinan],
                "Net Durum (TL)": [net]
            })
            st.session_state.kasa_gecmisi = pd.concat([st.session_state.kasa_gecmisi, yeni_veri], ignore_index=True)
            st.success("İşlem kasaya başarıyla eklendi!")
            st.rerun()

    st.divider()

    # Özet Metrikler
    if not st.session_state.kasa_gecmisi.empty:
        toplam_yatirilan = st.session_state.kasa_gecmisi["Yatırılan (TL)"].sum()
        toplam_alinan = st.session_state.kasa_gecmisi["Alınan (TL)"].sum()
        net_kar_zarar = toplam_alinan - toplam_yatirilan

        m1, m2, m3 = st.columns(3)
        m1.metric("Toplam Yatırılan", f"{toplam_yatirilan:.2f} TL")
        m2.metric("Toplam Alınan", f"{toplam_alinan:.2f} TL")
        m3.metric("Net Kâr / Zarar", f"{net_kar_zarar:.2f} TL", delta=f"{net_kar_zarar:.2f} TL")

        st.subheader("📋 Kasa Geçmişi ve İşlem Silme")
        st.caption("İstediğin satırı sırasına göre seçip silebilirsin.")

        # Satır satır silme arayüzü (Ondalık küsurat sabitlendi)
        for idx, row in st.session_state.kasa_gecmisi.iterrows():
            col_s1, col_s2, col_s3, col_s4, col_s5, col_s6 = st.columns([1.5, 2.5, 1, 1, 1, 0.8])
            col_s1.write(f"📅 {row['Tarih']}")
            col_s2.write(f"📝 {row['Açıklama']}")
            col_s3.write(f"Yatırılan: {row['Yatırılan (TL)']:.2f} TL")
            col_s4.write(f"Alınan: {row['Alınan (TL)']:.2f} TL")
            col_s5.write(f"Net: {row['Net Durum (TL)']:.2f} TL")
            
            # Her satıra özel çöp kutusu butonu
            if col_s6.button("🗑️ Sil", key=f"sil_{idx}"):
                st.session_state.kasa_gecmisi = st.session_state.kasa_gecmisi.drop(idx).reset_index(drop=True)
                st.rerun()

        st.divider()
        if st.button("🗑️ Tüm Kasayı Sıfırla", use_container_width=True):
            st.session_state.kasa_gecmisi = pd.DataFrame(columns=["Tarih", "Açıklama", "Yatırılan (TL)", "Alınan (TL)", "Net Durum (TL)"])
            st.rerun()
    else:
        st.info("Henüz kasaya kaydedilmiş bir işlem yok. Yukarıdaki formdan ekleme yapabilirsin.")