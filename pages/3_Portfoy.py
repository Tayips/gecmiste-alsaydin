"""
PORTFOYUM / MY PORTFOLIO (cok dilli)
------------------------------------------------
Sahip oldugun hisseleri (adet + ortalama maliyet) gir;
canli fiyatla anlik kar/zarar, toplam deger ve dagilim gor.
Dil, ana sayfada secilen dille (st.session_state['dil_ad']) senkrondur.
"""
import streamlit as st
import yfinance as yf
import pandas as pd
import plotly.express as px
import requests
from datetime import datetime
import db

try:
    st.set_page_config(page_title="Portföyüm — WhatIfInvest", page_icon="assets/favicon.png", layout="wide")
except Exception:
    st.set_page_config(page_title="Portföyüm — WhatIfInvest", page_icon="💼", layout="wide")
try:
    st.logo("assets/logo_lockup.png", size="large", icon_image="assets/favicon.png")
except Exception:
    pass

# ---------- Dil ----------
DILLER = {"Türkçe": "tr", "English": "en", "Deutsch": "de",
          "Русский": "ru", "Español": "es", "العربية": "ar"}
st.session_state.setdefault("dil_ad", "Türkçe")
lang = DILLER.get(st.session_state["dil_ad"], "tr")

T = {
 "tr": dict(title="💼 Portföyüm", login="Portföyünü kaydedebilmek için önce Google ile giriş yapmalısın.",
   login_btn="Google ile giriş yap", logout="Çıkış yap", currency="Para birimi", refresh="🔄 Yenile",
   intro="Sahip olduğun hisseleri gir; canlı fiyatla anlık kâr/zararını gör. Veriler Google hesabına bağlı olarak kaydedilir.",
   add_hdr="➕ Yeni pozisyon ekle", stock="Hisse", other="Diğer (elle yaz)",
   code="Kod (Diğer seçtiysen)", code_ph="örn. GOOGL", qty="Adet", cost="Ort. maliyet (USD)",
   cost_help="Bu hisse için ortalama alış fiyatın (USD).", add="Ekle",
   w_pick="Bir hisse kodu seç ya da yaz.", w_pos="Adet ve maliyet 0'dan büyük olmalı.",
   added="eklendi.", add_err="Eklenemedi: ", read_err="Portföy okunamadı: ",
   empty="Henüz pozisyon yok. Yukarıdan ilk hisseni ekle.", m_value="Toplam değer",
   m_cost="Toplam maliyet", m_pl="Kâr / Zarar", m_count="Pozisyon sayısı",
   pie="Portföy dağılımı (güncel değere göre)", shares="adet", no_price="_fiyat alınamadı_",
   price="Fiyat", value="Değer", pl="K/Z", del_help="Bu pozisyonu sil", del_err="Silinemedi: ",
   updated="Son güncelleme", live="🟢 Canlı fiyat: Finnhub", off="Fiyatlar Yahoo (gecikmeli)",
   foot="maliyeti USD olarak girersin, gösterim {s}. Yatırım tavsiyesi değildir."),
 "en": dict(title="💼 My Portfolio", login="Sign in with Google first to save your portfolio.",
   login_btn="Sign in with Google", logout="Log out", currency="Currency", refresh="🔄 Refresh",
   intro="Add the stocks you own; see live profit/loss with current prices. Data is saved to your Google account.",
   add_hdr="➕ Add new position", stock="Stock", other="Other (type manually)",
   code="Ticker (if Other)", code_ph="e.g. GOOGL", qty="Shares", cost="Avg cost (USD)",
   cost_help="Your average buy price for this stock (USD).", add="Add",
   w_pick="Pick or type a ticker.", w_pos="Shares and cost must be greater than 0.",
   added="added.", add_err="Could not add: ", read_err="Could not load portfolio: ",
   empty="No positions yet. Add your first stock above.", m_value="Total value",
   m_cost="Total cost", m_pl="Profit / Loss", m_count="Positions",
   pie="Portfolio allocation (by current value)", shares="shares", no_price="_price unavailable_",
   price="Price", value="Value", pl="P/L", del_help="Delete this position", del_err="Could not delete: ",
   updated="Last update", live="🟢 Live price: Finnhub", off="Prices from Yahoo (delayed)",
   foot="enter cost in USD, shown in {s}. Not investment advice."),
 "de": dict(title="💼 Mein Portfolio", login="Melde dich zuerst mit Google an, um dein Portfolio zu speichern.",
   login_btn="Mit Google anmelden", logout="Abmelden", currency="Währung", refresh="🔄 Aktualisieren",
   intro="Füge deine Aktien hinzu; sieh Gewinn/Verlust mit aktuellen Kursen. Daten werden in deinem Google-Konto gespeichert.",
   add_hdr="➕ Neue Position hinzufügen", stock="Aktie", other="Andere (manuell)",
   code="Kürzel (falls Andere)", code_ph="z. B. GOOGL", qty="Anzahl", cost="Ø Kaufpreis (USD)",
   cost_help="Dein durchschnittlicher Kaufpreis (USD).", add="Hinzufügen",
   w_pick="Wähle oder tippe ein Kürzel.", w_pos="Anzahl und Kosten müssen größer als 0 sein.",
   added="hinzugefügt.", add_err="Konnte nicht hinzufügen: ", read_err="Portfolio nicht ladbar: ",
   empty="Noch keine Positionen. Füge oben deine erste Aktie hinzu.", m_value="Gesamtwert",
   m_cost="Gesamtkosten", m_pl="Gewinn / Verlust", m_count="Positionen",
   pie="Portfolio-Aufteilung (nach aktuellem Wert)", shares="Stück", no_price="_Kurs nicht verfügbar_",
   price="Kurs", value="Wert", pl="G/V", del_help="Diese Position löschen", del_err="Konnte nicht löschen: ",
   updated="Letzte Aktualisierung", live="🟢 Live-Kurs: Finnhub", off="Kurse von Yahoo (verzögert)",
   foot="Kosten in USD eingeben, Anzeige in {s}. Keine Anlageberatung."),
 "ru": dict(title="💼 Мой портфель", login="Сначала войдите через Google, чтобы сохранить портфель.",
   login_btn="Войти через Google", logout="Выйти", currency="Валюта", refresh="🔄 Обновить",
   intro="Добавьте свои акции; смотрите прибыль/убыток по текущим ценам. Данные сохраняются в вашем аккаунте Google.",
   add_hdr="➕ Добавить позицию", stock="Акция", other="Другое (вручную)",
   code="Тикер (если Другое)", code_ph="напр. GOOGL", qty="Кол-во", cost="Ср. цена (USD)",
   cost_help="Ваша средняя цена покупки (USD).", add="Добавить",
   w_pick="Выберите или введите тикер.", w_pos="Кол-во и цена должны быть больше 0.",
   added="добавлено.", add_err="Не удалось добавить: ", read_err="Не удалось загрузить портфель: ",
   empty="Пока нет позиций. Добавьте первую акцию выше.", m_value="Общая стоимость",
   m_cost="Общие затраты", m_pl="Прибыль / Убыток", m_count="Позиции",
   pie="Распределение портфеля (по текущей стоимости)", shares="шт", no_price="_цена недоступна_",
   price="Цена", value="Стоимость", pl="П/У", del_help="Удалить позицию", del_err="Не удалось удалить: ",
   updated="Обновлено", live="🟢 Живая цена: Finnhub", off="Цены Yahoo (с задержкой)",
   foot="стоимость вводится в USD, показ в {s}. Не инвестсовет."),
 "es": dict(title="💼 Mi cartera", login="Inicia sesión con Google para guardar tu cartera.",
   login_btn="Iniciar sesión con Google", logout="Cerrar sesión", currency="Moneda", refresh="🔄 Actualizar",
   intro="Añade tus acciones; mira ganancia/pérdida con precios actuales. Los datos se guardan en tu cuenta de Google.",
   add_hdr="➕ Añadir posición", stock="Acción", other="Otra (escribir)",
   code="Símbolo (si Otra)", code_ph="p. ej. GOOGL", qty="Cantidad", cost="Coste medio (USD)",
   cost_help="Tu precio medio de compra (USD).", add="Añadir",
   w_pick="Elige o escribe un símbolo.", w_pos="Cantidad y coste deben ser mayores que 0.",
   added="añadido.", add_err="No se pudo añadir: ", read_err="No se pudo cargar la cartera: ",
   empty="Aún no hay posiciones. Añade tu primera acción arriba.", m_value="Valor total",
   m_cost="Coste total", m_pl="Ganancia / Pérdida", m_count="Posiciones",
   pie="Distribución de cartera (por valor actual)", shares="uds", no_price="_precio no disponible_",
   price="Precio", value="Valor", pl="G/P", del_help="Eliminar esta posición", del_err="No se pudo eliminar: ",
   updated="Última actualización", live="🟢 Precio en vivo: Finnhub", off="Precios de Yahoo (con retraso)",
   foot="coste en USD, mostrado en {s}. No es asesoramiento."),
 "ar": dict(title="💼 محفظتي", login="سجّل الدخول عبر Google أولاً لحفظ محفظتك.",
   login_btn="تسجيل الدخول عبر Google", logout="تسجيل الخروج", currency="العملة", refresh="🔄 تحديث",
   intro="أضف أسهمك؛ شاهد الربح/الخسارة بالأسعار الحية. تُحفظ البيانات في حساب Google الخاص بك.",
   add_hdr="➕ إضافة مركز جديد", stock="السهم", other="أخرى (اكتب يدويًا)",
   code="الرمز (إذا أخرى)", code_ph="مثل GOOGL", qty="الكمية", cost="متوسط التكلفة (USD)",
   cost_help="متوسط سعر شرائك (USD).", add="إضافة",
   w_pick="اختر أو اكتب رمزًا.", w_pos="يجب أن تكون الكمية والتكلفة أكبر من 0.",
   added="أُضيف.", add_err="تعذّرت الإضافة: ", read_err="تعذّر تحميل المحفظة: ",
   empty="لا مراكز بعد. أضف أول سهم بالأعلى.", m_value="القيمة الإجمالية",
   m_cost="التكلفة الإجمالية", m_pl="ربح / خسارة", m_count="المراكز",
   pie="توزيع المحفظة (حسب القيمة الحالية)", shares="سهم", no_price="_السعر غير متاح_",
   price="السعر", value="القيمة", pl="ر/خ", del_help="حذف هذا المركز", del_err="تعذّر الحذف: ",
   updated="آخر تحديث", live="🟢 سعر حي: Finnhub", off="أسعار Yahoo (متأخرة)",
   foot="أدخل التكلفة بالدولار، والعرض بـ {s}. ليست نصيحة استثمارية."),
}
L = T[lang]

# ---------- Giris zorunlu ----------
_u = getattr(st, "user", None)
if not _u or not _u.is_logged_in:
    st.title(L["title"])
    st.info(L["login"])
    if st.button(L["login_btn"], type="primary"):
        st.login()
    st.stop()
EMAIL = st.user.email

ADLAR = {
 "AAPL":"Apple","MSFT":"Microsoft","NVDA":"NVIDIA","AMZN":"Amazon","GOOGL":"Alphabet (Google)",
 "META":"Meta","TSLA":"Tesla","JPM":"JPMorgan","V":"Visa","MA":"Mastercard","KO":"Coca-Cola",
 "PEP":"PepsiCo","DIS":"Disney","NFLX":"Netflix","AMD":"AMD","INTC":"Intel","ORCL":"Oracle",
 "ADBE":"Adobe","CRM":"Salesforce","NKE":"Nike","MCD":"McDonald's","SBUX":"Starbucks",
 "BA":"Boeing","XOM":"Exxon","PFE":"Pfizer","BAC":"Bank of America","WMT":"Walmart",
 "COST":"Costco","HD":"Home Depot","UBER":"Uber","PLTR":"Palantir","COIN":"Coinbase",
 "SPY":"S&P 500","QQQ":"Nasdaq 100","BTC-USD":"Bitcoin","ETH-USD":"Ethereum","GLD":"Gold",
 "F":"Ford","GM":"General Motors","RIVN":"Rivian","NIO":"NIO",
}

try:
    FINN = st.secrets.get("FINNHUB_KEY", "")
except Exception:
    FINN = ""


@st.cache_data(ttl=60)
def finnhub_fiyat(ticker, key):
    if not key:
        return None
    try:
        r = requests.get("https://finnhub.io/api/v1/quote",
                         params={"symbol": ticker, "token": key}, timeout=6)
        j = r.json()
        if j.get("c"):
            return float(j["c"])
    except Exception:
        return None
    return None


@st.cache_data(ttl=300)
def yahoo_fiyat(ticker):
    try:
        df = yf.download(ticker, period="5d", auto_adjust=True, progress=False)
        if df.empty:
            return None
        close = df["Close"]
        if isinstance(close, pd.DataFrame):
            close = close.iloc[:, 0]
        return float(close.dropna().iloc[-1])
    except Exception:
        return None


def guncel_fiyat(ticker):
    f = finnhub_fiyat(ticker, FINN)
    if f and f > 0:
        return f
    return yahoo_fiyat(ticker)


@st.cache_data(ttl=3600)
def kur(sembol):
    if sembol == "$":
        return 1.0
    try:
        if sembol == "€":
            df = yf.download("EURUSD=X", period="5d", auto_adjust=True, progress=False)
            c = df["Close"]
            if isinstance(c, pd.DataFrame):
                c = c.iloc[:, 0]
            return 1.0 / float(c.dropna().iloc[-1])
        if sembol == "₺":
            df = yf.download("USDTRY=X", period="5d", auto_adjust=True, progress=False)
            c = df["Close"]
            if isinstance(c, pd.DataFrame):
                c = c.iloc[:, 0]
            return float(c.dropna().iloc[-1])
    except Exception:
        return 1.0
    return 1.0


def para(x, s="$"):
    return f"{x:,.2f}".replace(",", "@").replace(".", ",").replace("@", ".") + " " + s


with st.sidebar:
    st.caption(f"👤 {EMAIL}")
    if st.button(L["logout"], width="stretch"):
        st.logout()
    st.divider()
    sembol = st.selectbox(L["currency"], ["$", "€", "₺"])
    if st.button(L["refresh"], width="stretch"):
        st.cache_data.clear()
        st.rerun()

st.title(L["title"])
st.caption(L["intro"])

with st.form("ekle", clear_on_submit=True):
    st.markdown(f"**{L['add_hdr']}**")
    c = st.columns([2, 1, 1, 1])
    secenekler = [f"{ad} ({tk})" for tk, ad in ADLAR.items()]
    secim = c[0].selectbox(L["stock"], secenekler + [L["other"]])
    elle = c[0].text_input(L["code"], placeholder=L["code_ph"])
    adet = c[1].number_input(L["qty"], min_value=0.0, step=1.0)
    maliyet = c[2].number_input(L["cost"], min_value=0.0, step=1.0, help=L["cost_help"])
    c[3].markdown("<div style='height:28px'></div>", unsafe_allow_html=True)
    ekle = c[3].form_submit_button(L["add"], type="primary", width="stretch")
    if ekle:
        if secim == L["other"]:
            ticker = elle.strip().upper()
        else:
            ticker = secim.split("(")[-1].rstrip(")").strip().upper()
        if not ticker:
            st.warning(L["w_pick"])
        elif adet <= 0 or maliyet <= 0:
            st.warning(L["w_pos"])
        else:
            try:
                db.portfoy_ekle(EMAIL, ticker, adet, maliyet)
                st.success(f"✅ {ticker} {L['added']}")
                st.rerun()
            except Exception as e:
                st.error(L["add_err"] + str(e))

try:
    pozisyonlar = db.portfoy_getir(EMAIL)
except Exception as e:
    st.error(L["read_err"] + str(e))
    st.stop()

if not pozisyonlar:
    st.info(L["empty"])
    st.stop()

k = kur(sembol)

satirlar = []
toplam_deger = toplam_maliyet = 0.0
for p in pozisyonlar:
    fiyat_usd = guncel_fiyat(p["ticker"])
    if fiyat_usd is None:
        satirlar.append(dict(p=p, fiyat=None))
        continue
    deger = fiyat_usd * p["adet"] * k
    maliyet_top = p["maliyet"] * p["adet"] * k
    kz = deger - maliyet_top
    kz_pct = (kz / maliyet_top * 100) if maliyet_top else 0.0
    toplam_deger += deger
    toplam_maliyet += maliyet_top
    satirlar.append(dict(p=p, fiyat=fiyat_usd * k, deger=deger,
                         maliyet_top=maliyet_top, kz=kz, kz_pct=kz_pct))

toplam_kz = toplam_deger - toplam_maliyet
toplam_kz_pct = (toplam_kz / toplam_maliyet * 100) if toplam_maliyet else 0.0

m1, m2, m3, m4 = st.columns(4)
m1.metric(L["m_value"], para(toplam_deger, sembol))
m2.metric(L["m_cost"], para(toplam_maliyet, sembol))
m3.metric(L["m_pl"], para(toplam_kz, sembol), f"{toplam_kz_pct:+.2f}%")
m4.metric(L["m_count"], str(len(pozisyonlar)))
st.divider()

pasta = [(ADLAR.get(s["p"]["ticker"], s["p"]["ticker"]), s["deger"])
         for s in satirlar if s["fiyat"] is not None and s["deger"] > 0]
if pasta:
    isimler = [x[0] for x in pasta]
    degerler = [x[1] for x in pasta]
    fig = px.pie(names=isimler, values=degerler, hole=0.45)
    fig.update_traces(textposition="inside", textinfo="percent+label",
                      hovertemplate="%{label}<br>%{value:,.2f} " + sembol +
                                    "<br>%{percent}<extra></extra>")
    fig.update_layout(showlegend=True, height=380,
                      margin=dict(t=30, b=10, l=10, r=10), title=L["pie"])
    st.plotly_chart(fig, width="stretch")
    st.divider()

for s in satirlar:
    p = s["p"]
    ad = ADLAR.get(p["ticker"], p["ticker"])
    c = st.columns([3, 2, 2, 2, 1])
    c[0].markdown(f"**{ad}**  \n`{p['ticker']}` · {p['adet']:g} {L['shares']}")
    if s["fiyat"] is None:
        c[1].markdown(L["no_price"])
        c[2].markdown("—")
        c[3].markdown("—")
    else:
        c[1].markdown(f"{L['price']}  \n**{para(s['fiyat'], sembol)}**")
        c[2].markdown(f"{L['value']}  \n**{para(s['deger'], sembol)}**")
        kzr = "#16a34a" if s["kz"] >= 0 else "#dc2626"
        c[3].markdown(f"{L['pl']}  \n<span style='color:{kzr};font-weight:700'>"
                      f"{para(s['kz'], sembol)} ({s['kz_pct']:+.1f}%)</span>",
                      unsafe_allow_html=True)
    c[4].markdown("<div style='height:6px'></div>", unsafe_allow_html=True)
    if c[4].button("🗑️", key=f"sil_{p['id']}", help=L["del_help"]):
        try:
            db.portfoy_sil(p["id"])
            st.rerun()
        except Exception as e:
            st.error(L["del_err"] + str(e))
    st.divider()

st.caption(f'{L["updated"]}: {datetime.now().strftime("%H:%M")} · '
           f'{L["live"] if FINN else L["off"]} · {L["foot"].format(s=sembol)}')
