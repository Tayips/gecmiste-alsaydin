"""
db.py — ORTAK VERITABANI YARDIMCISI (Supabase / Postgres)
---------------------------------------------------------
Tum sayfalar (Takip, Portfoy) bu dosyadaki fonksiyonlari kullanir.
Her kullanicinin verisi kendi e-postasina bagli saklanir.

Tablolar (Supabase'de zaten olusturuldu):
  takip(email, ticker)
  alarm(email, ticker, yon, hedef)
  portfoy(id, email, ticker, adet, maliyet, eklendi)

Baglanti bilgisi Streamlit Secrets icindeki DB_URL'den okunur.
"""
import streamlit as st
import psycopg2


def _conn():
    """Yeni bir veritabani baglantisi acar."""
    url = st.secrets["DB_URL"]
    return psycopg2.connect(url, connect_timeout=8)


def _run(sorgu, parametreler=None, getir=False, cok=False):
    """
    Tek bir sorguyu calistirir, baglantiyi guvenli sekilde kapatir.
      getir=True  -> satirlari dondurur
      cok=True    -> executemany (parametreler bir liste olmali)
    """
    conn = _conn()
    try:
        cur = conn.cursor()
        if cok:
            cur.executemany(sorgu, parametreler or [])
        else:
            cur.execute(sorgu, parametreler or ())
        sonuc = cur.fetchall() if getir else None
        conn.commit()
        cur.close()
        return sonuc
    finally:
        conn.close()


# ---------------- TAKIP LISTESI ----------------
def takip_getir(email):
    """Kullanicinin takip listesindeki hisse kodlarini dondurur."""
    satirlar = _run("select ticker from takip where email=%s order by ticker",
                    (email,), getir=True)
    return [r[0] for r in satirlar]


def takip_kaydet(email, kodlar):
    """Takip listesini komple gunceller (once sil, sonra ekle)."""
    _run("delete from takip where email=%s", (email,))
    if kodlar:
        _run("insert into takip(email, ticker) values(%s, %s) on conflict do nothing",
             [(email, k) for k in kodlar], cok=True)


# ---------------- FIYAT ALARMLARI ----------------
def alarm_getir(email):
    """{ticker: (yon, hedef)} sozlugu dondurur. yon: '>=' veya '<='."""
    satirlar = _run("select ticker, yon, hedef from alarm where email=%s",
                    (email,), getir=True)
    return {r[0]: (r[1], float(r[2])) for r in satirlar}


def alarm_kaydet(email, alarmlar):
    """Alarmlari komple gunceller. alarmlar: {ticker: (yon, hedef)}."""
    _run("delete from alarm where email=%s", (email,))
    if alarmlar:
        _run("insert into alarm(email, ticker, yon, hedef) values(%s, %s, %s, %s)",
             [(email, t, y, float(h)) for t, (y, h) in alarmlar.items()], cok=True)


# ---------------- PORTFOY ----------------
def portfoy_getir(email):
    """Kullanicinin portfoyundaki tum pozisyonlari liste (sozluk) olarak dondurur."""
    satirlar = _run(
        "select id, ticker, adet, maliyet from portfoy where email=%s order by ticker",
        (email,), getir=True)
    return [dict(id=r[0], ticker=r[1], adet=float(r[2]), maliyet=float(r[3]))
            for r in satirlar]


def portfoy_ekle(email, ticker, adet, maliyet):
    """Portfoye yeni bir pozisyon ekler."""
    _run("insert into portfoy(email, ticker, adet, maliyet) values(%s, %s, %s, %s)",
         (email, ticker.upper(), float(adet), float(maliyet)))


def portfoy_sil(pid):
    """id ile tek bir pozisyonu siler."""
    _run("delete from portfoy where id=%s", (pid,))
