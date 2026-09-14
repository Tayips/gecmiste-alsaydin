"""
GECICI — Veritabani baglanti testi
Baglantiyi ve tablolari dogruladiktan sonra bu dosyayi silebilirsin.
"""
import streamlit as st

st.set_page_config(page_title="DB Test", page_icon="🔌")
st.title("🔌 Veritabanı Bağlantı Testi")

url = ""
try:
    url = st.secrets.get("DB_URL", "")
except Exception:
    url = ""

if not url:
    st.error("`DB_URL` secrets içinde bulunamadı. Streamlit → Manage app → Settings → Secrets "
             "içine `DB_URL = \"...\"` satırını ekledin mi?")
    st.stop()

try:
    import psycopg2
except Exception as e:
    st.error("psycopg2 yüklenemedi. requirements.txt'e `psycopg2-binary` eklendi mi? Hata: " + str(e))
    st.stop()

try:
    conn = psycopg2.connect(url, connect_timeout=8)
    cur = conn.cursor()
    cur.execute("select 1;")
    st.success("✅ Veritabanına başarıyla bağlandı. Test sorgusu: " + str(cur.fetchone()))
    cur.execute("""select table_name from information_schema.tables
                   where table_schema='public' and table_name in ('takip','alarm','portfoy')
                   order by table_name;""")
    tablolar = [r[0] for r in cur.fetchall()]
    if set(tablolar) == {"takip", "alarm", "portfoy"}:
        st.success("✅ Üç tablo da yerinde: " + ", ".join(tablolar))
    else:
        st.warning("Tablolar eksik görünüyor. Bulunan: " + str(tablolar))
    cur.close(); conn.close()
except Exception as e:
    st.error("❌ Bağlantı hatası: " + str(e))
    st.caption("En sık sebep: DB_URL'de şifre yanlış, ya da 'Session pooler' yerine 'Direct connection' "
               "seçilmiş (Streamlit IPv4 olduğu için Session pooler gerekir).")
