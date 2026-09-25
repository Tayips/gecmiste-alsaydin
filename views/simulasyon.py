"""
SIMULASYON / DENEME HESABI (Paper Trading, cok dilli)
------------------------------------------------
Her kullaniciya 100.000 USD sanal nakit. Canli fiyatlarla al/sat yapar;
anlik kar/zarar, islem gecmisi ve herkese acik liderlik tablosu.
Muhasebe USD; gosterim secilen para biriminde. Egitim amaclidir; gercek para degildir.
"""
import streamlit as st
import yfinance as yf
import pandas as pd
import requests
from datetime import datetime, timezone
import db

# NOT: set_page_config, logo, dil secici yonlendirici app.py'dedir.
DILLER = {"Türkçe": "tr", "English": "en", "Deutsch": "de",
          "Русский": "ru", "Español": "es", "العربية": "ar"}
st.session_state.setdefault("dil_ad", "Türkçe")
lang = DILLER.get(st.session_state["dil_ad"], "tr")

T = {
 "tr": dict(title="🎮 Deneme Hesabı", login="Sanal hesabını kullanmak için Google ile giriş yap.",
   login_btn="Google ile giriş yap", logout="Çıkış yap", currency="Para birimi", refresh="🔄 Yenile",
   reset="♻️ Hesabı sıfırla", reset_confirm="Emin misin? Tüm sanal pozisyon ve geçmiş silinir, bakiye 100.000$ olur.",
   reset_yes="Evet, sıfırla", reset_done="✅ Hesap sıfırlandı.",
   intro="100.000$ sanal bakiye ile risksiz alım-satım pratiği yap. **Gerçek para değildir; eğitim amaçlıdır.**",
   cash="Nakit", invested="Yatırımdaki", total="Toplam değer", pl="Kâr / Zarar",
   buy_hdr="🟢 Al", stock="Hisse", other="Diğer (elle yaz)", code="Kod", code_ph="örn. GOOGL",
   mode="Nasıl alınsın?", by_shares="Adet ile", by_amount="Tutar ile", qty="Adet", amount="Tutar",
   buy="Satın al", e_pick="Bir hisse seç ya da yaz.", e_pos="Miktar 0'dan büyük olmalı.",
   e_balance="Yetersiz bakiye.", bought="alındı.", price_err="Fiyat alınamadı, tekrar dene.",
   holdings_hdr="📦 Pozisyonlarım", empty_pos="Henüz pozisyon yok. Yukarıdan ilk alımını yap.",
   col_price="Fiyat", col_val="Değer", col_pl="K/Z", sell="Sat", sell_qty="Satılacak adet",
   e_sell="Yetersiz adet.", sold="satıldı.", no_price="fiyat yok",
   hist_hdr="🧾 İşlem geçmişi", hist_empty="Henüz işlem yok.", buy_word="AL", sell_word="SAT",
   lead_hdr="🏆 Liderlik Tablosu", lead_rank="#", lead_user="Kullanıcı", lead_total="Toplam", lead_ret="Getiri",
   lead_empty="Henüz katılımcı yok.", shares="adet",
   foot="Sanal para ile eğitim amaçlıdır; yatırım tavsiyesi değildir. Fiyatlar gecikmeli olabilir."),
 "en": dict(title="🎮 Practice Account", login="Sign in with Google to use your virtual account.",
   login_btn="Sign in with Google", logout="Log out", currency="Currency", refresh="🔄 Refresh",
   reset="♻️ Reset account", reset_confirm="Are you sure? All virtual positions and history are erased, balance returns to $100,000.",
   reset_yes="Yes, reset", reset_done="✅ Account reset.",
   intro="Practice trading risk-free with a $100,000 virtual balance. **Not real money; for education.**",
   cash="Cash", invested="Invested", total="Total value", pl="Profit / Loss",
   buy_hdr="🟢 Buy", stock="Stock", other="Other (type)", code="Ticker", code_ph="e.g. GOOGL",
   mode="How to buy?", by_shares="By shares", by_amount="By amount", qty="Shares", amount="Amount",
   buy="Buy", e_pick="Pick or type a stock.", e_pos="Quantity must be greater than 0.",
   e_balance="Insufficient balance.", bought="bought.", price_err="Price unavailable, try again.",
   holdings_hdr="📦 My positions", empty_pos="No positions yet. Make your first buy above.",
   col_price="Price", col_val="Value", col_pl="P/L", sell="Sell", sell_qty="Shares to sell",
   e_sell="Not enough shares.", sold="sold.", no_price="no price",
   hist_hdr="🧾 Transaction history", hist_empty="No transactions yet.", buy_word="BUY", sell_word="SELL",
   lead_hdr="🏆 Leaderboard", lead_rank="#", lead_user="User", lead_total="Total", lead_ret="Return",
   lead_empty="No participants yet.", shares="shares",
   foot="Virtual money for education; not investment advice. Prices may be delayed."),
 "de": dict(title="🎮 Übungskonto", login="Melde dich mit Google an, um dein virtuelles Konto zu nutzen.",
   login_btn="Mit Google anmelden", logout="Abmelden", currency="Währung", refresh="🔄 Aktualisieren",
   reset="♻️ Konto zurücksetzen", reset_confirm="Sicher? Alle virtuellen Positionen und Historie werden gelöscht, Guthaben zurück auf 100.000$.",
   reset_yes="Ja, zurücksetzen", reset_done="✅ Konto zurückgesetzt.",
   intro="Übe risikofrei mit 100.000$ virtuellem Guthaben. **Kein echtes Geld; zu Lernzwecken.**",
   cash="Bargeld", invested="Investiert", total="Gesamtwert", pl="Gewinn / Verlust",
   buy_hdr="🟢 Kaufen", stock="Aktie", other="Andere (tippen)", code="Kürzel", code_ph="z. B. GOOGL",
   mode="Wie kaufen?", by_shares="Nach Anzahl", by_amount="Nach Betrag", qty="Anzahl", amount="Betrag",
   buy="Kaufen", e_pick="Aktie wählen oder tippen.", e_pos="Menge muss größer als 0 sein.",
   e_balance="Unzureichendes Guthaben.", bought="gekauft.", price_err="Kurs nicht verfügbar, erneut versuchen.",
   holdings_hdr="📦 Meine Positionen", empty_pos="Noch keine Positionen. Kaufe oben zuerst.",
   col_price="Kurs", col_val="Wert", col_pl="G/V", sell="Verkaufen", sell_qty="Zu verkaufen (Anzahl)",
   e_sell="Nicht genug Anteile.", sold="verkauft.", no_price="kein Kurs",
   hist_hdr="🧾 Verlauf", hist_empty="Noch keine Transaktionen.", buy_word="KAUF", sell_word="VERKAUF",
   lead_hdr="🏆 Bestenliste", lead_rank="#", lead_user="Nutzer", lead_total="Gesamt", lead_ret="Rendite",
   lead_empty="Noch keine Teilnehmer.", shares="Stück",
   foot="Virtuelles Geld zu Lernzwecken; keine Anlageberatung. Kurse evtl. verzögert."),
 "ru": dict(title="🎮 Тренировочный счёт", login="Войдите через Google, чтобы использовать виртуальный счёт.",
   login_btn="Войти через Google", logout="Выйти", currency="Валюта", refresh="🔄 Обновить",
   reset="♻️ Сбросить счёт", reset_confirm="Уверены? Все виртуальные позиции и история удаляются, баланс станет $100,000.",
   reset_yes="Да, сбросить", reset_done="✅ Счёт сброшен.",
   intro="Тренируйтесь без риска с виртуальным балансом $100,000. **Не реальные деньги; для обучения.**",
   cash="Наличные", invested="В активах", total="Итого", pl="Прибыль / Убыток",
   buy_hdr="🟢 Купить", stock="Акция", other="Другое (ввести)", code="Тикер", code_ph="напр. GOOGL",
   mode="Как купить?", by_shares="По количеству", by_amount="По сумме", qty="Кол-во", amount="Сумма",
   buy="Купить", e_pick="Выберите или введите акцию.", e_pos="Количество должно быть больше 0.",
   e_balance="Недостаточно средств.", bought="куплено.", price_err="Цена недоступна, повторите.",
   holdings_hdr="📦 Мои позиции", empty_pos="Пока нет позиций. Сделайте первую покупку выше.",
   col_price="Цена", col_val="Стоимость", col_pl="П/У", sell="Продать", sell_qty="Кол-во к продаже",
   e_sell="Недостаточно акций.", sold="продано.", no_price="нет цены",
   hist_hdr="🧾 История сделок", hist_empty="Пока нет сделок.", buy_word="ПОК", sell_word="ПРОД",
   lead_hdr="🏆 Таблица лидеров", lead_rank="#", lead_user="Пользователь", lead_total="Итого", lead_ret="Доход",
   lead_empty="Пока нет участников.", shares="шт",
   foot="Виртуальные деньги для обучения; не инвестсовет. Цены могут запаздывать."),
 "es": dict(title="🎮 Cuenta de práctica", login="Inicia sesión con Google para usar tu cuenta virtual.",
   login_btn="Iniciar sesión con Google", logout="Cerrar sesión", currency="Moneda", refresh="🔄 Actualizar",
   reset="♻️ Reiniciar cuenta", reset_confirm="¿Seguro? Se borran todas las posiciones e historial, el saldo vuelve a 100.000$.",
   reset_yes="Sí, reiniciar", reset_done="✅ Cuenta reiniciada.",
   intro="Practica sin riesgo con un saldo virtual de 100.000$. **No es dinero real; es educativo.**",
   cash="Efectivo", invested="Invertido", total="Valor total", pl="Ganancia / Pérdida",
   buy_hdr="🟢 Comprar", stock="Acción", other="Otra (escribir)", code="Símbolo", code_ph="p. ej. GOOGL",
   mode="¿Cómo comprar?", by_shares="Por cantidad", by_amount="Por importe", qty="Cantidad", amount="Importe",
   buy="Comprar", e_pick="Elige o escribe una acción.", e_pos="La cantidad debe ser mayor que 0.",
   e_balance="Saldo insuficiente.", bought="comprado.", price_err="Precio no disponible, reintenta.",
   holdings_hdr="📦 Mis posiciones", empty_pos="Aún no hay posiciones. Haz tu primera compra arriba.",
   col_price="Precio", col_val="Valor", col_pl="G/P", sell="Vender", sell_qty="Cantidad a vender",
   e_sell="No hay suficientes acciones.", sold="vendido.", no_price="sin precio",
   hist_hdr="🧾 Historial", hist_empty="Aún no hay operaciones.", buy_word="COMP", sell_word="VENTA",
   lead_hdr="🏆 Clasificación", lead_rank="#", lead_user="Usuario", lead_total="Total", lead_ret="Rendimiento",
   lead_empty="Aún no hay participantes.", shares="uds",
   foot="Dinero virtual educativo; no es asesoramiento. Los precios pueden retrasarse."),
 "ar": dict(title="🎮 حساب تجريبي", login="سجّل الدخول عبر Google لاستخدام حسابك الافتراضي.",
   login_btn="تسجيل الدخول عبر Google", logout="تسجيل الخروج", currency="العملة", refresh="🔄 تحديث",
   reset="♻️ إعادة تعيين الحساب", reset_confirm="متأكد؟ ستُحذف كل المراكز والسجل، ويعود الرصيد إلى 100,000$.",
   reset_yes="نعم، أعد التعيين", reset_done="✅ تمت إعادة التعيين.",
   intro="تدرّب دون مخاطرة برصيد افتراضي 100,000$. **ليست أموالًا حقيقية؛ لأغراض تعليمية.**",
   cash="النقد", invested="المستثمر", total="القيمة الإجمالية", pl="ربح / خسارة",
   buy_hdr="🟢 شراء", stock="السهم", other="أخرى (اكتب)", code="الرمز", code_ph="مثل GOOGL",
   mode="كيف تشتري؟", by_shares="بالكمية", by_amount="بالمبلغ", qty="الكمية", amount="المبلغ",
   buy="شراء", e_pick="اختر أو اكتب سهمًا.", e_pos="يجب أن تكون الكمية أكبر من 0.",
   e_balance="الرصيد غير كافٍ.", bought="تم الشراء.", price_err="السعر غير متاح، حاول مجددًا.",
   holdings_hdr="📦 مراكزي", empty_pos="لا مراكز بعد. نفّذ أول عملية شراء بالأعلى.",
   col_price="السعر", col_val="القيمة", col_pl="ر/خ", sell="بيع", sell_qty="الكمية للبيع",
   e_sell="لا توجد أسهم كافية.", sold="تم البيع.", no_price="لا سعر",
   hist_hdr="🧾 سجل العمليات", hist_empty="لا عمليات بعد.", buy_word="شراء", sell_word="بيع",
   lead_hdr="🏆 المتصدرون", lead_rank="#", lead_user="المستخدم", lead_total="الإجمالي", lead_ret="العائد",
   lead_empty="لا مشاركين بعد.", shares="سهم",
   foot="أموال افتراضية للتعليم؛ ليست نصيحة استثمارية. قد تتأخر الأسعار."),
}
L = T[lang]

# ---------- Giris ----------
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
        c = r.json().get("c")
        return float(c) if c else None
    except Exception:
        return None


@st.cache_data(ttl=300)
def yahoo_fiyat(ticker):
    try:
        df = yf.download(ticker, period="5d", auto_adjust=True, progress=False)
        if df.empty:
            return None
        c = df["Close"]
        if isinstance(c, pd.DataFrame):
            c = c.iloc[:, 0]
        return float(c.dropna().iloc[-1])
    except Exception:
        return None


def fiyat(ticker):
    f = finnhub_fiyat(ticker, FINN)
    if f and f > 0:
        return f
    return yahoo_fiyat(ticker)


@st.cache_data(ttl=3600)
def kur(sembol):
    """1 USD kac 'sembol' eder."""
    if sembol == "$":
        return 1.0
    try:
        if sembol == "€":
            df = yf.download("EURUSD=X", period="5d", auto_adjust=True, progress=False)
            c = df["Close"]; c = c.iloc[:, 0] if isinstance(c, pd.DataFrame) else c
            return 1.0 / float(c.dropna().iloc[-1])
        if sembol == "₺":
            df = yf.download("USDTRY=X", period="5d", auto_adjust=True, progress=False)
            c = df["Close"]; c = c.iloc[:, 0] if isinstance(c, pd.DataFrame) else c
            return float(c.dropna().iloc[-1])
    except Exception:
        return 1.0
    return 1.0


def para(x, s):
    return f"{x:,.2f}".replace(",", "@").replace(".", ",").replace("@", ".") + " " + s


def zaman(dt):
    if not isinstance(dt, datetime):
        return ""
    try:
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        s = int((datetime.now(timezone.utc) - dt).total_seconds())
        if s < 3600: return f"{max(1, s//60)} dk"
        if s < 86400: return f"{s//3600} sa"
        return f"{s//86400} g"
    except Exception:
        return ""


# ---------- Kenar cubugu ----------
with st.sidebar:
    st.caption(f"👤 {EMAIL}")
    if st.button(L["logout"], width="stretch"):
        st.logout()
    st.divider()
    sembol = st.selectbox(L["currency"], ["$", "€", "₺"])
    if st.button(L["refresh"], width="stretch"):
        st.cache_data.clear(); st.rerun()
    with st.expander(L["reset"]):
        st.caption(L["reset_confirm"])
        if st.button(L["reset_yes"], width="stretch"):
            db.sim_sifirla(EMAIL); st.success(L["reset_done"]); st.rerun()

k = kur(sembol)

st.title(L["title"])
st.caption(L["intro"])

# ---------- Hesap + pozisyonlar ----------
hesap = db.sim_hesap_getir(EMAIL)
nakit_usd = hesap["nakit"]; baslangic_usd = hesap["baslangic"]
pozisyonlar = db.sim_pozisyonlar_getir(EMAIL)

fiyatlar = {p["ticker"]: fiyat(p["ticker"]) for p in pozisyonlar}
yatirim_usd = sum((fiyatlar[p["ticker"]] or 0) * p["adet"] for p in pozisyonlar)
toplam_usd = nakit_usd + yatirim_usd
getiri_pct = (toplam_usd - baslangic_usd) / baslangic_usd * 100 if baslangic_usd else 0

# ---------- Ozet KPI ----------
m1, m2, m3, m4 = st.columns(4)
m1.metric(L["total"], para(toplam_usd * k, sembol))
m2.metric(L["cash"], para(nakit_usd * k, sembol))
m3.metric(L["invested"], para(yatirim_usd * k, sembol))
m4.metric(L["pl"], para((toplam_usd - baslangic_usd) * k, sembol), f"{getiri_pct:+.2f}%")
st.divider()

# ---------- Al ----------
with st.expander(L["buy_hdr"], expanded=not pozisyonlar):
    with st.form("al", clear_on_submit=True):
        secenekler = [f"{ad} ({tk})" for tk, ad in ADLAR.items()]
        secim = st.selectbox(L["stock"], secenekler + [L["other"]])
        elle = st.text_input(L["code"], placeholder=L["code_ph"])
        mod = st.radio(L["mode"], [L["by_shares"], L["by_amount"]], horizontal=True)
        c = st.columns(2)
        adet_in = c[0].number_input(L["qty"], min_value=0.0, step=1.0)
        tutar_in = c[1].number_input(L["amount"] + f" ({sembol})", min_value=0.0, step=100.0)
        if st.form_submit_button(L["buy"], type="primary"):
            ticker = (elle.strip().upper() if secim == L["other"]
                      else secim.split("(")[-1].rstrip(")").strip().upper())
            if not ticker:
                st.warning(L["e_pick"])
            else:
                f_usd = fiyat(ticker)
                if not f_usd:
                    st.error(L["price_err"])
                else:
                    if mod == L["by_shares"]:
                        adet = adet_in
                    else:
                        adet = (tutar_in / k) / f_usd if f_usd else 0  # tutar secilen para birimi -> USD -> adet
                    if adet <= 0:
                        st.warning(L["e_pos"])
                    else:
                        ok, hata = db.sim_al(EMAIL, ticker, adet, f_usd)
                        if ok:
                            st.success(f"✅ {adet:g} {ticker} {L['bought']}")
                            st.rerun()
                        elif hata == "bakiye":
                            st.error(L["e_balance"])

# ---------- Pozisyonlar ----------
st.subheader(L["holdings_hdr"])
if not pozisyonlar:
    st.info(L["empty_pos"])
else:
    for p in pozisyonlar:
        tk = p["ticker"]; f_usd = fiyatlar.get(tk)
        ad = ADLAR.get(tk, tk)
        with st.container(border=True):
            c = st.columns([3, 2, 2, 3])
            c[0].markdown(f"**{ad}**  \n`{tk}` · {p['adet']:g} {L['shares']}")
            if not f_usd:
                c[1].markdown(f"_{L['no_price']}_"); c[2].markdown("—")
            else:
                deger = f_usd * p["adet"] * k
                maliyet = p["ort_maliyet"] * p["adet"] * k
                kz = deger - maliyet; kz_pct = (kz / maliyet * 100) if maliyet else 0
                c[1].markdown(f"{L['col_price']}  \n**{para(f_usd * k, sembol)}**")
                kzr = "#16a34a" if kz >= 0 else "#dc2626"
                c[2].markdown(f"{L['col_val']}: **{para(deger, sembol)}**  \n"
                              f"<span style='color:{kzr};font-weight:700'>{para(kz, sembol)} ({kz_pct:+.1f}%)</span>",
                              unsafe_allow_html=True)
            with c[3]:
                sc = st.columns([2, 1])
                sat_adet = sc[0].number_input(L["sell_qty"], min_value=0.0, max_value=float(p["adet"]),
                                              value=float(p["adet"]), step=1.0, key=f"sat_{tk}")
                sc[1].markdown("<div style='height:28px'></div>", unsafe_allow_html=True)
                if sc[1].button(L["sell"], key=f"satbtn_{tk}", width="stretch"):
                    f_now = fiyat(tk)
                    if not f_now:
                        st.error(L["price_err"])
                    elif sat_adet <= 0:
                        st.warning(L["e_pos"])
                    else:
                        ok, hata = db.sim_sat(EMAIL, tk, sat_adet, f_now)
                        if ok:
                            st.success(f"✅ {sat_adet:g} {tk} {L['sold']}"); st.rerun()
                        elif hata == "adet":
                            st.error(L["e_sell"])

# ---------- Islem gecmisi ----------
with st.expander(L["hist_hdr"]):
    islemler = db.sim_islemler_getir(EMAIL, limit=60)
    if not islemler:
        st.caption(L["hist_empty"])
    else:
        df = pd.DataFrame([{
            "": (("🟢 " + L["buy_word"]) if i["tur"] == "AL" else ("🔴 " + L["sell_word"])),
            L["stock"]: i["ticker"], L["qty"]: f'{i["adet"]:g}',
            L["col_price"]: para(i["fiyat"] * k, sembol),
            L["amount"]: para(i["tutar"] * k, sembol),
            "🕐": zaman(i["olusturuldu"]),
        } for i in islemler])
        st.dataframe(df, hide_index=True, width="stretch")

# ---------- Liderlik tablosu ----------
st.divider()
st.subheader(L["lead_hdr"])
try:
    hesaplar, pozlar = db.sim_liderlik_veri()
except Exception:
    hesaplar, pozlar = [], []

if not hesaplar:
    st.caption(L["lead_empty"])
else:
    # Tum tickerlar icin fiyatlari topla (cache'li)
    tum_tk = {pz["ticker"] for pz in pozlar}
    fyt = {t: (fiyat(t) or 0) for t in tum_tk}
    poz_by_email = {}
    for pz in pozlar:
        poz_by_email.setdefault(pz["email"], []).append(pz)
    tablo = []
    for h in hesaplar:
        yat = sum(fyt.get(pz["ticker"], 0) * pz["adet"] for pz in poz_by_email.get(h["email"], []))
        toplam = h["nakit"] + yat
        ret = (toplam - h["baslangic"]) / h["baslangic"] * 100 if h["baslangic"] else 0
        tablo.append(dict(ad=h["ad"], toplam=toplam, ret=ret))
    tablo.sort(key=lambda x: x["ret"], reverse=True)
    df = pd.DataFrame([{
        L["lead_rank"]: i + 1,
        L["lead_user"]: t["ad"],
        L["lead_total"]: para(t["toplam"] * k, sembol),
        L["lead_ret"]: f'{t["ret"]:+.2f}%',
    } for i, t in enumerate(tablo[:20])])
    st.dataframe(df, hide_index=True, width="stretch")

st.divider()
st.caption("⚠️ " + L["foot"])
