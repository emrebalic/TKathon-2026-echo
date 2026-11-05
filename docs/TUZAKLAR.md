# Veri tuzakları

120 başvuruluk ham dosya (depoda yok; `data/test/` bunun alt kümesi) üzerinde kural taraması ve keşifsel analizle bulunan tuzaklar. Etkilenen sayıları bu dosyadan
hesaplandı; yeni bir dosyada değişebilir. Grafikli rapor: https://claude.ai/artifact/A8Nvwk6ZSrNjmFQzZKDYi6

Seviye: **Kritik** bir kırmızı çizgiye doğrudan yol açar; **Yüksek** puan kaybettirir; **Dikkat** sessiz hataya yol açabilir.

## Kayıt

| Kod | Seviye | Tuzak | Neden tuzak? | Örnek | Etkilenen | MVP kuralı |
|---|---|---|---|---|---|---|
| T01 | Kritik | Aynı görevde çelişen iki gözlem | Aynı görüşme/görev ID’sinde iki değerlendirici farklı sonuç yazmış; ortak not girilmemiş. İK notu EVET olsa bile çelişki çözülmüş sayılmaz. | `AS-003-03 ↔ AS-003-04` | 4 | Karar aşamasında aynı etkinlik_id için birden fazla değerlendirici satırı varsa İK’ya ayır. |
| T02 | Kritik | Dayanağı sonradan düzeltilmiş karar | Düzeltme kayıtları karardan 19–20 saat sonra girilmiş; eski “eksiklik” gözlemi geçersiz, karar ve İK notu güncellenmemiş. | `AS-005-06 → AS-005-07` | 5 | Karar ya da İK dayanağındaki bir ID başka bir satırın “düzelttiği kayıt” alanında geçiyorsa İK’ya ayır. |
| T03 | Kritik | Yeniden puanlanınca geçen sınav | İngilizce bölümü yanlış cevap anahtarıyla puanlanmış; düzeltmede 6/15 doğru 11/15 olmuş ve sonuç GEÇTİ’ye dönmüş. Ret kaydı hâlâ duruyor. | `SN-033-EN → SN-033-EN-D1` | 1 | Sınav düzeltmesi bölüm sonucunu değiştiriyorsa e-posta üretme; kararı da kendin değiştirme. |
| T04 | Yüksek | Öznel aşamada İK notu yok | Video, grup ve İK/birim retlerinde son İK gerekçesi zorunlu; bu başvuruların İK notu satırı hiç yok. | `BSV-040, BSV-057, BSV-081` | 3 | Öznel aşama retlerinde Başvuru ID ile İK notu bulunamazsa İK’ya ayır. |

## Kod

| Kod | Seviye | Tuzak | Neden tuzak? | Örnek | Etkilenen | MVP kuralı |
|---|---|---|---|---|---|---|
| T05 | Yüksek | BELIRTILMEDI ile UYGULANMAZ aynı değil | Gerekçe kodu BELIRTILMEDI: neden yazılmamış. UYGULANMAZ ise yalnız kabul kayıtlarında, “aranmaz” demek. | `IK-044` | 3 | Gerekçe kodu yalnız GEREKLILIK_KARSILANMADI ya da KONTENJAN_KISITI ise taslak üret. |
| T06 | Yüksek | Paylaşım teyidi yazılmamış | Teyit BELIRTILMEDI: izin var da denemez, yok da. Gerekçe dolu olsa bile paylaşım kapsamı belirsiz. | `IK-047` | 6 | Öznel aşamada teyit EVET değilse İK’ya ayır. |
| T07 | Kritik | Paylaşım onaylanmamış (HAYIR) | Bu başvurularda dayanak gözlem de KURUM_ICI. Ayrıntılı gerekçe adaya aktarılamaz. | `IK-007 + AS-007-03` | 4 | Teyit HAYIR ise e-posta üretme; İK paylaşım kapsamını belirlesin. |
| T08 | Kritik | EVET teyidi güvenli demek değil | Teyit EVET olan bazı başvurular yine de çelişki, düzeltme ya da kurum içi dayanak taşıyor. EVET, KURUM_ICI kısıtını ve çelişkiyi kaldırmaz. | `BSV-003, BSV-005, BSV-006, BSV-045 …` | 9 | Teyidi diğer kontrollerden sonra değerlendir; EVET tek başına onay değildir. |

## İçerik

| Kod | Seviye | Tuzak | Neden tuzak? | Örnek | Etkilenen | MVP kuralı |
|---|---|---|---|---|---|---|
| T09 | Kritik | Kurum içi kişilik yargısı | Dayanak gözlem “içine kapanık, liderlik kişiliği zayıf” diyor; somut örnek yok ve kayıt KURUM_ICI. İK notu yine de EVET. | `AS-006-06` | 1 | KURUM_ICI dayanak ya da kişilik ifadesi varsa İK’ya ayır; kişilik yargısını asla aktarma. |
| T10 | Kritik | Kontenjan reddi yetersizlik değildir | Aday tüm aşamaları geçmiş; birimin 4 kişilik kontenjanı 0’a indirilmiş. Gelişim önerisi, gelecek dönem vaadi ve yetersizlik imasının hiçbiri olmamalı. | `AS-008-07, IK-008` | 4 | Kontenjan şablonu ayrı tutulsun; çıktıda “eksik, geliştir, yetersiz” gibi kelimeler aranıp engellensin. |
| T11 | Yüksek | İç kodlar taslağa sızabilir | Taslağa uygun başvuruların bazılarında kurum içi not var: T101-K-036, T101-T8, GRP-B, KP-2026-03-25-01 gibi kodlar. | `BSV-008, BSV-036, BSV-052, BSV-056 …` | 7 | Kurum içi not alanını modele hiç verme; çıktıda iç kod kalıplarını tara. |
| T12 | Dikkat | İki sınav bölümünden de kalanlar | Kararın iki dayanağı var; e-posta yalnız birini anlatırsa eksik kalır. | `BSV-014: SN-014-GY;SN-014-EN` | 8 | Dayanak listesindeki her sınav bölümünü e-postada ayrı göster. |
| T15 | Yüksek | Görüşme puanı dil seviyesi değildir | Puan yalnız o görüşmeye ait. CEFR, “B2” ya da genel İngilizce düzeyi yazmak kayıtta olmayan iddia olur. | `DL-004` | 12 | Çıktıda A1–C2, CEFR, “seviye” gibi ifadeleri engelle. |
| T16 | Yüksek | Envanter ret gerekçesi olamaz | Kişilik envanterinde yalnız “tamamlandı” bilgisi var ve kayıtlar KURUM_ICI. | `AS-005-05` | 38 | Envanter kayıtlarını modele verme. |
| T17 | Kritik | Geçilen aşama ret nedeni değildir | Olumsuz başvuruların geçilmiş aşamalarındaki gözlemlerin hepsi beklentiyi karşılayan türden. Model bunları ret nedeni gibi yazarsa uydurmuş olur. | `BSV-003 video gözlemi` | 64 | Modele yalnız karar aşamasının kayıtlarını ver. |

## Eşik

| Kod | Seviye | Tuzak | Neden tuzak? | Örnek | Etkilenen | MVP kuralı |
|---|---|---|---|---|---|---|
| T13 | Dikkat | Baraja eşit puan geçer | Geçme koşulu “en az”: tam baraj puanı alan satırlar GEÇTİ, bir eksik alan GEÇEMEDİ. “>” ile hesaplamak bu satırları ters çevirir. | `SN-006-EN: 10/15 GEÇTİ` | 29 | Sonucu yeniden hesaplama; kayıtlı sonuç kodunu kullan, yalnız tutarlılık için ≥ ile kontrol et. |
| T14 | Yüksek | İki ayrı İngilizce barajı | Sınavın İngilizce bölümü 15 soruda 10 doğru, sözlü görüşme 20 puanda 12 istiyor. Görüşmede 10–11 alan adaylar kaldı. | `DL-068: 10/20 GEÇEMEDİ` | 3 | Sınav ve görüşme kayıtlarını ayrı tablolardan, ayrı barajlarla anlat. |

## Kapsam

| Kod | Seviye | Tuzak | Neden tuzak? | Örnek | Etkilenen | MVP kuralı |
|---|---|---|---|---|---|---|
| T18 | Yüksek | Kabul ve devam edenlere ret e-postası yok | DEVAM_EDIYOR başvuruların her birinde bir DEGERLENDIRILIYOR kaydı var. TAMAMLANDI da geçti demek değil. | `BSV-011 (VIDEO, değerlendiriliyor)` | 40 | Yalnız karar kodu OLUMSUZ olan başvurular işlensin; tanımsız ya da boş kod İK’ya. |

## Teknik

| Kod | Seviye | Tuzak | Neden tuzak? | Örnek | Etkilenen | MVP kuralı |
|---|---|---|---|---|---|---|
| T19 | Yüksek | Sütun adında tipografik kesme işareti | “İK’nın kaydettiği başvuru sonucu (kod)” başlığındaki işaret düz tırnak (') değil, U+2019 (’). Koda elle yazılan sütun adı eşleşmez. | `Başvuru Kararları F sütunu` | 5 | Sütunları Alan Sözlüğü’ndeki teknik adlara eşle ya da adları normalize et. |
| T20 | Dikkat | İK notlarındaki formül sütunları | İK Değerlendirme Notları M–N sütunları Excel formülü. Dosya bir kütüphaneyle değiştirilirse önbellekteki açıklama eski ya da boş kalabilir. | `IK-002 M2/N2` | 122 | Kod anlamlarını formül sütunlarından değil, Kod Açıklamaları’ndan üret. |
| T21 | Dikkat | Birden çok dayanak tek hücrede | Dayanak ID’leri noktalı virgülle ayrılmış. Tek ID varsayan bir birleştirme kayıt kaçırır. | `AS-003-03;AS-003-04` | 16 | Dayanak alanını “;” ile bölüp her ID’yi ayrı doğrula. |
| T22 | Dikkat | Boş hücre her zaman hata değil | Kabul ve devam kayıtlarında karar dayanağı boş; kontenjan İK notlarında beceri kodu boş. Bunlar eksik veri sayılmamalı. | `BSV-009 dayanak boş` | 40 | Boşluğu alanına göre yorumla (Alan Sözlüğü); karar kodu boşsa İK’ya ayır. |

## Ölçek

| Kod | Seviye | Tuzak | Neden tuzak? | Örnek | Etkilenen | MVP kuralı |
|---|---|---|---|---|---|---|
| T23 | Yüksek | Örnekteki sorun oranı dönemi temsil etmez | Dosyadaki sorunlu kayıtlar bilerek artırılmış: örnekte olumsuzların yaklaşık üçte biri İK’ya gidiyor, 1.200’lük dönemde 160/1.200. | `120 ↔ 1.200` | 23 | İş yükünü 120 kayıttan ölçekleme; dönem verisini, kendi ölçtüğün başvuru başı süreyle kullan. |
