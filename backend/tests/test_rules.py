from pathlib import Path

import pytest

from core.loader import Veri, yukle
from core.rules import IK_INCELEME, TASLAK_UYGUN, KuralMotoru, ozet
from core.schema import column_lookup, normalize

VERI_DOSYASI = Path(__file__).resolve().parents[2] / "data" / "raw" / "02_Veriler.xlsx"
IK_LISTESI = {f"BSV-{i:03d}" for i in
              [3, 5, 6, 7, 33, 40, 44, 45, 47, 48, 49, 53, 57, 59, 61, 62, 64, 77, 79, 81, 82, 83, 84]}
# Görev dosyasında (docs/MVP_GOREV.md) "en az" İK'ya düşmesi beklenenler; fazlası çelişkili gözlem kuralından gelir.
GOREV_BEKLENEN = {f"BSV-{i:03d}" for i in [5, 6, 7, 33, 40, 44, 45, 47, 48, 57, 59, 61, 62, 64, 77, 79, 81, 83, 84]}

veri_gerekli = pytest.mark.skipif(not VERI_DOSYASI.exists(), reason="data/raw/02_Veriler.xlsx yok")


@pytest.fixture(scope="module")
def veri():
    return yukle(VERI_DOSYASI)


def test_tipografik_kesme_isareti_eslesir():
    assert normalize("İK’nın kaydettiği başvuru sonucu (kod)") == normalize("İK'nın kaydettiği başvuru sonucu (kod)")
    assert column_lookup("kararlar", ["İK’nın kaydettiği başvuru sonucu (kod)"]) == {
        "İK’nın kaydettiği başvuru sonucu (kod)": "karar_kodu"}


@veri_gerekli
def test_sayilar(veri):
    assert veri.gecerli, veri.hatalar
    s = ozet(KuralMotoru(veri).degerlendir())
    assert (s["toplam"], s["olumsuz"], s["kabul"], s["devam"]) == (120, 80, 20, 20)
    assert (s["taslaga_uygun"], s["ik_incelemesi"]) == (57, 23)


@veri_gerekli
def test_ik_listesi(veri):
    ds = KuralMotoru(veri).degerlendir()
    assert {d.basvuru_id for d in ds if d.durum == IK_INCELEME} == IK_LISTESI


@veri_gerekli
def test_ornek_nedenler(veri):
    ds = {d.basvuru_id: d for d in KuralMotoru(veri).degerlendir()}
    kodlar = lambda b: {x.kod for x in ds[b].bulgular}
    assert "DUZELTME" in kodlar("BSV-033")
    assert "COKLU_GOZLEM" in kodlar("BSV-003")
    assert {"KURUM_ICI", "KISILIK_YARGISI"} <= kodlar("BSV-006")
    assert "IK_NOTU_YOK" in kodlar("BSV-040")
    assert ds["BSV-008"].durum == TASLAK_UYGUN
    assert any("Kontenjan" in u for u in ds["BSV-008"].uyarilar)


@veri_gerekli
def test_farkli_kayit_sayisi(veri):
    secilen = set(sorted(veri["kararlar"]["basvuru_id"])[:40])
    alt = Veri(tablolar={k: df[df["basvuru_id"].isin(secilen)] if "basvuru_id" in df else df
                         for k, df in veri.tablolar.items()})
    s = ozet(KuralMotoru(alt).degerlendir())
    assert s["toplam"] == 40
    assert s["olumsuz"] + s["kabul"] + s["devam"] == 40


@veri_gerekli
def test_veri_degisince_parmak_izi_degisir(veri):
    once = {d.basvuru_id: d.parmak_izi for d in KuralMotoru(veri).degerlendir()}
    sinav = veri["sinav"].copy()
    sinav.loc[sinav["kaynak_id"] == "SN-001-EN", "dogru_sayisi"] = 7
    degisen = Veri(tablolar={**veri.tablolar, "sinav": sinav})
    sonra = {d.basvuru_id: d.parmak_izi for d in KuralMotoru(degisen).degerlendir()}
    assert once["BSV-001"] != sonra["BSV-001"]
    assert all(once[b] == sonra[b] for b in once if b != "BSV-001")


@veri_gerekli
def test_gorev_dosyasindaki_beklenen_liste_kapsaniyor(veri):
    ik = {d.basvuru_id for d in KuralMotoru(veri).degerlendir() if d.durum == IK_INCELEME}
    assert GOREV_BEKLENEN <= ik
    assert ik - GOREV_BEKLENEN == {"BSV-003", "BSV-049", "BSV-053", "BSV-082"}


def _degisik(veri, key, kaynak_id, alan, deger):
    df = veri[key].copy()
    df.loc[df["kaynak_id"] == kaynak_id, alan] = deger
    return Veri(tablolar={**veri.tablolar, key: df})


@veri_gerekli
def test_yeni_kurallar(veri):
    kodlar = lambda v, b: {x.kod for d in KuralMotoru(v).degerlendir() if d.basvuru_id == b for x in d.bulgular}
    assert "GOZLEM_YOK" in kodlar(_degisik(veri, "dil", "DL-065", "gozlem_metni", None), "BSV-065")
    assert "KONTENJAN_KAYDI_YOK" in kodlar(_degisik(veri, "asama_kayitlari", "AS-008-07", "kaynak_rolu", "IK_UZMANI"), "BSV-008")
    assert "GOZLEM_GEREKCE_CELISKI" in kodlar(veri, "BSV-049")
