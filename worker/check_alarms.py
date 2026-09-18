"""
check_alarms.py — ARKA PLAN ALARM ISCISI
------------------------------------------------
GitHub Actions tarafindan her ~15 dakikada bir calistirilir.
Streamlit uygulamasindan BAGIMSIZDIR; sadece veritabanini okur.

Yaptigi is:
  1. Veritabanindaki tum alarmlari + kullanici bildirim ayarlarini okur.
  2. Her hisse icin guncel USD fiyati ceker (Finnhub -> Yahoo yedek).
  3. Hedefe ulasan ve daha once gonderilmemis alarmlar icin:
       - Telegram mesaji ve/veya e-posta gonderir
       - alarm.gonderildi = true yapar (tekrar tekrar gelmesin diye)
  4. Kosul artik saglanmiyorsa alarm.gonderildi = false yapar (yeniden kurulur).

Gizli bilgiler ortam degiskenlerinden (GitHub Actions secrets) okunur:
  DB_URL, FINNHUB_KEY, TELEGRAM_BOT_TOKEN, GMAIL_ADDRESS, GMAIL_APP_PASSWORD
"""
import os
import smtplib
from email.mime.text import MIMEText

import requests
import psycopg2

DB_URL = os.environ["DB_URL"]
FINNHUB_KEY = os.environ.get("FINNHUB_KEY", "")
TG_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN", "")
GMAIL = os.environ.get("GMAIL_ADDRESS", "")
GMAIL_PW = os.environ.get("GMAIL_APP_PASSWORD", "")


# ---------------- Fiyat ----------------
def finnhub_fiyat(ticker):
    if not FINNHUB_KEY:
        return None
    try:
        r = requests.get("https://finnhub.io/api/v1/quote",
                         params={"symbol": ticker, "token": FINNHUB_KEY}, timeout=10)
        c = r.json().get("c")
        return float(c) if c else None
    except Exception:
        return None


def yahoo_fiyat(ticker):
    """yfinance yedegi (kripto vb. icin). Basarisizsa None."""
    try:
        import yfinance as yf
        df = yf.download(ticker, period="5d", auto_adjust=True, progress=False)
        if df.empty:
            return None
        close = df["Close"]
        if hasattr(close, "columns"):
            close = close.iloc[:, 0]
        return float(close.dropna().iloc[-1])
    except Exception:
        return None


def guncel_fiyat(ticker):
    f = finnhub_fiyat(ticker)
    if f and f > 0:
        return f
    return yahoo_fiyat(ticker)


# ---------------- Bildirim gonderme ----------------
def telegram_gonder(chat_id, mesaj):
    if not (TG_TOKEN and chat_id):
        return False
    try:
        r = requests.post(f"https://api.telegram.org/bot{TG_TOKEN}/sendMessage",
                          data={"chat_id": chat_id, "text": mesaj}, timeout=10)
        return r.ok
    except Exception as e:
        print("Telegram hatasi:", e)
        return False


def eposta_gonder(alici, konu, mesaj):
    if not (GMAIL and GMAIL_PW and alici):
        return False
    try:
        msg = MIMEText(mesaj, _charset="utf-8")
        msg["Subject"] = konu
        msg["From"] = GMAIL
        msg["To"] = alici
        with smtplib.SMTP_SSL("smtp.gmail.com", 465, timeout=15) as s:
            s.login(GMAIL, GMAIL_PW)
            s.sendmail(GMAIL, [alici], msg.as_string())
        return True
    except Exception as e:
        print("E-posta hatasi:", e)
        return False


# ---------------- Ana akis ----------------
def main():
    conn = psycopg2.connect(DB_URL, connect_timeout=15)
    cur = conn.cursor()
    cur.execute("""
        select a.email, a.ticker, a.yon, a.hedef, coalesce(a.gonderildi, false),
               b.telegram_chat_id,
               coalesce(b.telegram_aktif, true),
               coalesce(b.eposta_aktif, true)
        from alarm a
        left join bildirim b on b.email = a.email
    """)
    alarmlar = cur.fetchall()
    print(f"{len(alarmlar)} alarm kontrol ediliyor...")

    # Ayni hisseyi bir kez cek
    fiyat_cache = {}

    for (email, ticker, yon, hedef, gonderildi,
         chat_id, tg_aktif, mail_aktif) in alarmlar:
        if ticker not in fiyat_cache:
            fiyat_cache[ticker] = guncel_fiyat(ticker)
        fiyat = fiyat_cache[ticker]
        if fiyat is None:
            print(f"  {ticker}: fiyat alinamadi, atlaniyor")
            continue

        hedef = float(hedef)
        tetik = (fiyat >= hedef) if yon == ">=" else (fiyat <= hedef)

        if tetik and not gonderildi:
            yon_txt = "üstüne çıktı" if yon == ">=" else "altına indi"
            mesaj = (f"🔔 {ticker} alarmı tetiklendi!\n"
                     f"Hedef: {yon} {hedef:g} USD ({yon_txt})\n"
                     f"Güncel fiyat: {fiyat:.2f} USD\n\n"
                     f"— Geçmişte Alsaydın? (yatırım tavsiyesi değildir)")
            gonderildi_mi = False
            if tg_aktif:
                gonderildi_mi = telegram_gonder(chat_id, mesaj) or gonderildi_mi
            if mail_aktif:
                gonderildi_mi = eposta_gonder(email, f"🔔 {ticker} fiyat alarmı", mesaj) or gonderildi_mi
            # En az bir kanaldan gittiyse (ya da hic kanal acik degilse bile) isaretle
            cur.execute("update alarm set gonderildi=true where email=%s and ticker=%s",
                        (email, ticker))
            conn.commit()
            print(f"  {ticker}: TETIKLENDI ({fiyat:.2f}), bildirim gonderildi={gonderildi_mi}")

        elif (not tetik) and gonderildi:
            # Kosul artik saglanmiyor -> yeniden kur
            cur.execute("update alarm set gonderildi=false where email=%s and ticker=%s",
                        (email, ticker))
            conn.commit()
            print(f"  {ticker}: yeniden kuruldu ({fiyat:.2f})")

    cur.close()
    conn.close()
    print("Bitti.")


if __name__ == "__main__":
    main()
