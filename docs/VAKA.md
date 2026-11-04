# Vaka: yapay zekâ destekli geri bildirim

Özet; asıl metin `materials/01_Vaka_ve_Veri_Rehberi.pdf`. Tema: İnsan Kaynakları Başkanlığı özelinde yapay zekâ çözümleri.

## Sorun

Junior Wings başvurusu olumsuz biten adaylar standart bir e-posta alıyor ve neden elendiklerini öğrenemiyor.
Açıklama talepleri İK'nın iş yükünü artırıyor; şikâyetler güveni zedeliyor. İK daha hızlı dönmek istiyor, ama
ayrıntılı geri bildirim kontrol ve düzeltme süresini uzatıyor. Adaya neyin, ne zaman ve ne ayrıntıda
anlatılacağına takım karar verir; kararlar ve paylaşım kuralları sabittir. Her e-posta gönderilmeden önce İK
onayından geçer.

Örnek dosyada 120 kurgusal başvuru var: 80 olumsuz, 20 kabul, 20 değerlendirmesi süren. Bazı olumsuzlar kontenjan nedenlidir.

## Junior Wings süreci

| Sıra | Kod | Aşama | Veride ne var |
|---|---|---|---|
| 1 | SINAV | Genel Yetenek ve İngilizce Testi | Bölüm başına soru, doğru, yanlış, boş, baraj, sonuç (GY 25 soru / 16 baraj, İng 15 / 10) |
| 2 | VIDEO | Video Mülakat | Değerlendirici gözlemi + İK notu |
| 3 | GRUP | Grup Çalışması | Değerlendirici gözlemi + İK notu |
| 4 | INGILIZCE | Sözlü İngilizce Mülakatı | Puan (20 üzerinden, baraj 12), sonuç, gözlem; sınavın İngilizce bölümünden ayrı |
| 5 | ENVANTER | Kişilik Envanteri | Yalnız tamamlanma kaydı; kişilik puanı yok |
| 6 | IK_TEKNIK | İK ve Birim Mülakatı | İK ve iş birimi notları (bireysel iş uygulamaları bu aşamada) |
| 7 | TEKLIF | İş Teklifi | Süreç kaydı |
| 8 | BELGE | Belge ve İşe Giriş | Süreç kaydı |

## Puanlama (toplam 100 + en fazla 10 ek)

| Madde | Puan | İstenen |
|---|---|---|
| 01 Sorunu anlama | 15 | Aday ve İK sorununu veriden örneklerle incele; bulguyu varsayımdan ayır; en büyük riski yaz |
| 02 İletişim kararları | 25 | A–G yedi soruya karar; her biri veriye dayalı, düşünülen başka seçenek ve neden elendiği |
| 03 Yapay zekâyla yazdırma ve kontrol | 15 | Modele ne verildiği, ne istendiği; çıktıların okunması (neden anlaşılıyor mu, kayıtta olmayan var mı); yakalanan hata ve düzeltmesi |
| 04 İK işi ve süre | 15 | Kısa kontrol / ayrıntılı inceleme ayrımı ve gerekçesi; bir e-postanın kontrol süresinin ölçümü; elle ve önerilen sürecin aynı sayıda başvuruda karşılaştırması (okuma, yazma, kontrol, düzeltme); bir süre tahmini değiştirilerek dönüş süresine etkisi |
| 05 MVP kalitesi | 10 | Excel'deki bütün başvuruları okuyup sayar, seçilen olumsuz başvuru için yapay zekâ taslağını gösterir; kolay ve anlaşılır |
| 06 Hata kontrolü | 10 | Eksik, çelişkili, paylaşım izni açık olmayan, dayanağı sonradan düzeltilmiş kayıtlar İK'ya ayrılır; taslağın dayandığı kayıtlar gösterilir |
| 07 Değişim | 10 | Yeni dosyada sayılar güncellenir; veri değişince eski yanıt ve İK onayı düşer; üç testin sonucu |
| Ek görevler | +10 | En fazla iki görev, her biri 5 puan (`docs/EK_GOREVLER.md`) |

Araç adı ya da kod miktarı tek başına puan getirmez.

### A–G iletişim soruları

- **A** Sınavda kalan adaya puan ve baraj söylenecek mi; bölüm bölüm mü, toplam mı?
- **B** Video, grup ve mülakat notları nasıl aktarılacak: özetleyerek mi, ölçüt ölçüt mü, hiç mi?
- **C** Kontenjan nedeniyle olumsuz sonuçlanan adaya durum nasıl anlatılacak?
- **D** Gelişim önerisi verilecek mi; verilecekse hangi kayda dayanarak?
- **E** Dil ve üslup resmî mi, sıcak mı; e-posta ne uzunlukta?
- **F** E-posta ne zaman gidecek: karardan hemen sonra mı, aşama sonunda toplu mu?
- **G** Aday itiraz eder ya da soru sorarsa ne olacak?

Taslak kararlar: `docs/ILETISIM_KARARLARI.md`.

## Çalışan çözümün şartları

1. Arayüzden yüklenen dosyadaki bütün başvuruları okur; kayıtlı sonuca göre olumsuz, kabul ve süren başvuruları
   otomatik ayırıp sayar. Aynı yapıda 40, 60 ya da 1.000 başvuruluk dosyayla da çalışır. Sayı, ID ve sonuç koda
   sabit yazılmaz.
2. Seçilen olumsuz başvuru için İK onayına giden en az bir e-posta taslağı üretir. Taslak yapay zekâ ile
   üretilir (elle yazılan metin sayılmaz). Uygulama yanıtı otomatik işler; e-postayı, dayandığı kayıtları ve
   inceleme gerekip gerekmediğini gösterir. Yanıtın doğru başvuruya ait, eksiksiz ve kayıtlarla uyumlu olduğu
   kontrol edilir. İK'ya ayrılan başvuruda e-posta üretilmez, inceleme nedeni gösterilir.
3. Toplam başvuru ve sonuçlara göre dağılım gösterilir. Olumsuzlarda taslağı hazırlanan, ek inceleme bekleyen ve
   henüz işlenmeyen ayrı belirtilir. İK düzeltmeleri kaydedilir. Kabul ve sürenlere olumsuz e-posta üretilmez.
   Sunumda bütün e-postaları üretmek gerekmez.
4. Üç test: **olağan başvuru** (sorunsuz bir olumsuzun taslağı, dayanağı ve İK onayı), **yeni dosya** (farklı kayıt
   sayılı aynı yapıda dosya; listeler ve sayılar güncellenir), **değişen veri** (bir başvurunun bilgisi değişir,
   yapay zekâdan güncel yanıt alınır). Veri değişirse eski yanıt ve İK onayı, e-posta değişirse İK onayı geçersiz
   olur. Beklenen ve gerçekleşen sonuç karşılaştırılır.

Diğer koşullar: Model eğitimi, kullanıcı hesabı ve kurumsal entegrasyon beklenmez. Ayrıntılı sürüm ekranı gerekmez;
ilk taslak, İK düzeltmesi ve onayın saklanması yeterli. Model API ile anlık çağrılabilir **ya da** yanıtlar dışarıda
üretilip Excel gibi bir dosyayla yüklenebilir; iki yol eşit değerlendirilir. Yüklenen yanıtlar Başvuru ID ile
eşleşir, eşleşmeyen yanıt onaya açılmaz. Kayıtlı yanıtlar ile yeni üretilenler ayırt edilir.

## Veri kuralları

- Sonuç alanı: Başvuru Kararları'ndaki "İK'nın kaydettiği başvuru sonucu (kod)" (OLUMSUZ / KABUL / DEVAM_EDIYOR).
  Eksik ya da tanımsızsa veri sorunu olarak İK'ya ayrılır.
- Doğru + yanlış + boş = soru sayısı olmalı. Sınav aşamasında ayrıca İK notu gerekmez.
- Video, grup ve İK/teknik değerlendirmeleri İK gerekçesiyle birlikte ele alınır; kontenjan kararında ilgili
  idari kayıt kullanılır. Envanterde yalnız tamamlanma bilgisi var.
- Olumsuz geri bildirim yalnız OLUMSUZ kararlılara. Geçilen aşama ret gerekçesi olmaz; katılınmayan aşamada
  başarısızlık varsayılmaz.
- Gerekçe eksik, kayıtlar çelişkili, paylaşım izni açık değil ya da bir düzeltme kararın dayanağını değiştiriyorsa
  aday e-postası üretilmez, İK incelemesi istenir. Düzeltilmiş kaydın güncel hâli kullanılır; düzeltme kararı
  kendiliğinden değiştirmez.
- E-posta nedeni açık ve saygılı anlatır. Kayıtta olmayan dil seviyesi, kişilik özelliği ya da başarı vaadi
  eklenmez; aday başkalarıyla kıyaslanmaz. Gelişim önerisi ilgili gözleme dayanır; her e-postada şart değildir.

Ayrıntılı paylaşım kuralları Excel'deki "Paylaşım Kuralları" sayfasında (PK-01…PK-06). Veride bulunan tuzaklar:
`docs/TUZAKLAR.md`.

## Kırmızı çizgiler

Kararı değiştirmek · başka başvurunun bilgisini kullanmak · kurum içi bilgiyi paylaşmak · kayıtta olmayan iddia
eklemek · kontenjan adayına yetersizlik ima etmek · başarı veya işe alım vaadi vermek · e-postayı İK onayı olmadan
göndermek.

## Teslim ve sunum

Teslimler ve kontrol listesi `teslim/README.md`'de; sunum şablonunun yapısı `docs/SUNUM.md`'de.

- **Son teslim:** 16.45, TKDrive'daki takım klasörüne (bağlantı ve şifre e-postayla geldi).
- **Sunum:** 17.00'de başlar; takım başına 5 dk sunum + 5 dk jüri sorusu. Video ya da canlı demo bu 5 dakikaya dahil.
- Sunum, İK'ya ayrılan başvuruların listelendiği son sayfayla biter.
- Kural değişikliği ya da ek açıklama olursa bütün takımlara aynı anda duyurulur.
