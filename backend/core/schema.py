"""Excel sayfa ve sütun başlıklarını Alan Sözlüğü'ndeki teknik adlara eşler.

Başlıklar karşılaştırılmadan önce normalize edilir: tipografik kesme işareti (’)
düz kesme işaretine çevrilir, boşluklar sadeleştirilir ve harf büyüklüğü yok sayılır.
"""
import re

SHEETS = {
    "kararlar": "Başvuru Kararları",
    "basvurular": "Başvuru Listesi",
    "asamalar": "Program Aşamaları",
    "asama_kayitlari": "Aşama Kayıtları",
    "sinav": "Sınav Sonuçları",
    "dil": "İngilizce Görüşme Sonuçları",
    "ik_notlari": "İK Değerlendirme Notları",
    "beceriler": "Beceri Tanımları",
    "is_yuku": "İş Yükü Verileri",
    "planlama": "Planlama Verileri",
}

# Uygulamanın çalışması için zorunlu sayfalar; diğerleri varsa okunur.
REQUIRED_SHEETS = ["kararlar", "asama_kayitlari", "sinav", "dil", "ik_notlari"]

COLUMNS = {
    "kararlar": {
        "Kayıt ID": "kaynak_id",
        "Başvuru ID": "basvuru_id",
        "Kayıt tarihi": "kayit_tarihi",
        "Aşama kodu": "asama_kodu",
        "Kaydı oluşturan görevli (kod)": "kaynak_rolu",
        "İK'nın kaydettiği başvuru sonucu (kod)": "karar_kodu",
        "Kararın dayandığı kayıt ID'leri": "dayanak_kaynak_idleri",
        "İK'nın karar / süreç açıklaması": "karar_notu",
    },
    "basvurular": {
        "Başvuru ID": "basvuru_id",
        "Anonim aday ID": "aday_id",
        "İlan ID": "ilan_id",
        "Başvuru tarihi": "basvuru_tarihi",
    },
    "asamalar": {
        "Aşama kodu": "asama_kodu",
        "Sıra": "sira",
        "Aşama adı": "asama_adi",
        "Aşamaya İlişkin Kapsam": "aciklama",
    },
    "asama_kayitlari": {
        "Kayıt ID": "kaynak_id",
        "Başvuru ID": "basvuru_id",
        "Görüşme / görev ID": "etkinlik_id",
        "Kayıt tarihi": "kayit_tarihi",
        "Aşama kodu": "asama_kodu",
        "Aşamanın tamamlanma durumu (kod)": "asama_durumu",
        "Kaydı oluşturan görevli (kod)": "kaynak_rolu",
        "Beceri kodu": "gereklilik_kodu",
        "Değerlendiricinin gözlemi / süreç notu": "gozlem_metni",
        "Bilginin adayla paylaşılma durumu (kod)": "paylasim_kodu",
        "Bu kaydın düzelttiği eski kayıt ID": "duzelttigi_kaynak_id",
        "Düzeltme açıklaması": "duzeltme_aciklamasi",
    },
    "sinav": {
        "Kayıt ID": "kaynak_id",
        "Başvuru ID": "basvuru_id",
        "Kayıt tarihi": "kayit_tarihi",
        "Aşama kodu": "asama_kodu",
        "Sınav bölümü": "test_turu",
        "Soru sayısı": "soru_sayisi",
        "Doğru sayısı": "dogru_sayisi",
        "Yanlış sayısı": "yanlis_sayisi",
        "Boş sayısı": "bos_sayisi",
        "Geçmek için gereken doğru sayısı": "gecme_baraji",
        "Sınav bölümünün sonucu (kod)": "kayitli_sonuc",
        "Bilginin adayla paylaşılma durumu (kod)": "paylasim_kodu",
        "Bu kaydın düzelttiği eski kayıt ID": "duzelttigi_kaynak_id",
        "Düzeltme açıklaması": "duzeltme_aciklamasi",
    },
    "dil": {
        "Kayıt ID": "kaynak_id",
        "Başvuru ID": "basvuru_id",
        "Kayıt tarihi": "kayit_tarihi",
        "Aşama kodu": "asama_kodu",
        "Kaydı oluşturan görevli (kod)": "kaynak_rolu",
        "İngilizce görüşme puanı": "kayitli_puan",
        "Alınabilecek en yüksek puan": "olcek_tavani",
        "Geçmek için gereken puan": "gecme_baraji",
        "İngilizce görüşmesinin sonucu (kod)": "kayitli_sonuc",
        "Değerlendiricinin gözlemi / süreç notu": "gozlem_metni",
        "Bilginin adayla paylaşılma durumu (kod)": "paylasim_kodu",
    },
    "ik_notlari": {
        "Kayıt ID": "kaynak_id",
        "Başvuru ID": "basvuru_id",
        "Kayıt tarihi": "kayit_tarihi",
        "Aşama kodu": "asama_kodu",
        "Kaydı oluşturan görevli (kod)": "kaynak_rolu",
        "İK ret gerekçesinin türü (kod)": "gerekce_kodu",
        "İK tarafından kaydedilen ret gerekçesi": "nihai_ret_gerekcesi",
        "Beceri kodu": "gereklilik_kodu",
        "Gerekçenin dayandığı kayıt ID'leri": "dayanak_kaynak_idleri",
        "Gerekçenin paylaşımı için İK teyidi (kod)": "dis_paylasim_teyidi",
        "İK'nın paylaşılabilecek bilgilere ilişkin açıklaması": "dis_paylasim_aciklamasi",
        "Kurum içi not — dış paylaşıma kapalı": "kurum_ici_not",
    },
    "beceriler": {
        "Beceri kodu": "gereklilik_kodu",
        "İlan ID": "ilan_id",
        "Beceri Tanımı": "gereklilik_aciklamasi",
    },
    "is_yuku": {
        "Planlama dönemi kodu": "donem_kodu",
        "Olumsuz karar aşaması": "asama_kodu",
        "Olumsuz başvuru sayısı": "olumsuz_basvuru_sayisi",
        "Bu başvuruların kaçında ek inceleme gerekiyor?": "ek_inceleme_sayisi",
        "Bir başvurunun kayıtlarını okuma (dk)": "kayit_okuma_dk",
        "Bir başvuruya mesaj yazma (dk)": "taslak_yazma_dk",
        "Bir mesajın son kontrolü (dk)": "son_kontrol_dk",
        "Ek inceleme gereken başvuru başına ek süre (dk)": "ek_inceleme_dk",
    },
    "planlama": {
        "Planlama dönemi kodu": "donem_kodu",
        "İş günü sayısı": "is_gunu_sayisi",
        "Dönem boyunca ayrılabilen toplam İK süresi (saat)": "ayrilan_toplam_ik_saati",
    },
}

# Kayıt kimliği ve kod alanları; okurken metne çevrilip kırpılır.
ID_FIELDS = {"kaynak_id", "basvuru_id", "aday_id", "ilan_id", "etkinlik_id", "duzelttigi_kaynak_id",
             "dayanak_kaynak_idleri", "gereklilik_kodu"}
CODE_FIELDS = {"karar_kodu", "asama_kodu", "asama_durumu", "kaynak_rolu", "paylasim_kodu", "test_turu",
               "kayitli_sonuc", "gerekce_kodu", "dis_paylasim_teyidi"}


def normalize(name) -> str:
    text = str(name).replace("’", "'").replace("‘", "'")
    return re.sub(r"\s+", " ", text).strip().casefold()


def sheet_lookup(sheet_names):
    """Dosyadaki sayfa adlarını iç anahtarlara eşler: {iç_anahtar: dosyadaki_ad}."""
    by_norm = {normalize(s): s for s in sheet_names}
    return {key: by_norm[normalize(title)] for key, title in SHEETS.items() if normalize(title) in by_norm}


def column_lookup(key, headers):
    """Bir sayfanın başlıklarını teknik adlara eşler: {dosyadaki_başlık: teknik_ad}."""
    wanted = {normalize(h): tech for h, tech in COLUMNS[key].items()}
    return {h: wanted[normalize(h)] for h in headers if normalize(h) in wanted}
