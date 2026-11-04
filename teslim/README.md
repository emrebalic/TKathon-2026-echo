# Teslim klasörü

Son teslim **16.45**, TKDrive'daki takım klasörüne. Sunumlar 17.00'de başlar.

| # | Teslim | Biçim | Sorumlu dal | Durum |
|---|---|---|---|---|
| 01 | Bir sayfalık çözüm özeti: sorun ve kanıt, A–G kararları ve elenen seçenekler, yapay zekâ kullanımı, iş yükü sonucu | .docx (`Cozum_Ozeti_Sablonu.docx`) | `ideathon` | ☐ |
| 02 | Çalışan MVP + kısa çalıştırma notu; API anahtarı (kullanılıyorsa), yapay zekâya verilen girdiler ve ham yanıtlar (`store/ai_kayitlari.jsonl`), İK düzeltmeleri ayrıca | .zip ya da herkese açık GitHub linki içeren .txt | `backend`, `ai`, `ui` | ☐ |
| 03 | Hesap ve test dosyası: iş yükü hesabı (ölçüm ile tahmin ayrı) ve üç testin ekran görüntülü sonucu | Excel ya da Word | `sunum`, `ideathon` | ☐ |
| 04 | Sunum (şablonun dört jüri slaytı + İK listesi) ve en fazla 90 sn video | .pptx + video | `sunum` | ☐ |
| 05 | Ek görevler (isteğe bağlı): her görev ayrı dosya, ekran görüntüleriyle, adında görev numarası (ör. `Ek_Gorev_8`) | ayrı dosyalar | `sunum` | ☐ |

İkiden fazla ek görev yüklenirse değerlendirilecek ikisi çözüm özetinde yazılır.

## Çözüm özeti şablonunun bölümleri

`Cozum_Ozeti_Sablonu.docx`: 01 Sorun ve kanıt (bulgu / varsayım / en büyük risk) · 02 A–G tablosu (karar ve veri
gerekçesi, elenen seçenek, örnek kayıt) · 03 Yapay zekâ (girdi, istek, kontrol, yakalanan hata) · 04 İş yükü
(elle / önerilen / hassasiyet; ölçülenler ve varsayılanlar) · seçilen ek görevler. Son sayfadaki ekip kontrol listesi
teslimden önce silinmeli.

## Teslimden önce

- [ ] Kırmızı çizgi taraması: karar değişmiyor, başka başvuru bilgisi yok, kurum içi not yok, kayıtta olmayan iddia yok, kontenjanda yetersizlik imâsı yok, vaat yok, onaysız gönderim yok
- [ ] "Memnuniyet arttı" gibi ölçülmemiş bir etki sonuç olarak yazılmadı
- [ ] İş yükü 1.200 başvuru için hesaplandı; kontrol süresi gerçekten ölçüldü (kaç e-posta, ortalama kaç dk)
- [ ] MVP zip'i `.venv` ve `data/raw` olmadan, README'deki adımlarla açılıp çalıştırıldı
- [ ] API anahtarı yalnız teslim paketinde; GitHub'da değil
