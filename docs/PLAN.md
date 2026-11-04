# Ekip planı

5 kişi, 6 saat. Sabit saatler: **16.30** son iç kontrol ve yükleme başlangıcı, **16.45** son teslim, **17.00** sunumlar.

## Roller

| Kişi | Dal | Sorumluluk | Teslim |
|---|---|---|---|
| 1 | `backend` | Okuyucu, kural motoru, taslak / düzeltme / onay deposu, parmak iziyle onay düşürme | MVP |
| 2 | `ai` | Muse istemi, JSON çıktı, kural kontrolü + Muse kontrolcüsü, ham girdi/yanıt kaydı | MVP, özetin 03. bölümü |
| 3 | `ui` | Panel: sayılar, listeler, taslak düzenleme ve onay akışı | MVP, video |
| 4 | `ideathon` | Sorun ve kanıt, A–G kararları, kontrol süresi ölçümü, iş yükü Excel'i, tek sayfalık .docx | Teslim 01, 03 |
| 5 | `sunum` | 40/60 satırlık ve değiştirilmiş test dosyaları, üç testin ekran görüntüleri, pptx, 90 sn video, ek görevler | Teslim 03, 04, 05 |

## Zaman çizelgesi

| Saat | Herkes | Kontrol noktası |
|---|---|---|
| Başlangıç + 0:45 | Veriyi anla (`docs/ANALIZ.md`, `docs/TUZAKLAR.md`), A–G kararlarında anlaş | Kararlar yazılı |
| → 14.30 | Paralel geliştirme | Muse bağlantısı çalışıyor; ilk taslak üretildi |
| 14.30 – 15.30 | Onay akışı, kontrol katmanı, ek görevler; Kişi 4 kontrol süresini ölçer | Bir taslak üretilip düzeltilip onaylandı |
| 15.30 – 16.00 | `main`'e birleştir; üç testi çalıştır, ekran görüntüleri | 7. slayt ve test dosyası dolu |
| 16.00 – 16.30 | Video kaydı, pptx, .docx, MVP zip'i | Teslim listesi tamam |
| 16.30 – 16.45 | TKDrive'a yükleme | Bütün dosyalar yüklendi |

## Kurallar

- Her saat başı 5 dakikalık durum turu: ne bitti, ne takıldı.
- `main`'e yalnız testleri geçen kod girer (`pytest`).
- Sayılar ve başvuru ID'leri koda yazılmaz; her şey yüklenen dosyadan hesaplanır.
- Kırmızı çizgiler için `docs/VAKA.md`; şüphede İK'ya ayır.

## Mentorlere sorulacaklar

- İşe Alım tarafındaki mentorlere: bir geri bildirim e-postasının İK kontrolü gerçekte kaç dakika sürer? A–G'de hangi
  ayrıntı düzeyi İK pratiğine uyar?
- Yapay zekâ mentorlerine: kontrol katmanı için kural ve model kontrolünü ayırma yaklaşımımız makul mü?

Mentorlerin adları ve uzmanlıkları yalnız yerel kopyada: `materials/MENTORLER.md` (git'e girmez).
