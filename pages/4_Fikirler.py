"""
FIKIRLER / TOPLULUK (cok dilli)
------------------------------------------------
Kullanicilar yatirim fikri paylasir; digerleri begenir/begenmez ve yorum yapar.
Okuma herkese aciktir; paylasim/begeni/yorum icin Google girisi gerekir.
Dil ana sayfayla senkron (st.session_state['dil_ad']).
ONEMLI: Icerikler kullanici gorusleridir; YATIRIM TAVSIYESI DEGILDIR.
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

DILLER = {"Türkçe": "tr", "English": "en", "Deutsch": "de",
          "Русский": "ru", "Español": "es", "العربية": "ar"}
st.session_state.setdefault("dil_ad", "Türkçe")
lang = DILLER.get(st.session_state["dil_ad"], "tr")

T = {
 "tr": dict(title="💡 Fikirler",
   intro="Yatırım fikirlerini paylaş, başkalarınınkini gör. ⚠️ İçerikler kullanıcı görüşleridir, **yatırım tavsiyesi değildir**.",
   s_login="Paylaşım, beğeni ve yorum için giriş yap.", login_btn="Google ile giriş yap", logout="Çıkış yap",
   sort="Sırala", s_new="🆕 En yeni", s_pop="🔥 En popüler", no_uname="(kullanıcı adı yok)",
   uname_warn="Paylaşım yapmadan önce bir **kullanıcı adı** belirlemelisin.", uname_lbl="Kullanıcı adın",
   uname_ph="örn. yatirimci_tayyip", save="Kaydet", e_short3="En az 3 karakter olmalı.",
   e_taken="Bu kullanıcı adı alınmış, başka bir tane dene.",
   new_exp="➕ Yeni fikir paylaş", b_lbl="Başlık", b_ph="örn. Neden uzun vadede X'e inanıyorum",
   tk_lbl="Hisse (ops.)", tk_ph="AAPL", m_lbl="Fikrin", m_ph="Tezini, gerekçeni ve risklerini yaz...",
   rules="Lütfen saygılı ol ve manipülasyondan kaçın. Yatırım tavsiyesi verme.", share="Paylaş",
   e_b5="Başlık en az 5 karakter olmalı.", e_m10="Fikir metni en az 10 karakter olmalı.", shared_ok="✅ Paylaşıldı.",
   feed_err="Akış yüklenemedi: ", empty="Henüz paylaşım yok. İlk fikri sen paylaş!",
   t_like="Beğenmek için giriş yap.", t_vote="Oy vermek için giriş yap.",
   del_p="Paylaşımını sil", rep_p="Uygunsuz içeriği bildir", rep_ok="Bildirildi, teşekkürler.",
   comments="yorum", del_c="Yorumunu sil", c_lbl="Yorum yaz", c_ph="Görüşünü yaz...", send="Gönder",
   c_short="Yorum çok kısa.", c_login="Yorum yapmak için giriş yap.",
   disc="⚠️ Sorumluluk reddi: Paylaşımlar kullanıcıların kişisel görüşleridir ve yatırım tavsiyesi değildir. Kendi araştırmanı yap.",
   now="az önce", mn="dk önce", hr="sa önce", dy="gün önce"),
 "en": dict(title="💡 Ideas",
   intro="Share investment ideas and see others'. ⚠️ Content reflects user opinions, **not investment advice**.",
   s_login="Sign in to post, like and comment.", login_btn="Sign in with Google", logout="Log out",
   sort="Sort", s_new="🆕 Newest", s_pop="🔥 Most popular", no_uname="(no username)",
   uname_warn="Set a **username** before posting.", uname_lbl="Your username",
   uname_ph="e.g. investor_alex", save="Save", e_short3="At least 3 characters.",
   e_taken="That username is taken, try another.",
   new_exp="➕ Share a new idea", b_lbl="Title", b_ph="e.g. Why I believe in X long-term",
   tk_lbl="Ticker (opt.)", tk_ph="AAPL", m_lbl="Your idea", m_ph="Write your thesis, reasoning and risks...",
   rules="Please be respectful and avoid manipulation. Don't give financial advice.", share="Post",
   e_b5="Title must be at least 5 characters.", e_m10="Idea text must be at least 10 characters.", shared_ok="✅ Posted.",
   feed_err="Could not load feed: ", empty="No posts yet. Share the first idea!",
   t_like="Sign in to like.", t_vote="Sign in to vote.",
   del_p="Delete your post", rep_p="Report inappropriate content", rep_ok="Reported, thanks.",
   comments="comments", del_c="Delete your comment", c_lbl="Write a comment", c_ph="Share your view...", send="Send",
   c_short="Comment too short.", c_login="Sign in to comment.",
   disc="⚠️ Disclaimer: Posts are users' personal opinions and not investment advice. Do your own research.",
   now="just now", mn="min ago", hr="h ago", dy="d ago"),
 "de": dict(title="💡 Ideen",
   intro="Teile Anlageideen und sieh die anderer. ⚠️ Inhalte sind Nutzermeinungen, **keine Anlageberatung**.",
   s_login="Melde dich an, um zu posten, zu liken und zu kommentieren.", login_btn="Mit Google anmelden", logout="Abmelden",
   sort="Sortieren", s_new="🆕 Neueste", s_pop="🔥 Beliebteste", no_uname="(kein Benutzername)",
   uname_warn="Lege einen **Benutzernamen** fest, bevor du postest.", uname_lbl="Dein Benutzername",
   uname_ph="z. B. anleger_alex", save="Speichern", e_short3="Mindestens 3 Zeichen.",
   e_taken="Benutzername vergeben, wähle einen anderen.",
   new_exp="➕ Neue Idee teilen", b_lbl="Titel", b_ph="z. B. Warum ich langfristig an X glaube",
   tk_lbl="Kürzel (opt.)", tk_ph="AAPL", m_lbl="Deine Idee", m_ph="These, Begründung und Risiken...",
   rules="Bitte respektvoll bleiben und keine Manipulation. Keine Anlageberatung.", share="Posten",
   e_b5="Titel mindestens 5 Zeichen.", e_m10="Text mindestens 10 Zeichen.", shared_ok="✅ Gepostet.",
   feed_err="Feed nicht ladbar: ", empty="Noch keine Beiträge. Teile die erste Idee!",
   t_like="Zum Liken anmelden.", t_vote="Zum Abstimmen anmelden.",
   del_p="Beitrag löschen", rep_p="Unangemessenen Inhalt melden", rep_ok="Gemeldet, danke.",
   comments="Kommentare", del_c="Kommentar löschen", c_lbl="Kommentar schreiben", c_ph="Deine Meinung...", send="Senden",
   c_short="Kommentar zu kurz.", c_login="Zum Kommentieren anmelden.",
   disc="⚠️ Haftungsausschluss: Beiträge sind persönliche Meinungen, keine Anlageberatung. Recherchiere selbst.",
   now="gerade eben", mn="Min", hr="Std", dy="T"),
 "ru": dict(title="💡 Идеи",
   intro="Делитесь инвестидеями и смотрите чужие. ⚠️ Контент — мнения пользователей, **не инвестсовет**.",
   s_login="Войдите, чтобы публиковать, лайкать и комментировать.", login_btn="Войти через Google", logout="Выйти",
   sort="Сортировка", s_new="🆕 Новые", s_pop="🔥 Популярные", no_uname="(нет имени)",
   uname_warn="Задайте **имя пользователя** перед публикацией.", uname_lbl="Ваше имя пользователя",
   uname_ph="напр. investor_alex", save="Сохранить", e_short3="Минимум 3 символа.",
   e_taken="Имя занято, выберите другое.",
   new_exp="➕ Поделиться идеей", b_lbl="Заголовок", b_ph="напр. Почему я верю в X надолго",
   tk_lbl="Тикер (необ.)", tk_ph="AAPL", m_lbl="Ваша идея", m_ph="Тезис, обоснование и риски...",
   rules="Будьте уважительны и без манипуляций. Не давайте финсоветов.", share="Опубликовать",
   e_b5="Заголовок минимум 5 символов.", e_m10="Текст минимум 10 символов.", shared_ok="✅ Опубликовано.",
   feed_err="Не удалось загрузить ленту: ", empty="Пока нет постов. Поделитесь первой идеей!",
   t_like="Войдите, чтобы лайкнуть.", t_vote="Войдите, чтобы голосовать.",
   del_p="Удалить пост", rep_p="Пожаловаться на контент", rep_ok="Отправлено, спасибо.",
   comments="комм.", del_c="Удалить комментарий", c_lbl="Написать комментарий", c_ph="Ваше мнение...", send="Отправить",
   c_short="Комментарий слишком короткий.", c_login="Войдите, чтобы комментировать.",
   disc="⚠️ Отказ: посты — личные мнения, не инвестсовет. Проводите свой анализ.",
   now="только что", mn="мин", hr="ч", dy="д"),
 "es": dict(title="💡 Ideas",
   intro="Comparte ideas de inversión y mira las de otros. ⚠️ Son opiniones, **no asesoramiento**.",
   s_login="Inicia sesión para publicar, dar me gusta y comentar.", login_btn="Iniciar sesión con Google", logout="Cerrar sesión",
   sort="Ordenar", s_new="🆕 Recientes", s_pop="🔥 Populares", no_uname="(sin usuario)",
   uname_warn="Define un **nombre de usuario** antes de publicar.", uname_lbl="Tu nombre de usuario",
   uname_ph="p. ej. inversor_alex", save="Guardar", e_short3="Mínimo 3 caracteres.",
   e_taken="Ese usuario ya existe, prueba otro.",
   new_exp="➕ Compartir una idea", b_lbl="Título", b_ph="p. ej. Por qué creo en X a largo plazo",
   tk_lbl="Símbolo (opc.)", tk_ph="AAPL", m_lbl="Tu idea", m_ph="Tu tesis, razones y riesgos...",
   rules="Sé respetuoso y evita la manipulación. No des asesoramiento.", share="Publicar",
   e_b5="El título debe tener al menos 5 caracteres.", e_m10="El texto al menos 10 caracteres.", shared_ok="✅ Publicado.",
   feed_err="No se pudo cargar: ", empty="Aún no hay publicaciones. ¡Comparte la primera!",
   t_like="Inicia sesión para dar me gusta.", t_vote="Inicia sesión para votar.",
   del_p="Eliminar tu publicación", rep_p="Reportar contenido", rep_ok="Reportado, gracias.",
   comments="comentarios", del_c="Eliminar tu comentario", c_lbl="Escribe un comentario", c_ph="Tu opinión...", send="Enviar",
   c_short="Comentario muy corto.", c_login="Inicia sesión para comentar.",
   disc="⚠️ Aviso: las publicaciones son opiniones personales, no asesoramiento. Investiga por tu cuenta.",
   now="ahora", mn="min", hr="h", dy="d"),
 "ar": dict(title="💡 أفكار",
   intro="شارك أفكار الاستثمار وشاهد أفكار الآخرين. ⚠️ المحتوى آراء المستخدمين، **ليس نصيحة استثمارية**.",
   s_login="سجّل الدخول للنشر والإعجاب والتعليق.", login_btn="تسجيل الدخول عبر Google", logout="تسجيل الخروج",
   sort="ترتيب", s_new="🆕 الأحدث", s_pop="🔥 الأكثر رواجًا", no_uname="(لا اسم مستخدم)",
   uname_warn="حدّد **اسم مستخدم** قبل النشر.", uname_lbl="اسم المستخدم",
   uname_ph="مثل investor_alex", save="حفظ", e_short3="3 أحرف على الأقل.",
   e_taken="الاسم مأخوذ، جرّب غيره.",
   new_exp="➕ شارك فكرة جديدة", b_lbl="العنوان", b_ph="مثل لماذا أؤمن بـ X على المدى الطويل",
   tk_lbl="الرمز (اختياري)", tk_ph="AAPL", m_lbl="فكرتك", m_ph="اكتب أطروحتك ومبرراتك والمخاطر...",
   rules="كن محترمًا وتجنّب التلاعب. لا تقدّم نصائح مالية.", share="نشر",
   e_b5="العنوان 5 أحرف على الأقل.", e_m10="النص 10 أحرف على الأقل.", shared_ok="✅ تم النشر.",
   feed_err="تعذّر تحميل الموجز: ", empty="لا منشورات بعد. شارك أول فكرة!",
   t_like="سجّل الدخول للإعجاب.", t_vote="سجّل الدخول للتصويت.",
   del_p="حذف منشورك", rep_p="الإبلاغ عن محتوى غير لائق", rep_ok="تم الإبلاغ، شكرًا.",
   comments="تعليق", del_c="حذف تعليقك", c_lbl="اكتب تعليقًا", c_ph="شارك رأيك...", send="إرسال",
   c_short="التعليق قصير جدًا.", c_login="سجّل الدخول للتعليق.",
   disc="⚠️ إخلاء مسؤولية: المنشورات آراء شخصية وليست نصيحة استثمارية. ابحث بنفسك.",
   now="الآن", mn="د", hr="س", dy="ي"),
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
        if s < 60: return L["now"]
        if s < 3600: return f"{s // 60} {L['mn']}"
        if s < 86400: return f"{s // 3600} {L['hr']}"
        return f"{s // 86400} {L['dy']}"
    except Exception:
        return ""


st.title(L["title"])
st.caption(L["intro"])

with st.sidebar:
    if GIRIS:
        try:
            prof = db.profil_getir(EMAIL)
        except Exception:
            prof = None
        st.caption(f"👤 {prof['kullanici_adi'] if prof else L['no_uname']}")
        if st.button(L["logout"], width="stretch"):
            st.logout()
    else:
        st.info(L["s_login"])
        if st.button(L["login_btn"], type="primary", width="stretch"):
            st.login()
    st.divider()
    sirala = st.radio(L["sort"], [L["s_new"], L["s_pop"]], index=0)
sirala_kod = "populer" if sirala == L["s_pop"] else "yeni"

if GIRIS:
    try:
        prof = db.profil_getir(EMAIL)
    except Exception:
        prof = None
    if not prof or not prof.get("kullanici_adi"):
        st.warning(L["uname_warn"])
        with st.form("hizli_profil", clear_on_submit=False):
            yeni_ad = st.text_input(L["uname_lbl"], max_chars=24, placeholder=L["uname_ph"])
            if st.form_submit_button(L["save"], type="primary"):
                ad_t = (yeni_ad or "").strip()
                if len(ad_t) < 3:
                    st.error(L["e_short3"])
                elif not db.kullanici_adi_musait(ad_t, EMAIL):
                    st.error(L["e_taken"])
                else:
                    db.profil_kaydet(EMAIL, ad_t, "")
                    st.rerun()
    else:
        with st.expander(L["new_exp"], expanded=False):
            with st.form("yeni_paylasim", clear_on_submit=True):
                c = st.columns([3, 1])
                baslik = c[0].text_input(L["b_lbl"], max_chars=120, placeholder=L["b_ph"])
                ticker = c[1].text_input(L["tk_lbl"], max_chars=12, placeholder=L["tk_ph"])
                metin = st.text_area(L["m_lbl"], max_chars=2000, placeholder=L["m_ph"])
                st.caption(L["rules"])
                if st.form_submit_button(L["share"], type="primary"):
                    if len((baslik or "").strip()) < 5:
                        st.error(L["e_b5"])
                    elif len((metin or "").strip()) < 10:
                        st.error(L["e_m10"])
                    else:
                        db.paylasim_ekle(EMAIL, ticker, baslik, metin)
                        st.success(L["shared_ok"])
                        st.rerun()

st.divider()

try:
    paylasimlar = db.paylasimlar_getir(email=EMAIL, sirala=sirala_kod, limit=60)
except Exception as e:
    st.error(L["feed_err"] + str(e))
    st.stop()

if not paylasimlar:
    st.info(L["empty"])
    st.stop()

for p in paylasimlar:
    with st.container(border=True):
        ust = st.columns([6, 2])
        tk = f" · `{p['ticker']}`" if p["ticker"] else ""
        ust[0].markdown(f"**{p['baslik']}**{tk}")
        ust[1].caption(f"👤 {p['ad']} · {zaman(p['olusturuldu'])}")
        st.write(p["metin"])

        b = st.columns([1, 1, 2, 1, 1])
        like_tip = "primary" if p["benim_oyum"] == 1 else "secondary"
        dis_tip = "primary" if p["benim_oyum"] == -1 else "secondary"
        if b[0].button(f"👍 {p['begeni']}", key=f"like_{p['id']}", type=like_tip, width="stretch"):
            if GIRIS:
                db.begeni_ver(p["id"], EMAIL, 1); st.rerun()
            else:
                st.toast(L["t_like"])
        if b[1].button(f"👎 {p['begenme']}", key=f"dis_{p['id']}", type=dis_tip, width="stretch"):
            if GIRIS:
                db.begeni_ver(p["id"], EMAIL, -1); st.rerun()
            else:
                st.toast(L["t_vote"])
        if GIRIS and p["sahip_email"] == EMAIL:
            if b[3].button("🗑️", key=f"psil_{p['id']}", help=L["del_p"], width="stretch"):
                db.paylasim_sil(p["id"], EMAIL); st.rerun()
        if GIRIS and p["sahip_email"] != EMAIL:
            if b[4].button("⚠️", key=f"prapor_{p['id']}", help=L["rep_p"], width="stretch"):
                db.rapor_ekle(EMAIL, paylasim_id=p["id"], sebep="paylasim bildirimi")
                st.toast(L["rep_ok"])

        with st.expander(f"💬 {p['yorum_sayi']} {L['comments']}"):
            try:
                yorumlar = db.yorumlar_getir(p["id"])
            except Exception:
                yorumlar = []
            for y in yorumlar:
                yc = st.columns([8, 1])
                yc[0].markdown(f"**{y['ad']}** · {zaman(y['olusturuldu'])}  \n{y['metin']}")
                if GIRIS and y["sahip_email"] == EMAIL:
                    if yc[1].button("🗑️", key=f"ysil_{y['id']}", help=L["del_c"]):
                        db.yorum_sil(y["id"], EMAIL); st.rerun()
            if GIRIS:
                yeni_yorum = st.text_input(L["c_lbl"], key=f"yeni_yorum_{p['id']}",
                                           max_chars=500, placeholder=L["c_ph"])
                if st.button(L["send"], key=f"yorum_gonder_{p['id']}"):
                    if len((yeni_yorum or "").strip()) >= 2:
                        db.yorum_ekle(p["id"], EMAIL, yeni_yorum); st.rerun()
                    else:
                        st.warning(L["c_short"])
            else:
                st.caption(L["c_login"])

st.divider()
st.caption(L["disc"])
