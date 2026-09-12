"""
GECMISTE ALSAYDIN? — Surum 5 (Coklu karsilastirma)
------------------------------------------------
- Tek hisse: detayli gorunum (cumle + KPI + paylasim)
- Birden cok hisse: karsilastirma modu (sirali kartlar + tek grafik)
- Sol kontrol paneli, KPI kartlari, etkilesimli Plotly grafik, hazir senaryolar
- DCA (her ay + yillik artis), € / $ / ₺ (gercek kur), her zaman endeks (SPY) kiyasi

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
          padding:18px 20px; box-shadow:0 1px 3px rgba(20,33,61,.06); margin-bottom:8px; }
  .kpi-baslik { color:#6b7280; font-size:13px; font-weight:600; }
  .kpi-deger { font-size:28px; font-weight:800; color:#14213d; margin-top:4px; }
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
 "SPY":"S&P 500 (SPY)","QQQ":"Nasdaq 100 (QQQ)","BTC-USD":"Bitcoin","ETH-USD":"Ethereum",
 "GLD":"Altın (GLD)",
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

# ABD TUFE (CPIAUCSL) — yaklasik yillik (Ocak) degerleri, uygulamaya gomulu.
# Kaynak: FRED. Guvenilirlik icin internetten cekmek yerine gomulu; yeni yil
# ciktikca son degeri guncelleyebilirsin. Reel (enflasyona gore) mod bunu kullanir.
_CPI_YILLIK = {
    2000: 169.3, 2001: 175.6, 2002: 177.7, 2003: 181.7, 2004: 185.2, 2005: 190.7,
    2006: 198.3, 2007: 202.4, 2008: 211.1, 2009: 211.1, 2010: 216.7, 2011: 220.2,
    2012: 226.7, 2013: 230.3, 2014: 233.9, 2015: 233.7, 2016: 236.9, 2017: 242.8,
    2018: 247.9, 2019: 251.7, 2020: 257.9, 2021: 261.6, 2022: 281.1, 2023: 299.2,
    2024: 308.4, 2025: 317.6, 2026: 324.4, 2027: 331.0,
}

@st.cache_data
def cpi_serisi():
    """Gomulu yillik TUFE'yi aylik seriye cevirir (dogrusal ara deger)."""
    s = pd.Series(_CPI_YILLIK)
    s.index = pd.to_datetime([f"{y}-01-01" for y in s.index])
    return s.sort_index().resample("MS").interpolate("linear")

def reel_ayarla(curve, cpi):
    """Nominal degeri, baslangic tarihi alim gucune gore enflasyondan arindirir."""
    if cpi is None: return None
    c = cpi.reindex(curve.index, method="ffill").ffill().bfill()
    if c.isna().all(): return None
    return curve * (float(c.iloc[0]) / c)

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

def kart(baslik, deger, alt, alt_sinif=""):
    return (f'<div class="kart"><div class="kpi-baslik">{baslik}</div>'
            f'<div class="kpi-deger">{deger}</div>'
            f'<div class="kpi-alt {alt_sinif}">{alt}</div></div>')

def ozet_gorseli(ad, bas, bit, yatirilan, son, getiri, s_son, sembol):
    fig, ax = plt.subplots(figsize=(6.4, 3.35), dpi=200)
    fig.patch.set_facecolor("#14213d"); ax.axis("off")
    renk = "#4ade80" if son >= yatirilan else "#f87171"
    ax.text(0.5, 0.90, "Geçmişte Alsaydın?", ha="center", color="#fff",
            fontsize=16, fontweight="bold", transform=ax.transAxes)
    ax.text(0.5, 0.74, f"{ad} · {bas} – {bit}", ha="center", color="#c7d0e0",
            fontsize=10, transform=ax.transAxes)
    ax.text(0.5, 0.50, para(son, sembol), ha="center", color=renk,
            fontsize=30, fontweight="bold", transform=ax.transAxes)
    ax.text(0.5, 0.34, f"{para(yatirilan, sembol)} yatırım → {getiri:+.0f}%",
            ha="center", color="#fff", fontsize=12, transform=ax.transAxes)
    ax.text(0.5, 0.15, f"Aynı para endekste (SPY): {para(s_son, sembol)}",
            ha="center", color="#9aa7bd", fontsize=9, transform=ax.transAxes)
    buf = io.BytesIO(); fig.savefig(buf, format="png", bbox_inches="tight",
                                    facecolor=fig.get_facecolor()); plt.close(fig)
    return buf.getvalue()

RENKLER = ["#2563eb", "#dc2626", "#16a34a", "#d97706", "#7c3aed"]

# ---------- Preset & durum ----------
BUGUN = date.today()
PRESETS = [
    ("🚀 Pandemi başında Apple", dict(k_sorgu="AAPL", k_ekstra="", k_tutar=1000.0, k_sembol="$",
        k_bas=date(2020, 3, 1), k_bit=BUGUN, k_yontem="Tek seferde (baştan hepsi)")),
    ("⚔️ Apple vs Microsoft vs Nvidia", dict(k_sorgu="AAPL", k_ekstra="MSFT, NVDA", k_tutar=1000.0,
        k_sembol="$", k_bas=date(2019, 1, 1), k_bit=BUGUN, k_yontem="Tek seferde (baştan hepsi)")),
    ("🏛️ 2010'dan beri SPY", dict(k_sorgu="SPY", k_ekstra="", k_tutar=1000.0, k_sembol="$",
        k_bas=date(2010, 1, 1), k_bit=BUGUN, k_yontem="Tek seferde (baştan hepsi)")),
]
_def = dict(k_sorgu="Apple", k_ekstra="", k_tutar=1000.0, k_aylik=100.0, k_artis=0, k_sembol="€",
            k_bas=date(2020, 1, 1), k_bit=BUGUN, k_yontem="Tek seferde (baştan hepsi)")
for k, v in _def.items():
    st.session_state.setdefault(k, v)

# ---------- SIDEBAR ----------
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

    katalog = [f"{ad} ({tk})" for tk, ad in POPULER.items()]
    katalog_map = {f"{ad} ({tk})": tk for tk, ad in POPULER.items()}
    secili_etk = st.multiselect("Karşılaştır (listeden seç)", katalog,
                                help="Aynı grafikte kıyaslamak için şirket ekle (yazınca filtreler).")
    ekstra = st.text_input("Listede yoksa kod yaz (virgülle)", key="k_ekstra",
                           help="Örn. GOOGL, BTC-USD. Boş bırakabilirsin.")

    sembol = st.selectbox("Para birimi", ["€", "$", "₺"], key="k_sembol")
    reel = st.checkbox("Enflasyona göre (reel) göster",
                       help="ABD TÜFE ile enflasyondan arındırılmış gerçek alım gücü.")
    yontem = st.radio("Yatırım şekli", ["Tek seferde (baştan hepsi)",
                      "Aylara yayarak (her ay biraz)"], key="k_yontem")
    if yontem.startswith("Tek"):
        tutar = st.number_input("Yatırılan tutar", min_value=1.0, step=100.0, key="k_tutar")
        aylik = artis = None
    else:
        aylik = st.number_input("Her ay ne kadar?", min_value=1.0, step=50.0, key="k_aylik")
        artis = st.slider("Her yıl katkıyı artır (%)", 0, 30, key="k_artis") / 100.0

    c_b, c_e = st.columns(2)
    bas = c_b.date_input("Başlangıç", key="k_bas", min_value=date(2000, 1, 1), max_value=BUGUN)
    bit = c_e.date_input("Bitiş", key="k_bit", min_value=date(2000, 1, 2), max_value=BUGUN)
    hesapla = st.button("Hesapla", type="primary", use_container_width=True)

# ---------- ANA ALAN ----------
st.title("📈 Geçmişte Alsaydın?")
st.caption("Soldaki panelden bir (veya birkaç) şirket, tutar ve tarih seç. Sonuç her zaman "
           "borsa endeksi (SPY) ile karşılaştırılır. Yatırım tavsiyesi değildir; geçmişi gösterir.")

def hesapla_egri(fiyat_usd):
    if yontem.startswith("Tek"):
        return lump_deger(fiyat_usd, tutar, kur)
    return dca_deger(fiyat_usd, aylik, artis, kur)

def ad_ver(kod):
    if kod == secilen: return secilen_ad
    return POPULER.get(kod, kod)

if hesapla:
    if bas >= bit:
        st.error("Başlangıç tarihi, bitiş tarihinden önce olmalı.")
    else:
        kodlar = ([secilen] + [katalog_map[e] for e in secili_etk]
                  + [x.strip().upper() for x in ekstra.split(",") if x.strip()])
        gor = set(); kodlar = [k for k in kodlar if k and not (k in gor or gor.add(k))][:5]
        with st.spinner("Hesaplanıyor..."):
            ham = {k: fiyat_indir(k, bas, bit) for k in kodlar}
            spy = fiyat_indir("SPY", bas, bit)
            kur = kur_serisi(sembol, bas, bit)
            cpi = cpi_serisi() if reel else None
        ham = {k: v for k, v in ham.items() if v is not None}
        if not ham or spy is None:
            st.error("Veri bulunamadı. Hisse adını/kodunu kontrol et.")
        else:
            if sembol != "$" and kur is None:
                st.caption("Not: Kur verisi alınamadı; sonuç dolar bazlı gösteriliyor.")
            eksikler = [k for k in kodlar if k not in ham]
            if eksikler:
                st.caption("Bulunamayan ve atlanan: " + ", ".join(eksikler))
            reel_aktif = reel and cpi is not None
            if reel and not reel_aktif:
                st.caption("Not: Enflasyon (TÜFE) verisi alınamadı; nominal gösteriliyor.")

            ortak = spy.index
            for v in ham.values():
                ortak = ortak.intersection(v.index)
            spy = spy.loc[ortak]

            def belki_reel(curve):
                if reel_aktif:
                    r = reel_ayarla(curve, cpi)
                    if r is not None: return r
                return curve

            spy_egri, yat = hesapla_egri(spy); spy_egri = belki_reel(spy_egri)
            s_son = float(spy_egri.iloc[-1])

            def _hesap(v):
                e, y = hesapla_egri(v.loc[ortak]); e = belki_reel(e)
                return e, y, metrik(e, y)
            hesap = {k: _hesap(v) for k, v in ham.items()}
            bas_s, bit_s = bas.strftime("%d.%m.%Y"), bit.strftime("%d.%m.%Y")
            if reel_aktif:
                st.caption(f"🔎 Reel mod açık: değerler ABD enflasyonundan arındırıldı "
                           f"({bas_s} alım gücüne göre).")

            # =============== TEK HISSE: DETAYLI GORUNUM ===============
            if len(hesap) == 1:
                k = next(iter(hesap)); h_egri, y, (h_son, h_get, h_yil) = hesap[k]
                kar = h_son - y; kz = "kâr" if kar >= 0 else "zarar"
                ekdca = (f" (her ay {para(aylik, sembol)}, toplam {para(y, sembol)})"
                         if not yontem.startswith("Tek") else "")
                sinif = "cumle" if kar >= 0 else "cumle zarar"
                st.markdown(
                    f'<div class="{sinif}"><b>{bas_s} – {bit_s}</b> arasında <b>{ad_ver(k)}</b> '
                    f'hissesine <b>{para(y, sembol)}</b> yatırsaydınız{ekdca}, dönem sonunda '
                    f'<b>{para(h_son, sembol)}</b> olurdu — yaklaşık <b>{para(abs(kar), sembol)} {kz}</b> '
                    f'({h_get:+.0f}%).</div>', unsafe_allow_html=True)
                st.write("")
                c1, c2, c3 = st.columns(3)
                c1.markdown(kart("Dönem sonu değeri", para(h_son, sembol), f"{h_get:+.0f}%",
                            "yesil" if kar >= 0 else "kirmizi"), unsafe_allow_html=True)
                c2.markdown(kart("Yıllık ortalama (yaklaşık)", f"{h_yil:+.1f}%", "yıllık büyüme"),
                            unsafe_allow_html=True)
                c3.markdown(kart("Endekse (SPY) göre", para(s_son, sembol),
                            "Endeksi geçti ✅" if h_son >= s_son else "Endeksin altında ⚠️",
                            "yesil" if h_son >= s_son else "kirmizi"), unsafe_allow_html=True)
                st.write("")
                seriler = [(ad_ver(k), h_egri)]
                png = ozet_gorseli(ad_ver(k), bas_s, bit_s, y, h_son, h_get, s_son, sembol)
            # =============== COKLU: KARSILASTIRMA ===============
            else:
                sirali = sorted(hesap.items(), key=lambda kv: kv[1][2][0], reverse=True)
                st.markdown(f'<div class="cumle"><b>{bas_s} – {bit_s}</b> arasında '
                            f'<b>{para(yat, sembol)}</b> yatırımla en çok kazandıran: '
                            f'<b>{ad_ver(sirali[0][0])}</b> ({sirali[0][1][2][1]:+.0f}%).</div>',
                            unsafe_allow_html=True)
                st.write("")
                sutunlar = st.columns(len(sirali) + 1)
                for idx, (k, (egri, y, (son, get, yil))) in enumerate(sirali):
                    tac = "🏆 " if idx == 0 else ""
                    sutunlar[idx].markdown(kart(f"{tac}{ad_ver(k)}", para(son, sembol),
                        f"{get:+.0f}%", "yesil" if son >= y else "kirmizi"), unsafe_allow_html=True)
                sutunlar[-1].markdown(kart("Endeks (SPY)", para(s_son, sembol),
                    f"{(s_son - yat) / yat * 100:+.0f}%"), unsafe_allow_html=True)
                st.write("")
                seriler = [(ad_ver(k), egri) for k, (egri, _, _) in sirali]
                png = None

            # --- Ortak grafik (tek veya coklu) ---
            fig = go.Figure()
            for idx, (ad, egri) in enumerate(seriler):
                fig.add_trace(go.Scatter(x=egri.index, y=egri.values, name=ad,
                    line=dict(color=RENKLER[idx % len(RENKLER)], width=2.5),
                    hovertemplate="%{x|%d.%m.%Y}<br>"+ad+": %{y:,.0f} "+sembol+"<extra></extra>"))
            fig.add_trace(go.Scatter(x=spy_egri.index, y=spy_egri.values, name="Endeks (SPY)",
                line=dict(color="#9aa7bd", width=2, dash="dot"),
                hovertemplate="%{x|%d.%m.%Y}<br>Endeks: %{y:,.0f} "+sembol+"<extra></extra>"))
            fig.update_layout(hovermode="x unified", height=450, margin=dict(l=10, r=10, t=30, b=10),
                legend=dict(orientation="h", y=1.12), plot_bgcolor="#fff", paper_bgcolor="#fff",
                yaxis_title="Değer (" + sembol + ")")
            st.plotly_chart(fig, use_container_width=True)

            # --- Paylasim (yalnizca tek hisse) ---
            if png is not None:
                p1, p2 = st.columns(2)
                p1.download_button("📥 Özet görseli indir (paylaş)", data=png,
                    file_name=f"gecmiste_{secilen}.png", mime="image/png", use_container_width=True)
                tw = "https://twitter.com/intent/tweet?" + urllib.parse.urlencode({
                    "text": f"{secilen_ad} hissesine {bas_s}'de {para(yat, sembol)} yatırsaydım "
                            f"bugün {para(s_son, sembol)}... #GeçmişteAlsaydın"})
                p2.link_button("🐦 Twitter'da paylaş", tw, use_container_width=True)
else:
    st.info("👈 Soldaki panelden bilgileri girip **Hesapla**'ya bas. Birden çok hisseyi "
            "karşılaştırmak için “Karşılaştır” kutusuna kod ekle (örn. MSFT, NVDA). "
            "Hızlı denemek için yukarıdaki hazır senaryoları kullan.")

st.divider()
with st.expander("ℹ️ Bu araç hakkında / uyarı"):
    st.write("Sadece geçmiş veriye dayalı, eğitim amaçlı bir araçtır. **Yatırım tavsiyesi değildir.** "
             "Tek bir kazanan hisseye bakıp 'kolay para' sanma — o hisseyi önceden seçmek imkânsızdı; "
             "bu yüzden her sonuç endeksle (SPY) kıyaslanır. ₺/€ için tarihsel döviz kuru uygulanır. "
             "Veri kaynağı: Yahoo Finance.")
