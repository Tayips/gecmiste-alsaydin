"""
GECMISTE ALSAYDIN? / IF YOU HAD INVESTED? — Surum 8 (cok dilli)
------------------------------------------------
Diller: Türkçe, English, Deutsch, Русский, Español, العربية (RTL).
Ozellikler: sirket arama/listeden secim, coklu karsilastirma, € / $ / ₺ (gercek kur),
tek seferlik & DCA, enflasyona gore (reel) mod, KPI kartlari + mini grafik,
etkilesimli Plotly grafik (zengin tooltip), hazir senaryolar, paylasim.

Egitim amaclidir; yatirim tavsiyesi degildir.
CALISTIRMA:  pip install streamlit yfinance pandas numpy plotly matplotlib curl_cffi
             streamlit run app.py
"""

import io, urllib.parse
from datetime import date, timedelta

import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
import requests
import plotly.graph_objects as go
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

try:
    st.set_page_config(page_title="WhatIfInvest — Geçmişte Alsaydın?",
                       page_icon="assets/favicon.png", layout="wide")
except Exception:
    st.set_page_config(page_title="WhatIfInvest — Geçmişte Alsaydın?",
                       page_icon="📈", layout="wide")

# Marka logosu (sol menu ustu + her sayfada)
try:
    st.logo("assets/logo_lockup.png", size="large", icon_image="assets/favicon.png")
except Exception:
    pass

# ==================== CEVIRILER ====================
DILLER = {"Türkçe": "tr", "English": "en", "Deutsch": "de",
          "Русский": "ru", "Español": "es", "العربية": "ar"}

T = {
"tr": dict(
 title="📈 Geçmişte Alsaydın?", settings="Ayarlar", try_preset="Hazır senaryo dene:",
 p_pandemic="🚀 Pandemi başında 1.000$ Apple", p_dca="📈 5 yıldır her ay 100$ NVDA",
 p_2008="🏛️ 2008 krizinde SPY", p_vs="⚔️ Apple vs Microsoft vs Nvidia",
 company="Şirket (listeden seç)", company_help="Tıkla ve listeden seç; yazarak da filtreleyebilirsin.",
 search="Listede yoksa şirket adı/kodu ara", search_help="Boş bırakırsan üstteki seçim geçerli.",
 search_pick="Arama sonucundan seç", compare="Karşılaştır (listeden seç)",
 compare_help="Aynı grafikte kıyaslamak için şirket ekle.",
 compare_extra="Listede yoksa kod yaz (virgülle)", compare_extra_help="Örn. GOOGL, BTC-USD. İsteğe bağlı.",
 currency="Para birimi", real="Enflasyona göre (reel) göster",
 real_help="ABD TÜFE ile enflasyondan arındırılmış gerçek alım gücü.",
 method="Yatırım şekli", lump="Tek seferde (baştan hepsi)", dca="Aylara yayarak (her ay biraz)",
 amount="Yatırılan tutar", monthly="Her ay ne kadar?", yearly_inc="Her yıl katkıyı artır (%)",
 start="Başlangıç", end="Bitiş", calc="Hesapla",
 intro="Soldaki panelden bir (veya birkaç) şirket, tutar ve tarih seç. Sonuç her zaman borsa "
       "endeksi (SPY) ile karşılaştırılır. Yatırım tavsiyesi değildir; geçmişi gösterir.",
 err_dates="Başlangıç tarihi, bitiş tarihinden önce olmalı.", spinner="Hesaplanıyor...",
 err_nodata="Veri bulunamadı. Şirket adını/kodunu kontrol et.",
 cap_fx="Not: Kur verisi alınamadı; sonuç dolar bazlı gösteriliyor.",
 cap_skip="Bulunamayan ve atlanan: ", cap_cpi="Not: Enflasyon (TÜFE) verisi alınamadı; nominal gösteriliyor.",
 cap_real="🔎 Reel mod açık: değerler ABD enflasyonundan arındırıldı ({bas} alım gücüne göre).",
 sentence="<b>{bas} – {bit}</b> arasında <b>{ad}</b> hissesine <b>{tutar}</b> yatırsaydınız{ek}, "
          "dönem sonunda <b>{son}</b> olurdu — yaklaşık <b>{kar} {kz}</b> ({get}).",
 ekdca=" (her ay {aylik}, toplam {top})", kar="kâr", zarar="zarar",
 card_final="Dönem sonu değeri", card_yearly="Yıllık ortalama (yaklaşık)", yearly_sub="yıllık büyüme",
 card_vs="Endekse (SPY) göre", beat="Endeksi geçti ✅", below="Endeksin altında ⚠️",
 multi_top="<b>{bas} – {bit}</b> arasında <b>{tutar}</b> yatırımla en çok kazandıran: <b>{ad}</b> ({get}).",
 index_spy="Endeks (SPY)", hover_diff="Endeksten fark", hover_fx="O günkü kur (1$)",
 hover_index="Endeks", yaxis="Değer",
 share_dl="📥 Özet görseli indir", share_tw="🐦 Twitter/X", share_li="💼 LinkedIn",
 share_tip="İpucu: İndirdiğin görseli Instagram, WhatsApp veya her yerde paylaşabilirsin.",
 tweet="{ad} hissesine {bas}'de {tutar} yatırsaydım bugün {son} olurdu! #GeçmişteAlsaydın",
 info="👈 Soldaki panelden bilgileri girip **Hesapla**'ya bas. Hızlı denemek için yukarıdaki hazır senaryoları kullan.",
 about_title="ℹ️ Bu araç hakkında / uyarı",
 about="Sadece geçmiş veriye dayalı, eğitim amaçlı bir araçtır. Yatırım tavsiyesi değildir. "
       "Tek bir kazanan hisseye bakıp 'kolay para' sanma — o hisseyi önceden seçmek imkânsızdı; "
       "bu yüzden her sonuç endeksle (SPY) kıyaslanır. ₺/€ için tarihsel döviz kuru uygulanır. "
       "Veri kaynağı: Yahoo Finance.",
 img_title="Geçmişte Alsaydın?", img_inv="{yat} yatırım → {get}", img_idx="Endekste (SPY): {s}",
),
"en": dict(
 title="📈 If You Had Invested?", settings="Settings", try_preset="Try a scenario:",
 p_pandemic="🚀 $1,000 in Apple at pandemic start", p_dca="📈 $100/month in NVDA for 5 years",
 p_2008="🏛️ SPY since the 2008 crisis", p_vs="⚔️ Apple vs Microsoft vs Nvidia",
 company="Company (pick from list)", company_help="Click and pick; type to filter.",
 search="Not listed? Search name/ticker", search_help="Leave empty to use the pick above.",
 search_pick="Pick from results", compare="Compare (pick from list)",
 compare_help="Add companies to compare on the same chart.",
 compare_extra="Not listed? Type tickers (comma)", compare_extra_help="e.g. GOOGL, BTC-USD. Optional.",
 currency="Currency", real="Show inflation-adjusted (real)",
 real_help="Real purchasing power, adjusted by US CPI.",
 method="Investment type", lump="Lump sum (all at once)", dca="Monthly (a bit each month)",
 amount="Amount invested", monthly="How much each month?", yearly_inc="Increase contribution yearly (%)",
 start="Start", end="End", calc="Calculate",
 intro="Pick one (or more) companies, an amount and dates on the left. Every result is compared "
       "with the stock index (SPY). Not investment advice; it shows the past.",
 err_dates="Start date must be before end date.", spinner="Calculating...",
 err_nodata="No data found. Check the company name/ticker.",
 cap_fx="Note: exchange-rate data unavailable; showing in USD.",
 cap_skip="Not found and skipped: ", cap_cpi="Note: inflation (CPI) data unavailable; showing nominal.",
 cap_real="🔎 Real mode on: values adjusted for US inflation (in {bas} purchasing power).",
 sentence="If you had invested <b>{tutar}</b> in <b>{ad}</b> between <b>{bas} – {bit}</b>{ek}, "
          "it would be <b>{son}</b> at the end — about <b>{kar} {kz}</b> ({get}).",
 ekdca=" ({aylik}/month, {top} total)", kar="profit", zarar="loss",
 card_final="Final value", card_yearly="Yearly average (approx.)", yearly_sub="annual growth",
 card_vs="Vs index (SPY)", beat="Beat the index ✅", below="Below the index ⚠️",
 multi_top="Best performer with <b>{tutar}</b> between <b>{bas} – {bit}</b>: <b>{ad}</b> ({get}).",
 index_spy="Index (SPY)", hover_diff="Vs index", hover_fx="FX that day (1$)",
 hover_index="Index", yaxis="Value",
 share_dl="📥 Download summary image", share_tw="🐦 Twitter/X", share_li="💼 LinkedIn",
 share_tip="Tip: share the downloaded image on Instagram, WhatsApp, anywhere.",
 tweet="If I had invested {tutar} in {ad} on {bas}, today it would be {son}! #IfIHadInvested",
 info="👈 Set the options on the left and press **Calculate**. Use the ready scenarios above for a quick try.",
 about_title="ℹ️ About this tool / disclaimer",
 about="An educational tool based only on past data. Not investment advice. Don't look at a single "
       "winner and assume 'easy money' — picking it in advance was impossible; that's why every "
       "result is compared with the index (SPY). Historical FX applied for €/₺. Data: Yahoo Finance.",
 img_title="If You Had Invested", img_inv="{yat} invested → {get}", img_idx="In the index (SPY): {s}",
),
"de": dict(
 title="📈 Hättest du investiert?", settings="Einstellungen", try_preset="Szenario ausprobieren:",
 p_pandemic="🚀 1.000$ in Apple zu Pandemiebeginn", p_dca="📈 5 Jahre je 100$/Monat NVDA",
 p_2008="🏛️ SPY seit der Krise 2008", p_vs="⚔️ Apple vs Microsoft vs Nvidia",
 company="Unternehmen (aus Liste wählen)", company_help="Anklicken und wählen; zum Filtern tippen.",
 search="Nicht gelistet? Name/Kürzel suchen", search_help="Leer lassen, um die obige Auswahl zu nutzen.",
 search_pick="Aus Ergebnissen wählen", compare="Vergleichen (aus Liste)",
 compare_help="Unternehmen für den Vergleich im selben Diagramm hinzufügen.",
 compare_extra="Nicht gelistet? Kürzel (Komma)", compare_extra_help="z. B. GOOGL, BTC-USD. Optional.",
 currency="Währung", real="Inflationsbereinigt (real) anzeigen",
 real_help="Reale Kaufkraft, bereinigt um US-VPI.",
 method="Anlageart", lump="Einmalig (alles auf einmal)", dca="Monatlich (jeden Monat etwas)",
 amount="Angelegter Betrag", monthly="Wie viel pro Monat?", yearly_inc="Beitrag jährlich erhöhen (%)",
 start="Start", end="Ende", calc="Berechnen",
 intro="Wähle links ein (oder mehrere) Unternehmen, Betrag und Datum. Jedes Ergebnis wird mit dem "
       "Aktienindex (SPY) verglichen. Keine Anlageberatung; es zeigt die Vergangenheit.",
 err_dates="Startdatum muss vor dem Enddatum liegen.", spinner="Berechne...",
 err_nodata="Keine Daten gefunden. Name/Kürzel prüfen.",
 cap_fx="Hinweis: Wechselkursdaten nicht verfügbar; Anzeige in USD.",
 cap_skip="Nicht gefunden und übersprungen: ", cap_cpi="Hinweis: Inflationsdaten (VPI) nicht verfügbar; nominal.",
 cap_real="🔎 Real-Modus an: Werte um US-Inflation bereinigt (Kaufkraft von {bas}).",
 sentence="Hättest du <b>{tutar}</b> in <b>{ad}</b> zwischen <b>{bas} – {bit}</b> investiert{ek}, "
          "wären es am Ende <b>{son}</b> — etwa <b>{kar} {kz}</b> ({get}).",
 ekdca=" ({aylik}/Monat, {top} gesamt)", kar="Gewinn", zarar="Verlust",
 card_final="Endwert", card_yearly="Jährlicher Schnitt (ca.)", yearly_sub="jährl. Wachstum",
 card_vs="Ggü. Index (SPY)", beat="Schlug den Index ✅", below="Unter dem Index ⚠️",
 multi_top="Bester mit <b>{tutar}</b> zwischen <b>{bas} – {bit}</b>: <b>{ad}</b> ({get}).",
 index_spy="Index (SPY)", hover_diff="Ggü. Index", hover_fx="Kurs am Tag (1$)",
 hover_index="Index", yaxis="Wert",
 share_dl="📥 Bild herunterladen", share_tw="🐦 Twitter/X", share_li="💼 LinkedIn",
 share_tip="Tipp: Teile das Bild auf Instagram, WhatsApp, überall.",
 tweet="Hätte ich {bas} {tutar} in {ad} investiert, wären es heute {son}! #HättestDuInvestiert",
 info="👈 Optionen links einstellen und **Berechnen** drücken. Für einen schnellen Test die Szenarien oben nutzen.",
 about_title="ℹ️ Über dieses Tool / Hinweis",
 about="Ein Lern-Tool nur auf Basis vergangener Daten. Keine Anlageberatung. Ein einzelner Gewinner "
       "bedeutet kein 'leichtes Geld' — ihn vorab zu wählen war unmöglich; daher wird jedes Ergebnis "
       "mit dem Index (SPY) verglichen. Historischer Kurs für €/₺. Daten: Yahoo Finance.",
 img_title="Hättest du investiert?", img_inv="{yat} angelegt → {get}", img_idx="Im Index (SPY): {s}",
),
"ru": dict(
 title="📈 Если бы вы инвестировали?", settings="Настройки", try_preset="Попробуйте сценарий:",
 p_pandemic="🚀 1000$ в Apple в начале пандемии", p_dca="📈 5 лет по 100$/мес в NVDA",
 p_2008="🏛️ SPY с кризиса 2008", p_vs="⚔️ Apple vs Microsoft vs Nvidia",
 company="Компания (из списка)", company_help="Нажмите и выберите; печатайте для фильтра.",
 search="Нет в списке? Поиск по имени/тикеру", search_help="Оставьте пустым, чтобы использовать выбор выше.",
 search_pick="Выбрать из результатов", compare="Сравнить (из списка)",
 compare_help="Добавьте компании для сравнения на одном графике.",
 compare_extra="Нет в списке? Тикеры (через запятую)", compare_extra_help="напр. GOOGL, BTC-USD. Необязательно.",
 currency="Валюта", real="Показать с учётом инфляции (реально)",
 real_help="Реальная покупательная способность по ИПЦ США.",
 method="Тип инвестиции", lump="Единоразово (сразу всё)", dca="Ежемесячно (понемногу)",
 amount="Сумма вложения", monthly="Сколько в месяц?", yearly_inc="Увеличивать взнос ежегодно (%)",
 start="Начало", end="Конец", calc="Рассчитать",
 intro="Выберите слева компанию (или несколько), сумму и даты. Каждый результат сравнивается с "
       "индексом (SPY). Не является инвестсоветом; показывает прошлое.",
 err_dates="Дата начала должна быть раньше даты конца.", spinner="Расчёт...",
 err_nodata="Данные не найдены. Проверьте имя/тикер.",
 cap_fx="Примечание: курс недоступен; показано в USD.",
 cap_skip="Не найдено и пропущено: ", cap_cpi="Примечание: данные инфляции (ИПЦ) недоступны; номинал.",
 cap_real="🔎 Реальный режим: значения скорректированы на инфляцию США (покупат. способность {bas}).",
 sentence="Если бы вы вложили <b>{tutar}</b> в <b>{ad}</b> за <b>{bas} – {bit}</b>{ek}, "
          "в итоге было бы <b>{son}</b> — примерно <b>{kar} {kz}</b> ({get}).",
 ekdca=" ({aylik}/мес, всего {top})", kar="прибыль", zarar="убыток",
 card_final="Итоговая стоимость", card_yearly="Годовое в среднем (прибл.)", yearly_sub="годовой рост",
 card_vs="Против индекса (SPY)", beat="Обогнал индекс ✅", below="Ниже индекса ⚠️",
 multi_top="Лучший при вложении <b>{tutar}</b> за <b>{bas} – {bit}</b>: <b>{ad}</b> ({get}).",
 index_spy="Индекс (SPY)", hover_diff="Против индекса", hover_fx="Курс в тот день (1$)",
 hover_index="Индекс", yaxis="Стоимость",
 share_dl="📥 Скачать картинку", share_tw="🐦 Twitter/X", share_li="💼 LinkedIn",
 share_tip="Совет: поделитесь картинкой в Instagram, WhatsApp — где угодно.",
 tweet="Если бы я вложил {tutar} в {ad} {bas}, сегодня было бы {son}! #ЕслиБыИнвестировал",
 info="👈 Задайте параметры слева и нажмите **Рассчитать**. Для быстрой пробы используйте сценарии выше.",
 about_title="ℹ️ Об этом инструменте / оговорка",
 about="Образовательный инструмент только на исторических данных. Не инвестсовет. Один победитель "
       "не значит 'лёгкие деньги' — выбрать его заранее было невозможно; поэтому каждый результат "
       "сравнивается с индексом (SPY). Для €/₺ применяется исторический курс. Данные: Yahoo Finance.",
 img_title="Если бы вы инвестировали", img_inv="{yat} вложено → {get}", img_idx="В индексе (SPY): {s}",
),
"es": dict(
 title="📈 ¿Y si hubieras invertido?", settings="Ajustes", try_preset="Prueba un escenario:",
 p_pandemic="🚀 1.000$ en Apple al inicio de la pandemia", p_dca="📈 100$/mes en NVDA durante 5 años",
 p_2008="🏛️ SPY desde la crisis de 2008", p_vs="⚔️ Apple vs Microsoft vs Nvidia",
 company="Empresa (elige de la lista)", company_help="Haz clic y elige; escribe para filtrar.",
 search="¿No está? Busca nombre/símbolo", search_help="Déjalo vacío para usar la selección de arriba.",
 search_pick="Elige de los resultados", compare="Comparar (de la lista)",
 compare_help="Añade empresas para comparar en el mismo gráfico.",
 compare_extra="¿No está? Escribe símbolos (coma)", compare_extra_help="p. ej. GOOGL, BTC-USD. Opcional.",
 currency="Moneda", real="Mostrar ajustado por inflación (real)",
 real_help="Poder adquisitivo real, ajustado por el IPC de EE. UU.",
 method="Tipo de inversión", lump="De una vez (todo junto)", dca="Mensual (un poco cada mes)",
 amount="Cantidad invertida", monthly="¿Cuánto cada mes?", yearly_inc="Aumentar aporte cada año (%)",
 start="Inicio", end="Fin", calc="Calcular",
 intro="Elige a la izquierda una (o varias) empresas, un importe y fechas. Cada resultado se compara "
       "con el índice bursátil (SPY). No es asesoramiento; muestra el pasado.",
 err_dates="La fecha de inicio debe ser anterior a la de fin.", spinner="Calculando...",
 err_nodata="No se encontraron datos. Revisa el nombre/símbolo.",
 cap_fx="Nota: sin datos de tipo de cambio; se muestra en USD.",
 cap_skip="No encontrado y omitido: ", cap_cpi="Nota: sin datos de inflación (IPC); se muestra nominal.",
 cap_real="🔎 Modo real: valores ajustados por inflación de EE. UU. (poder adquisitivo de {bas}).",
 sentence="Si hubieras invertido <b>{tutar}</b> en <b>{ad}</b> entre <b>{bas} – {bit}</b>{ek}, "
          "al final serían <b>{son}</b> — unas <b>{kar} {kz}</b> ({get}).",
 ekdca=" ({aylik}/mes, {top} en total)", kar="de ganancia", zarar="de pérdida",
 card_final="Valor final", card_yearly="Media anual (aprox.)", yearly_sub="crecimiento anual",
 card_vs="Frente al índice (SPY)", beat="Superó al índice ✅", below="Por debajo del índice ⚠️",
 multi_top="Mejor con <b>{tutar}</b> entre <b>{bas} – {bit}</b>: <b>{ad}</b> ({get}).",
 index_spy="Índice (SPY)", hover_diff="Frente al índice", hover_fx="Cambio ese día (1$)",
 hover_index="Índice", yaxis="Valor",
 share_dl="📥 Descargar imagen", share_tw="🐦 Twitter/X", share_li="💼 LinkedIn",
 share_tip="Consejo: comparte la imagen en Instagram, WhatsApp, donde quieras.",
 tweet="Si hubiera invertido {tutar} en {ad} el {bas}, ¡hoy serían {son}! #YSiHubierasInvertido",
 info="👈 Configura a la izquierda y pulsa **Calcular**. Usa los escenarios de arriba para probar rápido.",
 about_title="ℹ️ Sobre esta herramienta / aviso",
 about="Herramienta educativa basada solo en datos pasados. No es asesoramiento. Un único ganador "
       "no es 'dinero fácil' — elegirlo de antemano era imposible; por eso cada resultado se compara "
       "con el índice (SPY). Cambio histórico para €/₺. Datos: Yahoo Finance.",
 img_title="¿Y si hubieras invertido?", img_inv="{yat} invertido → {get}", img_idx="En el índice (SPY): {s}",
),
"ar": dict(
 title="📈 لو كنت استثمرت؟", settings="الإعدادات", try_preset="جرّب سيناريو:",
 p_pandemic="🚀 1000$ في Apple بداية الجائحة", p_dca="📈 100$ شهريًا في NVDA لمدة 5 سنوات",
 p_2008="🏛️ SPY منذ أزمة 2008", p_vs="⚔️ Apple ضد Microsoft ضد Nvidia",
 company="الشركة (اختر من القائمة)", company_help="انقر واختر؛ اكتب للتصفية.",
 search="غير موجودة؟ ابحث بالاسم/الرمز", search_help="اتركه فارغًا لاستخدام الاختيار أعلاه.",
 search_pick="اختر من النتائج", compare="قارن (من القائمة)",
 compare_help="أضف شركات للمقارنة على نفس الرسم.",
 compare_extra="غير موجودة؟ اكتب الرموز (بفواصل)", compare_extra_help="مثل GOOGL, BTC-USD. اختياري.",
 currency="العملة", real="عرض معدّل حسب التضخم (حقيقي)",
 real_help="القوة الشرائية الحقيقية معدّلة بمؤشر أسعار المستهلك الأمريكي.",
 method="نوع الاستثمار", lump="دفعة واحدة", dca="شهريًا (قليل كل شهر)",
 amount="المبلغ المستثمر", monthly="كم كل شهر؟", yearly_inc="زيادة المساهمة سنويًا (%)",
 start="البداية", end="النهاية", calc="احسب",
 intro="اختر من اليسار شركة (أو أكثر) ومبلغًا وتواريخ. تُقارن كل نتيجة بمؤشر السوق (SPY). "
       "ليست نصيحة استثمارية؛ تعرض الماضي فقط.",
 err_dates="يجب أن يكون تاريخ البداية قبل النهاية.", spinner="جارٍ الحساب...",
 err_nodata="لا توجد بيانات. تحقق من الاسم/الرمز.",
 cap_fx="ملاحظة: بيانات الصرف غير متوفرة؛ العرض بالدولار.",
 cap_skip="غير موجود وتم تخطيه: ", cap_cpi="ملاحظة: بيانات التضخم غير متوفرة؛ العرض اسمي.",
 cap_real="🔎 الوضع الحقيقي: القيم معدّلة حسب التضخم الأمريكي (بقوة شرائية {bas}).",
 sentence="لو استثمرت <b>{tutar}</b> في <b>{ad}</b> بين <b>{bas} – {bit}</b>{ek}، "
          "لأصبحت في النهاية <b>{son}</b> — نحو <b>{kar} {kz}</b> ({get}).",
 ekdca=" ({aylik} شهريًا، الإجمالي {top})", kar="ربح", zarar="خسارة",
 card_final="القيمة النهائية", card_yearly="المتوسط السنوي (تقريبي)", yearly_sub="نمو سنوي",
 card_vs="مقابل المؤشر (SPY)", beat="تفوّق على المؤشر ✅", below="أقل من المؤشر ⚠️",
 multi_top="الأفضل باستثمار <b>{tutar}</b> بين <b>{bas} – {bit}</b>: <b>{ad}</b> ({get}).",
 index_spy="المؤشر (SPY)", hover_diff="مقابل المؤشر", hover_fx="السعر ذلك اليوم (1$)",
 hover_index="المؤشر", yaxis="القيمة",
 share_dl="📥 تنزيل الصورة", share_tw="🐦 Twitter/X", share_li="💼 LinkedIn",
 share_tip="نصيحة: شارك الصورة على Instagram أو WhatsApp أو أي مكان.",
 tweet="لو استثمرت {tutar} في {ad} بتاريخ {bas} لأصبحت اليوم {son}! #لو_كنت_استثمرت",
 info="👈 اضبط الخيارات على اليسار واضغط **احسب**. للتجربة السريعة استخدم السيناريوهات أعلاه.",
 about_title="ℹ️ حول الأداة / تنويه",
 about="أداة تعليمية تعتمد على بيانات ماضية فقط. ليست نصيحة استثمارية. رابح واحد لا يعني 'مالًا سهلًا' "
       "— اختياره مسبقًا كان مستحيلًا؛ لذلك تُقارن كل نتيجة بالمؤشر (SPY). يُطبّق سعر صرف تاريخي لـ €/₺. "
       "المصدر: Yahoo Finance.",
 img_title="If You Had Invested", img_inv="{yat} invested → {get}", img_idx="Index (SPY): {s}",
),
}

# ==================== VERI ====================
POPULER = {
 "AAPL":"Apple","MSFT":"Microsoft","NVDA":"NVIDIA","AMZN":"Amazon","GOOGL":"Alphabet (Google)",
 "META":"Meta","TSLA":"Tesla","JPM":"JPMorgan","V":"Visa","MA":"Mastercard","KO":"Coca-Cola",
 "PEP":"PepsiCo","DIS":"Disney","NFLX":"Netflix","AMD":"AMD","INTC":"Intel","ORCL":"Oracle",
 "ADBE":"Adobe","CRM":"Salesforce","NKE":"Nike","MCD":"McDonald's","SBUX":"Starbucks",
 "BA":"Boeing","XOM":"Exxon","PFE":"Pfizer","BAC":"Bank of America","WMT":"Walmart",
 "COST":"Costco","HD":"Home Depot","UBER":"Uber","PLTR":"Palantir","COIN":"Coinbase",
 "SPY":"S&P 500","QQQ":"Nasdaq 100","BTC-USD":"Bitcoin","ETH-USD":"Ethereum","GLD":"Gold",
}
KATALOG = [f"{ad} ({tk})" for tk, ad in POPULER.items()]
KATALOG_MAP = {f"{ad} ({tk})": tk for tk, ad in POPULER.items()}

_CPI_YILLIK = {
    2000:169.3,2001:175.6,2002:177.7,2003:181.7,2004:185.2,2005:190.7,2006:198.3,2007:202.4,
    2008:211.1,2009:211.1,2010:216.7,2011:220.2,2012:226.7,2013:230.3,2014:233.9,2015:233.7,
    2016:236.9,2017:242.8,2018:247.9,2019:251.7,2020:257.9,2021:261.6,2022:281.1,2023:299.2,
    2024:308.4,2025:317.6,2026:324.4,2027:331.0,
}

@st.cache_data
def cpi_serisi():
    s = pd.Series(_CPI_YILLIK); s.index = pd.to_datetime([f"{y}-01-01" for y in s.index])
    return s.sort_index().resample("MS").interpolate("linear")

def reel_ayarla(curve, cpi):
    if cpi is None: return None
    c = cpi.reindex(curve.index, method="ffill").ffill().bfill()
    if c.isna().all(): return None
    return curve * (float(c.iloc[0]) / c)

@st.cache_data(ttl=3600)
def hisse_ara(sorgu):
    s = sorgu.strip().lower(); sonuc = []
    for tk, ad in POPULER.items():
        if s in ad.lower() or s in tk.lower():
            sonuc.append((tk, f"{ad} ({tk})"))
    try:
        r = requests.get("https://query2.finance.yahoo.com/v1/finance/search",
                         params={"q": sorgu, "quotesCount": 10, "newsCount": 0},
                         headers={"User-Agent": "Mozilla/5.0"}, timeout=6)
        for q in r.json().get("quotes", []):
            if q.get("quoteType") != "EQUITY": continue
            tk = q.get("symbol", ""); ad = q.get("shortname") or tk
            if tk and tk not in [x[0] for x in sonuc]:
                sonuc.append((tk, f"{ad} ({tk}) · {q.get('exchDisp','')}"))
    except Exception:
        pass
    return sonuc[:15]

@st.cache_data(ttl=3600)
def fiyat_indir(ticker, bas, bit):
    df = yf.download(ticker, start=str(bas), end=str(bit), auto_adjust=True, progress=False)
    if df.empty: return None
    close = df["Close"]
    if isinstance(close, pd.DataFrame): close = close.iloc[:, 0]
    return close.dropna()

def kur_serisi(sembol, bas, bit):
    if sembol == "$": return None
    try:
        if sembol == "€": return 1.0 / fiyat_indir("EURUSD=X", bas, bit)
        if sembol == "₺": return fiyat_indir("USDTRY=X", bas, bit)
    except Exception:
        return None
    return None

def _kur_hazirla(kur, idx):
    if kur is None: kur = pd.Series(1.0, index=idx)
    return kur.reindex(idx).ffill().bfill()

def lump_deger(fiyat_usd, tutar, kur):
    kur = _kur_hazirla(kur, fiyat_usd.index)
    adet = (tutar / float(kur.iloc[0])) / float(fiyat_usd.iloc[0])
    return adet * fiyat_usd * kur, tutar

def dca_deger(fiyat_usd, aylik_tutar, artis, kur):
    kur = _kur_hazirla(kur, fiyat_usd.index)
    ilk = fiyat_usd.groupby(fiyat_usd.index.to_period("M")).head(1)
    kum = pd.Series(0.0, index=fiyat_usd.index); adet = 0.0; yatirilan = 0.0
    for i, (t, pv) in enumerate(ilk.items()):
        katki = aylik_tutar * (1 + artis) ** (i // 12)
        adet += (katki / float(kur.loc[t])) / float(pv)
        yatirilan += katki
        kum.loc[fiyat_usd.index >= t] = adet
    return kum * fiyat_usd * kur, yatirilan

def metrik(egri, yatirilan):
    son = float(egri.iloc[-1]); n = len(egri)
    getiri = (son - yatirilan) / yatirilan * 100
    yillik = ((son / yatirilan) ** (252 / n) - 1) * 100 if n > 1 and son > 0 else 0
    return son, getiri, yillik

def para(x, s="€"):
    return f"{x:,.0f}".replace(",", ".") + " " + s

def yuzde(x):
    return f"{x:+.0f}%"

def sparkline(seri, renk="#2563eb", w=150, h=36):
    v = seri.values.astype(float)
    if len(v) > 80: v = v[:: max(1, len(v) // 80)]
    lo, hi = float(np.nanmin(v)), float(np.nanmax(v)); rng = (hi - lo) or 1.0; n = len(v)
    pts = " ".join(f"{w*i/(max(1,n-1)):.1f},{h-3-(h-6)*(x-lo)/rng:.1f}" for i, x in enumerate(v))
    return (f'<svg width="100%" height="{h}" viewBox="0 0 {w} {h}" preserveAspectRatio="none" '
            f'style="margin-top:8px;display:block"><polyline fill="none" stroke="{renk}" '
            f'stroke-width="2" points="{pts}"/></svg>')

def kart(baslik, deger, alt, alt_sinif="", spark=""):
    return (f'<div class="kart"><div class="kpi-baslik">{baslik}</div>'
            f'<div class="kpi-deger">{deger}</div>'
            f'<div class="kpi-alt {alt_sinif}">{alt}</div>{spark}</div>')

def ozet_gorseli(L, ad, bas, bit, yatirilan, son, getiri, s_son, sembol):
    fig, ax = plt.subplots(figsize=(6.4, 3.35), dpi=200)
    fig.patch.set_facecolor("#14213d"); ax.axis("off")
    renk = "#4ade80" if son >= yatirilan else "#f87171"
    ax.text(0.5, 0.90, L["img_title"], ha="center", color="#fff", fontsize=16,
            fontweight="bold", transform=ax.transAxes)
    ax.text(0.5, 0.74, f"{ad} · {bas} – {bit}", ha="center", color="#c7d0e0",
            fontsize=10, transform=ax.transAxes)
    ax.text(0.5, 0.50, para(son, sembol), ha="center", color=renk, fontsize=30,
            fontweight="bold", transform=ax.transAxes)
    ax.text(0.5, 0.34, L["img_inv"].format(yat=para(yatirilan, sembol), get=yuzde(getiri)),
            ha="center", color="#fff", fontsize=12, transform=ax.transAxes)
    ax.text(0.5, 0.15, L["img_idx"].format(s=para(s_son, sembol)),
            ha="center", color="#9aa7bd", fontsize=9, transform=ax.transAxes)
    buf = io.BytesIO(); fig.savefig(buf, format="png", bbox_inches="tight",
                                    facecolor=fig.get_facecolor()); plt.close(fig)
    return buf.getvalue()

RENKLER = ["#2563eb", "#dc2626", "#16a34a", "#d97706", "#7c3aed"]
BUGUN = date.today()

# Preset ayarlari (etiket L'den gelir). k_yontem: 0=tek, 1=dca
PRESETS = [
    ("p_pandemic", dict(k_ana="Apple (AAPL)", k_sorgu="", k_ekstra="", k_tutar=1000.0,
        k_sembol="$", k_bas=date(2020, 3, 1), k_bit=BUGUN, k_yontem=0)),
    ("p_dca", dict(k_ana="NVIDIA (NVDA)", k_sorgu="", k_ekstra="", k_aylik=100.0, k_artis=0,
        k_sembol="$", k_bas=BUGUN - timedelta(days=365*5), k_bit=BUGUN, k_yontem=1)),
    ("p_2008", dict(k_ana="S&P 500 (SPY)", k_sorgu="", k_ekstra="", k_tutar=1000.0,
        k_sembol="$", k_bas=date(2008, 9, 1), k_bit=BUGUN, k_yontem=0)),
    ("p_vs", dict(k_ana="Apple (AAPL)", k_sorgu="", k_ekstra="MSFT, NVDA", k_tutar=1000.0,
        k_sembol="$", k_bas=date(2019, 1, 1), k_bit=BUGUN, k_yontem=0)),
]
_def = dict(k_ana="Apple (AAPL)", k_sorgu="", k_ekstra="", k_tutar=1000.0, k_aylik=100.0,
            k_artis=0, k_sembol="€", k_bas=date(2020, 1, 1), k_bit=BUGUN, k_yontem=0)
for k, v in _def.items():
    st.session_state.setdefault(k, v)

# ==================== DIL + TEMA ====================
DARK_LBL = {"tr":"🌙 Karanlık mod","en":"🌙 Dark mode","de":"🌙 Dunkelmodus",
            "ru":"🌙 Тёмная тема","es":"🌙 Modo oscuro","ar":"🌙 الوضع الداكن"}
def palet(koyu):
    if koyu:
        return dict(bg="#0f1420", panel="#1a2233", border="#2a3550", text="#e8eaed", muted="#9aa7bd")
    return dict(bg="#f7f9fc", panel="#ffffff", border="#e6eaf0", text="#14213d", muted="#6b7280")

# Dil + tema sayfalar arasi KALICI tutulur (normal anahtar; widget anahtari sayfa
# degisince silinebildigi icin Turkce'ye donuyordu).
st.session_state.setdefault("dil_ad", "Türkçe")
st.session_state.setdefault("tema_koyu", False)
_diller = list(DILLER.keys())
_idx = _diller.index(st.session_state["dil_ad"]) if st.session_state["dil_ad"] in _diller else 0
dil_ad = st.sidebar.selectbox("🌐 Language / Dil", _diller, index=_idx)
st.session_state["dil_ad"] = dil_ad
lang = DILLER[dil_ad]
L = T[lang]
koyu = st.sidebar.toggle(DARK_LBL.get(lang, "🌙 Dark"), value=st.session_state["tema_koyu"])
st.session_state["tema_koyu"] = koyu
P = palet(koyu)
btn_css = (f'.stDownloadButton button, [data-testid="stLinkButton"] a '
           f'{{ background:{P["panel"]}; color:{P["text"]}; border:1px solid {P["border"]}; }}'
           if koyu else "")

st.markdown(f"""
<style>
  {btn_css}
  .stApp {{ background:{P['bg']}; }}
  [data-testid="stSidebar"] {{ background:{P['panel']}; }}
  .stApp, [data-testid="stSidebar"], h1, h2, h3, label, p, span, .stMarkdown {{ color:{P['text']}; }}
  h1 {{ font-weight:800; }}
  .kart {{ background:{P['panel']}; border:1px solid {P['border']}; border-radius:16px;
          padding:18px 20px; box-shadow:0 1px 3px rgba(0,0,0,.08); margin-bottom:8px; }}
  .kpi-baslik {{ color:{P['muted']}; font-size:13px; font-weight:600; }}
  .kpi-deger {{ font-size:28px; font-weight:800; color:{P['text']}; margin-top:4px; }}
  .kpi-alt {{ font-size:15px; font-weight:700; margin-top:2px; }}
  .yesil {{ color:#16a34a; }} .kirmizi {{ color:#dc2626; }}
  .cumle {{ background:{P['panel']}; border-radius:16px; padding:20px 24px; font-size:20px;
           color:{P['text']}; line-height:1.6; border-left:6px solid #16a34a; }}
  .cumle.zarar {{ border-left-color:#dc2626; }}
  {"[data-testid='stAppViewContainer'],[data-testid='stSidebar']{direction:rtl;text-align:right}" if lang=="ar" else ""}
</style>
""", unsafe_allow_html=True)

# ==================== SIDEBAR ====================
with st.sidebar:
    st.header(L["settings"])
    st.caption(L["try_preset"])
    for key, ayar in PRESETS:
        if st.button(L[key], width="stretch"):
            for k, v in ayar.items():
                st.session_state[k] = v
            st.rerun()
    st.divider()

    ana_lbl = st.selectbox(L["company"], KATALOG, key="k_ana", help=L["company_help"])
    secilen, secilen_ad = KATALOG_MAP[ana_lbl], ana_lbl.split(" (")[0]
    serbest = st.text_input(L["search"], key="k_sorgu", help=L["search_help"])
    if serbest.strip():
        bulunan = hisse_ara(serbest)
        if bulunan:
            etiketler = [e for _, e in bulunan]
            secim = st.selectbox(L["search_pick"], etiketler, key="k_sonuc")
            i = etiketler.index(secim)
            secilen, secilen_ad = bulunan[i][0], bulunan[i][1].split(" (")[0]
        else:
            secilen, secilen_ad = serbest.upper().strip(), serbest.strip()

    secili_etk = st.multiselect(L["compare"], KATALOG, help=L["compare_help"])
    ekstra = st.text_input(L["compare_extra"], key="k_ekstra", help=L["compare_extra_help"])

    sembol = st.selectbox(L["currency"], ["€", "$", "₺"], key="k_sembol")
    reel = st.checkbox(L["real"], help=L["real_help"])
    yontem = st.radio(L["method"], [0, 1], key="k_yontem",
                      format_func=lambda i: L["lump"] if i == 0 else L["dca"])
    tek_mi = (yontem == 0)
    if tek_mi:
        tutar = st.number_input(L["amount"], min_value=1.0, step=100.0, key="k_tutar")
        aylik = artis = None
    else:
        aylik = st.number_input(L["monthly"], min_value=1.0, step=50.0, key="k_aylik")
        artis = st.slider(L["yearly_inc"], 0, 30, key="k_artis") / 100.0

    c_b, c_e = st.columns(2)
    bas = c_b.date_input(L["start"], key="k_bas", min_value=date(2000, 1, 1), max_value=BUGUN)
    bit = c_e.date_input(L["end"], key="k_bit", min_value=date(2000, 1, 2), max_value=BUGUN)
    hesapla = st.button(L["calc"], type="primary", width="stretch")

# ==================== ANA ALAN ====================
try:
    st.image("assets/logo_lockup.png", width=380)
except Exception:
    pass
st.title(L["title"])
st.caption(L["intro"])

def hesapla_egri(fiyat_usd):
    if tek_mi:
        return lump_deger(fiyat_usd, tutar, kur)
    return dca_deger(fiyat_usd, aylik, artis, kur)

def ad_ver(kod):
    if kod == secilen: return secilen_ad
    return POPULER.get(kod, kod)

if hesapla:
    if bas >= bit:
        st.error(L["err_dates"])
    else:
        kodlar = ([secilen] + [KATALOG_MAP[e] for e in secili_etk]
                  + [x.strip().upper() for x in ekstra.split(",") if x.strip()])
        gor = set(); kodlar = [k for k in kodlar if k and not (k in gor or gor.add(k))][:5]
        with st.spinner(L["spinner"]):
            ham = {k: fiyat_indir(k, bas, bit) for k in kodlar}
            spy = fiyat_indir("SPY", bas, bit)
            kur = kur_serisi(sembol, bas, bit)
            cpi = cpi_serisi() if reel else None
        ham = {k: v for k, v in ham.items() if v is not None}
        if not ham or spy is None:
            st.error(L["err_nodata"])
        else:
            if sembol != "$" and kur is None:
                st.caption(L["cap_fx"])
            eksik = [k for k in kodlar if k not in ham]
            if eksik:
                st.caption(L["cap_skip"] + ", ".join(eksik))
            reel_aktif = reel and cpi is not None
            if reel and not reel_aktif:
                st.caption(L["cap_cpi"])

            ortak = spy.index
            for v in ham.values():
                ortak = ortak.intersection(v.index)
            spy = spy.loc[ortak]

            def belki_reel(curve):
                if reel_aktif:
                    r = reel_ayarla(curve, cpi)
                    if r is not None: return r
                return curve

            spy_egri, yat = hesapla_egri(spy); spy_egri = belki_reel(spy_egri)
            s_son = float(spy_egri.iloc[-1])

            def _hesap(v):
                e, y = hesapla_egri(v.loc[ortak]); e = belki_reel(e)
                return e, y, metrik(e, y)
            hesap = {k: _hesap(v) for k, v in ham.items()}
            bas_s, bit_s = bas.strftime("%d.%m.%Y"), bit.strftime("%d.%m.%Y")
            if reel_aktif:
                st.caption(L["cap_real"].format(bas=bas_s))

            # ---------- TEK HISSE ----------
            if len(hesap) == 1:
                k = next(iter(hesap)); h_egri, y, (h_son, h_get, h_yil) = hesap[k]
                kar = h_son - y; kz = L["kar"] if kar >= 0 else L["zarar"]
                ek = L["ekdca"].format(aylik=para(aylik, sembol), top=para(y, sembol)) if not tek_mi else ""
                sinif = "cumle" if kar >= 0 else "cumle zarar"
                st.markdown(f'<div class="{sinif}">' + L["sentence"].format(
                    bas=bas_s, bit=bit_s, ad=ad_ver(k), tutar=para(y, sembol), ek=ek,
                    son=para(h_son, sembol), kar=para(abs(kar), sembol), kz=kz, get=yuzde(h_get)) +
                    '</div>', unsafe_allow_html=True)
                st.write("")
                h_renk = "#16a34a" if kar >= 0 else "#dc2626"
                c1, c2, c3 = st.columns(3)
                c1.markdown(kart(L["card_final"], para(h_son, sembol), yuzde(h_get),
                            "yesil" if kar >= 0 else "kirmizi", sparkline(h_egri, h_renk)),
                            unsafe_allow_html=True)
                c2.markdown(kart(L["card_yearly"], f"{h_yil:+.1f}%", L["yearly_sub"]),
                            unsafe_allow_html=True)
                c3.markdown(kart(L["card_vs"], para(s_son, sembol),
                            L["beat"] if h_son >= s_son else L["below"],
                            "yesil" if h_son >= s_son else "kirmizi",
                            sparkline(spy_egri, "#9aa7bd")), unsafe_allow_html=True)
                st.write("")
                seriler = [(ad_ver(k), h_egri)]
                png = ozet_gorseli(L, ad_ver(k), bas_s, bit_s, y, h_son, h_get, s_son, sembol)
            # ---------- COKLU ----------
            else:
                sirali = sorted(hesap.items(), key=lambda kv: kv[1][2][0], reverse=True)
                st.markdown('<div class="cumle">' + L["multi_top"].format(
                    bas=bas_s, bit=bit_s, tutar=para(yat, sembol),
                    ad=ad_ver(sirali[0][0]), get=yuzde(sirali[0][1][2][1])) + '</div>',
                    unsafe_allow_html=True)
                st.write("")
                sut = st.columns(len(sirali) + 1)
                for idx, (k, (egri, y, (son, get, yil))) in enumerate(sirali):
                    tac = "🏆 " if idx == 0 else ""
                    renk = "#16a34a" if son >= y else "#dc2626"
                    sut[idx].markdown(kart(f"{tac}{ad_ver(k)}", para(son, sembol), yuzde(get),
                        "yesil" if son >= y else "kirmizi", sparkline(egri, renk)),
                        unsafe_allow_html=True)
                sut[-1].markdown(kart(L["index_spy"], para(s_son, sembol),
                    yuzde((s_son - yat) / yat * 100), "", sparkline(spy_egri, "#9aa7bd")),
                    unsafe_allow_html=True)
                st.write("")
                seriler = [(ad_ver(k), egri) for k, (egri, _, _) in sirali]
                png = None

            # ---------- GRAFIK ----------
            kur_gost = None if sembol == "$" else _kur_hazirla(kur, spy_egri.index)
            fig = go.Figure()
            for idx, (ad, egri) in enumerate(seriler):
                fark = (egri - spy_egri.reindex(egri.index)).values
                cd = (np.column_stack([fark, kur_gost.reindex(egri.index).values])
                      if kur_gost is not None else fark.reshape(-1, 1))
                ht = ("%{x|%d.%m.%Y}<br>" + ad + ": %{y:,.0f} " + sembol +
                      "<br>" + L["hover_diff"] + ": %{customdata[0]:,.0f} " + sembol)
                if kur_gost is not None:
                    ht += "<br>" + L["hover_fx"] + ": %{customdata[1]:,.2f} " + sembol
                fig.add_trace(go.Scatter(x=egri.index, y=egri.values, name=ad,
                    line=dict(color=RENKLER[idx % len(RENKLER)], width=2.5),
                    customdata=cd, hovertemplate=ht + "<extra></extra>"))
            fig.add_trace(go.Scatter(x=spy_egri.index, y=spy_egri.values, name=L["hover_index"],
                line=dict(color="#9aa7bd", width=2, dash="dot"),
                hovertemplate="%{x|%d.%m.%Y}<br>" + L["hover_index"] + ": %{y:,.0f} " + sembol + "<extra></extra>"))
            fig.update_layout(hovermode="x unified", height=450, margin=dict(l=10, r=10, t=30, b=10),
                legend=dict(orientation="h", y=1.12), plot_bgcolor=P["panel"], paper_bgcolor=P["panel"],
                font=dict(color=P["text"]), yaxis_title=L["yaxis"] + " (" + sembol + ")")
            st.plotly_chart(fig, use_container_width=True)

            # ---------- PAYLASIM ----------
            if png is not None:
                metin = L["tweet"].format(ad=secilen_ad, bas=bas_s, tutar=para(yat, sembol),
                                          son=para(h_son, sembol))
                p1, p2, p3 = st.columns(3)
                p1.download_button(L["share_dl"], data=png, file_name=f"invest_{secilen}.png",
                                   mime="image/png", width="stretch")
                tw = "https://twitter.com/intent/tweet?" + urllib.parse.urlencode({"text": metin})
                p2.link_button(L["share_tw"], tw, width="stretch")
                li = "https://www.linkedin.com/feed/?" + urllib.parse.urlencode(
                    {"shareActive": "true", "text": metin})
                p3.link_button(L["share_li"], li, width="stretch")
                st.caption(L["share_tip"])
else:
    st.info(L["info"])

st.divider()
with st.expander(L["about_title"]):
    st.write(L["about"])
