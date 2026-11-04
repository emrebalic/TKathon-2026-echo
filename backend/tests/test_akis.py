"""Model girdisi, son kontrol ve API akışı. Gerçek API çağrısı yapılmaz; sahte model kullanılır."""
import json
import sys
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from core.girdi import model_girdisi
from core.llm import Yanit
from core.loader import yukle
from core.rules import KuralMotoru
from core.son_kontrol import kontrol_et

KOK = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(KOK / "scripts"))
VERI = KOK / "data" / "raw" / "02_Veriler.xlsx"
XLSX = "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
veri_gerekli = pytest.mark.skipif(not VERI.exists(), reason="data/raw/02_Veriler.xlsx yok")


@pytest.fixture(scope="module")
def motor():
    m = KuralMotoru(yukle(VERI))
    return m, {d.basvuru_id: d for d in m.degerlendir()}


@veri_gerekli
def test_girdi_yalniz_kalinan_bolum_ve_kurum_ici_yok(motor):
    m, ds = motor
    g = model_girdisi(m, ds["BSV-001"])
    assert [k["kayit_id"] for k in g["kayitlar"]] == ["SN-001-EN"]
    for b, d in ds.items():
        g = model_girdisi(m, d)
        if g is None:
            continue
        metin = json.dumps(g, ensure_ascii=False)
        assert not any(x in metin for x in ("T101", "GRP-", "KP-2026", "Kişilik envanteri", "KURUM_ICI")), b
        assert all(k["kayit_id"].endswith(b[4:]) or k["kayit_id"].split("-")[1] == b[4:] for k in g["kayitlar"]), b


@veri_gerekli
def test_ik_incelemesindekilere_girdi_yok(motor):
    m, ds = motor
    assert model_girdisi(m, ds["BSV-033"]) is None
    assert model_girdisi(m, ds["BSV-009"]) is None  # kabul


@veri_gerekli
def test_son_kontrol_hatalari_yakalar(motor):
    m, ds = motor
    g = model_girdisi(m, ds["BSV-001"])
    dolgu = " ".join(["Değerlendirme sürecine gösterdiğiniz ilgi için teşekkür ederiz."] * 9)
    iyi = (f"{dolgu} İngilizce bölümünde 15 sorunun 6'sına doğru yanıt verdiniz; geçme barajı 10 doğruydu. "
           f"Sorularınızı BSV-001 Başvuru ID'si ile iletebilirsiniz.")
    assert kontrol_et(g, "BSV-001 başvurunuz hakkında", iyi, ["SN-001-EN"]) == []
    kotu = iyi.replace("6'sına", "7'sine") + " İngilizceniz B2 seviyesinde. AS-001-02"
    kodlar = {s["kod"] for s in kontrol_et(g, "Konu", kotu, ["SN-001-EN", "SN-001-GY"])}
    assert {"KAYITTA_OLMAYAN_SAYI", "YASAK_IFADE", "IC_KOD", "YABANCI_KAYIT"} <= kodlar
    k = model_girdisi(m, ds["BSV-008"])
    kodlar = {s["kod"] for s in kontrol_et(k, "BSV-008", dolgu + " Eksik yönlerinizi geliştirmenizi öneririz. BSV-008", ["AS-008-07"])}
    assert "YASAK_IFADE" in kodlar


def _sahte_model(sistem, kullanici, sema, amac="", basvuru_id=""):
    if amac == "ingilizce":
        b = basvuru_id
        govde = " ".join(["Thank you for your interest in the Junior Wings assessment process."] * 9)
        veri = {"email_subject": f"About your application {b}",
                "email_body": govde + f" You can send your questions with application ID {b} by replying to this email.",
                "anlam_farki_notlari": []}
        return Yanit("sahte", "sahte-model", json.dumps(veri), veri, 0.0)
    girdi = json.loads(kullanici.split("\n", 1)[1])
    b = girdi["basvuru_id"]
    metin = " ".join(["Junior Wings değerlendirme sürecine gösterdiğiniz ilgi için teşekkür ederiz."] * 9)
    metin += f" Sorularınızı {b} Başvuru ID'si ile bu e-postayı yanıtlayarak iletebilirsiniz."
    veri = {"email_konu": f"{b} başvurunuz hakkında", "email_metni": metin,
            "kullanilan_kayit_idleri": [k["kayit_id"] for k in girdi["kayitlar"]], "emin_olunmayan_noktalar": []}
    return Yanit("sahte", "sahte-model", json.dumps(veri, ensure_ascii=False), veri, 0.0)


@pytest.fixture()
def istemci(tmp_path):
    from app.main import create_app
    return TestClient(create_app(tmp_path, cagir=_sahte_model, on_uretim=False))


def _uretimi_bekle(istemci, sure=20.0):
    import time
    bitis = time.time() + sure
    while time.time() < bitis:
        u = istemci.get("/api/uretim").json()
        if not u["calisiyor"]:
            return u
        time.sleep(0.1)
    raise AssertionError("Ön üretim zamanında bitmedi")


@veri_gerekli
def test_on_uretim_hepsini_hazirlar_degiseni_yeniler(tmp_path):
    from alt_kume_olustur import degistir
    from app.main import create_app
    istemci = TestClient(create_app(tmp_path / "db", cagir=_sahte_model, on_uretim=True))
    _yukle(istemci, VERI)
    u = _uretimi_bekle(istemci)
    assert (u["toplam"], u["tamam"], u["hata"]) == (57, 57, 0)
    oz = istemci.get("/api/ozet").json()
    assert (oz["taslak_hazir"], oz["islenmedi"], oz["ik_incelemesi"]) == (57, 0, 23)
    istemci.post("/api/basvurular/BSV-001/onay", json={})

    _yukle(istemci, VERI)  # aynı dosya: yeniden üretilecek taslak yok
    assert _uretimi_bekle(istemci)["toplam"] == 0

    degisen = tmp_path / "degisen.xlsx"
    degistir(VERI, degisen, "Aşama Kayıtları", "AS-002-02", "Değerlendiricinin gözlemi / süreç notu", "Değişmiş gözlem metni.")
    _yukle(istemci, degisen)
    assert _uretimi_bekle(istemci)["toplam"] == 1
    assert istemci.get("/api/basvurular/BSV-002").json()["taslak"]["durum"]["kod"] == "onay_bekliyor"
    assert istemci.get("/api/basvurular/BSV-001").json()["taslak"]["durum"]["kod"] == "onaylandi"


def _yukle(istemci, yol):
    return istemci.post("/api/yukle", files={"dosya": (yol.name, yol.read_bytes(), XLSX)})


@veri_gerekli
def test_olagan_basvuru_taslak_duzeltme_onay(istemci):
    oz = _yukle(istemci, VERI).json()
    assert (oz["toplam"], oz["olumsuz"], oz["kabul"], oz["devam"]) == (120, 80, 20, 20)
    assert (oz["taslak_hazir"], oz["ik_incelemesi"], oz["islenmedi"]) == (0, 23, 57)

    d = istemci.post("/api/basvurular/BSV-002/taslak").json()
    assert d["taslak"]["durum"]["kod"] == "onay_bekliyor" and d["taslak"]["kontrol"] == []
    assert {k["kayit_id"] for k in d["kayitlar"] if k["modele_verildi"]} == {"AS-002-02", "IK-002"}
    d = istemci.post("/api/basvurular/BSV-002/onay", json={}).json()
    assert d["taslak"]["durum"]["kod"] == "onaylandi"

    yeni = d["taslak"]["metin"].replace("teşekkür ederiz", "teşekkür ediyoruz", 1)
    d = istemci.put("/api/basvurular/BSV-002/duzeltme", json={"konu": d["taslak"]["konu"], "metin": yeni}).json()
    assert d["taslak"]["durum"]["kod"] == "onay_dustu" and d["taslak"]["ik_duzeltti"]
    assert istemci.get("/api/ozet").json()["taslak_hazir"] == 1


@veri_gerekli
def test_kapsam_disi_ve_ik_incelemesine_taslak_yok(istemci):
    _yukle(istemci, VERI)
    assert istemci.post("/api/basvurular/BSV-009/taslak").status_code == 409
    assert istemci.post("/api/basvurular/BSV-033/taslak").status_code == 409


@veri_gerekli
def test_degisen_veri_taslagi_ve_onayi_dusurur(istemci, tmp_path):
    from alt_kume_olustur import degistir
    _yukle(istemci, VERI)
    istemci.post("/api/basvurular/BSV-002/taslak")
    istemci.post("/api/basvurular/BSV-001/taslak")
    istemci.post("/api/basvurular/BSV-002/onay", json={})
    degisen = tmp_path / "degisen.xlsx"
    degistir(VERI, degisen, "Aşama Kayıtları", "AS-002-02", "Değerlendiricinin gözlemi / süreç notu", "Değişmiş gözlem metni.")
    _yukle(istemci, degisen)
    assert istemci.get("/api/basvurular/BSV-002").json()["taslak"]["durum"]["kod"] == "gecersiz"
    assert istemci.get("/api/basvurular/BSV-001").json()["taslak"]["durum"]["kod"] == "onay_bekliyor"
    assert istemci.post("/api/basvurular/BSV-002/onay", json={}).status_code == 409
    d = istemci.post("/api/basvurular/BSV-002/taslak").json()
    assert d["taslak"]["durum"]["kod"] == "onay_bekliyor"


@veri_gerekli
def test_yeni_dosya_sayilari_gunceller(istemci, tmp_path):
    from alt_kume_olustur import alt_kume
    kucuk = tmp_path / "kirk.xlsx"
    assert alt_kume(VERI, kucuk, 40) == 40
    _yukle(istemci, VERI)
    oz = _yukle(istemci, kucuk).json()
    assert oz["toplam"] == 40 and oz["olumsuz"] + oz["kabul"] + oz["devam"] == 40
    assert len(istemci.get("/api/basvurular").json()) == 40


@veri_gerekli
def test_is_yuku_vaka_rakamlari(istemci):
    _yukle(istemci, VERI)
    r = istemci.get("/api/is-yuku").json()
    assert r["elle"]["dakika"] == 15552 and r["elle"]["saat"] == 259.2 and r["elle"]["is_gunu"] == 43.2
    assert r["oneri"]["saat"] == 55.2 and r["oneri"]["is_gunu"] == 9.2
    assert istemci.get("/api/is-yuku", params={"sorunlulari_elle_yaz": True}).json()["oneri"]["saat"] == 69.5


@veri_gerekli
def test_mulakat_blogu_ve_istem_degisince_taslak_yenilenir(motor, monkeypatch):
    from core import istem as istem_modulu
    from core.taslak import taslak_anahtari
    m, ds = motor
    tur = {b: model_girdisi(m, ds[b])["gerekce_turu"] for b in ("BSV-001", "BSV-002", "BSV-051", "BSV-065", "BSV-008")}
    assert tur == {"BSV-001": "sinav", "BSV-002": "mulakat", "BSV-051": "oznel_degerlendirme",
                   "BSV-065": "ingilizce_gorusme", "BSV-008": "kontenjan"}
    video, grup = model_girdisi(m, ds["BSV-002"]), model_girdisi(m, ds["BSV-051"])
    once = taslak_anahtari(video), taslak_anahtari(grup)
    monkeypatch.setitem(istem_modulu.BLOKLAR, "mulakat", istem_modulu.BLOKLAR["mulakat"] + " Ek kural.")
    assert taslak_anahtari(video) != once[0]   # yalnız istemi değişen başvurunun taslağı düşer
    assert taslak_anahtari(grup) == once[1]


@veri_gerekli
def test_ingilizce_surum_o_anda_uretilir_ve_turkce_degisince_eskir(istemci):
    _yukle(istemci, VERI)
    istemci.post("/api/basvurular/BSV-002/taslak")
    assert istemci.get("/api/basvurular/BSV-002").json()["taslak"]["ingilizce"] is None
    d = istemci.post("/api/basvurular/BSV-002/ingilizce").json()
    en = d["taslak"]["ingilizce"]
    assert en["guncel"] and "BSV-002" in en["metin"] and en["kontrol"] == []
    t = d["taslak"]
    istemci.put("/api/basvurular/BSV-002/duzeltme", json={"konu": t["konu"], "metin": t["metin"] + " Saygılarımızla."})
    assert istemci.get("/api/basvurular/BSV-002").json()["taslak"]["ingilizce"]["guncel"] is False


def test_ceviri_kontrolu_sayi_ve_kimlik_farkini_yakalar():
    from core.ceviri import kontrol
    girdi = {"basvuru_id": "BSV-001", "gerekce_turu": "sinav"}
    tr = "İngilizce bölümünde 15 sorunun 6'sına doğru yanıt verdiniz; geçme barajı 10 doğruydu. BSV-001"
    iyi = "You answered 6 of 15 questions correctly in the English section; the pass mark was 10. BSV-001"
    assert kontrol(girdi, "Konu", tr, "Subject", iyi) == []
    kotu = "You answered 7 of 15 questions; your English level is B2."
    kodlar = {s["kod"] for s in kontrol(girdi, "Konu", tr, "Subject", kotu)}
    assert {"SAYI_FARKI", "BASVURU_ID_YOK", "YASAK_IFADE"} <= kodlar
