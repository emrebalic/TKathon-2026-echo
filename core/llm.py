"""Meta Model API (Muse Spark) istemcisi.

Meta'nın OpenAI uyumlu Chat Completions uç noktasını kullanır. Her çağrının girdisi ve ham
yanıtı store/ai_kayitlari.jsonl dosyasına eklenir (teslimde istenen "yapay zekâya verilen
girdiler ve ham yanıtlar").

Ayarlar .env dosyasından okunur: MODEL_API_KEY (zorunlu), MODEL_ID, MODEL_API_BASE_URL.
"""
import json
import os
import time
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path

from dotenv import load_dotenv
from openai import OpenAI

KOK = Path(__file__).resolve().parents[1]
load_dotenv(KOK / ".env")

BASE_URL = os.getenv("MODEL_API_BASE_URL", "https://api.meta.ai/v1")
MODEL = os.getenv("MODEL_ID", "muse-spark-1.3")
KAYIT_DOSYASI = KOK / "store" / "ai_kayitlari.jsonl"


class ModelHatasi(RuntimeError):
    pass


@dataclass
class Yanit:
    cagri_id: str
    model: str
    metin: str
    veri: dict | None
    sure_sn: float
    kullanim: dict = field(default_factory=dict)


def _istemci():
    anahtar = os.getenv("MODEL_API_KEY")
    if not anahtar:
        raise ModelHatasi("MODEL_API_KEY tanımlı değil; .env dosyasına ekleyin.")
    return OpenAI(base_url=BASE_URL, api_key=anahtar, timeout=90, max_retries=2)


def _kaydet(kayit):
    KAYIT_DOSYASI.parent.mkdir(exist_ok=True)
    with KAYIT_DOSYASI.open("a", encoding="utf-8") as f:
        f.write(json.dumps(kayit, ensure_ascii=False, default=str) + "\n")


def cagir(sistem: str, kullanici: str, sema: dict | None = None, amac: str = "", basvuru_id: str = "") -> Yanit:
    """Modeli bir kez çağırır. `sema` verilirse yanıt bu JSON şemasına uymak zorundadır."""
    mesajlar = [{"role": "system", "content": sistem}, {"role": "user", "content": kullanici}]
    istek = {"model": MODEL, "messages": mesajlar}
    if sema:
        istek["response_format"] = {"type": "json_schema", "json_schema": {"name": "yanit", "schema": sema, "strict": True}}

    cagri_id = uuid.uuid4().hex[:12]
    kayit = {"cagri_id": cagri_id, "zaman": datetime.now(timezone.utc).isoformat(), "amac": amac,
             "basvuru_id": basvuru_id, "istek": istek}
    baslangic = time.perf_counter()
    try:
        cevap = _istemci().chat.completions.create(**istek)
    except ModelHatasi:
        raise
    except Exception as exc:
        kayit["hata"] = repr(exc)
        _kaydet(kayit)
        raise ModelHatasi(f"Model çağrısı başarısız: {exc}") from exc
    sure = round(time.perf_counter() - baslangic, 2)

    metin = cevap.choices[0].message.content or ""
    veri = None
    if sema:
        try:
            veri = json.loads(metin)
        except json.JSONDecodeError:
            veri = None
    kullanim = cevap.usage.model_dump() if getattr(cevap, "usage", None) else {}
    kayit.update({"model": cevap.model, "ham_yanit": metin, "sure_sn": sure, "kullanim": kullanim,
                  "json_gecerli": veri is not None if sema else None})
    _kaydet(kayit)
    return Yanit(cagri_id, cevap.model, metin, veri, sure, kullanim)
