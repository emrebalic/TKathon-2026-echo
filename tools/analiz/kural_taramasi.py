import sys, re, pandas as pd
sys.stdout.reconfigure(encoding='utf-8')
f = sys.argv[1]
mode = sys.argv[2] if len(sys.argv) > 2 else 'flags'

K = pd.read_excel(f, 'Başvuru Kararları')
A = pd.read_excel(f, 'Aşama Kayıtları')
S = pd.read_excel(f, 'Sınav Sonuçları')
D = pd.read_excel(f, 'İngilizce Görüşme Sonuçları')
I = pd.read_excel(f, 'İK Değerlendirme Notları')

KC = 'İK’nın kaydettiği başvuru sonucu (kod)'
DAY = 'Kararın dayandığı kayıt ID’leri'
SHARE = 'Bilginin adayla paylaşılma durumu (kod)'
FIX = 'Bu kaydın düzelttiği eski kayıt ID'
FIXT = 'Düzeltme açıklaması'

def ids(v):
    if pd.isna(v):
        return []
    return [x.strip() for x in str(v).split(';') if x.strip()]

# unified source index: id -> (table, row)
src = {}
for name, df in [('AS', A), ('SN', S), ('DL', D), ('IK', I), ('KR', K)]:
    for _, r in df.iterrows():
        src[r['Kayıt ID']] = (name, r)

# corrections: old id -> list of correcting rows
corr = {}
for name, df in [('AS', A), ('SN', S)]:
    for _, r in df[df[FIX].notna()].iterrows():
        corr.setdefault(r[FIX], []).append((name, r))

def short(r, cols):
    return ' | '.join(f'{c[:18]}={r[c]}' for c in cols if c in r.index and not pd.isna(r[c]))

out_rows = []
for _, k in K.iterrows():
    b = k['Başvuru ID']; code = k[KC]; stage = k['Aşama kodu']
    flags = []
    if code not in ('OLUMSUZ', 'KABUL', 'DEVAM_EDIYOR'):
        flags.append(f'TANIMSIZ_KARAR_KODU:{code}')
    if code != 'OLUMSUZ':
        out_rows.append((b, code, stage, flags, k)); continue
    dids = ids(k[DAY])
    if not dids:
        flags.append('KARAR_DAYANAGI_BOS')
    for d in dids:
        if d not in src:
            flags.append(f'DAYANAK_YOK:{d}'); continue
        t, r = src[d]
        if r['Başvuru ID'] != b:
            flags.append(f'BASKA_BASVURU_DAYANAGI:{d}->{r["Başvuru ID"]}')
        if SHARE in r.index and r[SHARE] == 'KURUM_ICI':
            flags.append(f'DAYANAK_KURUM_ICI:{d}')
        if d in corr:
            for ct, cr in corr[d]:
                flags.append(f'DAYANAK_DUZELTILDI:{d}->{cr["Kayıt ID"]}')
        if t == 'SN':
            if r['Doğru sayısı'] + r['Yanlış sayısı'] + r['Boş sayısı'] != r['Soru sayısı']:
                flags.append(f'SINAV_TOPLAM_TUTMUYOR:{d}')
            exp = 'GECTI' if r['Doğru sayısı'] >= r['Geçmek için gereken doğru sayısı'] else 'GECEMEDI'
            if exp != r['Sınav bölümünün sonucu (kod)']:
                flags.append(f'SINAV_SONUC_BARAJ_CELISKI:{d}')
            if r['Sınav bölümünün sonucu (kod)'] == 'GECTI':
                flags.append(f'GECILEN_BOLUM_DAYANAK:{d}')
        if t == 'DL':
            exp = 'GECTI' if r['İngilizce görüşme puanı'] >= r['Geçmek için gereken puan'] else 'GECEMEDI'
            if exp != r['İngilizce görüşmesinin sonucu (kod)']:
                flags.append(f'DIL_SONUC_BARAJ_CELISKI:{d}')
            if r['İngilizce görüşmesinin sonucu (kod)'] == 'GECTI':
                flags.append(f'GECILEN_GORUSME_DAYANAK:{d}')
        if t == 'AS' and r['Aşama kodu'] != stage:
            flags.append(f'DAYANAK_ASAMA_FARKLI:{d}:{r["Aşama kodu"]}')
    # stage-specific checks
    stage_rows = A[(A['Başvuru ID'] == b) & (A['Aşama kodu'] == stage)]
    if stage in ('VIDEO', 'GRUP', 'IK_TEKNIK', 'INGILIZCE') and stage_rows.empty:
        flags.append('KARAR_ASAMASINDA_KAYIT_YOK')
    if (stage_rows['Aşamanın tamamlanma durumu (kod)'] == 'DEGERLENDIRILIYOR').any():
        flags.append('ASAMA_HALA_DEGERLENDIRILIYOR')
    if stage in ('VIDEO', 'GRUP', 'IK_TEKNIK'):
        notes = I[I['Başvuru ID'] == b]
        if notes.empty:
            flags.append('IK_NOTU_YOK')
        for _, n in notes.iterrows():
            gk = n['İK ret gerekçesinin türü (kod)']; tey = n['Gerekçenin paylaşımı için İK teyidi (kod)']
            if gk not in ('GEREKLILIK_KARSILANMADI', 'KONTENJAN_KISITI'):
                flags.append(f'IK_GEREKCE:{gk}')
            if tey != 'EVET':
                flags.append(f'IK_TEYIT:{tey}')
            if n['Aşama kodu'] != stage:
                flags.append(f'IK_NOT_ASAMA_FARKLI:{n["Aşama kodu"]}')
            for d in ids(n['Gerekçenin dayandığı kayıt ID’leri']):
                if d not in src:
                    flags.append(f'IK_DAYANAK_YOK:{d}'); continue
                t, r = src[d]
                if r['Başvuru ID'] != b:
                    flags.append(f'IK_BASKA_BASVURU:{d}->{r["Başvuru ID"]}')
                if SHARE in r.index and r[SHARE] == 'KURUM_ICI':
                    flags.append(f'IK_DAYANAK_KURUM_ICI:{d}')
                if d in corr:
                    flags.append(f'IK_DAYANAK_DUZELTILDI:{d}')
            if gk == 'KONTENJAN_KISITI':
                flags.append('KONTENJAN')
    # multiple evaluator rows on same etkinlik in decision stage -> possible contradiction
    ev = stage_rows[stage_rows['Beceri kodu'].notna()]
    for eid, g in ev.groupby('Görüşme / görev ID'):
        if len(g) > 1:
            flags.append(f'AYNI_GOREVDE_COKLU_GOZLEM:{eid}:{";".join(g["Kayıt ID"])}')
    out_rows.append((b, code, stage, flags, k))

if mode == 'flags':
    import collections
    c = collections.Counter()
    for b, code, stage, flags, k in out_rows:
        if code == 'OLUMSUZ' or flags:
            print(b, code, stage, flags)
        for fl in flags:
            c[fl.split(':')[0]] += 1
    print(c)

if mode == 'detail':
    want = set(sys.argv[3].split(',')) if len(sys.argv) > 3 else None
    for b, code, stage, flags, k in out_rows:
        if want and b not in want:
            continue
        print('=' * 100)
        print(b, code, stage, 'KARAR_DAYANAK=', k[DAY], 'FLAGS=', flags)
        print('  KARAR NOTU:', k['İK’nın karar / süreç açıklaması'])
        for _, r in S[S['Başvuru ID'] == b].iterrows():
            print('  SN', short(r, ['Kayıt ID', 'Kayıt tarihi', 'Sınav bölümü', 'Doğru sayısı', 'Yanlış sayısı', 'Boş sayısı', 'Geçmek için gereken doğru sayısı', 'Sınav bölümünün sonucu (kod)', SHARE, FIX, FIXT]))
        for _, r in A[A['Başvuru ID'] == b].iterrows():
            print('  AS', short(r, ['Kayıt ID', 'Görüşme / görev ID', 'Kayıt tarihi', 'Aşama kodu', 'Aşamanın tamamlanma durumu (kod)', 'Kaydı oluşturan görevli (kod)', 'Beceri kodu', SHARE, FIX]))
            print('       GÖZLEM:', r['Değerlendiricinin gözlemi / süreç notu'])
            if not pd.isna(r[FIXT]):
                print('       DÜZELTME:', r[FIXT])
        for _, r in D[D['Başvuru ID'] == b].iterrows():
            print('  DL', short(r, ['Kayıt ID', 'Kayıt tarihi', 'İngilizce görüşme puanı', 'Geçmek için gereken puan', 'İngilizce görüşmesinin sonucu (kod)', SHARE]))
            print('       GÖZLEM:', r['Değerlendiricinin gözlemi / süreç notu'])
        for _, r in I[I['Başvuru ID'] == b].iterrows():
            print('  IK', short(r, ['Kayıt ID', 'Kayıt tarihi', 'Aşama kodu', 'İK ret gerekçesinin türü (kod)', 'Beceri kodu', 'Gerekçenin dayandığı kayıt ID’leri', 'Gerekçenin paylaşımı için İK teyidi (kod)']))
            print('       GEREKÇE:', r['İK tarafından kaydedilen ret gerekçesi'])
            print('       PAYLAŞIM AÇ.:', r['İK’nın paylaşılabilecek bilgilere ilişkin açıklaması'])
            if not pd.isna(r['Kurum içi not — dış paylaşıma kapalı']):
                print('       KURUM İÇİ:', r['Kurum içi not — dış paylaşıma kapalı'])
