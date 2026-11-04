# Görev: TKATHON 2026 — Junior Wings yapay zekâ destekli geri bildirim MVP'si

Önce **plan modunda** çalış: dosyaları oku, planı bana göster, onayımdan sonra uygula. Teslim saati bugün 16:45; kapsamı buna göre küçük ve sağlam tut. Gösterişli değil, **doğru ve test edilebilir** bir MVP istiyoruz.

## Bağlam
- Vaka: `01_Vaka_ve_Veri_Rehberi.pdf` (özellikle "Çalışan çözüm" ve "Verileri kullanırken" bölümleri). Bunları kaynak kabul et; benim özetimle çelişirse PDF geçerlidir.
- Veri: `02_Veriler.xlsx`. Ek görev örnekleri: `06_Ek_Gorev_Ornekleri.xlsx` (şimdilik kapsam dışı).
- Takımın kararları: `Cozum_Ozeti_Sablonu.docx` (01 bulgular, 02 A–G kararları). Prompt ve kurallar bu kararlara uymalı.
- **Teknoloji:** Ayrı bir frontend ve backend istiyoruz.
  - **Backend:** Python + **FastAPI**, paket yönetimi **uv**. Veri okuma, ön kontrol kuralları, prompt oluşturma, son kontrol, depolama ve hash mantığının **tamamı backend'de** olacak. Ben Python biliyorum; kuralların doğruluğunu buradan kontrol edeceğim. Frontend iş kuralı içermeyecek, yalnız gösterecek.
  - **Frontend:** **React + Vite + TypeScript**, stil için Tailwind. Ekranlar sade, anlaşılır ve Türkçe olsun; jüri "kolay kullanılmalı ve anlaşılır olmalı" diye puanlıyor.
  - **Depolama:** SQLite (backend içinde). Kullanıcı hesabı yok.
  - **Çalıştırma:** Tek komutla iki tarafı birden başlat (ör. kökte `npm run dev` ya da bir `Makefile`/betik). Frontend backend'e Vite proxy ile bağlanır; CORS sorunu çıkmasın. Windows ve macOS'ta çalışmalı.
  - Planda bu yığın zamana yetmeyecek gibi görünürse bunu açıkça söyle ve gerekçesiyle daha basit bir alternatif öner (ör. FastAPI'nin kendisinin sunduğu tek sayfalık HTML). Kendi başına yığın değiştirme.
- Yapay zekâ: Anthropic Claude API (Python `anthropic` SDK, backend'de). Anahtar `.env` içindeki `ANTHROPIC_API_KEY`'den okunur, koda yazılmaz. Model adını tek bir sabitte tut. API çalışmazsa ikinci yol: yanıtları Excel/JSON ile yükleme (Başvuru ID ile eşleşir, eşleşmeyen onaya açılmaz). Vaka iki yolu eşit sayıyor.

## Veri yapısı (02_Veriler.xlsx — başlıklar 1. satırda)
- **Başvuru Kararları:** Kayıt ID, Başvuru ID, Kayıt tarihi, Aşama kodu, Kaydı oluşturan görevli, **"İK’nın kaydettiği başvuru sonucu (kod)"** (OLUMSUZ / KABUL / DEVAM_EDIYOR), "Kararın dayandığı kayıt ID’leri" (`;` ile ayrılmış), açıklama.
- **Başvuru Listesi:** Başvuru ID, Anonim aday ID, İlan ID, Başvuru tarihi.
- **Aşama Kayıtları:** Kayıt ID, Başvuru ID, Görüşme/görev ID, tarih, Aşama kodu, tamamlanma durumu, görevli, Beceri kodu, gözlem/süreç notu, **paylaşım durumu (PAYLASILABILIR / KURUM_ICI)**, **"Bu kaydın düzelttiği eski kayıt ID"**, düzeltme açıklaması.
- **Sınav Sonuçları:** bölüm (GENEL_YETENEK / INGILIZCE), soru/doğru/yanlış/boş, geçme barajı, sonuç (GECTI / GECEMEDI), paylaşım, düzeltilen eski kayıt ID, düzeltme açıklaması. Doğru+yanlış+boş = soru sayısı olmalı.
- **İngilizce Görüşme Sonuçları:** puan, en yüksek puan, baraj, sonuç, gözlem, paylaşım.
- **İK Değerlendirme Notları:** ret gerekçesi türü (GEREKLILIK_KARSILANMADI / KONTENJAN_KISITI / BELIRTILMEDI / UYGULANMAZ), ret gerekçesi, beceri kodu, gerekçenin dayandığı kayıt ID’leri, **paylaşım teyidi (EVET / HAYIR / BELIRTILMEDI / UYGULANMAZ)**, paylaşılabilir bilgiye ilişkin açıklama, **"Kurum içi not — dış paylaşıma kapalı"**.
- **Program Aşamaları, Beceri Tanımları, Paylaşım Kuralları (PK-01…), Kod Açıklamaları (başlık 5. satırda), Alan Sözlüğü, İş Yükü Verileri, Planlama Verileri.**

Sütunları **başlık adıyla** oku (pozisyonla değil), Türkçe karakter ve tırnak (’) farklarına dayanıklı ol. Başvuru ID, sayı ve sonuçlar **koda sabit yazılmayacak**; aynı yapıda 40, 60 ve 1.000 kayıtlı dosyayla çalışmalı.

## İşlevler

### 1. Yükleme ve sayım
- Arayüzden Excel yüklenir. Toplam başvuru sayısı ve OLUMSUZ / KABUL / DEVAM_EDIYOR dağılımı gösterilir.
- Sonuç kodu eksik ya da tanınmıyorsa → "veri sorunu" olarak İK incelemesine ayrılır.
- OLUMSUZ başvurular üç gruba ayrılır ve ayrı sayılır: **taslağı hazırlanan**, **İK incelemesine ayrılan** (nedeniyle birlikte), **henüz işlenmeyen**.
- KABUL ve DEVAM_EDIYOR için olumsuz e-posta **asla** üretilmez (buton bile görünmesin).

### 2. Ön kontrol — taslaktan önce (deterministik kod, yapay zekâ değil)
Bir OLUMSUZ başvuru aşağıdakilerden birine uyuyorsa **taslak üretilmez**, İK listesine okunur bir nedenle düşer:
1. Kararın dayandığı kayıt ID’lerinden biri bulunamıyor veya başka başvuruya ait.
2. Dayanak kayıt veya onun gerekçe kayıtlarından biri **düzeltilmiş** (başka bir kaydın "düzelttiği eski kayıt ID" alanında geçiyor). Örnek: BSV-033'ün İngilizce sonucu düzeltmeyle GECTI oldu ama karar olumsuz; BSV-005, 045, 059, 077'de gözlem düzeltildi, gerekçe güncellenmedi. Düzeltilmiş kaydın güncel hâli kullanılır ama karar kendiliğinden değişmez.
3. Sınav reti: dayanak bölüm GECEMEDI değil, ya da doğru+yanlış+boş ≠ soru sayısı.
4. İngilizce görüşme reti: kayıtlı sonuç GECEMEDI değil veya gözlem yok.
5. VIDEO / GRUP / IK_TEKNIK reti: İK notu yok; gerekçe türü BELIRTILMEDI; paylaşım teyidi EVET değil; **veya teyit EVET olsa bile gerekçenin dayandığı kayıtlardan biri KURUM_ICI** (örnek: BSV-006 — teyit EVET ama dayanak kurum içi bir kişilik yorumu).
6. Kontenjan reti: ilgili idari kayıt veya İK teyidi eksik.
7. Gözlemlerle gerekçe çelişiyor (ör. dayanak aşama notu olumlu, gerekçe olumsuz). Bunu basit kurallarla yakalayabildiğin kadar yakala; yakalayamadığını planda dürüstçe belirt.

Kontrol için: örnek dosyada en az şu başvuruların İK'ya düşmesini bekliyoruz: BSV-005, 006, 007, 033, 040, 044, 045, 047, 048, 057, 059, 061, 062, 064, 077, 079, 081, 083, 084. Bu **test için beklenen sonuçtur, koda yazılmaz**. Fark çıkarsa bana nedenini raporla.

### 3. Yapay zekâ taslağı (yalnız ön kontrolden geçen OLUMSUZ başvuru için)
**Modele giden girdi** (yalnız o başvurunun kayıtları):
- Sınav reti: kaldığı bölümün güncel soru/doğru/baraj bilgisi.
- İngilizce görüşme reti: puan, baraj, değerlendirici gözlemi.
- VIDEO / GRUP / IK_TEKNIK: PAYLASILABILIR gözlem + teyidi EVET olan İK gerekçesi + beceri tanımı.
- Kontenjan: İK'nın paylaşılabilir açıklaması + idari kayıt.
- **Asla gitmeyen:** "Kurum içi not" sütunu, KURUM_ICI kayıtlar, kişilik envanteri, başka başvurular, geçilen aşamaların sonuçları.

**System prompt** — aşamaya göre üç blok (sınav/dil, öznel aşama, kontenjan) + ortak kurallar. Takımın 02 kararları:
- A: Yalnız kalınan bölümün doğru sayısı ve barajı ("İngilizce bölümünde 15 sorunun 6'sına doğru yanıt verdiniz; geçme barajı 10 doğruydu"). Toplam puan verilmez.
- B: Güncel, paylaşılabilir ve İK gerekçesiyle tutarlı gözlem kısa özetlenir; ham not aktarılmaz.
- C: Kontenjan nedeni açıkça söylenir; yetersizlik ima edilmez; gelişim önerisi ve gelecek vaadi yok.
- D: Gelişim önerisi yalnız somut, paylaşılabilir bir gözleme dayanıyorsa, kısa. Zorunlu değil.
- E: Kurumsal ama empatik, açık; **80–120 kelime**.
- Ortak yasaklar: kararı değiştirmek veya sorgulamak; kayıtta olmayan iddia; dil seviyesi/CEFR çıkarımı; kişilik yorumu; başkalarıyla kıyas; başarı veya işe alım vaadi; kesin tarih sözü.
- G: E-posta sonunda adayın soru veya itirazını Başvuru ID ile iletebileceği belirtilir; sonuç sözü verilmez.

**Çıktı formatı (JSON):** `email_konu`, `email_metni`, `kullanilan_kayit_idleri` (liste), `emin_olunmayan_noktalar`.

### 4. Son kontrol — taslaktan sonra (kod)
- `kullanilan_kayit_idleri`'nin hepsi bu başvuruya ait ve modele verilenler içinde mi?
- Metindeki her sayı girdideki bir sayıyla eşleşiyor mu?
- Yasaklı ifade taraması: seviye/CEFR (A1–C2), kişilik sıfatları, "başka adaylar", vaat kalıpları ("ileride", "bir sonraki dönemde kabul"), kontenjan başvurusunda "eksik", "yetersiz", "geliştirmeniz".
- Kelime sayısı 80–120 aralığında mı?
- Sorun varsa taslak "İK dikkat" etiketiyle gösterilir, sorun listelenir. **Otomatik düzeltme yok**; İK düzenler veya yeniden üretir.

### 5. İK ekranı ve onay
- Seçilen başvuru için yan yana: e-posta taslağı, dayandığı kayıtlar (ID + içerik), ön ve son kontrol sonuçları.
- İK metni düzenleyip kaydedebilir. **İlk taslak, İK düzeltmesi ve onay ayrı saklanır** (SQLite ya da JSON dosyası yeterli; kullanıcı hesabı yok).
- "Gönder" butonu yok; yalnız **"İK onayla"**. Gerçek e-posta gönderimi yok.
- **Geçersiz kılma kuralı:** Her taslak, girdi kayıtlarının hash'iyle saklanır.
  - Yeni dosya yüklendiğinde girdi hash'i değiştiyse → eski taslak ve onay "geçersiz (veri değişti)" olur.
  - Onaydan sonra e-posta metni değişirse → onay düşer.
- Kayıtlı yanıtlar ile yeni üretilen yanıtlar ekranda ayırt edilir.

### 6. Kayıt ve teslim için dosyalar
- Modele giden her girdi ve ham yanıt `logs/` altına Başvuru ID + zaman damgasıyla JSON olarak yazılır (teslim şartı).
- İK düzeltmeleri ayrı bir dışa aktarımla (CSV/Excel) indirilebilir.
- İK'ya ayrılan başvuruların tam listesi (Başvuru, Aşama, Neden, Dayandığı kayıt) dışa aktarılabilir; sunumun son sayfasında kullanacağız.

### 7. (Zaman kalırsa) İş yükü sekmesi
İş Yükü Verileri ve Planlama Verileri'ni okuyup elle süreç için toplam süreyi ve dönüş süresini hesapla (beklenen: 15.552 dk ≈ 259,2 saat; 120 saat/20 gün ile ≈ 43,2 iş günü). Kullanıcı yeni süreç için okuma / kontrol / düzeltme dakikalarını girebilsin ve dönüş süresi yeniden hesaplansın.

## Testler (vaka üç test istiyor; her biri için beklenen ve gerçekleşen sonucu yaz)
1. **Olağan başvuru:** Sorunsuz bir OLUMSUZ başvuru (ör. BSV-001 sınav, BSV-002 video) → taslak + dayandığı kayıtlar + İK onayı.
2. **Yeni dosya:** Aynı yapıda, kayıt sayısı farklı bir dosya (scripts/ altında 02_Veriler.xlsx'ten ~40 başvuruluk bir alt küme üreten küçük bir betik yaz) → sayılar ve listeler güncellenir.
3. **Değişen veri:** Bir başvurunun kaydını değiştir (ör. BSV-002'nin gözlem metni) → eski taslak ve onay düşer, yeni taslak üretilir.

Ek olarak `pytest` ile ön kontrol kurallarını ve hash geçersiz kılmayı test et (API çağrısı gerektirmeyen testler).

## Teslim biçimi
- Proje yapısı:
  - `backend/` — FastAPI uygulaması; `core/` (veri okuma, kurallar, prompt, son kontrol, depolama), `tests/`, `logs/`.
  - `frontend/` — React + Vite + TypeScript.
  - `scripts/` (test dosyası üretme vb.), kökte `README.md` ve başlatma betiği.
- **API uçları** (öneri, planda netleştir): dosya yükleme ve özet sayılar; başvuru listesi (filtre: grup/aşama); başvuru detayı ve dayandığı kayıtlar; taslak üret; İK düzeltmesini kaydet; İK onayla; İK listesini dışa aktar; iş yükü hesabı.
- **Ekranlar** (öneri): (1) Yükleme + özet kartları (toplam, OLUMSUZ/KABUL/DEVAM; taslak/İK/işlenmeyen), (2) başvuru listesi ve İK inceleme listesi (nedenleriyle), (3) başvuru detayı: solda dayandığı kayıtlar, sağda taslak + kontrol sonuçları + düzenleme + onay, durum etiketleri ("yeni üretildi", "kayıtlı", "geçersiz – veri değişti", "onaylandı"), (4) iş yükü sekmesi.
- `README.md`: kurulum ve çalıştırma adımları (backend için `uv sync`, frontend için `npm install`, `.env`, tek başlatma komutu), iki yapay zekâ yolu ve üç testin nasıl tekrarlanacağı.
- Sunum videosu (≤90 sn) çekeceğiz: yükleme → sayılar → bir olumsuz başvuru seçimi → taslak ve dayandığı kayıtlar → kontrol → İK onayı akışı birkaç tıklamayla gösterilebilmeli.
- `.env` git'e girmez; `.env.example` olsun.
- Sonunda bana şunları raporla: neyi bitirdin, neyi kapsam dışı bıraktın, beklenen İK listesiyle farklar, 3 test sonucu.

## Çalışma şekli
- Önce planı göster: dosya yapısı, ön kontrol kurallarının listesi, iş sırası. Onaydan sonra başla.
- Sıra: **backend: veri okuma + sayım → ön kontrol + İK listesi → taslak + son kontrol → onay + hash → pytest**; ardından **frontend: yükleme/özet → listeler → detay/onay ekranı → iş yükü sekmesi.** Backend uçlarını frontend'den önce bitirip test et. Her adım çalışır hâlde bitsin; sonuna kadar yetişmezsek elimizde çalışan bir parça kalsın.
- Belirsiz bir veri durumunda tahmin etme; İK incelemesine ayır ve bana not düş.
