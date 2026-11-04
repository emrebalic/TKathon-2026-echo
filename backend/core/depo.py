"""SQLite depo: ilk taslak, İK düzeltmesi ve onay ayrı saklanır.

Taslak, girdi kayıtlarının hash'iyle saklanır. Durum her okumada hesaplanır:
girdi hash'i değiştiyse taslak ve onay geçersizdir; onaydan sonra metin değiştiyse onay düşer.
"""
import hashlib
import json
import sqlite3
from datetime import datetime
from pathlib import Path

SEMA = """
CREATE TABLE IF NOT EXISTS taslaklar (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    basvuru_id TEXT NOT NULL,
    girdi_hash TEXT NOT NULL,
    girdi_json TEXT NOT NULL,
    kaynak TEXT NOT NULL,
    model TEXT,
    cagri_id TEXT,
    ilk_konu TEXT NOT NULL,
    ilk_metin TEXT NOT NULL,
    kullanilan_idler TEXT NOT NULL,
    emin_olunmayan TEXT NOT NULL,
    ilk_kontrol TEXT NOT NULL,
    ik_konu TEXT,
    ik_metin TEXT,
    ik_kontrol TEXT,
    ik_zaman TEXT,
    onay_metin_hash TEXT,
    onay_zaman TEXT,
    olusturma TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS ix_taslak_basvuru ON taslaklar (basvuru_id, id);
"""

DURUM_ADLARI = {
    "gecersiz": "Geçersiz – veri değişti",
    "onay_dustu": "Onay düştü – metin değişti",
    "onaylandi": "Onaylandı",
    "onay_bekliyor": "İK onayı bekliyor",
}


def metin_hash(konu: str, metin: str) -> str:
    return hashlib.sha256(f"{konu}\n{metin}".encode("utf-8")).hexdigest()


def _simdi():
    return datetime.now().isoformat(timespec="seconds")


class Depo:
    def __init__(self, yol: Path):
        yol.parent.mkdir(parents=True, exist_ok=True)
        self.yol = yol
        with self._baglan() as db:
            db.executescript(SEMA)

    def _baglan(self):
        db = sqlite3.connect(self.yol, timeout=30)
        db.row_factory = sqlite3.Row
        return db

    def ekle(self, basvuru_id, girdi, g_hash, taslak, kaynak="model"):
        with self._baglan() as db:
            cur = db.execute(
                "INSERT INTO taslaklar (basvuru_id, girdi_hash, girdi_json, kaynak, model, cagri_id, ilk_konu, ilk_metin, "
                "kullanilan_idler, emin_olunmayan, ilk_kontrol, olusturma) VALUES (?,?,?,?,?,?,?,?,?,?,?,?)",
                (basvuru_id, g_hash, json.dumps(girdi, ensure_ascii=False), kaynak, taslak.get("model"), taslak.get("cagri_id"),
                 taslak["konu"], taslak["metin"], json.dumps(taslak["kullanilan_idler"], ensure_ascii=False),
                 json.dumps(taslak["emin_olunmayan"], ensure_ascii=False), json.dumps(taslak["kontrol"], ensure_ascii=False),
                 _simdi()))
            return cur.lastrowid

    def son(self, basvuru_id):
        with self._baglan() as db:
            row = db.execute("SELECT * FROM taslaklar WHERE basvuru_id=? ORDER BY id DESC LIMIT 1", (basvuru_id,)).fetchone()
        return dict(row) if row else None

    def sonlar(self):
        with self._baglan() as db:
            rows = db.execute("SELECT t.* FROM taslaklar t JOIN (SELECT basvuru_id, MAX(id) AS id FROM taslaklar "
                              "GROUP BY basvuru_id) s ON t.id = s.id").fetchall()
        return {r["basvuru_id"]: dict(r) for r in rows}

    def duzeltme_kaydet(self, taslak_id, konu, metin, kontrol):
        with self._baglan() as db:
            db.execute("UPDATE taslaklar SET ik_konu=?, ik_metin=?, ik_kontrol=?, ik_zaman=? WHERE id=?",
                       (konu, metin, json.dumps(kontrol, ensure_ascii=False), _simdi(), taslak_id))

    def onayla(self, taslak_id, m_hash):
        with self._baglan() as db:
            db.execute("UPDATE taslaklar SET onay_metin_hash=?, onay_zaman=? WHERE id=?", (m_hash, _simdi(), taslak_id))

    def duzeltmeler(self):
        with self._baglan() as db:
            return [dict(r) for r in db.execute("SELECT * FROM taslaklar WHERE ik_metin IS NOT NULL ORDER BY basvuru_id, id")]


def guncel_metin(t):
    """İK düzelttiyse düzeltilmiş hâl, yoksa ilk taslak."""
    return (t["ik_konu"] or t["ilk_konu"], t["ik_metin"] or t["ilk_metin"])


def durum(t, guncel_girdi_hash, yukleme_zamani):
    """Taslağın hesaplanmış durumu ve etiketleri."""
    konu, metin = guncel_metin(t)
    if guncel_girdi_hash is None or t["girdi_hash"] != guncel_girdi_hash:
        kod = "gecersiz"
    elif t["onay_metin_hash"]:
        kod = "onaylandi" if t["onay_metin_hash"] == metin_hash(konu, metin) else "onay_dustu"
    else:
        kod = "onay_bekliyor"
    kontrol = json.loads(t["ik_kontrol"] or t["ilk_kontrol"])
    return {
        "kod": kod,
        "ad": DURUM_ADLARI[kod],
        "kaynak": "Yeni üretildi" if (yukleme_zamani and t["olusturma"] >= yukleme_zamani) else "Kayıtlı",
        "ik_dikkat": bool(kontrol),
    }
