"""
PROFIL
------------------------------------------------
- Giris yapan kullanici kendi profilini olusturur/duzenler (kullanici adi + bio).
- Herkes bir kullanicinin profilini ?u=kullanici_adi ile goruntuleyebilir (paylasimlari).
E-posta asla gosterilmez.
"""
import streamlit as st
from datetime import datetime, timezone
import db

try:
    st.set_page_config(page_title="Profil — WhatIfInvest", page_icon="assets/favicon.png", layout="wide")
except Exception:
    st.set_page_config(page_title="Profil — WhatIfInvest", page_icon="🙍", layout="wide")
try:
    st.logo("assets/logo_lockup.png", size="large", icon_image="assets/favicon.png")
except Exception:
    pass

_u = getattr(st, "user", None)
GIRIS = bool(_u and _u.is_logged_in)
EMAIL = st.user.email if GIRIS else ""


def zaman(dt):
    if not isinstance(dt, datetime):
        return ""
    try:
        s = int((datetime.now(timezone.utc) - (dt if dt.tzinfo else dt.replace(tzinfo=timezone.utc))).total_seconds())
        if s < 3600: return f"{max(1, s // 60)} dk önce"
        if s < 86400: return f"{s // 3600} sa önce"
        return f"{s // 86400} gün önce"
    except Exception:
        return ""


def paylasimlari_goster(kullanici_email):
    try:
        pler = db.paylasimlar_getir(email=EMAIL, sirala="yeni", limit=50,
                                    kullanici_email=kullanici_email)
    except Exception as e:
        st.error("Paylaşımlar yüklenemedi: " + str(e))
        return
    if not pler:
        st.info("Henüz paylaşım yok.")
        return
    for p in pler:
        with st.container(border=True):
            tk = f" · `{p['ticker']}`" if p["ticker"] else ""
            st.markdown(f"**{p['baslik']}**{tk}")
            st.caption(f"{zaman(p['olusturuldu'])} · 👍 {p['begeni']} · 👎 {p['begenme']} · 💬 {p['yorum_sayi']}")
            st.write(p["metin"])


# ---------- Herkese acik profil goruntuleme (?u=kullanici_adi) ----------
bakilan = st.query_params.get("u", "")

if bakilan:
    hedef_email = None
    try:
        hedef_email = db.profil_email_bul(bakilan)
    except Exception:
        hedef_email = None
    if not hedef_email:
        st.title("🙍 Profil")
        st.warning(f"'{bakilan}' adlı kullanıcı bulunamadı.")
        st.stop()
    prof = db.profil_getir(hedef_email) or {}
    st.title(f"🙍 {prof.get('kullanici_adi', bakilan)}")
    if prof.get("bio"):
        st.caption(prof["bio"])
    if GIRIS and hedef_email == EMAIL:
        st.info("Bu senin profilin. Düzenlemek için üstteki adres çubuğundan `?u=` kısmını kaldır "
                "ya da menüden **Profil**'e tekrar gir.")
    st.divider()
    st.subheader("Paylaşımları")
    paylasimlari_goster(hedef_email)
    st.stop()

# ---------- Kendi profilim ----------
st.title("🙍 Profilim")

if not GIRIS:
    st.info("Profil oluşturmak için Google ile giriş yap.")
    if st.button("Google ile giriş yap", type="primary"):
        st.login()
    st.stop()

with st.sidebar:
    st.caption(f"👤 {EMAIL}")
    if st.button("Çıkış yap", width="stretch"):
        st.logout()

prof = None
try:
    prof = db.profil_getir(EMAIL)
except Exception as e:
    st.error("Profil okunamadı: " + str(e))

mevcut_ad = prof["kullanici_adi"] if prof else ""
mevcut_bio = prof["bio"] if prof else ""

with st.form("profil"):
    st.markdown("**Profil bilgilerin**")
    ad = st.text_input("Kullanıcı adı", value=mevcut_ad, max_chars=24,
                       help="Herkese görünür. Harf, rakam ve alt çizgi kullan.")
    bio = st.text_area("Kısa bio (opsiyonel)", value=mevcut_bio, max_chars=200,
                       placeholder="Kendini bir cümleyle tanıt...")
    if st.form_submit_button("Kaydet", type="primary"):
        ad_t = (ad or "").strip()
        if len(ad_t) < 3:
            st.error("Kullanıcı adı en az 3 karakter olmalı.")
        elif not all(c.isalnum() or c in "_-." for c in ad_t):
            st.error("Sadece harf, rakam ve _ - . kullanılabilir (boşluk yok).")
        elif not db.kullanici_adi_musait(ad_t, EMAIL):
            st.error("Bu kullanıcı adı alınmış, başka bir tane dene.")
        else:
            db.profil_kaydet(EMAIL, ad_t, bio)
            st.success("✅ Profil kaydedildi.")
            st.rerun()

if prof and prof.get("kullanici_adi"):
    st.caption(f"Herkese açık profil bağlantın: bu sayfa `?u={prof['kullanici_adi']}` ile açılır.")
    st.divider()
    st.subheader("Paylaşımlarım")
    paylasimlari_goster(EMAIL)
