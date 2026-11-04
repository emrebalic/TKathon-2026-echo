"""Taslaktan sonra kod ile yapılan kontrol. Hem model çıktısına hem İK düzeltmesine uygulanır.

Sorun bulunursa taslak "İK dikkat" olarak işaretlenir; otomatik düzeltme yapılmaz.
"""
import json
import re

KELIME_ALT, KELIME_UST = 80, 120

# Küçük harfe çevrilmiş metinde, kelime başından aranır (bkz. _kucuk); "gözden geçirin" gibi kelime içi eşleşmeler sayılmaz.
YASAK = [
    (r"\b(?:a1|a2|b1|b2|c1|c2)\b|\b(?:cefr|dil seviye|seviyeniz|seviyesinde)", "Dil seviyesi ifadesi"),
    (r"\b(?:içine kapanık|kişiliğ|karakteriniz|uyumsuz|özgüven)", "Kişilik yorumu"),
    (r"\b(?:diğer adaylar|başka adaylar|adaylar arasında|daha güçlü aday|rakip)", "Başka adaylarla kıyas"),
    (r"\b(?:ileride|gelecek dönem|bir sonraki dönem|yeniden değerlendiril|tekrar değerlendiril|kabul edileceksiniz|"
     r"işe alınacak|garanti|öncelik tanı)", "Vaat ya da gelecek sözü"),
    (r"\b(?:tekrar başvur|yeniden başvur)", "Kayıtta olmayan bilgi: yeniden başvuru"),
    (r"\b(?:en geç|tarihine kadar|gün içinde|hafta içinde)\b", "Tarih ya da süre sözü"),
]
KONTENJAN_YASAK = (r"\b(?:eksik|yetersiz|geliştir|iyileştir|güçlendir|öneri)", "Kontenjan reddinde yetersizlik ya da öneri ifadesi")
IC_KOD = re.compile(r"\bKP-\d|T101|GRP-[A-Z]|KURUM_ICI|PAYLASILABILIR|\b(?:AS|SN|DL|IK|KR)-\d{3}")
SAYI = re.compile(r"\d+(?:[.,]\d+)?")


def _kucuk(metin: str) -> str:
    return metin.replace("İ", "i").replace("I", "ı").lower()


def kontrol_et(girdi: dict, konu: str, metin: str, kullanilan_idler: list) -> list[dict]:
    """Sorun listesi döndürür; boş liste geçti demektir."""
    sorunlar = []
    b = girdi["basvuru_id"]
    verilen = {k["kayit_id"] for k in girdi["kayitlar"]}

    yabanci = [i for i in kullanilan_idler if i not in verilen]
    if yabanci:
        sorunlar.append({"kod": "YABANCI_KAYIT", "aciklama": f"Modele verilmeyen kayıtlar kullanılmış: {', '.join(yabanci)}"})
    if not kullanilan_idler:
        sorunlar.append({"kod": "KAYNAK_YOK", "aciklama": "Taslak hangi kayda dayandığını belirtmiyor."})

    girdi_sayilari = set(SAYI.findall(json.dumps(girdi, ensure_ascii=False)))
    tam = f"{konu}\n{metin}"
    fazla = sorted({s for s in SAYI.findall(tam.replace(b, " ")) if s not in girdi_sayilari})
    if fazla:
        sorunlar.append({"kod": "KAYITTA_OLMAYAN_SAYI", "aciklama": f"Kayıtlarda geçmeyen sayılar: {', '.join(fazla)}"})

    kucuk = _kucuk(tam)
    for desen, ad in YASAK + ([KONTENJAN_YASAK] if girdi["gerekce_turu"] == "kontenjan" else []):
        bulunan = sorted({m.group(0) for m in re.finditer(desen, kucuk)})
        if bulunan:
            sorunlar.append({"kod": "YASAK_IFADE", "aciklama": f"{ad}: {', '.join(bulunan)}"})
    ic = sorted(set(IC_KOD.findall(tam)))
    if ic:
        sorunlar.append({"kod": "IC_KOD", "aciklama": f"Kurum içi kod ya da kayıt ID'si metinde: {', '.join(ic)}"})

    kelime = len(metin.split())
    if not KELIME_ALT <= kelime <= KELIME_UST:
        sorunlar.append({"kod": "UZUNLUK", "aciklama": f"Metin {kelime} kelime; karar {KELIME_ALT}–{KELIME_UST} kelime."})
    if b not in metin:
        sorunlar.append({"kod": "BASVURU_ID_YOK", "aciklama": f"Metinde Başvuru ID ({b}) yok; aday soru ya da itirazında kullanamaz."})
    return sorunlar
