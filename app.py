"""
GECMISTE ALSAYDIN? — Surum 3
------------------------------------------------
- Sirket arama (yerel populer liste + canli Yahoo aramasi; tum ABD hisseleri)
- Para birimi: € / $ / ₺ (gercek tarihsel kur ile cevrilir)
- Sade bir sonuc cumlesi (herkesin anlayacagi dille)
- Baslangic + bitis tarihi, DCA secenegi, her zaman endeks (SPY) kiyasi

Egitim amaclidir; yatirim tavsiyesi degildir.
CALISTIRMA:  streamlit run app.py
"""

import streamlit as st
import yfinance as yf
import pandas as pd
import requests
from datetime import date

st.set_page_config(page_title="Geçmişte Alsaydın?", page_icon="📈", layout="centered")

st.markdown("""
<style>
  html, body, [class*="css"] { font-size: 17px; }
  .stApp { background:#ffffff; }
  h1 { color:#14213d; font-weight:800; }
  .aciklama { color:#4b5563; font-size:18px; }
  .adim { background:#f3f6fb; border:1px solid #e2e8f0; border-radius:10px;
          padding:12px 16px; color:#334155; font-size:16px; margin-bottom:14px; }
  .sonuckutu { background:#f0f7f0; border:1px solid #cfe6cf; border-left:6px solid #16a34a;
          border-radius:10px; padding:18px 20px; font-size:19px; color:#14213d; line-height:1.6; }
  .sonuckutu.zarar { background:#fdf3f3; border-color:#f0d0d0; border-left-color:#dc2626; }
  div.stButton > button { background:#14213d; color:#fff; font-size:18px;
          padding:10px 26px; border-radius:8px; border:none; }
  div.stButton > button:hover { background:#1f3a5f; }
</style>
""", unsafe_allow_html=True)

# ---------- Populer ABD hisseleri (yerel arama tabani) ----------
POPULER = {
 "AAPL":"Apple","MSFT":"Microsoft","NVDA":"NVIDIA","AMZN":"Amazon","GOOGL":"Alphabet (Google)",
 "META":"Meta (Facebook)","TSLA":"Tesla","BRK-B":"Berkshire Hathaway","JPM":"JPMorgan Chase",
 "V":"Visa","MA":"Mastercard","JNJ":"Johnson & Johnson","WMT":"Walmart","PG":"Procter & Gamble",
 "KO":"Coca-Cola","PEP":"PepsiCo","DIS":"Walt Disney","NFLX":"Netflix","INTC":"Intel",
 "AMD":"AMD","ORCL":"Oracle","CSCO":"Cisco","ADBE":"Adobe","CRM":"Salesforce","QCOM":"Qualcomm",
 "IBM":"IBM","BA":"Boeing","GE":"General Electric","NKE":"Nike","MCD":"McDonald's",
 "SBUX":"Starbucks","PYPL":"PayPal","UBER":"Uber","ABNB":"Airbnb","PLTR":"Palantir",
 "BABA":"Alibaba","T":"AT&T","VZ":"Verizon","XOM":"Exxon Mobil","CVX":"Chevron",
 "PFE":"Pfizer","MRNA":"Moderna","BAC":"Bank of America","GS":"Goldman Sachs","F":"Ford",
 "GM":"General Motors","COST":"Costco","HD":"Home Depot","LMT":"Lockheed Martin",
 "SPY":"S&P 500 endeksi (SPY)","QQQ":"Nasdaq 100 (QQQ)","COIN":"Coinbase","SHOP":"Shopify",
}

@st.cache_data(ttl=3600)
def hisse_ara(sorgu):
    """Yerel populer liste + canli Yahoo aramasi. [(sembol, etiket), ...] doner."""
    s = sorgu.strip().lower()
    sonuc = []
    for tk, ad in POPULER.items():
        if s in ad.lower() or s in tk.lower():
            sonuc.append((tk, f"{ad} ({tk})"))
    try:
        r = requests.get("https://query2.finance.yahoo.com/v1/finance/search",
                         params={"q": sorgu, "quotesCount": 10, "newsCount": 0},
                         headers={"User-Agent": "Mozilla/5.0"}, timeout=6)
        for q in r.json().get("quotes", []):
            if q.get("quoteType") != "EQUITY":
                continue
            tk = q.get("symbol", "")
            ad = q.get("shortname") or q.get("longname") or tk
            if tk and tk not in [x[0] for x in sonuc]:
                sonuc.append((tk, f"{ad} ({tk}) · {q.get('exchDisp','')}"))
    except Exception:
        pass
    return sonuc[:15]

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

def kur_serisi(sembol, baslangic, bitis):
    """'Secilen para birimi / 1 USD' serisi. $ -> None (cevrim yok)."""
    if sembol == "$":
        return None
    try:
        if sembol == "€":
            eurusd = fiyat_indir("EURUSD=X", baslangic, bitis)  # 1 EUR = ? USD
            return 1.0 / eurusd                                 # EUR / USD
        if sembol == "₺":
            return fiyat_indir("USDTRY=X", baslangic, bitis)    # TRY / USD
    except Exception:
        return None
    return None

def deger_egrisi(fiyat_usd, tutar, kur, yontem):
    """USD fiyat serisinden, secilen para birimindeki deger egrisini uretir."""
    if kur is None:
        kur = pd.Series(1.0, index=fiyat_usd.index)
    kur = kur.reindex(fiyat_usd.index).ffill().bfill()
    n = taksit = None
    if yontem.startswith("Tek"):
        usd_tutar = tutar / float(kur.iloc[0])
        adet = usd_tutar / float(fiyat_usd.iloc[0])
        deger_usd = adet * fiyat_usd
    else:
        aylik = fiyat_usd.resample("MS").first().dropna()
        n = len(aylik); taksit = tutar / n
        kum = pd.Series(0.0, index=fiyat_usd.index); toplam = 0.0
        for tarih, ay_fiyat in aylik.items():
            kur_o = float(kur.asof(tarih))
            toplam += (taksit / kur_o) / float(ay_fiyat)
            kum.loc[fiyat_usd.index >= tarih] = toplam
        deger_usd = kum * fiyat_usd
    return deger_usd * kur, n, taksit

def metrik(egri, tutar):
    son = float(egri.iloc[-1]); n = len(egri)
    return son, (son - tutar) / tutar * 100, ((son / tutar) ** (252 / n) - 1) * 100 if n > 1 else 0

def para(x, s="€"):
    return f"{x:,.0f}".replace(",", ".") + " " + s

# ---------- Baslik ----------
st.title("📈 Geçmişte Alsaydın?")
st.markdown('<p class="aciklama">Bir hisseye geçmişte yatırım yapsaydın ne olurdu? '
            'Sonuç her zaman borsa endeksi (SPY) ile karşılaştırılır.</p>', unsafe_allow_html=True)
st.markdown('<div class="adim">Nasıl kullanılır: <b>1)</b> Şirketi ara ve seç &nbsp; '
            '<b>2)</b> Tutarı gir &nbsp; <b>3)</b> Tarihleri seç &nbsp; <b>4)</b> “Hesapla”ya bas</div>',
            unsafe_allow_html=True)
st.info("ℹ️ Bu araç yalnızca **geçmiş** verileri gösterir. Yatırım tavsiyesi değildir; "
        "geçmiş performans geleceği garanti etmez.", icon="ℹ️")

# ---------- 1) Sirket ----------
st.subheader("1) Hangi şirket?")
sorgu = st.text_input("Şirket adını veya kodunu yazın (örn. Apple, Microsoft, NVDA):", "Apple")
secilen, secilen_ad = sorgu.upper().strip(), sorgu.strip()
if sorgu.strip():
    bulunan = hisse_ara(sorgu)
    if bulunan:
        etiketler = [e for _, e in bulunan]
        secim = st.selectbox("Aradığınız şirketi listeden seçin:", etiketler)
        i = etiketler.index(secim)
        secilen, secilen_ad = bulunan[i][0], bulunan[i][1].split(" (")[0]
    else:
        st.caption(f"Liste bulunamadı; '{secilen}' kodunu doğrudan deneyeceğiz.")

# ---------- 2) Tutar ----------
st.subheader("2) Ne kadar yatırım?")
c1, c2 = st.columns([2, 1])
tutar = c1.number_input("Yatırılan tutar:", min_value=1.0, value=1000.0, step=100.0)
sembol = c2.selectbox("Para birimi:", ["€", "$", "₺"])

# ---------- 3) Tarihler ----------
st.subheader("3) Hangi tarihler arası?")
c3, c4 = st.columns(2)
baslangic = c3.date_input("Başlangıç tarihi:", date(2020, 1, 1),
                          min_value=date(2000, 1, 1), max_value=date.today())
bitis = c4.date_input("Bitiş tarihi:", date.today(),
                      min_value=date(2000, 1, 2), max_value=date.today())

# ---------- 4) Yontem ----------
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
            kur   = kur_serisi(sembol, baslangic, bitis)
        if fiyat is None or spy is None:
            st.error(f"'{secilen}' için veri bulunamadı. Şirket adını farklı yazmayı ya da "
                     "hisse kodunu (örn. AAPL) girmeyi dene.")
        else:
            if sembol != "$" and kur is None:
                st.caption("Not: Kur verisi alınamadı; sonuç dolar bazlı gösteriliyor.")
            ortak = fiyat.index.intersection(spy.index)
            fiyat, spy = fiyat.loc[ortak], spy.loc[ortak]

            h_egri, n, tk = deger_egrisi(fiyat, tutar, kur, yontem)
            s_egri, _, _  = deger_egrisi(spy,   tutar, kur, yontem)
            h_son, h_get, h_yil = metrik(h_egri, tutar)
            s_son, s_get, s_yil = metrik(s_egri, tutar)

            kar = h_son - tutar
            kz  = "kâr" if kar >= 0 else "zarar"
            bas_s, bit_s = baslangic.strftime("%d.%m.%Y"), bitis.strftime("%d.%m.%Y")
            ekdca = f" (aylara yayarak, {n} ayda ~{para(tk, sembol)})" if n else ""

            # ---- Sade sonuc cumlesi ----
            kutu_sinif = "sonuckutu" if kar >= 0 else "sonuckutu zarar"
            st.markdown(
                f'<div class="{kutu_sinif}">'
                f'<b>{bas_s} – {bit_s}</b> tarihleri arasında <b>{secilen_ad}</b> hissesine '
                f'<b>{para(tutar, sembol)}</b> yatırsaydınız{ekdca}, dönem sonunda '
                f'<b>{para(h_son, sembol)}</b> olurdu.<br>'
                f'Bu, yaklaşık <b>{para(abs(kar), sembol)} {kz}</b> demektir ({h_get:+.0f}%).<br>'
                f'<span style="font-size:16px;color:#4b5563">Aynı parayı borsa endeksine (SPY) '
                f'koysaydınız {para(s_son, sembol)} olurdu.</span>'
                f'</div>', unsafe_allow_html=True)

            # ---- Ozet kutular ----
            m1, m2, m3 = st.columns(3)
            m1.metric("Dönem sonu değeri", para(h_son, sembol), f"{h_get:+.0f}%")
            m2.metric("Yıllık ortalama", f"{h_yil:+.1f}%")
            m3.metric("Endekste (SPY)", para(s_son, sembol), f"{s_get:+.0f}%")

            if h_son > s_son:
                st.success("✅ Bu hisse, aynı dönemde borsa endeksini (SPY) geçti.")
            else:
                st.warning("⚠️ Bu hisse, aynı dönemde endeksin (SPY) altında kaldı — endeks daha iyiydi.")

            st.line_chart(pd.DataFrame({"Bu hisse": h_egri, "Endeks (SPY)": s_egri}))
            st.caption("Çizgiler, yatırdığın paranın zaman içindeki değerini gösterir.")

st.divider()
st.caption("⚠️ Sadece geçmiş veriye dayalı, eğitim amaçlı bir araçtır. Yatırım tavsiyesi değildir. "
           "Tek bir kazanan hisseye bakıp 'kolay para' sanma — o hisseyi önceden seçmek imkânsızdı. "
           "Bu yüzden her sonuç endeksle kıyaslanır. ₺/€ için tarihsel döviz kuru uygulanır. "
           "Veri kaynağı: Yahoo Finance.")
