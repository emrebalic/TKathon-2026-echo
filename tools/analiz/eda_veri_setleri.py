import sys, os, re, json, pandas as pd
sys.stdout.reconfigure(encoding='utf-8')
f, out = sys.argv[1], sys.argv[2]
os.makedirs(out, exist_ok=True)

K = pd.read_excel(f, 'Başvuru Kararları'); L = pd.read_excel(f, 'Başvuru Listesi'); A = pd.read_excel(f, 'Aşama Kayıtları')
S = pd.read_excel(f, 'Sınav Sonuçları'); D = pd.read_excel(f, 'İngilizce Görüşme Sonuçları'); I = pd.read_excel(f, 'İK Değerlendirme Notları')
P = pd.read_excel(f, 'Program Aşamaları'); W = pd.read_excel(f, 'İş Yükü Verileri'); PL = pd.read_excel(f, 'Planlama Verileri')

KC = 'İK’nın kaydettiği başvuru sonucu (kod)'; KD = 'Kararın dayandığı kayıt ID’leri'; ID_ = 'Gerekçenin dayandığı kayıt ID’leri'
SH = 'Bilginin adayla paylaşılma durumu (kod)'; FX = 'Bu kaydın düzelttiği eski kayıt ID'; OBS = 'Değerlendiricinin gözlemi / süreç notu'
GK = 'İK ret gerekçesinin türü (kod)'; TY = 'Gerekçenin paylaşımı için İK teyidi (kod)'; KI = 'Kurum içi not — dış paylaşıma kapalı'

order = dict(zip(P['Aşama kodu'], P['Sıra'])); names = dict(zip(P['Aşama kodu'], P['Aşama adı']))
short = {'SINAV': 'Sınav', 'VIDEO': 'Video', 'GRUP': 'Grup', 'INGILIZCE': 'İngilizce görüşme', 'ENVANTER': 'Envanter',
         'IK_TEKNIK': 'İK ve birim', 'TEKLIF': 'Teklif', 'BELGE': 'Belge'}
ids = lambda v: [] if pd.isna(v) else [x.strip() for x in str(v).split(';') if x.strip()]
src = {}
for df in (A, S, D, I):
    for _, r in df.iterrows():
        src[r['Kayıt ID']] = r
corr = {r[FX]: r['Kayıt ID'] for df in (A, S) for _, r in df[df[FX].notna()].iterrows()}
iknote = {r['Başvuru ID']: r for _, r in I.iterrows()}

CHECKS = ['Çelişkili gözlem', 'Dayanak düzeltildi', 'İK notu yok', 'Gerekçe yazılmamış',
          'Teyit yazılmamış', 'Teyit HAYIR', 'Dayanak kurum içi', 'Kişilik yargısı']
PERS = re.compile(r'kişiliği|içine kapanık|uyum sağlayamaz', re.I)

rows, matrix = [], []
for _, k in K.iterrows():
    b = k['Başvuru ID']; code = k[KC]; st = k['Aşama kodu']
    secs = S[(S['Başvuru ID'] == b) & S[FX].isna()]
    sec = {r['Sınav bölümü']: r for _, r in secs.iterrows()}
    fixes = S[(S['Başvuru ID'] == b) & S[FX].notna()]
    dl = D[D['Başvuru ID'] == b]
    reached = A[A['Başvuru ID'] == b]['Aşama kodu'].map(order).max()
    n = iknote.get(b)
    rec = dict(bsv=b, karar=code, karar_asama=short.get(st, st), karar_sira=int(order.get(st, 0)),
               ulasilan_sira=int(reached), durum='Kapsam dışı', inceleme_nedeni='', inceleme_dayanak='', ozel_dil='',
               gy_dogru=int(sec['GENEL_YETENEK']['Doğru sayısı']) if 'GENEL_YETENEK' in sec else None,
               en_dogru=int(sec['INGILIZCE']['Doğru sayısı']) if 'INGILIZCE' in sec else None,
               en_duzeltilmis=int(fixes.iloc[0]['Doğru sayısı']) if len(fixes) else None,
               dl_puan=int(dl.iloc[0]['İngilizce görüşme puanı']) if len(dl) else None,
               ik_gerekce=(n[GK] if n is not None else 'NOT YOK') if code == 'OLUMSUZ' and st in ('VIDEO', 'GRUP', 'IK_TEKNIK') else '',
               ik_teyit=(n[TY] if n is not None else 'NOT YOK') if code == 'OLUMSUZ' and st in ('VIDEO', 'GRUP', 'IK_TEKNIK') else '')
    if code == 'OLUMSUZ':
        hit = dict.fromkeys(CHECKS, 0); ev = []
        dids = ids(k[KD])
        for d in dids:
            r = src.get(d)
            if d in corr:
                hit['Dayanak düzeltildi'] = 1; ev.append(f'{d} → {corr[d]}')
            if r is not None and SH in r.index and r[SH] == 'KURUM_ICI':
                hit['Dayanak kurum içi'] = 1; ev.append(f'{d} kurum içi')
            if r is not None and OBS in r.index and isinstance(r[OBS], str) and PERS.search(r[OBS]):
                hit['Kişilik yargısı'] = 1
        stage_ev = A[(A['Başvuru ID'] == b) & (A['Aşama kodu'] == st) & A['Beceri kodu'].notna() & A[FX].isna()]
        for eid, g in stage_ev.groupby('Görüşme / görev ID'):
            g2 = g[~g['Kayıt ID'].isin(corr.keys())]
            if len(g) > 1 and not any(x in corr for x in g['Kayıt ID']):
                hit['Çelişkili gözlem'] = 1; ev.append(' ↔ '.join(g['Kayıt ID']))
        if st in ('VIDEO', 'GRUP', 'IK_TEKNIK'):
            if n is None:
                hit['İK notu yok'] = 1; ev.append('İK notu satırı yok')
            else:
                if n[GK] == 'BELIRTILMEDI': hit['Gerekçe yazılmamış'] = 1; ev.append(f"{n['Kayıt ID']} gerekçe = BELIRTILMEDI")
                if n[TY] == 'BELIRTILMEDI': hit['Teyit yazılmamış'] = 1; ev.append(f"{n['Kayıt ID']} teyit = BELIRTILMEDI")
                if n[TY] == 'HAYIR': hit['Teyit HAYIR'] = 1; ev.append(f"{n['Kayıt ID']} teyit = HAYIR")
        prio = ['Çelişkili gözlem', 'Dayanak düzeltildi', 'Kişilik yargısı', 'İK notu yok', 'Gerekçe yazılmamış', 'Teyit yazılmamış', 'Teyit HAYIR', 'Dayanak kurum içi']
        main = next((c for c in prio if hit[c]), '')
        labels = {'Çelişkili gözlem': 'Çelişkili gözlem', 'Dayanak düzeltildi': 'Dayanak sonradan düzeltildi',
                  'Kişilik yargısı': 'Kurum içi kişilik yargısı', 'İK notu yok': 'İK notu yok',
                  'Gerekçe yazılmamış': 'Ret gerekçesi yazılmamış', 'Teyit yazılmamış': 'Paylaşım teyidi yok',
                  'Teyit HAYIR': 'Paylaşım onaylanmadı', 'Dayanak kurum içi': 'Dayanak kurum içi'}
        rec['durum'] = 'İK incelemesi' if main else 'Taslağa uygun'
        rec['inceleme_nedeni'] = labels.get(main, '')
        rec['inceleme_dayanak'] = '; '.join(dict.fromkeys(ev)) if main else ''
        notes = []
        if n is not None and n[GK] == 'KONTENJAN_KISITI': notes.append('Kontenjan: yetersizlik ima etme, öneri ve vaat yok')
        if len(dids) == 2 and st == 'SINAV': notes.append('İki bölüm de baraj altında')
        if n is not None and pd.notna(n[KI]): notes.append('Kurum içi not var: iç kod sızmamalı')
        rec['ozel_dil'] = '; '.join(notes)
        for c in CHECKS:
            matrix.append(dict(bsv=b, asama=short[st], kontrol=c, deger=hit[c]))
    rows.append(rec)

bas = pd.DataFrame(rows)
print(bas['durum'].value_counts().to_dict()); print(bas[bas.durum == 'İK incelemesi'][['bsv', 'inceleme_nedeni', 'inceleme_dayanak']].to_string())
print(bas[bas.ozel_dil != ''][['bsv', 'durum', 'ozel_dil']].to_string())

sinav = [dict(kayit_id=r['Kayıt ID'], bsv=r['Başvuru ID'], bolum='Genel yetenek' if r['Sınav bölümü'] == 'GENEL_YETENEK' else 'İngilizce',
              soru=int(r['Soru sayısı']), dogru=int(r['Doğru sayısı']), yanlis=int(r['Yanlış sayısı']), bos=int(r['Boş sayısı']),
              baraj=int(r['Geçmek için gereken doğru sayısı']), sonuc='Geçti' if r['Sınav bölümünün sonucu (kod)'] == 'GECTI' else 'Geçemedi',
              duzeltme=int(pd.notna(r[FX]))) for _, r in S.iterrows()]
dil = [dict(kayit_id=r['Kayıt ID'], bsv=r['Başvuru ID'], puan=int(r['İngilizce görüşme puanı']), tavan=int(r['Alınabilecek en yüksek puan']),
            baraj=int(r['Geçmek için gereken puan']), sonuc='Geçti' if r['İngilizce görüşmesinin sonucu (kod)'] == 'GECTI' else 'Geçemedi') for _, r in D.iterrows()]

karar_of = dict(zip(K['Başvuru ID'], K[KC]))
ev_rows = []
def add(r, tablo, tur, paylasim=''):
    ev_rows.append(dict(kayit_id=r['Kayıt ID'], tablo=tablo, bsv=r['Başvuru ID'], tarih=r['Kayıt tarihi'].strftime('%Y-%m-%d'),
                        saat=r['Kayıt tarihi'].strftime('%H:%M'), asama=short.get(r['Aşama kodu'], r['Aşama kodu']), tur=tur,
                        paylasim=paylasim, karar=karar_of[r['Başvuru ID']]))
for _, r in K.iterrows(): add(r, 'Başvuru Kararları', 'Karar')
for _, r in I.iterrows(): add(r, 'İK Değerlendirme Notları', 'İK notu')
for _, r in A.iterrows():
    tur = 'Düzeltme' if pd.notna(r[FX]) else ('Değerlendirici gözlemi' if pd.notna(r['Beceri kodu']) else 'Süreç kaydı')
    add(r, 'Aşama Kayıtları', tur, r[SH])
for _, r in S.iterrows(): add(r, 'Sınav Sonuçları', 'Düzeltme' if pd.notna(r[FX]) else 'Sınav / görüşme sonucu', r[SH])
for _, r in D.iterrows(): add(r, 'İngilizce Görüşme Sonuçları', 'Sınav / görüşme sonucu', r[SH])

def tmpl(t):
    if 'ikinci değerlendirici' in t: return 'İkinci değerlendirici notu'
    if 'Önceki eksiklik gözlemi bu görev için geçerli değildir' in t or t.startswith('Doğru görev formu'): return 'Düzeltme'
    if 'kişiliği' in t: return 'Kişilik yargısı'
    if re.search(r'beklentisi bu görevde karşılandı|örneğinde kendi görevinin|önerisini sundu|bir öneri ekledi|kendi görevini, attığı adımı|ortak listeye bu görevi ekledi', t):
        return 'Beklentiyi karşılayan'
    if 'Bu gözlem yalnız bu soru' in t or re.search(r'belirtmedi|açıklamadı|açıklayamadı|eklemedi|tekrarladı|aktardı', t): return 'Eksiklik bildiren'
    return 'Beklentiyi karşılayan'
gz = A[A['Beceri kodu'].notna()].copy()
gozlem = []
for _, r in gz.iterrows():
    kst = K.loc[K['Başvuru ID'] == r['Başvuru ID'], 'Aşama kodu'].iloc[0]; kk = karar_of[r['Başvuru ID']]
    ctx = 'Olumsuz: karar aşaması' if kk == 'OLUMSUZ' and r['Aşama kodu'] == kst else ('Olumsuz: geçilmiş aşama' if kk == 'OLUMSUZ' else ('Kabul' if kk == 'KABUL' else 'Devam ediyor'))
    gozlem.append(dict(kayit_id=r['Kayıt ID'], bsv=r['Başvuru ID'], asama=short[r['Aşama kodu']], baglam=ctx, sablon=tmpl(r[OBS])))
print(pd.crosstab(pd.DataFrame(gozlem).sablon, pd.DataFrame(gozlem).baglam))

is_yuku = [dict(asama=short[r['Olumsuz karar aşaması']], olumsuz=int(r['Olumsuz başvuru sayısı']), ek_inceleme=int(r['Bu başvuruların kaçında ek inceleme gerekiyor?']),
                okuma_dk=float(r['Bir başvurunun kayıtlarını okuma (dk)']), yazma_dk=float(r['Bir başvuruya mesaj yazma (dk)']),
                kontrol_dk=float(r['Bir mesajın son kontrolü (dk)']), ek_dk=float(r['Ek inceleme gereken başvuru başına ek süre (dk)'])) for _, r in W.iterrows()]
planlama = [dict(donem=PL.iloc[0]['Planlama dönemi kodu'], is_gunu=int(PL.iloc[0]['İş günü sayısı']), ayrilan_saat=float(PL.iloc[0]['Dönem boyunca ayrılabilen toplam İK süresi (saat)']))]
varsayim = [dict(parametre='Yapay zekâ taslağının İK kontrolü (dk)', deger=2.0), dict(parametre='Ortalama İK düzeltmesi (dk)', deger=0.5)]

n_neg = int((bas.karar == 'OLUMSUZ').sum())
kur_ici_clean = bas[(bas.durum == 'Taslağa uygun') & bas.ozel_dil.str.contains('Kurum içi')].bsv.tolist()
evet_trap = bas[(bas.ik_teyit == 'EVET') & (bas.durum == 'İK incelemesi')].bsv.tolist()
cnt = lambda c: int(sum(m['deger'] for m in matrix if m['kontrol'] == c))
exact = int(((S['Doğru sayısı'] == S['Geçmek için gereken doğru sayısı']) & S[FX].isna()).sum())
dl_mid = int(D['İngilizce görüşme puanı'].between(int(S[S['Sınav bölümü'] == 'INGILIZCE']['Geçmek için gereken doğru sayısı'].iloc[0]), int(D['Geçmek için gereken puan'].iloc[0]) - 1).sum())
passed_pos = sum(1 for g in gozlem if g['baglam'] == 'Olumsuz: geçilmiş aşama')
T = [
 ('T01', 'Kayıt', 'Kritik', 'Aynı görevde çelişen iki gözlem', 'Aynı görüşme/görev ID’sinde iki değerlendirici farklı sonuç yazmış; ortak not girilmemiş. İK notu EVET olsa bile çelişki çözülmüş sayılmaz.', 'AS-003-03 ↔ AS-003-04', cnt('Çelişkili gözlem'), 'Karar aşamasında aynı etkinlik_id için birden fazla değerlendirici satırı varsa İK’ya ayır.'),
 ('T02', 'Kayıt', 'Kritik', 'Dayanağı sonradan düzeltilmiş karar', 'Düzeltme kayıtları karardan 19–20 saat sonra girilmiş; eski “eksiklik” gözlemi geçersiz, karar ve İK notu güncellenmemiş.', 'AS-005-06 → AS-005-07', cnt('Dayanak düzeltildi'), 'Karar ya da İK dayanağındaki bir ID başka bir satırın “düzelttiği kayıt” alanında geçiyorsa İK’ya ayır.'),
 ('T03', 'Kayıt', 'Kritik', 'Yeniden puanlanınca geçen sınav', 'İngilizce bölümü yanlış cevap anahtarıyla puanlanmış; düzeltmede 6/15 doğru 11/15 olmuş ve sonuç GEÇTİ’ye dönmüş. Ret kaydı hâlâ duruyor.', 'SN-033-EN → SN-033-EN-D1', 1, 'Sınav düzeltmesi bölüm sonucunu değiştiriyorsa e-posta üretme; kararı da kendin değiştirme.'),
 ('T04', 'Kayıt', 'Yüksek', 'Öznel aşamada İK notu yok', 'Video, grup ve İK/birim retlerinde son İK gerekçesi zorunlu; bu başvuruların İK notu satırı hiç yok.', 'BSV-040, BSV-057, BSV-081', cnt('İK notu yok'), 'Öznel aşama retlerinde Başvuru ID ile İK notu bulunamazsa İK’ya ayır.'),
 ('T05', 'Kod', 'Yüksek', 'BELIRTILMEDI ile UYGULANMAZ aynı değil', 'Gerekçe kodu BELIRTILMEDI: neden yazılmamış. UYGULANMAZ ise yalnız kabul kayıtlarında, “aranmaz” demek.', 'IK-044', cnt('Gerekçe yazılmamış'), 'Gerekçe kodu yalnız GEREKLILIK_KARSILANMADI ya da KONTENJAN_KISITI ise taslak üret.'),
 ('T06', 'Kod', 'Yüksek', 'Paylaşım teyidi yazılmamış', 'Teyit BELIRTILMEDI: izin var da denemez, yok da. Gerekçe dolu olsa bile paylaşım kapsamı belirsiz.', 'IK-047', cnt('Teyit yazılmamış'), 'Öznel aşamada teyit EVET değilse İK’ya ayır.'),
 ('T07', 'Kod', 'Kritik', 'Paylaşım onaylanmamış (HAYIR)', 'Bu başvurularda dayanak gözlem de KURUM_ICI. Ayrıntılı gerekçe adaya aktarılamaz.', 'IK-007 + AS-007-03', cnt('Teyit HAYIR'), 'Teyit HAYIR ise e-posta üretme; İK paylaşım kapsamını belirlesin.'),
 ('T08', 'Kod', 'Kritik', 'EVET teyidi güvenli demek değil', 'Teyit EVET olan bazı başvurular yine de çelişki, düzeltme ya da kurum içi dayanak taşıyor. EVET, KURUM_ICI kısıtını ve çelişkiyi kaldırmaz.', ', '.join(evet_trap[:4]) + ' …', len(evet_trap), 'Teyidi diğer kontrollerden sonra değerlendir; EVET tek başına onay değildir.'),
 ('T09', 'İçerik', 'Kritik', 'Kurum içi kişilik yargısı', 'Dayanak gözlem “içine kapanık, liderlik kişiliği zayıf” diyor; somut örnek yok ve kayıt KURUM_ICI. İK notu yine de EVET.', 'AS-006-06', cnt('Kişilik yargısı'), 'KURUM_ICI dayanak ya da kişilik ifadesi varsa İK’ya ayır; kişilik yargısını asla aktarma.'),
 ('T10', 'İçerik', 'Kritik', 'Kontenjan reddi yetersizlik değildir', 'Aday tüm aşamaları geçmiş; birimin 4 kişilik kontenjanı 0’a indirilmiş. Gelişim önerisi, gelecek dönem vaadi ve yetersizlik imasının hiçbiri olmamalı.', 'AS-008-07, IK-008', int((bas.ik_gerekce == 'KONTENJAN_KISITI').sum()), 'Kontenjan şablonu ayrı tutulsun; çıktıda “eksik, geliştir, yetersiz” gibi kelimeler aranıp engellensin.'),
 ('T11', 'İçerik', 'Yüksek', 'İç kodlar taslağa sızabilir', 'Taslağa uygun başvuruların bazılarında kurum içi not var: T101-K-036, T101-T8, GRP-B, KP-2026-03-25-01 gibi kodlar.', ', '.join(kur_ici_clean[:4]) + ' …', len(kur_ici_clean), 'Kurum içi not alanını modele hiç verme; çıktıda iç kod kalıplarını tara.'),
 ('T12', 'İçerik', 'Dikkat', 'İki sınav bölümünden de kalanlar', 'Kararın iki dayanağı var; e-posta yalnız birini anlatırsa eksik kalır.', 'BSV-014: SN-014-GY;SN-014-EN', int(bas.ozel_dil.str.contains('İki bölüm').sum()), 'Dayanak listesindeki her sınav bölümünü e-postada ayrı göster.'),
 ('T13', 'Eşik', 'Dikkat', 'Baraja eşit puan geçer', 'Geçme koşulu “en az”: tam baraj puanı alan satırlar GEÇTİ, bir eksik alan GEÇEMEDİ. “>” ile hesaplamak bu satırları ters çevirir.', 'SN-006-EN: 10/15 GEÇTİ', exact, 'Sonucu yeniden hesaplama; kayıtlı sonuç kodunu kullan, yalnız tutarlılık için ≥ ile kontrol et.'),
 ('T14', 'Eşik', 'Yüksek', 'İki ayrı İngilizce barajı', 'Sınavın İngilizce bölümü 15 soruda 10 doğru, sözlü görüşme 20 puanda 12 istiyor. Görüşmede 10–11 alan adaylar kaldı.', 'DL-068: 10/20 GEÇEMEDİ', dl_mid, 'Sınav ve görüşme kayıtlarını ayrı tablolardan, ayrı barajlarla anlat.'),
 ('T15', 'İçerik', 'Yüksek', 'Görüşme puanı dil seviyesi değildir', 'Puan yalnız o görüşmeye ait. CEFR, “B2” ya da genel İngilizce düzeyi yazmak kayıtta olmayan iddia olur.', 'DL-004', int(((bas.karar == 'OLUMSUZ') & (bas.karar_asama == 'İngilizce görüşme')).sum()), 'Çıktıda A1–C2, CEFR, “seviye” gibi ifadeleri engelle.'),
 ('T16', 'İçerik', 'Yüksek', 'Envanter ret gerekçesi olamaz', 'Kişilik envanterinde yalnız “tamamlandı” bilgisi var ve kayıtlar KURUM_ICI.', 'AS-005-05', int((A['Aşama kodu'] == 'ENVANTER').sum()), 'Envanter kayıtlarını modele verme.'),
 ('T17', 'İçerik', 'Kritik', 'Geçilen aşama ret nedeni değildir', 'Olumsuz başvuruların geçilmiş aşamalarındaki gözlemlerin hepsi beklentiyi karşılayan türden. Model bunları ret nedeni gibi yazarsa uydurmuş olur.', 'BSV-003 video gözlemi', passed_pos, 'Modele yalnız karar aşamasının kayıtlarını ver.'),
 ('T18', 'Kapsam', 'Yüksek', 'Kabul ve devam edenlere ret e-postası yok', 'DEVAM_EDIYOR başvuruların her birinde bir DEGERLENDIRILIYOR kaydı var. TAMAMLANDI da geçti demek değil.', 'BSV-011 (VIDEO, değerlendiriliyor)', int((bas.karar != 'OLUMSUZ').sum()), 'Yalnız karar kodu OLUMSUZ olan başvurular işlensin; tanımsız ya da boş kod İK’ya.'),
 ('T19', 'Teknik', 'Yüksek', 'Sütun adında tipografik kesme işareti', '“İK’nın kaydettiği başvuru sonucu (kod)” başlığındaki işaret düz tırnak (\') değil, U+2019 (’). Koda elle yazılan sütun adı eşleşmez.', 'Başvuru Kararları F sütunu', int(sum(1 for c in list(K.columns) + list(I.columns) if '’' in c)), 'Sütunları Alan Sözlüğü’ndeki teknik adlara eşle ya da adları normalize et.'),
 ('T20', 'Teknik', 'Dikkat', 'İK notlarındaki formül sütunları', 'İK Değerlendirme Notları M–N sütunları Excel formülü. Dosya bir kütüphaneyle değiştirilirse önbellekteki açıklama eski ya da boş kalabilir.', 'IK-002 M2/N2', int(len(I)) * 2, 'Kod anlamlarını formül sütunlarından değil, Kod Açıklamaları’ndan üret.'),
 ('T21', 'Teknik', 'Dikkat', 'Birden çok dayanak tek hücrede', 'Dayanak ID’leri noktalı virgülle ayrılmış. Tek ID varsayan bir birleştirme kayıt kaçırır.', 'AS-003-03;AS-003-04', int(sum(1 for v in list(K[KD]) + list(I[ID_]) if isinstance(v, str) and ';' in v)), 'Dayanak alanını “;” ile bölüp her ID’yi ayrı doğrula.'),
 ('T22', 'Teknik', 'Dikkat', 'Boş hücre her zaman hata değil', 'Kabul ve devam kayıtlarında karar dayanağı boş; kontenjan İK notlarında beceri kodu boş. Bunlar eksik veri sayılmamalı.', 'BSV-009 dayanak boş', int(K[KD].isna().sum()), 'Boşluğu alanına göre yorumla (Alan Sözlüğü); karar kodu boşsa İK’ya ayır.'),
 ('T23', 'Ölçek', 'Yüksek', 'Örnekteki sorun oranı dönemi temsil etmez', 'Dosyadaki sorunlu kayıtlar bilerek artırılmış: örnekte olumsuzların yaklaşık üçte biri İK’ya gidiyor, 1.200’lük dönemde 160/1.200.', '120 ↔ 1.200', int((bas.durum == 'İK incelemesi').sum()), 'İş yükünü 120 kayıttan ölçekleme; dönem verisini, kendi ölçtüğün başvuru başı süreyle kullan.'),
]
tuzak = [dict(kod=a, kategori=b, seviye=c, baslik=d, neden=e, ornek=f_, etkilenen=g, mvp_kurali=h) for a, b, c, d, e, f_, g, h in T]

def dump(name, data):
    with open(os.path.join(out, name + '.json'), 'w', encoding='utf-8') as fh:
        json.dump(data, fh, ensure_ascii=False, separators=(',', ':'), default=lambda o: None)
    print(name, len(data), os.path.getsize(os.path.join(out, name + '.json')))
dump('basvurular', json.loads(bas.to_json(orient='records', force_ascii=False)))
dump('kontrol_matrisi', matrix); dump('sinav', sinav); dump('dil', dil); dump('kayitlar', ev_rows)
dump('gozlemler', gozlem); dump('is_yuku', is_yuku); dump('planlama', planlama); dump('varsayimlar', varsayim); dump('tuzaklar', tuzak)
print('evet_trap', evet_trap, 'kur_ici_clean', kur_ici_clean, 'exact', exact, 'dl_mid', dl_mid, 'passed_pos', passed_pos)
