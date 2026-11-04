"""İK geri bildirim paneli: dosya yükleme, sayım, İK'ya ayırma ve dayanak kayıtları.

Çalıştırma: streamlit run app/main.py
"""
import io
import sys
from datetime import datetime
from pathlib import Path

import pandas as pd
import streamlit as st

KOK = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(KOK))

from core.degisiklik import degisen_basvurular  # noqa: E402
from core.loader import yukle  # noqa: E402
from core.rules import IK_INCELEME, KAPSAM_DISI, TASLAK_UYGUN, KuralMotoru, ozet  # noqa: E402
from core.schema import SHEETS  # noqa: E402

ASAMA_ADLARI = {"SINAV": "Sınav", "VIDEO": "Video", "GRUP": "Grup", "INGILIZCE": "İngilizce görüşme",
                "ENVANTER": "Envanter", "IK_TEKNIK": "İK ve birim", "TEKLIF": "Teklif", "BELGE": "Belge"}

st.set_page_config(page_title="Junior Wings geri bildirim", layout="wide")


@st.cache_data(show_spinner="Dosya okunuyor…")
def oku(icerik: bytes):
    return yukle(io.BytesIO(icerik))


def kayit_ozeti(tablo, r):
    if tablo == "sinav":
        return (f"{r['test_turu']}: {r['dogru_sayisi']}/{r['soru_sayisi']} doğru, baraj {r['gecme_baraji']}, "
                f"{r['kayitli_sonuc']}")
    if tablo == "dil":
        return (f"{r['kayitli_puan']}/{r['olcek_tavani']} puan, baraj {r['gecme_baraji']}, {r['kayitli_sonuc']}. "
                f"{r['gozlem_metni']}")
    if tablo == "ik_notlari":
        return f"{r['gerekce_kodu']} · teyit {r['dis_paylasim_teyidi']}. {r['nihai_ret_gerekcesi'] or ''}"
    return r.get("gozlem_metni") or ""


def kisalt(liste, en_fazla=8):
    return ", ".join(liste) if len(liste) <= en_fazla else ", ".join(liste[:en_fazla]) + f" ve {len(liste) - en_fazla} başvuru daha"


st.sidebar.header("Veri dosyası")
yuklenen = st.sidebar.file_uploader("ATS Excel dosyası", type=["xlsx"])
if yuklenen is None:
    st.title("Junior Wings geri bildirim paneli")
    st.info("Başlamak için soldan ATS Excel dosyasını yükleyin. Veri değiştiğinde dosyayı yeniden yükleyin.")
    st.stop()
icerik, dosya_adi = yuklenen.getvalue(), yuklenen.name

veri = oku(icerik)
if not veri.gecerli:
    st.error("Dosya beklenen yapıda değil.")
    for hata in veri.hatalar:
        st.write("•", hata)
    st.stop()
for uyari in veri.uyarilar:
    st.sidebar.warning(uyari)

motor = KuralMotoru(veri)
degerlendirmeler = motor.degerlendir()
sayilar = ozet(degerlendirmeler)

# Aynı oturumdaki bir önceki yüklemeyle karşılaştır: kaydı değişen başvurunun parmak izi değişir.
izler = {d.basvuru_id: d.parmak_izi for d in degerlendirmeler}
onceki = st.session_state.get("izler")
if onceki is not None and onceki != izler:
    st.session_state["son_degisim"] = (datetime.now(), st.session_state.get("dosya_adi"), degisen_basvurular(onceki, izler))
st.session_state["izler"], st.session_state["dosya_adi"] = izler, dosya_adi

st.title("Junior Wings geri bildirim paneli")
st.caption(f"Dosya: {dosya_adi}")
if "son_degisim" in st.session_state:
    zaman, eski_ad, fark = st.session_state["son_degisim"]
    parcalar = [f"{ad}: {kisalt(liste)}" for ad, liste in
                (("değişen", fark["degisen"]), ("yeni", fark["yeni"]), ("dosyada artık yok", fark["silinen"])) if liste]
    st.info(f"{zaman:%H:%M:%S} yüklemesi, bir önceki dosyayla ({eski_ad}) karşılaştırıldı · " + " · ".join(parcalar)
            + ". Değişen başvuruların eski taslağı ve İK onayı geçersizdir.")

c = st.columns(4)
c[0].metric("Toplam başvuru", sayilar["toplam"])
c[1].metric("Olumsuz", sayilar["olumsuz"])
c[2].metric("Kabul", sayilar["kabul"])
c[3].metric("Değerlendirmesi süren", sayilar["devam"])
c = st.columns(4)
c[0].metric("Taslağa uygun (henüz işlenmedi)", sayilar["taslaga_uygun"])
c[1].metric("İK incelemesi bekleyen", sayilar["ik_incelemesi"])
c[2].metric("Veri sorunu (karar kodu)", sayilar["veri_sorunu"])

tablo = pd.DataFrame([{
    "Başvuru": d.basvuru_id,
    "Karar": d.karar_kodu or "—",
    "Aşama": ASAMA_ADLARI.get(d.asama_kodu, d.asama_kodu or "—"),
    "Durum": d.durum,
    "İnceleme nedeni": "; ".join(b.ad for b in d.bulgular),
    "Dikkat": "; ".join(d.uyarilar),
} for d in degerlendirmeler])

sekme_olumsuz, sekme_ik, sekme_diger = st.tabs(["Olumsuz başvurular", "İK incelemesi", "Kapsam dışı"])
with sekme_olumsuz:
    st.dataframe(tablo[tablo["Karar"] == "OLUMSUZ"], hide_index=True)
with sekme_ik:
    st.dataframe(tablo[tablo["Durum"] == IK_INCELEME][["Başvuru", "Karar", "Aşama", "İnceleme nedeni"]], hide_index=True)
with sekme_diger:
    st.dataframe(tablo[tablo["Durum"] == KAPSAM_DISI][["Başvuru", "Karar", "Aşama"]], hide_index=True)

st.divider()
st.subheader("Başvuru ayrıntısı")
secenekler = [d for d in degerlendirmeler if d.karar_kodu == "OLUMSUZ" or d.durum == IK_INCELEME]
secim = st.selectbox("Olumsuz ya da İK incelemesindeki başvuru", secenekler,
                     format_func=lambda d: f"{d.basvuru_id} · {ASAMA_ADLARI.get(d.asama_kodu, d.asama_kodu)} · {d.durum}")
if secim:
    if secim.durum == IK_INCELEME:
        st.error("Bu başvuru için aday e-postası üretilmez. İK inceleme nedeni:")
        for b in secim.bulgular:
            st.write(f"• **{b.ad}**: {b.aciklama}")
    else:
        st.success("Kayıtlar tutarlı; yapay zekâ taslağı üretilebilir.")
    for u in secim.uyarilar:
        st.warning(u)

    satirlar = []
    for kid in secim.dayanak_kayitlari or [k for b in secim.bulgular for k in b.kayitlar]:
        bilgi = motor.kayit(kid)
        if bilgi is None:
            satirlar.append({"Kayıt ID": kid, "Sayfa": "bulunamadı", "Aşama": "", "Paylaşım": "", "İçerik": ""})
            continue
        t, r = bilgi
        satirlar.append({"Kayıt ID": kid, "Sayfa": SHEETS[t], "Aşama": ASAMA_ADLARI.get(r.get("asama_kodu"), ""),
                         "Paylaşım": r.get("paylasim_kodu") or "", "İçerik": kayit_ozeti(t, r)})
    st.markdown("**Taslağın dayandığı kayıtlar**")
    st.dataframe(pd.DataFrame(satirlar), hide_index=True)
    st.caption(f"Kayıt parmak izi: {secim.parmak_izi} · veri değişirse taslak ve İK onayı geçersiz olur.")

    if secim.durum == TASLAK_UYGUN:
        st.markdown("**Yapay zekâ taslağı**")
        st.info("Taslak üretimi `core/llm.py` bağlandığında burada görünecek.")
