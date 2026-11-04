"""İki yükleme arasında hangi başvuruların değiştiğini parmak izlerinden bulur."""


def degisen_basvurular(onceki: dict, simdiki: dict) -> dict:
    """{başvuru_id: parmak_izi} sözlüklerini karşılaştırır: {degisen, yeni, silinen}."""
    return {
        "degisen": sorted(b for b in simdiki if b in onceki and onceki[b] != simdiki[b]),
        "yeni": sorted(b for b in simdiki if b not in onceki),
        "silinen": sorted(b for b in onceki if b not in simdiki),
    }
