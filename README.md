# Aday geri bildirim MVP'si

Olumsuz sonuçlanan program başvuruları için ATS kayıtlarına dayanan, Meta Muse ile yazılan ve İK onayından
geçen geri bildirim e-postası taslakları. Kararı değiştirmez; dayanağı eksik, çelişkili, düzeltilmiş ya da paylaşımı
onaylanmamış başvuruları e-posta üretmeden İK'ya ayırır.

**Yığın:** FastAPI + uv (backend, bütün kurallar) · tek sayfa HTML + Tailwind (frontend, yalnız gösterim) · SQLite · Meta Model API (`muse-spark-1.3`).

## Çalıştırma

Gereken: [uv](https://docs.astral.sh/uv/) ve internet (Muse ve Tailwind CDN).

```bash
uv sync --directory backend
```

Depo kökünde `.env` dosyası oluşturun (`.env.example`'ı kopyalayın) ve `MODEL_API_KEY` satırına Meta Model API anahtarını yazın.

```bash
uv run --directory backend uvicorn app.main:create_app --factory --reload
```

Tarayıcıda **http://localhost:8000** adresini açın ve "ATS Excel dosyası yükle" ile `data/test/Veriler_60_basvuru.xlsx` dosyasını yükleyin
(aynı biçimdeki herhangi bir ATS dosyası da olur). Program adı `.env` içindeki `PROGRAM_ADI` ile değiştirilir.

- Testler: `uv run --directory backend pytest`
- Muse bağlantısı: `uv run --directory backend python ../scripts/muse_baglanti_testi.py`

Testler depodaki `data/test/` dosyalarıyla çalışır; ek dosya gerekmez.

## Akış

1. **Yükleme ve sayım:** toplam, OLUMSUZ / KABUL / DEVAM_EDIYOR, veri sorunu; olumsuzlarda taslağı hazırlanan / İK incelemesine ayrılan / henüz işlenmeyen.
2. **Ön kontrol** (kod): dayanak bulunamadı ya da başka başvuruya ait, dayanak düzeltilmiş, sınav sayıları tutarsız ya da geçilen bölüm, görüşmede gözlem yok, İK notu / gerekçe / teyit eksik, KURUM_ICI dayanak, kişilik yargısı, kontenjanın idari kaydı yok, çelişkili gözlem → e-posta üretilmez, İK'ya.
3. **Taslak** (Muse): yalnız o başvurunun paylaşılabilir kayıtları; aşamaya göre istem bloğu; JSON çıktı (`email_konu`, `email_metni`, `kullanilan_kayit_idleri`, `emin_olunmayan_noktalar`).
   Dosya yüklenince geçerli taslağı olmayan bütün uygun başvuruların taslakları arka planda (aynı anda 5 çağrı) hazırlanır; başvuruya tıklayınca taslak hazır açılır. Aynı dosya yeniden yüklenirse yalnız verisi değişen başvurular yeniden üretilir. Kapatmak için `.env`'e `MVP_ON_URETIM=0`.
4. **Son kontrol** (kod): kayıt ID'leri, kayıtta olmayan sayı, yasaklı ifadeler, iç kodlar, en fazla 120 kelime, Başvuru ID. Sorun varsa "İK dikkat"; otomatik düzeltme yok.
5. **İK:** düzenle, kaydet, onayla. İlk taslak, İK düzeltmesi ve onay ayrı saklanır. Girdi değişirse taslak ve onay, metin değişirse onay düşer.
6. **İngilizce sürüm (isteğe bağlı):** Taslağın üstündeki "English" sekmesinden o anda üretilir. Muse güncel Türkçe metni başvurunun kayıtlarıyla birlikte çevirir; sayılar, Başvuru ID, yasaklı ifadeler ve uzunluk kod ile karşılaştırılır. Türkçe metin değişirse İngilizce sürüm "eski" olarak işaretlenir.
7. **Dışa aktarım:** İK listesi ve İK düzeltmeleri Excel olarak. Her model çağrısı `backend/logs/` altında JSON.
8. **İş yükü:** dosyadaki İş Yükü ve Planlama sayfalarıyla elle süreç ve önerilen süreç; dakikalar değiştirilerek duyarlılık.

**İkinci yapay zekâ yolu:** Yanıtlar dışarıda üretildiyse `POST /api/yanitlar` ucuna Excel ya da JSON yüklenir (arayüzde düğmesi yok)
(sütunlar: `basvuru_id`, `email_konu`, `email_metni`, `kullanilan_kayit_idleri`). Başvuru ID'si eşleşmeyen yanıt onaya açılmaz.

## Üç test

Test dosyaları `data/test/` altındadır: `Veriler_60_basvuru.xlsx`, `Veriler_40_basvuru.xlsx` ve `Veriler_degisen_BSV-002.xlsx`.
Başka bir kaynaktan yeniden üretmek için: `uv run --directory backend python ../scripts/alt_kume_olustur.py <kaynak.xlsx>`.

1. **Olağan başvuru:** `Veriler_60_basvuru.xlsx` → BSV-001 ya da BSV-002 → taslak üret → dayandığı kayıtlar → İK onayla.
2. **Yeni dosya:** `Veriler_40_basvuru.xlsx` yükle → toplam 40, listeler güncel.
3. **Değişen veri:** BSV-002'yi onayla → `Veriler_degisen_BSV-002.xlsx` yükle → BSV-002 "Geçersiz – veri değişti"; yeniden üret.

Aynı akışlar `backend/tests/test_akis.py` içinde sahte modelle otomatik test edilir.

## Klasörler

| Yol | İçerik |
|---|---|
| `backend/` | FastAPI, kural motoru, istem, son kontrol, SQLite, testler |
| `frontend/` | Tek sayfa İK paneli |
| `scripts/` | Test dosyası üretici, Muse bağlantı testi |
| `data/test/` | Test dosyaları (60 ve 40 başvuru, BSV-002'si değişmiş kopya) |
| `docs/` | İletişim kararları (A–G), veri tuzakları, analiz, iş yükü |
| `tools/analiz/` | Veri analizi betikleri |
| `data/raw/` | Ham kaynak dosyalar (git'e girmez) |
