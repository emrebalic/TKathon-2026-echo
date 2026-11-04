"""FastAPI uygulaması: bütün iş kuralları burada ve core/ altında; arayüz yalnız gösterir.

Çalıştırma (depo kökünden): uv run --directory backend uvicorn app.main:create_app --factory --reload
İçe aktarmak uygulama oluşturmaz; böylece testler gerçek modeli ve kayıtlı veriyi tetiklemez.
"""
import io
import json
import os
import threading
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime
from pathlib import Path

import pandas as pd
from fastapi import FastAPI, File, HTTPException, UploadFile
from fastapi.responses import StreamingResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

from core import llm
from core.depo import Depo, durum, guncel_metin, metin_hash
from core.girdi import model_girdisi
from core.is_yuku import hesapla
from core.loader import yukle
from core.rules import IK_INCELEME, KAPSAM_DISI, KARAR_KODLARI, TASLAK_UYGUN, KuralMotoru
from core.schema import SHEETS
from core.son_kontrol import kontrol_et
from core.taslak import taslak_anahtari, taslak_uret

BACKEND = Path(__file__).resolve().parents[1]
FRONTEND = BACKEND.parent / "frontend"
ASAMA_ADLARI = {"SINAV": "Sınav", "VIDEO": "Video", "GRUP": "Grup", "INGILIZCE": "İngilizce görüşme",
                "ENVANTER": "Envanter", "IK_TEKNIK": "İK ve birim", "TEKLIF": "Teklif", "BELGE": "Belge"}


class Duzeltme(BaseModel):
    konu: str
    metin: str


class Onay(BaseModel):
    uyarilari_okudum: bool = False


def kayit_ozeti(tablo, r):
    if tablo == "sinav":
        return f"{r['test_turu']}: {r['dogru_sayisi']}/{r['soru_sayisi']} doğru, baraj {r['gecme_baraji']}, {r['kayitli_sonuc']}"
    if tablo == "dil":
        return f"{r['kayitli_puan']}/{r['olcek_tavani']} puan, baraj {r['gecme_baraji']}, {r['kayitli_sonuc']}. {r.get('gozlem_metni') or ''}"
    if tablo == "ik_notlari":
        return f"{r['gerekce_kodu']} · teyit {r['dis_paylasim_teyidi']}. {r.get('nihai_ret_gerekcesi') or ''}"
    return r.get("gozlem_metni") or ""


ESZAMANLI_CAGRI = 5


def create_app(veri_dizini: Path | None = None, cagir=None, on_uretim: bool | None = None) -> FastAPI:
    """`cagir` testte sahte modelle değiştirilir. `on_uretim`: yüklemeden sonra taslaklar arka planda hazırlansın mı."""
    veri_dizini = Path(veri_dizini or os.getenv("MVP_VERI_DIZINI", BACKEND / "data"))
    veri_dizini.mkdir(parents=True, exist_ok=True)
    if on_uretim is None:
        on_uretim = os.getenv("MVP_ON_URETIM", "1") != "0"
    son_dosya, son_meta = veri_dizini / "son_yukleme.xlsx", veri_dizini / "son_yukleme.json"
    depo = Depo(veri_dizini / "mvp.db")
    s = {"veri": None, "nesil": 0, "uretim": {"calisiyor": False, "toplam": 0, "tamam": 0, "hata": 0, "hatalar": []}}

    def uretimi_baslat():
        """Geçerli taslağı olmayan bütün uygun başvurular için taslağı arka planda üretir.

        Her çalıştırmanın kendi sayaç sözlüğü vardır; yeni dosya yüklenince eski çalıştırmanın sonuçları kaydedilmez.
        """
        nesil, girdiler = s["nesil"], dict(s["girdiler"])
        sonlar = depo.sonlar()
        bekleyen = [b for b, (_, h) in girdiler.items() if b not in sonlar or sonlar[b]["girdi_hash"] != h]
        calisma = {"calisiyor": bool(bekleyen), "toplam": len(bekleyen), "tamam": 0, "hata": 0, "hatalar": []}
        s["uretim"] = calisma
        if not bekleyen:
            return
        kilit = threading.Lock()

        def tek(b):
            g, h = girdiler[b]
            try:
                sonuc = taslak_uret(g, cagir)
                if s["nesil"] == nesil:
                    depo.ekle(b, g, h, sonuc)
                with kilit:
                    calisma["tamam"] += 1
            except Exception as exc:  # bir başvurunun hatası diğerlerini durdurmaz
                with kilit:
                    calisma["hata"] += 1
                    calisma["hatalar"].append({"basvuru_id": b, "mesaj": str(exc)[:200]})

        def calis():
            with ThreadPoolExecutor(max_workers=ESZAMANLI_CAGRI) as havuz:
                list(havuz.map(tek, bekleyen))
            calisma["calisiyor"] = False

        threading.Thread(target=calis, daemon=True).start()

    def isle(icerik: bytes, ad: str, zaman: str):
        veri = yukle(io.BytesIO(icerik))
        if not veri.gecerli:
            raise HTTPException(400, detail={"mesaj": "Dosya beklenen yapıda değil.", "hatalar": veri.hatalar})
        motor = KuralMotoru(veri)
        degerlendirmeler = {d.basvuru_id: d for d in motor.degerlendir()}
        girdiler = {}
        for b, d in degerlendirmeler.items():
            g = model_girdisi(motor, d)
            if g:
                girdiler[b] = (g, taslak_anahtari(g))
        s.update(veri=veri, motor=motor, d=degerlendirmeler, girdiler=girdiler, dosya_adi=ad, zaman=zaman, nesil=s["nesil"] + 1)
        if on_uretim:
            uretimi_baslat()

    if son_dosya.exists() and son_meta.exists():
        meta = json.loads(son_meta.read_text(encoding="utf-8"))
        try:
            isle(son_dosya.read_bytes(), meta["ad"], meta["zaman"])
        except HTTPException:
            pass

    def gerekli():
        if s["veri"] is None:
            raise HTTPException(409, detail="Önce ATS Excel dosyasını yükleyin.")

    def basvuru(b):
        gerekli()
        if b not in s["d"]:
            raise HTTPException(404, detail=f"{b} bu dosyada yok.")
        return s["d"][b]

    def taslak_bilgisi(b, t):
        if not t:
            return None
        g = s["girdiler"].get(b)
        konu, metin = guncel_metin(t)
        return {
            "id": t["id"], "konu": konu, "metin": metin, "ilk_konu": t["ilk_konu"], "ilk_metin": t["ilk_metin"],
            "ik_duzeltti": t["ik_metin"] is not None, "ik_zaman": t["ik_zaman"], "onay_zaman": t["onay_zaman"],
            "kullanilan_idler": json.loads(t["kullanilan_idler"]), "emin_olunmayan": json.loads(t["emin_olunmayan"]),
            "kontrol": guncel_kontrol(t), "kelime": len(metin.split()),
            "model": t["model"], "kaynak_turu": t["kaynak"], "olusturma": t["olusturma"],
            "durum": {**durum(t, g[1] if g else None, s["zaman"]), "ik_dikkat": bool(guncel_kontrol(t))},
        }

    def guncel_kontrol(t):
        """Son kontrol, taslağın dayandığı girdiyle ve güncel kurallarla her okumada yeniden hesaplanır."""
        konu, metin = guncel_metin(t)
        return kontrol_et(json.loads(t["girdi_json"]), konu, metin, json.loads(t["kullanilan_idler"]))

    def satir(d, sonlar):
        t = sonlar.get(d.basvuru_id)
        bilgi = taslak_bilgisi(d.basvuru_id, t)
        if d.karar_kodu == "OLUMSUZ" and d.durum == TASLAK_UYGUN:
            alt = "hazir" if bilgi and bilgi["durum"]["kod"] != "gecersiz" else "islenmedi"
        else:
            alt = None
        return {
            "basvuru_id": d.basvuru_id, "karar": d.karar_kodu, "asama": ASAMA_ADLARI.get(d.asama_kodu, d.asama_kodu),
            "durum": d.durum, "olumsuz_alt": alt, "nedenler": [b.ad for b in d.bulgular], "uyarilar": d.uyarilar,
            "taslak_uretilebilir": d.basvuru_id in s["girdiler"],
            "taslak_durumu": bilgi["durum"] if bilgi else None,
        }

    def detay(b):
        d = basvuru(b)
        g = s["girdiler"].get(b)
        verilen = {k["kayit_id"] for k in g[0]["kayitlar"]} if g else set()
        idler = list(dict.fromkeys(list(verilen) + d.dayanak_kayitlari + [k for x in d.bulgular for k in x.kayitlar]))
        kayitlar = []
        for kid in idler:
            bilgi = s["motor"].kayit(kid)
            if bilgi is None:
                kayitlar.append({"kayit_id": kid, "sayfa": "Bulunamadı", "asama": "", "paylasim": "", "icerik": "", "modele_verildi": False})
                continue
            t, r = bilgi
            kayitlar.append({"kayit_id": kid, "sayfa": SHEETS[t], "asama": ASAMA_ADLARI.get(r.get("asama_kodu"), ""),
                             "paylasim": r.get("paylasim_kodu") or "", "icerik": kayit_ozeti(t, r), "modele_verildi": kid in verilen})
        sonlar = {b: depo.son(b)} if depo.son(b) else {}
        return {**satir(d, sonlar), "bulgular": [{"kod": x.kod, "ad": x.ad, "aciklama": x.aciklama, "kayitlar": x.kayitlar} for x in d.bulgular],
                "kayitlar": kayitlar, "model_girdisi": g[0] if g else None, "taslak": taslak_bilgisi(b, depo.son(b))}

    app = FastAPI(title="Junior Wings geri bildirim MVP'si")

    @app.post("/api/yukle")
    def dosya_yukle(dosya: UploadFile = File(...)):
        icerik = dosya.file.read()
        zaman = datetime.now().isoformat(timespec="seconds")
        isle(icerik, dosya.filename, zaman)
        son_dosya.write_bytes(icerik)
        son_meta.write_text(json.dumps({"ad": dosya.filename, "zaman": zaman}, ensure_ascii=False), encoding="utf-8")
        return ozet()

    @app.get("/api/ozet")
    def ozet():
        if s["veri"] is None:
            return {"yuklu": False}
        sonlar = depo.sonlar()
        satirlar = [satir(d, sonlar) for d in s["d"].values()]
        say = lambda f: sum(1 for x in satirlar if f(x))
        return {
            "yuklu": True, "dosya_adi": s["dosya_adi"], "yukleme_zamani": s["zaman"], "uyarilar": s["veri"].uyarilar,
            "toplam": len(satirlar),
            "olumsuz": say(lambda x: x["karar"] == "OLUMSUZ"), "kabul": say(lambda x: x["karar"] == "KABUL"),
            "devam": say(lambda x: x["karar"] == "DEVAM_EDIYOR"), "veri_sorunu": say(lambda x: x["karar"] not in KARAR_KODLARI),
            "taslak_hazir": say(lambda x: x["olumsuz_alt"] == "hazir"),
            "ik_incelemesi": say(lambda x: x["karar"] == "OLUMSUZ" and x["durum"] == IK_INCELEME),
            "islenmedi": say(lambda x: x["olumsuz_alt"] == "islenmedi"),
            "onaylandi": say(lambda x: (x["taslak_durumu"] or {}).get("kod") == "onaylandi"),
            "ik_dikkat": say(lambda x: x["olumsuz_alt"] == "hazir" and (x["taslak_durumu"] or {}).get("ik_dikkat")),
            "uretim": {k: v for k, v in s["uretim"].items() if k != "hatalar"},
        }

    @app.get("/api/uretim")
    def uretim_durumu():
        return s["uretim"]

    @app.post("/api/uretim")
    def uretimi_yeniden_baslat():
        """Geçerli taslağı olmayanları (ör. hata alanları) yeniden hazırlar."""
        gerekli()
        if s["uretim"]["calisiyor"]:
            raise HTTPException(409, detail="Taslaklar zaten hazırlanıyor.")
        uretimi_baslat()
        return s["uretim"]

    @app.get("/api/basvurular")
    def liste(grup: str = "tum", asama: str = ""):
        gerekli()
        sonlar = depo.sonlar()
        satirlar = [satir(d, sonlar) for d in s["d"].values()]
        secim = {
            "olumsuz": lambda x: x["karar"] == "OLUMSUZ",
            "taslak": lambda x: x["durum"] == TASLAK_UYGUN,
            "ik": lambda x: x["durum"] == IK_INCELEME,
            "kapsam_disi": lambda x: x["durum"] == KAPSAM_DISI,
        }.get(grup, lambda x: True)
        return [x for x in satirlar if secim(x) and (not asama or x["asama"] == asama)]

    @app.get("/api/basvurular/{b}")
    def basvuru_detayi(b: str):
        return detay(b)

    @app.post("/api/basvurular/{b}/taslak")
    def taslak(b: str):
        d = basvuru(b)
        if d.karar_kodu != "OLUMSUZ":
            raise HTTPException(409, detail="Kabul edilen ya da değerlendirmesi süren başvuru için olumsuz e-posta üretilmez.")
        if b not in s["girdiler"]:
            raise HTTPException(409, detail="Bu başvuru İK incelemesinde; e-posta üretilmez. Neden: " + "; ".join(x.ad for x in d.bulgular))
        g, h = s["girdiler"][b]
        try:
            sonuc = taslak_uret(g, cagir)
        except llm.ModelHatasi as exc:
            raise HTTPException(502, detail=str(exc)) from exc
        depo.ekle(b, g, h, sonuc)
        return detay(b)

    @app.put("/api/basvurular/{b}/duzeltme")
    def duzeltme(b: str, govde: Duzeltme):
        basvuru(b)
        t = depo.son(b)
        g = s["girdiler"].get(b)
        if not t:
            raise HTTPException(404, detail="Önce taslak üretin.")
        if not g or t["girdi_hash"] != g[1]:
            raise HTTPException(409, detail="Veri değişti; bu taslak geçersiz. Yeni taslak üretin.")
        kontrol = kontrol_et(g[0], govde.konu.strip(), govde.metin.strip(), json.loads(t["kullanilan_idler"]))
        depo.duzeltme_kaydet(t["id"], govde.konu.strip(), govde.metin.strip(), kontrol)
        return detay(b)

    @app.post("/api/basvurular/{b}/onay")
    def onay(b: str, govde: Onay):
        basvuru(b)
        t = depo.son(b)
        g = s["girdiler"].get(b)
        if not t:
            raise HTTPException(404, detail="Onaylanacak taslak yok.")
        if not g or t["girdi_hash"] != g[1]:
            raise HTTPException(409, detail="Veri değişti; bu taslak onaylanamaz. Yeni taslak üretin.")
        if guncel_kontrol(t) and not govde.uyarilari_okudum:
            raise HTTPException(409, detail="Son kontrolde uyarılar var; okuduğunuzu işaretleyip yeniden onaylayın.")
        depo.onayla(t["id"], metin_hash(*guncel_metin(t)))
        return detay(b)

    @app.post("/api/yanitlar")
    def yanit_yukle(dosya: UploadFile = File(...)):
        """İkinci yol: yanıtlar dışarıda üretilip dosyayla yüklenir. Başvuru ID ile eşleşmeyen onaya açılmaz."""
        gerekli()
        icerik = dosya.file.read()
        if dosya.filename.lower().endswith(".json"):
            satirlar = json.loads(icerik.decode("utf-8"))
        else:
            satirlar = pd.read_excel(io.BytesIO(icerik)).fillna("").to_dict("records")
        kabul, red = [], []
        for r in satirlar:
            b = str(r.get("basvuru_id", "")).strip()
            if b not in s["girdiler"]:
                red.append({"basvuru_id": b, "neden": "Eşleşen ve taslağa uygun başvuru yok."})
                continue
            g, h = s["girdiler"][b]
            idler = r.get("kullanilan_kayit_idleri") or []
            idler = [x.strip() for x in idler.split(";") if x.strip()] if isinstance(idler, str) else list(idler)
            konu, metin = str(r.get("email_konu", "")).strip(), str(r.get("email_metni", "")).strip()
            depo.ekle(b, g, h, {"konu": konu, "metin": metin, "kullanilan_idler": idler, "emin_olunmayan": [],
                                "kontrol": kontrol_et(g, konu, metin, idler), "model": "dosya", "cagri_id": None}, kaynak="dosya")
            kabul.append(b)
        return {"kabul": kabul, "red": red}

    def excel(df, ad):
        tampon = io.BytesIO()
        df.to_excel(tampon, index=False)
        tampon.seek(0)
        return StreamingResponse(tampon, media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                                 headers={"Content-Disposition": f'attachment; filename="{ad}"'})

    @app.get("/api/disari/ik-listesi.xlsx")
    def ik_listesi():
        gerekli()
        rows = [{"Başvuru": d.basvuru_id, "Aşama": ASAMA_ADLARI.get(d.asama_kodu, d.asama_kodu or ""),
                 "Neden": "; ".join(x.ad for x in d.bulgular),
                 "Dayandığı kayıt": "; ".join(dict.fromkeys(k for x in d.bulgular for k in x.kayitlar)) or "—",
                 "Açıklama": " ".join(x.aciklama for x in d.bulgular)}
                for d in s["d"].values() if d.durum == IK_INCELEME]
        return excel(pd.DataFrame(rows), "ik_listesi.xlsx")

    @app.get("/api/disari/duzeltmeler.xlsx")
    def duzeltmeler():
        rows = [{"Başvuru": t["basvuru_id"], "Taslak ID": t["id"], "İlk konu": t["ilk_konu"], "İlk metin": t["ilk_metin"],
                 "İK konu": t["ik_konu"], "İK metni": t["ik_metin"], "Düzeltme zamanı": t["ik_zaman"],
                 "Onay zamanı": t["onay_zaman"] or ""} for t in depo.duzeltmeler()]
        return excel(pd.DataFrame(rows), "ik_duzeltmeleri.xlsx")

    @app.get("/api/is-yuku")
    def is_yuku(okuma_dk: float = 0.5, kontrol_dk: float = 1.0, duzeltme_orani: float = 0.10, duzeltme_dk: float = 2.0,
                sorunlulari_elle_yaz: bool = False):
        gerekli()
        t = s["veri"].tablolar
        if "is_yuku" not in t or "planlama" not in t:
            raise HTTPException(404, detail="Dosyada İş Yükü Verileri ya da Planlama Verileri sayfası yok.")
        return hesapla(t["is_yuku"].to_dict("records"), t["planlama"].to_dict("records"),
                       okuma_dk, kontrol_dk, duzeltme_orani, duzeltme_dk, sorunlulari_elle_yaz)

    if FRONTEND.exists():
        app.mount("/", StaticFiles(directory=FRONTEND, html=True), name="arayuz")
    return app
