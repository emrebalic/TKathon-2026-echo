"""İK iş yükü: vaka formülüyle elle süreç ve parametreli önerilen süreç (1.200 başvuruluk dönem)."""


def hesapla(is_yuku, planlama, okuma_dk=0.5, kontrol_dk=1.0, duzeltme_orani=0.10, duzeltme_dk=2.0,
            sorunlulari_elle_yaz=False):
    """`is_yuku` ve `planlama` dosyadaki sayfaların satırlarıdır (teknik sütun adlarıyla)."""
    p = planlama[0]
    gunluk = p["ayrilan_toplam_ik_saati"] / p["is_gunu_sayisi"]
    asamalar, elle_dk, oneri_dk = [], 0.0, 0.0
    for r in is_yuku:
        n, ek = r["olumsuz_basvuru_sayisi"], r["ek_inceleme_sayisi"]
        elle = n * (r["kayit_okuma_dk"] + r["taslak_yazma_dk"] + r["son_kontrol_dk"]) + ek * r["ek_inceleme_dk"]
        oneri = n * (okuma_dk + kontrol_dk) + n * duzeltme_orani * duzeltme_dk + ek * r["ek_inceleme_dk"]
        if sorunlulari_elle_yaz:
            oneri += ek * r["taslak_yazma_dk"]
        asamalar.append({"asama": r["asama_kodu"], "olumsuz": n, "ek_inceleme": ek,
                         "elle_saat": round(elle / 60, 1), "oneri_saat": round(oneri / 60, 1)})
        elle_dk += elle
        oneri_dk += oneri

    def ozet(dk):
        saat = dk / 60
        return {"dakika": round(dk), "saat": round(saat, 1), "is_gunu": round(saat / gunluk, 1),
                "kapasiteye_sigar": saat <= p["ayrilan_toplam_ik_saati"]}

    return {
        "kapasite_saat": p["ayrilan_toplam_ik_saati"],
        "is_gunu": p["is_gunu_sayisi"],
        "elle": ozet(elle_dk),
        "oneri": ozet(oneri_dk),
        "asamalar": asamalar,
        "parametreler": {"okuma_dk": okuma_dk, "kontrol_dk": kontrol_dk, "duzeltme_orani": duzeltme_orani,
                         "duzeltme_dk": duzeltme_dk, "sorunlulari_elle_yaz": sorunlulari_elle_yaz},
    }
