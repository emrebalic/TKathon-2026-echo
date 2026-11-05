# Analiz betikleri

`docs/ANALIZ.md`, `docs/TUZAKLAR.md` ve grafikli EDA raporu bu betiklerle üretildi. Uygulamanın kendisi
`core/rules.py`'yi kullanır; buradakiler keşif ve rapor içindir.

| Betik | Ne yapar | Çalıştırma |
|---|---|---|
| `kural_taramasi.py` | Her olumsuz başvuruyu tarar ve işaretleri listeler; `detail` modunda bir başvurunun bütün kayıt izini döker | `python tools/analiz/kural_taramasi.py data/test/Veriler_60_basvuru.xlsx flags`<br>`python tools/analiz/kural_taramasi.py data/test/Veriler_60_basvuru.xlsx detail BSV-003,BSV-033` |
| `ince_tuzaklar.py` | Tarih sıralaması, baraj sınırı, iki İngilizce barajı, gözlem kalıpları, kurum içi notlar | `python tools/analiz/ince_tuzaklar.py data/test/Veriler_60_basvuru.xlsx` |
| `eda_veri_setleri.py` | EDA raporunun JSON veri setlerini ve tuzak kataloğunu üretir | `python tools/analiz/eda_veri_setleri.py data/test/Veriler_60_basvuru.xlsx cikti/` |

Betikler orijinal Excel başlıklarını doğrudan kullanır; sütun adları değişmiş bir dosyada `core/loader.py` tercih edilmeli.
