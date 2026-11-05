"""Test dosyaları üretir: aynı yapıda daha az başvuru ve bir kaydı değiştirilmiş kopya.

Çalıştırma (depo kökünden): uv run --directory backend python ../scripts/alt_kume_olustur.py [kaynak.xlsx]
Kaynak verilmezse data/test/Veriler_60_basvuru.xlsx kullanılır. Çıktılar data/test/ altına yazılır;
kaynağın kendisinin üzerine yazılmaz.
"""
import sys
from pathlib import Path

import openpyxl

KOK = Path(__file__).resolve().parents[1]
HEDEF = KOK / "data" / "test"
VARSAYILAN_KAYNAK = HEDEF / "Veriler_60_basvuru.xlsx"


def _basvuru_sutunu(ws):
    for i, h in enumerate(c.value for c in ws[1]):
        if h == "Başvuru ID":
            return i
    return None


def alt_kume(kaynak: Path, hedef: Path, adet: int) -> int:
    """İlk `adet` başvuruyu bütün kayıt sayfalarında tutar; diğer sayfalara dokunmaz."""
    wb = openpyxl.load_workbook(kaynak)
    kararlar = wb["Başvuru Kararları"]
    sutun = _basvuru_sutunu(kararlar)
    tut = {r[sutun].value for r in list(kararlar.iter_rows(min_row=2))[:adet]}
    for ws in wb.worksheets:
        s = _basvuru_sutunu(ws)
        if s is None:
            continue
        for satir in range(ws.max_row, 1, -1):
            if ws.cell(satir, s + 1).value not in tut:
                ws.delete_rows(satir)
    hedef.parent.mkdir(parents=True, exist_ok=True)
    wb.save(hedef)
    return len(tut)


def degistir(kaynak: Path, hedef: Path, sayfa: str, kayit_id: str, sutun: str, deger) -> None:
    """Bir kaydın tek bir hücresini değiştirir."""
    wb = openpyxl.load_workbook(kaynak)
    ws = wb[sayfa]
    basliklar = [c.value for c in ws[1]]
    for satir in ws.iter_rows(min_row=2):
        if satir[0].value == kayit_id:
            satir[basliklar.index(sutun)].value = deger
    hedef.parent.mkdir(parents=True, exist_ok=True)
    wb.save(hedef)


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8")
    KAYNAK = Path(sys.argv[1]).resolve() if len(sys.argv) > 1 else VARSAYILAN_KAYNAK
    for adet in (40, 60):
        yol = HEDEF / f"Veriler_{adet}_basvuru.xlsx"
        if yol.resolve() == KAYNAK:
            continue
        print(f"{yol.name}: {alt_kume(KAYNAK, yol, adet)} başvuru")
    yol = HEDEF / "Veriler_degisen_BSV-002.xlsx"
    degistir(KAYNAK, yol, "Aşama Kayıtları", "AS-002-02", "Değerlendiricinin gözlemi / süreç notu",
             "Yanıtında ekip olarak yapılan işi anlattı. Kendi üstlendiği adım sorulduğunda yalnız ekibin sonucunu "
             "tekrarladı; kişisel katkısını ve bu katkının sonucunu açıklamadı.")
    print(f"{yol.name}: AS-002-02 gözlem metni değiştirildi")
