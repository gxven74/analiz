import streamlit as st
import numpy as np
import pandas as pd
from scipy.stats import poisson
import difflib
import os

# Mobil öncelikli sayfa ayarı ve Sol Menü Kapalı / Gizli
st.set_page_config(
    page_title="Poisson Tahmin", 
    page_icon="⚽", 
    layout="wide",
    initial_sidebar_state="collapsed"
)

# Tema Durumunu Session State'te Tutma
if "tema" not in st.session_state:
    st.session_state.tema = "Siyah"

# Kusursuz Buton, Tarih ve Tema Uyumlu CSS Ayarları
if st.session_state.tema == "Beyaz":
    tema_css = """
    <style>
        .stApp {
            background-color: #F8F9FA !important;
            color: #212529 !important;
        }
        div[data-testid="stMetric"] {
            background-color: #FFFFFF !important;
            border: 1px solid #CED4DA !important;
            color: #212529 !important;
        }
        .kombine-box {
            background: linear-gradient(135deg, #1b4d3e 0%, #0d2818 100%) !important;
            color: white !important;
        }
    </style>
    """
else:
    tema_css = """
    <style>
        .stApp {
            background-color: #0E1117 !important;
            color: #FAFAFA !important;
        }
        h1, h2, h3, h4, h5, h6, p, label, span, .stMarkdown {
            color: #FAFAFA !important;
        }
        div[data-testid="stMetric"] {
            background-color: #1A1C23 !important;
            border: 1px solid #30333D !important;
            color: #FAFAFA !important;
        }
        /* Selectbox, DateInput ve Input Alanları */
        div[data-baseweb="select"] > div {
            background-color: #1A1C23 !important;
            color: #FAFAFA !important;
            border-color: #30333D !important;
        }
        div[data-baseweb="input"] > div {
            background-color: #1A1C23 !important;
            color: #FAFAFA !important;
            border-color: #30333D !important;
        }
        input {
            background-color: #1A1C23 !important;
            color: #FAFAFA !important;
        }
        textarea {
            background-color: #1A1C23 !important;
            color: #FAFAFA !important;
        }
        /* Tüm Butonlar Koyu Temada Şık Antrasit */
        div.stButton > button {
            background-color: #1F242D !important;
            color: #FAFAFA !important;
            border: 1px solid #30333D !important;
        }
        div.stButton > button:hover {
            background-color: #1b4d3e !important;
            border-color: #2ecc71 !important;
            color: #2ecc71 !important;
        }
        /* Form Gönder Butonları */
        div.stFormSubmitButton > button {
            background-color: #1F242D !important;
            color: #FAFAFA !important;
            border: 1px solid #30333D !important;
        }
        div.stFormSubmitButton > button:hover {
            background-color: #1b4d3e !important;
            border-color: #2ecc71 !important;
            color: #2ecc71 !important;
        }
        /* Expander ve Kutular */
        div[data-testid="stExpander"] {
            background-color: #161922 !important;
            border: 1px solid #30333D !important;
        }
        .kombine-box {
            background: linear-gradient(135deg, #1b4d3e 0%, #0d2818 100%) !important;
            color: white !important;
        }
    </style>
    """

# Genel Mobil ve Arayüz Uyumlu CSS
st.markdown(f"""
{tema_css}
<style>
    .block-container {{
        padding-top: 2.0rem !important;
        padding-bottom: 2rem !important;
        padding-left: 1.2rem !important;
        padding-right: 1.2rem !important;
    }}
    /* 4 Sekmeyi Yatayda Tam Genişliğe Eşit Yayma ve Boşluklandırma */
    div[data-baseweb="tab-list"] {{
        display: flex !important;
        width: 100% !important;
        justify-content: space-around !important;
        background-color: rgba(128, 128, 128, 0.1);
        padding: 8px 10px;
        border-radius: 12px;
        margin-bottom: 20px;
    }}
    div[data-baseweb="tab"] {{
        flex: 1 !important;
        text-align: center !important;
        justify-content: center !important;
        font-weight: 600;
        padding: 12px 10px;
        margin: 0 5px;
        border-radius: 8px;
    }}
    div[data-testid="stMetricLabel"] p {{
        font-size: 0.85rem !important;
        font-weight: 600;
    }}
    div[data-testid="stMetricValue"] div {{
        font-size: 1.25rem !important;
    }}
    div.stButton > button {{
        height: 3em;
        font-size: 1rem;
        font-weight: bold;
    }}
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

    # ==================== DİĞER TAKIMLAR ====================
    "sunderland": {"hucum": 1.55, "savunma": 1.15, "seviye": 1.05},
    "olympiacos": {"hucum": 2.05, "savunma": 1.00, "seviye": 1.25},
    "jagiellonia": {"hucum": 1.45, "savunma": 1.25, "seviye": 0.90},
    "az alkmaar": {"hucum": 1.95, "savunma": 1.10, "seviye": 1.20},
    "anderlecht": {"hucum": 1.85, "savunma": 1.15, "seviye": 1.20},
    "corum fk": {"hucum": 1.20, "savunma": 1.25, "seviye": 0.75},
    "corum": {"hucum": 1.20, "savunma": 1.25, "seviye": 0.75},
    "benfica": {"hucum": 2.20, "savunma": 0.95, "seviye": 1.35},
    "levante": {"hucum": 1.30, "savunma": 1.25, "seviye": 0.90},
    "sturm graz": {"hucum": 1.65, "savunma": 1.15, "seviye": 1.05},
    "santander": {"hucum": 1.35, "savunma": 1.20, "seviye": 0.90},
    "celje": {"hucum": 1.40, "savunma": 1.25, "seviye": 0.85},

    # ==================== TÜRKİYE 1. LİG ====================
    "kocaelispor": {"hucum": 1.25, "savunma": 1.20, "seviye": 0.80},
    "fatih karagumruk": {"hucum": 1.30, "savunma": 1.25, "seviye": 0.80},
    "ankaragucu": {"hucum": 1.30, "savunma": 1.25, "seviye": 0.80},
    "istanbulspor": {"hucum": 1.20, "savunma": 1.30, "seviye": 0.75},
    "pendikspor": {"hucum": 1.20, "savunma": 1.30, "seviye": 0.75},
    "sakaryaspor": {"hucum": 1.15, "savunma": 1.25, "seviye": 0.75},
    "bandirmaspor": {"hucum": 1.20, "savunma": 1.25, "seviye": 0.75},
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
    "braga": "braga", "estoril": "estoril praia",
    "benfica": "benfica", "levante": "levante",
    "sturm": "sturm graz", "sturm graz": "sturm graz",
    "santander": "santander", "racing santander": "santander",
    "celje": "celje",
    "sunderland": "sunderland",
    "olympiacos": "olympiacos", "Olympiakos": "olympiacos",
    "jagiellonia": "jagiellonia",
    "az alkmaar": "az alkmaar", "alkmaar": "az alkmaar",
    "anderlecht": "anderlecht",
    "corum": "corum fk", "corum fk": "corum fk"
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

# Üst Başlık ve Sağ Üst Tema Değiştirme Butonu
col_baslik, col_tema = st.columns([4, 1])
with col_baslik:
    st.markdown(f"### ⚽ Poisson Tahmin Motoru ({len(TAKIM_PROFILLERI)} Takım)")
with col_tema:
    if st.session_state.tema == "Siyah":
        if st.button("☀️ Beyaz Tema", use_container_width=True):
            st.session_state.tema = "Beyaz"
            st.rerun()
    else:
        if st.button("🌙 Siyah Tema", use_container_width=True):
            st.session_state.tema = "Siyah"
            st.rerun()

# ================= SEKMELER (TABS) =================
tab1, tab2, tab3, tab4 = st.tabs(["🔍 Tekli Analiz", "⚡ Bülten & Kombine", "📈 Kâr / Zarar", "📊 İstatistikler"])

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
    st.caption("📋 Maçları alt alta yapıştırıp bülteni tara ve otomatik 3'lü kombine al:")
    ornek_bulten = (
        ""
    )
    bulten_metni = st.text_area("Maçlar", value=ornek_bulten, height=220, label_visibility="collapsed")

    c_b1, c_b2 = st.columns(2)
    with c_b1:
        tara_btn = st.button("🔥 Bülteni Tara", use_container_width=True)
    with c_b2:
        kombine_btn = st.button("🎯 Günün 3'lü Banko Kombinesi", use_container_width=True)

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

        if kombine_btn or (tara_btn and len(yesil_maclar) >= 3):
            if len(yesil_maclar) >= 3:
                sirali_yesiller = sorted(yesil_maclar, key=lambda x: x["guven_raw"], reverse=True)
                secilenler = sirali_yesiller[:3]
                toplam_guven = (secilenler[0]["guven_raw"] / 100) * (secilenler[1]["guven_raw"] / 100) * (secilenler[2]["guven_raw"] / 100) * 100

                st.markdown("### 🎫 GÜNÜN 3'LÜ BANKO KOMBİNESİ")
                st.markdown(f"""
                <div class="kombine-box">
                    <h4 style="margin:0; color:#2ecc71;">⚡ Modelin Seçtiği 3'lü İdeal Kupon</h4>
                    <p style="font-size:0.9rem; opacity:0.85; margin-bottom:10px;">En yüksek olasılıklı ve riski en düşük 3 maç birleştirildi.</p>
                    <hr style="border:0.5px solid rgba(255,255,255,0.2); margin:8px 0;">
                    <b>1. Maç:</b> {secilenler[0]['Maç']} ➔ <b>{secilenler[0]['aksiyon_raw']}</b> (%{secilenler[0]['guven_raw']:.1f})<br>
                    <b>2. Maç:</b> {secilenler[1]['Maç']} ➔ <b>{secilenler[1]['aksiyon_raw']}</b> (%{secilenler[1]['guven_raw']:.1f})<br>
                    <b>3. Maç:</b> {secilenler[2]['Maç']} ➔ <b>{secilenler[2]['aksiyon_raw']}</b> (%{secilenler[2]['guven_raw']:.1f})
                    <hr style="border:0.5px solid rgba(255,255,255,0.2); margin:8px 0;">
                    <b>Ortak Olasılık Başarısı:</b> %{toplam_guven:.1f}
                </div>
                """, unsafe_allow_html=True)
            else:
                st.warning("⚠️ 3'lü kombine için bültende en az 3 adet oynanabilir (yeşil) maç bulunmalıdır.")

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
DOSYA_KASA = "kasa_defteri.csv"

if os.path.exists(DOSYA_KASA):
    kasa_df = pd.read_csv(DOSYA_KASA)
    if "Durum" not in kasa_df.columns:
        kasa_df["Durum"] = "Kazandı ✅"
else:
    kasa_df = pd.DataFrame(columns=["Tarih", "Açıklama", "Durum", "Yatırılan (TL)", "Alınan (TL)", "Net Durum (TL)"])

with tab3:
    st.markdown("### 📊 Günlük Kasa ve Kâr/Zarar Takibi")
    st.caption("Buradan finansal yatırımlarını ve kasa durumunu takip edebilirsin.")

    with st.form("kasa_form", clear_on_submit=True):
        col_f1, col_f2, col_f3 = st.columns(3)
        with col_f1:
            tarih_input = st.date_input("📅 Tarih")
        with col_f2:
            aciklama_input = st.text_input("📝 İşlem Açıklaması", value="Günün Kombinesi")
        with col_f3:
            durum_tipi = st.selectbox("Durum", ["Kazandı ✅", "Yattı ❌", "Nakit Yatırma/Çekme 💵"])

        col_f4, col_f5 = st.columns(2)
        with col_f4:
            yatirilan = st.number_input("Yatırılan Tutar (TL)", min_value=0.0, value=0.0, step=5.0)
        with col_f5:
            alinan = st.number_input("Alınan / Geri Gelen Tutar (TL)", min_value=0.0, value=0.0, step=5.0)

        kaydet_btn = st.form_submit_button("💾 İşlemi Kasaya Ekle", use_container_width=True)

        if kaydet_btn:
            net = alinan - yatirilan
            yeni_veri = pd.DataFrame({
                "Tarih": [str(tarih_input)],
                "Açıklama": [f"{aciklama_input} ({durum_tipi})"],
                "Durum": [durum_tipi],
                "Yatırılan (TL)": [yatirilan],
                "Alınan (TL)": [alinan],
                "Net Durum (TL)": [net]
            })
            
            kasa_df = pd.concat([kasa_df, yeni_veri], ignore_index=True)
            kasa_df.to_csv(DOSYA_KASA, index=False)
            
            st.success("İşlem kasaya kalıcı olarak eklendi!")
            st.rerun()

    st.divider()

    if not kasa_df.empty:
        toplam_yatirilan = kasa_df["Yatırılan (TL)"].sum()
        toplam_alinan = kasa_df["Alınan (TL)"].sum()
        net_kar_zarar = toplam_alinan - toplam_yatirilan

        m1, m2, m3 = st.columns(3)
        m1.metric("Toplam Yatırılan", f"{toplam_yatirilan:.2f} TL")
        m2.metric("Toplam Alınan", f"{toplam_alinan:.2f} TL")
        m3.metric("Net Kâr / Zarar", f"{net_kar_zarar:.2f} TL", delta=f"{net_kar_zarar:.2f} TL")

        st.subheader("📋 Kasa Geçmişi ve İşlem Silme")

        kasa_arama = st.text_input("🔍 Kasa Geçmişinde Ara (Açıklama / Tarih)", value="", key="kasa_arama_input")
        filtrelenmis_kasa = kasa_df
        if kasa_arama.strip():
            filtrelenmis_kasa = kasa_df[kasa_df.astype(str).apply(lambda x: x.str.contains(kasa_arama, case=False)).any(axis=1)]

        for idx, row in filtrelenmis_kasa.iterrows():
            col_s1, col_s2, col_s3, col_s4, col_s5, col_s6 = st.columns([1.5, 2.5, 1, 1, 1, 0.8])
            col_s1.write(f"📅 {row['Tarih']}")
            col_s2.write(f"📝 {row['Açıklama']}")
            col_s3.write(f"Yat: {row['Yatırılan (TL)']:.2f}")
            col_s4.write(f"Al: {row['Alınan (TL)']:.2f}")
            col_s5.write(f"Net: {row['Net Durum (TL)']:.2f}")
            
            if col_s6.button("🗑️ Sil", key=f"sil_kasa_{idx}"):
                kasa_df = kasa_df.drop(idx).reset_index(drop=True)
                kasa_df.to_csv(DOSYA_KASA, index=False)
                st.rerun()

        st.divider()
        if st.button("🗑️ Tüm Kasayı Sıfırla", use_container_width=True):
            kasa_df = pd.DataFrame(columns=["Tarih", "Açıklama", "Durum", "Yatırılan (TL)", "Alınan (TL)", "Net Durum (TL)"])
            if os.path.exists(DOSYA_KASA):
                os.remove(DOSYA_KASA)
            st.rerun()
    else:
        st.info("Henüz kasaya kaydedilmiş bir işlem yok.")

# ================= TAB 4: İSTATİSTİKLER =================
DOSYA_ISTATISTIK = "istatistik_defteri.csv"

if os.path.exists(DOSYA_ISTATISTIK):
    istatistik_df = pd.read_csv(DOSYA_ISTATISTIK)
    if "Maç" not in istatistik_df.columns and "Tahmin / Maç Adı" in istatistik_df.columns:
        istatistik_df = istatistik_df.rename(columns={"Tahmin / Maç Adı": "Maç"})
    if "Tahmin" not in istatistik_df.columns:
        istatistik_df["Tahmin"] = "Genel"
else:
    istatistik_df = pd.DataFrame(columns=["Tarih", "Maç", "Tahmin", "Sonuç"])

with tab4:
    st.markdown("### 📊 Model Başarı İstatistikleri Karnesi")
    st.caption("Ev sahibi, deplasman takımlarını ve tahmin türünü seçerek modelinin başarı oranını takip et.")

    takim_listesi = sorted(list(TAKIM_PROFILLERI.keys()))

    with st.form("istatistik_form", clear_on_submit=True):
        col_i1, col_i2 = st.columns(2)
        with col_i1:
            ist_tarih = st.date_input("📅 Tarih", key="ist_tarih")
        with col_i2:
            tahmin_turu = st.selectbox("🎯 Tahmin / Bahis Türü", [
                "MS 1", "MS 2", "Maç Sonu Beraberlik (0)", 
                "1.5 ÜST", "1.5 ALT", 
                "2.5 ÜST", "2.5 ALT", 
                "KG VAR", "KG YOK", 
                "1X Çifte Şans", "X2 Çifte Şans"
            ])

        col_i3, col_i4, col_i5 = st.columns(3)
        with col_i3:
            ist_ev = st.selectbox("🏠 Ev Sahibi Takım", takim_listesi, index=0, key="ist_ev")
        with col_i4:
            ist_dep = st.selectbox("✈️ Deplasman Takım", takim_listesi, index=1 if len(takim_listesi) > 1 else 0, key="ist_dep")
        with col_i5:
            ist_sonuc = st.selectbox("🎯 Sonuç", ["Kazandı ✅", "Kaybetti ❌"], key="ist_sonuc_secim")

        ist_kaydet = st.form_submit_button("💾 Tahmini İstatistiklere Ekle", use_container_width=True)

        if ist_kaydet:
            mac_adi = f"{ist_ev.title()} vs {ist_dep.title()}"
            yeni_ist = pd.DataFrame({
                "Tarih": [str(ist_tarih)],
                "Maç": [mac_adi],
                "Tahmin": [tahmin_turu],
                "Sonuç": [ist_sonuc]
            })
            istatistik_df = pd.concat([istatistik_df, yeni_ist], ignore_index=True)
            istatistik_df.to_csv(DOSYA_ISTATISTIK, index=False)
            st.success("Maç tahmini istatistiklere eklendi!")
            st.rerun()

    st.divider()

    if not istatistik_df.empty:
        toplam_tahmin = len(istatistik_df)
        kazananlar_ist = istatistik_df[istatistik_df["Sonuç"] == "Kazandı ✅"]
        kaybedenler_ist = istatistik_df[istatistik_df["Sonuç"] == "Kaybetti ❌"]
        
        toplam_kazanan_ist = len(kazananlar_ist)
        toplam_kaybeden_ist = len(kaybedenler_ist)
        
        win_rate = (toplam_kazanan_ist / toplam_tahmin * 100) if toplam_tahmin > 0 else 0.0

        i1, i2, i3, i4 = st.columns(4)
        i1.metric("Toplam Girilen Tahmin", f"{toplam_tahmin}")
        i2.metric("Kazananlar 🟢", f"{toplam_kazanan_ist}")
        i3.metric("Kaybedenler 🔴", f"{toplam_kaybeden_ist}")
        i4.metric("Kazanma Oranı (Win Rate)", f"%{win_rate:.1f}")

        st.divider()
        st.subheader("📋 Kayıtlı Tahmin Geçmişi")

        ist_arama = st.text_input("🔍 Tahmin Geçmişinde Ara (Takım / Tahmin / Tarih)", value="", key="ist_arama_input")
        filtrelenmis_ist = istatistik_df
        if ist_arama.strip():
            filtrelenmis_ist = istatistik_df[istatistik_df.astype(str).apply(lambda x: x.str.contains(ist_arama, case=False)).any(axis=1)]

        for idx, row in filtrelenmis_ist.iterrows():
            col_is1, col_is2, col_is3, col_is4, col_is5 = st.columns([1.2, 2.5, 1.5, 1.2, 0.7])
            col_is1.write(f"📅 {row['Tarih']}")
            col_is2.write(f"⚽ {row['Maç']}")
            col_is3.write(f"🎯 <b>{row['Tahmin']}</b>", unsafe_allow_html=True)
            col_is4.write(f"<b>{row['Sonuç']}</b>", unsafe_allow_html=True)
            
            if col_is5.button("🗑️ Sil", key=f"sil_ist_{idx}"):
                istatistik_df = istatistik_df.drop(idx).reset_index(drop=True)
                istatistik_df.to_csv(DOSYA_ISTATISTIK, index=False)
                st.rerun()

        st.divider()
        if st.button("🗑️ Tüm İstatistikleri Sıfırla", use_container_width=True):
            istatistik_df = pd.DataFrame(columns=["Tarih", "Maç", "Tahmin", "Sonuç"])
            if os.path.exists(DOSYA_ISTATISTIK):
                os.remove(DOSYA_ISTATISTIK)
            st.rerun()
    else:
        st.info("Henüz istatistik için eklenmiş bir tahmin yok.")