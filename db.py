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
    """
    Alarmlari gunceller ama 'gonderildi' bayragini korur (arka plan iscisi yonetir).
    Listede olmayanlar silinir; hedef/yon degisirse gonderildi sifirlanir.
    alarmlar: {ticker: (yon, hedef)}.
    """
    tickerlar = list(alarmlar.keys())
    if tickerlar:
        _run("delete from alarm where email=%s and not (ticker = any(%s))", (email, tickerlar))
    else:
        _run("delete from alarm where email=%s", (email,))
    for t, (y, h) in alarmlar.items():
        _run("""insert into alarm(email, ticker, yon, hedef) values(%s, %s, %s, %s)
                on conflict (email, ticker) do update
                  set yon = excluded.yon,
                      hedef = excluded.hedef,
                      gonderildi = case
                        when alarm.yon <> excluded.yon or alarm.hedef <> excluded.hedef
                        then false else alarm.gonderildi end""",
             (email, t, y, float(h)))


# ---------------- BILDIRIM AYARLARI ----------------
def bildirim_getir(email):
    """Kullanicinin bildirim ayarlarini dondurur (yoksa None)."""
    satirlar = _run(
        "select telegram_chat_id, telegram_aktif, eposta_aktif from bildirim where email=%s",
        (email,), getir=True)
    if not satirlar:
        return None
    r = satirlar[0]
    return dict(telegram_chat_id=r[0], telegram_aktif=r[1], eposta_aktif=r[2])


def bildirim_kaydet(email, chat_id, telegram_aktif, eposta_aktif):
    """Bildirim ayarlarini ekler/gunceller."""
    _run("""insert into bildirim(email, telegram_chat_id, telegram_aktif, eposta_aktif)
            values(%s, %s, %s, %s)
            on conflict (email) do update
              set telegram_chat_id = excluded.telegram_chat_id,
                  telegram_aktif = excluded.telegram_aktif,
                  eposta_aktif = excluded.eposta_aktif""",
         (email, chat_id or None, bool(telegram_aktif), bool(eposta_aktif)))


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
