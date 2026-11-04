# Ek görevler

Özet; asıl metin `materials/04_Ek_Gorevler.pdf`, örnek veriler `data/raw/06_Ek_Gorev_Ornekleri.xlsx`.

## Kurallar

- Ana vakayı bitirmek ön koşul değil. En fazla **iki** görev seçilir; her biri 5 puan, toplam en fazla 10 ek puan.
- Her görev ayrı dosya olarak, ekran görüntüleriyle yüklenir; dosya adında görev numarası olur (ör. `Ek_Gorev_8`).
  İkiden fazla yüklenirse değerlendirilecek iki görev çözüm özetinde yazılır.
- Çıktı metin, tablo, ekran çizimi ya da çalışan özellik olabilir. Ana vakada zaten gösterilen iş, değişmeden tekrar
  sunulursa puan getirmez; aynı çıktı iki görevde tekrar puanlanmaz.
- 1, 6, 7, 8 ve 9. görevlerin örnek verisi var. `EG` ile başlayan kimlikler ana verideki 120 başvuruyla birleştirilmez;
  aynı adayın farklı başvuruları `aday_id` ve `basvuru_id` ile ayrılır. Gerçek e-posta gönderilmez.

## Görevler

| # | Senaryo | İstenen | Örnek veri |
|---|---|---|---|
| 1 | "Diğer başvurum da mı reddedildi?" Adayın bir başvurusu olumsuz, diğeri sürüyor | Karışıklığı önleyen geri bildirim; iki başvurunun ayrı göründüğü basit ekran çizimi ve örnek e-posta | Başvurular: EG-A001 → EG-B001 (OLUMSUZ, Veri Analitiği) ve EG-B002 (DEVAM, Süreç Geliştirme); Gelen Mesajlar EG-G007 |
| 2 | "Görüşmede anlattıklarım dikkate alınmamış." Notlar ne doğruluyor ne yalanlıyor | Adaya ilk yanıt + görüşmeciye bilgi talebi; konuyu kimin, nasıl sonuçlandıracağı. İtirazı dinleyen ama sonucu peşinen değiştirmeyen yaklaşım | (Ana senaryo; EG-B003 / EG-N001 / EG-G004 uygun) |
| 3 | "Üç haftadır haber bekliyorum." Süreç sürüyor | Ara bilgilendirme: hangi durumda yapılır, ne söylenebilir, sonraki iletişim nasıl izlenir. Belli olmayan sonuç ya da tarih için söz verilmez | (EG-B005: 21 gün; EG-G006) |
| 4 | "Geri bildirimimi İngilizce alabilir miyim?" | Seçilen geri bildirimlerin yapay zekâyla İngilizce sürümü; başvuru bilgisi, sayılar, gerekçe ve üslubun korunduğunun kontrolü; anlam kaymasını fark edip düzeltme. Çalışan uygulamada dil seçeneği olabilir | — |
| 5 | "Başka staj buldum, başvurumu geri çekiyorum." Olumsuz taslak hazır, henüz gönderilmedi | Başvurunun ve bekleyen e-postanın ele alınışı; adaya yanıt; eski taslağın yanlışlıkla gönderilmesini önleme; değerlendirme kayıtları ile geri çekme talebinin ayrılması | — |
| 6 | "Yeni sınav şirketinin dosyası uymuyor." Sütun adları değişmiş (`basvuru_id` → "Başvuru Referansı" vb.) | Değişen sütunları mevcut alanlara eşleyen küçük çözüm; kullanıcı eşlemeyi seçebilir; eşlenemeyen alanlar açıkça gösterilir. Yalnız dosya okuma adımı | Sınav Dosyası: Başvuru Referansı, Katılımcı Kodu, Test Adı, Soru Adedi, Doğru, Hatalı, Yanıtsız, Eşik, Sınav Durumu, Oturum Etiketi (karşılığı yok). Eşik burada 9; ana veriyle kıyaslanmaz |
| 7 | "Toplantıda göstereceğiz; aday bilgileri görünmesin." | Ad, iletişim ve notlardaki kişi isimleri çıkarılmış inceleme kopyası; örnekler ayırt edilebilir ve gerekçe anlaşılır kalır; asıl kayıt değişmez | İnceleme Notları: EG-N001…N003 (aday adı, e-posta, notta geçen görüşmeci isimleri) |
| 8 | "Geri bildirimleri gönderdik, yanıtlar birikiyor." | Gelen yanıtları yapay zekâyla konularına ayıran özellik; işlem gereken ile yalnız bilgi içerenler ayrılır; anlaşılamayan yanıt belirtilir | Gelen Mesajlar EG-G001…G007: puan itirazı, yeniden başvuru, teşekkür, itiraz + yeni ilan, belirsiz ("Bu yüzden mi?"), bekleme, hangi başvuru sorusu. Bir mesajın birden çok konusu olabilir |
| 9 | "Gönderildi görünüyor ama ulaşmamış." | Bekleyen, iletilen ve iletilemeyen e-postaların takibi; ne zaman yeniden denenir, ne zaman İK başka yoldan ulaşır. Küçük tablo ya da ekran yeterli | İletim Kayıtları EG-I001…I009 (KUYRUKTA, ILETILDI, GECICI_HATA, KALICI_HATA); son durum olay sırasıyla belirlenir |
| 10 | "Yeni kontenjan açıldı, bazı adaylarla yeniden görüşeceğiz." | Yeni davet ve önceki iletişimle birlikte gösterimi; neden tekrar iletişime geçildiği anlaşılır; davet, kabul ya da teklif gibi sunulmaz. Adayları İK seçer, yapay zekâ değil | (EG-B004 / EG-N003 uygun) |

## Önerimiz

- **Görev 6 + Görev 8.** İkisi de örnek veriyle çalışan bir özellik olarak gösterilebilir.
  - 6, mevcut `core/schema.py` eşleştiricisinin üstüne kullanıcı seçimli bir eşleme ekranıdır.
  - 8, Muse ile JSON sınıflandırmadır; belirsiz mesaj (EG-G005) ve çok konulu mesaj (EG-G004) iyi demo olur.
- **Daha az kodlu alternatif: Görev 1 + Görev 4.** 1 bir ekran çizimi ve e-postadan ibaret. 4, kontrol katmanını
  çeviride de kullanmayı gerektirir.
