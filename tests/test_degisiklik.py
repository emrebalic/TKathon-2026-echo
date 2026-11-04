import io
from pathlib import Path

import openpyxl
import pytest

from core.degisiklik import degisen_basvurular

KOK = Path(__file__).resolve().parents[1]
VERI_DOSYASI = KOK / "data" / "raw" / "02_Veriler.xlsx"
XLSX = "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"


def test_degisen_basvurular():
    fark = degisen_basvurular({"A": "1", "B": "2", "C": "3"}, {"A": "1", "B": "9", "D": "4"})
    assert fark == {"degisen": ["B"], "yeni": ["D"], "silinen": ["C"]}


def _degistirilmis(sayfa, kayit_id, sutun, deger):
    wb = openpyxl.load_workbook(VERI_DOSYASI)
    ws = wb[sayfa]
    basliklar = [c.value for c in ws[1]]
    for satir in ws.iter_rows(min_row=2):
        if satir[0].value == kayit_id:
            satir[basliklar.index(sutun)].value = deger
    tampon = io.BytesIO()
    wb.save(tampon)
    return tampon.getvalue()


def _sayi(at, etiket):
    return dict((m.label, m.value) for m in at.metric)[etiket]


@pytest.mark.skipif(not VERI_DOSYASI.exists(), reason="data/raw/02_Veriler.xlsx yok")
def test_yeniden_yuklenen_dosyada_degisen_basvuru_gosterilir():
    from streamlit.testing.v1 import AppTest

    at = AppTest.from_file(str(KOK / "app" / "main.py"), default_timeout=60).run()
    assert not at.exception and not at.metric  # dosya yüklenmeden sayı yok

    at.file_uploader[0].set_value(("02_Veriler.xlsx", VERI_DOSYASI.read_bytes(), XLSX))
    at.run()
    assert not at.exception
    assert _sayi(at, "İK incelemesi bekleyen") == "23"

    at.file_uploader[0].set_value(("02_Veriler_degisik.xlsx", _degistirilmis("Sınav Sonuçları", "SN-001-EN", "Doğru sayısı", 7), XLSX))
    at.run()
    assert not at.exception
    bant = " ".join(i.value for i in at.info)
    assert "değişen: BSV-001" in bant
    assert _sayi(at, "İK incelemesi bekleyen") == "24"
