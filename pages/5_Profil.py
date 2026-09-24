"""
PROFIL (cok dilli)
------------------------------------------------
- Giris yapan kullanici kendi profilini olusturur/duzenler (kullanici adi + bio).
- Herkes ?u=kullanici_adi ile bir profili goruntuleyebilir. E-posta asla gosterilmez.
Dil ana sayfayla senkron (st.session_state['dil_ad']).
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

DILLER = {"Türkçe": "tr", "English": "en", "Deutsch": "de",
          "Русский": "ru", "Español": "es", "العربية": "ar"}
st.session_state.setdefault("dil_ad", "Türkçe")
lang = DILLER.get(st.session_state["dil_ad"], "tr")

T = {
 "tr": dict(pub_title="🙍 Profil", not_found="'{u}' adlı kullanıcı bulunamadı.",
   mine_hint="Bu senin profilin. Düzenlemek için adres çubuğundan `?u=` kısmını kaldır.",
   posts="Paylaşımları", my_title="🙍 Profilim", login="Profil oluşturmak için Google ile giriş yap.",
   login_btn="Google ile giriş yap", logout="Çıkış yap", info="**Profil bilgilerin**",
   uname="Kullanıcı adı", uname_help="Herkese görünür. Harf, rakam ve alt çizgi kullan.",
   bio="Kısa bio (opsiyonel)", bio_ph="Kendini bir cümleyle tanıt...", save="Kaydet",
   e_short3="Kullanıcı adı en az 3 karakter olmalı.",
   e_chars="Sadece harf, rakam ve _ - . kullanılabilir (boşluk yok).",
   e_taken="Bu kullanıcı adı alınmış, başka bir tane dene.", saved="✅ Profil kaydedildi.",
   link="Herkese açık profil bağlantın: bu sayfa `?u={u}` ile açılır.", my_posts="Paylaşımlarım",
   load_err="Paylaşımlar yüklenemedi: ", read_err="Profil okunamadı: ", empty="Henüz paylaşım yok.",
   mn="dk", hr="sa", dy="gün"),
 "en": dict(pub_title="🙍 Profile", not_found="User '{u}' not found.",
   mine_hint="This is your profile. Remove `?u=` from the address bar to edit.",
   posts="Posts", my_title="🙍 My profile", login="Sign in with Google to create a profile.",
   login_btn="Sign in with Google", logout="Log out", info="**Your profile**",
   uname="Username", uname_help="Visible to everyone. Use letters, digits and underscore.",
   bio="Short bio (optional)", bio_ph="Introduce yourself in one line...", save="Save",
   e_short3="Username must be at least 3 characters.",
   e_chars="Only letters, digits and _ - . (no spaces).",
   e_taken="That username is taken, try another.", saved="✅ Profile saved.",
   link="Your public profile link: this page opens with `?u={u}`.", my_posts="My posts",
   load_err="Could not load posts: ", read_err="Could not read profile: ", empty="No posts yet.",
   mn="min", hr="h", dy="d"),
 "de": dict(pub_title="🙍 Profil", not_found="Benutzer '{u}' nicht gefunden.",
   mine_hint="Das ist dein Profil. Entferne `?u=` aus der Adresszeile zum Bearbeiten.",
   posts="Beiträge", my_title="🙍 Mein Profil", login="Melde dich mit Google an, um ein Profil zu erstellen.",
   login_btn="Mit Google anmelden", logout="Abmelden", info="**Dein Profil**",
   uname="Benutzername", uname_help="Für alle sichtbar. Buchstaben, Ziffern und Unterstrich.",
   bio="Kurze Bio (optional)", bio_ph="Stell dich in einem Satz vor...", save="Speichern",
   e_short3="Benutzername mindestens 3 Zeichen.",
   e_chars="Nur Buchstaben, Ziffern und _ - . (keine Leerzeichen).",
   e_taken="Benutzername vergeben, wähle einen anderen.", saved="✅ Profil gespeichert.",
   link="Dein öffentlicher Link: diese Seite öffnet mit `?u={u}`.", my_posts="Meine Beiträge",
   load_err="Beiträge nicht ladbar: ", read_err="Profil nicht lesbar: ", empty="Noch keine Beiträge.",
   mn="Min", hr="Std", dy="T"),
 "ru": dict(pub_title="🙍 Профиль", not_found="Пользователь '{u}' не найден.",
   mine_hint="Это ваш профиль. Уберите `?u=` из адресной строки для редактирования.",
   posts="Публикации", my_title="🙍 Мой профиль", login="Войдите через Google, чтобы создать профиль.",
   login_btn="Войти через Google", logout="Выйти", info="**Ваш профиль**",
   uname="Имя пользователя", uname_help="Видно всем. Буквы, цифры и подчёркивание.",
   bio="Краткое био (необ.)", bio_ph="Расскажите о себе одной строкой...", save="Сохранить",
   e_short3="Имя минимум 3 символа.",
   e_chars="Только буквы, цифры и _ - . (без пробелов).",
   e_taken="Имя занято, выберите другое.", saved="✅ Профиль сохранён.",
   link="Ваша публичная ссылка: страница открывается с `?u={u}`.", my_posts="Мои публикации",
   load_err="Не удалось загрузить публикации: ", read_err="Не удалось прочитать профиль: ", empty="Пока нет публикаций.",
   mn="мин", hr="ч", dy="д"),
 "es": dict(pub_title="🙍 Perfil", not_found="Usuario '{u}' no encontrado.",
   mine_hint="Este es tu perfil. Quita `?u=` de la barra de direcciones para editar.",
   posts="Publicaciones", my_title="🙍 Mi perfil", login="Inicia sesión con Google para crear un perfil.",
   login_btn="Iniciar sesión con Google", logout="Cerrar sesión", info="**Tu perfil**",
   uname="Nombre de usuario", uname_help="Visible para todos. Letras, dígitos y guion bajo.",
   bio="Bio corta (opcional)", bio_ph="Preséntate en una línea...", save="Guardar",
   e_short3="El usuario debe tener al menos 3 caracteres.",
   e_chars="Solo letras, dígitos y _ - . (sin espacios).",
   e_taken="Ese usuario ya existe, prueba otro.", saved="✅ Perfil guardado.",
   link="Tu enlace público: esta página abre con `?u={u}`.", my_posts="Mis publicaciones",
   load_err="No se pudieron cargar las publicaciones: ", read_err="No se pudo leer el perfil: ", empty="Aún no hay publicaciones.",
   mn="min", hr="h", dy="d"),
 "ar": dict(pub_title="🙍 الملف الشخصي", not_found="المستخدم '{u}' غير موجود.",
   mine_hint="هذا ملفك. أزل `?u=` من شريط العنوان للتعديل.",
   posts="المنشورات", my_title="🙍 ملفي", login="سجّل الدخول عبر Google لإنشاء ملف.",
   login_btn="تسجيل الدخول عبر Google", logout="تسجيل الخروج", info="**ملفك الشخصي**",
   uname="اسم المستخدم", uname_help="مرئي للجميع. أحرف وأرقام وشرطة سفلية.",
   bio="نبذة قصيرة (اختياري)", bio_ph="عرّف بنفسك في سطر...", save="حفظ",
   e_short3="اسم المستخدم 3 أحرف على الأقل.",
   e_chars="أحرف وأرقام و _ - . فقط (بدون مسافات).",
   e_taken="الاسم مأخوذ، جرّب غيره.", saved="✅ تم حفظ الملف.",
   link="رابطك العام: تُفتح الصفحة بـ `?u={u}`.", my_posts="منشوراتي",
   load_err="تعذّر تحميل المنشورات: ", read_err="تعذّر قراءة الملف: ", empty="لا منشورات بعد.",
   mn="د", hr="س", dy="ي"),
}
L = T[lang]

_u = getattr(st, "user", None)
GIRIS = bool(_u and _u.is_logged_in)
EMAIL = st.user.email if GIRIS else ""


def zaman(dt):
    if not isinstance(dt, datetime):
        return ""
    try:
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        s = int((datetime.now(timezone.utc) - dt).total_seconds())
        if s < 3600: return f"{max(1, s // 60)} {L['mn']}"
        if s < 86400: return f"{s // 3600} {L['hr']}"
        return f"{s // 86400} {L['dy']}"
    except Exception:
        return ""


def paylasimlari_goster(kullanici_email):
    try:
        pler = db.paylasimlar_getir(email=EMAIL, sirala="yeni", limit=50,
                                    kullanici_email=kullanici_email)
    except Exception as e:
        st.error(L["load_err"] + str(e))
        return
    if not pler:
        st.info(L["empty"])
        return
    for p in pler:
        with st.container(border=True):
            tk = f" · `{p['ticker']}`" if p["ticker"] else ""
            st.markdown(f"**{p['baslik']}**{tk}")
            st.caption(f"{zaman(p['olusturuldu'])} · 👍 {p['begeni']} · 👎 {p['begenme']} · 💬 {p['yorum_sayi']}")
            st.write(p["metin"])


# ---------- Herkese acik profil (?u=...) ----------
bakilan = st.query_params.get("u", "")

if bakilan:
    try:
        hedef_email = db.profil_email_bul(bakilan)
    except Exception:
        hedef_email = None
    if not hedef_email:
        st.title(L["pub_title"])
        st.warning(L["not_found"].format(u=bakilan))
        st.stop()
    prof = db.profil_getir(hedef_email) or {}
    st.title(f"🙍 {prof.get('kullanici_adi', bakilan)}")
    if prof.get("bio"):
        st.caption(prof["bio"])
    if GIRIS and hedef_email == EMAIL:
        st.info(L["mine_hint"])
    st.divider()
    st.subheader(L["posts"])
    paylasimlari_goster(hedef_email)
    st.stop()

# ---------- Kendi profilim ----------
st.title(L["my_title"])

if not GIRIS:
    st.info(L["login"])
    if st.button(L["login_btn"], type="primary"):
        st.login()
    st.stop()

with st.sidebar:
    st.caption(f"👤 {EMAIL}")
    if st.button(L["logout"], width="stretch"):
        st.logout()

prof = None
try:
    prof = db.profil_getir(EMAIL)
except Exception as e:
    st.error(L["read_err"] + str(e))

mevcut_ad = prof["kullanici_adi"] if prof else ""
mevcut_bio = prof["bio"] if prof else ""

with st.form("profil"):
    st.markdown(L["info"])
    ad = st.text_input(L["uname"], value=mevcut_ad, max_chars=24, help=L["uname_help"])
    bio = st.text_area(L["bio"], value=mevcut_bio, max_chars=200, placeholder=L["bio_ph"])
    if st.form_submit_button(L["save"], type="primary"):
        ad_t = (ad or "").strip()
        if len(ad_t) < 3:
            st.error(L["e_short3"])
        elif not all(c.isalnum() or c in "_-." for c in ad_t):
            st.error(L["e_chars"])
        elif not db.kullanici_adi_musait(ad_t, EMAIL):
            st.error(L["e_taken"])
        else:
            db.profil_kaydet(EMAIL, ad_t, bio)
            st.success(L["saved"])
            st.rerun()

if prof and prof.get("kullanici_adi"):
    st.caption(L["link"].format(u=prof["kullanici_adi"]))
    st.divider()
    st.subheader(L["my_posts"])
    paylasimlari_goster(EMAIL)
