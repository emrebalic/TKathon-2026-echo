"""Modele gidecek girdiyi kurar.

Yalnız ön kontrolden geçen olumsuz başvurunun, karar aşamasına ait ve paylaşılabilir kayıtları girer.
Hiç girmeyenler: kurum içi not, KURUM_ICI kayıtlar, envanter, geçilmiş aşamalar ve başka başvurular.
"""
import hashlib
import json
import re

from core import PROGRAM_ADI
from core.rules import TASLAK_UYGUN, kimlikler

IC_KOD = re.compile(r"\b(?:KP-\d{4}-\d{2}-\d{2}-\d{2}|T101[-\w]*|GRP-[A-Z0-9]+)\b\s*")
KAYIT_ATFI = re.compile(r"\b(?:AS|SN|DL|IK|KR)-\d{3}(?:-[A-Z0-9]+)*\b\s*")
BOLUM_ADLARI = {"GENEL_YETENEK": "Genel Yetenek", "INGILIZCE": "İngilizce"}
SONUC_ADLARI = {"GECTI": "geçti", "GECEMEDI": "geçemedi"}


def temizle(metin):
    """İç kodları ve kayıt ID atıflarını metinden çıkarır."""
    if not isinstance(metin, str):
        return ""
    return re.sub(r"\s{2,}", " ", KAYIT_ATFI.sub("", IC_KOD.sub("", metin))).strip()


def girdi_hash(girdi: dict) -> str:
    metin = json.dumps(girdi, ensure_ascii=False, sort_keys=True, default=str)
    return hashlib.sha256(metin.encode("utf-8")).hexdigest()


def _tablo_sozluk(motor, key, anahtar, deger):
    df = motor.t.get(key)
    if df is None or anahtar not in df or deger not in df:
        return {}
    return dict(zip(df[anahtar], df[deger]))


def model_girdisi(motor, d) -> dict | None:
    """Taslağa uygun değilse None döner."""
    if d.durum != TASLAK_UYGUN or d.karar_kodu != "OLUMSUZ":
        return None
    b, asama = d.basvuru_id, d.asama_kodu
    asama_adlari = _tablo_sozluk(motor, "asamalar", "asama_kodu", "asama_adi")
    beceriler = _tablo_sozluk(motor, "beceriler", "gereklilik_kodu", "gereklilik_aciklamasi")
    karar = motor._satirlar("kararlar", b).iloc[0].to_dict()
    karar_dayanak = kimlikler(karar.get("dayanak_kaynak_idleri"))

    notlar = motor._satirlar("ik_notlari", b)
    ik_not = notlar.sort_values("kayit_tarihi").iloc[-1].to_dict() if not notlar.empty else None
    kontenjan = bool(ik_not and ik_not.get("gerekce_kodu") == "KONTENJAN_KISITI")
    # Mülakat aşamaları (video, İK ve birim) daha yumuşak ve az ayrıntılı bir blokla yazılır; grup çalışması ayrı kalır.
    tur = "kontenjan" if kontenjan else {"SINAV": "sinav", "INGILIZCE": "ingilizce_gorusme",
                                         "VIDEO": "mulakat", "IK_TEKNIK": "mulakat"}.get(asama, "oznel_degerlendirme")

    kayitlar = []
    if tur == "sinav":
        for kid in karar_dayanak:
            tablo, r = motor.kayit(kid)
            if tablo == "sinav" and r.get("kayitli_sonuc") == "GECEMEDI":
                kayitlar.append({"kayit_id": kid, "tur": "sinav_bolumu", "bolum": BOLUM_ADLARI.get(r["test_turu"], r["test_turu"]),
                                 "soru_sayisi": int(r["soru_sayisi"]), "dogru_sayisi": int(r["dogru_sayisi"]),
                                 "gecme_baraji_dogru": int(r["gecme_baraji"]), "sonuc": SONUC_ADLARI[r["kayitli_sonuc"]]})
    elif tur == "ingilizce_gorusme":
        for kid in karar_dayanak:
            tablo, r = motor.kayit(kid)
            if tablo == "dil":
                kayitlar.append({"kayit_id": kid, "tur": "ingilizce_gorusmesi", "puan": int(r["kayitli_puan"]),
                                 "en_yuksek_puan": int(r["olcek_tavani"]), "gecme_baraji_puan": int(r["gecme_baraji"]),
                                 "sonuc": SONUC_ADLARI.get(r["kayitli_sonuc"], r["kayitli_sonuc"]),
                                 "degerlendirici_gozlemi": temizle(r.get("gozlem_metni"))})
    else:
        dayanak = list(dict.fromkeys(karar_dayanak + kimlikler(ik_not.get("dayanak_kaynak_idleri") if ik_not else None)))
        for kid in dayanak:
            bilgi = motor.kayit(kid)
            if not bilgi or bilgi[0] != "asama_kayitlari":
                continue
            r = bilgi[1]
            if r.get("paylasim_kodu") != "PAYLASILABILIR" or r.get("asama_kodu") != asama:
                continue
            if kontenjan and r.get("kaynak_rolu") == "IK_YETKILISI":
                kayitlar.append({"kayit_id": kid, "tur": "kontenjan_idari_kaydi", "aciklama": temizle(r.get("gozlem_metni"))})
            elif not kontenjan:
                kod = r.get("gereklilik_kodu")
                kayitlar.append({"kayit_id": kid, "tur": "degerlendirici_gozlemi", "beceri": beceriler.get(kod, ""),
                                 "gozlem": temizle(r.get("gozlem_metni"))})
        if ik_not:
            ik = {"kayit_id": ik_not["kaynak_id"], "tur": "ik_gerekcesi", "gerekce": temizle(ik_not.get("nihai_ret_gerekcesi"))}
            if kontenjan:
                ik["paylasim_aciklamasi"] = temizle(ik_not.get("dis_paylasim_aciklamasi"))
            kayitlar.append(ik)

    return {
        "basvuru_id": b,
        "program": PROGRAM_ADI,
        "karar": "olumsuz",
        "karar_asamasi": asama_adlari.get(asama, asama),
        "gerekce_turu": tur,
        "kayitlar": kayitlar,
    }
