import streamlit as st
import numpy as np
import pandas as pd
from scipy.stats import poisson
import difflib
import os
from datetime import datetime, timedelta
import urllib.request
import json
import concurrent.futures
import re

# Dosyaların her zaman kodun olduğu klasörde açılmasını garantileyen tam yol ayarı
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DOSYA_KASA = os.path.join(BASE_DIR, "kasa_defteri.csv")
DOSYA_ISTATISTIK = os.path.join(BASE_DIR, "istatistik_defteri.csv")
DOSYA_CANLI_API = os.path.join(BASE_DIR, "canli_api_verisi.json")

# Mobil öncelikli sayfa ayarı ve Sol Menü Kapalı / Gizli
st.set_page_config(
    page_title="Poisson Pro 26/27",
    page_icon="⚽",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# Tema Durumunu Session State'te Tutma
if "tema" not in st.session_state:
    st.session_state.tema = "Siyah"

# CSV'den Verileri Güvenli Okuma Fonksiyonu
def verileri_yukle():
    if "kasa_verileri" not in st.session_state:
        if os.path.exists(DOSYA_KASA):
            try:
                st.session_state.kasa_verileri = pd.read_csv(DOSYA_KASA).to_dict('records')
            except:
                st.session_state.kasa_verileri = []
        else:
            st.session_state.kasa_verileri = []

    if "istatistik_verileri" not in st.session_state:
        if os.path.exists(DOSYA_ISTATISTIK):
            try:
                st.session_state.istatistik_verileri = pd.read_csv(DOSYA_ISTATISTIK).to_dict('records')
            except:
                st.session_state.istatistik_verileri = []
        else:
            st.session_state.istatistik_verileri = []

verileri_yukle()

# URL parametresi ile tema değişimi kontrolü
query_params = st.query_params
if "tema_degis" in query_params:
    yeni_t = query_params["tema_degis"]
    if yeni_t in ["Siyah", "Beyaz"]:
        st.session_state.tema = yeni_t

# Tema CSS Ayarları
if st.session_state.tema == "Beyaz":
    tema_css = """
    <style>
        .stApp { background-color: #F8F9FA !important; color: #212529 !important; }
        header[data-testid="stHeader"] { background-color: #F8F9FA !important; }
        div[data-testid="stMetric"] { background-color: #FFFFFF !important; border: 1px solid #CED4DA !important; color: #212529 !important; }
        .kombine-box { background: linear-gradient(135deg, #1b4d3e 0%, #0d2818 100%) !important; color: white !important; }
        .kurtarma-box { background: linear-gradient(135deg, #1e3c72 0%, #2a5298 100%) !important; color: white !important; }
        .custom-table { width: 100%; border-collapse: collapse; background-color: #FFFFFF; color: #212529; font-size: 0.9rem; }
        .custom-table th, .custom-table td { border: 1px solid #CED4DA; padding: 8px 12px; text-align: center; }
        .custom-table th { background-color: #E9ECEF; }
    </style>
    """
else:
    tema_css = """
    <style>
        .stApp { background-color: #0E1117 !important; color: #FAFAFA !important; }
        header[data-testid="stHeader"] { background-color: #0E1117 !important; }
        h1, h2, h3, h4, h5, h6, p, label, span, .stMarkdown { color: #FAFAFA !important; }
        div[data-testid="stMetric"] { background-color: #1A1C23 !important; border: 1px solid #30333D !important; color: #FAFAFA !important; }
        div[data-baseweb="select"] > div, div[data-baseweb="input"] > div, input, textarea { background-color: #1A1C23 !important; color: #FAFAFA !important; border-color: #30333D !important; }
        div[data-testid="stExpander"] { background-color: #161922 !important; border: 1px solid #30333D !important; color: #FAFAFA !important; }
        .custom-table { width: 100%; border-collapse: collapse; background-color: #161922 !important; color: #FAFAFA !important; font-size: 0.9rem; border-radius: 8px; overflow: hidden; }
        .custom-table th, .custom-table td { border: 1px solid #30333D !important; padding: 10px 12px; text-align: center; background-color: #161922 !important; color: #FAFAFA !important; }
        .custom-table th { background-color: #1F242D !important; color: #2ecc71 !important; font-weight: bold; }
        .custom-table tr:nth-child(even) td { background-color: #1A1C23 !important; }
        div.stButton > button, div.stFormSubmitButton > button { background-color: #1F242D !important; color: #FAFAFA !important; border: 1px solid #30333D !important; }
        div.stButton > button:hover, div.stFormSubmitButton > button:hover { background-color: #1b4d3e !important; border-color: #2ecc71 !important; color: #2ecc71 !important; }
        .kombine-box { background: linear-gradient(135deg, #1b4d3e 0%, #0d2818 100%) !important; color: white !important; }
        .kurtarma-box { background: linear-gradient(135deg, #141E30 0%, #243B55 100%) !important; color: white !important; border: 1px solid #3498db !important; }
    </style>
    """

st.markdown(f"""
{tema_css}
<style>
    .block-container {{ padding-top: 2.0rem !important; padding-bottom: 2rem !important; padding-left: 1.2rem !important; padding-right: 1.2rem !important; }}
    div[data-baseweb="tab-list"] {{ display: flex !important; width: 100% !important; justify-content: space-around !important; background-color: rgba(128, 128, 128, 0.1); padding: 8px 10px; border-radius: 12px; margin-bottom: 20px; }}
    div[data-baseweb="tab"] {{ flex: 1 !important; text-align: center !important; justify-content: center !important; font-weight: 600; padding: 12px 10px; margin: 0 5px; border-radius: 8px; }}
    
    @media (max-width: 768px) {{
        .block-container {{
            padding-top: 1.0rem !important;
            padding-bottom: 1.5rem !important;
            padding-left: 0.5rem !important;
            padding-right: 0.5rem !important;
        }}
        div[data-baseweb="tab-list"] {{
            overflow-x: auto !important;
            flex-wrap: nowrap !important;
            justify-content: flex-start !important;
            padding: 6px 4px !important;
            gap: 4px !important;
            -webkit-overflow-scrolling: touch !important;
        }}
        div[data-baseweb="tab"] {{
            flex: 0 0 auto !important;
            white-space: nowrap !important;
            padding: 8px 12px !important;
            font-size: 0.85rem !important;
        }}
        .custom-table {{
            font-size: 0.78rem !important;
            display: block !important;
            overflow-x: auto !important;
            -webkit-overflow-scrolling: touch !important;
        }}
        .custom-table th, .custom-table td {{
            padding: 6px 8px !important;
        }}
        div.stButton > button, div.stFormSubmitButton > button {{
            padding: 0.6rem 0.8rem !important;
            font-size: 0.9rem !important;
        }}
    }}
</style>
""", unsafe_allow_html=True)

# ==============================================================================
# 2026-27 SEZONU KALİBRE EDİLMİŞ KULÜP GÜÇ PROFİLLERİ (DİXON-COLES & AVRUPA UYUMLU)
# hucum: Maç başı baz üretim gücü | savunma: Zaaf katsayısı (düşük = daha sağlam savunma)
# seviye: Global kadro/kulüp klasmanı (0.50 - 1.46 arası)
# ==============================================================================
TAKIM_PROFILLERI = {
    # --- TÜRKİYE SÜPER LİG & 1. LİG (2026-27) ---
    "galatasaray": {"hucum": 2.20, "savunma": 1.00, "seviye": 1.32},
    "fenerbahce": {"hucum": 2.15, "savunma": 1.00, "seviye": 1.30},
    "besiktas": {"hucum": 1.75, "savunma": 1.15, "seviye": 1.18},
    "trabzonspor": {"hucum": 1.58, "savunma": 1.16, "seviye": 1.08},
    "basaksehir": {"hucum": 1.45, "savunma": 1.30, "seviye": 1.00},
    "samsunspor": {"hucum": 1.18, "savunma": 1.45, "seviye": 0.90},
    "goztepe": {"hucum": 1.40, "savunma": 1.15, "seviye": 1.00},
    "eyupspor": {"hucum": 1.40, "savunma": 1.20, "seviye": 0.98},
    "amed": {"hucum": 1.65, "savunma": 1.10, "seviye": 1.16},
    "kasimpasa": {"hucum": 1.45, "savunma": 1.46, "seviye": 0.94},
    "sivasspor": {"hucum": 1.28, "savunma": 1.35, "seviye": 0.90},
    "antalyaspor": {"hucum": 1.25, "savunma": 1.35, "seviye": 0.90},
    "alanyaspor": {"hucum": 1.26, "savunma": 1.30, "seviye": 0.90},
    "rizespor": {"hucum": 1.25, "savunma": 1.34, "seviye": 0.90},
    "gaziantep": {"hucum": 1.20, "savunma": 1.38, "seviye": 0.86},
    "konyaspor": {"hucum": 1.16, "savunma": 1.32, "seviye": 0.86},
    "kayserispor": {"hucum": 1.15, "savunma": 1.44, "seviye": 0.84},
    "kocaelispor": {"hucum": 1.28, "savunma": 1.22, "seviye": 0.85},
    "fatih karagumruk": {"hucum": 1.30, "savunma": 1.26, "seviye": 0.84},
    "genclerbirligi": {"hucum": 1.18, "savunma": 1.25, "seviye": 0.78},
    "bodrum fk": {"hucum": 1.02, "savunma": 1.28, "seviye": 0.80},
    "hatayspor": {"hucum": 1.05, "savunma": 1.45, "seviye": 0.78},
    "ankaragucu": {"hucum": 1.28, "savunma": 1.26, "seviye": 0.80},
    "bandirmaspor": {"hucum": 1.22, "savunma": 1.24, "seviye": 0.76},
    "corum": {"hucum": 1.20, "savunma": 1.24, "seviye": 0.76},
    "erzurumspor": {"hucum": 1.16, "savunma": 1.20, "seviye": 0.75},
    "istanbulspor": {"hucum": 1.20, "savunma": 1.30, "seviye": 0.75},
    "pendikspor": {"hucum": 1.20, "savunma": 1.30, "seviye": 0.75},
    "sakaryaspor": {"hucum": 1.15, "savunma": 1.26, "seviye": 0.75},
    "igdir fk": {"hucum": 1.18, "savunma": 1.25, "seviye": 0.74},
    "boluspor": {"hucum": 1.12, "savunma": 1.22, "seviye": 0.72},
    "umraniyespor": {"hucum": 1.15, "savunma": 1.30, "seviye": 0.72},
    "manisa fk": {"hucum": 1.15, "savunma": 1.32, "seviye": 0.70},
    "keciorengucu": {"hucum": 1.12, "savunma": 1.30, "seviye": 0.70},
    "esenler erokspor": {"hucum": 1.16, "savunma": 1.32, "seviye": 0.70},
    "adana demirspor": {"hucum": 0.98, "savunma": 1.68, "seviye": 0.68},
    "sanliurfaspor": {"hucum": 1.05, "savunma": 1.36, "seviye": 0.65},
    "adanaspor": {"hucum": 0.98, "savunma": 1.48, "seviye": 0.64},
    "yeni malatyaspor": {"hucum": 0.70, "savunma": 1.90, "seviye": 0.50},

    # --- İNGİLTERE PREMIER LİG & CHAMPIONSHIP (2026-27) ---
    "manchester city": {"hucum": 2.28, "savunma": 0.94, "seviye": 1.46},
    "arsenal": {"hucum": 2.10, "savunma": 0.86, "seviye": 1.44},
    "liverpool": {"hucum": 2.20, "savunma": 0.95, "seviye": 1.42},
    "chelsea": {"hucum": 1.90, "savunma": 1.20, "seviye": 1.25},
    "tottenham": {"hucum": 1.92, "savunma": 1.34, "seviye": 1.22},
    "aston villa": {"hucum": 1.68, "savunma": 1.14, "seviye": 1.20},
    "newcastle": {"hucum": 1.68, "savunma": 1.12, "seviye": 1.20},
    "manchester united": {"hucum": 1.66, "savunma": 1.28, "seviye": 1.16},
    "brighton": {"hucum": 1.70, "savunma": 1.28, "seviye": 1.16},
    "bournemouth": {"hucum": 1.52, "savunma": 1.28, "seviye": 1.10},
    "nottingham forest": {"hucum": 1.40, "savunma": 1.14, "seviye": 1.08},
    "brentford": {"hucum": 1.56, "savunma": 1.38, "seviye": 1.06},
    "fulham": {"hucum": 1.38, "savunma": 1.22, "seviye": 1.06},
    "west ham": {"hucum": 1.40, "savunma": 1.42, "seviye": 1.04},
    "crystal palace": {"hucum": 1.32, "savunma": 1.22, "seviye": 1.02},
    "everton": {"hucum": 1.22, "savunma": 1.22, "seviye": 1.00},
    "leeds": {"hucum": 1.52, "savunma": 1.30, "seviye": 1.05},
    "sunderland": {"hucum": 1.48, "savunma": 1.18, "seviye": 1.02},
    "burnley": {"hucum": 1.34, "savunma": 1.18, "seviye": 0.98},
    "wolves": {"hucum": 1.28, "savunma": 1.52, "seviye": 0.95},
    "middlesbrough": {"hucum": 1.52, "savunma": 1.24, "seviye": 1.02},
    "sheffield united": {"hucum": 1.38, "savunma": 1.28, "seviye": 0.95},
    "coventry": {"hucum": 1.40, "savunma": 1.26, "seviye": 0.95},
    "west bromwich": {"hucum": 1.42, "savunma": 1.24, "seviye": 0.95},
    "hull city": {"hucum": 1.34, "savunma": 1.30, "seviye": 0.94},
    "millwall": {"hucum": 1.22, "savunma": 1.20, "seviye": 0.92},
    "leicester": {"hucum": 1.25, "savunma": 1.52, "seviye": 0.92},
    "norwich": {"hucum": 1.35, "savunma": 1.44, "seviye": 0.90},
    "watford": {"hucum": 1.30, "savunma": 1.38, "seviye": 0.88},
    "luton": {"hucum": 1.25, "savunma": 1.42, "seviye": 0.88},
    "ipswich": {"hucum": 1.15, "savunma": 1.58, "seviye": 0.85},
    "southampton": {"hucum": 1.12, "savunma": 1.62, "seviye": 0.85},

    # --- İSPANYA LA LİGA & LA LİGA 2 (2026-27) ---
    "real madrid": {"hucum": 2.36, "savunma": 0.96, "seviye": 1.46},
    "barcelona": {"hucum": 2.45, "savunma": 1.06, "seviye": 1.45},
    "atletico madrid": {"hucum": 1.80, "savunma": 0.92, "seviye": 1.35},
    "athletic bilbao": {"hucum": 1.52, "savunma": 0.98, "seviye": 1.18},
    "villarreal": {"hucum": 1.85, "savunma": 1.32, "seviye": 1.18},
    "real betis": {"hucum": 1.40, "savunma": 1.06, "seviye": 1.14},
    "real sociedad": {"hucum": 1.32, "savunma": 1.04, "seviye": 1.12},
    "girona": {"hucum": 1.58, "savunma": 1.30, "seviye": 1.12},
    "mallorca": {"hucum": 1.16, "savunma": 1.08, "seviye": 1.04},
    "celta vigo": {"hucum": 1.50, "savunma": 1.42, "seviye": 1.02},
    "osasuna": {"hucum": 1.30, "savunma": 1.28, "seviye": 1.00},
    "sevilla": {"hucum": 1.34, "savunma": 1.30, "seviye": 1.00},
    "rayo vallecano": {"hucum": 1.16, "savunma": 1.18, "seviye": 0.95},
    "getafe": {"hucum": 0.95, "savunma": 1.08, "seviye": 0.95},
    "alaves": {"hucum": 1.18, "savunma": 1.32, "seviye": 0.94},
    "levante": {"hucum": 1.32, "savunma": 1.20, "seviye": 0.95},
    "racing": {"hucum": 1.55, "savunma": 1.28, "seviye": 0.96},
    "espanyol": {"hucum": 1.16, "savunma": 1.38, "seviye": 0.90},
    "valencia": {"hucum": 1.12, "savunma": 1.42, "seviye": 0.90},
    "las palmas": {"hucum": 1.18, "savunma": 1.44, "seviye": 0.90},
    "almeria": {"hucum": 1.56, "savunma": 1.26, "seviye": 1.05},
    "granada": {"hucum": 1.48, "savunma": 1.22, "seviye": 1.04},
    "real oviedo": {"hucum": 1.24, "savunma": 1.18, "seviye": 0.90},
    "mirandes": {"hucum": 1.26, "savunma": 1.22, "seviye": 0.88},
    "burgos": {"hucum": 1.14, "savunma": 1.10, "seviye": 0.88},
    "elche": {"hucum": 1.12, "savunma": 1.28, "seviye": 0.86},
    "leganes": {"hucum": 1.06, "savunma": 1.26, "seviye": 0.86},
    "deportivo": {"hucum": 1.28, "savunma": 1.24, "seviye": 0.86},
    "valladolid": {"hucum": 1.00, "savunma": 1.58, "seviye": 0.84},
    "malaga": {"hucum": 1.22, "savunma": 1.24, "seviye": 0.82},
    "tenerife": {"hucum": 0.88, "savunma": 1.42, "seviye": 0.76},

    # --- İTALYA SERIE A & SERIE B (2026-27) ---
    "inter": {"hucum": 2.20, "savunma": 0.86, "seviye": 1.42},
    "napoli": {"hucum": 1.82, "savunma": 0.92, "seviye": 1.32},
    "atalanta": {"hucum": 1.95, "savunma": 1.32, "seviye": 1.18},
    "juventus": {"hucum": 1.70, "savunma": 0.96, "seviye": 1.25},
    "milan": {"hucum": 1.85, "savunma": 1.22, "seviye": 1.25},
    "lazio": {"hucum": 1.78, "savunma": 1.22, "seviye": 1.20},
    "roma": {"hucum": 1.62, "savunma": 1.16, "seviye": 1.18},
    "bologna": {"hucum": 1.46, "savunma": 1.14, "seviye": 1.15},
    "fiorentina": {"hucum": 1.55, "savunma": 1.22, "seviye": 1.12},
    "como": {"hucum": 1.40, "savunma": 1.24, "seviye": 1.02},
    "torino": {"hucum": 1.24, "savunma": 1.18, "seviye": 1.00},
    "genoa": {"hucum": 1.22, "savunma": 1.24, "seviye": 0.96},
    "udinese": {"hucum": 1.22, "savunma": 1.32, "seviye": 0.94},
    "sassuolo": {"hucum": 1.42, "savunma": 1.42, "seviye": 0.94},
    "parma": {"hucum": 1.34, "savunma": 1.42, "seviye": 0.92},
    "cagliari": {"hucum": 1.20, "savunma": 1.42, "seviye": 0.90},
    "empoli": {"hucum": 1.08, "savunma": 1.26, "seviye": 0.90},
    "verona": {"hucum": 1.22, "savunma": 1.52, "seviye": 0.88},
    "lecce": {"hucum": 1.05, "savunma": 1.35, "seviye": 0.88},
    "cremonese": {"hucum": 1.24, "savunma": 1.30, "seviye": 0.88},
    "palermo": {"hucum": 1.28, "savunma": 1.28, "seviye": 0.88},
    "pisa": {"hucum": 1.24, "savunma": 1.28, "seviye": 0.86},
    "monza": {"hucum": 1.06, "savunma": 1.36, "seviye": 0.85},
    "frosinone": {"hucum": 1.62, "savunma": 1.30, "seviye": 1.08},
    "bari": {"hucum": 1.18, "savunma": 1.28, "seviye": 0.84},
    "venezia": {"hucum": 1.05, "savunma": 1.54, "seviye": 0.80},
    "sudtirol": {"hucum": 1.10, "savunma": 1.34, "seviye": 0.80},

    # --- ALMANYA BUNDESLIGA & BUNDESLIGA 2 (2026-27) ---
    "bayern munih": {"hucum": 2.52, "savunma": 1.02, "seviye": 1.46},
    "bayer leverkusen": {"hucum": 2.25, "savunma": 1.12, "seviye": 1.35},
    "leipzig": {"hucum": 1.94, "savunma": 1.10, "seviye": 1.28},
    "dortmund": {"hucum": 1.48, "savunma": 1.12, "seviye": 1.18},
    "eintracht frankfurt": {"hucum": 1.46, "savunma": 1.12, "seviye": 1.14},
    "stuttgart": {"hucum": 1.88, "savunma": 1.28, "seviye": 1.20},
    "freiburg": {"hucum": 1.55, "savunma": 1.22, "seviye": 1.12},
    "koln": {"hucum": 1.62, "savunma": 1.22, "seviye": 1.08},
    "werder bremen": {"hucum": 1.50, "savunma": 1.38, "seviye": 1.05},
    "borussia monchengladbach": {"hucum": 1.52, "savunma": 1.40, "seviye": 1.05},
    "union berlin": {"hucum": 1.24, "savunma": 1.15, "seviye": 1.04},
    "mainz": {"hucum": 1.44, "savunma": 1.32, "seviye": 1.02},
    "wolfsburg": {"hucum": 1.48, "savunma": 1.42, "seviye": 1.02},
    "hamburg": {"hucum": 1.36, "savunma": 1.22, "seviye": 1.02},
    "augsburg": {"hucum": 1.38, "savunma": 1.44, "seviye": 0.98},
    "hoffenheim": {"hucum": 1.54, "savunma": 1.56, "seviye": 0.96},
    "heidenheim": {"hucum": 1.32, "savunma": 1.38, "seviye": 0.95},
    "paderborn": {"hucum": 1.24, "savunma": 1.22, "seviye": 0.96},
    "schalke": {"hucum": 1.38, "savunma": 1.50, "seviye": 0.90},
    "st pauli": {"hucum": 1.08, "savunma": 1.30, "seviye": 0.86},
    "elversberg": {"hucum": 1.28, "savunma": 1.34, "seviye": 0.84},
    "holstein kiel": {"hucum": 1.24, "savunma": 1.72, "seviye": 0.80},
    "bochum": {"hucum": 1.15, "savunma": 1.72, "seviye": 0.80},

    # --- FRANSA LIGUE 1 & LIGUE 2 (2026-27) ---
    "psg": {"hucum": 2.15, "savunma": 1.08, "seviye": 1.36},
    "monaco": {"hucum": 1.92, "savunma": 1.15, "seviye": 1.24},
    "marsilya": {"hucum": 1.82, "savunma": 1.18, "seviye": 1.22},
    "lille": {"hucum": 1.70, "savunma": 1.08, "seviye": 1.20},
    "lyon": {"hucum": 1.76, "savunma": 1.28, "seviye": 1.16},
    "lens": {"hucum": 1.46, "savunma": 1.06, "seviye": 1.15},
    "nice": {"hucum": 1.58, "savunma": 1.14, "seviye": 1.15},
    "brest": {"hucum": 1.48, "savunma": 1.24, "seviye": 1.08},
    "rennes": {"hucum": 1.45, "savunma": 1.28, "seviye": 1.05},
    "strasbourg": {"hucum": 1.55, "savunma": 1.42, "seviye": 1.02},
    "reims": {"hucum": 1.38, "savunma": 1.34, "seviye": 1.00},
    "lorient": {"hucum": 1.55, "savunma": 1.18, "seviye": 1.00},
    "paris fc": {"hucum": 1.44, "savunma": 1.20, "seviye": 0.98},
    "toulouse": {"hucum": 1.34, "savunma": 1.25, "seviye": 0.96},
    "auxerre": {"hucum": 1.38, "savunma": 1.42, "seviye": 0.95},
    "metz": {"hucum": 1.32, "savunma": 1.30, "seviye": 0.90},
    "nantes": {"hucum": 1.24, "savunma": 1.35, "seviye": 0.90},
    "guingamp": {"hucum": 1.28, "savunma": 1.28, "seviye": 0.86},
    "angers": {"hucum": 1.18, "savunma": 1.40, "seviye": 0.85},
    "saint-etienne": {"hucum": 1.15, "savunma": 1.62, "seviye": 0.85},
    "le havre": {"hucum": 1.06, "savunma": 1.44, "seviye": 0.84},
    "montpellier": {"hucum": 1.22, "savunma": 1.72, "seviye": 0.80},
    "le mans": {"hucum": 1.20, "savunma": 1.25, "seviye": 0.80},
    "troyes": {"hucum": 1.10, "savunma": 1.45, "seviye": 0.76},

    # --- HOLLANDA EREDIVISIE & PORTEKİZ LIGA PORTUGAL (2026-27) ---
    "psv": {"hucum": 2.10, "savunma": 1.12, "seviye": 1.25},
    "benfica": {"hucum": 1.98, "savunma": 1.00, "seviye": 1.26},
    "porto": {"hucum": 1.92, "savunma": 1.00, "seviye": 1.25},
    "sporting cp": {"hucum": 1.90, "savunma": 1.05, "seviye": 1.24},
    "feyenoord": {"hucum": 1.75, "savunma": 1.15, "seviye": 1.18},
    "ajax": {"hucum": 1.82, "savunma": 1.18, "seviye": 1.18},
    "braga": {"hucum": 1.70, "savunma": 1.14, "seviye": 1.14},
    "twente": {"hucum": 1.66, "savunma": 1.16, "seviye": 1.10},
    "az alkmaar": {"hucum": 1.55, "savunma": 1.15, "seviye": 1.06},
    "utrecht": {"hucum": 1.58, "savunma": 1.22, "seviye": 1.06},
    "vitoria guimaraes": {"hucum": 1.48, "savunma": 1.16, "seviye": 1.04},
    "famalicao": {"hucum": 1.32, "savunma": 1.22, "seviye": 0.96},
    "santa clara": {"hucum": 1.30, "savunma": 1.24, "seviye": 0.95},
    "moreirense": {"hucum": 1.26, "savunma": 1.24, "seviye": 0.94},
    "gil vicente": {"hucum": 1.25, "savunma": 1.32, "seviye": 0.90},
    "go ahead": {"hucum": 1.42, "savunma": 1.30, "seviye": 0.98},
    "heerenveen": {"hucum": 1.38, "savunma": 1.35, "seviye": 0.95},
    "nec": {"hucum": 1.38, "savunma": 1.34, "seviye": 0.95},
    "groningen": {"hucum": 1.25, "savunma": 1.35, "seviye": 0.90},
    "fortuna sittard": {"hucum": 1.24, "savunma": 1.35, "seviye": 0.90},
    "estoril praia": {"hucum": 1.28, "savunma": 1.40, "seviye": 0.90},
    "arouca": {"hucum": 1.20, "savunma": 1.40, "seviye": 0.86},
    "sparta rotterdam": {"hucum": 1.18, "savunma": 1.50, "seviye": 0.86},
    "excelsior": {"hucum": 1.24, "savunma": 1.50, "seviye": 0.85},
    "zwolle": {"hucum": 1.24, "savunma": 1.45, "seviye": 0.85},
    "willem 2": {"hucum": 1.20, "savunma": 1.40, "seviye": 0.85},
    "cambuur": {"hucum": 1.40, "savunma": 1.40, "seviye": 0.84},
    "ado": {"hucum": 1.36, "savunma": 1.40, "seviye": 0.84},
    "telstar": {"hucum": 1.28, "savunma": 1.45, "seviye": 0.80},
    "torreense": {"hucum": 1.15, "savunma": 1.35, "seviye": 0.80},

    # --- AVRUPA KUPALARI & DİĞER LİGLER (BELÇİKA, İSKOÇYA, AVUSTURYA, YUNANİSTAN, İSVİÇRE, İSKANDİNAVYA, DOĞU AVRUPA, MLS) ---
    "club brugge": {"hucum": 1.78, "savunma": 1.08, "seviye": 1.18},
    "union st.g": {"hucum": 1.70, "savunma": 1.10, "seviye": 1.14},
    "celtic": {"hucum": 1.82, "savunma": 1.10, "seviye": 1.16},
    "salzburg": {"hucum": 1.78, "savunma": 1.16, "seviye": 1.16},
    "olympiacos": {"hucum": 1.48, "savunma": 1.04, "seviye": 1.12},
    "rangers": {"hucum": 1.72, "savunma": 1.12, "seviye": 1.12},
    "genk": {"hucum": 1.68, "savunma": 1.18, "seviye": 1.10},
    "antwerp": {"hucum": 1.56, "savunma": 1.24, "seviye": 1.08},
    "gent": {"hucum": 1.54, "savunma": 1.22, "seviye": 1.06},
    "standard liege": {"hucum": 1.28, "savunma": 1.30, "seviye": 0.94},
    "anderlecht": {"hucum": 1.48, "savunma": 1.15, "seviye": 1.04},
    "panathinaikos": {"hucum": 1.55, "savunma": 1.12, "seviye": 1.10},
    "aek atina": {"hucum": 1.58, "savunma": 1.12, "seviye": 1.10},
    "paok": {"hucum": 1.60, "savunma": 1.12, "seviye": 1.10},
    "aris": {"hucum": 1.32, "savunma": 1.20, "seviye": 0.96},
    "ofi": {"hucum": 1.18, "savunma": 1.36, "seviye": 0.85},
    "kopenhag": {"hucum": 1.54, "savunma": 1.12, "seviye": 1.08},
    "midtjylland": {"hucum": 1.42, "savunma": 1.14, "seviye": 1.02},
    "brondby": {"hucum": 1.44, "savunma": 1.18, "seviye": 0.98},
    "nordsjaelland": {"hucum": 1.46, "savunma": 1.24, "seviye": 0.96},
    "slavia prag": {"hucum": 1.58, "savunma": 1.10, "seviye": 1.08},
    "sparta prag": {"hucum": 1.54, "savunma": 1.15, "seviye": 1.06},
    "viktoria plzen": {"hucum": 1.50, "savunma": 1.16, "seviye": 1.04},
    "jablonec": {"hucum": 1.25, "savunma": 1.35, "seviye": 0.85},
    "bodo glimt": {"hucum": 1.36, "savunma": 1.14, "seviye": 1.02},
    "brann": {"hucum": 1.56, "savunma": 1.18, "seviye": 1.02},
    "molde": {"hucum": 1.52, "savunma": 1.22, "seviye": 1.00},
    "rosenborg": {"hucum": 1.42, "savunma": 1.26, "seviye": 0.94},
    "lillestrom": {"hucum": 1.22, "savunma": 1.40, "seviye": 0.85},
    "sandefjord": {"hucum": 1.18, "savunma": 1.58, "seviye": 0.84},
    "malmo": {"hucum": 1.44, "savunma": 1.14, "seviye": 1.04},
    "djurgardens": {"hucum": 1.42, "savunma": 1.16, "seviye": 1.02},
    "hammarby": {"hucum": 1.42, "savunma": 1.18, "seviye": 1.00},
    "elfsborg": {"hucum": 1.38, "savunma": 1.18, "seviye": 0.98},
    "hacken": {"hucum": 1.55, "savunma": 1.36, "seviye": 0.96},
    "gais": {"hucum": 1.28, "savunma": 1.34, "seviye": 0.90},
    "sturm graz": {"hucum": 1.36, "savunma": 1.14, "seviye": 0.98},
    "lask linz": {"hucum": 1.38, "savunma": 1.16, "seviye": 0.96},
    "rapid wien": {"hucum": 1.40, "savunma": 1.18, "seviye": 0.96},
    "austria wien": {"hucum": 1.34, "savunma": 1.24, "seviye": 0.92},
    "young boys": {"hucum": 1.58, "savunma": 1.22, "seviye": 1.04},
    "basel": {"hucum": 1.52, "savunma": 1.22, "seviye": 1.02},
    "servette": {"hucum": 1.44, "savunma": 1.20, "seviye": 1.00},
    "lugano": {"hucum": 1.46, "savunma": 1.26, "seviye": 0.98},
    "sion": {"hucum": 1.34, "savunma": 1.32, "seviye": 0.94},
    "grasshoppers": {"hucum": 1.26, "savunma": 1.40, "seviye": 0.90},
    "shakhtar donetsk": {"hucum": 1.40, "savunma": 1.22, "seviye": 1.00},
    "dinamo kiev": {"hucum": 1.42, "savunma": 1.20, "seviye": 1.00},
    "dinamo zagreb": {"hucum": 1.48, "savunma": 1.18, "seviye": 1.02},
    "hajduk split": {"hucum": 1.40, "savunma": 1.18, "seviye": 0.96},
    "rijeka": {"hucum": 1.36, "savunma": 1.18, "seviye": 0.94},
    "kizilyildiz": {"hucum": 1.42, "savunma": 1.16, "seviye": 0.98},
    "partizan": {"hucum": 1.38, "savunma": 1.26, "seviye": 0.92},
    "ferencvaros": {"hucum": 1.48, "savunma": 1.18, "seviye": 0.98},
    "qarabag": {"hucum": 1.52, "savunma": 1.20, "seviye": 0.98},
    "sabah fk": {"hucum": 1.42, "savunma": 1.22, "seviye": 0.94},
    "lech poznan": {"hucum": 1.44, "savunma": 1.18, "seviye": 0.96},
    "legia varsova": {"hucum": 1.45, "savunma": 1.20, "seviye": 0.96},
    "rakow": {"hucum": 1.38, "savunma": 1.14, "seviye": 0.95},
    "jagiellonia": {"hucum": 1.40, "savunma": 1.24, "seviye": 0.90},
    "fcsb": {"hucum": 1.42, "savunma": 1.18, "seviye": 0.95},
    "cfr cluj": {"hucum": 1.36, "savunma": 1.16, "seviye": 0.94},
    "ludogorets": {"hucum": 1.44, "savunma": 1.18, "seviye": 0.95},
    "levski sofya": {"hucum": 1.30, "savunma": 1.20, "seviye": 0.86},
    "slovan bratislava": {"hucum": 1.38, "savunma": 1.30, "seviye": 0.90},
    "pafos": {"hucum": 1.38, "savunma": 1.26, "seviye": 0.90},
    "omonia": {"hucum": 1.42, "savunma": 1.28, "seviye": 0.92},
    "hapoel beer sheva": {"hucum": 1.40, "savunma": 1.16, "seviye": 0.94},
    "truidense": {"hucum": 1.18, "savunma": 1.16, "seviye": 0.88},
    "celje": {"hucum": 1.38, "savunma": 1.26, "seviye": 0.86},
    "olimpija ljubljana": {"hucum": 1.36, "savunma": 1.24, "seviye": 0.88},
    "maribor": {"hucum": 1.34, "savunma": 1.28, "seviye": 0.86},
    "hearts": {"hucum": 1.44, "savunma": 1.22, "seviye": 0.98},
    "aberdeen": {"hucum": 1.38, "savunma": 1.26, "seviye": 0.94},
    "hibernian": {"hucum": 1.35, "savunma": 1.30, "seviye": 0.92},
    "falkrik": {"hucum": 1.32, "savunma": 1.26, "seviye": 0.85},
    "inter miami": {"hucum": 2.15, "savunma": 1.32, "seviye": 1.20},
    "vancouver whitecaps": {"hucum": 1.65, "savunma": 1.22, "seviye": 1.08},
    "philadelphia union": {"hucum": 1.58, "savunma": 1.26, "seviye": 1.06},
    "san diego fc": {"hucum": 1.48, "savunma": 1.30, "seviye": 0.98},
    "austin fc": {"hucum": 1.34, "savunma": 1.35, "seviye": 0.94}
}

TAKMA_ADLAR = {
    "fb": "fenerbahce", "fener": "fenerbahce", "gs": "galatasaray", "cimbom": "galatasaray",
    "bjk": "besiktas", "besik": "besiktas", "ts": "trabzonspor", "trabzon": "trabzonspor",
    "ibfk": "basaksehir", "basak": "basaksehir", "amed": "amed", "amedspor": "amed",
    "samsun": "samsunspor", "eyup": "eyupspor", "gozgoz": "goztepe", "sivas": "sivasspor",
    "antalya": "antalyaspor", "alanya": "alanyaspor", "pasa": "kasimpasa", "rize": "rizespor",
    "antep": "gaziantep", "gfk": "gaziantep", "konya": "konyaspor", "kayseri": "kayserispor",
    "bodrum": "bodrum fk", "hatay": "hatayspor", "adana": "adana demirspor", "ads": "adana demirspor",
    "kocaeli": "kocaelispor", "istanbul": "istanbulspor", "karagumruk": "fatih karagumruk",
    "ankaragucu": "ankaragucu", "sakarya": "sakaryaspor", "bandirma": "bandirmaspor",
    "corum": "corum", "corum fk": "corum", "erzurum": "erzurumspor", "bolu": "boluspor", "umraniye": "umraniyespor",
    "manisa": "manisa fk", "gencler": "genclerbirligi", "keciorengucu": "keciorengucu",
    "igdir": "igdir fk", "erokspor": "esenler erokspor", "urfaspor": "sanliurfaspor",
    "malatya": "yeni malatyaspor", "city": "manchester city", "manc": "manchester city",
    "mancity": "manchester city", "man city": "manchester city", "united": "manchester united",
    "manu": "manchester united", "manchester united": "manchester united", "man u": "manchester united",
    "pool": "liverpool", "villa": "aston villa", "palace": "crystal palace", "spurs": "tottenham",
    "newcastle united": "newcastle", "wolves": "wolves", "wolverhampton": "wolves",
    "nottingham": "nottingham forest", "forest": "nottingham forest", "leicester city": "leicester",
    "middlesbrough": "middlesbrough", "boro": "middlesbrough", "millwall": "millwall",
    "leeds": "leeds", "leeds united": "leeds", "burnley fc": "burnley", "sheffield": "sheffield united",
    "sheffield utd": "sheffield united", "luton town": "luton", "watford fc": "watford",
    "real": "real madrid", "barca": "barcelona", "atletico": "atletico madrid", "atm": "atletico madrid",
    "sociedad": "real sociedad", "socciedad": "real sociedad", "bilbao": "athletic bilbao",
    "betis": "real betis", "celta": "celta vigo", "rayo": "rayo vallecano", "espanyol": "espanyol",
    "tenerife": "tenerife", "malaga": "malaga", "elche": "elche", "alaves": "alaves",
    "oviedo": "real oviedo", "cd mirandes": "mirandes",
    "juve": "juventus", "inter milan": "inter", "ac milan": "milan", "viola": "fiorentina",
    "toro": "torino", "hellas": "verona", "hellas verona": "verona", "sassuolo": "sassuolo",
    "sas": "sassuolo", "pisa": "pisa", "sudtirol": "sudtirol", "sudtriol": "sudtirol",
    "udinesse": "udinese", "udinese": "udinese", "us cremonese": "cremonese", "palermo fc": "palermo",
    "bayern": "bayern munih", "munih": "bayern munih", "fc bayern": "bayern munih",
    "leverkusen": "bayer leverkusen", "bayer": "bayer leverkusen",
    "bvb": "dortmund", "borussia dortmund": "dortmund", "rbl": "leipzig", "rb leipzig": "leipzig",
    "frankfurt": "eintracht frankfurt", "bremen": "werder bremen", "gladbach": "borussia monchengladbach",
    "monchengladbach": "borussia monchengladbach", "elversberg": "elversberg", "elvers": "elversberg",
    "psg": "psg", "paris": "psg", "paris sg": "psg", "paris saint germain": "psg", "paris saint-germain": "psg",
    "om": "marsilya", "ol": "lyon", "asm": "monaco", "st etienne": "saint-etienne", "saint etienne": "saint-etienne",
    "fc metz": "metz", "ea guingamp": "guingamp",
    "troyes": "troyes", "psv": "psv", "sparta": "sparta rotterdam", "rotterdam": "sparta rotterdam",
    "prag": "sparta prag", "sparta prag": "sparta prag", "slavia prag": "slavia prag",
    "shakhtar": "shakhtar donetsk", "shakhtar donetsk": "shakhtar donetsk",
    "dynamo kyiv": "dinamo kiev", "dinamo kyiv": "dinamo kiev", "kiev": "dinamo kiev",
    "aek": "aek atina", "aek atina": "aek atina", "athena": "aek atina",
    "pao": "panathinaikos", "panathinaikos": "panathinaikos", "paok selanik": "paok",
    "falkirk": "falkrik", "falkrik": "falkrik", "hearts": "hearts", "grasshoppers": "grasshoppers",
    "gc": "grasshoppers", "sion": "sion", "djurgardens": "djurgardens", "gais": "gais",
    "vancouver": "vancouver whitecaps", "austin": "austin fc", "bodo": "bodo glimt", "bodo/glimt": "bodo glimt",
    "sandefjord": "sandefjord", "san diego": "san diego fc", "san diego fc": "san diego fc",
    "philadelphia": "philadelphia union", "braga": "braga", "estoril": "estoril praia",
    "guimaraes": "vitoria guimaraes", "vitoria sc": "vitoria guimaraes",
    "benfica": "benfica", "levante": "levante", "sturm": "sturm graz", "sturm graz": "sturm graz",
    "celje": "celje", "sunderland": "sunderland", "olympiacos": "olympiacos", "jagiellonia": "jagiellonia",
    "az alkmaar": "az alkmaar", "alkmaar": "az alkmaar", "anderlecht": "anderlecht",
    "levski": "levski sofya", "levski sofya": "levski sofya", "ofi": "ofi", "ferencvaros": "ferencvaros",
    "lech poznan": "lech poznan", "legia": "legia varsova", "legia warsaw": "legia varsova",
    "union st.g": "union st.g", "union saint-gilloise": "union st.g",
    "union saint gilloise": "union st.g", "union sg": "union st.g",
    "torreense": "torreense", "norwich": "norwich", "norwich city": "norwich",
    "hull": "hull city", "coventry city": "coventry", "paris fc": "paris fc",
    "sporting": "sporting cp", "sporting lizbon": "sporting cp",
    "fortuna": "fortuna sittard", "fc porto": "porto", "porto": "porto",
    "west brom": "west bromwich", "wba": "west bromwich", "west bromwich albion": "west bromwich",
    "fc twente": "twente", "twente": "twente", "glasgow rangers": "rangers", "rangers": "rangers",
    "sk brann": "brann", "brann": "brann", "ud almeria": "almeria", "almeria": "almeria",
    "burgos cf": "burgos", "burgos": "burgos", "granada cf": "granada", "granada": "granada",
    "brugge": "club brugge", "club brugge": "club brugge", "krc genk": "genk", "genk": "genk",
    "kaa gent": "gent", "standard": "standard liege",
    "cd santa clara": "santa clara", "santa clara": "santa clara",
    "scpaderborn": "paderborn", "paderborn": "paderborn",
    "inter miami": "inter miami", "miami": "inter miami",
    "royal antwerp": "antwerp", "antwerp": "antwerp", "feyenoord rotterdam": "feyenoord",
    "lask": "lask linz", "linz": "lask linz", "slovan": "slovan bratislava", "bratislava": "slovan bratislava",
    "zagreb": "dinamo zagreb", "dinamo": "dinamo zagreb", "copenhagen": "kopenhag", "fc copenhagen": "kopenhag",
    "fc midtjylland": "midtjylland", "malmo ff": "malmo", "if elfsborg": "elfsborg", "bk hacken": "hacken",
    "crvena zvezda": "kizilyildiz", "red star": "kizilyildiz", "steaua": "fcsb", "steaua bukres": "fcsb",
    "karabag": "qarabag", "qarabag fk": "qarabag", "bsc young boys": "young boys", "fc basel": "basel",
    "nordsjaelland": "nordsjaelland", "fcn": "nordsjaelland", "pafos fc": "pafos", "fk jablonec": "jablonec",
    "frosinone": "frosinone", "fc utrecht": "utrecht", "go ahead eagles": "go ahead",
    "nec nijmegen": "nec", "nijmegen": "nec", "fc groningen": "groningen", "pec zwolle": "zwolle",
    "willem ii": "willem 2", "willem": "willem 2", "sc cambuur": "cambuur", "cambuur leeuwarden": "cambuur",
    "ado den haag": "ado", "den haag": "ado", "sc telstar": "telstar",
    "hamburger sv": "hamburg", "hsv": "hamburg", "fc koln": "koln", "1. fc koln": "koln",
    "schalke 04": "schalke", "fc schalke 04": "schalke", "fc schalke": "schalke",
    "fc lorient": "lorient", "le mans fc": "le mans",
    "racing santander": "racing", "real racing": "racing", "santander": "racing",
    "sabah": "sabah fk", "sabah baku": "sabah fk", "fk sabah": "sabah fk", "sabah baki": "sabah fk",
    "deportivo la coruna": "deportivo", "la coruna": "deportivo", "rc deportivo": "deportivo",
    "beer sheva": "hapoel beer sheva", "hapoel bs": "hapoel beer sheva", "h. beer sheva": "hapoel beer sheva",
    "hapoel beer-sheva": "hapoel beer sheva", "hapoel beersheba": "hapoel beer sheva", "beersheba": "hapoel beer sheva",
    "st truidense": "truidense", "sint truidense": "truidense", "sint-truidense": "truidense",
    "st. truidense": "truidense", "stvv": "truidense", "sint truiden": "truidense", "st truiden": "truidense",
    "omonia nicosia": "omonia", "omonia lefkosa": "omonia", "ac omonia": "omonia", "omonoia": "omonia"
}

def takim_bul(girdi):
    g = girdi.strip().replace("İ", "i").replace("I", "i").lower()
    g = g.replace("ı", "i").replace("ğ", "g").replace("ü", "u").replace("ş", "s").replace("ö", "o").replace("ç", "c").replace("æ", "ae")
    if g in TAKIM_PROFILLERI: return g
    if g in TAKMA_ADLAR: return TAKMA_ADLAR[g]
    for k in TAKIM_PROFILLERI:
        if len(k) >= 4 and (g in k or k in g): return k
    yakin = difflib.get_close_matches(g, list(TAKIM_PROFILLERI.keys()) + list(TAKMA_ADLAR.keys()), n=1, cutoff=0.55)
    if yakin:
        return TAKMA_ADLAR.get(yakin[0], yakin[0])
    return None

# Lig Gol Karakteri / Tempo Grupları (Hollanda ve Almanya Açık Savunmalı Takımlar = Açık/Golcü | İtalya/Fransa/İspanya Alt-Orta = Kısır/Taktiksel)
ACIK_GOLCU_TAKIMLAR = {
    "bayern munih", "bayer leverkusen", "leipzig", "stuttgart", "freiburg",
    "koln", "werder bremen", "borussia monchengladbach", "mainz", "wolfsburg", "augsburg", "hoffenheim",
    "heidenheim", "schalke", "elversberg", "holstein kiel", "bochum",
    "psv", "feyenoord", "ajax", "twente", "az alkmaar", "utrecht", "go ahead", "heerenveen", "nec", "groningen",
    "fortuna sittard", "sparta rotterdam", "excelsior", "zwolle", "willem 2", "cambuur", "ado", "telstar",
    "young boys", "basel", "lugano", "salzburg",
    "celtic", "rangers", "inter miami", "vancouver whitecaps", "philadelphia union"
}

KISIR_TAKTIK_TAKIMLAR = {
    "torino", "udinese", "genoa", "cagliari", "empoli", "lecce", "monza", "venezia", "bari", "sudtirol", "pisa",
    "brest", "nice", "lens", "reims", "toulouse", "nantes", "angers", "le havre", "metz", "le mans", "troyes",
    "getafe", "rayo vallecano", "mallorca", "osasuna", "real sociedad", "athletic bilbao", "real betis", "sevilla", "alaves", "leganes",
    "valladolid", "burgos", "tenerife", "levante", "elche", "malaga", "real oviedo", "mirandes", "union berlin",
    "olympiacos", "panathinaikos", "aek atina", "aris", "ofi", "hapoel beer sheva", "truidense", "sturm graz", "kizilyildiz", "bodo glimt"
}

AVRUPA_KUPASI_TAKIMLARI = {
    "galatasaray", "fenerbahce", "besiktas", "trabzonspor", "basaksehir",
    "real madrid", "barcelona", "atletico madrid", "athletic bilbao", "real sociedad", "real betis",
    "manchester city", "arsenal", "liverpool", "aston villa", "chelsea", "tottenham", "manchester united",
    "bayern munih", "bayer leverkusen", "dortmund", "leipzig", "stuttgart", "eintracht frankfurt", "hoffenheim",
    "inter", "juventus", "milan", "atalanta", "bologna", "roma", "lazio", "fiorentina",
    "psg", "monaco", "brest", "lille", "nice", "lyon",
    "sporting cp", "benfica", "porto", "braga", "psv", "feyenoord", "ajax", "twente", "az alkmaar",
    "celtic", "rangers", "salzburg", "sturm graz", "slavia prag", "bodo glimt", "malmo"
}

def sabika_hafizasi_getir():
    # Kalıcı kara liste yerine NET FORM HAFIZASI: Kazandıkça sabıka silinir, sadece net zararda olan (Kayıp > Kazanç) formsuz takımlar uyarılır!
    sabika = {}
    for kayit in st.session_state.get("istatistik_verileri", []):
        sonuc = str(kayit.get("Sonuç", ""))
        parcalar = str(kayit.get("Maç", "")).split(" vs ")
        if len(parcalar) == 2:
            e_k, d_k = takim_bul(parcalar[0]), takim_bul(parcalar[1])
            if "Kaybetti" in sonuc:
                if e_k:
                    sabika[e_k] = sabika.get(e_k, 0) + 1
                if d_k:
                    sabika[d_k] = sabika.get(d_k, 0) + 1
            elif "Kazandı" in sonuc:
                if e_k:
                    sabika[e_k] = max(0, sabika.get(e_k, 0) - 1)
                if d_k:
                    sabika[d_k] = max(0, sabika.get(d_k, 0) - 1)
    return sabika

def canli_api_takim_esle(espn_name):
    g = espn_name.lower().strip()
    # Rezerv / Altyapı / B takımlarını ana takımla eşleşip istatistiklerini bozmaması için filtrele
    if re.search(r'(\b(ii|reserve|reserves|u21|u23|u19|amateur|amateure|youth|jong)\b|\s+[b2]$)', g):
        return None
    g = g.replace("İ", "i").replace("I", "i").replace("ı", "i").replace("ğ", "g").replace("ü", "u").replace("ş", "s").replace("ö", "o").replace("ç", "c")
    words = re.findall(r'[a-z0-9]+', g)
    clean = " ".join([w for w in words if w not in ["fc", "cf", "sc", "sv", "afc", "ac", "fk", "bb", "as", "tsv", "rb", "1", "07", "04"]])
    
    if g in TAKIM_PROFILLERI: return g
    if g in TAKMA_ADLAR: return TAKMA_ADLAR[g]
    if clean in TAKIM_PROFILLERI: return clean
    if clean in TAKMA_ADLAR: return TAKMA_ADLAR[clean]
    
    for k in TAKIM_PROFILLERI:
        if len(k) >= 4 and (k == clean or f" {k} " in f" {clean} " or clean.startswith(f"{k} ") or clean.endswith(f" {k}")):
            return k
    for alias, target in TAKMA_ADLAR.items():
        if alias in ["city", "united", "real"]: continue
        if len(alias) >= 4 and (alias == clean or f" {alias} " in f" {clean} " or clean.startswith(f"{alias} ") or clean.endswith(f" {alias}")):
            return target
    return None

def canli_api_yukle():
    if os.path.exists(DOSYA_CANLI_API):
        try:
            with open(DOSYA_CANLI_API, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return {}
    return {}

def canli_api_guncelle():
    leagues = [
        'eng.1', 'esp.1', 'ita.1', 'ger.1', 'ger.2', 'fra.1',
        'tur.1', 'ned.1', 'por.1', 'bel.1', 'eng.2', 'esp.2', 'ita.2', 'fra.2'
    ]
    def fetch_standings(code):
        teams = {}
        try:
            url = f'https://site.api.espn.com/apis/v2/sports/soccer/{code}/standings'
            req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
            with urllib.request.urlopen(req, timeout=5) as resp:
                data = json.loads(resp.read().decode())
                entries = data.get('children', [{}])[0].get('standings', {}).get('entries', [])
                for e in entries:
                    raw_name = e['team']['displayName']
                    tk = canli_api_takim_esle(raw_name)
                    if not tk:
                        tk = canli_api_takim_esle(e['team'].get('shortDisplayName', ''))
                    if tk:
                        st_map = {s['name']: s.get('value', s.get('displayValue')) for s in e.get('stats', [])}
                        gp = float(st_map.get('gamesPlayed', 0) or 0)
                        if gp > 0:
                            gf = float(st_map.get('pointsFor', 0) or 0)
                            ga = float(st_map.get('pointsAgainst', 0) or 0)
                            teams[tk] = {
                                "lig": code,
                                "isim": raw_name,
                                "sira": int(float(st_map.get('rank', 0) or 0)),
                                "mac": int(gp),
                                "g": int(float(st_map.get('wins', 0) or 0)),
                                "b": int(float(st_map.get('ties', 0) or 0)),
                                "m": int(float(st_map.get('losses', 0) or 0)),
                                "ag": int(gf), "yg": int(ga),
                                "puan": int(float(st_map.get('points', 0) or 0)),
                                "mb_ag": round(gf / gp, 2),
                                "mb_yg": round(ga / gp, 2),
                                "mb_toplam": round((gf + ga) / gp, 2),
                                "karne": f"{int(float(st_map.get('wins',0)))}G-{int(float(st_map.get('ties',0)))}B-{int(float(st_map.get('losses',0)))}M"
                            }
        except Exception:
            pass
        return teams

    canli_db = {}
    with concurrent.futures.ThreadPoolExecutor(max_workers=10) as ex:
        all_results = list(ex.map(fetch_standings, leagues))
        for res in all_results:
            for k, v in res.items():
                if k not in canli_db:
                    canli_db[k] = v
                else:
                    mevcut_lig = canli_db[k].get("lig", "")
                    yeni_lig = v.get("lig", "")
                    if ".1" in mevcut_lig and ".2" in yeni_lig:
                        continue
                    canli_db[k] = v

    try:
        with open(DOSYA_CANLI_API, "w", encoding="utf-8") as f:
            json.dump(canli_db, f, ensure_ascii=False, indent=2)
    except Exception:
        pass
    return canli_db

def canli_api_fikstur_cek(tarih_str=None):
    if not tarih_str:
        tarih_str = datetime.now().strftime("%Y%m%d")
    ligler = ['eng.1', 'esp.1', 'ita.1', 'ger.1', 'fra.1', 'tur.1', 'ned.1', 'por.1', 'ger.2']
    mac_listesi = []
    gorulen = set()
    def fetch_lig_fikstur(code):
        res = []
        try:
            url = f'https://site.api.espn.com/apis/site/v2/sports/soccer/{code}/scoreboard?dates={tarih_str}'
            req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
            with urllib.request.urlopen(req, timeout=5) as resp:
                data = json.loads(resp.read().decode())
                for ev in data.get('events', []):
                    comp = ev['competitions'][0]
                    c_home = [c for c in comp['competitors'] if c['homeAway'] == 'home'][0]
                    c_away = [c for c in comp['competitors'] if c['homeAway'] == 'away'][0]
                    h_name = c_home['team']['displayName']
                    a_name = c_away['team']['displayName']
                    h_tk = canli_api_takim_esle(h_name) or canli_api_takim_esle(c_home['team'].get('shortDisplayName', ''))
                    a_tk = canli_api_takim_esle(a_name) or canli_api_takim_esle(c_away['team'].get('shortDisplayName', ''))
                    if h_tk and a_tk:
                        res.append(f"{h_tk.title()} vs {a_tk.title()}")
        except Exception:
            pass
        return res

    with concurrent.futures.ThreadPoolExecutor(max_workers=8) as ex:
        for lig_maclar in ex.map(fetch_lig_fikstur, ligler):
            for m in lig_maclar:
                if m not in gorulen:
                    gorulen.add(m)
                    mac_listesi.append(m)
    return "\n".join(mac_listesi)

def canli_biten_skorlari_getir():
    ligler = ['eng.1', 'esp.1', 'ita.1', 'ger.1', 'fra.1', 'tur.1', 'ned.1', 'por.1', 'ger.2', 'eng.2', 'esp.2', 'ita.2', 'fra.2', 'bel.1']
    bugun = datetime.now()
    tarihler = [(bugun - timedelta(days=i)).strftime("%Y%m%d") for i in range(4)]
    gorevler = [(lig, t) for lig in ligler for t in tarihler]
    
    def cek(args):
        lig, t = args
        url = f"https://site.api.espn.com/apis/site/v2/sports/soccer/{lig}/scoreboard?dates={t}"
        try:
            req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
            with urllib.request.urlopen(req, timeout=4) as resp:
                data = json.loads(resp.read().decode('utf-8'))
                events = data.get('events', [])
                items = []
                for ev in events:
                    status = ev.get('status', {}).get('type', {})
                    if status.get('completed', False):
                        comps = ev.get('competitions', [{}])[0].get('competitors', [])
                        if len(comps) == 2:
                            home_comp = comps[0] if comps[0].get('homeAway') == 'home' else comps[1]
                            away_comp = comps[1] if comps[0].get('homeAway') == 'home' else comps[0]
                            h_name = home_comp.get('team', {}).get('displayName', '')
                            a_name = away_comp.get('team', {}).get('displayName', '')
                            h_score = int(home_comp.get('score', 0))
                            a_score = int(away_comp.get('score', 0))
                            items.append((h_name, a_name, h_score, a_score))
                return items
        except Exception:
            return []

    skor_db = {}
    with concurrent.futures.ThreadPoolExecutor(max_workers=16) as executor:
        for sub in executor.map(cek, gorevler):
            for h_name, a_name, h_score, a_score in sub:
                ek = takim_bul(h_name) or canli_api_takim_esle(h_name)
                dk = takim_bul(a_name) or canli_api_takim_esle(a_name)
                if ek and dk:
                    skor_db[(ek, dk)] = (h_score, a_score)
    return skor_db

def tahmin_sonucunu_belirle(tahmin_str, h_score, a_score):
    toplam = h_score + a_score
    t = str(tahmin_str).upper()
    t = t.replace("Ü", "U").replace("İ", "I").replace("Ş", "S").replace("Ö", "O").replace("Ç", "C")
    
    # 1. Kombine / Çoklu Seçenekler (Öncelikli: tekli '1.5 ÜST' ya da 'MS 1' gibi kurallar önce yakalamasın!)
    if ("MS 1" in t or t.startswith("1 &") or t.startswith("1&") or " 1 &" in t) and "1.5" in t:
        return h_score > a_score and toplam >= 2
    elif ("MS 2" in t or t.startswith("2 &") or t.startswith("2&") or " 2 &" in t) and "1.5" in t:
        return a_score > h_score and toplam >= 2
    elif ("MS 1" in t or t.startswith("1 &") or t.startswith("1&") or " 1 &" in t) and "2.5" in t:
        return h_score > a_score and toplam >= 3
    elif ("MS 2" in t or t.startswith("2 &") or t.startswith("2&") or " 2 &" in t) and "2.5" in t:
        return a_score > h_score and toplam >= 3
    elif ("MS 1" in t or t.startswith("1 &") or t.startswith("1&")) and "KG VAR" in t:
        return h_score > a_score and a_score >= 1
    elif ("MS 2" in t or t.startswith("2 &") or t.startswith("2&")) and "KG VAR" in t:
        return a_score > h_score and h_score >= 1
    elif "1X" in t and "1.5" in t:
        return h_score >= a_score and toplam >= 2
    elif "X2" in t and "1.5" in t:
        return a_score >= h_score and toplam >= 2

    # 2. Özel Takım / Yarı Golleri
    elif "EV 1.5" in t:
        return h_score >= 2
    elif "DEP 1.5" in t:
        return a_score >= 2
    elif "IY 0.5" in t or "ILK YARI 0.5" in t:
        return toplam >= 1

    # 3. Çifte Şans
    elif "1X" in t:
        return h_score >= a_score
    elif "X2" in t:
        return a_score >= h_score

    # 4. Maç Sonucu
    elif "MS 0" in t or "BERABERLIK" in t or t.strip() in ["0", "X"]:
        return h_score == a_score
    elif "MS 1" in t:
        return h_score > a_score
    elif "MS 2" in t:
        return a_score > h_score

    # 5. Genel Alt / Üst ve KG
    elif "2.5 ALT" in t:
        return toplam <= 2
    elif "2.5 UST" in t:
        return toplam >= 3
    elif "1.5 UST" in t:
        return toplam >= 2
    elif "KG VAR" in t:
        return h_score >= 1 and a_score >= 1
    elif "KG YOK" in t:
        return h_score == 0 or a_score == 0

    return False

def mac_hesapla(ev_key, dep_key, ev_mod=None, dep_mod=None):
    ep = TAKIM_PROFILLERI[ev_key].copy()
    dp = TAKIM_PROFILLERI[dep_key].copy()
    radar_uyarilari = []

    # 🚑 Kadro / Sakatlık & Fikstür Yorgunluğu Radarı
    if ev_mod:
        if ev_mod.get("forvet_yok"):
            ep["hucum"] = max(0.85, ep["hucum"] - 0.20)
            radar_uyarilari.append(f"🎯 {ev_key.title()}: As Golcü Eksik (-0.20 Hücum)")
        if ev_mod.get("kaleci_yok"):
            ep["savunma"] = min(1.85, ep["savunma"] + 0.25)
            radar_uyarilari.append(f"🧤 {ev_key.title()}: As Kaleci/Defans Sakat (+0.25 Zaaf)")
        if ev_mod.get("avrupa_yorgun"):
            ep["seviye"] -= 0.08
            radar_uyarilari.append(f"⚡ {ev_key.title()}: Hafta İçi Ağır Fikstür / Yorgunluk Riski")

    if dep_mod:
        if dep_mod.get("forvet_yok"):
            dp["hucum"] = max(0.85, dp["hucum"] - 0.20)
            radar_uyarilari.append(f"🎯 {dep_key.title()}: As Golcü Eksik (-0.20 Hücum)")
        if dep_mod.get("kaleci_yok"):
            dp["savunma"] = min(1.85, dp["savunma"] + 0.25)
            radar_uyarilari.append(f"🧤 {dep_key.title()}: As Kaleci/Defans Sakat (+0.25 Zaaf)")
        if dep_mod.get("avrupa_yorgun"):
            dp["seviye"] -= 0.08
            radar_uyarilari.append(f"⚡ {dep_key.title()}: Hafta İçi Ağır Fikstür / Yorgunluk Riski")

    sabika_haritasi = sabika_hafizasi_getir()
    ev_sabika = sabika_haritasi.get(ev_key, 0)
    dep_sabika = sabika_haritasi.get(dep_key, 0)
    canli_db = canli_api_yukle()
    canli_ev = canli_db.get(ev_key)
    canli_dep = canli_db.get(dep_key)

    seviye_farki = ep["seviye"] - dp["seviye"]
    mutlak_fark = abs(seviye_farki)
    max_seviye = max(ep["seviye"], dp["seviye"])
    min_seviye = min(ep["seviye"], dp["seviye"])
    ortalama_savunma = (ep["savunma"] + dp["savunma"]) / 2.0
    derbi_kilit_tuzagi = (
        min_seviye >= 1.20
        and max_seviye <= 1.28
        and mutlak_fark <= 0.08
        and min(ep["savunma"], dp["savunma"]) >= 1.12
    )
    alt_lig_denk_tuzak = (
        min_seviye < 1.00
        and max_seviye <= 1.05
        and mutlak_fark <= 0.10
        and ortalama_savunma > 1.20
    )
    iki_acik_takim = (
        ev_key in ACIK_GOLCU_TAKIMLAR
        and dep_key in ACIK_GOLCU_TAKIMLAR
        and not (min_seviye < 1.05 and mutlak_fark >= 0.20)
        and not (mutlak_fark <= 0.12 and ortalama_savunma <= 1.20)
        and not derbi_kilit_tuzagi
        and not alt_lig_denk_tuzak
    )
    zayif_halka_otobus = (min_seviye < 1.05 and max_seviye <= 1.28 and not iki_acik_takim)
    denk_taktik_kilit = (
        mutlak_fark <= 0.10
        and max_seviye <= 1.16
        and ortalama_savunma <= 1.18
        and ev_key not in ACIK_GOLCU_TAKIMLAR
        and dep_key not in ACIK_GOLCU_TAKIMLAR
    )

    # 1. Dinamik Ev Sahibi & Seviye Çarpanı
    if max_seviye < 1.10 and mutlak_fark <= 0.12:
        ev_carpani, dep_carpani = 1.05, 0.95
        seviye_us = 0.30
    else:
        ev_carpani, dep_carpani = 1.09, 0.91
        seviye_us = 0.42

    exp_h = (ep["hucum"] * dp["savunma"] / 1.35) * ev_carpani
    exp_a = (dp["hucum"] * ep["savunma"] / 1.35) * dep_carpani

    seviye_orani = (ep["seviye"] / dp["seviye"]) ** seviye_us
    exp_h *= min(1.25, max(0.80, seviye_orani))
    exp_a /= min(1.25, max(0.80, seviye_orani))

    # 2. Lig Gol Karakteri & Zayıf Halka / Denk Maç Kilitlenmesi Çarpanı
    tempo_carpani = 1.0
    if iki_acik_takim:
        tempo_carpani = 1.08
    elif ev_key in ACIK_GOLCU_TAKIMLAR or dep_key in ACIK_GOLCU_TAKIMLAR:
        if ev_key not in KISIR_TAKTIK_TAKIMLAR and dep_key not in KISIR_TAKTIK_TAKIMLAR:
            tempo_carpani = 1.04
    elif ev_key in KISIR_TAKTIK_TAKIMLAR and dep_key in KISIR_TAKTIK_TAKIMLAR:
        tempo_carpani = 0.90
    elif (ev_key in KISIR_TAKTIK_TAKIMLAR or dep_key in KISIR_TAKTIK_TAKIMLAR) and max_seviye < 1.26:
        tempo_carpani = 0.93

    # İki takım da üst düzey (seviye >= 1.10) ve kilitli değilse hücum kalitesi kilidi açar;
    # denk derbiler (Chelsea-Tottenham, Dortmund-Frankfurt, Newcastle-Villa) veya alt lig denk maçlarında (Paderborn-Hamburg) el freni çekilir!
    if denk_taktik_kilit:
        tempo_carpani *= 0.80
    elif derbi_kilit_tuzagi or alt_lig_denk_tuzak:
        tempo_carpani *= 0.86
    elif min_seviye >= 1.10 and ev_key not in KISIR_TAKTIK_TAKIMLAR and dep_key not in KISIR_TAKTIK_TAKIMLAR:
        tempo_carpani *= 1.03
    elif zayif_halka_otobus:
        tempo_carpani *= 0.88

    if (ev_mod and ev_mod.get("avrupa_yorgun")) or (dep_mod and dep_mod.get("avrupa_yorgun")):
        tempo_carpani *= 0.94

    exp_h *= tempo_carpani
    exp_a *= tempo_carpani

    # 3. Dixon-Coles Düşük Skor Korelasyonu (Taktiksel Kilitlenme Düzeltmesi)
    rho = -0.06
    if denk_taktik_kilit:
        rho = -0.15
    elif derbi_kilit_tuzagi or alt_lig_denk_tuzak or (mutlak_fark <= 0.15 and ortalama_savunma <= 1.20) or zayif_halka_otobus:
        rho = -0.12
    elif tempo_carpani >= 1.06:
        rho = -0.02

    matrix = np.zeros((6, 6))
    for h in range(6):
        for a in range(6):
            p_base = poisson.pmf(h, exp_h) * poisson.pmf(a, exp_a)
            tau = 1.0
            if h == 0 and a == 0:
                tau = 1.0 - (exp_h * exp_a * rho)
            elif h == 0 and a == 1:
                tau = 1.0 + (exp_h * rho)
            elif h == 1 and a == 0:
                tau = 1.0 + (exp_a * rho)
            elif h == 1 and a == 1:
                tau = 1.0 - rho
            matrix[h, a] = max(0.0, p_base * tau)

    matrix = (matrix / np.sum(matrix)) * 100
    p_ev = float(np.sum(np.tril(matrix, -1)))
    p_ber = float(np.sum(np.diag(matrix)))
    p_dep = float(np.sum(np.triu(matrix, 1)))
    p_15_ust = float(100 - (matrix[0, 0] + matrix[1, 0] + matrix[0, 1]))
    p_25_ust = float(100 - (matrix[0, 0] + matrix[1, 0] + matrix[0, 1] + matrix[1, 1] + matrix[2, 0] + matrix[0, 2]))
    p_25_alt = float(100 - p_25_ust)
    p_kg_yok = float(np.sum(matrix[0, :]) + np.sum(matrix[:, 0]) - matrix[0, 0])
    p_kg_var = float(100 - p_kg_yok)
    p_1x = float(p_ev + p_ber)
    p_x2 = float(p_dep + p_ber)
    toplam_xg = exp_h + exp_a

    # Oran Katlayıcı Özel Market Olasılıkları (Ev/Dep 1.5 Üst, MS & 1.5 Üst, İlk Yarı 0.5 Üst)
    p_ev_15_ust = float(100.0 - np.sum(matrix[0:2, :]))
    p_dep_15_ust = float(100.0 - np.sum(matrix[:, 0:2]))
    p_ms1_15_ust = float(max(0.0, p_ev - matrix[1, 0]))
    p_ms2_15_ust = float(max(0.0, p_dep - matrix[0, 1]))
    iy_xg = toplam_xg * 0.44
    p_iy_05_ust = float((1.0 - np.exp(-iy_xg)) * 100.0)

    # 4. Öz-Öğrenmeli Dinamik Net Form Cezası (Kazandıkça Sıfırlanan Hafıza - Kalıcı Kara Liste Yok!)
    max_sabika = max(ev_sabika, dep_sabika)
    sabika_ceza = min(6.0, max_sabika * 2.0) if max_sabika >= 2 else 0.0
    sabika_etiketi = ""
    if max_sabika >= 2:
        sabikali_isim = f"{ev_key.title()} (Net -{ev_sabika})" if ev_sabika >= dep_sabika else f"{dep_key.title()} (Net -{dep_sabika})"
        sabika_etiketi = f"⚠️ Formsuz Takım: {sabikali_isim}"

    # 5. KARAR MOTORU & ORAN KATLAYICI SEÇİCİ
    durum, aksiyon, guven_orani = "SARI", "PAS GEÇ / RİSKLİ", 0.0
    tuzak_notu = ""

    ms1_baraj = 64.0 if ep["savunma"] >= 1.25 else 61.0
    ms2_baraj = 62.0 if dp["savunma"] >= 1.25 else 59.5

    if derbi_kilit_tuzagi or alt_lig_denk_tuzak:
        durum, aksiyon, guven_orani = "SARI", "PAS GEÇ / RİSKLİ", 0.0
    # B) Yüksek Tempolu Açık Gol Şölenleri (3.65+ xG & %70+ 2.5Ü): Deplasman Taraf Bahsi Tuzağı Yerine 2.5 ÜST! (Hoffenheim, Stuttgart & PSG-Barça Kuralı)
    elif p_15_ust >= 88.2 and p_25_ust >= 70.0 and toplam_xg >= 3.65 and (mutlak_fark >= 0.09 or max_seviye >= 1.44):
        durum, aksiyon, guven_orani = "YESIL", "2.5 ÜST", p_25_ust
    # A) Net Favori Galibiyeti (MS 1 / MS 2)
    elif p_ev >= ms1_baraj and (seviye_farki >= 0.14 or p_ev >= 64.0):
        durum, aksiyon, guven_orani = "YESIL", f"MS 1 ({ev_key.title()})", p_ev
    elif p_dep >= ms2_baraj and (seviye_farki <= -0.14 or p_dep >= 63.0):
        durum, aksiyon, guven_orani = "YESIL", f"MS 2 ({dep_key.title()})", p_dep
    # C) İdeal Banko 1.5 ÜST Bandı (Zayıf Halka Otobüs Kilitlenmesi Korumalı!)
    elif (
        p_15_ust >= 74.0
        and toplam_xg >= 2.55
        and not (zayif_halka_otobus and p_15_ust < 81.5)
        and not (mutlak_fark <= 0.05 and ortalama_savunma <= 1.15 and toplam_xg < 2.75)
    ):
        durum, aksiyon, guven_orani = "YESIL", "1.5 ÜST", p_15_ust
    # D) 2.5 ÜST (Minimal baraj: %58.5, Zayıf halka otobüs maçlarında kapalı)
    elif p_25_ust >= 58.5 and toplam_xg >= 2.85 and not zayif_halka_otobus:
        durum, aksiyon, guven_orani = "YESIL", "2.5 ÜST", p_25_ust
    # E) KG VAR (Minimal baraj: %59.0)
    elif p_kg_var >= 59.0 and exp_h >= 1.15 and exp_a >= 1.12 and not zayif_halka_otobus:
        durum, aksiyon, guven_orani = "YESIL", "KG VAR", p_kg_var
    # F) X2 Çifte Şans (Minimal baraj: %73.5 - Kısır deplasman tuzağı korumalı)
    elif p_x2 >= 73.5 and dp["seviye"] >= 1.12 and seviye_farki <= -0.12 and exp_a >= 1.38:
        durum, aksiyon, guven_orani = "YESIL", "X2 Çifte Şans", p_x2
    # G) 1X Çifte Şans (Minimal baraj: %73.5 - Alt sıra/kısır 1X tuzağı korumalı)
    elif p_1x >= 73.5 and ep["seviye"] >= 1.05 and exp_h >= 1.48 and (seviye_farki >= 0.12 or ep["savunma"] <= 1.10):
        durum, aksiyon, guven_orani = "YESIL", "1X Çifte Şans", p_1x
    # H) Gerçek 2.5 ALT & Taktiksel Denk Maç Kilitlenmesi (Deplasman Favorisi Tuzağı ve Açık Takım Korumalı!)
    elif (
        p_25_alt >= 60.0
        and toplam_xg <= 2.25
        and seviye_farki > -0.12
        and ev_key not in ACIK_GOLCU_TAKIMLAR
        and dep_key not in ACIK_GOLCU_TAKIMLAR
        and ep["savunma"] <= 1.20
        and dp["savunma"] <= 1.20
        and ep["hucum"] <= 1.60
        and dp["hucum"] <= 1.60
    ):
        durum, aksiyon, guven_orani = "YESIL", "2.5 ALT", p_25_alt
    # I) KG YOK (Minimal baraj: %60.0 - Deplasman favorisi tuzağı korumalı!)
    elif p_kg_yok >= 60.0 and min(exp_h, exp_a) <= 0.80 and seviye_farki > -0.12 and ep["savunma"] <= 1.20:
        durum, aksiyon, guven_orani = "YESIL", "KG YOK", p_kg_yok

    # 🔥 Oran Katlayıcı Alternatif Tercih (Daha Yüksek Oran İsteyenler veya 1.5Ü Kapalıysa Alternatif)
    katlayici_aksiyon = "-"
    katlayici_yuzde = 0.0
    # 1) Çelik savunmalı favori (Örn: Inter 1-0 Shakhtar) veya 2.5 ALT maçları -> KG YOK öner!
    if "MS 1" in aksiyon and ep["savunma"] <= 0.90 and exp_a <= 0.85 and p_kg_yok >= 56.0:
        katlayici_aksiyon, katlayici_yuzde = f"KG YOK (%{p_kg_yok:.0f})", p_kg_yok
    elif aksiyon == "2.5 ALT" and p_kg_yok >= 54.0:
        katlayici_aksiyon, katlayici_yuzde = f"KG YOK (%{p_kg_yok:.0f})", p_kg_yok
    elif p_ms1_15_ust >= 58.0 and "MS 1" in aksiyon:
        katlayici_aksiyon, katlayici_yuzde = f"MS 1 & 1.5 ÜST (%{p_ms1_15_ust:.0f})", p_ms1_15_ust
    elif p_ms2_15_ust >= 56.0 and "MS 2" in aksiyon:
        katlayici_aksiyon, katlayici_yuzde = f"MS 2 & 1.5 ÜST (%{p_ms2_15_ust:.0f})", p_ms2_15_ust
    # 2) 1-1 bitmeye aday dengeli derbiler (Man Utd-Tottenham 1-1) veya sert savunmalı dev maçları (Stuttgart-Atletico 1-1) -> 2.5 ÜST yerine KG VAR!
    elif (
        aksiyon == "1.5 ÜST"
        and p_kg_var >= 60.0
        and exp_h >= 1.20
        and exp_a >= 1.20
        and (
            min(ep["savunma"], dp["savunma"]) <= 0.94
            or (not (ev_key in ACIK_GOLCU_TAKIMLAR or dep_key in ACIK_GOLCU_TAKIMLAR) and mutlak_fark <= 0.05)
        )
    ):
        katlayici_aksiyon, katlayici_yuzde = f"KG VAR (%{p_kg_var:.0f})", p_kg_var
    # 3) Açık ve bol gollü maçlarda 2.5 ÜST
    elif p_25_ust >= 59.0 and aksiyon == "1.5 ÜST":
        katlayici_aksiyon, katlayici_yuzde = f"2.5 ÜST (%{p_25_ust:.0f})", p_25_ust
    # 4) İki takımın da gol bulacağı dengeli maçlarda (Örn: Celtic-Celta Vigo 1-2, Lille-GS 2-4) İY 0.5Ü yerine önce KG VAR!
    elif p_kg_var >= 60.0 and exp_h >= 1.15 and exp_a >= 1.10:
        katlayici_aksiyon, katlayici_yuzde = f"KG VAR (%{p_kg_var:.0f})", p_kg_var
    elif p_ev_15_ust >= 64.0:
        katlayici_aksiyon, katlayici_yuzde = f"Ev 1.5 ÜST (%{p_ev_15_ust:.0f})", p_ev_15_ust
    elif p_dep_15_ust >= 62.0:
        katlayici_aksiyon, katlayici_yuzde = f"Dep 1.5 ÜST (%{p_dep_15_ust:.0f})", p_dep_15_ust
    elif p_iy_05_ust >= 70.0 and ev_key not in KISIR_TAKTIK_TAKIMLAR and dep_key not in KISIR_TAKTIK_TAKIMLAR and aksiyon != "2.5 ALT":
        katlayici_aksiyon, katlayici_yuzde = f"İY 0.5 ÜST (%{p_iy_05_ust:.0f})", p_iy_05_ust
    elif "X2" in aksiyon and p_dep >= 50.0:
        katlayici_aksiyon, katlayici_yuzde = f"MS 2 ({dep_key.title()}) (%{p_dep:.0f})", p_dep
    elif "1X" in aksiyon and p_ev >= 52.0:
        katlayici_aksiyon, katlayici_yuzde = f"MS 1 ({ev_key.title()}) (%{p_ev:.0f})", p_ev

    # Eğer maç SARI (PAS) kaldıysa neden elendiğini açıkla
    if durum == "SARI":
        if derbi_kilit_tuzagi or (mutlak_fark <= 0.08 and min_seviye >= 1.14 and p_15_ust >= 70.0):
            tuzak_notu = f"🚨 DENK DERBİ / 6 PUAN KİLİDİ TUZAĞI ({ev_key.title()} vs {dep_key.title()}): Güçleri birbirine çok yakın ({ep['seviye']:.2f} vs {dp['seviye']:.2f}) iki üst sıra takımının kritik maçında el freni çekilir; Üst/KG tuzağına girilmez!"
        elif alt_lig_denk_tuzak:
            tuzak_notu = f"🚨 ALT LİG DENK MAÇ TUZAĞI ({ev_key.title()} vs {dep_key.title()}): İki denk alt klasman takımının ({ep['seviye']:.2f} vs {dp['seviye']:.2f}) mücadelesi 0-0 / 1-0 kilitlenmeye çok açıktır!"
        elif p_25_alt >= 58.0 and seviye_farki <= -0.12:
            tuzak_notu = f"🚨 DEPLASMAN FAVORİSİ ALT TUZAĞI ({ev_key.title()} vs {dep_key.title()}): Zayıf ev sahibi kendi seyircisi önünde açık oynarsa güçlü deplasman ({dep_key.title()}) kontradan maçı Üst'e patlatır!"
        elif zayif_halka_otobus and p_15_ust >= 70.0:
            zayif_takim = ev_key.title() if ep["seviye"] <= dp["seviye"] else dep_key.title()
            tuzak_notu = f"🚨 ZAYIF HALKA / OTOBÜS TUZAĞI ({zayif_takim}): Küçük/taktiksel takım kapanırsa maç 0-0 veya 1-0 kilitlenebilir (1.5Ü: %{p_15_ust:.0f})!"
        elif p_25_alt >= 58.0 and (ev_key in ACIK_GOLCU_TAKIMLAR or dep_key in ACIK_GOLCU_TAKIMLAR or ep["savunma"] > 1.20 or dp["savunma"] > 1.20):
            acik_takim = ev_key.title() if (ev_key in ACIK_GOLCU_TAKIMLAR or ep["savunma"] > 1.20) else dep_key.title()
            tuzak_notu = f"🚨 SAHTE 2.5 ALT TUZAĞI: Kağıt üzerinde Alt (%{p_25_alt:.0f}) görünse de {acik_takim} savunması açık; maç bir anda Üst'e patlayabilir!"
        elif p_1x >= 72.0 and (ep["seviye"] < 1.05 or exp_h < 1.48):
            tuzak_notu = f"🚨 SAHTE 1X TUZAĞI ({ev_key.title()}): Ev sahibi kısır ({exp_h:.2f} xG) veya orta/alt sıra; ilk golü yerse çeviremez!"
        elif tempo_carpani < 1.0 and p_15_ust >= 70.0:
            tuzak_notu = f"🚨 KISIR LİG / SAVUNMA KİLİDİ: Takımlar kontrollü/savunmacı karakterde (1.5Ü: %{p_15_ust:.0f}), 0-0 / 1-0 bitme riski var!"
        else:
            tuzak_notu = "⚠️ ORTADA / RİSKLİ MAÇ: Barajları geçemedi, kupona eklenmesi önerilmez."

    # 🤖 YZ Kalite & Otomatik Seçim Puanı (Gerçek Tutma İhtimali + Kulüp Kalite Güvencesi)
    if "MS 1" in aksiyon or "MS 2" in aksiyon:
        yz_kalite_puani = min(94.0, guven_orani + 10.5)
    elif "2.5 ÜST" in aksiyon:
        yz_kalite_puani = min(92.0, guven_orani + 11.5)
    elif "KG VAR" in aksiyon:
        yz_kalite_puani = min(90.0, guven_orani + 10.0)
    elif "Çifte Şans" in aksiyon:
        yz_kalite_puani = guven_orani - 4.5
    elif "2.5 ALT" in aksiyon:
        yz_kalite_puani = min(85.0, guven_orani + 10.0)
    else:
        yz_kalite_puani = guven_orani

    # Elit Kalite Güvencesi vs Zayıf Halka Cezası (2.5 ALT maçlarında taktiksel kilit ceza değil, avantajdır!)
    if "2.5 ALT" in aksiyon and (denk_taktik_kilit or zayif_halka_otobus):
        yz_kalite_puani += 1.0
    elif min_seviye >= 1.10 or max_seviye >= 1.28:
        yz_kalite_puani += 1.5
    elif zayif_halka_otobus:
        yz_kalite_puani -= 4.5

    if iki_acik_takim and ("ÜST" in aksiyon or "KG VAR" in aksiyon):
        yz_kalite_puani += 1.5

    # 🔥 Çift Onay Koruması (Real Betis vs Feyenoord 1-0 Kilitlenme Kalkanı):
    # Eğer 1.5 ÜST önerilen bir maçın Oran Katlayıcı sütunu "-" (boş) kaldıysa (ikinci bir gol onayı yoksa) YZ puanını kırp!
    if aksiyon == "1.5 ÜST" and katlayici_aksiyon == "-":
        yz_kalite_puani -= 3.5

    yz_kalite_puani -= sabika_ceza

    # 6. Canlı API Form & Kısırlık İnce Ayarı
    if canli_ev and canli_dep and canli_ev.get("mac", 0) >= 4 and canli_dep.get("mac", 0) >= 4:
        # İki takım da maç başı 1.05 golün altında atıyorsa ÜST tuzağına karşı koru
        if canli_ev["mb_ag"] <= 1.05 and canli_dep["mb_ag"] <= 1.05 and canli_ev["mb_toplam"] <= 2.30 and durum == "YESIL" and "ÜST" in aksiyon:
            durum, aksiyon, guven_orani = "SARI", "PAS GEÇ / RİSKLİ", 0.0
            tuzak_notu = f"🚨 CANLI FORM KISIRLIK TUZAĞI ({ev_key.title()} vs {dep_key.title()}): Bu sezon iki takım da ligde maç başı 1 golün altında üretiyor ({canli_ev['mb_ag']:.2f} vs {canli_dep['mb_ag']:.2f})!"
        elif durum == "YESIL" and "2.5 ALT" in aksiyon and (canli_ev.get("mb_toplam", 0) >= 3.20 and canli_dep.get("mb_toplam", 0) >= 3.20):
            durum, aksiyon, guven_orani = "SARI", "PAS GEÇ / RİSKLİ", 0.0
            tuzak_notu = f"⚠️ CANLI TEMPO & SAVUNMA ZAAFI TUZAĞI ({ev_key.title()} vs {dep_key.title()}): Kağıt üstünde 2.5 Alt görünse de canlı lig istatistiklerinde iki takımın da maçları çok gollü geçiyor ({canli_ev.get('mb_toplam', 0):.2f} vs {canli_dep.get('mb_toplam', 0):.2f} gol ort.); maç Üst'e patlayabilir!"
        elif "MS 1" in aksiyon and canli_ev.get("win_rate", 0) >= 70.0 and canli_dep.get("win_rate", 0) <= 35.0:
            yz_kalite_puani += 1.0
        elif "MS 2" in aksiyon and canli_dep.get("win_rate", 0) >= 70.0 and canli_ev.get("win_rate", 0) <= 35.0:
            yz_kalite_puani += 1.0
        elif ("MS 2" in aksiyon or "X2" in aksiyon) and canli_dep.get("sira", 10) <= 3 and canli_ev.get("sira", 10) >= 15:
            yz_kalite_puani += 4.5
        elif ("MS 1" in aksiyon or "1X" in aksiyon) and canli_ev.get("sira", 10) <= 3 and canli_dep.get("sira", 10) >= 15:
            yz_kalite_puani += 4.5

    min_oran = round(max(1.10, (100.0 / max(guven_orani, 50.0)) * 0.84), 2) if guven_orani > 0 else 0.0
    if durum == "YESIL" and yz_kalite_puani >= 79.0:
        kademe = "💎 YZ ELMAS"
    elif durum == "YESIL" and yz_kalite_puani >= 76.0:
        kademe = "🟢 YZ ONAYLI"
    elif durum == "YESIL":
        kademe = "🟡 SINIRDA (YEDEK)"
    else:
        kademe = "🔴 PAS / TUZAK"

    return {
        "exp_h": exp_h, "exp_a": exp_a, "toplam_xg": toplam_xg, "matrix": matrix,
        "p_ev": p_ev, "p_ber": p_ber, "p_dep": p_dep,
        "p_15_ust": p_15_ust, "p_25_ust": p_25_ust, "p_25_alt": p_25_alt,
        "p_kg_var": p_kg_var, "p_kg_yok": p_kg_yok, "p_1x": p_1x, "p_x2": p_x2,
        "p_ev_15_ust": p_ev_15_ust, "p_dep_15_ust": p_dep_15_ust,
        "p_ms1_15_ust": p_ms1_15_ust, "p_ms2_15_ust": p_ms2_15_ust, "p_iy_05_ust": p_iy_05_ust,
        "durum": durum, "aksiyon": aksiyon, "guven_orani": guven_orani,
        "katlayici_aksiyon": katlayici_aksiyon, "katlayici_yuzde": katlayici_yuzde,
        "yz_kalite_puani": yz_kalite_puani,
        "min_oran": min_oran, "kademe": kademe, "tuzak_notu": tuzak_notu,
        "sabika_etiketi": sabika_etiketi, "ev_sabika": ev_sabika, "dep_sabika": dep_sabika,
        "canli_ev": canli_ev, "canli_dep": canli_dep,
        "radar_uyarilari": radar_uyarilari
    }

col_baslik, col_tema = st.columns([5, 1])
with col_baslik:
    st.markdown(f"### ⚽ Poisson Pro 26/27 Tahmin & Kasa Motoru ({len(TAKIM_PROFILLERI)} Kulüp)")
with col_tema:
    if st.session_state.tema == "Siyah":
        if st.button("☀️", key="tema_degis_buton_A", use_container_width=False):
            st.session_state.tema = "Beyaz"
            st.rerun()
    else:
        if st.button("🌙", key="tema_degis_buton_B", use_container_width=False):
            st.session_state.tema = "Siyah"
            st.rerun()

tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs([
    "🔍 Tekli Analiz",
    "⚡ Bülten & Kombine",
    "📈 Kasa & Kurtarma Koçu",
    "📊 İstatistikler",
    "🛡️ Kupon Risk Analizi",
    "⚡ Canlı Asistan"
])

# ==============================================================================
# TAB 1: TEKLİ ANALİZ (2026-27 GÜÇ KARNESİ & TUZAK RÖNTGENİ)
# ==============================================================================
with tab1:
    takim_listesi = sorted(list(TAKIM_PROFILLERI.keys()))
    c1, c2 = st.columns(2)
    with c1:
        ev = st.selectbox("🏠 Ev Sahibi", takim_listesi, index=takim_listesi.index("galatasaray") if "galatasaray" in takim_listesi else 0)
    with c2:
        dep = st.selectbox("✈️ Deplasman", takim_listesi, index=takim_listesi.index("fenerbahce") if "fenerbahce" in takim_listesi else 1)

    with st.expander("🚑 Kadro / Sakatlık & Fikstür Yorgunluğu Radarı (İsteğe Bağlı)"):
        col_ek1, col_ek2 = st.columns(2)
        with col_ek1:
            st.markdown(f"**🏠 {ev.title()} Eksik & Yorgunluk:**")
            ev_forvet = st.checkbox("🎯 As Golcü / 10 Numara Eksik (-0.20 Hücum)", key="ev_forvet_cb")
            ev_kaleci = st.checkbox("🧤 As Kaleci / Savunma Lideri Sakat (+0.25 Zaaf)", key="ev_kaleci_cb")
            ev_avrupa = st.checkbox("⚡ Hafta İçi Ağır Avrupa Maçı Oynadı (Rotasyon Riski)", key="ev_avrupa_cb")
        with col_ek2:
            st.markdown(f"**✈️ {dep.title()} Eksik & Yorgunluk:**")
            dep_forvet = st.checkbox("🎯 As Golcü / 10 Numara Eksik (-0.20 Hücum)", key="dep_forvet_cb")
            dep_kaleci = st.checkbox("🧤 As Kaleci / Savunma Lideri Sakat (+0.25 Zaaf)", key="dep_kaleci_cb")
            dep_avrupa = st.checkbox("⚡ Hafta İçi Ağır Avrupa Maçı Oynadı (Rotasyon Riski)", key="dep_avrupa_cb")

    if st.button("🚀 Detaylı Analiz Et", use_container_width=True):
        if ev == dep:
            st.error("⚠️ Aynı takımı hem Ev Sahibi hem Deplasman olarak seçtin kanka! Lütfen iki farklı takım seç.")
            st.stop()
        ev_mod = {"forvet_yok": ev_forvet, "kaleci_yok": ev_kaleci, "avrupa_yorgun": ev_avrupa}
        dep_mod = {"forvet_yok": dep_forvet, "kaleci_yok": dep_kaleci, "avrupa_yorgun": dep_avrupa}
        res = mac_hesapla(ev, dep, ev_mod, dep_mod)
        ep = TAKIM_PROFILLERI[ev]
        dp = TAKIM_PROFILLERI[dep]
        matrix = res["matrix"]
        st.divider()

        if res.get("radar_uyarilari"):
            for rad_u in res["radar_uyarilari"]:
                st.warning(f"🚑 **KADRO / ROTASYON RADARI:** {rad_u} (Hücum/savunma zaafları ve tempo çarpanı modele dinamik yansıtıldı!)")

        if res["sabika_etiketi"]:
            st.error(f"🚨 **GEÇMİŞ SABIKA UYARISI:** {res['sabika_etiketi']} — Bu takım geçmişte kuponlarını yatırdığı için sistem güven barajını otomatik yükseltti!")

        if res["durum"] == "YESIL":
            st.success(
                f"{res['kademe']} | **SNIPER TAHMİN:** {res['aksiyon']} (**%{res['guven_orani']:.1f}**)  \n"
                f"💡 **Değer (Value) & Oran Kuralı:** Bu tercihi kupona eklemek için İddaa oranı **{res['min_oran']:.2f}** ile **{res['min_oran']+0.32:.2f}** aralığında olmalıdır (Oran çok daha yüksekse kadro/rotasyon tuzağı vardır!)."
            )
        else:
            st.warning(f"⚠️ **SNIPER KARARI: PAS GEÇ / RİSKLİ MAÇ**  \n{res['tuzak_notu']}")

        # Canlı API 2026-27 Sezon Karnesi (Varsa)
        cev, cdep = res.get("canli_ev"), res.get("canli_dep")
        if cev or cdep:
            with st.expander("🌐 2026-27 Canlı Sezon Karnesi (ESPN API - Canlı Form)", expanded=True):
                col_c1, col_c2 = st.columns(2)
                with col_c1:
                    if cev:
                        st.markdown(f"**🏠 {cev['isim']}** (`{cev['lig'].upper()}`)")
                        st.write(f"🏆 Sıra: **{cev['sira']}** | Puan: **{cev['puan']}** | Maç: **{cev['mac']}**")
                        st.write(f"📊 Form: **{cev['karne']}** (Galibiyet: %{cev.get('win_rate',0):.0f})")
                        st.write(f"⚽ Gol: **{cev['ag']} Attı** ({cev['mb_ag']}/m) - **{cev['yg']} Yedi** ({cev['mb_yg']}/m)")
                    else:
                        st.caption(f"🏠 {ev.title()}: Canlı lig verisi bulunamadı.")
                with col_c2:
                    if cdep:
                        st.markdown(f"**✈️ {cdep['isim']}** (`{cdep['lig'].upper()}`)")
                        st.write(f"🏆 Sıra: **{cdep['sira']}** | Puan: **{cdep['puan']}** | Maç: **{cdep['mac']}**")
                        st.write(f"📊 Form: **{cdep['karne']}** (Galibiyet: %{cdep.get('win_rate',0):.0f})")
                        st.write(f"⚽ Gol: **{cdep['ag']} Attı** ({cdep['mb_ag']}/m) - **{cdep['yg']} Yedi** ({cdep['mb_yg']}/m)")
                    else:
                        st.caption(f"✈️ {dep.title()}: Canlı lig verisi bulunamadı.")

        # Kulüp Güç & Beklenen Gol (xG) Karşılaştırma Kartları
        xg1, xg2, xg3 = st.columns(3)
        xg1.metric(f"🏠 {ev.title()} xG", f"{res['exp_h']:.2f} Gol", f"Seviye: {ep['seviye']:.2f} | Sav: {ep['savunma']:.2f}")
        xg2.metric(f"✈️ {dep.title()} xG", f"{res['exp_a']:.2f} Gol", f"Seviye: {dp['seviye']:.2f} | Sav: {dp['savunma']:.2f}")
        xg3.metric("🔥 Toplam Maç xG", f"{res['toplam_xg']:.2f} Gol", "Yüksek Tempo" if res["toplam_xg"] >= 2.80 else "Dengeli / Kısır")

        skorlar = {f"{h}-{a}": matrix[h, a] for h in range(6) for a in range(6)}
        sirali = sorted(skorlar.items(), key=lambda x: x[1], reverse=True)[:3]
        s1, s2, s3 = st.columns(3)
        s1.metric("1. Olası Skor", sirali[0][0], f"%{sirali[0][1]:.1f}")
        s2.metric("2. Olası Skor", sirali[1][0], f"%{sirali[1][1]:.1f}")
        s3.metric("3. Olası Skor", sirali[2][0], f"%{sirali[2][1]:.1f}")

        st.caption("🏆 Maç Sonu & Çifte Şans Olasılıkları")
        t1, t2 = st.columns(2)
        t1.metric(f"MS 1 ({ev[:10].title()})", f"%{res['p_ev']:.1f}")
        t2.metric(f"MS 2 ({dep[:10].title()})", f"%{res['p_dep']:.1f}")
        t3, t4 = st.columns(2)
        t3.metric("1X Çifte Şans", f"%{res['p_1x']:.1f}")
        t4.metric("X2 Çifte Şans", f"%{res['p_x2']:.1f}")

        st.caption("⚽ Gol, İlk Yarı ve Oran Katlayıcı Baremler")
        g1, g2, g3 = st.columns(3)
        g1.metric("1.5 ÜST", f"%{res['p_15_ust']:.1f}")
        g2.metric("2.5 ÜST", f"%{res['p_25_ust']:.1f}")
        g3.metric("İlk Yarı 0.5 ÜST", f"%{res['p_iy_05_ust']:.1f}")
        k1, k2, k3 = st.columns(3)
        k1.metric("KG VAR", f"%{res['p_kg_var']:.1f}")
        k2.metric(f"Ev 1.5 ÜST ({ev[:7].title()})", f"%{res['p_ev_15_ust']:.1f}")
        k3.metric(f"Dep 1.5 ÜST ({dep[:7].title()})", f"%{res['p_dep_15_ust']:.1f}")
        if res["katlayici_aksiyon"] != "-":
            st.info(f"🔥 **Bu Maç İçin Oran Katlayıcı Tercih:** **{res['katlayici_aksiyon']}** (Düşük oran yerine yüksek oran arayanlar için en değerli alternatif)")

        c_tek_ist1, c_tek_ist2 = st.columns(2)
        with c_tek_ist1:
            if st.button(f"💾 Ana Tercihi İstatistiğe Ekle ({res['aksiyon']})", key=f"tek_kaydet_ana_{ev}_{dep}", use_container_width=True):
                b_tarih = datetime.now().strftime("%d/%m/%Y")
                st.session_state.istatistik_verileri.append({
                    "Tarih": b_tarih, "Maç": f"{ev.title()} vs {dep.title()}", "Tahmin": res['aksiyon'], "Sonuç": "Bekliyor ⏳"
                })
                try:
                    pd.DataFrame(st.session_state.istatistik_verileri).to_csv(DOSYA_ISTATISTIK, index=False, encoding="utf-8")
                except Exception:
                    pass
                st.success(f"✅ {res['aksiyon']} tercihi İstatistik Defteri'ne eklendi!")
                st.rerun()
        with c_tek_ist2:
            if res["katlayici_aksiyon"] != "-":
                clean_kat = re.sub(r'\s*\(\s*%\s*\d+\s*\)', '', res['katlayici_aksiyon']).strip()
                if st.button(f"🔥 Kombine / Katlayıcı Tercihi Ekle ({clean_kat})", key=f"tek_kaydet_kat_{ev}_{dep}", use_container_width=True):
                    b_tarih = datetime.now().strftime("%d/%m/%Y")
                    st.session_state.istatistik_verileri.append({
                        "Tarih": b_tarih, "Maç": f"{ev.title()} vs {dep.title()}", "Tahmin": clean_kat, "Sonuç": "Bekliyor ⏳"
                    })
                    try:
                        pd.DataFrame(st.session_state.istatistik_verileri).to_csv(DOSYA_ISTATISTIK, index=False, encoding="utf-8")
                    except Exception:
                        pass
                    st.success(f"🔥 {clean_kat} kombine tercihi İstatistik Defteri'ne eklendi!")
                    st.rerun()

        with st.expander("📊 Skor Olasılık Matrisini Gör (0-0'dan 5-5'e)"):
            df_matrix = pd.DataFrame(np.round(matrix, 1), index=[f"{ev[:4]}. {i}" for i in range(6)], columns=[f"{dep[:4]}. {j}" for j in range(6)])
            st.markdown(df_matrix.to_html(classes='custom-table', escape=False), unsafe_allow_html=True)

# ==============================================================================
# TAB 2: BÜLTEN & OTOMATİK YZ DİNAMİK KUPON SEÇİCİ (SABİT SAYI YOK, BARAJ ÜSTÜ TÜM MAÇLAR!)
# ==============================================================================
with tab2:
    st.caption("📋 Tüm maçları alt alta yapıştır veya aşağıdaki butona basarak günün canlı bültenini API'den tek tıkla çek. Sen maç seçme; YZ belirlediğin barajın üstüne çıkan TÜM sağlam maçları otomatik seçip kuponlarını hazırlar:")

    col_api1, col_api2, col_api3 = st.columns(3)
    bugun_str = datetime.now().strftime("%Y%m%d")
    yarin_str = (datetime.now() + timedelta(days=1)).strftime("%Y%m%d")

    with col_api1:
        if st.button("🌐 Bugünün Maçlarını Çek", use_container_width=True, help=f"Bugünkü ({datetime.now().strftime('%d.%m.%Y')}) Avrupa maçlarını canlı API'den bültene aktarır"):
            with st.spinner("Bugünün canlı fikstürü çekiliyor..."):
                fiksturler = canli_api_fikstur_cek(bugun_str)
                if not fiksturler:
                    fiksturler = canli_api_fikstur_cek(yarin_str)
                st.session_state["bulten_metni_api"] = fiksturler
                st.rerun()
    with col_api2:
        if st.button("📅 Yarının Maçlarını Çek", use_container_width=True, help=f"Yarının ({(datetime.now() + timedelta(days=1)).strftime('%d.%m.%Y')}) Avrupa maçlarını canlı API'den bültene aktarır"):
            with st.spinner("Yarının canlı fikstürü çekiliyor..."):
                fiksturler = canli_api_fikstur_cek(yarin_str)
                st.session_state["bulten_metni_api"] = fiksturler
                st.rerun()
    with col_api3:
        if st.button("🔄 Puan & Formları Güncelle", use_container_width=True, help="14 büyük ligin canlı gol ve puan durumlarını ESPN'den anlık günceller"):
            with st.spinner("Canlı puan durumları senkronize ediliyor..."):
                db = canli_api_guncelle()
                st.success(f"✅ {len(db)} kulübün 2026-27 sezon karnesi güncellendi!")
                st.rerun()

    varsayilan_metin = st.session_state.get("bulten_metni_api", "")
    bulten_metni = st.text_area("Maçlar", value=varsayilan_metin, height=220, label_visibility="collapsed", placeholder="Örn:\nStuttgart vs Monchengladbach\nGo Ahead vs Telstar\nElfsborg vs Malmö\nTorino vs Monza\nBrest vs Nice")

    col_baraj1, col_baraj2 = st.columns([2, 1])
    with col_baraj1:
        yz_baraji = st.slider(
            "🤖 YZ Otomatik Maç Seçim Barajı (Bu puanın üstüne çıkan TÜM maçları YZ seçer)",
            min_value=70.0, max_value=85.0, value=76.5, step=0.5,
            help="76.5 ideal dengedir. Barajı düşürürsen daha çok maç seçer, yükseltirsen sadece Elmas maçları alır."
        )
    with col_baraj2:
        paket_boyutu = st.selectbox(
            "📦 Çok Maç Çıkarsa Kupon Bölme",
            [3, 2, 4],
            index=0,
            help="Örn: Barajı geçen 6 maç çıkarsa YZ bunları kaçarlı kuponlara bölsün?"
        )

    tara_btn = st.button("🤖 YZ Analiz Etsin ve Baraj Üstü Tüm Maçları Seçip Kuponları Kursun", use_container_width=True)

    if tara_btn:
        satirlar = bulten_metni.strip().split("\n")
        yz_secilenler, sinirda_kalanlar, sari_maclar, bulunamayanlar, ayni_takim_hatalari = [], [], [], [], []
        gorulen_maclar = set()
        for satir in satirlar:
            if not satir.strip():
                continue
            temiz_satir = satir.replace("İ", "i").replace("I", "i").lower()
            temiz_satir = temiz_satir.replace("saint-etienne", "saint etienne").replace("saint-gilloise", "saint gilloise").replace("paris saint-germain", "psg").replace("sint-truidense", "truidense").replace("beer-sheva", "beer sheva")
            if " - " in temiz_satir:
                parcalar = temiz_satir.split(" - ")
            elif " vs " in temiz_satir:
                parcalar = temiz_satir.split(" vs ")
            elif "-" in temiz_satir:
                parcalar = temiz_satir.split("-")
            else:
                parcalar = temiz_satir.split("vs")
            if len(parcalar) < 2:
                continue
            ev_k, dep_k = takim_bul(parcalar[0]), takim_bul(parcalar[1])
            if not ev_k or not dep_k:
                bulunamayanlar.append(satir.strip())
                continue
            if ev_k == dep_k:
                ayni_takim_hatalari.append(f"{ev_k.title()} vs {dep_k.title()} (Aynı takım)")
                continue
            if (ev_k, dep_k) in gorulen_maclar:
                ayni_takim_hatalari.append(f"{ev_k.title()} vs {dep_k.title()} (Mükerrer satır)")
                continue
            gorulen_maclar.add((ev_k, dep_k))
            sonuc = mac_hesapla(ev_k, dep_k)
            cev, cdep = sonuc.get("canli_ev"), sonuc.get("canli_dep")
            ev_form_str = f"{cev['karne']} ({cev['ag']}-{cev['yg']} Gol)" if cev else "-"
            dep_form_str = f"{cdep['karne']} ({cdep['ag']}-{cdep['yg']} Gol)" if cdep else "-"
            
            avrupa_durum = []
            if ev_k in AVRUPA_KUPASI_TAKIMLARI:
                avrupa_durum.append(f"{ev_k.title()}")
            if dep_k in AVRUPA_KUPASI_TAKIMLARI:
                avrupa_durum.append(f"{dep_k.title()}")
            avrupa_str = "⚡ " + ", ".join(avrupa_durum) if avrupa_durum else "Dinlenmiş"

            bilgi = {
                "Kademe": sonuc["kademe"],
                "Maç": f"{ev_k.title()} vs {dep_k.title()}",
                "Ana Öneri": f"{sonuc['aksiyon']} (%{sonuc['guven_orani']:.0f})" if sonuc["durum"] == "YESIL" else "PAS GEÇ",
                "🔥 Oran Katlayıcı": sonuc["katlayici_aksiyon"],
                "🏠 Ev Formu (G-B-M)": ev_form_str,
                "✈️ Dep Formu (G-B-M)": dep_form_str,
                "⚡ Fikstür Radarı": avrupa_str,
                "YZ Puanı": f"{sonuc['yz_kalite_puani']:.1f}",
                "Min. Oran": f"{sonuc['min_oran']:.2f}" if sonuc["durum"] == "YESIL" else "-",
                "Toplam xG": f"{sonuc['toplam_xg']:.2f}",
                "1.5Ü": f"%{sonuc['p_15_ust']:.0f}",
                "2.5Ü": f"%{sonuc['p_25_ust']:.0f}",
                "İY 0.5Ü": f"%{sonuc['p_iy_05_ust']:.0f}",
                "guven_raw": sonuc["guven_orani"],
                "yz_raw": sonuc["yz_kalite_puani"],
                "aksiyon_raw": sonuc["aksiyon"],
                "katlayici_raw": sonuc["katlayici_aksiyon"],
                "katlayici_yuzde_raw": sonuc["katlayici_yuzde"],
                "min_oran_raw": sonuc["min_oran"],
                "tuzak_notu": sonuc["tuzak_notu"]
            }
            if sonuc["durum"] == "YESIL" and sonuc["yz_kalite_puani"] >= yz_baraji:
                yz_secilenler.append(bilgi)
            elif sonuc["durum"] == "YESIL":
                sinirda_kalanlar.append(bilgi)
            else:
                sari_maclar.append(bilgi)

        st.divider()
        if ayni_takim_hatalari:
            st.warning(f"⚠️ Hatalı / Mükerrer yazıldığı için otomatik atlanan satırlar: {', '.join(ayni_takim_hatalari)}")
        if bulunamayanlar:
            st.info(f"ℹ️ Tanınmayan satırlar ({len(bulunamayanlar)}): {', '.join(bulunamayanlar)}")

        # Sıralama: En yüksek Tutma Yüzdesinden (% Güven) aşağıya doğru sıralama
        sirali_secilenler = sorted(yz_secilenler, key=lambda x: (x["guven_raw"], x["yz_raw"]), reverse=True)
        secilen_sayisi = len(sirali_secilenler)

        if secilen_sayisi > 0:
            # 1) ANA KUTU: BARAJI GEÇEN TÜM MAÇLAR (SABİT 3-4 DEĞİL, HEPSİ!)
            tum_satirlar_html = ""
            for i, m in enumerate(sirali_secilenler, 1):
                kat_metin = f" &nbsp;|&nbsp; <span style='color:#f1c40f;'>🔥 Yüksek Oran: <b>{m['katlayici_raw']}</b></span>" if m["katlayici_raw"] != "-" else ""
                tum_satirlar_html += (
                    f"<div style='padding:5px 0; border-bottom:0.5px solid rgba(255,255,255,0.12);'>"
                    f"<b>{i}. {m['Maç']}</b> ➔ <b style='color:#2ecc71;'>{m['aksiyon_raw']}</b> "
                    f"(Güven: %{m['guven_raw']:.1f} | YZ Puanı: {m['YZ Puanı']} | Min Oran: {m['min_oran_raw']:.2f}){kat_metin}"
                    f"</div>"
                )
            toplam_birlesik_olasilik = float(np.prod([m["guven_raw"] / 100.0 for m in sirali_secilenler])) * 100.0

            st.markdown(f"""
            <div class="kombine-box" style="padding:18px; border-radius:12px; margin-bottom:16px;">
                <h4 style="margin:0; color:#2ecc71;">🤖 YZ'nin Bültenden Seçtiği Tüm Banko Maçlar ({secilen_sayisi} Maç Barajı Geçti!)</h4>
                <small style="color:#d4efdf;">Sabit maç sınırı olmadan, <b>{yz_baraji:.1f}</b> YZ kalite barajını geçen ve tuzak içermeyen tüm maçlar:</small>
                <hr style="border:0.5px solid rgba(255,255,255,0.25); margin:10px 0;">
                {tum_satirlar_html}
                <div style="margin-top:10px; font-size:0.95rem;">
                    <b>📊 Seçilen Maç Sayısı:</b> {secilen_sayisi} Maç &nbsp;|&nbsp;
                    <b>🎯 Tek Kuponda Ortak Olasılık:</b> %{toplam_birlesik_olasilik:.1f}
                </div>
            </div>
            """, unsafe_allow_html=True)

            # 2) EĞER ÇOK MAÇ ÇIKTIYSA FERMUAR (SNAKE-DRAFT) DENGELİ KUPON DAĞITIMI
            kupon_sayisi = (secilen_sayisi + paket_boyutu - 1) // paket_boyutu
            if kupon_sayisi > 1:
                paketler = [[] for _ in range(kupon_sayisi)]
                for idx, mac_item in enumerate(sirali_secilenler):
                    tur = idx // kupon_sayisi
                    hedef_k = (idx % kupon_sayisi) if (tur % 2 == 0) else (kupon_sayisi - 1 - (idx % kupon_sayisi))
                    paketler[hedef_k].append(mac_item)
                paketler = [p for p in paketler if p]

                st.markdown(f"#### 📦 YZ Otomatik Bölünmüş Kupon Paketleri ({paket_boyutu}'li Fermuar Dengeli Dağılım)")
                st.caption(
                    f"Bültende {secilen_sayisi} sağlam maç çıktığı için YZ, en yüksek güvenilirlikli Elmas maçları tüm kuponlara "
                    f"eşit dağıtarak ({len(paketler)} ayrı kupon) her kuponun tutma ihtimalini maksimumda tuttu:"
                )
                p_cols = st.columns(min(3, len(paketler)))
                for p_idx, paket in enumerate(paketler):
                    with p_cols[p_idx % len(p_cols)]:
                        p_guven = float(np.prod([x["guven_raw"] / 100.0 for x in paket])) * 100.0
                        p_html = "<br>".join([f"• <b>{x['Maç']}</b> ➔ <b>{x['aksiyon_raw']}</b> (%{x['guven_raw']:.0f})" for x in paket])
                        st.markdown(f"""
                        <div class="kurtarma-box" style="padding:14px; border-radius:10px; margin-bottom:10px;">
                            <h5 style="margin:0; color:#5dade2;">🎫 YZ Kupon #{p_idx + 1} ({len(paket)} Maç)</h5>
                            <hr style="border:0.5px solid rgba(255,255,255,0.2); margin:6px 0;">
                            {p_html}
                            <hr style="border:0.5px solid rgba(255,255,255,0.2); margin:6px 0;">
                            <small><b>Kupon Tutma İhtimali:</b> %{p_guven:.1f}</small>
                        </div>
                        """, unsafe_allow_html=True)

            # 2B) 🔥 ORAN KATLAYICI ÖZEL KUPON (Yüksek Oran Arayanlar İçin En Sağlam 3 Katlayıcı Maç)
            katlayici_adaylar = [
                m for m in sirali_secilenler
                if m["katlayici_raw"] != "-" and "İY 0.5" not in m["katlayici_raw"] and m["katlayici_yuzde_raw"] >= 61.0
            ]
            if len(katlayici_adaylar) >= 2:
                secilen_katlayici = katlayici_adaylar[:3]
                kat_ortak_guven = float(np.prod([x["katlayici_yuzde_raw"] / 100.0 for x in secilen_katlayici])) * 100.0
                kat_html = "<br>".join([f"• <b>{x['Maç']}</b> ➔ <b style='color:#f1c40f;'>{x['katlayici_raw']}</b>" for x in secilen_katlayici])
                st.markdown(f"""
                <div class="kurtarma-box" style="padding:14px; border-radius:10px; margin-bottom:14px; border:1px solid rgba(241,196,15,0.45);">
                    <h5 style="margin:0; color:#f1c40f;">🔥 YZ Oran Katlayıcı Özel Kupon ({len(secilen_katlayici)} Maç - Yüksek Oran Paketi)</h5>
                    <small style="color:#fcf3cf;">Ana kuponların yanında ufak misliyle yüksek oran vurmak isteyenler için bültenin en güçlü katlayıcı tercihleri:</small>
                    <hr style="border:0.5px solid rgba(255,255,255,0.2); margin:6px 0;">
                    {kat_html}
                    <hr style="border:0.5px solid rgba(255,255,255,0.2); margin:6px 0;">
                    <small><b>Katlayıcı Kupon Tutma İhtimali:</b> %{kat_ortak_guven:.1f}</small>
                </div>
                """, unsafe_allow_html=True)

            # 3) TABLO GÖRÜNÜMÜ
            st.markdown(f"#### 🟢 YZ Tarafından Seçilen Maçların Detay Tablosu ({secilen_sayisi} Maç)")
            goster_df = pd.DataFrame(sirali_secilenler).drop(columns=["guven_raw", "yz_raw", "aksiyon_raw", "katlayici_raw", "katlayici_yuzde_raw", "min_oran_raw", "tuzak_notu"])
            st.markdown(goster_df.to_html(classes='custom-table', index=False, escape=False), unsafe_allow_html=True)
            
            st.markdown("<br>", unsafe_allow_html=True)
            col_b_aktar1, col_b_aktar2 = st.columns(2)
            with col_b_aktar1:
                if st.button("💾 1) Ana Yeşil Tahminleri İstatistik Defterine Ekle", use_container_width=True, key="bulten_aktar_btn"):
                    bugun_str = datetime.now().strftime("%d/%m/%Y")
                    eklenen = 0
                    mevcut_maclar = {f"{r.get('Maç')}_{r.get('Tarih')}_{r.get('Tahmin')}" for r in st.session_state.istatistik_verileri}
                    for m in sirali_secilenler:
                        anahtar = f"{m['Maç']}_{bugun_str}_{m['aksiyon_raw']}"
                        if anahtar not in mevcut_maclar:
                            st.session_state.istatistik_verileri.append({
                                "Tarih": bugun_str,
                                "Maç": m["Maç"],
                                "Tahmin": m["aksiyon_raw"],
                                "Sonuç": "Bekliyor ⏳"
                            })
                            mevcut_maclar.add(anahtar)
                            eklenen += 1
                    try:
                        pd.DataFrame(st.session_state.istatistik_verileri).to_csv(DOSYA_ISTATISTIK, index=False, encoding="utf-8")
                    except Exception:
                        pass
                    st.success(f"✅ {eklenen} maç (Ana Tercihler) İstatistik Defteri'ne eklendi!")
                    st.rerun()

            with col_b_aktar2:
                if st.button("🔥 2) Oran Katlayıcı / Kombine Tercihleri İstatistik Defterine Ekle", use_container_width=True, key="bulten_aktar_katlayici_btn"):
                    bugun_str = datetime.now().strftime("%d/%m/%Y")
                    eklenen = 0
                    mevcut_maclar = {f"{r.get('Maç')}_{r.get('Tarih')}_{r.get('Tahmin')}" for r in st.session_state.istatistik_verileri}
                    for m in sirali_secilenler:
                        kat_aks = m.get("katlayici_raw", "-")
                        if kat_aks and kat_aks != "-":
                            clean_tahmin = re.sub(r'\s*\(\s*%\s*\d+\s*\)', '', kat_aks).strip()
                            anahtar = f"{m['Maç']}_{bugun_str}_{clean_tahmin}"
                            if anahtar not in mevcut_maclar:
                                st.session_state.istatistik_verileri.append({
                                    "Tarih": bugun_str,
                                    "Maç": m["Maç"],
                                    "Tahmin": clean_tahmin,
                                    "Sonuç": "Bekliyor ⏳"
                                })
                                mevcut_maclar.add(anahtar)
                                eklenen += 1
                    try:
                        pd.DataFrame(st.session_state.istatistik_verileri).to_csv(DOSYA_ISTATISTIK, index=False, encoding="utf-8")
                    except Exception:
                        pass
                    st.success(f"🔥 {eklenen} maç (Kombine / Katlayıcı Tercihler) İstatistik Defteri'ne eklendi!")
                    st.rerun()
        else:
            st.warning(f"⚠️ Bültende **{yz_baraji:.1f}** YZ kalite barajını geçen maç bulunamadı. Yukarıdaki kaydırıcıdan barajı biraz düşürebilirsin.")

        if sinirda_kalanlar:
            sinir_sirali = sorted(sinirda_kalanlar, key=lambda x: (x["guven_raw"], x["yz_raw"]), reverse=True)
            with st.expander(f"🟡 Yeşil Olup YZ Barajının ({yz_baraji:.1f}) Altında Kalan Sınırda Maçlar ({len(sinirda_kalanlar)}) - Ana Kupona Alınmadı"):
                sinir_df = pd.DataFrame(sinir_sirali).drop(columns=["guven_raw", "yz_raw", "aksiyon_raw", "katlayici_raw", "katlayici_yuzde_raw", "min_oran_raw", "tuzak_notu"])
                st.markdown(sinir_df.to_html(classes='custom-table', index=False, escape=False), unsafe_allow_html=True)

        if sari_maclar:
            with st.expander(f"🔴 Tuzak Kalkanına Takılan / Pas Geçilen Maçlar ({len(sari_maclar)}) - Kesinlikle Oynama!"):
                sari_df = pd.DataFrame(sari_maclar)[["Maç", "🏠 Ev Formu (G-B-M)", "✈️ Dep Formu (G-B-M)", "Toplam xG", "1.5Ü", "2.5Ü", "tuzak_notu"]].rename(columns={"tuzak_notu": "Elenme Sebebi (Tuzak Röntgeni)"})
                st.markdown(sari_df.to_html(classes='custom-table', index=False, escape=False), unsafe_allow_html=True)

# ==============================================================================
# TAB 3: GÜNLÜK KASA & -1200 TL KURTARMA KOÇU (TILT / ALL-IN KORUMALI)
# ==============================================================================
with tab3:
    st.markdown("### 📊 Günlük Kasa Takibi & Zarar Kurtarma Koçu")
    bugun_tarih = datetime.now().strftime("%d/%m/%Y")

    # Mevcut Kasa Analizi ve All-In / Tilt Koruması
    if st.session_state.kasa_verileri:
        kasa_df_analiz = pd.DataFrame(st.session_state.kasa_verileri)
        mevcut_net = float(kasa_df_analiz["Net Durum (TL)"].sum())
        bugunku_islemler = kasa_df_analiz[kasa_df_analiz["Tarih"].astype(str) == bugun_tarih]
        bugun_kazanan_var = any("Kazandı" in str(d) for d in bugunku_islemler["Durum"]) if len(bugunku_islemler) > 0 else False
        bugun_net = float(bugunku_islemler["Net Durum (TL)"].sum()) if len(bugunku_islemler) > 0 else 0.0

        if mevcut_net < 0:
            kalan_zarar = abs(mevcut_net)
            hedef_kupon_basi_net_kar = 80.0  # 100 TL sabit bahis, ~1.80 oran ile kupon başı ortalama +80 TL net kâr
            gereken_net_isabet = int(np.ceil(kalan_zarar / hedef_kupon_basi_net_kar))
            st.markdown(f"""
            <div class="kurtarma-box" style="padding:15px; border-radius:10px; margin-bottom:15px;">
                <h4 style="margin:0; color:#f39c12;">🛡️ Kasa Kurtarma & Disiplin Paneli (Hedef: 0 TL Başabaş)</h4>
                <hr style="border:0.5px solid rgba(255,255,255,0.2); margin:8px 0;">
                📌 <b>Mevcut Net Durum:</b> {mevcut_net:.2f} TL &nbsp;|&nbsp; <b>Kapatılacak Fark:</b> {kalan_zarar:.2f} TL<br>
                🎯 <b>Kurtuluş Formülü:</b> Sabit <b>100 TL</b> kasa ve ortalama <b>1.80</b> oranlı 2'li/3'lü kuponlarla <b>{gereken_net_isabet} net kazanan kupon</b> adımında zararın tamamen sıfırlanır!<br>
                🚫 <b>ALTIN KURAL (All-In Yasağı):</b> Kazandığın kupondan dönen 180-320 TL'nin tamamını ASLA bir sonraki kupona basma! Her zaman <b>sadece 100 TL</b> bas, üstünü kasaya kilitle.
            </div>
            """, unsafe_allow_html=True)

        if bugun_kazanan_var or bugun_net > 0:
            st.warning(
                f"🚨 **TILT / ALL-IN KORUMA KALKANI AKTİF!** Bugün kasanda kazanan işlem var (Bugünkü Net: **{bugun_net:+.2f} TL**). "
                f"Geçmişte kazandığın gün tüm parayı (342 TL / 322 TL / 184 TL) 3. kupona basıp kârı sildin. "
                f"Bugün yeni kupon yapacaksan **maksimum 100 TL** (veya sadece kârın %40'ını) yatır!"
            )

    with st.form("kasa_form", clear_on_submit=True):
        col_f1, col_f2, col_f3 = st.columns(3)
        tarih_input = col_f1.text_input("📅 Tarih", value=bugun_tarih)
        aciklama_input = col_f2.text_input("📝 İşlem Açıklaması", value="Günün Kombinesi")
        durum_tipi = col_f3.selectbox("Durum", ["Kazandı ✅", "Yattı ❌", "Nakit Yatırma/Çekme 💵"])

        col_f4, col_f5 = st.columns(2)
        yatirilan = col_f4.number_input("Yatırılan Tutar (TL) [Önerilen Sabit: 100 TL]", min_value=0.0, value=100.0, step=10.0)
        alinan = col_f5.number_input("Alınan / Geri Gelen Tutar (TL)", min_value=0.0, value=0.0, step=5.0)

        if st.form_submit_button("💾 İşlemi Kasaya Ekle", use_container_width=True):
            net = alinan - yatirilan
            st.session_state.kasa_verileri.append({
                "Tarih": str(tarih_input), "Açıklama": f"{aciklama_input} ({durum_tipi})",
                "Durum": durum_tipi, "Yatırılan (TL)": yatirilan, "Alınan (TL)": alinan, "Net Durum (TL)": net
            })
            try:
                pd.DataFrame(st.session_state.kasa_verileri).to_csv(DOSYA_KASA, index=False, encoding="utf-8")
            except:
                pass
            st.success("İşlem kasaya eklendi!")
            st.rerun()

    st.divider()
    if st.session_state.kasa_verileri:
        kasa_df = pd.DataFrame(st.session_state.kasa_verileri)
        m1, m2, m3, m4 = st.columns(4)
        m1.metric("Toplam Yatırılan", f"{kasa_df['Yatırılan (TL)'].sum():.2f} TL")
        m2.metric("Toplam Alınan", f"{kasa_df['Alınan (TL)'].sum():.2f} TL")
        net_kar = kasa_df['Net Durum (TL)'].sum()
        m3.metric("Net Kâr / Zarar", f"{net_kar:.2f} TL", delta=f"{net_kar:.2f} TL")
        kazanan_kupon_sayisi = len(kasa_df[kasa_df["Durum"].astype(str).str.contains("Kazandı")])
        toplam_kupon_sayisi = len(kasa_df)
        m4.metric("Kupon İsabeti", f"{kazanan_kupon_sayisi} / {toplam_kupon_sayisi}", f"%{(kazanan_kupon_sayisi/toplam_kupon_sayisi*100) if toplam_kupon_sayisi else 0:.1f}")

        st.subheader("📋 Kasa Geçmişi ve İşlem Silme")

        kasa_arama = st.text_input("🔍 Kasa Geçmişinde Ara", value="", key="kasa_arama_input")
        ters_kasa_df = kasa_df.iloc[::-1]
        if kasa_arama.strip():
            ters_kasa_df = ters_kasa_df[ters_kasa_df.astype(str).apply(lambda x: x.str.contains(kasa_arama, case=False)).any(axis=1)]

        KASA_SAYFA_BOYUTU = 50
        toplam_kasa_kayit = len(ters_kasa_df)
        toplam_kasa_sayfa = max(1, (toplam_kasa_kayit + KASA_SAYFA_BOYUTU - 1) // KASA_SAYFA_BOYUTU)

        if "kasa_sayfa" not in st.session_state:
            st.session_state.kasa_sayfa = 1
        if st.session_state.kasa_sayfa > toplam_kasa_sayfa:
            st.session_state.kasa_sayfa = toplam_kasa_sayfa

        kp1, kp2, kp3 = st.columns([1.5, 2, 1.5])
        with kp1:
            if st.button("⬅️ Önceki Sayfa", disabled=(st.session_state.kasa_sayfa <= 1), use_container_width=True, key="kasa_onceki_btn"):
                st.session_state.kasa_sayfa -= 1
                st.rerun()
        with kp2:
            st.markdown(f"<div style='text-align:center; padding-top:8px; font-weight:bold;'>📄 Sayfa {st.session_state.kasa_sayfa} / {toplam_kasa_sayfa} (Toplam {toplam_kasa_kayit} İşlem)</div>", unsafe_allow_html=True)
        with kp3:
            if st.button("Sonraki Sayfa ➡️", disabled=(st.session_state.kasa_sayfa >= toplam_kasa_sayfa), use_container_width=True, key="kasa_sonraki_btn"):
                st.session_state.kasa_sayfa += 1
                st.rerun()

        st.divider()

        k_baslangic = (st.session_state.kasa_sayfa - 1) * KASA_SAYFA_BOYUTU
        k_bitis = k_baslangic + KASA_SAYFA_BOYUTU
        kasa_sayfa_df = ters_kasa_df.iloc[k_baslangic:k_bitis]

        for idx, row in kasa_sayfa_df.iterrows():
            cs1, cs2, cs3, cs4, cs5, cs6 = st.columns([1.5, 2.5, 1, 1, 1, 0.8])
            cs1.write(f"📅 {row['Tarih']}")
            cs2.write(f"📝 {row['Açıklama']}")
            cs3.write(f"Yat: {row['Yatırılan (TL)']:.2f}")
            cs4.write(f"Al: {row['Alınan (TL)']:.2f}")
            cs5.write(f"Net: {row['Net Durum (TL)']:.2f}")
            if cs6.button("🗑️", key=f"sil_kasa_{idx}"):
                st.session_state.kasa_verileri.pop(idx)
                try:
                    pd.DataFrame(st.session_state.kasa_verileri).to_csv(DOSYA_KASA, index=False, encoding="utf-8")
                except:
                    pass
                st.rerun()

        st.divider()
        if st.button("🗑️ Tüm Kasayı Sıfırla", use_container_width=True):
            st.session_state.kasa_verileri = []
            st.session_state.kasa_sayfa = 1
            if os.path.exists(DOSYA_KASA):
                try:
                    os.remove(DOSYA_KASA)
                except:
                    pass
            st.rerun()
    else:
        st.info("Henüz kasaya kaydedilmiş bir işlem yok.")

# ==============================================================================
# TAB 4: İSTATİSTİKLER KARNESİ
# ==============================================================================
with tab4:
    st.markdown("### 📊 Model Başarı İstatistikleri Karnesi ve Derinlemesine Analiz")
    
    # ⚡ Canlı Biten Maçları Çekme & Otomatik Sonuçlandırıcı
    st.markdown("#### ⚡ Canlı Skor Senkronizasyonu & Otomatik Sonuçlandırıcı")
    cs_col1, cs_col2 = st.columns([3, 2])
    with cs_col1:
        st.caption("ESPN canlı skor merkezinden son 4 günde oynanan tüm maçların resmi bitiş skorlarını tarar; 'Bekliyor ⏳' durumundaki tahminlerini otomatik olarak **Kazandı ✅** veya **Kaybetti ❌** olarak sonuçlandırır.")
    with cs_col2:
        if st.button("🔄 Biten Maçları Canlı Çek & Otomatik Sonuçlandır", use_container_width=True, type="primary", key="canli_sonuc_cek_btn"):
            with st.spinner("📡 Canlı skorlar taranıyor ve maçlar sonuçlandırılıyor..."):
                skorlar = canli_biten_skorlari_getir()
                guncellenen = 0
                kazanan_yeni = 0
                kaybeden_yeni = 0
                for row in st.session_state.istatistik_verileri:
                    durum_str = str(row.get("Sonuç", ""))
                    if "Bekliyor" in durum_str or "⏳" in durum_str:
                        mac_str = row.get("Maç", "")
                        tahmin_str = row.get("Tahmin", "")
                        parcalar = mac_str.split(" vs ") if " vs " in mac_str else mac_str.split(" - ")
                        if len(parcalar) == 2:
                            ev_t = takim_bul(parcalar[0].strip())
                            dep_t = takim_bul(parcalar[1].strip())
                            if (ev_t, dep_t) in skorlar:
                                hs, as_ = skorlar[(ev_t, dep_t)]
                                if tahmin_sonucunu_belirle(tahmin_str, hs, as_):
                                    row["Sonuç"] = f"Kazandı ✅ ({hs}-{as_})"
                                    kazanan_yeni += 1
                                else:
                                    row["Sonuç"] = f"Kaybetti ❌ ({hs}-{as_})"
                                    kaybeden_yeni += 1
                                guncellenen += 1
                if guncellenen > 0:
                    try:
                        pd.DataFrame(st.session_state.istatistik_verileri).to_csv(DOSYA_ISTATISTIK, index=False, encoding="utf-8")
                    except Exception:
                        pass
                    st.success(f"🎉 Harika! {guncellenen} bekleyen maç canlı skorlarla sonuçlandırıldı: **{kazanan_yeni} Kazandı ✅**, **{kaybeden_yeni} Kaybetti ❌**!")
                    st.rerun()
                else:
                    st.info(f"ℹ️ Henüz sonucu kesinleşen veya skor havuzunda eşleşen bekleyen maç bulunamadı ({len(skorlar)} biten maç tarandı).")

    st.divider()
    takim_listesi = sorted(list(TAKIM_PROFILLERI.keys()))

    with st.form("istatistik_form", clear_on_submit=True):
        ci1, ci2 = st.columns(2)
        ist_tarih = ci1.text_input("📅 Tarih", value=bugun_tarih, key="ist_t_in")
        tahmin_turu = ci2.selectbox("🎯 Tahmin Türü", [
            "1.5 ÜST", "2.5 ÜST", "2.5 ALT",
            "KG VAR", "KG YOK",
            "MS 1", "MS 2", "1X Çifte Şans", "X2 Çifte Şans",
            "MS 1 & 1.5 ÜST", "MS 2 & 1.5 ÜST",
            "MS 1 & 2.5 ÜST", "MS 2 & 2.5 ÜST",
            "1 & KG VAR", "2 & KG VAR",
            "1X & 1.5 ÜST", "X2 & 1.5 ÜST",
            "Ev 1.5 ÜST", "Dep 1.5 ÜST",
            "İlk Yarı 0.5 ÜST", "MS 0"
        ])

        ci3, ci4, ci5 = st.columns(3)
        ist_ev = ci3.selectbox("Ev Sahibi", takim_listesi, index=takim_listesi.index("galatasaray") if "galatasaray" in takim_listesi else 0, key="ist_ev_in")
        ist_dep = ci4.selectbox("Deplasman", takim_listesi, index=takim_listesi.index("fenerbahce") if "fenerbahce" in takim_listesi else 1, key="ist_dep_in")
        ist_sonuc = ci5.selectbox("Sonuç", ["Bekliyor ⏳", "Kazandı ✅", "Kaybetti ❌"], key="ist_s_in")

        if st.form_submit_button("💾 Tahmini İstatistiklere Ekle", use_container_width=True):
            mac_adi = f"{ist_ev.title()} vs {ist_dep.title()}"
            st.session_state.istatistik_verileri.append({
                "Tarih": str(ist_tarih), "Maç": mac_adi, "Tahmin": tahmin_turu, "Sonuç": ist_sonuc
            })
            try:
                pd.DataFrame(st.session_state.istatistik_verileri).to_csv(DOSYA_ISTATISTIK, index=False, encoding="utf-8")
            except:
                pass
            st.success("İstatistik eklendi!")
            st.rerun()

    st.divider()
    if st.session_state.istatistik_verileri:
        istatistik_df = pd.DataFrame(st.session_state.istatistik_verileri)
        toplam = len(istatistik_df)
        kazanan = len(istatistik_df[istatistik_df["Sonuç"].astype(str).str.contains("Kazandı", na=False)])
        kaybeden = len(istatistik_df[istatistik_df["Sonuç"].astype(str).str.contains("Kaybetti", na=False)])
        bekleyen = len(istatistik_df[istatistik_df["Sonuç"].astype(str).str.contains("Bekliyor|⏳", na=False)])
        sonuclanmis = kazanan + kaybeden
        win_rate = (kazanan / sonuclanmis * 100) if sonuclanmis > 0 else 0

        ci1, ci2, ci3, ci4 = st.columns(4)
        ci1.metric("Toplam Tahmin", toplam)
        ci2.metric("Kazanan ✅", kazanan)
        ci3.metric("Bekleyen ⏳", bekleyen)
        ci4.metric("Win Rate (%)", f"%{win_rate:.1f}")

        st.subheader("🎯 Tahmin Türü Bazlı Başarı Dağılımı ve Kârlılık Notu")
        if "Tahmin" in istatistik_df.columns:
            tahmin_gruplari = []
            for t_turu in istatistik_df["Tahmin"].unique():
                alt_df = istatistik_df[istatistik_df["Tahmin"] == t_turu]
                t_toplam = len(alt_df)
                t_kazanan = len(alt_df[alt_df["Sonuç"].astype(str).str.contains("Kazandı", na=False)])
                t_kaybeden = len(alt_df[alt_df["Sonuç"].astype(str).str.contains("Kaybetti", na=False)])
                t_sonuclanmis = t_kazanan + t_kaybeden
                t_oran = (t_kazanan / t_sonuclanmis * 100) if t_sonuclanmis > 0 else 0
                if "Çifte Şans" in str(t_turu) and t_oran < 82.0:
                    durum_notu = "⚠️ Düşük Oran / Yüksek Risk (Filtrelenmeli)"
                elif "&" in str(t_turu):
                    if t_oran >= 60.0:
                        durum_notu = "🔥 Yüksek Değerli Elmas Kombine"
                    elif t_oran >= 45.0:
                        durum_notu = "✅ Dengeli Kombine (Kârlı)"
                    else:
                        durum_notu = "⚠️ Riskli Kombine"
                elif t_oran >= 82.0:
                    durum_notu = "💎 Ana Kasa Lokomotifi"
                else:
                    durum_notu = "✅ Dengeli"
                tahmin_gruplari.append({
                    "Tahmin Türü": t_turu,
                    "Toplam Tahmin": t_toplam,
                    "Tutan": t_kazanan,
                    "Başarı Oranı (%)": f"%{t_oran:.1f}",
                    "Strateji Notu": durum_notu,
                    "oran_raw": t_oran
                })
            df_tahmin_analiz = pd.DataFrame(tahmin_gruplari).sort_values(by="oran_raw", ascending=False).drop(columns=["oran_raw"])
            st.markdown(df_tahmin_analiz.to_html(classes='custom-table', index=False, escape=False), unsafe_allow_html=True)

        st.subheader("📋 Geçmiş Tahmin Kayıtları")

        ist_arama = st.text_input("🔍 Kayıtlarda Ara (Takım, Tarih veya Tahmin Türü)", value="", key="ist_arama_input")
        ters_ist_df = istatistik_df.iloc[::-1]
        if ist_arama.strip():
            ters_ist_df = ters_ist_df[ters_ist_df.astype(str).apply(lambda x: x.str.contains(ist_arama, case=False)).any(axis=1)]

        SAYFA_BOYUTU = 50
        toplam_kayit = len(ters_ist_df)
        toplam_sayfa = max(1, (toplam_kayit + SAYFA_BOYUTU - 1) // SAYFA_BOYUTU)

        if "ist_sayfa" not in st.session_state:
            st.session_state.ist_sayfa = 1
        if st.session_state.ist_sayfa > toplam_sayfa:
            st.session_state.ist_sayfa = toplam_sayfa

        sp1, sp2, sp3 = st.columns([1.5, 2, 1.5])
        with sp1:
            if st.button("⬅️ Önceki Sayfa", disabled=(st.session_state.ist_sayfa <= 1), use_container_width=True, key="ist_onceki_btn"):
                st.session_state.ist_sayfa -= 1
                st.rerun()
        with sp2:
            st.markdown(f"<div style='text-align:center; padding-top:8px; font-weight:bold;'>📄 Sayfa {st.session_state.ist_sayfa} / {toplam_sayfa} (Toplam {toplam_kayit} Kayıt)</div>", unsafe_allow_html=True)
        with sp3:
            if st.button("Sonraki Sayfa ➡️", disabled=(st.session_state.ist_sayfa >= toplam_sayfa), use_container_width=True, key="ist_sonraki_btn"):
                st.session_state.ist_sayfa += 1
                st.rerun()

        st.divider()

        baslangic = (st.session_state.ist_sayfa - 1) * SAYFA_BOYUTU
        bitis = baslangic + SAYFA_BOYUTU
        sayfa_df = ters_ist_df.iloc[baslangic:bitis]

        for idx, row in sayfa_df.iterrows():
            cis1, cis2, cis3, cis4, cis5 = st.columns([1.2, 2.5, 1.5, 1.2, 0.7])
            cis1.write(f"📅 {row['Tarih']}")
            cis2.write(f"⚽ {row['Maç']}")
            cis3.write(f"🎯 <b>{row['Tahmin']}</b>", unsafe_allow_html=True)
            cis4.write(f"<b>{row['Sonuç']}</b>", unsafe_allow_html=True)
            if cis5.button("🗑️", key=f"sil_ist_{idx}"):
                st.session_state.istatistik_verileri.pop(idx)
                try:
                    pd.DataFrame(st.session_state.istatistik_verileri).to_csv(DOSYA_ISTATISTIK, index=False, encoding="utf-8")
                except:
                    pass
                st.rerun()

        st.divider()
        if st.button("🗑️ Tüm İstatistikleri Sıfırla", use_container_width=True):
            st.session_state.istatistik_verileri = []
            st.session_state.ist_sayfa = 1
            if os.path.exists(DOSYA_ISTATISTIK):
                try:
                    os.remove(DOSYA_ISTATISTIK)
                except:
                    pass
            st.rerun()
    else:
        st.info("Henüz istatistik eklenmedi.")

# ==============================================================================
# TAB 5: AKILLI KUPON CHECK-UP (0-3 BİTEN 1X & VALUE DEDEKTÖRÜ)
# ==============================================================================
with tab5:
    st.markdown("### 🕵️‍♂️ Akıllı Kupon Check-Up & Value Hunter (26/27 Tuzak & İddaa Açığı Radarı)")

    if "aktif_kupon" not in st.session_state:
        st.session_state.aktif_kupon = []

    takim_listesi = sorted(list(TAKIM_PROFILLERI.keys()))

    c_ev_col, c_dep_col = st.columns(2)
    k_ev = c_ev_col.selectbox("🏠 Ev Sahibi", takim_listesi, index=takim_listesi.index("galatasaray") if "galatasaray" in takim_listesi else 0, key="k_ev_sec")
    k_dep = c_dep_col.selectbox("✈️ Deplasman", takim_listesi, index=takim_listesi.index("fenerbahce") if "fenerbahce" in takim_listesi else 1, key="k_dep_sec")

    if k_ev and k_dep and k_ev != k_dep:
        analiz_onizleme = mac_hesapla(k_ev, k_dep)
        marketler = [
            {"Market": "1.5 ÜST", "Olasılık": analiz_onizleme["p_15_ust"], "Karakter": "Temel Banko"},
            {"Market": "İY 0.5 ÜST", "Olasılık": analiz_onizleme["p_iy_05_ust"], "Karakter": "İlk Yarı Gol"},
            {"Market": "2.5 ÜST", "Olasılık": analiz_onizleme["p_25_ust"], "Karakter": "Yüksek Skor"},
            {"Market": "KG VAR", "Olasılık": analiz_onizleme["p_kg_var"], "Karakter": "Karşılıklı Skor"},
            {"Market": "MS 1", "Olasılık": analiz_onizleme["p_ev"], "Karakter": "Ev Galibiyeti"},
            {"Market": "MS 2", "Olasılık": analiz_onizleme["p_dep"], "Karakter": "Deplasman Galibiyeti"},
            {"Market": "1X Çifte Şans", "Olasılık": analiz_onizleme["p_1x"], "Karakter": "Ev Kaybetmez"},
            {"Market": "X2 Çifte Şans", "Olasılık": analiz_onizleme["p_x2"], "Karakter": "Deplasman Kaybetmez"},
            {"Market": "MS 1 & 1.5 ÜST", "Olasılık": analiz_onizleme["p_ms1_15_ust"], "Karakter": "Kombine / Katlayıcı"},
            {"Market": "MS 2 & 1.5 ÜST", "Olasılık": analiz_onizleme["p_ms2_15_ust"], "Karakter": "Kombine / Katlayıcı"},
            {"Market": "2.5 ALT", "Olasılık": analiz_onizleme["p_25_alt"], "Karakter": "Kısır Maç"},
            {"Market": "KG YOK", "Olasılık": analiz_onizleme["p_kg_yok"], "Karakter": "Tek Taraflı / Savunma"}
        ]

        tablo_verisi = []
        for m in marketler:
            ol = m["Olasılık"]
            ad_oran = round(100.0 / max(ol, 5.0), 2)
            val_esik = round(ad_oran * 1.05, 2)
            if ol >= 75.0:
                durum = "💎 Güçlü Banko (%75+)"
            elif ol >= 60.0:
                durum = "🟢 Dengeli Tercih"
            elif ol >= 45.0:
                durum = "⚡ Sürpriz / Yüksek Oran"
            else:
                durum = "⚠️ Düşük İhtimal"
            tablo_verisi.append({
                "🎯 Market": m["Market"],
                "🤖 YZ İhtimali": f"%{ol:.1f}",
                "⚖️ YZ Adil Oran": f"{ad_oran:.2f}",
                "🔥 Value Eşiği (Min İddaa Oranı)": f"{val_esik:.2f}+",
                "💡 Güven & Durum": durum
            })

        with st.expander(f"🔍 {k_ev.title()} vs {k_dep.title()} — Tüm Marketlerin Değer Röntgeni (Value Hunter)", expanded=False):
            st.caption("💡 **Nasıl Kullanılır?** İddaa bürosunun açtığı oran, tablodaki 'Value Eşiği'nden yüksekse o markette **matematiksel kâr marjı (İddaa Açığı)** vardır!")
            st.markdown(pd.DataFrame(tablo_verisi).to_html(classes='custom-table', index=False, escape=False), unsafe_allow_html=True)

    with st.form("kupon_mac_ekle_form", clear_on_submit=False):
        ck3, ck4 = st.columns([2, 1.5])
        k_tahmin = ck3.selectbox(
            "🎯 Tahmin",
            [
                "1.5 ÜST", "İY 0.5 ÜST", "2.5 ÜST", "KG VAR",
                "MS 1", "MS 2", "Ev 1.5 ÜST", "Dep 1.5 ÜST",
                "MS 1 & 1.5 ÜST", "MS 2 & 1.5 ÜST",
                "2.5 ALT", "KG YOK", "1X Çifte Şans", "X2 Çifte Şans", "MS 0"
            ],
            key="k_tah_sec"
        )
        k_oran = ck4.number_input("📈 İddaa Oranı", min_value=1.01, max_value=50.0, value=1.30, step=0.05, key="k_oran_sec")

        ekle_btn = st.form_submit_button("➕ Maçı Analiz Et ve Kupona Ekle", use_container_width=True)

        if ekle_btn:
            if k_ev == k_dep:
                st.error("⚠️ Aynı takımı hem Ev Sahibi hem Deplasman olarak seçtin kanka!")
                st.stop()
            analiz = mac_hesapla(k_ev, k_dep)
            ep = TAKIM_PROFILLERI[k_ev]
            dp = TAKIM_PROFILLERI[k_dep]

            oran_haritasi = {
                "MS 1": analiz["p_ev"], "MS 2": analiz["p_dep"], "MS 0": analiz["p_ber"],
                "1.5 ÜST": analiz["p_15_ust"], "İY 0.5 ÜST": analiz["p_iy_05_ust"],
                "2.5 ÜST": analiz["p_25_ust"], "2.5 ALT": analiz["p_25_alt"],
                "KG VAR": analiz["p_kg_var"], "KG YOK": analiz["p_kg_yok"],
                "Ev 1.5 ÜST": analiz["p_ev_15_ust"], "Dep 1.5 ÜST": analiz["p_dep_15_ust"],
                "MS 1 & 1.5 ÜST": analiz["p_ms1_15_ust"], "MS 2 & 1.5 ÜST": analiz["p_ms2_15_ust"],
                "1X Çifte Şans": analiz["p_1x"], "X2 Çifte Şans": analiz["p_x2"]
            }
            model_yuzdesi = oran_haritasi.get(k_tahmin, 50.0)
            beklenen_deger_ev = round((model_yuzdesi / 100.0) * k_oran, 3)
            adil_oran = round(100.0 / max(model_yuzdesi, 5.0), 2)
            value_edge = round(((k_oran - adil_oran) / adil_oran) * 100.0, 1)

            if value_edge >= 12.0:
                value_rozeti = f"🔥 +%{value_edge:.1f} VALUE"
            elif value_edge >= 3.0:
                value_rozeti = f"✅ +%{value_edge:.1f} DEĞERLİ"
            elif value_edge >= -5.0:
                value_rozeti = f"⚖️ %{value_edge:+.1f} DENGELİ"
            else:
                value_rozeti = f"⚠️ %{value_edge:+.1f} EZİLMİŞ"

            min_hak_edilen_oran = round(max(1.10, (100.0 / max(model_yuzdesi, 40.0)) * 0.84), 2)

            seviye_farki = ep["seviye"] - dp["seviye"]
            mutlak_fark = abs(seviye_farki)
            toplam_xg = analiz["toplam_xg"]
            ortalama_savunma = (ep["savunma"] + dp["savunma"]) / 2.0
            risk_puani = 15
            uyari_notu = "✅ Sağlam Seçim (Kuponda Kalabilir)"

            # Gelişmiş 2026-27 Sniper Tuzak, Ölü Oran & Oran Anomalisi Kuralları
            oran_anomalisi = k_oran >= (adil_oran * 1.28) and model_yuzdesi >= 68.0
            olu_oran_tuzagi = k_oran < (min_hak_edilen_oran - 0.05)

            if oran_anomalisi:
                risk_puani = 82
                uyari_notu = f"🚨 ORAN ANOMALİSİ (KADRO/MOTİVASYON ŞÜPHESİ): Model %{model_yuzdesi:.0f} (Adil Oran: {adil_oran:.2f}) diyor ama İddaa {k_oran:.2f} açmış! Eksik/yedek kadro tuzağı olabilir!"
            elif k_tahmin == "1X Çifte Şans":
                if ep["seviye"] < 1.00 and mutlak_fark <= 0.14:
                    risk_puani = 90
                    uyari_notu = f"🚨 0-3 BİTEN 1X TUZAĞI: Alt sıra istikrarsız takım ({ep['seviye']} vs {dp['seviye']}); ilk golü yerse dağılır!"
                elif analiz["exp_h"] < 1.40 and ep["savunma"] > 1.12:
                    risk_puani = 80
                    uyari_notu = f"🚨 KISIR EV SAHİBİ RİSKİ: Ev sahibinin gol beklentisi düşük ({analiz['exp_h']:.2f} xG). Geriye düşerse çeviremez!"
                elif model_yuzdesi < 73.5:
                    risk_puani = 75
                    uyari_notu = f"🚨 BARAJ ALTI: 1X güveni (%{model_yuzdesi:.1f}) %73.5 barajının altında!"
                else:
                    risk_puani = 15
                    uyari_notu = f"💎 SAĞLAM 1X: Ev sahibi güçlü ve üretken ({analiz['exp_h']:.2f} xG)."

            elif k_tahmin == "X2 Çifte Şans":
                if dp["seviye"] < 1.12 or seviye_farki > -0.12:
                    risk_puani = 85
                    uyari_notu = f"🚨 DEPLASMAN X2 TUZAĞI: Deplasman takımı ({dp['seviye']}) bu deplasmanda X2 için riskli!"
                elif analiz["exp_a"] < 1.38 or model_yuzdesi < 73.5:
                    risk_puani = 78
                    uyari_notu = f"🚨 KISIR DEPLASMAN TUZAĞI: Deplasman xG ({analiz['exp_a']:.2f}) veya güven (%{model_yuzdesi:.1f}) yetersiz!"
                else:
                    risk_puani = 15
                    uyari_notu = f"💎 BANKO X2: Güçlü deplasman favorisi ({analiz['exp_a']:.2f} xG)."

            elif k_tahmin == "MS 1":
                if model_yuzdesi < 54.0:
                    risk_puani = 78
                    uyari_notu = f"⚠️ BARAJ ALTI: MS 1 (%{model_yuzdesi:.1f}) %54 minimal barajının altında."
                elif model_yuzdesi < 61.0:
                    risk_puani = 28
                    uyari_notu = f"🟢 EV SAHİBİ FAVORİSİ: Model %{model_yuzdesi:.1f} ile ev sahibini net favori görüyor."
                else:
                    risk_puani = 15
                    uyari_notu = f"💎 SAĞLAM MS 1: Model %{model_yuzdesi:.1f} ve {analiz['exp_h']:.2f} xG ile onaylıyor."

            elif k_tahmin == "MS 2":
                if model_yuzdesi < 54.0:
                    risk_puani = 78
                    uyari_notu = f"⚠️ BARAJ ALTI: Deplasman galibiyeti (%{model_yuzdesi:.1f}) %54 minimal barajının altında."
                elif model_yuzdesi < 59.5:
                    risk_puani = 28
                    uyari_notu = f"🟢 DEPLASMAN FAVORİSİ: Model %{model_yuzdesi:.1f} ile deplasmanı net favori görüyor (Ev: %{analiz['p_ev']:.0f})."
                else:
                    risk_puani = 18
                    uyari_notu = f"✅ SAĞLAM MS 2: Model %{model_yuzdesi:.1f} ile onaylıyor."

            elif k_tahmin == "1.5 ÜST":
                if model_yuzdesi < 74.0 or toplam_xg < 2.55:
                    risk_puani = 80
                    uyari_notu = f"🚨 BARAJ ALTI: 1.5 Üst güveni (%{model_yuzdesi:.1f} | {toplam_xg:.2f} xG) %74 barajının altında!"
                elif olu_oran_tuzagi:
                    risk_puani = 35
                    uyari_notu = f"⚠️ EZİLMİŞ ORAN ({k_oran:.2f} < Min {min_hak_edilen_oran:.2f}): Maç sağlam ama İddaa oranı çok düşük! Alternatif: **{analiz['katlayici_aksiyon']}**"
                else:
                    risk_puani = 15
                    uyari_notu = f"💎 İDEAL 1.5 ÜST: Hem oranı açık hem gol beklentisi ({toplam_xg:.2f} xG) uygun."

            elif k_tahmin == "İY 0.5 ÜST":
                if model_yuzdesi < 68.0 or toplam_xg < 2.60:
                    risk_puani = 76
                    uyari_notu = f"🚨 BARAJ ALTI: İlk Yarı 0.5 Üst (%{model_yuzdesi:.1f} | {toplam_xg:.2f} xG) ilk yarı kilitlenmesine açık!"
                elif olu_oran_tuzagi:
                    risk_puani = 35
                    uyari_notu = f"⚠️ EZİLMİŞ ORAN ({k_oran:.2f} < Min {min_hak_edilen_oran:.2f}): İY 0.5 Üst oranı düşük kalmış, **1.5 ÜST (%{analiz['p_15_ust']:.0f})** veya **2.5 ÜST** kıyasla."
                else:
                    risk_puani = 18
                    uyari_notu = f"💎 SAĞLAM İY 0.5 ÜST: İlk yarı gol beklentisi yüksek (%{model_yuzdesi:.1f} | {toplam_xg:.2f} xG)."

            elif k_tahmin == "2.5 ÜST":
                if model_yuzdesi < 57.0 or toplam_xg < 2.75:
                    risk_puani = 80
                    uyari_notu = f"🚨 BARAJ ALTI: 2.5 Üst (%{model_yuzdesi:.1f} | {toplam_xg:.2f} xG) %57 barajının altında."
                elif olu_oran_tuzagi:
                    risk_puani = 42
                    uyari_notu = f"⚠️ EZİLMİŞ ORAN ({k_oran:.2f} < Min {min_hak_edilen_oran:.2f}): 2.5 Üst (%{model_yuzdesi:.0f}) için {k_oran:.2f} oran çok düşük! **İY 0.5 ÜST (%{analiz['p_iy_05_ust']:.0f})** veya **KG VAR (%{analiz['p_kg_var']:.0f})** oranına bak!"
                else:
                    risk_puani = 18
                    uyari_notu = f"💎 SAĞLAM 2.5 ÜST: Yüksek tempolu maç ({toplam_xg:.2f} xG)."

            elif k_tahmin in ("Ev 1.5 ÜST", "Dep 1.5 ÜST", "MS 1 & 1.5 ÜST", "MS 2 & 1.5 ÜST"):
                if model_yuzdesi < 56.0:
                    risk_puani = 78
                    uyari_notu = f"🚨 BARAJ ALTI: {k_tahmin} (%{model_yuzdesi:.1f}) %56 güven barajının altında!"
                else:
                    risk_puani = 20
                    uyari_notu = f"🔥 SAĞLAM KATLAYICI ({k_tahmin}): Model %{model_yuzdesi:.1f} ile onaylıyor (Min Oran: {min_hak_edilen_oran:.2f})."

            elif k_tahmin == "2.5 ALT":
                if ep["hucum"] > 1.30 or dp["hucum"] > 1.30 or ep["savunma"] > 1.24 or dp["savunma"] > 1.24:
                    risk_puani = 92
                    uyari_notu = f"🚨 SAHTE 2.5 ALT TUZAĞI (Getafe-Lugano Sendromu): Takımlardan biri açık/golcü karakterde ({ep['hucum']}/{dp['hucum']} hücum), maç Üst'e patlayabilir!"
                elif model_yuzdesi < 61.0 or toplam_xg > 2.20:
                    risk_puani = 80
                    uyari_notu = f"🚨 ÜST RİSKİ: 2.5 Alt güveni (%{model_yuzdesi:.1f}) %61 barajının altında ({toplam_xg:.2f} xG)!"
                else:
                    risk_puani = 18
                    uyari_notu = f"✅ GERÇEK 2.5 ALT: İki takım da kısır ve savunmacı ({toplam_xg:.2f} xG)."

            elif k_tahmin == "KG VAR":
                if model_yuzdesi < 62.0 or analiz["exp_h"] < 1.15 or analiz["exp_a"] < 1.10:
                    risk_puani = 80
                    uyari_notu = f"🚨 BARAJ ALTI: Takımlardan biri gol bulmakta zorlanabilir (%{model_yuzdesi:.1f})."
                else:
                    risk_puani = 20
                    uyari_notu = f"✅ SAĞLAM KG VAR: İki takım da skora yatkın."

            elif k_tahmin == "KG YOK":
                if model_yuzdesi < 62.0:
                    risk_puani = 80
                    uyari_notu = f"🚨 BARAJ ALTI: KG YOK (%{model_yuzdesi:.1f}) riskli!"
                else:
                    risk_puani = 25
                    uyari_notu = f"✅ UYGUN KG YOK: Savunma direnci uyumlu."

            elif k_tahmin == "MS 0":
                if model_yuzdesi < 32.0:
                    risk_puani = 85
                    uyari_notu = f"🚨 YÜKSEK RİSK: Beraberlik (%{model_yuzdesi:.1f}) ihtimali düşük!"
                else:
                    risk_puani = 45
                    uyari_notu = f"⚠️ DENK MAÇ: Beraberlik potansiyeli var (%{model_yuzdesi:.1f}) ama tekli önerilir."

            if value_edge >= 12.0 and risk_puani <= 40:
                uyari_notu += f" • 🔥 İddaa Açığı (+%{value_edge:.1f} Value)"

            st.session_state.aktif_kupon.append({
                "Maç": f"{k_ev.title()} vs {k_dep.title()}",
                "Tahmin": k_tahmin,
                "Oran": k_oran,
                "Adil Oran": adil_oran,
                "Model (%)": model_yuzdesi,
                "Value Edge (%)": value_edge,
                "Value Rozeti": value_rozeti,
                "EV": beklenen_deger_ev,
                "Risk Puanı": risk_puani,
                "Analiz Notu": uyari_notu
            })
            st.rerun()

    if st.session_state.aktif_kupon:
        st.divider()
        col_baslik, col_bedel = st.columns([2, 1])
        col_baslik.markdown("### 📋 Aktif Kupon & Value Röntgeni")
        kupon_bedeli = col_bedel.number_input("💵 Kupon Bedeli (TL) [Sabit Kasa: 100 TL]", min_value=1.0, value=float(st.session_state.get("k_bedel_sec", 100.0)), step=10.0, key="k_bedel_sec")

        kupon_df = pd.DataFrame(st.session_state.aktif_kupon)
        mac_sayisi = len(kupon_df)
        toplam_oran = float(np.prod(kupon_df["Oran"]))
        olasi_kazanc = toplam_oran * kupon_bedeli
        ortak_olasilik = float(np.prod(kupon_df["Model (%)"] / 100.0)) * 100.0
        kupon_ev = (ortak_olasilik / 100.0) * toplam_oran
        kupon_ev_fark = round((kupon_ev - 1.0) * 100.0, 1)

        curuk_elmalar = kupon_df[kupon_df["Risk Puanı"] >= 60]
        en_zayif_halka = kupon_df.loc[kupon_df["Risk Puanı"].idxmax()]
        kupon_saglik_skoru = max(0, 100 - int(kupon_df["Risk Puanı"].max() * 0.45) - (len(curuk_elmalar) * 15) - (max(0, mac_sayisi - 3) * 4))

        km1, km2, km3, km4, km5, km6 = st.columns(6)
        km1.metric("Maç Sayısı", f"{mac_sayisi} Maç")
        km2.metric("Toplam Oran", f"{toplam_oran:.2f}")
        km3.metric("Olası Kazanç", f"{olasi_kazanc:.2f} TL", delta=f"Net: +{olasi_kazanc - kupon_bedeli:.1f} TL")
        km4.metric("Kupon İhtimali", f"%{ortak_olasilik:.1f}")
        km5.metric(
            "Kupon Değeri (EV)",
            f"%{kupon_ev_fark:+.1f}",
            delta="Kasa Lehine 🔥" if kupon_ev_fark > 0 else "Kasa Aleyhine 🚨",
            delta_color="normal" if kupon_ev_fark > 0 else "inverse"
        )
        km6.metric("Sağlık Puanı", f"{kupon_saglik_skoru} / 100")

        if kupon_bedeli > 150:
            st.warning(f"⚠️ **KASA UYARISI:** Kupon bedelin ({kupon_bedeli:.0f} TL) önerilen sabit kasa limitinin (100-150 TL) üzerinde! Tek kupona yüksek basmak yerine sabit üniteyle git.")

        if kupon_ev_fark >= 5.0 and len(curuk_elmalar) == 0:
            st.success(f"🔥 **MATEMATİKSEL VALUE KUPON! (Beklenen Kâr: +%{kupon_ev_fark:.1f} EV)** — Bu kupondaki genel oran/ihtimal dengesi kasanın lehine. Uzun vadede artı yazar!")
        elif kupon_ev_fark <= -20.0:
            st.error(f"🚨 **AĞIR EZİLMİŞ KUPON (-%{abs(kupon_ev_fark):.1f} EV):** İddaa'nın açtığı oranlar maçların tutma ihtimaline göre çok kırpılmış! Bu kupon uzun vadede büroya çalışır.")

        value_maclar = kupon_df[kupon_df.get("Value Edge (%)", pd.Series([0]*len(kupon_df))) >= 10.0]
        if len(value_maclar) > 0:
            v_isimler = ", ".join([f"**{r['Maç']}** ({r['Tahmin']} @ {r['Oran']:.2f} | Adil: {r.get('Adil Oran', 0):.2f})" for _, r in value_maclar.iterrows()])
            st.info(f"💎 **İDDAA AÇIĞI (VALUE BET) TESPİT EDİLDİ:** {v_isimler} seçiminde İddaa bürosu modele göre cömert oran açmış (+%10+ Value Edge)!")

        if len(curuk_elmalar) > 0:
            curuk_isimler = ", ".join([f"**{r['Maç']} ({r['Tahmin']})**" for _, r in curuk_elmalar.iterrows()])
            st.error(
                f"🎯 **YATMA ALARMI! ({len(curuk_elmalar)} Tehlikeli Maç Tespit Edildi)**\n\n"
                f"⚠️ **Tehlikeli Maçlar:** {curuk_isimler}\n\n"
                f"🔍 **En Büyük Risk ({en_zayif_halka['Maç']}):** {en_zayif_halka['Analiz Notu']}\n\n"
                f"💡 **Tavsiye:** Bu maçı kupondan çıkarırsan sağlığın anında yükselecek!"
            )
        elif mac_sayisi <= 3 and (ortak_olasilik / 100.0) * toplam_oran < 0.64:
            hak_edilen_kupon_orani = (100.0 / max(ortak_olasilik, 20.0)) * 0.72
            st.warning(
                f"⚠️ **MAÇLAR ÇOK SAĞLAM AMA İDDAA ORANLARI EZİLMİŞ! (Toplam Oran: {toplam_oran:.2f} | Hak Edilen Min: {hak_edilen_kupon_orani:.2f})**\n\n"
                f"Seçtiğin maçlar kaliteli (**%{ortak_olasilik:.1f}** tutma ihtimali var) ancak İddaa oranları çok düşük açıldığı için "
                f"**{kupon_bedeli:.0f} TL** riske edip sadece **+{olasi_kazanc - kupon_bedeli:.0f} TL** net kâr alıyorsun. "
                f"Oranı çok düşük kalan 1-2 maçı **İY 0.5 ÜST**, **2.5 ÜST** veya **KG VAR** seçeneğine çevirerek toplam oranı **{hak_edilen_kupon_orani:.2f}+** bandına çekmen çok daha kârlı olur!"
            )
        elif mac_sayisi <= 3:
            st.success(
                f"✅ **KARAR: OYNANIR! (TEMİZ VE İDEAL KUPON)**\n\n"
                f"Kuponunda sahte 1X/X2 veya kilitlenme tuzağı bulunamadı. Maç sayısı ({mac_sayisi}) ve oran/risk dengesi ideal."
            )
        else:
            st.warning(
                f"⚡ **KARAR: MAÇLAR TEMİZ AMA KUPON KALABALIK ({mac_sayisi} MAÇ)**\n\n"
                f"Maç başı seçimlerin doğru ancak {mac_sayisi} maç birleşince ortak tutma ihtimali **%{ortak_olasilik:.1f}** seviyesine düşüyor. En iyi 2 veya 3 maça indirmen önerilir."
            )

        st.subheader("📋 Kupondaki Maçlar ve Kalite & Value Röntgeni")
        for idx, row in kupon_df.iterrows():
            cl1, cl2, cl3, cl4, cl5, cl6, cl7 = st.columns([1.8, 1.2, 0.8, 0.8, 1.3, 3.4, 0.5])
            cl1.write(f"⚽ **{row['Maç']}**")
            cl2.write(f"🎯 {row['Tahmin']}")
            cl3.write(f"📈 **{row['Oran']:.2f}**")
            adil_val = row.get("Adil Oran", 0.0)
            cl4.write(f"⚖️ `{adil_val:.2f}`" if adil_val > 0 else "-")
            roz_val = row.get("Value Rozeti", "-")
            cl5.write(f"**{roz_val}**")
            cl6.write(f"🤖 %{row['Model (%)']:.1f} • {row['Analiz Notu']}")
            if cl7.button("🗑️", key=f"k_sil_{idx}"):
                st.session_state.aktif_kupon.pop(idx)
                st.rerun()

        if st.button("🗑️ Kuponu Tamamen Temizle", use_container_width=True):
            st.session_state.aktif_kupon = []
            st.rerun()
    else:
        st.info("Kuponun şu an boş. Yukarıdaki formdan maçları ekleyerek risk analizini başlatabilirsin.")

# ==============================================================================
# TAB 6: CANLI MAÇ & İSTATİSTİK BAZLI MOMENTUM ASİSTANI (CANLI POISSON MOTORU)
# ==============================================================================
with tab6:
    st.markdown("### ⚡ Canlı Maç & İstatistik Bazlı Momentum Asistanı")

    c_canli1, c_canli2 = st.columns(2)
    c_ev_canli = c_canli1.selectbox("🏠 Ev Sahibi (Canlı)", takim_listesi, index=takim_listesi.index("galatasaray") if "galatasaray" in takim_listesi else 0, key="canli_ev_sec_v3")
    c_dep_canli = c_canli2.selectbox("✈️ Deplasman (Canlı)", takim_listesi, index=takim_listesi.index("fenerbahce") if "fenerbahce" in takim_listesi else 1, key="canli_dep_sec_v3")

    cc1, cc2, cc3 = st.columns(3)
    dakika_input = cc1.number_input("⏱️ Maçın Dakikası", min_value=1, max_value=120, value=60, step=1, key="canli_dk_v3")
    ev_skor = cc2.number_input("⚽ Ev Sahibi Skor", min_value=0, max_value=10, value=0, step=1, key="canli_ev_skor_v3")
    dep_skor = cc3.number_input("⚽ Deplasman Skor", min_value=0, max_value=10, value=0, step=1, key="canli_dep_skor_v3")

    st.divider()
    st.markdown("#### 📊 Anlık Maç İstatistikleri (Canlı Paneli)")

    sc1, sc2 = st.columns(2)
    with sc1:
        st.markdown(f"**🏠 {c_ev_canli.title()}**")
        ev_toplam_sut = st.number_input("Toplam Şut (Ev)", min_value=0, value=12, step=1, key="ev_ts_v3")
        ev_isabetli = st.number_input("İsabetli Şut (Ev)", min_value=0, value=5, step=1, key="ev_isab_v3")
        ev_topla_oynama = st.slider("Topla Oynama % (Ev)", min_value=10, max_value=90, value=60, step=1, key="ev_topla_v3")
        ev_korner = st.number_input("Korner (Ev)", min_value=0, value=6, step=1, key="ev_korn_v3")

    with sc2:
        st.markdown(f"**✈️ {c_dep_canli.title()}**")
        dep_toplam_sut = st.number_input("Toplam Şut (Dep)", min_value=0, value=4, step=1, key="dep_ts_v3")
        dep_isabetli = st.number_input("İsabetli Şut (Dep)", min_value=0, value=1, step=1, key="dep_isab_v3")
        dep_korner = st.number_input("Korner (Dep)", min_value=0, value=2, step=1, key="dep_korn_v3")

    if st.button("🔄 İstatistikleri İşle ve Canlı Olasılıkları Güncelle", use_container_width=True):
        temel_analiz = mac_hesapla(c_ev_canli, c_dep_canli)
        kalan_sure_orani = max(0.05, (92 - min(90, dakika_input)) / 90.0)
        gecen_sure_orani = max(0.15, min(90, dakika_input) / 90.0)

        # Dakika başına tempo ve saha baskısı
        ev_aktivite = (ev_isabetli * 2.5) + (ev_toplam_sut * 0.5) + (ev_topla_oynama / 15.0) + (ev_korner * 0.4)
        dep_aktivite = (dep_isabetli * 2.5) + (dep_toplam_sut * 0.5) + ((100 - ev_topla_oynama) / 15.0) + (dep_korner * 0.4)

        toplam_aktivite = max(1.0, ev_aktivite + dep_aktivite)
        ev_guc_orani = ev_aktivite / toplam_aktivite
        dep_guc_orani = dep_aktivite / toplam_aktivite

        # Şut temposu çarpanı (Beklenen normal şut temposuna göre maç ne kadar hızlı?)
        beklenen_normal_aktivite = 28.0 * gecen_sure_orani
        tempo_carpani = min(1.65, max(0.60, toplam_aktivite / max(5.0, beklenen_normal_aktivite)))

        baz_kalan_ev_xg = temel_analiz["exp_h"] * kalan_sure_orani
        baz_kalan_dep_xg = temel_analiz["exp_a"] * kalan_sure_orani

        guncel_ev_xg = baz_kalan_ev_xg * (0.45 + ev_guc_orani * 1.10) * tempo_carpani
        guncel_dep_xg = baz_kalan_dep_xg * (0.45 + dep_guc_orani * 1.10) * tempo_carpani
        kalan_toplam_xg = guncel_ev_xg + guncel_dep_xg

        # Canlı Poisson Olasılıkları (Kalan Süredeki Gol İhtimalleri)
        p_kalan_en_az_1_gol = (1.0 - np.exp(-kalan_toplam_xg)) * 100.0
        p_kalan_en_az_2_gol = (1.0 - np.exp(-kalan_toplam_xg) * (1.0 + kalan_toplam_xg)) * 100.0
        p_ev_gol_atar = (1.0 - np.exp(-guncel_ev_xg)) * 100.0
        p_dep_gol_atar = (1.0 - np.exp(-guncel_dep_xg)) * 100.0

        st.divider()
        st.markdown(f"#### 📈 Canlı Analiz Sonucu (Dakika {dakika_input} | Skor: {ev_skor} - {dep_skor} | Mevcut Toplam Gol: {ev_skor + dep_skor})")

        mc1, mc2, mc3, mc4 = st.columns(4)
        mc1.metric("Kalan Süre xG (Ev)", f"{guncel_ev_xg:.2f} xG", delta=f"Baskı: %{ev_guc_orani*100:.0f}")
        mc2.metric("Kalan Süre xG (Dep)", f"{guncel_dep_xg:.2f} xG", delta=f"Baskı: %{dep_guc_orani*100:.0f}")
        mc3.metric(f"Sıradaki Gol ({ev_skor+dep_skor+0.5:.1f} ÜST)", f"%{p_kalan_en_az_1_gol:.1f}", f"{c_ev_canli[:6].title()}: %{p_ev_gol_atar:.0f}")
        mc4.metric(f"En Az 2 Gol Daha ({ev_skor+dep_skor+1.5:.1f} ÜST)", f"%{p_kalan_en_az_2_gol:.1f}", f"{c_dep_canli[:6].title()}: %{p_dep_gol_atar:.0f}")

        toplam_isabetli = ev_isabetli + dep_isabetli
        toplam_sut = ev_toplam_sut + dep_toplam_sut
        mevcut_toplam_gol = ev_skor + dep_skor

        if p_kalan_en_az_1_gol >= 72.0 and ev_isabetli >= 5 and ev_skor <= dep_skor:
            st.success(
                f"💎 **CANLI BASKI & GOL ALARMI:** {c_ev_canli.title()} rakibi bunaltmış durumda ({ev_isabetli} isabetli şut, %{ev_topla_oynama} topla oynama)! "
                f"Kalan sürede **Ev Sahibi Gol Atar (%{p_ev_gol_atar:.1f})** veya **{mevcut_toplam_gol + 0.5:.1f} ÜST (%{p_kalan_en_az_1_gol:.1f})** çok değerli!"
            )
        elif p_kalan_en_az_1_gol >= 70.0 and dep_isabetli >= 4 and dep_skor <= ev_skor:
            st.success(
                f"💎 **DEPLASMAN BASKISI ALARMI:** {c_dep_canli.title()} tehlikeli geliyor ({dep_isabetli} isabetli şut)! "
                f"**{c_dep_canli.title()} Gol Atar (%{p_dep_gol_atar:.1f})** veya **{mevcut_toplam_gol + 0.5:.1f} ÜST (%{p_kalan_en_az_1_gol:.1f})** değerlendirilebilir."
            )
        elif p_kalan_en_az_1_gol >= 75.0 and toplam_sut >= 16:
            st.success(
                f"🔥 **YÜKSEK TEMPO / GOL YAĞMURU:** Maçta şut trafiği çok yüksek ({toplam_sut} şut, {toplam_isabetli} isabet). "
                f"Canlıdan **{mevcut_toplam_gol + 0.5:.1f} ÜST (%{p_kalan_en_az_1_gol:.1f})** ideal!"
            )
        elif dakika_input >= 70 and p_kalan_en_az_1_gol < 42.0:
            st.warning(
                f"🛡️ **KİLİTLENMİŞ MAÇ ({mevcut_toplam_gol + 0.5:.1f} ALT EĞİLİMİ):** Tempo düşük ve kalan sürede gol çıkma ihtimali sadece **%{p_kalan_en_az_1_gol:.1f}**. Canlıdan Üst bahsine girme!"
            )
        else:
            st.info(f"ℹ️ Kalan sürede en az 1 gol olasılığı **%{p_kalan_en_az_1_gol:.1f}**. Anlık oran değerliyse değerlendirebilirsin.")
