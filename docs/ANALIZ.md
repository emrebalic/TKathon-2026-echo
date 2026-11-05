# Veri analizi bulguları

Kaynak: 120 kurgusal başvuruluk ham dosya (depoda yok; `data/test/` dosyaları bunun alt kümesidir). Grafikli rapor: https://claude.ai/artifact/A8Nvwk6ZSrNjmFQzZKDYi6

## Sayılar

| Sonuç | Adet |
|---|---|
| OLUMSUZ | 80 (Sınav 24 · Video 16 · Grup 16 · İngilizce görüşme 12 · İK ve birim 12) |
| KABUL | 20 |
| DEVAM_EDIYOR | 20 |

Olumsuzların 57'si taslağa uygun (4'ü kontenjan reddi), 23'ü İK incelemesine ayrılmalı.

## İK'ya ayrılacak 23 başvuru

| Neden | Başvurular |
|---|---|
| Aynı görevde birden fazla, çelişen gözlem | BSV-003, 049, 053, 082 |
| Dayanak sonradan düzeltilmiş | BSV-005, 045, 059, 077; BSV-033 (sınav yeniden puanlandı, 6→11, GEÇTİ) |
| Öznel aşamada İK notu yok | BSV-040, 057, 081 |
| Ret gerekçesi kodu BELIRTILMEDI | BSV-044, 061, 083 |
| Paylaşım teyidi BELIRTILMEDI | BSV-047, 062, 079 |
| Teyit HAYIR ve dayanak KURUM_ICI | BSV-007, 048, 064, 084 |
| Dayanak KURUM_ICI ve kişilik yargısı | BSV-006 |

## Dikkat edilecek tuzaklar

- Teyidi EVET olan 31 başvurudan 9'u yine de İK'ya gider: EVET, çelişkiyi, düzeltmeyi ve KURUM_ICI kısıtını kaldırmaz.
- Eksiklik bildiren gözlemlerin tamamı karar aşamasında. Geçilmiş aşamalardaki gözlemlerin hiçbiri eksiklik bildirmiyor: modele yalnız karar aşamasının kayıtları verilmeli.
- Düzeltmelerin 5'i de karardan 19–20 saat sonra girilmiş; hiçbirinde karar güncellenmemiş.
- Baraj "en az" demek: 29 sınav satırı tam barajda GEÇTİ. Sonucu yeniden hesaplamak yerine kayıtlı sonucu kullanın.
- İki ayrı İngilizce barajı var: sınavda 10/15 doğru, sözlü görüşmede 12/20 puan.
- Görüşme puanı dil seviyesi değildir; CEFR veya "B2" yazılmaz. Envanter yalnız tamamlanma kaydıdır.
- Kontenjan reddinde (BSV-008, 076, 078, 080) yetersizlik, gelişim önerisi veya vaat olmaz.
- Kurum içi notlar ve iç kodlar (T101-…, GRP-B, KP-…) modele verilmemeli; taslağa uygun 7 başvuruda bu not var.
- 8 sınav reddinde iki bölüm de baraj altında; e-posta ikisini de anlatmalı.
- Sütun başlıklarında tipografik kesme işareti (’) var; İK notlarındaki M–N sütunları Excel formülü.

## İş yükü (1.200 başvuruluk dönem)

Elle hazırlama: 259,2 saat; 120 saatlik kapasiteyle 43,2 iş günü (kapasiteye sığmaz).
Taslak başına İK kontrolü ve düzeltmesi 3,8 dakikayı aşarsa önerilen süreç de 20 iş gününe sığmaz.
Bu süre ekip tarafından ölçülmeli.
