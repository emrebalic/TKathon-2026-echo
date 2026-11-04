# İK iş yükü hesabı

Hesap 1.200 başvuruluk dönem için yapılır (İş Yükü Verileri + Planlama Verileri). Dosyadaki 120 başvurunun sonucu
doğrudan 1.200 ile kıyaslanmaz; 120'lik örnekte sorunlu kayıtlar bilerek artırılmış. Tablodaki süreler e-postaların
tamamen elle hazırlanması içindir ve ölçülmüş işlem süresi değil, ayrılan kapasitedir.

## Formül

- Toplam iş yükü = Σ aşama [olumsuz × (okuma + yazma + son kontrol) + ek inceleme × ek süre]
- Dönüş süresi = toplam saat ÷ (ayrılan saat ÷ iş günü) = toplam saat ÷ 6 saat/gün

## Elle hazırlama

| Aşama | Olumsuz | Ek inceleme | Okuma + yazma + kontrol (dk) | Ek süre (dk) | Toplam (dk) | Saat |
|---|---|---|---|---|---|---|
| Sınav | 600 | 60 | 4 + 5 + 2 = 11 | 6 | 6.960 | 116,0 |
| Video | 300 | 36 | 4 + 5 + 3 = 12 | 8 | 3.888 | 64,8 |
| Grup | 160 | 32 | 5 + 6 + 3 = 14 | 10 | 2.560 | 42,7 |
| İngilizce görüşme | 100 | 20 | 4 + 5 + 3 = 12 | 8 | 1.360 | 22,7 |
| İK ve birim | 40 | 12 | 6 + 7 + 3 = 16 | 12 | 784 | 13,1 |
| **Toplam** | **1.200** | **160** | | | **15.552** | **259,2** |

Kapasite 120 saat / 20 iş günü → **dönüş süresi 43,2 iş günü; kapasiteye sığmaz** (2,16 kat).

## Takımın önerilen süreç hesabı (çözüm özetindeki)

Bütün 1.200 başvuru için okuma 0,5 dk + İK kontrolü 1 dk (30 saat); başvuruların %10'unda 2 dk düzeltme (4 saat);
ek inceleme süreleri dosyadan (1.272 dk = 21,2 saat) → **55,2 saat, 9,2 iş günü; kapasiteye sığar.**
MVP'nin İş yükü sekmesi bu varsayılanlarla açılır; değerler değiştirilerek duyarlılık gösterilir.

**Dikkat:** Sorunlu 160 başvuruya yapay zekâ taslağı üretilmiyor, e-postaları elle yazılıyor. Yazma süresi eklenince
(+856 dk ≈ 14,3 sa) toplam **≈ 69,5 saat, 11,6 iş günü**; yine kapasiteye sığar. Sekmede "Sorunlu başvuruların e-postası
elle yazılır" seçeneği bu durumu gösterir. İK kontrolü için 1 dk bir varsayım; ölçülen süreyle güncellenmeli.

## Alternatif önerilen süreç hesabı (örnek varsayımla)

- **Sorunsuz 1.040 başvuru:** Yapay zekâ taslağı, dayandığı kayıtlarla İK'ya gelir. İK yalnız kontrol eder ve gerekirse düzeltir.
  Varsayım: kontrol 2 dk + düzeltme ortalaması 0,5 dk = 2,5 dk → 2.600 dk.
- **Sorunlu 160 başvuru:** Sistem bunları e-posta üretmeden ayırır; elle hazırlanır ve ek incelemesi yapılır → 3.244 dk.
  - Sınav: 60 × 17 = 1.020 dk
  - Video: 36 × 20 = 720 dk
  - Grup: 32 × 24 = 768 dk
  - İngilizce görüşme: 20 × 20 = 400 dk
  - İK ve birim: 12 × 28 = 336 dk
- **Toplam:** 5.844 dk = **97,4 saat → 16,2 iş günü; kapasiteye sığar**.

## Duyarlılık: taslak başına İK süresi

| dk / taslak | 1 | 2 | 2,5 | 3 | 3,5 | **3,8** | 4 | 5 | 6 | 8 |
|---|---|---|---|---|---|---|---|---|---|---|
| Dönüş (iş günü) | 11,9 | 14,8 | 16,2 | 17,7 | 19,1 | **20,0** | 20,6 | 23,5 | 26,3 | 32,1 |

Eşik: (7.200 − 3.244) ÷ 1.040 ≈ **3,8 dk**. Taslak başına İK süresi bunu aşarsa önerilen süreç de 20 iş gününe sığmaz.
Daha ayrıntılı e-posta, kontrol süresini uzatır; bu yüzden ayrıntı kararı (A, B, E) bu eşikle birlikte savunulmalı.

## Ölçüm protokolü (madde 04 bunu istiyor)

1. İki ekip üyesi İK rolüne geçer. Her biri 10 taslak kontrol eder: 4 sınav, 2 video, 2 grup, 1 İngilizce, 1 kontenjan.
2. Kronometre detay ekranının açılmasıyla başlar, onay ya da düzeltmenin kaydıyla biter.
3. Her taslak için süre (dk), düzeltme yapıldı mı ve ne düzeltildiği not edilir.
4. Ortalama ve dağılım hesaplanır. Ölçülen değer "ölçüm", vakadan alınan süreler "veri", kalanlar "varsayım"
   olarak ayrı sütunlarda gösterilir.
5. Ölçülen ortalama yukarıdaki 2,5 dk'nın yerine konur; tablo ve sunumun 11. slaytı güncellenir.

Zaman tasarrufu tek başına aday memnuniyetinin arttığını göstermez; memnuniyet verisi yok.
