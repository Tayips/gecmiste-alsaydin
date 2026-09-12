"""
"GECMISTE ALSAYDIN" — Streamlit MVP
------------------------------------------------
Kullanici bir hisse + tutar + baslangic tarihi girer; uygulama geriye donuk olarak
"o gun yatirsaydin bugun ne olurdu" senaryosunu gosterir. Hem tek seferlik hem
DCA (aylara yayarak), ve her zaman SPY (endeks) kiyasiyla.

SORUMLU TASARIM:
 - Sadece GECMIS gercekleri gosterir; tahmin/tavsiye yok.
 - Her zaman endeks kiyasi (kolay para yanilgisini onlemek icin).
 - Net uyari: gecmis performans gelecegi garanti etmez.

CALISTIRMA (yerelde):
   pip install streamlit yfinance pandas
   streamlit run app.py
Tarayicida otomatik acilir. Yayinlamak icin: Streamlit Community Cloud (ucretsiz).
"""

import streamlit as st
import yfinance as yf
import pandas as pd
from datetime import date

st.set_page_config(page_title="Gecmiste Alsaydin", page_icon="📈", layout="centered")

# ---------- Hesaplama fonksiyonlari ----------
@st.cache_data(ttl=3600)
def fiyat_indir(ticker, baslangic):
    df = yf.download(ticker, start=str(baslangic), auto_adjust=True, progress=False)
    if df.empty:
        return None
    close = df["Close"]
    # yeni yfinance tek hisse icin bile tablo (DataFrame) dondurur -> tek sutunu seriye cevir
    if isinstance(close, pd.DataFrame):
        close = close.iloc[:, 0]
    return close.dropna()

def tek_seferlik(fiyat, tutar):
    """Baslangicta tum tutari yatir; gunluk deger egrisi doner."""
    adet = tutar / float(fiyat.iloc[0])
    return adet * fiyat

def dca(fiyat, tutar):
    """Tutari aylik esit taksitlerle yatir; gunluk deger egrisi doner."""
    aylik = fiyat.resample("MS").first().dropna()      # her ayin ilk fiyati
    n = len(aylik)
    taksit = tutar / n
    kum_adet = pd.Series(0.0, index=fiyat.index)
    toplam = 0.0
    for tarih, ay_fiyat in aylik.items():
        toplam += taksit / float(ay_fiyat)
        kum_adet.loc[fiyat.index >= tarih] = toplam
    return kum_adet * fiyat, n, taksit

def metrik(deger_egrisi, tutar):
    son = float(deger_egrisi.iloc[-1])
    n_gun = len(deger_egrisi)
    getiri = (son - tutar) / tutar * 100
    yillik = ((son / tutar) ** (252 / n_gun) - 1) * 100 if n_gun > 1 else 0
    return son, getiri, yillik

# ---------- Arayuz ----------
st.title("📈 Gecmiste Alsaydin?")
st.caption("Bir hisseye geçmişte yatırım yapsaydın bugün ne olurdu — ve endeks (SPY) ile kıyası.")

st.info("ℹ️ Bu araç yalnızca **geçmiş** verileri gösterir. Yatırım tavsiyesi değildir; "
        "geçmiş performans geleceği garanti etmez.", icon="ℹ️")

c1, c2 = st.columns(2)
ticker = c1.text_input("Hisse kodu", "NVDA").upper().strip()
tutar  = c2.number_input("Yatırılan tutar (€/$)", min_value=1.0, value=1000.0, step=100.0)
c3, c4 = st.columns(2)
baslangic = c3.date_input("Başlangıç tarihi", date(2020, 1, 1),
                          min_value=date(2000, 1, 1), max_value=date.today())
yontem = c4.selectbox("Yatırım şekli", ["Tek seferlik", "Aylara yayarak (DCA)"])

if st.button("Hesapla", type="primary"):
    fiyat = fiyat_indir(ticker, baslangic)
    spy   = fiyat_indir("SPY", baslangic)
    if fiyat is None or spy is None:
        st.error(f"'{ticker}' için veri bulunamadı. Kodu kontrol et (örn. AAPL, MSFT, NVDA).")
    else:
        # ortak tarih araligi
        ortak = fiyat.index.intersection(spy.index)
        fiyat, spy = fiyat.loc[ortak], spy.loc[ortak]

        if yontem == "Tek seferlik":
            hisse_egri = tek_seferlik(fiyat, tutar)
            spy_egri   = tek_seferlik(spy, tutar)
            ek = ""
        else:
            hisse_egri, n, taksit = dca(fiyat, tutar)
            spy_egri, _, _        = dca(spy, tutar)
            ek = f" · {n} ay boyunca ayda ~{taksit:,.0f} taksit"

        h_son, h_get, h_yil = metrik(hisse_egri, tutar)
        s_son, s_get, s_yil = metrik(spy_egri, tutar)

        st.subheader(f"{ticker} sonucu{ek}")
        m1, m2, m3 = st.columns(3)
        m1.metric("Bugünkü değer", f"{h_son:,.0f}", f"{h_get:+.1f}%")
        m2.metric("Yıllık ortalama", f"{h_yil:+.1f}%")
        m3.metric(f"Aynı para SPY'de", f"{s_son:,.0f}", f"{s_get:+.1f}%")

        if h_son > s_son:
            st.success(f"✅ {ticker}, aynı dönemde SPY endeksini **geçti** "
                       f"({h_son:,.0f} vs {s_son:,.0f}).")
        else:
            st.warning(f"⚠️ {ticker}, aynı dönemde SPY endeksinin **altında** kaldı "
                       f"({h_son:,.0f} vs {s_son:,.0f}). Endeks daha iyiydi.")

        grafik = pd.DataFrame({ticker: hisse_egri, "SPY (endeks)": spy_egri})
        st.line_chart(grafik)
        st.caption("Yatırdığın tutarın zaman içindeki değeri. Mavi/kırmızı senin hissen, "
                   "diğeri aynı parayı endekse koysaydın.")

st.divider()
st.caption("⚠️ Sadece geçmiş veriye dayalı eğitim amaçlı bir araçtır. Yatırım tavsiyesi değildir. "
           "Tek bir kazanan hisseye bakıp 'kolay para' sanma — o hisseyi önceden seçmek "
           "imkânsızdı. Bu yüzden her sonuç endeksle kıyaslanır. Veri: Yahoo Finance.")
