"""Başvuruları kayıtlı karara göre ayırır ve İK incelemesi gerektiren kayıtları bulur.

Kural motoru karar vermez ve kararı değiştirmez. Yalnız kayıtlı kararın dayanaklarının
mevcut, güncel, tutarlı ve paylaşılabilir olup olmadığını kontrol eder (Paylaşım
Kuralları PK-01…PK-05). Bir bulgu çıkan olumsuz başvuru için aday e-postası üretilmez.
"""
import hashlib
import json
import re
from dataclasses import dataclass, field

import pandas as pd

KARAR_KODLARI = {"OLUMSUZ", "KABUL", "DEVAM_EDIYOR"}
OZNEL_ASAMALAR = {"VIDEO", "GRUP", "IK_TEKNIK"}
KAYIT_GEREKEN_ASAMALAR = OZNEL_ASAMALAR | {"INGILIZCE"}
GECERLI_GEREKCELER = {"GEREKLILIK_KARSILANMADI", "KONTENJAN_KISITI"}
KISILIK_YARGISI = re.compile(r"kişiliği|içine kapanık|uyum sağlayamaz", re.IGNORECASE)

TASLAK_UYGUN = "Taslağa uygun"
IK_INCELEME = "İK incelemesi"
KAPSAM_DISI = "Kapsam dışı"

BULGU_ADLARI = {
    "KARAR_YOK": "Karar kaydı yok",
    "KARAR_KODU": "Karar kodu eksik ya da tanımsız",
    "COKLU_KARAR": "Birden fazla karar kaydı",
    "DAYANAK_YOK": "Kararın dayanağı belirtilmemiş",
    "DAYANAK_BULUNAMADI": "Dayanak kaydı bulunamadı",
    "BASKA_BASVURU": "Dayanak başka başvuruya ait",
    "DUZELTME": "Dayanak sonradan düzeltilmiş",
    "KURUM_ICI": "Dayanak kurum içi",
    "KISILIK_YARGISI": "Kişilik yargısı",
    "SINAV_TOPLAM": "Sınav sayıları tutarsız",
    "SONUC_BARAJ": "Sonuç barajla çelişiyor",
    "GECILEN_DAYANAK": "Geçilen değerlendirme ret dayanağı",
    "DAYANAK_ASAMA_FARKLI": "Dayanak başka aşamaya ait",
    "ASAMA_KAYDI_YOK": "Karar aşamasında kayıt yok",
    "ASAMA_SURUYOR": "Aşama değerlendirmesi sürüyor",
    "IK_NOTU_YOK": "İK notu yok",
    "GEREKCE_YOK": "Ret gerekçesi yazılmamış",
    "TEYIT_YOK": "Paylaşım teyidi yok",
    "PAYLASIM_ONAYSIZ": "Paylaşım onaylanmamış",
    "COKLU_GOZLEM": "Aynı görevde birden fazla gözlem",
}


@dataclass
class Bulgu:
    kod: str
    aciklama: str
    kayitlar: list = field(default_factory=list)

    @property
    def ad(self):
        return BULGU_ADLARI.get(self.kod, self.kod)


@dataclass
class Degerlendirme:
    basvuru_id: str
    karar_kodu: str | None
    asama_kodu: str | None
    durum: str
    bulgular: list = field(default_factory=list)
    uyarilar: list = field(default_factory=list)
    dayanak_kayitlari: list = field(default_factory=list)
    parmak_izi: str = ""


def kimlikler(deger):
    """Noktalı virgülle ayrılmış kayıt ID'lerini listeye çevirir."""
    if deger is None or (isinstance(deger, float) and pd.isna(deger)):
        return []
    return [x.strip() for x in str(deger).split(";") if x.strip()]


def _bos(v):
    return v is None or (isinstance(v, float) and pd.isna(v)) or v == ""


class KuralMotoru:
    def __init__(self, veri):
        self.t = veri.tablolar
        self.kaynaklar = {}
        for key in ("asama_kayitlari", "sinav", "dil", "ik_notlari"):
            for row in self.t.get(key, pd.DataFrame()).to_dict("records"):
                self.kaynaklar[row["kaynak_id"]] = (key, row)
        self.duzeltmeler = {}
        for key in ("asama_kayitlari", "sinav"):
            df = self.t.get(key, pd.DataFrame())
            if "duzelttigi_kaynak_id" in df:
                for row in df[df["duzelttigi_kaynak_id"].notna()].to_dict("records"):
                    self.duzeltmeler[row["duzelttigi_kaynak_id"]] = row["kaynak_id"]
        self.gruplar = {
            key: {b: g for b, g in df.groupby("basvuru_id")}
            for key, df in self.t.items() if "basvuru_id" in df
        }

    def kayit(self, kaynak_id):
        """Bir kayıt ID'sinin (tablo, satır) bilgisini döndürür; yoksa None."""
        return self.kaynaklar.get(kaynak_id)

    def _satirlar(self, key, b):
        return self.gruplar.get(key, {}).get(b, pd.DataFrame(columns=self.t.get(key, pd.DataFrame()).columns))

    def _parmak_izi(self, b):
        parcalar = []
        for key in sorted(self.gruplar):
            rows = self._satirlar(key, b)
            parcalar.append([key, rows.astype(str).values.tolist()])
        metin = json.dumps(parcalar, ensure_ascii=False, default=str)
        return hashlib.sha256(metin.encode("utf-8")).hexdigest()[:16]

    def degerlendir(self):
        kararlar = self.t["kararlar"]
        tum = list(dict.fromkeys(list(kararlar["basvuru_id"].dropna()) +
                                 list(self.t.get("basvurular", pd.DataFrame(columns=["basvuru_id"]))["basvuru_id"].dropna())))
        sonuc = []
        for b in tum:
            k = self._satirlar("kararlar", b)
            if k.empty:
                d = Degerlendirme(b, None, None, IK_INCELEME, [Bulgu("KARAR_YOK", "Başvurunun karar kaydı yok.")])
            elif len(k) > 1:
                d = Degerlendirme(b, None, None, IK_INCELEME,
                                  [Bulgu("COKLU_KARAR", "Başvurunun birden fazla karar kaydı var.", list(k["kaynak_id"]))])
            else:
                d = self._tek(b, k.iloc[0].to_dict())
            d.parmak_izi = self._parmak_izi(b)
            sonuc.append(d)
        return sonuc

    def _tek(self, b, k):
        kod, asama = k.get("karar_kodu"), k.get("asama_kodu")
        if kod not in KARAR_KODLARI:
            return Degerlendirme(b, kod, asama, IK_INCELEME,
                                 [Bulgu("KARAR_KODU", f"Karar kodu tanınmıyor: {kod or 'boş'}.", [k.get("kaynak_id")])])
        if kod != "OLUMSUZ":
            return Degerlendirme(b, kod, asama, KAPSAM_DISI)

        bulgular, uyarilar, dayanaklar = [], [], []
        karar_dayanak = kimlikler(k.get("dayanak_kaynak_idleri"))
        if not karar_dayanak:
            bulgular.append(Bulgu("DAYANAK_YOK", "Olumsuz kararın dayandığı kayıt belirtilmemiş.", [k.get("kaynak_id")]))
        for d in karar_dayanak:
            self._dayanak_kontrol(d, b, asama, bulgular, karardan=True)
        dayanaklar += karar_dayanak

        asama_satirlari = self._satirlar("asama_kayitlari", b)
        asama_satirlari = asama_satirlari[asama_satirlari["asama_kodu"] == asama]
        if asama in KAYIT_GEREKEN_ASAMALAR and asama_satirlari.empty:
            bulgular.append(Bulgu("ASAMA_KAYDI_YOK", "Karar aşamasına ait kayıt yok; aday bu aşamaya katılmamış olabilir."))
        surenler = asama_satirlari[asama_satirlari["asama_durumu"] == "DEGERLENDIRILIYOR"]
        if not surenler.empty:
            bulgular.append(Bulgu("ASAMA_SURUYOR", "Karar aşamasının değerlendirmesi sürüyor.", list(surenler["kaynak_id"])))

        if asama in OZNEL_ASAMALAR:
            notlar = self._satirlar("ik_notlari", b)
            if notlar.empty:
                bulgular.append(Bulgu("IK_NOTU_YOK", "Öznel aşama retinde son İK gerekçesi bulunmuyor."))
            else:
                n = notlar.sort_values("kayit_tarihi").iloc[-1].to_dict()
                dayanaklar.append(n["kaynak_id"])
                gerekce, teyit = n.get("gerekce_kodu"), n.get("dis_paylasim_teyidi")
                if gerekce not in GECERLI_GEREKCELER:
                    bulgular.append(Bulgu("GEREKCE_YOK", f"Ret gerekçesi kodu: {gerekce or 'boş'}.", [n["kaynak_id"]]))
                if teyit == "HAYIR":
                    bulgular.append(Bulgu("PAYLASIM_ONAYSIZ", "İK gerekçenin adayla paylaşımını onaylamamış.", [n["kaynak_id"]]))
                elif teyit != "EVET":
                    bulgular.append(Bulgu("TEYIT_YOK", f"Paylaşım teyidi: {teyit or 'boş'}.", [n["kaynak_id"]]))
                for d in kimlikler(n.get("dayanak_kaynak_idleri")):
                    self._dayanak_kontrol(d, b, asama, bulgular, karardan=False)
                    dayanaklar.append(d)
                if not _bos(n.get("kurum_ici_not")):
                    uyarilar.append("Kurum içi not var: içeriği ve iç kodlar e-postaya aktarılmamalı.")
                if gerekce == "KONTENJAN_KISITI":
                    uyarilar.append("Kontenjan reddi: yetersizlik ima edilmemeli; gelişim önerisi ve vaat olmamalı.")

        degerlendirici = asama_satirlari[asama_satirlari["gereklilik_kodu"].notna()
                                         & asama_satirlari["duzelttigi_kaynak_id"].isna()
                                         & ~asama_satirlari["kaynak_id"].isin(self.duzeltmeler.keys())]
        for etkinlik, g in degerlendirici.groupby("etkinlik_id"):
            if len(g) > 1:
                bulgular.append(Bulgu("COKLU_GOZLEM", f"{etkinlik} için birden fazla değerlendirici gözlemi var; "
                                      "ortak sonuç girilmemiş, tutarlılığı İK doğrulamalı.", list(g["kaynak_id"])))

        if asama == "SINAV":
            kalan = [d for d in karar_dayanak if (self.kayit(d) or (None, {}))[1].get("kayitli_sonuc") == "GECEMEDI"]
            if len(kalan) > 1:
                uyarilar.append("Birden fazla sınav bölümü baraj altında: her bölüm ayrı anlatılmalı.")

        tekil = {}
        for bulgu in bulgular:
            tekil.setdefault((bulgu.kod, tuple(bulgu.kayitlar)), bulgu)
        durum = IK_INCELEME if tekil else TASLAK_UYGUN
        return Degerlendirme(b, kod, asama, durum, list(tekil.values()), uyarilar, list(dict.fromkeys(dayanaklar)))

    def _dayanak_kontrol(self, d, b, asama, bulgular, karardan):
        bilgi = self.kayit(d)
        if bilgi is None:
            bulgular.append(Bulgu("DAYANAK_BULUNAMADI", f"{d} hiçbir kayıt sayfasında yok.", [d]))
            return
        tablo, r = bilgi
        if r.get("basvuru_id") != b:
            bulgular.append(Bulgu("BASKA_BASVURU", f"{d} başka bir başvuruya ({r.get('basvuru_id')}) ait.", [d]))
            return
        if d in self.duzeltmeler:
            yeni = self.duzeltmeler[d]
            bulgular.append(Bulgu("DUZELTME", f"{d}, kararın ardından {yeni} ile düzeltilmiş; karar ve İK notu güncellenmemiş.", [d, yeni]))
        if r.get("paylasim_kodu") == "KURUM_ICI":
            bulgular.append(Bulgu("KURUM_ICI", f"{d} kurum içi; içeriği adayla paylaşılamaz.", [d]))
        if isinstance(r.get("gozlem_metni"), str) and KISILIK_YARGISI.search(r["gozlem_metni"]):
            bulgular.append(Bulgu("KISILIK_YARGISI", f"{d} somut örneği olmayan bir kişilik yargısı içeriyor.", [d]))
        if tablo == "asama_kayitlari" and r.get("asama_kodu") != asama:
            bulgular.append(Bulgu("DAYANAK_ASAMA_FARKLI", f"{d} karar aşamasına değil {r.get('asama_kodu')} aşamasına ait.", [d]))
        if tablo == "sinav":
            if r["dogru_sayisi"] + r["yanlis_sayisi"] + r["bos_sayisi"] != r["soru_sayisi"]:
                bulgular.append(Bulgu("SINAV_TOPLAM", f"{d}: doğru + yanlış + boş, soru sayısına eşit değil.", [d]))
            beklenen = "GECTI" if r["dogru_sayisi"] >= r["gecme_baraji"] else "GECEMEDI"
            if beklenen != r.get("kayitli_sonuc"):
                bulgular.append(Bulgu("SONUC_BARAJ", f"{d}: kayıtlı sonuç barajla çelişiyor.", [d]))
            if karardan and r.get("kayitli_sonuc") == "GECTI":
                bulgular.append(Bulgu("GECILEN_DAYANAK", f"{d}: geçilen bir sınav bölümü ret dayanağı gösterilmiş.", [d]))
        if tablo == "dil":
            beklenen = "GECTI" if r["kayitli_puan"] >= r["gecme_baraji"] else "GECEMEDI"
            if beklenen != r.get("kayitli_sonuc"):
                bulgular.append(Bulgu("SONUC_BARAJ", f"{d}: kayıtlı sonuç barajla çelişiyor.", [d]))
            if karardan and r.get("kayitli_sonuc") == "GECTI":
                bulgular.append(Bulgu("GECILEN_DAYANAK", f"{d}: geçilen görüşme ret dayanağı gösterilmiş.", [d]))


def ozet(degerlendirmeler):
    say = lambda f: sum(1 for d in degerlendirmeler if f(d))
    return {
        "toplam": len(degerlendirmeler),
        "olumsuz": say(lambda d: d.karar_kodu == "OLUMSUZ"),
        "kabul": say(lambda d: d.karar_kodu == "KABUL"),
        "devam": say(lambda d: d.karar_kodu == "DEVAM_EDIYOR"),
        "veri_sorunu": say(lambda d: d.karar_kodu not in KARAR_KODLARI),
        "taslaga_uygun": say(lambda d: d.durum == TASLAK_UYGUN),
        "ik_incelemesi": say(lambda d: d.durum == IK_INCELEME),
    }
