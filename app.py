"""
GECMISTE ALSAYDIN? — Surum 2
------------------------------------------------
Sade, profesyonel ve herkesin (yasli kullanicilar dahil) kolayca anlayabilecegi
bir arayuz. Sirket adiyla arama (tum ABD hisseleri), baslangic + bitis tarihi,
ve her zaman endeks (SPY) kiyasi.

Egitim amaclidir; yatirim tavsiyesi degildir.

CALISTIRMA:  streamlit run app.py
"""

import streamlit as st
import yfinance as yf
import pandas as pd
import requests
from datetime import date

st.set_page_config(page_title="Geçmişte Alsaydın?", page_icon="📈", layout="centered")

# ---------- Basit, temiz gorunum (buyuk ve okunakli) ----------
st.markdown("""
<style>
  html, body, [class*="css"] { font-size: 17px; }
  .stApp { background: #ffffff; }
  h1 { color: #14213d; font-weight: 800; }
  .aciklama { color:#4b5563; font-size:18px; margin-bottom:8px; }
  .adim { background:#f3f6fb; border:1px solid #e2e8f0; border-radius:10px;
          padding:12px 16px; color:#334155; font-size:16px; margin-bottom:14px; }
  div.stButton > button { background:#14213d; color:#fff; font-size:18px;
          padding:10px 26px; border-radius:8px; border:none; }
  div.stButton > button:hover { background:#1f3a5f; }
</style>
""", unsafe_allow_html=True)

# ---------- Veri ve arama ----------
@st.cache_data(ttl=3600)
def hisse_ara(sorgu):
    """Sirket adi/kod ile ABD hisselerini arar. [(sembol, ad), ...] doner."""
    try:
        r = requests.get(
            "https://query2.finance.yahoo.com/v1/finance/search",
            params={"q": sorgu, "quotesCount": 12, "newsCount": 0},
            headers={"User-Agent": "Mozilla/5.0"}, timeout=6)
        veri = r.json().get("quotes", [])
        sonuc = []
        for q in veri:
            if q.get("quoteType") != "EQUITY":
                continue
            sembol = q.get("symbol", "")
            ad = q.get("shortname") or q.get("longname") or sembol
            borsa = q.get("exchDisp", "")
            sonuc.append((sembol, f"{ad} ({sembol}) · {borsa}"))
        return sonuc
    except Exception:
        return []

@st.cache_data(ttl=3600)
def fiyat_indir(ticker, baslangic, bitis):
    df = yf.download(ticker, start=str(baslangic), end=str(bitis),
                     auto_adjust=True, progress=False)
    if df.empty:
        return None
    close = df["Close"]
    if isinstance(close, pd.DataFrame):
        close = close.iloc[:, 0]
    return close.dropna()

def tek_seferlik(fiyat, tutar):
    return (tutar / float(fiyat.iloc[0])) * fiyat

def dca(fiyat, tutar):
    aylik = fiyat.resample("MS").first().dropna()
    n = len(aylik); taksit = tutar / n
    kum = pd.Series(0.0, index=fiyat.index); toplam = 0.0
    for tarih, ay_fiyat in aylik.items():
        toplam += taksit / float(ay_fiyat)
        kum.loc[fiyat.index >= tarih] = toplam
    return kum * fiyat, n, taksit

def metrik(egri, tutar):
    son = float(egri.iloc[-1]); n = len(egri)
    getiri = (son - tutar) / tutar * 100
    yillik = ((son / tutar) ** (252 / n) - 1) * 100 if n > 1 else 0
    return son, getiri, yillik

def para(x, sembol="€"):
    return f"{x:,.0f}".replace(",", ".") + " " + sembol

# ---------- Baslik ----------
st.title("📈 Geçmişte Alsaydın?")
st.markdown('<p class="aciklama">Bir hisseye geçmişte yatırım yapsaydın bugün ne olurdu? '
            'Sonuç her zaman borsa endeksi (SPY) ile karşılaştırılır.</p>', unsafe_allow_html=True)
st.markdown('<div class="adim">Nasıl kullanılır: <b>1)</b> Şirketi ara ve seç &nbsp; '
            '<b>2)</b> Tutarı gir &nbsp; <b>3)</b> Tarihleri seç &nbsp; '
            '<b>4)</b> “Hesapla”ya bas</div>', unsafe_allow_html=True)

st.info("ℹ️ Bu araç yalnızca **geçmiş** verileri gösterir. Yatırım tavsiyesi değildir; "
        "geçmiş performans geleceği garanti etmez.", icon="ℹ️")

# ---------- 1) Sirket secimi ----------
st.subheader("1) Hangi şirket?")
sorgu = st.text_input("Şirket adı veya hisse kodu yazın (örn. Apple, Microsoft, NVDA):", "Apple")
secilen = sorgu.upper().strip()
sonuclar = hisse_ara(sorgu) if sorgu.strip() else []
if sonuclar:
    etiketler = [ad for _, ad in sonuclar]
    secim = st.selectbox("Bulunan şirketlerden birini seçin:", etiketler)
    secilen = sonuclar[etiketler.index(secim)][0]
elif sorgu.strip():
    st.caption(f"Arama sonucu bulunamadı; '{secilen}' kodunu doğrudan deneyeceğiz.")

# ---------- 2) Tutar ve para birimi ----------
st.subheader("2) Ne kadar yatırım?")
c1, c2 = st.columns([2, 1])
tutar = c1.number_input("Yatırılan tutar:", min_value=1.0, value=1000.0, step=100.0)
sembol = c2.selectbox("Para birimi:", ["€", "$"])

# ---------- 3) Tarihler ----------
st.subheader("3) Hangi tarihler arası?")
c3, c4 = st.columns(2)
baslangic = c3.date_input("Başlangıç tarihi:", date(2020, 1, 1),
                          min_value=date(2000, 1, 1), max_value=date.today())
bitis = c4.date_input("Bitiş tarihi:", date.today(),
                      min_value=date(2000, 1, 2), max_value=date.today())

# ---------- 4) Yontem + Hesapla ----------
st.subheader("4) Yatırım şekli")
yontem = st.radio("", ["Tek seferde (baştan hepsi)", "Aylara yayarak (her ay biraz)"],
                  horizontal=True, label_visibility="collapsed")

if st.button("Hesapla"):
    if baslangic >= bitis:
        st.error("Başlangıç tarihi, bitiş tarihinden önce olmalı.")
    else:
        with st.spinner("Hesaplanıyor..."):
            fiyat = fiyat_indir(secilen, baslangic, bitis)
            spy   = fiyat_indir("SPY", baslangic, bitis)
        if fiyat is None or spy is None:
            st.error(f"'{secilen}' için veri bulunamadı. Şirket adını farklı yazmayı "
                     "ya da hisse kodunu (örn. AAPL) girmeyi dene.")
        else:
            ortak = fiyat.index.intersection(spy.index)
            fiyat, spy = fiyat.loc[ortak], spy.loc[ortak]
            if yontem.startswith("Tek"):
                h_egri, s_egri = tek_seferlik(fiyat, tutar), tek_seferlik(spy, tutar)
                ek = ""
            else:
                h_egri, n, tk = dca(fiyat, tutar); s_egri, _, _ = dca(spy, tutar)
                ek = f" · {n} ay boyunca ayda ~{para(tk, sembol)}"

            h_son, h_get, h_yil = metrik(h_egri, tutar)
            s_son, s_get, s_yil = metrik(s_egri, tutar)

            st.subheader(f"Sonuç{ek}")
            m1, m2, m3 = st.columns(3)
            m1.metric("Bugünkü değeri", para(h_son, sembol), f"{h_get:+.0f}%")
            m2.metric("Yıllık ortalama", f"{h_yil:+.1f}%")
            m3.metric("Aynı para endekste (SPY)", para(s_son, sembol), f"{s_get:+.0f}%")

            if h_son > s_son:
                st.success(f"✅ Bu hisse, aynı dönemde borsa endeksini (SPY) **geçti**: "
                           f"{para(h_son, sembol)} — endeks {para(s_son, sembol)}.")
            else:
                st.warning(f"⚠️ Bu hisse, aynı dönemde endeksin (SPY) **altında kaldı**: "
                           f"{para(h_son, sembol)} — endeks {para(s_son, sembol)}. "
                           "Yani endeks daha iyiydi.")

            grafik = pd.DataFrame({"Bu hisse": h_egri, "Endeks (SPY)": s_egri})
            st.line_chart(grafik)
            st.caption("Çizgiler, yatırdığın paranın zaman içindeki değerini gösterir.")

st.divider()
st.caption("⚠️ Sadece geçmiş veriye dayalı, eğitim amaçlı bir araçtır. Yatırım tavsiyesi değildir. "
           "Tek bir kazanan hisseye bakıp 'kolay para' sanma — o hisseyi önceden seçmek imkânsızdı. "
           "Bu yüzden her sonuç endeksle kıyaslanır. Veri kaynağı: Yahoo Finance.")
