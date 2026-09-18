"""
TAKIP LISTESI / WATCHLIST — v2
------------------------------------------------
- Kart veya Tablo gorunumu (tabloda satir ici mini grafik)
- Hazir listeler (Big Tech / Otomotiv-EV / Populer) tek tikla
- Siralama (en cok yukselen / dusen / isme gore)
- Portfoy ozet KPI'i (ortalama gunluk performans)
- Guncel fiyat, gunluk degisim, hacim, 52 hafta konumu, son guncelleme
- Karttan "cikar" butonu, € / $ / ₺ (gercek kur), 6 dil, liste URL'de saklanir

NOT: Yahoo verisi ~15 dk gecikmeli olabilir; gercek zamanli degildir.
Egitim amaclidir; yatirim tavsiyesi degildir.
"""

import re
import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
import requests
from datetime import datetime
import db  # ortak veritabani yardimcisi (repo ana klasorunde db.py)

st.set_page_config(page_title="Takip Listesi / Watchlist", page_icon="📊", layout="wide")

# ---------- Giris zorunlu (kim oldugunu bilmemiz gerek) ----------
_u = getattr(st, "user", None)
if not _u or not _u.is_logged_in:
    st.title("📊 Takip Listesi")
    st.info("Takip listeni kaydedebilmek için önce Google ile giriş yapmalısın.")
    if st.button("Google ile giriş yap", type="primary"):
        st.login()
    st.stop()
EMAIL = st.user.email

DILLER = {"Türkçe": "tr", "English": "en", "Deutsch": "de",
          "Русский": "ru", "Español": "es", "العربية": "ar"}

T = {
 "tr": dict(title="📊 Takip Listesi", intro="Takip etmek istediğin hisseleri ekle; güncel fiyat ve günlük değişimi gör.",
   currency="Para birimi", pick="Takip listem (ekle/çıkar)", pick_help="Tıkla ve ekle; çipteki × ile çıkar.",
   extra="Listede yoksa kod (virgülle)", extra_help="Örn. GOOGL, BTC-USD.",
   presets="Hazır listeler:", p_big="💻 Dev Teknoloji", p_ev="🚗 Otomotiv & EV", p_pop="🚀 Popüler",
   view="Görünüm", v_card="Kartlar", v_table="Tablo",
   sort="Sırala", s_def="Varsayılan", s_up="En çok yükselen", s_down="En çok düşen", s_name="İsme göre",
   refresh="🔄 Yenile", empty="Yukarıdan takip listene hisse ekle.",
   today="Bugün", vol="Hacim", range52="52 hafta", inrange="aralığın %{p}’inde", remove="Çıkar",
   port="Portföy özeti", avg="Ortalama günlük", best="En iyi", worst="En kötü", count="Hisse", pe="F/K", mcap="Piyasa değeri", a_title="Fiyat alarmı", a_up="Üstüne çıkınca", a_down="Altına inince", a_price="Hedef fiyat", a_add="Ekle", a_reached="ulaştı", a_pending="hedef", c_alarm="Alarm", a_none="Alarm yok", src_live="🟢 Canlı fiyat: Finnhub · geçmiş: Yahoo", src_off="Fiyatlar Yahoo (gecikmeli). Canlı fiyat için Finnhub anahtarı ekle.", delayed_live="ℹ️ Canlı fiyat Finnhub; geçmiş veri Yahoo (gecikmeli olabilir). Yatırım tavsiyesi değildir.",
   c_sym="Sembol", c_name="Şirket", c_price="Fiyat", c_chg="Değişim %", c_vol="Hacim",
   c_low="52h Düşük", c_high="52h Yüksek", c_chart="Grafik",
   updated="Son güncelleme", delayed="ℹ️ Fiyatlar ~15 dk gecikmeli olabilir (Yahoo Finance). Yatırım tavsiyesi değildir.",
   saved="✅ Listen URL’ye kaydedildi — bu sayfayı yer imine ekleyerek geri getirebilirsin."),
 "en": dict(title="📊 Watchlist", intro="Add stocks you want to follow; see current price and daily change.",
   currency="Currency", pick="My watchlist (add/remove)", pick_help="Click to add; remove via × on the chip.",
   extra="Not listed? Ticker (comma)", extra_help="e.g. GOOGL, BTC-USD.",
   presets="Ready lists:", p_big="💻 Big Tech", p_ev="🚗 Auto & EV", p_pop="🚀 Popular",
   view="View", v_card="Cards", v_table="Table",
   sort="Sort", s_def="Default", s_up="Top gainers", s_down="Top losers", s_name="By name",
   refresh="🔄 Refresh", empty="Add stocks to your watchlist above.",
   today="Today", vol="Volume", range52="52-week", inrange="{p}% of range", remove="Remove",
   port="Portfolio summary", avg="Avg daily", best="Best", worst="Worst", count="Stocks", pe="P/E", mcap="Market cap", a_title="Price alert", a_up="Rises above", a_down="Falls below", a_price="Target price", a_add="Add", a_reached="reached", a_pending="target", c_alarm="Alert", a_none="No alerts", src_live="🟢 Live price: Finnhub · history: Yahoo", src_off="Prices from Yahoo (delayed). Add a Finnhub key for live prices.", delayed_live="ℹ️ Live price from Finnhub; historical data from Yahoo (may be delayed). Not investment advice.",
   c_sym="Symbol", c_name="Company", c_price="Price", c_chg="Change %", c_vol="Volume",
   c_low="52w Low", c_high="52w High", c_chart="Chart",
   updated="Last update", delayed="ℹ️ Prices may be ~15 min delayed (Yahoo Finance). Not investment advice.",
   saved="✅ Your list is saved in the URL — bookmark this page to bring it back."),
 "de": dict(title="📊 Watchlist", intro="Füge Aktien hinzu, die du verfolgen willst; sieh Kurs und Tagesänderung.",
   currency="Währung", pick="Meine Watchlist (hinzu/entf.)", pick_help="Klick zum Hinzufügen; × am Chip entfernt.",
   extra="Nicht gelistet? Kürzel (Komma)", extra_help="z. B. GOOGL, BTC-USD.",
   presets="Fertige Listen:", p_big="💻 Big Tech", p_ev="🚗 Auto & EV", p_pop="🚀 Beliebt",
   view="Ansicht", v_card="Karten", v_table="Tabelle",
   sort="Sortieren", s_def="Standard", s_up="Top-Gewinner", s_down="Top-Verlierer", s_name="Nach Name",
   refresh="🔄 Aktualisieren", empty="Füge oben Aktien zu deiner Watchlist hinzu.",
   today="Heute", vol="Volumen", range52="52 Wochen", inrange="{p}% der Spanne", remove="Entfernen",
   port="Portfolio-Übersicht", avg="Ø täglich", best="Beste", worst="Schlechteste", count="Aktien", pe="KGV", mcap="Marktkap.", a_title="Preisalarm", a_up="Steigt über", a_down="Fällt unter", a_price="Zielpreis", a_add="Hinzufügen", a_reached="erreicht", a_pending="Ziel", c_alarm="Alarm", a_none="Keine Alarme", src_live="🟢 Live-Kurs: Finnhub · Verlauf: Yahoo", src_off="Kurse von Yahoo (verzögert). Finnhub-Key für Live-Kurse hinzufügen.", delayed_live="ℹ️ Live-Kurs von Finnhub; historische Daten von Yahoo (evtl. verzögert). Keine Anlageberatung.",
   c_sym="Symbol", c_name="Firma", c_price="Kurs", c_chg="Änderung %", c_vol="Volumen",
   c_low="52W Tief", c_high="52W Hoch", c_chart="Chart",
   updated="Letzte Aktualisierung", delayed="ℹ️ Kurse können ~15 Min verzögert sein (Yahoo Finance). Keine Anlageberatung.",
   saved="✅ Deine Liste ist in der URL gespeichert — als Lesezeichen speichern."),
 "ru": dict(title="📊 Список наблюдения", intro="Добавьте акции для отслеживания; смотрите цену и дневное изменение.",
   currency="Валюта", pick="Мой список (добавить/убрать)", pick_help="Нажмите, чтобы добавить; × на чипе убирает.",
   extra="Нет в списке? Тикер (запятая)", extra_help="напр. GOOGL, BTC-USD.",
   presets="Готовые списки:", p_big="💻 Big Tech", p_ev="🚗 Авто и EV", p_pop="🚀 Популярное",
   view="Вид", v_card="Карточки", v_table="Таблица",
   sort="Сортировка", s_def="По умолчанию", s_up="Лидеры роста", s_down="Лидеры падения", s_name="По имени",
   refresh="🔄 Обновить", empty="Добавьте акции в список выше.",
   today="Сегодня", vol="Объём", range52="52 недели", inrange="{p}% диапазона", remove="Убрать",
   port="Сводка портфеля", avg="Средн. за день", best="Лучшая", worst="Худшая", count="Акции", pe="P/E", mcap="Капитализация", a_title="Ценовой алерт", a_up="Выше", a_down="Ниже", a_price="Целевая цена", a_add="Добавить", a_reached="достигнуто", a_pending="цель", c_alarm="Алерт", a_none="Нет алертов", src_live="🟢 Живая цена: Finnhub · история: Yahoo", src_off="Цены Yahoo (задержка). Добавьте ключ Finnhub для живых цен.", delayed_live="ℹ️ Живая цена — Finnhub; история — Yahoo (возможна задержка). Не инвестсовет.",
   c_sym="Тикер", c_name="Компания", c_price="Цена", c_chg="Изм. %", c_vol="Объём",
   c_low="52н мин", c_high="52н макс", c_chart="График",
   updated="Обновлено", delayed="ℹ️ Цены могут задерживаться ~15 мин (Yahoo Finance). Не инвестсовет.",
   saved="✅ Ваш список сохранён в URL — добавьте страницу в закладки."),
 "es": dict(title="📊 Lista de seguimiento", intro="Añade acciones para seguir; ve el precio y el cambio diario.",
   currency="Moneda", pick="Mi lista (añadir/quitar)", pick_help="Haz clic para añadir; × en el chip quita.",
   extra="¿No está? Símbolo (coma)", extra_help="p. ej. GOOGL, BTC-USD.",
   presets="Listas listas:", p_big="💻 Big Tech", p_ev="🚗 Auto y EV", p_pop="🚀 Populares",
   view="Vista", v_card="Tarjetas", v_table="Tabla",
   sort="Ordenar", s_def="Predeterminado", s_up="Mayores subidas", s_down="Mayores bajadas", s_name="Por nombre",
   refresh="🔄 Actualizar", empty="Añade acciones a tu lista arriba.",
   today="Hoy", vol="Volumen", range52="52 semanas", inrange="{p}% del rango", remove="Quitar",
   port="Resumen de cartera", avg="Media diaria", best="Mejor", worst="Peor", count="Acciones", pe="PER", mcap="Cap. mercado", a_title="Alerta de precio", a_up="Sube por encima", a_down="Baja por debajo", a_price="Precio objetivo", a_add="Añadir", a_reached="alcanzado", a_pending="objetivo", c_alarm="Alerta", a_none="Sin alertas", src_live="🟢 Precio en vivo: Finnhub · histórico: Yahoo", src_off="Precios de Yahoo (con retraso). Añade una clave Finnhub para precios en vivo.", delayed_live="ℹ️ Precio en vivo de Finnhub; datos históricos de Yahoo (pueden retrasarse). No es asesoramiento.",
   c_sym="Símbolo", c_name="Empresa", c_price="Precio", c_chg="Cambio %", c_vol="Volumen",
   c_low="Mín 52s", c_high="Máx 52s", c_chart="Gráfico",
   updated="Última actualización", delayed="ℹ️ Los precios pueden tener ~15 min de retraso (Yahoo Finance). No es asesoramiento.",
   saved="✅ Tu lista está guardada en la URL — añade esta página a favoritos."),
 "ar": dict(title="📊 قائمة المتابعة", intro="أضف الأسهم التي تريد متابعتها؛ شاهد السعر والتغير اليومي.",
   currency="العملة", pick="قائمتي (إضافة/إزالة)", pick_help="انقر للإضافة؛ × على الرقاقة للإزالة.",
   extra="غير موجود؟ رمز (بفواصل)", extra_help="مثل GOOGL, BTC-USD.",
   presets="قوائم جاهزة:", p_big="💻 التقنية الكبرى", p_ev="🚗 سيارات وكهربائية", p_pop="🚀 شائع",
   view="العرض", v_card="بطاقات", v_table="جدول",
   sort="ترتيب", s_def="افتراضي", s_up="الأكثر ارتفاعًا", s_down="الأكثر انخفاضًا", s_name="حسب الاسم",
   refresh="🔄 تحديث", empty="أضف أسهمًا إلى قائمتك بالأعلى.",
   today="اليوم", vol="الحجم", range52="52 أسبوعًا", inrange="{p}% من النطاق", remove="إزالة",
   port="ملخص المحفظة", avg="متوسط يومي", best="الأفضل", worst="الأسوأ", count="أسهم", pe="مكرر الربح", mcap="القيمة السوقية", a_title="تنبيه سعري", a_up="يتجاوز", a_down="ينزل تحت", a_price="السعر المستهدف", a_add="إضافة", a_reached="تحقق", a_pending="الهدف", c_alarm="تنبيه", a_none="لا تنبيهات", src_live="🟢 سعر حي: Finnhub · التاريخ: Yahoo", src_off="الأسعار من Yahoo (متأخرة). أضف مفتاح Finnhub للأسعار الحية.", delayed_live="ℹ️ السعر الحي من Finnhub؛ البيانات التاريخية من Yahoo (قد تتأخر). ليست نصيحة استثمارية.",
   c_sym="الرمز", c_name="الشركة", c_price="السعر", c_chg="التغير %", c_vol="الحجم",
   c_low="أدنى 52أ", c_high="أعلى 52أ", c_chart="رسم",
   updated="آخر تحديث", delayed="ℹ️ قد تتأخر الأسعار ~15 دقيقة (Yahoo Finance). ليست نصيحة استثمارية.",
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
 "F":"Ford","GM":"General Motors","RIVN":"Rivian","NIO":"NIO",
}
KATALOG = [f"{ad} ({tk})" for tk, ad in POPULER.items()]
KATALOG_MAP = {f"{ad} ({tk})": tk for tk, ad in POPULER.items()}

HAZIR = {
 "p_big": ["AAPL", "MSFT", "NVDA", "GOOGL", "AMZN", "META"],
 "p_ev":  ["TSLA", "F", "GM", "RIVN", "NIO"],
 "p_pop": ["AAPL", "MSFT", "AMZN", "NVDA", "META", "GOOGL", "JPM", "V"],
}

@st.cache_data(ttl=300)
def cek(ticker):
    df = yf.download(ticker, period="1y", auto_adjust=True, progress=False)
    if df.empty: return None
    close = df["Close"]; vol = df.get("Volume")
    if isinstance(close, pd.DataFrame): close = close.iloc[:, 0]
    if vol is not None and isinstance(vol, pd.DataFrame): vol = vol.iloc[:, 0]
    out = pd.DataFrame({"close": close})
    out["vol"] = vol if vol is not None else 0.0
    return out.dropna(subset=["close"])

try:
    FINN = st.secrets.get("FINNHUB_KEY", "")
except Exception:
    FINN = ""

@st.cache_data(ttl=60)
def finnhub_quote(ticker, key):
    """Finnhub'dan canli fiyat + gunluk degisim (USD). Basarisizsa None."""
    if not key:
        return None
    try:
        r = requests.get("https://finnhub.io/api/v1/quote",
                         params={"symbol": ticker, "token": key}, timeout=6)
        j = r.json()
        if j.get("c"):
            return dict(c=float(j["c"]), d=float(j.get("d") or 0), dp=float(j.get("dp") or 0))
    except Exception:
        return None
    return None

@st.cache_data(ttl=3600)
def fx(sembol):
    if sembol == "$": return None
    try:
        if sembol == "€":
            e = cek("EURUSD=X"); return (1.0 / e["close"]) if e is not None else None
        if sembol == "₺":
            u = cek("USDTRY=X"); return u["close"] if u is not None else None
    except Exception:
        return None
    return None

def para(x, s="€"):
    return f"{x:,.2f}".replace(",", "@").replace(".", ",").replace("@", ".") + " " + s

def hacim(v):
    for birim, b in [("B", 1e9), ("M", 1e6), ("K", 1e3)]:
        if v >= b: return f"{v/b:.1f}{birim}"
    return f"{v:.0f}"

def buyuk(v):
    for birim, b in [("T", 1e12), ("B", 1e9), ("M", 1e6)]:
        if v >= b: return f"{v/b:.2f}{birim}"
    return f"{v:.0f}"

@st.cache_data(ttl=86400)
def temel(ticker):
    """F/K ve Piyasa Degeri (USD). Yavas/eksik olabilir; alinamazsa (None,None)."""
    try:
        info = yf.Ticker(ticker).info
        pe = info.get("trailingPE")
        mc = info.get("marketCap")
        return (float(pe) if pe else None, float(mc) if mc else None)
    except Exception:
        return (None, None)

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
DARK_LBL = {"tr":"🌙 Karanlık mod","en":"🌙 Dark mode","de":"🌙 Dunkelmodus",
            "ru":"🌙 Тёмная тема","es":"🌙 Modo oscuro","ar":"🌙 الوضع الداكن"}
def palet(koyu):
    if koyu:
        return dict(bg="#0f1420", panel="#1a2233", border="#2a3550", text="#e8eaed",
                    muted="#9aa7bd", kpi="#0b1626")
    return dict(bg="#f7f9fc", panel="#ffffff", border="#e6eaf0", text="#14213d",
                muted="#6b7280", kpi="#14213d")

with st.sidebar:
    dil_ad = st.selectbox("🌐 Language / Dil", list(DILLER.keys()),
                          index=list(DILLER.keys()).index(dil_ad) if dil_ad in DILLER else 0, key="k_lang")
lang = DILLER.get(dil_ad, "tr"); L = T[lang]
koyu = st.sidebar.toggle(DARK_LBL.get(lang, "🌙 Dark"), key="k_koyu")
P = palet(koyu)
btn_css = (f'.stDownloadButton button, [data-testid="stLinkButton"] a, .stButton button '
           f'{{ background:{P["panel"]}; color:{P["text"]}; border:1px solid {P["border"]}; }}'
           if koyu else "")

st.markdown(f"""
<style>
  {btn_css}
  .stApp {{ background:{P['bg']}; }}
  [data-testid="stSidebar"] {{ background:{P['panel']}; }}
  .stApp, [data-testid="stSidebar"], h1, h2, h3, label, p, span, .stMarkdown {{ color:{P['text']}; }}
  .wkart {{ background:{P['panel']}; border:1px solid {P['border']}; border-radius:16px; padding:16px 18px;
           box-shadow:0 1px 3px rgba(0,0,0,.08); margin-bottom:6px; }}
  .wad {{ color:{P['muted']}; font-size:13px; font-weight:600; }}
  .wfiyat {{ font-size:26px; font-weight:800; color:{P['text']}; margin-top:2px; }}
  .wdeg {{ font-size:15px; font-weight:700; }} .yesil {{ color:#16a34a; }} .kirmizi {{ color:#dc2626; }}
  .w52 {{ color:{P['muted']}; font-size:12px; margin-top:6px; }}
  .kpi {{ background:{P['kpi']}; color:#fff; border-radius:14px; padding:14px 18px; }}
  .kpi small {{ color:#9aa7bd; font-size:12px; }} .kpi b {{ font-size:22px; }}
  {"[data-testid='stAppViewContainer'],[data-testid='stSidebar']{direction:rtl;text-align:right}" if lang=="ar" else ""}
</style>
""", unsafe_allow_html=True)

# ---------- Liste durumu (veritabanindan ilk yukleme) ----------
if "takip_loaded" not in st.session_state:
    db_kodlar = db.takip_getir(EMAIL) or ["AAPL", "MSFT", "NVDA"]
    st.session_state["takip_ms"] = [f"{POPULER[c]} ({c})" for c in db_kodlar if c in POPULER]
    st.session_state["takip_extra"] = ", ".join([c for c in db_kodlar if c not in POPULER])
    st.session_state["takip_loaded"] = True

def uygula_hazir(kodlar):
    st.session_state["takip_ms"] = [f"{POPULER[c]} ({c})" for c in kodlar if c in POPULER]
    st.session_state["takip_extra"] = ", ".join([c for c in kodlar if c not in POPULER])

def cikar(kod):
    lbl = f"{POPULER.get(kod, kod)} ({kod})"
    if lbl in st.session_state.get("takip_ms", []):
        st.session_state["takip_ms"] = [x for x in st.session_state["takip_ms"] if x != lbl]
    else:
        ex = [c.strip().upper() for c in st.session_state.get("takip_extra", "").split(",") if c.strip()]
        st.session_state["takip_extra"] = ", ".join([c for c in ex if c != kod])

# ---------- Sidebar kontrolleri ----------
with st.sidebar:
    st.caption(f"👤 {EMAIL}")
    if st.button("Çıkış yap", width="stretch"):
        st.logout()
    st.divider()
    sembol = st.selectbox(L["currency"], ["€", "$", "₺"], key="k_takip_sembol")
    st.caption(L["presets"])
    hc = st.columns(3)
    if hc[0].button(L["p_big"], width="stretch"): uygula_hazir(HAZIR["p_big"]); st.rerun()
    if hc[1].button(L["p_ev"], width="stretch"): uygula_hazir(HAZIR["p_ev"]); st.rerun()
    if hc[2].button(L["p_pop"], width="stretch"): uygula_hazir(HAZIR["p_pop"]); st.rerun()
    secili = st.multiselect(L["pick"], KATALOG, key="takip_ms", help=L["pick_help"])
    ekstra = st.text_input(L["extra"], key="takip_extra", help=L["extra_help"])
    gorunum = st.radio(L["view"], [L["v_card"], L["v_table"]], horizontal=True)
    sirala = st.selectbox(L["sort"], [L["s_def"], L["s_up"], L["s_down"], L["s_name"]])
    if st.button(L["refresh"], width="stretch"):
        st.cache_data.clear(); st.rerun()

kodlar = [KATALOG_MAP[e] for e in secili] + [x.strip().upper() for x in ekstra.split(",") if x.strip()]
gor = set(); kodlar = [k for k in kodlar if k and not (k in gor or gor.add(k))][:20]
# Liste degistiyse veritabanina kaydet
if st.session_state.get("takip_saved") != kodlar:
    try:
        db.takip_kaydet(EMAIL, kodlar)
        st.session_state["takip_saved"] = list(kodlar)
    except Exception as e:
        st.warning("Takip listesi kaydedilemedi: " + str(e))

# ---------- Fiyat alarmlari (URL'de saklanir) ----------
def _parse_alarm(txt):
    d = {}
    for p in txt.split("|"):
        m = re.match(r"([A-Za-z0-9.\-]+)(>=|<=)([0-9.]+)$", p)
        if m: d[m.group(1).upper()] = (m.group(2), float(m.group(3)))
    return d
if "alarm_loaded" not in st.session_state:
    st.session_state["alarmlar"] = db.alarm_getir(EMAIL)
    st.session_state["alarm_loaded"] = True

with st.sidebar.expander("🔔 " + L["a_title"]):
    if kodlar:
        at = st.selectbox(L["c_sym"], kodlar, key="al_sym")
        ay = st.radio(L["a_title"], [">=", "<="], key="al_yon",
                      format_func=lambda y: L["a_up"] if y == ">=" else L["a_down"], horizontal=True)
        ah = st.number_input(L["a_price"] + " (USD)", min_value=0.0, step=1.0, key="al_fiyat",
                             help="Hedef fiyatı USD olarak gir. Bildirim, fiyat bu USD seviyesini geçince gelir.")
        if st.button(L["a_add"], width="stretch") and ah > 0:
            st.session_state["alarmlar"][at] = (ay, ah); st.rerun()
    if st.session_state["alarmlar"]:
        for tk, (y, h) in list(st.session_state["alarmlar"].items()):
            c = st.columns([4, 1])
            c[0].caption(f"{tk} {y} {h:g}")
            if c[1].button("✕", key=f"aldel_{tk}"):
                del st.session_state["alarmlar"][tk]; st.rerun()
    else:
        st.caption(L["a_none"])
# Alarmlar degistiyse veritabanina kaydet
if st.session_state.get("alarm_saved") != st.session_state["alarmlar"]:
    try:
        db.alarm_kaydet(EMAIL, st.session_state["alarmlar"])
        st.session_state["alarm_saved"] = dict(st.session_state["alarmlar"])
    except Exception as e:
        st.warning("Alarmlar kaydedilemedi: " + str(e))

# ---------- Bildirim ayarlari (Telegram + e-posta) ----------
if "bildirim_loaded" not in st.session_state:
    try:
        b = db.bildirim_getir(EMAIL)
    except Exception:
        b = None
    st.session_state["b_chat"] = (b or {}).get("telegram_chat_id", "") or ""
    st.session_state["b_tg"] = bool((b or {}).get("telegram_aktif", True))
    st.session_state["b_mail"] = bool((b or {}).get("eposta_aktif", True))
    st.session_state["bildirim_loaded"] = True

with st.sidebar.expander("📣 Bildirim ayarları"):
    st.caption("Alarm tetiklenince (uygulama kapalı olsa bile) sana haber gelir.")
    chat = st.text_input("Telegram Chat ID", value=st.session_state["b_chat"],
                         help="Kendi bot'undan getUpdates ile aldığın sayısal ID.")
    tg = st.checkbox("Telegram bildirimi", value=st.session_state["b_tg"])
    ml = st.checkbox(f"E-posta bildirimi ({EMAIL})", value=st.session_state["b_mail"])
    if st.button("Ayarları kaydet", width="stretch"):
        try:
            db.bildirim_kaydet(EMAIL, chat.strip(), tg, ml)
            st.session_state["b_chat"] = chat.strip()
            st.session_state["b_tg"] = tg
            st.session_state["b_mail"] = ml
            st.success("✅ Bildirim ayarları kaydedildi.")
        except Exception as e:
            st.error("Kaydedilemedi: " + str(e))

st.title(L["title"])
st.caption(L["intro"])

if not kodlar:
    st.info(L["empty"])
    st.stop()

fxs = fx(sembol)
with st.spinner("..."):
    veriler = {k: cek(k) for k in kodlar}

rows = []
for k in kodlar:
    d = veriler.get(k)
    if d is None or len(d) < 2:
        continue
    s = d["close"]
    if fxs is not None:
        s = s * fxs.reindex(s.index).ffill().bfill()
    kur_son = float(fxs.reindex(d["close"].index).ffill().bfill().iloc[-1]) if fxs is not None else 1.0
    # Canli fiyat (Finnhub) varsa onu kullan; yoksa Yahoo son kapanis
    q = finnhub_quote(k, FINN)
    if q and q["c"] > 0:
        son = q["c"] * kur_son; deg = q["d"] * kur_son; pct = q["dp"]
    else:
        son = float(s.iloc[-1]); onceki = float(s.iloc[-2])
        deg = son - onceki; pct = (deg / onceki * 100) if onceki else 0
    lo, hi = float(s.min()), float(s.max())
    konum = max(0, min(100, (son - lo) / (hi - lo) * 100)) if hi > lo else 50
    hac = float(d["vol"].iloc[-1]) if "vol" in d else 0.0
    pe, mc = temel(k)
    # Alarm her zaman USD fiyat uzerinden kontrol edilir (arka plan iscisi ile ayni)
    son_usd = q["c"] if (q and q["c"] > 0) else float(d["close"].iloc[-1])
    al = st.session_state["alarmlar"].get(k)
    tetik = bool(al) and ((son_usd >= al[1]) if al[0] == ">=" else (son_usd <= al[1]))
    rows.append(dict(k=k, ad=POPULER.get(k, k), son=son, deg=deg, pct=pct, lo=lo, hi=hi,
                     konum=konum, hac=hac, seri=s.tail(22), pe=pe, mc=mc, al=al, tetik=tetik))

# Siralama
if sirala == L["s_up"]:
    rows.sort(key=lambda r: r["pct"], reverse=True)
elif sirala == L["s_down"]:
    rows.sort(key=lambda r: r["pct"])
elif sirala == L["s_name"]:
    rows.sort(key=lambda r: r["ad"].lower())

# ---------- Portfoy ozeti ----------
if rows:
    ort = np.mean([r["pct"] for r in rows])
    en_iyi = max(rows, key=lambda r: r["pct"]); en_kotu = min(rows, key=lambda r: r["pct"])
    renk = "#4ade80" if ort >= 0 else "#f87171"
    k1, k2, k3, k4 = st.columns(4)
    k1.markdown(f'<div class="kpi"><small>{L["avg"]}</small><br><b style="color:{renk}">{ort:+.2f}%</b></div>', unsafe_allow_html=True)
    k2.markdown(f'<div class="kpi"><small>{L["best"]}</small><br><b>{en_iyi["ad"]} {en_iyi["pct"]:+.1f}%</b></div>', unsafe_allow_html=True)
    k3.markdown(f'<div class="kpi"><small>{L["worst"]}</small><br><b>{en_kotu["ad"]} {en_kotu["pct"]:+.1f}%</b></div>', unsafe_allow_html=True)
    k4.markdown(f'<div class="kpi"><small>{L["count"]}</small><br><b>{len(rows)}</b></div>', unsafe_allow_html=True)
    st.write("")

# ---------- Gorunum ----------
if gorunum == L["v_table"]:
    def alarm_metni(r):
        if not r["al"]: return ""
        y, h = r["al"]
        return (f"🎯 {L['a_reached']} {h:g}" if r["tetik"] else f"🔔 {y}{h:g}")
    df = pd.DataFrame([{
        L["c_sym"]: r["k"], L["c_name"]: r["ad"], L["c_price"]: r["son"],
        L["c_chg"]: r["pct"], L["pe"]: (round(r["pe"], 1) if r["pe"] else None),
        L["mcap"]: ("$" + buyuk(r["mc"]) if r["mc"] else "—"),
        L["c_vol"]: hacim(r["hac"]),
        L["c_low"]: r["lo"], L["c_high"]: r["hi"],
        L["c_alarm"]: alarm_metni(r),
        L["c_chart"]: list(r["seri"].values),
    } for r in rows])
    st.dataframe(df, hide_index=True, width="stretch", column_config={
        L["c_price"]: st.column_config.NumberColumn(format="%.2f " + sembol),
        L["c_chg"]: st.column_config.NumberColumn(format="%+.2f%%"),
        L["pe"]: st.column_config.NumberColumn(format="%.1f"),
        L["c_low"]: st.column_config.NumberColumn(format="%.2f"),
        L["c_high"]: st.column_config.NumberColumn(format="%.2f"),
        L["c_chart"]: st.column_config.LineChartColumn(width="medium"),
    })
else:
    for i in range(0, len(rows), 4):
        satir = st.columns(4)
        for j, r in enumerate(rows[i:i+4]):
            with satir[j]:
                renk = "#16a34a" if r["deg"] >= 0 else "#dc2626"
                sinif = "yesil" if r["deg"] >= 0 else "kirmizi"
                vurgu = ('style="border:2px solid #f59e0b;box-shadow:0 0 0 3px rgba(245,158,11,.25)"'
                         if r["tetik"] else "")
                if r["al"]:
                    y, h = r["al"]
                    alarm_satir = (f'<div class="w52" style="color:#f59e0b;font-weight:700">'
                                   f'🎯 {L["a_reached"]} ({h:g})</div>' if r["tetik"]
                                   else f'<div class="w52">🔔 {L["a_pending"]}: {y}{h:g}</div>')
                else:
                    alarm_satir = ""
                st.markdown(
                    f'<div class="wkart" {vurgu}><div class="wad">{r["ad"]} · {r["k"]}</div>'
                    f'<div class="wfiyat">{para(r["son"], sembol)}</div>'
                    f'<div class="wdeg {sinif}">{para(r["deg"], sembol)} ({r["pct"]:+.2f}%) · {L["today"]}</div>'
                    f'{sparkline(r["seri"], renk)}'
                    f'<div class="w52">{L["pe"]}: {round(r["pe"],1) if r["pe"] else "—"} · '
                    f'{L["mcap"]}: {("$"+buyuk(r["mc"])) if r["mc"] else "—"} · {L["vol"]}: {hacim(r["hac"])}</div>'
                    f'<div class="w52">{L["range52"]}: {para(r["lo"], sembol)} – {para(r["hi"], sembol)} · '
                    f'{L["inrange"].format(p=int(r["konum"]))}</div>'
                    f'{alarm_satir}</div>', unsafe_allow_html=True)
                if st.button("✕ " + L["remove"], key=f"rm_{r['k']}", width="stretch"):
                    cikar(r["k"]); st.rerun()

st.caption(f'{L["updated"]}: {datetime.now().strftime("%H:%M")} · ✅ {EMAIL} hesabına kaydedildi')
st.caption(L["src_live"] if FINN else L["src_off"])
st.divider()
st.caption(L["delayed_live"] if FINN else L["delayed"])
