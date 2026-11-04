"""Muse API bağlantısını ve JSON şeması desteğini dener.

Çalıştırma: python tools/muse_baglanti_testi.py
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
sys.stdout.reconfigure(encoding="utf-8")

from core.llm import BASE_URL, MODEL, ModelHatasi, cagir  # noqa: E402

SEMA = {
    "type": "object",
    "properties": {"durum": {"type": "string"}, "dil": {"type": "string"}},
    "required": ["durum", "dil"],
    "additionalProperties": False,
}

print(f"Uç nokta: {BASE_URL} · model: {MODEL}")
try:
    y = cagir("Yalnız istenen JSON'u döndür.", 'durum alanına "hazır", dil alanına "tr" yaz.', SEMA, amac="baglanti_testi")
except ModelHatasi as exc:
    print("BAŞARISIZ:", exc)
    sys.exit(1)
print(f"Yanıt ({y.sure_sn} sn, {y.model}): {y.metin}")
print("JSON şeması:", "çalışıyor" if y.veri else "yanıt JSON olarak ayrıştırılamadı")
