"""Bir başvuru için taslak üretir: girdi → istem → model → son kontrol."""
from core import llm
from core.istem import CIKTI_SEMASI, istem
from core.son_kontrol import kontrol_et


def taslak_uret(girdi: dict, cagir=None) -> dict:
    """Model yanıtını ayrıştırır ve son kontrolden geçirir. `cagir` testte sahte modelle değiştirilir."""
    cagir = cagir or llm.cagir
    sistem, kullanici = istem(girdi)
    yanit = cagir(sistem, kullanici, CIKTI_SEMASI, amac="taslak", basvuru_id=girdi["basvuru_id"])
    veri = yanit.veri
    if not isinstance(veri, dict) or not all(k in veri for k in CIKTI_SEMASI["required"]):
        raise llm.ModelHatasi("Model yanıtı beklenen JSON yapısında değil.")
    konu, metin = str(veri["email_konu"]).strip(), str(veri["email_metni"]).strip()
    idler = [str(i) for i in veri["kullanilan_kayit_idleri"]]
    return {
        "konu": konu,
        "metin": metin,
        "kullanilan_idler": idler,
        "emin_olunmayan": [str(x) for x in veri["emin_olunmayan_noktalar"]],
        "kontrol": kontrol_et(girdi, konu, metin, idler),
        "model": yanit.model,
        "cagri_id": yanit.cagri_id,
    }
