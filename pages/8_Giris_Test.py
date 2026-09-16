"""
GECICI — Google ile giris testi.
Giris calistigini dogruladiktan sonra bu dosyayi silebilirsin.
"""
import streamlit as st

st.set_page_config(page_title="Giriş Testi", page_icon="🔑")
st.title("🔑 Google ile Giriş Testi")

# st.user / st.login Streamlit'in yerlesik kimlik dogrulamasi (Authlib gerekir)
if not getattr(st, "user", None) or not st.user.is_logged_in:
    st.info("Henüz giriş yapılmadı.")
    if st.button("Google ile giriş yap", type="primary"):
        st.login()
else:
    st.success(f"✅ Giriş başarılı! E-posta: **{st.user.email}**")
    st.write("Ad:", st.user.get("name", "—"))
    if st.button("Çıkış yap"):
        st.logout()
