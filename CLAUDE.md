# TKATHON 2026 · Junior Wings geri bildirim MVP'si

Olumsuz Junior Wings başvuruları için ATS kayıtlarına dayanan, İK onayından geçen geri bildirim taslakları.
Vaka `docs/VAKA.md`, görev tanımı `docs/MVP_GOREV.md`, takım kararları `docs/ILETISIM_KARARLARI.md`,
veri tuzakları `docs/TUZAKLAR.md`. Son teslim 16.45, sunum 17.00.

## Komutlar (depo kökünden)

```bash
uv sync --directory backend
uv run --directory backend uvicorn app.main:create_app --factory --reload     # http://localhost:8000
uv run --directory backend pytest
uv run --directory backend python ../scripts/alt_kume_olustur.py
uv run --directory backend python ../scripts/muse_baglanti_testi.py
```

## Yapı

- `backend/core/`: schema, loader (Excel → teknik adlar), rules (ön kontrol), girdi (modele giden kayıtlar),
  istem (A–G), llm (Muse, `muse-spark-1.3`), son_kontrol, taslak, depo (SQLite + hash), is_yuku
- `backend/app/main.py`: `create_app()` fabrikası (içe aktarmak uygulama başlatmaz); FastAPI uçları; yüklemeden sonra
  taslakları arka planda üretir (`/api/uretim`, `MVP_ON_URETIM=0` ile kapanır); `frontend/` klasörünü `/` altında sunar
- `frontend/`: tek sayfa (Tailwind CDN + sade JS); iş kuralı içermez, yalnız API'yi gösterir
- `backend/logs/`: her model çağrısının girdisi ve ham yanıtı (teslim şartı); `backend/data/`: SQLite ve son yükleme

## Değişmez kurallar

- Karar verilmez, değiştirilmez. Yalnız OLUMSUZ için taslak; KABUL ve DEVAM_EDIYOR'a olumsuz e-posta yok; boş ya da tanımsız kod İK'ya.
- Ön kontrolde bir bulgu çıkarsa e-posta üretilmez, başvuru nedeniyle İK listesine düşer.
- Modele yalnız karar aşamasının PAYLASILABILIR kayıtları ve teyidi EVET olan İK gerekçesi gider; kurum içi not, KURUM_ICI kayıt,
  envanter, geçilmiş aşamalar ve başka başvurular gitmez; iç kodlar temizlenir.
- A–G: kalınan bölümün doğru sayısı ve barajı (toplam yok); gözlem kısa özet; kontenjanda yetersizlik, öneri ve vaat yok;
  öneri yalnız somut gözlemle; 80–120 kelime, kurumsal-empatik; soru/itiraz Başvuru ID ile, sonuç ya da tarih sözü yok.
- Son kontrol otomatik düzeltmez, "İK dikkat" işaretler. Gönder düğmesi yok; yalnız İK onayı.
- Girdi hash'i değişirse taslak ve onay, metin değişirse onay geçersiz.
- Sayılar ve başvuru ID'leri koda yazılmaz; 40, 60 ya da 1.000 satırlık dosyada da çalışmalı.

## Kod düzeni

- Tanımlayıcılar ve arayüz metinleri Türkçe; yorumlar seyrek.
- Kural değişikliğinde `backend/tests/` güncellenir; `main`'e yalnız testleri geçen kod girer.
- `.env`, `data/raw/`, `data/test/*.xlsx`, `materials/`, `backend/data/`, `backend/logs/` git'e girmez.
