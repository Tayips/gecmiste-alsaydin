"""
GECMISTE ALSAYDIN? — Surum 4 (UI/UX yenilemesi)
------------------------------------------------
- Sol kontrol paneli (sidebar) + sag sonuc alani (dashboard hissi)
- Buyuk KPI kartlari
- Etkilesimli grafik (Plotly, fareyle deger gosterir)
- Hazir senaryo butonlari (preset)
- DCA: "her ay ne kadar" + yillik artis
- Sirket arama, € / $ / ₺ (gercek kur), sade sonuc cumlesi
- Paylasilabilir ozet gorseli (PNG indir) + Twitter linki

Egitim amaclidir; yatirim tavsiyesi degildir.
CALISTIRMA:  pip install streamlit yfinance pandas curl_cffi plotly matplotlib
             streamlit run app.py
"""

import io, urllib.parse
from datetime import date, timedelta

import streamlit as st
import yfinance as yf
import pandas as pd
import requests
import plotly.graph_objects as go
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

st.set_page_config(page_title="Geçmişte Alsaydın?", page_icon="📈", layout="wide")

st.markdown("""
<style>
  .stApp { background:#f7f9fc; }
  h1 { color:#14213d; font-weight:800; }
  .kart { background:#fff; border:1px solid #e6eaf0; border-radius:16px;
          padding:18px 20px; box-shadow:0 1px 3px rgba(20,33,61,.06); }
  .kpi-baslik { color:#6b7280; font-size:13px; text-transform:uppercase; letter-spacing:.04em; }
  .kpi-deger { font-size:30px; font-weight:800; color:#14213d; margin-top:4px; }
  .kpi-alt { font-size:15px; font-weight:700; margin-top:2px; }
  .yesil { color:#16a34a; } .kirmizi { color:#dc2626; }
  .cumle { background:#fff; border-radius:16px; padding:20px 24px; font-size:20px;
           color:#14213d; line-height:1.6; border-left:6px solid #16a34a; }
  .cumle.zarar { border-left-color:#dc2626; }
</style>
""", unsafe_allow_html=True)

POPULER = {
 "AAPL":"Apple","MSFT":"Microsoft","NVDA":"NVIDIA","AMZN":"Amazon","GOOGL":"Alphabet (Google)",
 "META":"Meta","TSLA":"Tesla","JPM":"JPMorgan","V":"Visa","MA":"Mastercard","KO":"Coca-Cola",
 "PEP":"PepsiCo","DIS":"Disney","NFLX":"Netflix","AMD":"AMD","INTC":"Intel","ORCL":"Oracle",
 "ADBE":"Adobe","CRM":"Salesforce","NKE":"Nike","MCD":"McDonald's","SBUX":"Starbucks",
 "BA":"Boeing","XOM":"Exxon","PFE":"Pfizer","BAC":"Bank of America","WMT":"Walmart",
 "COST":"Costco","HD":"Home Depot","UBER":"Uber","PLTR":"Palantir","COIN":"Coinbase",
 "SPY":"S&P 500 (SPY)","QQQ":"Nasdaq 100 (QQQ)",
}

@st.cache_data(ttl=3600)
def hisse_ara(sorgu):
    s = sorgu.strip().lower(); sonuc = []
    for tk, ad in POPULER.items():
        if s in ad.lower() or s in tk.lower():
            sonuc.append((tk, f"{ad} ({tk})"))
    try:
        r = requests.get("https://query2.finance.yahoo.com/v1/finance/search",
                         params={"q": sorgu, "quotesCount": 10, "newsCount": 0},
                         headers={"User-Agent": "Mozilla/5.0"}, timeout=6)
        for q in r.json().get("quotes", []):
            if q.get("quoteType") != "EQUITY": continue
            tk = q.get("symbol", ""); ad = q.get("shortname") or tk
            if tk and tk not in [x[0] for x in sonuc]:
                sonuc.append((tk, f"{ad} ({tk}) · {q.get('exchDisp','')}"))
    except Exception:
        pass
    return sonuc[:15]

@st.cache_data(ttl=3600)
def fiyat_indir(ticker, bas, bit):
    df = yf.download(ticker, start=str(bas), end=str(bit), auto_adjust=True, progress=False)
    if df.empty: return None
    close = df["Close"]
    if isinstance(close, pd.DataFrame): close = close.iloc[:, 0]
    return close.dropna()

def kur_serisi(sembol, bas, bit):
    if sembol == "$": return None
    try:
        if sembol == "€": return 1.0 / fiyat_indir("EURUSD=X", bas, bit)
        if sembol == "₺": return fiyat_indir("USDTRY=X", bas, bit)
    except Exception:
        return None
    return None

def _kur_hazirla(kur, idx):
    if kur is None: kur = pd.Series(1.0, index=idx)
    return kur.reindex(idx).ffill().bfill()

def lump_deger(fiyat_usd, tutar, kur):
    kur = _kur_hazirla(kur, fiyat_usd.index)
    adet = (tutar / float(kur.iloc[0])) / float(fiyat_usd.iloc[0])
    return adet * fiyat_usd * kur, tutar

def dca_deger(fiyat_usd, aylik_tutar, artis, kur):
    kur = _kur_hazirla(kur, fiyat_usd.index)
    # Her ayin GERCEK ilk islem gunu (ay basi tatile denk gelirse nan olmasin diye):
    ilk_gunler = fiyat_usd.groupby(fiyat_usd.index.to_period("M")).head(1)
    kum = pd.Series(0.0, index=fiyat_usd.index); adet = 0.0; yatirilan = 0.0
    for i, (t, pv) in enumerate(ilk_gunler.items()):
        katki = aylik_tutar * (1 + artis) ** (i // 12)
        adet += (katki / float(kur.loc[t])) / float(pv)
        yatirilan += katki
        kum.loc[fiyat_usd.index >= t] = adet
    return kum * fiyat_usd * kur, yatirilan

def metrik(egri, yatirilan):
    son = float(egri.iloc[-1]); n = len(egri)
    getiri = (son - yatirilan) / yatirilan * 100
    yillik = ((son / yatirilan) ** (252 / n) - 1) * 100 if n > 1 and son > 0 else 0
    return son, getiri, yillik

def para(x, s="€"):
    return f"{x:,.0f}".replace(",", ".") + " " + s

def ozet_gorseli(ad, bas, bit, yatirilan, son, getiri, s_son, sembol):
    fig, ax = plt.subplots(figsize=(6.4, 3.35), dpi=200)
    fig.patch.set_facecolor("#14213d"); ax.axis("off")
    renk = "#4ade80" if son >= yatirilan else "#f87171"
    ax.text(0.5, 0.90, "Geçmişte Alsaydın?", ha="center", color="#ffffff",
            fontsize=16, fontweight="bold", transform=ax.transAxes)
    ax.text(0.5, 0.74, f"{ad} · {bas} – {bit}", ha="center", color="#c7d0e0",
            fontsize=10, transform=ax.transAxes)
    ax.text(0.5, 0.50, para(son, sembol), ha="center", color=renk,
            fontsize=30, fontweight="bold", transform=ax.transAxes)
    ax.text(0.5, 0.34, f"{para(yatirilan, sembol)} yatırım → {getiri:+.0f}%",
            ha="center", color="#ffffff", fontsize=12, transform=ax.transAxes)
    ax.text(0.5, 0.15, f"Aynı para endekste (SPY): {para(s_son, sembol)}",
            ha="center", color="#9aa7bd", fontsize=9, transform=ax.transAxes)
    buf = io.BytesIO(); fig.savefig(buf, format="png", bbox_inches="tight",
                                    facecolor=fig.get_facecolor()); plt.close(fig)
    return buf.getvalue()

# ---------- Preset & durum ----------
BUGUN = date.today()
PRESETS = [
    ("🚀 Pandemi başında Apple", dict(k_sorgu="AAPL", k_tutar=1000.0, k_sembol="$",
        k_bas=date(2020, 3, 1), k_bit=BUGUN, k_yontem="Tek seferde (baştan hepsi)")),
    ("📈 5 yıl her ay NVDA", dict(k_sorgu="NVDA", k_aylik=100.0, k_sembol="$",
        k_bas=BUGUN - timedelta(days=365*5), k_bit=BUGUN,
        k_yontem="Aylara yayarak (her ay biraz)")),
    ("🏛️ 2010'dan beri SPY", dict(k_sorgu="SPY", k_tutar=1000.0, k_sembol="$",
        k_bas=date(2010, 1, 1), k_bit=BUGUN, k_yontem="Tek seferde (baştan hepsi)")),
]
_def = dict(k_sorgu="Apple", k_tutar=1000.0, k_aylik=100.0, k_artis=0, k_sembol="€",
            k_bas=date(2020, 1, 1), k_bit=BUGUN, k_yontem="Tek seferde (baştan hepsi)")
for k, v in _def.items():
    st.session_state.setdefault(k, v)

# ---------- SIDEBAR: kontrol paneli ----------
with st.sidebar:
    st.header("Ayarlar")
    st.caption("Hazır senaryo dene:")
    for etiket, ayar in PRESETS:
        if st.button(etiket, use_container_width=True):
            for k, v in ayar.items():
                st.session_state[k] = v
            st.rerun()
    st.divider()

    sorgu = st.text_input("Şirket (ad veya kod)", key="k_sorgu",
                          help="Apple, Microsoft, NVDA gibi yazın; listeden seçin.")
    secilen, secilen_ad = sorgu.upper().strip(), sorgu.strip()
    if sorgu.strip():
        bulunan = hisse_ara(sorgu)
        if bulunan:
            etiketler = [e for _, e in bulunan]
            secim = st.selectbox("Listeden seçin", etiketler)
            i = etiketler.index(secim)
            secilen, secilen_ad = bulunan[i][0], bulunan[i][1].split(" (")[0]

    sembol = st.selectbox("Para birimi", ["€", "$", "₺"], key="k_sembol")
    yontem = st.radio("Yatırım şekli", ["Tek seferde (baştan hepsi)",
                      "Aylara yayarak (her ay biraz)"], key="k_yontem")
    if yontem.startswith("Tek"):
        tutar = st.number_input("Yatırılan tutar", min_value=1.0, step=100.0, key="k_tutar")
        aylik = artis = None
    else:
        aylik = st.number_input("Her ay ne kadar?", min_value=1.0, step=50.0, key="k_aylik")
        artis = st.slider("Her yıl katkıyı artır (%)", 0, 30, key="k_artis",
                          help="Enflasyona göre her yıl aylık yatırımını artırmak istersen.") / 100.0

    c_b, c_e = st.columns(2)
    bas = c_b.date_input("Başlangıç", key="k_bas",
                         min_value=date(2000, 1, 1), max_value=BUGUN)
    bit = c_e.date_input("Bitiş", key="k_bit",
                         min_value=date(2000, 1, 2), max_value=BUGUN)
    hesapla = st.button("Hesapla", type="primary", use_container_width=True)

# ---------- ANA ALAN ----------
st.title("📈 Geçmişte Alsaydın?")
st.caption("Soldaki panelden bir şirket, tutar ve tarih seç; sonuç her zaman borsa endeksi (SPY) "
           "ile karşılaştırılır. Bu araç yatırım tavsiyesi değildir; yalnızca geçmişi gösterir.")

if hesapla:
    if bas >= bit:
        st.error("Başlangıç tarihi, bitiş tarihinden önce olmalı.")
    else:
        with st.spinner("Hesaplanıyor..."):
            fiyat = fiyat_indir(secilen, bas, bit)
            spy = fiyat_indir("SPY", bas, bit)
            kur = kur_serisi(sembol, bas, bit)
        if fiyat is None or spy is None:
            st.error(f"'{secilen}' için veri bulunamadı. Şirket adını/kodunu kontrol et.")
        else:
            if sembol != "$" and kur is None:
                st.caption("Not: Kur verisi alınamadı; sonuç dolar bazlı gösteriliyor.")
            ortak = fiyat.index.intersection(spy.index)
            fiyat, spy = fiyat.loc[ortak], spy.loc[ortak]

            if yontem.startswith("Tek"):
                h_egri, yat = lump_deger(fiyat, tutar, kur)
                s_egri, _   = lump_deger(spy,   tutar, kur)
                ekdca = ""
            else:
                h_egri, yat = dca_deger(fiyat, aylik, artis, kur)
                s_egri, _   = dca_deger(spy,   aylik, artis, kur)
                ekdca = f" (her ay {para(aylik, sembol)}, toplam {para(yat, sembol)} yatırım)"

            h_son, h_get, h_yil = metrik(h_egri, yat)
            s_son, s_get, s_yil = metrik(s_egri, yat)
            kar = h_son - yat
            kz = "kâr" if kar >= 0 else "zarar"
            bas_s, bit_s = bas.strftime("%d.%m.%Y"), bit.strftime("%d.%m.%Y")

            # --- Sonuc cumlesi ---
            sinif = "cumle" if kar >= 0 else "cumle zarar"
            st.markdown(
                f'<div class="{sinif}"><b>{bas_s} – {bit_s}</b> arasında <b>{secilen_ad}</b> '
                f'hissesine <b>{para(yat, sembol)}</b> yatırsaydınız{ekdca}, dönem sonunda '
                f'<b>{para(h_son, sembol)}</b> olurdu — yaklaşık <b>{para(abs(kar), sembol)} {kz}</b> '
                f'({h_get:+.0f}%).</div>', unsafe_allow_html=True)
            st.write("")

            # --- KPI kartlari ---
            def kart(baslik, deger, alt, alt_sinif=""):
                return (f'<div class="kart"><div class="kpi-baslik">{baslik}</div>'
                        f'<div class="kpi-deger">{deger}</div>'
                        f'<div class="kpi-alt {alt_sinif}">{alt}</div></div>')
            k1, k2, k3 = st.columns(3)
            k1.markdown(kart("Dönem sonu değeri", para(h_son, sembol),
                        f"{h_get:+.0f}%", "yesil" if kar >= 0 else "kirmizi"),
                        unsafe_allow_html=True)
            k2.markdown(kart("Yıllık ortalama (yaklaşık)", f"{h_yil:+.1f}%", "yıllık büyüme"),
                        unsafe_allow_html=True)
            fark = h_son - s_son
            k3.markdown(kart("Endekse (SPY) göre", para(s_son, sembol),
                        ("Endeksi geçti ✅" if fark >= 0 else "Endeksin altında ⚠️"),
                        "yesil" if fark >= 0 else "kirmizi"), unsafe_allow_html=True)
            st.write("")

            # --- Etkilesimli grafik ---
            fig = go.Figure()
            fig.add_trace(go.Scatter(x=h_egri.index, y=h_egri.values, name=secilen_ad,
                          line=dict(color="#2563eb", width=2.5),
                          hovertemplate="%{x|%d.%m.%Y}<br>Bu hisse: %{y:,.0f} "+sembol+"<extra></extra>"))
            fig.add_trace(go.Scatter(x=s_egri.index, y=s_egri.values, name="Endeks (SPY)",
                          line=dict(color="#9aa7bd", width=2, dash="dot"),
                          hovertemplate="%{x|%d.%m.%Y}<br>Endeks: %{y:,.0f} "+sembol+"<extra></extra>"))
            fig.update_layout(hovermode="x unified", height=430, margin=dict(l=10, r=10, t=30, b=10),
                              legend=dict(orientation="h", y=1.1), plot_bgcolor="#fff",
                              paper_bgcolor="#fff", yaxis_title="Değer ("+sembol+")")
            st.plotly_chart(fig, use_container_width=True)

            # --- Paylasim ---
            png = ozet_gorseli(secilen_ad, bas_s, bit_s, yat, h_son, h_get, s_son, sembol)
            pc1, pc2 = st.columns(2)
            pc1.download_button("📥 Özet görseli indir (paylaş)", data=png,
                                file_name=f"gecmiste_{secilen}.png", mime="image/png",
                                use_container_width=True)
            tw = "https://twitter.com/intent/tweet?" + urllib.parse.urlencode({
                "text": f"{secilen_ad} hissesine {bas_s}'de {para(yat, sembol)} yatırsaydım "
                        f"bugün {para(h_son, sembol)} olurdu ({h_get:+.0f}%)! #GeçmişteAlsaydın"})
            pc2.link_button("🐦 Twitter'da paylaş", tw, use_container_width=True)
else:
    st.info("👈 Soldaki panelden bilgileri girip **Hesapla**'ya bas. Hızlı denemek için "
            "yukarıdaki hazır senaryo butonlarını da kullanabilirsin.")

st.divider()
with st.expander("ℹ️ Bu araç hakkında / uyarı"):
    st.write("Sadece geçmiş veriye dayalı, eğitim amaçlı bir araçtır. **Yatırım tavsiyesi değildir.** "
             "Tek bir kazanan hisseye bakıp 'kolay para' sanma — o hisseyi önceden seçmek imkânsızdı; "
             "bu yüzden her sonuç endeksle (SPY) kıyaslanır. ₺/€ için tarihsel döviz kuru uygulanır. "
             "Veri kaynağı: Yahoo Finance.")
