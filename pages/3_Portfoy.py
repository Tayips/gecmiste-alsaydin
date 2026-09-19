"""
PORTFOYUM / MY PORTFOLIO
------------------------------------------------
Sahip oldugun hisseleri (adet + ortalama maliyet) gir;
canli fiyatla anlik kar/zarar, toplam deger ve dagilim gor.

Veri, Google hesabina bagli olarak veritabaninda saklanir.
Canli fiyat: Finnhub · gecmis/yedek: Yahoo. Egitim amaclidir; yatirim tavsiyesi degildir.
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
    st.logo("assets/logo_lockup.png", icon_image="assets/favicon.png")
except Exception:
    pass

# ---------- Giris zorunlu ----------
_u = getattr(st, "user", None)
if not _u or not _u.is_logged_in:
    st.title("💼 Portföyüm")
    st.info("Portföyünü kaydedebilmek için önce Google ile giriş yapmalısın.")
    if st.button("Google ile giriş yap", type="primary"):
        st.login()
    st.stop()
EMAIL = st.user.email

# ---------- Sirket adlari (Takip sayfasindakiyle ayni cekirdek) ----------
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
    """Finnhub'dan canli fiyat (USD). Basarisizsa None."""
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
    """Yahoo son kapanis (USD). Finnhub yedegi. Basarisizsa None."""
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
    """Once Finnhub (canli), olmazsa Yahoo (gecikmeli)."""
    f = finnhub_fiyat(ticker, FINN)
    if f and f > 0:
        return f
    return yahoo_fiyat(ticker)


@st.cache_data(ttl=3600)
def kur(sembol):
    """1 USD kac 'sembol' eder (fiyatlar USD -> sembol icin carpan)."""
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


# ---------- Kenar cubugu ----------
with st.sidebar:
    st.caption(f"👤 {EMAIL}")
    if st.button("Çıkış yap", width="stretch"):
        st.logout()
    st.divider()
    sembol = st.selectbox("Para birimi", ["$", "€", "₺"])
    if st.button("🔄 Yenile", width="stretch"):
        st.cache_data.clear()
        st.rerun()

st.title("💼 Portföyüm")
st.caption("Sahip olduğun hisseleri gir; canlı fiyatla anlık kâr/zararını gör. "
           "Veriler Google hesabına bağlı olarak kaydedilir.")

# ---------- Yeni pozisyon ekleme formu ----------
with st.form("ekle", clear_on_submit=True):
    st.markdown("**➕ Yeni pozisyon ekle**")
    c = st.columns([2, 1, 1, 1])
    secenekler = [f"{ad} ({tk})" for tk, ad in ADLAR.items()]
    secim = c[0].selectbox("Hisse", secenekler + ["Diğer (elle yaz)"])
    elle = c[0].text_input("Kod (Diğer seçtiysen)", placeholder="örn. GOOGL")
    adet = c[1].number_input("Adet", min_value=0.0, step=1.0)
    maliyet = c[2].number_input("Ort. maliyet (USD)", min_value=0.0, step=1.0,
                                help="Bu hisse için ortalama alış fiyatın (USD).")
    c[3].markdown("<div style='height:28px'></div>", unsafe_allow_html=True)
    ekle = c[3].form_submit_button("Ekle", type="primary", width="stretch")
    if ekle:
        if secim == "Diğer (elle yaz)":
            ticker = elle.strip().upper()
        else:
            ticker = secim.split("(")[-1].rstrip(")").strip().upper()
        if not ticker:
            st.warning("Bir hisse kodu seç ya da yaz.")
        elif adet <= 0 or maliyet <= 0:
            st.warning("Adet ve maliyet 0'dan büyük olmalı.")
        else:
            try:
                db.portfoy_ekle(EMAIL, ticker, adet, maliyet)
                st.success(f"✅ {ticker} eklendi.")
                st.rerun()
            except Exception as e:
                st.error("Eklenemedi: " + str(e))

# ---------- Portfoyu yukle ----------
try:
    pozisyonlar = db.portfoy_getir(EMAIL)
except Exception as e:
    st.error("Portföy okunamadı: " + str(e))
    st.stop()

if not pozisyonlar:
    st.info("Henüz pozisyon yok. Yukarıdan ilk hisseni ekle.")
    st.stop()

k = kur(sembol)  # USD -> sembol carpani

# ---------- Hesaplama ----------
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

# ---------- Ozet KPI ----------
renk = "#16a34a" if toplam_kz >= 0 else "#dc2626"
m1, m2, m3, m4 = st.columns(4)
m1.metric("Toplam değer", para(toplam_deger, sembol))
m2.metric("Toplam maliyet", para(toplam_maliyet, sembol))
m3.metric("Kâr / Zarar", para(toplam_kz, sembol), f"{toplam_kz_pct:+.2f}%")
m4.metric("Pozisyon sayısı", str(len(pozisyonlar)))
st.divider()

# ---------- Dagilim pastasi ----------
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
                      margin=dict(t=30, b=10, l=10, r=10),
                      title="Portföy dağılımı (güncel değere göre)")
    st.plotly_chart(fig, width="stretch")
    st.divider()

# ---------- Pozisyon karti listesi ----------
for s in satirlar:
    p = s["p"]
    ad = ADLAR.get(p["ticker"], p["ticker"])
    c = st.columns([3, 2, 2, 2, 1])
    c[0].markdown(f"**{ad}**  \n`{p['ticker']}` · {p['adet']:g} adet")
    if s["fiyat"] is None:
        c[1].markdown("_fiyat alınamadı_")
        c[2].markdown("—")
        c[3].markdown("—")
    else:
        c[1].markdown(f"Fiyat  \n**{para(s['fiyat'], sembol)}**")
        c[2].markdown(f"Değer  \n**{para(s['deger'], sembol)}**")
        kzr = "#16a34a" if s["kz"] >= 0 else "#dc2626"
        c[3].markdown(f"K/Z  \n<span style='color:{kzr};font-weight:700'>"
                      f"{para(s['kz'], sembol)} ({s['kz_pct']:+.1f}%)</span>",
                      unsafe_allow_html=True)
    c[4].markdown("<div style='height:6px'></div>", unsafe_allow_html=True)
    if c[4].button("🗑️", key=f"sil_{p['id']}", help="Bu pozisyonu sil"):
        try:
            db.portfoy_sil(p["id"])
            st.rerun()
        except Exception as e:
            st.error("Silinemedi: " + str(e))
    st.divider()

st.caption(f'Son güncelleme: {datetime.now().strftime("%H:%M")} · '
           f'{"🟢 Canlı fiyat: Finnhub" if FINN else "Fiyatlar Yahoo (gecikmeli)"} · '
           f'maliyeti USD olarak girersin, gösterim {sembol}. Yatırım tavsiyesi değildir.')
