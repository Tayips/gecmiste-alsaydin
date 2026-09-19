"""
FIKIRLER / TOPLULUK
------------------------------------------------
Kullanicilar yatirim fikri paylasir; digerleri begenir/begenmez ve yorum yapar.
Okuma herkese aciktir; paylasim/begeni/yorum icin Google girisi gerekir.

ONEMLI: Buradaki icerikler kullanicilarin kisisel gorusleridir; YATIRIM TAVSIYESI DEGILDIR.
"""
import streamlit as st
from datetime import datetime, timezone
import db

try:
    st.set_page_config(page_title="Fikirler — WhatIfInvest", page_icon="assets/favicon.png", layout="wide")
except Exception:
    st.set_page_config(page_title="Fikirler — WhatIfInvest", page_icon="💡", layout="wide")
try:
    st.logo("assets/logo_lockup.png", size="large", icon_image="assets/favicon.png")
except Exception:
    pass

# ---------- Giris durumu (okuma herkese acik) ----------
_u = getattr(st, "user", None)
GIRIS = bool(_u and _u.is_logged_in)
EMAIL = st.user.email if GIRIS else ""


def zaman(dt):
    """Basit 'x once' metni."""
    if not isinstance(dt, datetime):
        return ""
    try:
        simdi = datetime.now(timezone.utc)
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        fark = simdi - dt
        s = int(fark.total_seconds())
        if s < 60: return "az önce"
        if s < 3600: return f"{s // 60} dk önce"
        if s < 86400: return f"{s // 3600} sa önce"
        return f"{s // 86400} gün önce"
    except Exception:
        return ""


st.title("💡 Fikirler")
st.caption("Yatırım fikirlerini paylaş, başkalarınınkini gör. "
           "⚠️ Buradaki içerikler kullanıcı görüşleridir, **yatırım tavsiyesi değildir**.")

# ---------- Kenar cubugu: giris / profil / siralama ----------
with st.sidebar:
    if GIRIS:
        prof = None
        try:
            prof = db.profil_getir(EMAIL)
        except Exception:
            prof = None
        ad = prof["kullanici_adi"] if prof else "(kullanıcı adı yok)"
        st.caption(f"👤 {ad}")
        if st.button("Çıkış yap", width="stretch"):
            st.logout()
    else:
        st.info("Paylaşım, beğeni ve yorum için giriş yap.")
        if st.button("Google ile giriş yap", type="primary", width="stretch"):
            st.login()
    st.divider()
    sirala = st.radio("Sırala", ["🆕 En yeni", "🔥 En popüler"], index=0)
sirala_kod = "populer" if "popüler" in sirala else "yeni"

# ---------- Yeni paylasim ----------
if GIRIS:
    prof = None
    try:
        prof = db.profil_getir(EMAIL)
    except Exception:
        prof = None
    if not prof or not prof.get("kullanici_adi"):
        st.warning("Paylaşım yapmadan önce bir **kullanıcı adı** belirlemelisin.")
        with st.form("hizli_profil", clear_on_submit=False):
            yeni_ad = st.text_input("Kullanıcı adın", max_chars=24,
                                    placeholder="örn. yatirimci_tayyip")
            if st.form_submit_button("Kaydet", type="primary"):
                ad_t = (yeni_ad or "").strip()
                if len(ad_t) < 3:
                    st.error("En az 3 karakter olmalı.")
                elif not db.kullanici_adi_musait(ad_t, EMAIL):
                    st.error("Bu kullanıcı adı alınmış, başka bir tane dene.")
                else:
                    db.profil_kaydet(EMAIL, ad_t, "")
                    st.rerun()
    else:
        with st.expander("➕ Yeni fikir paylaş", expanded=False):
            with st.form("yeni_paylasim", clear_on_submit=True):
                c = st.columns([3, 1])
                baslik = c[0].text_input("Başlık", max_chars=120,
                                         placeholder="örn. Neden uzun vadede X'e inanıyorum")
                ticker = c[1].text_input("Hisse (ops.)", max_chars=12, placeholder="AAPL")
                metin = st.text_area("Fikrin", max_chars=2000,
                                     placeholder="Tezini, gerekçeni ve risklerini yaz...")
                st.caption("Lütfen saygılı ol ve manipülasyondan kaçın. Yatırım tavsiyesi verme.")
                if st.form_submit_button("Paylaş", type="primary"):
                    if len((baslik or "").strip()) < 5:
                        st.error("Başlık en az 5 karakter olmalı.")
                    elif len((metin or "").strip()) < 10:
                        st.error("Fikir metni en az 10 karakter olmalı.")
                    else:
                        db.paylasim_ekle(EMAIL, ticker, baslik, metin)
                        st.success("✅ Paylaşıldı.")
                        st.rerun()

st.divider()

# ---------- Akis ----------
try:
    paylasimlar = db.paylasimlar_getir(email=EMAIL, sirala=sirala_kod, limit=60)
except Exception as e:
    st.error("Akış yüklenemedi: " + str(e))
    st.stop()

if not paylasimlar:
    st.info("Henüz paylaşım yok. İlk fikri sen paylaş!")
    st.stop()

for p in paylasimlar:
    with st.container(border=True):
        ust = st.columns([6, 2])
        tk = f" · `{p['ticker']}`" if p["ticker"] else ""
        ust[0].markdown(f"**{p['baslik']}**{tk}")
        ust[1].caption(f"👤 {p['ad']} · {zaman(p['olusturuldu'])}")
        st.write(p["metin"])

        # Begeni / begenmeme / yorum sayaci
        b = st.columns([1, 1, 2, 1, 1])
        like_tip = "primary" if p["benim_oyum"] == 1 else "secondary"
        dis_tip = "primary" if p["benim_oyum"] == -1 else "secondary"
        if b[0].button(f"👍 {p['begeni']}", key=f"like_{p['id']}", type=like_tip, width="stretch"):
            if GIRIS:
                db.begeni_ver(p["id"], EMAIL, 1); st.rerun()
            else:
                st.toast("Beğenmek için giriş yap.")
        if b[1].button(f"👎 {p['begenme']}", key=f"dis_{p['id']}", type=dis_tip, width="stretch"):
            if GIRIS:
                db.begeni_ver(p["id"], EMAIL, -1); st.rerun()
            else:
                st.toast("Oy vermek için giriş yap.")
        # Kendi paylasimini sil
        if GIRIS and p["sahip_email"] == EMAIL:
            if b[3].button("🗑️", key=f"psil_{p['id']}", help="Paylaşımını sil", width="stretch"):
                db.paylasim_sil(p["id"], EMAIL); st.rerun()
        # Bildir
        if GIRIS and p["sahip_email"] != EMAIL:
            if b[4].button("⚠️", key=f"prapor_{p['id']}", help="Uygunsuz içeriği bildir", width="stretch"):
                db.rapor_ekle(EMAIL, paylasim_id=p["id"], sebep="paylasim bildirimi")
                st.toast("Bildirildi, teşekkürler.")

        # Yorumlar
        with st.expander(f"💬 {p['yorum_sayi']} yorum"):
            try:
                yorumlar = db.yorumlar_getir(p["id"])
            except Exception:
                yorumlar = []
            for y in yorumlar:
                yc = st.columns([8, 1])
                yc[0].markdown(f"**{y['ad']}** · {zaman(y['olusturuldu'])}  \n{y['metin']}")
                if GIRIS and y["sahip_email"] == EMAIL:
                    if yc[1].button("🗑️", key=f"ysil_{y['id']}", help="Yorumunu sil"):
                        db.yorum_sil(y["id"], EMAIL); st.rerun()
            if GIRIS:
                yeni_yorum = st.text_input("Yorum yaz", key=f"yeni_yorum_{p['id']}",
                                           max_chars=500, placeholder="Görüşünü yaz...")
                if st.button("Gönder", key=f"yorum_gonder_{p['id']}"):
                    if len((yeni_yorum or "").strip()) >= 2:
                        db.yorum_ekle(p["id"], EMAIL, yeni_yorum); st.rerun()
                    else:
                        st.warning("Yorum çok kısa.")
            else:
                st.caption("Yorum yapmak için giriş yap.")

st.divider()
st.caption("⚠️ Sorumluluk reddi: Buradaki paylaşımlar kullanıcıların kişisel görüşleridir ve "
           "yatırım tavsiyesi değildir. Yatırım kararların için kendi araştırmanı yap.")
