"""
TAKIP LISTESI / WATCHLIST — ikinci sayfa
------------------------------------------------
Kullanici hisse ekler; guncel fiyat, gunluk degisim, 1 aylik mini grafik ve
52 hafta icindeki konumu gorur. Para birimi € / $ / ₺ (gercek kur ile).
Liste URL'de saklanir (yer imine ekle -> listen geri gelir).

NOT: Yahoo verisi ~15 dk gecikmelidir; gercek zamanli (tik-tik) degildir.
Egitim amaclidir; yatirim tavsiyesi degildir.
"""

import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np

st.set_page_config(page_title="Takip Listesi / Watchlist", page_icon="📊", layout="wide")

# ---------- Diller ----------
DILLER = {"Türkçe": "tr", "English": "en", "Deutsch": "de",
          "Русский": "ru", "Español": "es", "العربية": "ar"}
T = {
 "tr": dict(title="📊 Takip Listesi", intro="Takip etmek istediğin hisseleri ekle; güncel fiyat ve günlük değişimi gör.",
   currency="Para birimi", pick="Hisse ekle (listeden)", pick_help="Takip listene şirket ekle.",
   extra="Listede yoksa kod yaz (virgülle)", extra_help="Örn. GOOGL, BTC-USD.",
   refresh="🔄 Yenile", empty="Yukarıdan takip listene hisse ekle.",
   today="Bugün", range52="52 hafta", inrange="aralığın %{p}’inde",
   delayed="ℹ️ Fiyatlar ~15 dk gecikmeli olabilir (Yahoo Finance). Yatırım tavsiyesi değildir.",
   saved="✅ Listen URL’ye kaydedildi — bu sayfayı yer imine ekleyerek geri getirebilirsin."),
 "en": dict(title="📊 Watchlist", intro="Add stocks you want to follow; see current price and daily change.",
   currency="Currency", pick="Add stock (from list)", pick_help="Add a company to your watchlist.",
   extra="Not listed? Type tickers (comma)", extra_help="e.g. GOOGL, BTC-USD.",
   refresh="🔄 Refresh", empty="Add stocks to your watchlist above.",
   today="Today", range52="52-week", inrange="{p}% of range",
   delayed="ℹ️ Prices may be ~15 min delayed (Yahoo Finance). Not investment advice.",
   saved="✅ Your list is saved in the URL — bookmark this page to bring it back."),
 "de": dict(title="📊 Watchlist", intro="Füge Aktien hinzu, die du verfolgen willst; sieh Kurs und Tagesänderung.",
   currency="Währung", pick="Aktie hinzufügen (Liste)", pick_help="Unternehmen zur Watchlist hinzufügen.",
   extra="Nicht gelistet? Kürzel (Komma)", extra_help="z. B. GOOGL, BTC-USD.",
   refresh="🔄 Aktualisieren", empty="Füge oben Aktien zu deiner Watchlist hinzu.",
   today="Heute", range52="52 Wochen", inrange="{p}% der Spanne",
   delayed="ℹ️ Kurse können ~15 Min verzögert sein (Yahoo Finance). Keine Anlageberatung.",
   saved="✅ Deine Liste ist in der URL gespeichert — als Lesezeichen speichern."),
 "ru": dict(title="📊 Список наблюдения", intro="Добавьте акции для отслеживания; смотрите цену и дневное изменение.",
   currency="Валюта", pick="Добавить акцию (из списка)", pick_help="Добавьте компанию в список.",
   extra="Нет в списке? Тикеры (запятая)", extra_help="напр. GOOGL, BTC-USD.",
   refresh="🔄 Обновить", empty="Добавьте акции в список выше.",
   today="Сегодня", range52="52 недели", inrange="{p}% диапазона",
   delayed="ℹ️ Цены могут задерживаться на ~15 мин (Yahoo Finance). Не инвестсовет.",
   saved="✅ Ваш список сохранён в URL — добавьте страницу в закладки."),
 "es": dict(title="📊 Lista de seguimiento", intro="Añade acciones para seguir; ve el precio y el cambio diario.",
   currency="Moneda", pick="Añadir acción (de la lista)", pick_help="Añade una empresa a tu lista.",
   extra="¿No está? Escribe símbolos (coma)", extra_help="p. ej. GOOGL, BTC-USD.",
   refresh="🔄 Actualizar", empty="Añade acciones a tu lista arriba.",
   today="Hoy", range52="52 semanas", inrange="{p}% del rango",
   delayed="ℹ️ Los precios pueden tener ~15 min de retraso (Yahoo Finance). No es asesoramiento.",
   saved="✅ Tu lista está guardada en la URL — añade esta página a favoritos."),
 "ar": dict(title="📊 قائمة المتابعة", intro="أضف الأسهم التي تريد متابعتها؛ شاهد السعر والتغير اليومي.",
   currency="العملة", pick="أضف سهمًا (من القائمة)", pick_help="أضف شركة إلى قائمتك.",
   extra="غير موجود؟ اكتب الرموز (بفواصل)", extra_help="مثل GOOGL, BTC-USD.",
   refresh="🔄 تحديث", empty="أضف أسهمًا إلى قائمتك بالأعلى.",
   today="اليوم", range52="52 أسبوعًا", inrange="{p}% من النطاق",
   delayed="ℹ️ قد تتأخر الأسعار ~15 دقيقة (Yahoo Finance). ليست نصيحة استثمارية.",
   saved="✅ قائمتك محفوظة في الرابط — أضف الصفحة إلى المفضلة."),
}

POPULER = {
 "AAPL":"Apple","MSFT":"Microsoft","NVDA":"NVIDIA","AMZN":"Amazon","GOOGL":"Alphabet (Google)",
 "META":"Meta","TSLA":"Tesla","JPM":"JPMorgan","V":"Visa","MA":"Mastercard","KO":"Coca-Cola",
 "PEP":"PepsiCo","DIS":"Disney","NFLX":"Netflix","AMD":"AMD","INTC":"Intel","ORCL":"Oracle",
 "ADBE":"Adobe","CRM":"Salesforce","NKE":"Nike","MCD":"McDonald's","SBUX":"Starbucks",
 "BA":"Boeing","XOM":"Exxon","PFE":"Pfizer","BAC":"Bank of America","WMT":"Walmart",
 "COST":"Costco","HD":"Home Depot","UBER":"Uber","PLTR":"Palantir","COIN":"Coinbase",
 "SPY":"S&P 500","QQQ":"Nasdaq 100","BTC-USD":"Bitcoin","ETH-USD":"Ethereum","GLD":"Gold",
}
KATALOG = [f"{ad} ({tk})" for tk, ad in POPULER.items()]
KATALOG_MAP = {f"{ad} ({tk})": tk for tk, ad in POPULER.items()}

@st.cache_data(ttl=300)
def cek(ticker):
    df = yf.download(ticker, period="1y", auto_adjust=True, progress=False)
    if df.empty: return None
    c = df["Close"]
    if isinstance(c, pd.DataFrame): c = c.iloc[:, 0]
    return c.dropna()

@st.cache_data(ttl=3600)
def fx(sembol):
    if sembol == "$": return None
    try:
        if sembol == "€": return 1.0 / cek("EURUSD=X")
        if sembol == "₺": return cek("USDTRY=X")
    except Exception:
        return None
    return None

def para(x, s="€"):
    return f"{x:,.2f}".replace(",", "@").replace(".", ",").replace("@", ".") + " " + s

def sparkline(seri, renk, w=150, h=34):
    v = seri.values.astype(float)
    if len(v) > 60: v = v[:: max(1, len(v)//60)]
    lo, hi = float(np.nanmin(v)), float(np.nanmax(v)); rng = (hi-lo) or 1.0; n = len(v)
    pts = " ".join(f"{w*i/(max(1,n-1)):.1f},{h-3-(h-6)*(x-lo)/rng:.1f}" for i, x in enumerate(v))
    return (f'<svg width="100%" height="{h}" viewBox="0 0 {w} {h}" preserveAspectRatio="none" '
            f'style="margin-top:6px;display:block"><polyline fill="none" stroke="{renk}" '
            f'stroke-width="2" points="{pts}"/></svg>')

# ---------- Dil ----------
dil_ad = st.session_state.get("k_lang", "Türkçe")
with st.sidebar:
    dil_ad = st.selectbox("🌐 Language / Dil", list(DILLER.keys()),
                          index=list(DILLER.keys()).index(dil_ad) if dil_ad in DILLER else 0,
                          key="k_lang")
lang = DILLER.get(dil_ad, "tr")
L = T[lang]

st.markdown(f"""
<style>
  .stApp {{ background:#f7f9fc; }}
  .wkart {{ background:#fff; border:1px solid #e6eaf0; border-radius:16px; padding:16px 18px;
           box-shadow:0 1px 3px rgba(20,33,61,.06); margin-bottom:10px; }}
  .wad {{ color:#6b7280; font-size:13px; font-weight:600; }}
  .wfiyat {{ font-size:26px; font-weight:800; color:#14213d; margin-top:2px; }}
  .wdeg {{ font-size:15px; font-weight:700; }} .yesil {{ color:#16a34a; }} .kirmizi {{ color:#dc2626; }}
  .w52 {{ color:#6b7280; font-size:12px; margin-top:6px; }}
  {"[data-testid='stAppViewContainer'],[data-testid='stSidebar']{direction:rtl;text-align:right}" if lang=="ar" else ""}
</style>
""", unsafe_allow_html=True)

# ---------- URL'den liste ----------
qp = st.query_params.get("takip", "")
url_kodlar = [c.strip().upper() for c in qp.split(",") if c.strip()] or ["AAPL", "MSFT", "NVDA"]
on_secili = [f"{POPULER[c]} ({c})" for c in url_kodlar if c in POPULER]
on_ekstra = ", ".join([c for c in url_kodlar if c not in POPULER])

# ---------- Kontroller ----------
with st.sidebar:
    sembol = st.selectbox(L["currency"], ["€", "$", "₺"], key="k_takip_sembol")
    secili = st.multiselect(L["pick"], KATALOG, default=on_secili, help=L["pick_help"])
    ekstra = st.text_input(L["extra"], value=on_ekstra, help=L["extra_help"])
    if st.button(L["refresh"], use_container_width=True):
        st.cache_data.clear(); st.rerun()

kodlar = [KATALOG_MAP[e] for e in secili] + [x.strip().upper() for x in ekstra.split(",") if x.strip()]
gor = set(); kodlar = [k for k in kodlar if k and not (k in gor or gor.add(k))][:16]
st.query_params["takip"] = ",".join(kodlar)   # URL'de sakla

st.title(L["title"])
st.caption(L["intro"])

if not kodlar:
    st.info(L["empty"])
else:
    fxs = fx(sembol)
    with st.spinner("..."):
        veriler = {k: cek(k) for k in kodlar}
    kartlar = []
    for k in kodlar:
        s = veriler.get(k)
        if s is None or len(s) < 2:
            continue
        if fxs is not None:
            s = s * fxs.reindex(s.index).ffill().bfill()
        son = float(s.iloc[-1]); onceki = float(s.iloc[-2])
        deg = son - onceki; pct = (deg / onceki * 100) if onceki else 0
        lo, hi = float(s.min()), float(s.max())
        konum = (son - lo) / (hi - lo) * 100 if hi > lo else 50
        kartlar.append((k, son, deg, pct, s.tail(22), lo, hi, konum))

    # 4'lu izgara
    for i in range(0, len(kartlar), 4):
        satir = st.columns(4)
        for j, (k, son, deg, pct, spark, lo, hi, konum) in enumerate(kartlar[i:i+4]):
            renk = "#16a34a" if deg >= 0 else "#dc2626"
            sinif = "yesil" if deg >= 0 else "kirmizi"
            ad = POPULER.get(k, k)
            satir[j].markdown(
                f'<div class="wkart"><div class="wad">{ad} · {k}</div>'
                f'<div class="wfiyat">{para(son, sembol)}</div>'
                f'<div class="wdeg {sinif}">{para(deg, sembol)} ({pct:+.2f}%) · {L["today"]}</div>'
                f'{sparkline(spark, renk)}'
                f'<div class="w52">{L["range52"]}: {para(lo, sembol)} – {para(hi, sembol)} · '
                f'{L["inrange"].format(p=int(konum))}</div></div>', unsafe_allow_html=True)

    st.caption(L["saved"])

st.divider()
st.caption(L["delayed"])
