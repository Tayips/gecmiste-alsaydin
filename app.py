"""
WhatIfInvest — YONLENDIRICI (router)
------------------------------------------------
Bu dosya uygulamanin giris noktasidir. Sayfalar views/ klasorunde tutulur ve
st.navigation ile tanimlanir; boylece menu isimleri secilen dile gore degisir.
Dil ve tema burada (tum sayfalarda ortak) secilir.
"""
import streamlit as st

st.set_page_config(page_title="WhatIfInvest", page_icon="assets/favicon.png", layout="wide")
try:
    st.logo("assets/logo_lockup.png", size="large", icon_image="assets/favicon.png")
except Exception:
    pass

DILLER = {"Türkçe": "tr", "English": "en", "Deutsch": "de",
          "Русский": "ru", "Español": "es", "العربية": "ar"}
DARK_LBL = {"tr": "🌙 Karanlık mod", "en": "🌙 Dark mode", "de": "🌙 Dunkelmodus",
            "ru": "🌙 Тёмная тема", "es": "🌙 Modo oscuro", "ar": "🌙 الوضع الداكن"}

# Menu isimleri (dile gore)
NAV = {
 "tr": dict(home="🏠 Ana Sayfa", takip="📊 Takip", portfoy="💼 Portföy", fikirler="💡 Fikirler", profil="🙍 Profil"),
 "en": dict(home="🏠 Home", takip="📊 Watchlist", portfoy="💼 Portfolio", fikirler="💡 Ideas", profil="🙍 Profile"),
 "de": dict(home="🏠 Startseite", takip="📊 Watchlist", portfoy="💼 Portfolio", fikirler="💡 Ideen", profil="🙍 Profil"),
 "ru": dict(home="🏠 Главная", takip="📊 Список", portfoy="💼 Портфель", fikirler="💡 Идеи", profil="🙍 Профиль"),
 "es": dict(home="🏠 Inicio", takip="📊 Seguimiento", portfoy="💼 Cartera", fikirler="💡 Ideas", profil="🙍 Perfil"),
 "ar": dict(home="🏠 الرئيسية", takip="📊 المتابعة", portfoy="💼 المحفظة", fikirler="💡 أفكار", profil="🙍 الملف"),
}

# ---- Dil + tema (tum sayfalarda ortak, kalici) ----
st.session_state.setdefault("dil_ad", "Türkçe")
st.session_state.setdefault("tema_koyu", False)
_diller = list(DILLER.keys())
_idx = _diller.index(st.session_state["dil_ad"]) if st.session_state["dil_ad"] in _diller else 0
dil_ad = st.sidebar.selectbox("🌐 Language / Dil", _diller, index=_idx)
st.session_state["dil_ad"] = dil_ad
lang = DILLER[dil_ad]
st.session_state["tema_koyu"] = st.sidebar.toggle(
    DARK_LBL.get(lang, "🌙 Dark"), value=st.session_state["tema_koyu"])

N = NAV.get(lang, NAV["tr"])

# ---- Sayfalar ----
sayfalar = [
    st.Page("views/anasayfa.py", title=N["home"], url_path="home", default=True),
    st.Page("views/takip.py",    title=N["takip"],    url_path="watchlist"),
    st.Page("views/portfoy.py",  title=N["portfoy"],  url_path="portfolio"),
    st.Page("views/fikirler.py", title=N["fikirler"], url_path="ideas"),
    st.Page("views/profil.py",   title=N["profil"],   url_path="profile"),
]

st.navigation(sayfalar).run()
