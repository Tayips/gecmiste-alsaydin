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


# ==================== TOPLULUK (Fikirler) ====================

# ---------------- PROFIL ----------------
def profil_getir(email):
    """Kullanicinin profilini dondurur (yoksa None)."""
    r = _run("select kullanici_adi, bio from profil where email=%s", (email,), getir=True)
    if not r:
        return None
    return dict(kullanici_adi=r[0][0], bio=r[0][1])


def profil_email_bul(kullanici_adi):
    """Kullanici adindan e-postayi bulur (herkese acik profil goruntuleme icin)."""
    r = _run("select email from profil where kullanici_adi=%s", (kullanici_adi,), getir=True)
    return r[0][0] if r else None


def kullanici_adi_musait(kullanici_adi, email):
    """Bu kullanici adi baskasi tarafindan alinmis mi? (kendi adin serbest)"""
    r = _run("select email from profil where kullanici_adi=%s", (kullanici_adi,), getir=True)
    return (not r) or (r[0][0] == email)


def profil_kaydet(email, kullanici_adi, bio):
    """Profili ekler/gunceller."""
    _run("""insert into profil(email, kullanici_adi, bio) values(%s, %s, %s)
            on conflict (email) do update
              set kullanici_adi = excluded.kullanici_adi, bio = excluded.bio""",
         (email, kullanici_adi.strip(), (bio or "").strip()))


# ---------------- PAYLASIMLAR ----------------
def paylasim_ekle(email, ticker, baslik, metin):
    """Yeni bir yatirim fikri paylasir."""
    _run("insert into paylasim(email, ticker, baslik, metin) values(%s, %s, %s, %s)",
         (email, (ticker or "").upper().strip() or None, baslik.strip(), metin.strip()))


def paylasim_sil(pid, email):
    """Sadece kendi paylasimini siler."""
    _run("delete from paylasim where id=%s and email=%s", (pid, email))


def paylasimlar_getir(email="", sirala="yeni", limit=50, kullanici_email=None):
    """
    Akis: paylasimlar + yazar adi + begeni/begenmeme sayilari + yorum sayisi
    + (giris yapan) kullanicinin kendi oyu. E-posta asla disari verilmez.
    kullanici_email verilirse sadece o kisinin paylasimlari (profil sayfasi icin).
    """
    kosul = "where p.email = %s" if kullanici_email else ""
    sira = ("order by (coalesce(sum(b.deger),0)) desc, p.olusturuldu desc"
            if sirala == "populer" else "order by p.olusturuldu desc")
    sql = f"""
        select p.id, p.ticker, p.baslik, p.metin, p.olusturuldu, p.email,
               coalesce(pr.kullanici_adi, 'Anonim') as ad,
               coalesce(sum(case when b.deger=1 then 1 else 0 end), 0) as begeni,
               coalesce(sum(case when b.deger=-1 then 1 else 0 end), 0) as begenme,
               (select count(*) from yorum y where y.paylasim_id = p.id) as yorum_sayi,
               coalesce(max(case when b.email = %s then b.deger else 0 end), 0) as benim_oyum
        from paylasim p
        left join profil pr on pr.email = p.email
        left join begeni b on b.paylasim_id = p.id
        {kosul}
        group by p.id, pr.kullanici_adi
        {sira}
        limit %s
    """
    params = [email]
    if kullanici_email:
        params.append(kullanici_email)
    params.append(limit)
    rows = _run(sql, tuple(params), getir=True)
    return [dict(id=r[0], ticker=r[1], baslik=r[2], metin=r[3], olusturuldu=r[4],
                 sahip_email=r[5], ad=r[6], begeni=int(r[7]), begenme=int(r[8]),
                 yorum_sayi=int(r[9]), benim_oyum=int(r[10])) for r in rows]


# ---------------- BEGENI ----------------
def begeni_ver(paylasim_id, email, deger):
    """
    Begeni (+1) / begenmeme (-1). Ayni tusa tekrar basinca oy kalkar (toggle).
    Farkli tusa basinca oy degisir.
    """
    mevcut = _run("select deger from begeni where paylasim_id=%s and email=%s",
                  (paylasim_id, email), getir=True)
    if mevcut and mevcut[0][0] == deger:
        _run("delete from begeni where paylasim_id=%s and email=%s", (paylasim_id, email))
    else:
        _run("""insert into begeni(paylasim_id, email, deger) values(%s, %s, %s)
                on conflict (paylasim_id, email) do update set deger = excluded.deger""",
             (paylasim_id, email, int(deger)))


# ---------------- YORUM ----------------
def yorumlar_getir(paylasim_id):
    """Bir paylasimin yorumlarini (yazar adiyla) dondurur."""
    rows = _run("""
        select y.id, y.metin, y.olusturuldu, coalesce(pr.kullanici_adi, 'Anonim'), y.email
        from yorum y
        left join profil pr on pr.email = y.email
        where y.paylasim_id = %s
        order by y.olusturuldu asc
    """, (paylasim_id,), getir=True)
    return [dict(id=r[0], metin=r[1], olusturuldu=r[2], ad=r[3], sahip_email=r[4])
            for r in rows]


def yorum_ekle(paylasim_id, email, metin):
    """Bir paylasima yorum ekler."""
    _run("insert into yorum(paylasim_id, email, metin) values(%s, %s, %s)",
         (paylasim_id, email, metin.strip()))


def yorum_sil(yid, email):
    """Sadece kendi yorumunu siler."""
    _run("delete from yorum where id=%s and email=%s", (yid, email))


# ---------------- RAPOR (moderasyon) ----------------
def rapor_ekle(email, paylasim_id=None, yorum_id=None, sebep=""):
    """Uygunsuz icerigi bildirir."""
    _run("insert into rapor(email, paylasim_id, yorum_id, sebep) values(%s, %s, %s, %s)",
         (email, paylasim_id, yorum_id, (sebep or "").strip()))


# ==================== SIMULASYON (Deneme Hesabi / Paper Trading) ====================
# Tum muhasebe USD uzerinden yapilir. Baslangic bakiyesi 100.000 USD.
BASLANGIC_USD = 100000.0


def _sim_hesap_var(cur, email):
    """Hesap yoksa 100.000 USD ile olusturur; (nakit, baslangic) dondurur."""
    cur.execute("select nakit_usd, baslangic_usd from sim_hesap where email=%s", (email,))
    r = cur.fetchone()
    if not r:
        cur.execute("insert into sim_hesap(email, nakit_usd, baslangic_usd) values(%s, %s, %s)",
                    (email, BASLANGIC_USD, BASLANGIC_USD))
        return BASLANGIC_USD, BASLANGIC_USD
    return float(r[0]), float(r[1])


def sim_hesap_getir(email):
    """Nakit (USD) ve baslangic bakiyesini dondurur; yoksa olusturur."""
    conn = _conn()
    try:
        cur = conn.cursor()
        nakit, bas = _sim_hesap_var(cur, email)
        conn.commit(); cur.close()
        return dict(nakit=nakit, baslangic=bas)
    finally:
        conn.close()


def sim_pozisyonlar_getir(email):
    """Sanal portfoydeki pozisyonlar (adet + ortalama maliyet USD)."""
    rows = _run("""select ticker, adet, ort_maliyet_usd from sim_pozisyon
                   where email=%s and adet > 0 order by ticker""", (email,), getir=True)
    return [dict(ticker=r[0], adet=float(r[1]), ort_maliyet=float(r[2])) for r in rows]


def sim_al(email, ticker, adet, fiyat_usd):
    """Sanal alim. Tek islemde: nakit dus, pozisyon guncelle (ort. maliyet), gecmise yaz.
    (basari, hata_kodu) dondurur. hata_kodu: None | 'bakiye'."""
    adet = float(adet); fiyat_usd = float(fiyat_usd); tutar = adet * fiyat_usd
    conn = _conn()
    try:
        cur = conn.cursor()
        nakit, _ = _sim_hesap_var(cur, email)
        if tutar > nakit + 1e-6:
            cur.close(); return False, "bakiye"
        cur.execute("update sim_hesap set nakit_usd = nakit_usd - %s, guncellendi=now() where email=%s",
                    (tutar, email))
        cur.execute("select adet, ort_maliyet_usd from sim_pozisyon where email=%s and ticker=%s",
                    (email, ticker))
        r = cur.fetchone()
        if r:
            eski_adet = float(r[0]); eski_mal = float(r[1])
            yeni_adet = eski_adet + adet
            yeni_mal = (eski_adet * eski_mal + adet * fiyat_usd) / yeni_adet
            cur.execute("update sim_pozisyon set adet=%s, ort_maliyet_usd=%s where email=%s and ticker=%s",
                        (yeni_adet, yeni_mal, email, ticker))
        else:
            cur.execute("""insert into sim_pozisyon(email, ticker, adet, ort_maliyet_usd)
                           values(%s, %s, %s, %s)""", (email, ticker, adet, fiyat_usd))
        cur.execute("""insert into sim_islem(email, ticker, tur, adet, fiyat_usd, tutar_usd)
                       values(%s, %s, 'AL', %s, %s, %s)""", (email, ticker, adet, fiyat_usd, tutar))
        conn.commit(); cur.close()
        return True, None
    finally:
        conn.close()


def sim_sat(email, ticker, adet, fiyat_usd):
    """Sanal satis. (basari, hata_kodu). hata_kodu: None | 'adet'."""
    adet = float(adet); fiyat_usd = float(fiyat_usd); tutar = adet * fiyat_usd
    conn = _conn()
    try:
        cur = conn.cursor()
        _sim_hesap_var(cur, email)
        cur.execute("select adet from sim_pozisyon where email=%s and ticker=%s", (email, ticker))
        r = cur.fetchone()
        if not r or float(r[0]) < adet - 1e-6:
            cur.close(); return False, "adet"
        eski_adet = float(r[0]); kalan = eski_adet - adet
        cur.execute("update sim_hesap set nakit_usd = nakit_usd + %s, guncellendi=now() where email=%s",
                    (tutar, email))
        if kalan <= 1e-6:
            cur.execute("delete from sim_pozisyon where email=%s and ticker=%s", (email, ticker))
        else:
            cur.execute("update sim_pozisyon set adet=%s where email=%s and ticker=%s",
                        (kalan, email, ticker))
        cur.execute("""insert into sim_islem(email, ticker, tur, adet, fiyat_usd, tutar_usd)
                       values(%s, %s, 'SAT', %s, %s, %s)""", (email, ticker, adet, fiyat_usd, tutar))
        conn.commit(); cur.close()
        return True, None
    finally:
        conn.close()


def sim_sifirla(email):
    """Hesabi sifirla: pozisyon ve gecmisi sil, nakiti 100.000 USD yap."""
    conn = _conn()
    try:
        cur = conn.cursor()
        cur.execute("delete from sim_pozisyon where email=%s", (email,))
        cur.execute("delete from sim_islem where email=%s", (email,))
        cur.execute("""insert into sim_hesap(email, nakit_usd, baslangic_usd) values(%s, %s, %s)
                       on conflict(email) do update
                         set nakit_usd=excluded.nakit_usd, baslangic_usd=excluded.baslangic_usd,
                             guncellendi=now()""", (email, BASLANGIC_USD, BASLANGIC_USD))
        conn.commit(); cur.close()
    finally:
        conn.close()


def sim_islemler_getir(email, limit=60):
    """Islem gecmisi (en yeni ustte)."""
    rows = _run("""select ticker, tur, adet, fiyat_usd, tutar_usd, olusturuldu
                   from sim_islem where email=%s order by olusturuldu desc limit %s""",
                (email, limit), getir=True)
    return [dict(ticker=r[0], tur=r[1], adet=float(r[2]), fiyat=float(r[3]),
                 tutar=float(r[4]), olusturuldu=r[5]) for r in rows]


def sim_liderlik_veri():
    """Liderlik icin ham veri: hesaplar (kullanici adiyla) + tum pozisyonlar.
    Toplam deger, fiyatlarla sayfada hesaplanir. E-posta disari verilmez (sadece ad)."""
    hesaplar = _run("""select h.email, coalesce(pr.kullanici_adi, 'Anonim'),
                              h.nakit_usd, h.baslangic_usd
                       from sim_hesap h left join profil pr on pr.email = h.email""", getir=True)
    pozlar = _run("select email, ticker, adet from sim_pozisyon where adet > 0", getir=True)
    h = [dict(email=r[0], ad=r[1], nakit=float(r[2]), baslangic=float(r[3])) for r in hesaplar]
    p = [dict(email=r[0], ticker=r[1], adet=float(r[2])) for r in pozlar]
    return h, p
