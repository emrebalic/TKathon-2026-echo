"""İK geri bildirim paneli: dosya yükleme, sayım, İK'ya ayırma ve dayanak kayıtları.

Çalıştırma: streamlit run app/main.py
"""
import io
import sys
from pathlib import Path

import pandas as pd
import streamlit as st

KOK = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(KOK))

from core.loader import yukle  # noqa: E402
from core.rules import IK_INCELEME, KAPSAM_DISI, TASLAK_UYGUN, KuralMotoru, ozet  # noqa: E402
from core.schema import SHEETS  # noqa: E402

ORNEK_DOSYA = KOK / "data" / "raw" / "02_Veriler.xlsx"
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


st.sidebar.header("Veri dosyası")
yuklenen = st.sidebar.file_uploader("ATS Excel dosyası", type=["xlsx"])
if yuklenen is not None:
    icerik, dosya_adi = yuklenen.getvalue(), yuklenen.name
elif ORNEK_DOSYA.exists():
    icerik, dosya_adi = ORNEK_DOSYA.read_bytes(), ORNEK_DOSYA.name
    st.sidebar.caption("Dosya yüklenmedi; örnek veri kullanılıyor.")
else:
    st.info("Başlamak için soldan bir Excel dosyası yükleyin.")
    st.stop()

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

st.title("Junior Wings geri bildirim paneli")
st.caption(f"Dosya: {dosya_adi}")

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
