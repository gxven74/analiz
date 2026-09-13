import streamlit as st
import numpy as np
import pandas as pd
from scipy.stats import poisson
import difflib
streamlit
numpy
scipy
pandas

st.set_page_config(page_title="Poisson Tahmin Paneli", page_icon="⚽", layout="wide")

TAKIM_PROFILLERI = {
    # --- TRENDYOL SÜPER LİG (TÜM TAKIMLAR) ---
    "galatasaray": {"hucum": 2.25, "savunma": 1.00, "seviye": 1.40},
    "fenerbahce": {"hucum": 2.20, "savunma": 1.00, "seviye": 1.35},
    "besiktas": {"hucum": 1.75, "savunma": 1.15, "seviye": 1.20},
    "trabzonspor": {"hucum": 1.60, "savunma": 1.15, "seviye": 1.10},
    "basaksehir": {"hucum": 1.55, "savunma": 1.15, "seviye": 1.10},
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
    "kocaelispor": {"hucum": 1.10, "savunma": 1.40, "seviye": 0.75},
    "amed": {"hucum": 1.15, "savunma": 1.35, "seviye": 0.75},
    "istanbulspor": {"hucum": 0.95, "savunma": 1.55, "seviye": 0.70},

    # --- PREMIER LİG & İNGİLTERE ---
    "man city": {"hucum": 2.15, "savunma": 1.00, "seviye": 1.40},
    "liverpool": {"hucum": 2.05, "savunma": 1.05, "seviye": 1.35},
    "arsenal": {"hucum": 1.95, "savunma": 0.95, "seviye": 1.30},
    "chelsea": {"hucum": 1.80, "savunma": 1.35, "seviye": 1.15},
    "man united": {"hucum": 1.65, "savunma": 1.35, "seviye": 1.15},
    "brighton": {"hucum": 1.70, "savunma": 1.25, "seviye": 1.15},
    "aston villa": {"hucum": 1.80, "savunma": 1.30, "seviye": 1.20},
    "everton": {"hucum": 1.25, "savunma": 1.25, "seviye": 1.00},
    "nottingham forest": {"hucum": 1.25, "savunma": 1.25, "seviye": 0.95},
    "fulham": {"hucum": 1.15, "savunma": 1.25, "seviye": 0.95},
    "crystal palace": {"hucum": 1.35, "savunma": 1.25, "seviye": 1.00},
    "ipswich": {"hucum": 1.15, "savunma": 1.50, "seviye": 0.80},
    "coventry": {"hucum": 1.30, "savunma": 1.35, "seviye": 0.85},
    "hull city": {"hucum": 1.20, "savunma": 1.35, "seviye": 0.85},
    "sunderland": {"hucum": 1.25, "savunma": 1.30, "seviye": 0.85},
    "middlesbrough": {"hucum": 1.35, "savunma": 1.30, "seviye": 0.90},

    # --- LA LİGA & İSPANYA ---
    "real madrid": {"hucum": 2.35, "savunma": 1.05, "seviye": 1.45},
    "barcelona": {"hucum": 2.30, "savunma": 1.15, "seviye": 1.40},
    "atletico madrid": {"hucum": 1.60, "savunma": 1.05, "seviye": 1.30},
    "real sociedad": {"hucum": 1.55, "savunma": 1.10, "seviye": 1.20},
    "sevilla": {"hucum": 1.45, "savunma": 1.25, "seviye": 1.10},
    "villareal": {"hucum": 1.80, "savunma": 1.25, "seviye": 1.15},
    "real betis": {"hucum": 1.50, "savunma": 1.15, "seviye": 1.15},
    "bilbao": {"hucum": 1.65, "savunma": 1.05, "seviye": 1.20},
    "leganes": {"hucum": 1.05, "savunma": 1.25, "seviye": 0.85},
    "levante": {"hucum": 1.25, "savunma": 1.35, "seviye": 0.85},
    "elche": {"hucum": 1.00, "savunma": 1.40, "seviye": 0.80},
    "malaga": {"hucum": 1.05, "savunma": 1.30, "seviye": 0.75},
    "tenerife": {"hucum": 0.95, "savunma": 1.30, "seviye": 0.75},

    # --- SERIE A ---
    "inter": {"hucum": 2.10, "savunma": 1.00, "seviye": 1.35},
    "milan": {"hucum": 1.85, "savunma": 1.20, "seviye": 1.25},
    "juventus": {"hucum": 1.75, "savunma": 1.00, "seviye": 1.30},
    "napoli": {"hucum": 1.75, "savunma": 1.15, "seviye": 1.20},
    "bologna": {"hucum": 1.45, "savunma": 1.10, "seviye": 1.15},
    "roma": {"hucum": 1.60, "savunma": 1.15, "seviye": 1.15},
    "torino": {"hucum": 1.20, "savunma": 1.15, "seviye": 1.00},
    "como": {"hucum": 1.20, "savunma": 1.40, "seviye": 0.85},
    "sassuolo": {"hucum": 1.35, "savunma": 1.45, "seviye": 0.90},

    # --- ALMANYA ---
    "bayern munih": {"hucum": 2.35, "savunma": 1.10, "seviye": 1.40},
    "dortmund": {"hucum": 2.20, "savunma": 1.15, "seviye": 1.30},
    "leipzig": {"hucum": 1.95, "savunma": 1.20, "seviye": 1.25},
    "elversberg": {"hucum": 1.20, "savunma": 1.35, "seviye": 0.80},

    # --- DİĞER AVRUPA ---
    "psg": {"hucum": 2.25, "savunma": 1.10, "seviye": 1.35},
    "marsilya": {"hucum": 1.85, "savunma": 1.20, "seviye": 1.20},
    "lille": {"hucum": 1.65, "savunma": 1.15, "seviye": 1.15},
    "brest": {"hucum": 1.45, "savunma": 1.20, "seviye": 1.10},
    "troyes": {"hucum": 1.10, "savunma": 1.45, "seviye": 0.75},
    "psv": {"hucum": 2.20, "savunma": 1.10, "seviye": 1.25},
    "sparta rotterdam": {"hucum": 1.30, "savunma": 1.40, "seviye": 0.90},
    "porto": {"hucum": 1.95, "savunma": 1.05, "seviye": 1.25},
    "sporting lizbon": {"hucum": 2.05, "savunma": 1.05, "seviye": 1.25},
    "famalicao": {"hucum": 1.15, "savunma": 1.30, "seviye": 0.85},
    "clup brugge": {"hucum": 1.70, "savunma": 1.25, "seviye": 1.10}
}

TAKMA_ADLAR = {
    "fb": "fenerbahce", "fener": "fenerbahce",
    "gs": "galatasaray", "cimbom": "galatasaray",
    "bjk": "besiktas", "besik": "besiktas",
    "ts": "trabzonspor", "trabzon": "trabzonspor",
    "ibfk": "basaksehir", "basak": "basaksehir",
    "samsun": "samsunspor", "eyup": "eyupspor",
    "gozgoz": "goztepe", "sivas": "sivasspor",
    "antalya": "antalyaspor", "alanya": "alanyaspor",
    "pasa": "kasimpasa", "rize": "rizespor",
    "antep": "gaziantep", "gfk": "gaziantep",
    "konya": "konyaspor", "kayseri": "kayserispor",
    "bodrum": "bodrum fk", "hatay": "hatayspor",
    "adana": "adana demirspor", "ads": "adana demirspor",
    "kocaeli": "kocaelispor", "istanbul": "istanbulspor",
    "city": "man city", "manc": "man city",
    "united": "man united", "manu": "man united",
    "pool": "liverpool", "villa": "aston villa",
    "palace": "crystal palace", "boro": "middlesbrough",
    "real": "real madrid", "barca": "barcelona", "barça": "barcelona",
    "atletico": "atletico madrid", "atm": "atletico madrid",
    "sociedad": "real sociedad", "socciedad": "real sociedad",
    "bayern": "bayern munih", "munih": "bayern munih",
    "elversberg": "elversberg", "elvers": "elversberg",
    "sporting": "sporting lizbon", "brugge": "clup brugge",
    "troyes": "troyes", "brest": "brest",
    "sparta": "sparta rotterdam", "rotterdam": "sparta rotterdam",
    "famalicao": "famalicao", "fama": "famalicao",
    "torino": "torino", "toro": "torino",
    "tenerife": "tenerife", "leganes": "leganes"
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
    p_25_ust = float(100 - (matrix[0,0] + matrix[1,0] + matrix[0,1] + matrix[1,1] + matrix[2,0] + matrix[0,2]))
    p_25_alt = float(100 - p_25_ust)
    p_1x = float(p_ev + p_ber)
    p_x2 = float(p_dep + p_ber)

    durum = "SARI"
    aksiyon = "PAS GEÇ / RİSKLİ"

    # --- GELİŞMİŞ VE ESNETİLMİŞ KARAR MOTORU ---
    if p_ev >= 65.0:
        durum = "YESIL"
        aksiyon = f"MS 1 ({ev_key.title()}) (%{p_ev:.1f})"
    elif p_dep >= 65.0:
        durum = "YESIL"
        aksiyon = f"MS 2 ({dep_key.title()}) (%{p_dep:.1f})"
    elif p_x2 >= 75.0:
        durum = "YESIL"
        aksiyon = f"X2 Çifte Şans (%{p_x2:.1f})"
    elif p_1x >= 75.0:
        durum = "YESIL"
        aksiyon = f"1X Çifte Şans (%{p_1x:.1f})"
    elif p_25_ust >= 58.0:
        durum = "YESIL"
        aksiyon = f"2.5 ÜST (%{p_25_ust:.1f})"
    elif p_25_alt >= 60.0:
        durum = "YESIL"
        aksiyon = f"2.5 ALT (%{p_25_alt:.1f})"

    return {
        "exp_h": exp_h, "exp_a": exp_a, "matrix": matrix,
        "p_ev": p_ev, "p_ber": p_ber, "p_dep": p_dep,
        "p_25_ust": p_25_ust, "p_25_alt": p_25_alt,
        "p_1x": p_1x, "p_x2": p_x2,
        "durum": durum, "aksiyon": aksiyon
    }

st.title("🎯 Akıllı Olasılık Motoru")
tab1, tab2 = st.tabs(["🔍 Tekli Detaylı Analiz", "⚡ Toplu Bülten Tarayıcı"])

# ================= TAB 1: TEKLİ DETAYLI ANALİZ =================
with tab1:
    takim_listesi = sorted(list(TAKIM_PROFILLERI.keys()))
    c1, c2 = st.columns(2)
    with c1:
        ev = st.selectbox("🏠 Ev Sahibi", takim_listesi, index=takim_listesi.index("torino") if "torino" in takim_listesi else 0)
    with c2:
        dep = st.selectbox("✈️ Deplasman", takim_listesi, index=takim_listesi.index("roma") if "roma" in takim_listesi else 1)

    if st.button("🚀 Tekli Analiz Et", use_container_width=True):
        res = mac_hesapla(ev, dep)
        matrix = res["matrix"]

        st.divider()
        if res["durum"] == "YESIL":
            st.success(f"### ✅ MODEL KARARI: {res['aksiyon']}")
        else:
            st.warning("### ⚠️ MODEL KARARI: PAS GEÇ / RİSKLİ (Tuzak Maç)")

        skorlar = {f"{h}-{a}": matrix[h, a] for h in range(6) for a in range(6)}
        sirali = sorted(skorlar.items(), key=lambda x: x[1], reverse=True)[:3]

        sc1, sc2, sc3 = st.columns(3)
        sc1.metric("1. İhtimal Skor", f"{sirali[0][0]}", f"%{sirali[0][1]:.1f}")
        sc2.metric("2. İhtimal Skor", f"{sirali[1][0]}", f"%{sirali[1][1]:.1f}")
        sc3.metric("3. İhtimal Skor", f"{sirali[2][0]}", f"%{sirali[2][1]:.1f}")

        st.markdown("##### 🏆 Maç Sonu (1-X-2) ve Çifte Şans Dağılımı")
        col_t1, col_t2, col_t3, col_t4, col_t5 = st.columns(5)
        col_t1.metric(f"MS 1 ({ev.title()})", f"%{res['p_ev']:.1f}")
        col_t2.metric("Beraberlik (X)", f"%{res['p_ber']:.1f}")
        col_t3.metric(f"MS 2 ({dep.title()})", f"%{res['p_dep']:.1f}")
        col_t4.metric("1X Çifte Şans", f"%{res['p_1x']:.1f}")
        col_t5.metric("X2 Çifte Şans", f"%{res['p_x2']:.1f}")

        m1, m2 = st.columns(2)
        m1.metric("Beklenen Gol Dengesi", f"{res['exp_h']:.2f} - {res['exp_a']:.2f}")
        m2.metric("2.5 Gol İhtimali", f"Üst: %{res['p_25_ust']:.1f}", f"Alt: %{res['p_25_alt']:.1f}")

        st.markdown("#### 📊 Skor Olasılık Matrisi (%)")
        df_matrix = pd.DataFrame(
            matrix,
            index=[f"{ev.title()} {i}" for i in range(6)],
            columns=[f"{dep.title()} {j}" for j in range(6)]
        )
        st.dataframe(df_matrix.style.background_gradient(cmap="YlGnBu", axis=None).format("{:.1f}%"), use_container_width=True)

# ================= TAB 2: TOPLU BÜLTEN TARAYICI =================
with tab2:
    st.markdown("##### 📋 Hafta Sonu Maçlarını Alt Alta Yapıştır")
    st.caption("Örnek format: `famalicao - sporting` veya `torino - roma` (tire `-` veya `vs` ile ayır)")

    ornek_bulten = (
        "famalicao - sporting lizbon\n"
        "sassuolo - juventus\n"
        "real sociedad - atletico madrid\n"
        "brest - psg\n"
        "torino - roma\n"
        "tenerife - leganes"
    )
    bulten_metni = st.text_area("Maç Listesi", value=ornek_bulten, height=180)

    if st.button("🔥 Bülteni Tara ve Analiz Et", use_container_width=True):
        satirlar = bulten_metni.strip().split("\n")
        yesil_maclar = []
        sari_maclar = []

        for satir in satirlar:
            if not satir.strip(): continue
            if "-" in satir:
                parcalar = satir.split("-")
            elif "vs" in satir.lower():
                parcalar = satir.lower().split("vs")
            else:
                continue

            ev_in, dep_in = parcalar[0].strip(), parcalar[1].strip()
            ev_k = takim_bul(ev_in)
            dep_k = takim_bul(dep_in)

            if not ev_k or not dep_k:
                continue

            sonuc = mac_hesapla(ev_k, dep_k)
            bilgi = {
                "Maç": f"{ev_k.title()} vs {dep_k.title()}",
                "Model Önerisi": sonuc["aksiyon"] if sonuc["durum"] == "YESIL" else "PAS GEÇ (Tuzak)",
                "MS 1 %": f"%{sonuc['p_ev']:.1f}",
                "MS 2 %": f"%{sonuc['p_dep']:.1f}",
                "1X %": f"%{sonuc['p_1x']:.1f}",
                "X2 %": f"%{sonuc['p_x2']:.1f}",
                "2.5 Üst %": f"%{sonuc['p_25_ust']:.1f}",
                "Beklenen Gol": f"{sonuc['exp_h']:.2f} - {sonuc['exp_a']:.2f}"
            }

            if sonuc["durum"] == "YESIL":
                yesil_maclar.append(bilgi)
            else:
                sari_maclar.append(bilgi)

        st.divider()
        st.markdown(f"### 🟢 OYNANABİLİR YEŞİL MAÇLAR ({len(yesil_maclar)} Maç)")
        if yesil_maclar:
            st.dataframe(pd.DataFrame(yesil_maclar), use_container_width=True)
            st.success("💡 Yeşil yanan maçlardan 2'li kombineler oluşturabilirsin.")
        else:
            st.info("Bültende doğrudan eşiği aşan yeşil maç bulunamadı.")

        with st.expander(f"🟡 Pas Geçilen / Sarı Maçlar ({len(sari_maclar)} Maç)"):
            if sari_maclar:
                st.dataframe(pd.DataFrame(sari_maclar), use_container_width=True)