"""İsteğe bağlı İngilizce sürüm: güncel Türkçe e-posta, başvurunun kayıtlarıyla birlikte o anda çevrilir.

Çeviri kararı, gerekçeyi, sayıları, Başvuru ID'yi ve üslubu korumalıdır; kod ile kontrol edilir.
"""
import json
import re

from core import llm
from core.son_kontrol import SAYI

SISTEM = """You translate a Turkish rejection-feedback email for the Junior Wings programme into English.
The email will be reviewed by HR before sending. Keep the context exactly:
1. Translate faithfully. Do not add, remove or soften any fact, reason, number or the decision itself.
2. Keep every number, score and threshold exactly as written, and keep the application ID {basvuru_id} unchanged.
3. Keep the tone: corporate but warm, polite, plain English; address the candidate directly ("you").
4. Do not add language levels (A1–C2, CEFR), personality judgements, comparisons with other candidates,
   promises about the future, re-evaluation or dates.
5. Use the attached application records only to choose the right terms (for example the stage name);
   never add information from them that is not in the Turkish email.
6. If a phrase cannot be translated without changing its meaning, list it in "anlam_farki_notlari" (in Turkish);
   otherwise leave the list empty."""

SEMA = {
    "type": "object",
    "properties": {
        "email_subject": {"type": "string"},
        "email_body": {"type": "string"},
        "anlam_farki_notlari": {"type": "array", "items": {"type": "string"}},
    },
    "required": ["email_subject", "email_body", "anlam_farki_notlari"],
    "additionalProperties": False,
}

YASAK_EN = [
    (r"\b(?:a1|a2|b1|b2|c1|c2)\b|\bcefr\b|\b(?:language|english|proficiency) level", "Dil seviyesi ifadesi"),
    (r"\b(?:personality|introvert)", "Kişilik yorumu"),
    (r"\bother (?:candidates|applicants)\b|\bcompared (?:to|with) other", "Başka adaylarla kıyas"),
    (r"\b(?:in the future|next (?:term|period|year)|reconsider|guarantee|will be (?:accepted|hired)|priority)\b", "Vaat ya da gelecek sözü"),
    (r"\b(?:by \w+ \d|within \d+ (?:days|weeks)|at the latest)\b", "Tarih ya da süre sözü"),
]
KONTENJAN_EN = (r"\b(?:lack|insufficient|inadequa|shortcoming|improve|develop)", "Kontenjan reddinde yetersizlik ya da öneri ifadesi")


def kontrol(girdi: dict, tr_konu: str, tr_metin: str, en_konu: str, en_metin: str) -> list[dict]:
    """Bağlamın korunup korunmadığını kod ile denetler; boş liste geçti demektir."""
    b = girdi["basvuru_id"]
    sorunlar = []
    sayilar = lambda m: sorted(SAYI.findall(m.replace(b, " ")))
    tr, en = sayilar(f"{tr_konu}\n{tr_metin}"), sayilar(f"{en_konu}\n{en_metin}")
    if tr != en:
        eksik = sorted(set(tr) - set(en))
        fazla = sorted(set(en) - set(tr))
        sorunlar.append({"kod": "SAYI_FARKI", "aciklama": "Sayılar Türkçe metinle aynı değil"
                         + (f"; eksik: {', '.join(eksik)}" if eksik else "") + (f"; fazla: {', '.join(fazla)}" if fazla else "")})
    if b not in en_metin:
        sorunlar.append({"kod": "BASVURU_ID_YOK", "aciklama": f"İngilizce metinde Başvuru ID ({b}) yok."})
    kucuk = en_metin.lower() + "\n" + en_konu.lower()
    for desen, ad in YASAK_EN + ([KONTENJAN_EN] if girdi["gerekce_turu"] == "kontenjan" else []):
        bulunan = sorted({m.group(0) for m in re.finditer(desen, kucuk)})
        if bulunan:
            sorunlar.append({"kod": "YASAK_IFADE", "aciklama": f"{ad}: {', '.join(bulunan)}"})
    tr_kelime, en_kelime = len(tr_metin.split()), len(en_metin.split())
    if tr_kelime and not 0.6 <= en_kelime / tr_kelime <= 1.8:
        sorunlar.append({"kod": "UZUNLUK_FARKI", "aciklama": f"Uzunluk çok farklı ({tr_kelime} → {en_kelime} kelime); "
                         "eksik ya da eklenmiş bölüm olabilir."})
    return sorunlar


def cevir(girdi: dict, tr_konu: str, tr_metin: str, cagir=None) -> dict:
    cagir = cagir or llm.cagir
    sistem = SISTEM.format(basvuru_id=girdi["basvuru_id"])
    kullanici = ("Turkish email subject:\n" + tr_konu + "\n\nTurkish email body:\n" + tr_metin
                 + "\n\nApplication records (context only):\n" + json.dumps(girdi, ensure_ascii=False, indent=2))
    yanit = cagir(sistem, kullanici, SEMA, amac="ingilizce", basvuru_id=girdi["basvuru_id"])
    veri = yanit.veri
    if not isinstance(veri, dict) or not all(k in veri for k in SEMA["required"]):
        raise llm.ModelHatasi("Çeviri yanıtı beklenen JSON yapısında değil.")
    konu, metin = str(veri["email_subject"]).strip(), str(veri["email_body"]).strip()
    return {"konu": konu, "metin": metin, "notlar": [str(x) for x in veri["anlam_farki_notlari"]],
            "kontrol": kontrol(girdi, tr_konu, tr_metin, konu, metin)}
