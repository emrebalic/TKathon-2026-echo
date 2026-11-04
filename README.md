# Junior Wings geri bildirim MVP'si (TKATHON 2026)

Olumsuz sonuçlanan Junior Wings başvuruları için, ATS kayıtlarına dayanan ve İK onayından geçen
geri bildirim e-postası taslakları üretir. Kararı değiştirmez; dayanağı eksik, çelişkili,
düzeltilmiş ya da paylaşımı onaylanmamış başvuruları e-posta üretmeden İK'ya ayırır.

## Kurulum

```bash
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
copy .env.example .env
```

Yarışma dosyalarını `data/raw/` içine kopyalayın (git'e girmez): `02_Veriler.xlsx`, `06_Ek_Gorev_Ornekleri.xlsx`.

## Çalıştırma ve test

```bash
streamlit run app/main.py
pytest
```

Arayüz `http://localhost:8501` adresinde açılır. ATS Excel dosyasını soldan yükleyin; veri değiştiğinde
dosyayı yeniden yükleyin. Panel yeni dosyayı aynı oturumdaki bir önceki yüklemeyle karşılaştırır ve kaydı
değişen, yeni gelen ve dosyadan çıkan başvuruları üstte listeler. Değişen başvuruların eski taslağı ve İK
onayı geçersiz sayılır.

## Yapay zekâ: Meta Muse

`core/llm.py`, Meta Model API'nin OpenAI uyumlu uç noktasını (`https://api.meta.ai/v1`, model `muse-spark-1.3`)
çağırır ve her çağrının girdisini ve ham yanıtını `store/ai_kayitlari.jsonl` dosyasına yazar.
Anahtarı `.env` içine `MODEL_API_KEY` olarak koyup bağlantıyı deneyin:

```bash
python tools/muse_baglanti_testi.py
```

## Klasörler

| Yol | İçerik |
|---|---|
| `core/schema.py` | Excel başlıklarını Alan Sözlüğü'ndeki teknik adlara eşler (’ ve ' farkını yok sayar) |
| `core/loader.py` | Dosyayı okur, zorunlu sayfa ve sütunları doğrular |
| `core/rules.py` | Kural motoru: başvuruları Taslağa uygun / İK incelemesi / Kapsam dışı olarak ayırır, dayanak kayıtlarını ve parmak izini çıkarır |
| `core/degisiklik.py` | İki yükleme arasında değişen başvuruları bulur |
| `core/llm.py` | Muse Spark istemcisi ve yapay zekâ girdi/yanıt kaydı |
| `tools/muse_baglanti_testi.py` | API anahtarı ve JSON şeması desteği denemesi |
| `app/main.py` | Streamlit İK paneli |
| `tests/` | Sayım, İK listesi, farklı kayıt sayısı, veri değişikliği ve yeniden yükleme testleri |
| `docs/ANALIZ.md` | Veri analizi bulguları ve tuzak listesi |
| `data/test/` | 40 / 60 satırlık ve değiştirilmiş test dosyaları |

## Ekip ve dallar

Herkes kendi dalında çalışır, küçük parçalar halinde `main`'e birleştirir.

| Dal | Sorumluluk | Sıradaki iş |
|---|---|---|
| `backend` | Veri ve kural motoru | Taslak / düzeltme / onay deposu (`store/`), parmak izi ile onay geçersizleştirme |
| `ai` | Yapay zekâ | Taslak istemi (yalnız paylaşılabilir alanlar, JSON çıktı) ve çıktı doğrulayıcı (iç kod, CEFR, vaat, kontenjanda yetersizlik ifadesi) |
| `ui` | Arayüz | Taslak düzenleme ve onay akışı, durum sayıları (hazırlanan / bekleyen / işlenmeyen) |
| `ideathon` | İçerik | A–G iletişim kararları, İK kontrol süresi ölçümü, iş yükü Excel'i, 1 sayfalık .docx |
| `sunum` | Test ve sunum | Test dosyaları, 3 testin ekran görüntüleri, pptx, 90 sn video, ek görevler |

## Teslim (son saat 16.45)

1. Bir sayfalık çözüm özeti (.docx)
2. MVP (.zip ya da bu deponun linki) ve çalıştırma notu; kullanılıyorsa API anahtarı, yapay zekâ girdileri ve ham yanıtlar
3. Hesap ve test dosyası (üç testin ekran görüntüleri)
4. Sunum (.pptx) ve en fazla 90 saniyelik video
5. Ek görevler (ayrı dosyalar, ör. `Ek_Gorev_8`)

## Kırmızı çizgiler

Kararı değiştirmek, başka başvurunun bilgisini kullanmak, kurum içi bilgiyi paylaşmak, kayıtta olmayan
iddia eklemek, kontenjan adayına yetersizlik ima etmek, başarı veya işe alım vaadi vermek, e-postayı İK
onayı olmadan göndermek.
