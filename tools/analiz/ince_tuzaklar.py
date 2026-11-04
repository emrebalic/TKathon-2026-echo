import sys, re, pandas as pd
sys.stdout.reconfigure(encoding='utf-8')
pd.set_option('display.width', 250); pd.set_option('display.max_colwidth', 120); pd.set_option('display.max_rows', 300)
f = sys.argv[1]
K = pd.read_excel(f, 'Başvuru Kararları'); L = pd.read_excel(f, 'Başvuru Listesi'); A = pd.read_excel(f, 'Aşama Kayıtları')
S = pd.read_excel(f, 'Sınav Sonuçları'); D = pd.read_excel(f, 'İngilizce Görüşme Sonuçları'); I = pd.read_excel(f, 'İK Değerlendirme Notları')
P = pd.read_excel(f, 'Program Aşamaları'); IL = pd.read_excel(f, 'İlanlar')
KC = 'İK’nın kaydettiği başvuru sonucu (kod)'; OBS = 'Değerlendiricinin gözlemi / süreç notu'
KD = 'Kararın dayandığı kayıt ID’leri'; ID_ = 'Gerekçenin dayandığı kayıt ID’leri'
print(P[['Aşama kodu', 'Sıra', 'Aşama adı']].to_string())
close = IL['Kapanış tarihi'].iloc[0]; pub = IL['Yayın tarihi'].iloc[0]
print('\nBaşvuru tarihi aralığı', L['Başvuru tarihi'].min(), L['Başvuru tarihi'].max(), 'ilan', pub, close)
print('Kapanıştan sonra:', L[L['Başvuru tarihi'] > close]['Başvuru ID'].tolist(), ' yayından önce:', L[L['Başvuru tarihi'] < pub]['Başvuru ID'].tolist())
print('Başvuru günleri:', {str(k): v for k, v in L['Başvuru tarihi'].dt.date.value_counts().sort_index().items()})

m = K.merge(I[['Başvuru ID', ID_, 'Aşama kodu', 'Beceri kodu', 'İK tarafından kaydedilen ret gerekçesi', 'Kayıt tarihi']], on='Başvuru ID', how='left', suffixes=('', '_ik'))
neg = m[m[KC] == 'OLUMSUZ']
mm = neg[neg[ID_].notna() & (neg[KD] != neg[ID_])]
print('\nKarar dayanağı != İK dayanağı:', mm[['Başvuru ID', KD, ID_]].values.tolist())
print('İK not aşaması != karar aşaması:', neg[neg['Aşama kodu_ik'].notna() & (neg['Aşama kodu'] != neg['Aşama kodu_ik'])][['Başvuru ID', 'Aşama kodu', 'Aşama kodu_ik']].values.tolist())
AS = A.set_index('Kayıt ID')
bad = []; mis = []
for _, r in neg.iterrows():
    g = r['İK tarafından kaydedilen ret gerekçesi']
    for d in str(r[ID_]).split(';'):
        if d in AS.index:
            if pd.notna(r['Beceri kodu']) and AS.loc[d, 'Beceri kodu'] != r['Beceri kodu']:
                bad.append((r['Başvuru ID'], d, AS.loc[d, 'Beceri kodu'], r['Beceri kodu']))
            mt = re.search(r'Görev: ([^.]+)\.', AS.loc[d, OBS])
            if pd.notna(g) and mt and mt.group(1).strip().lower()[:25] not in g.lower():
                mis.append((r['Başvuru ID'], d, mt.group(1)))
print('İK beceri != gözlem beceri:', bad)
print('Gözlem görevi İK gerekçesinde yok:', mis)
ev = []
for _, r in neg.iterrows():
    for d in str(r[KD]).split(';'):
        for df in (A, S, D):
            x = df[df['Kayıt ID'] == d]
            if len(x) and x.iloc[0]['Kayıt tarihi'] > r['Kayıt tarihi']:
                ev.append((r['Başvuru ID'], d, 'dayanak karardan sonra'))
    if pd.notna(r['Kayıt tarihi_ik']) and r['Kayıt tarihi_ik'] < r['Kayıt tarihi']:
        ev.append((r['Başvuru ID'], 'IK notu karardan önce', str(r['Kayıt tarihi_ik']), str(r['Kayıt tarihi'])))
print('Tarih anomalileri:', ev)
cor = pd.concat([A[A['Bu kaydın düzelttiği eski kayıt ID'].notna()][['Kayıt ID', 'Başvuru ID', 'Kayıt tarihi']],
                 S[S['Bu kaydın düzelttiği eski kayıt ID'].notna()][['Kayıt ID', 'Başvuru ID', 'Kayıt tarihi']]])
cor = cor.merge(K[['Başvuru ID', 'Kayıt tarihi']], on='Başvuru ID', suffixes=('', '_karar'))
cor['saat_fark'] = (cor['Kayıt tarihi'] - cor['Kayıt tarihi_karar']).dt.total_seconds() / 3600
print('\nDüzeltme - karar saat farkı:\n', cor.to_string())
K['gun'] = K['Kayıt tarihi'].dt.strftime('%m-%d')
print('\nKarar günü x aşama:\n', pd.crosstab(K['Aşama kodu'], K['gun']))
print('\nİK notu günü - karar günü:', (neg['Kayıt tarihi_ik'] - neg['Kayıt tarihi']).dt.total_seconds().div(3600).round(1).value_counts().to_dict())
print('\nTam barajda GECTI sınav:', S[S['Doğru sayısı'] == S['Geçmek için gereken doğru sayısı']][['Kayıt ID', 'Doğru sayısı']].values.tolist())
print('Bir eksik GECEMEDI:', S[S['Doğru sayısı'] == S['Geçmek için gereken doğru sayısı'] - 1][['Kayıt ID', 'Doğru sayısı']].values.tolist())
print('DL tam baraj:', D[D['İngilizce görüşme puanı'] == 12]['Kayıt ID'].tolist(), ' DL 10-11:', D[D['İngilizce görüşme puanı'].between(10, 11)][['Kayıt ID', 'İngilizce görüşme puanı']].values.tolist())
print('\nBeceri kullanımı AS', A['Beceri kodu'].value_counts().to_dict(), ' IK', I['Beceri kodu'].value_counts().to_dict())
negm = re.compile(r'belirtmedi|açıklamadı|açıklayamadı|vermedi|eklemedi|yalnız|tekrarladı|veremedi|aktardı', re.I)
order = {'SINAV': 1, 'VIDEO': 2, 'GRUP': 3, 'INGILIZCE': 4, 'ENVANTER': 5, 'IK_TEKNIK': 6, 'TEKLIF': 7, 'BELGE': 8}
pas = []
for _, k in K[K[KC] == 'OLUMSUZ'].iterrows():
    rows = A[(A['Başvuru ID'] == k['Başvuru ID']) & A['Beceri kodu'].notna()]
    for _, r in rows.iterrows():
        if order[r['Aşama kodu']] < order[k['Aşama kodu']] and negm.search(r[OBS]):
            pas.append((k['Başvuru ID'], k['Aşama kodu'], r['Kayıt ID'], r[OBS][:120]))
print('\nGeçilmiş aşamada olumsuz ifadeli gözlem:', len(pas))
for p in pas: print('  ', p)
for code in ['DEVAM_EDIYOR', 'KABUL']:
    ids = K[K[KC] == code]['Başvuru ID']
    rows = A[A['Başvuru ID'].isin(ids) & A['Beceri kodu'].notna()]
    print(f'\n{code}: olumsuz ifadeli gözlem', rows[rows[OBS].str.contains(negm)][['Başvuru ID', 'Kayıt ID', 'Aşama kodu']].values.tolist())
    print(f'{code} DEGERLENDIRILIYOR kayıtları:', A[A['Başvuru ID'].isin(ids) & (A['Aşamanın tamamlanma durumu (kod)'] == 'DEGERLENDIRILIYOR')][['Başvuru ID', 'Aşama kodu']].values.tolist())
def tmpl(t):
    if 'ikinci değerlendirici' in t: return 'ikinci_degerlendirici'
    if 'Bu gözlem yalnız bu soru' in t or 'Gözlem bu görüşmeyle sınırlıdır' in t: return 'olumsuz_sinirli'
    if 'örneğinde kendi görevinin' in t: return 'olumlu_ornek'
    if 'beklentisi bu görevde karşılandı' in t: return 'olumlu_isbirimi'
    if 'önerisini sundu' in t: return 'olumlu_grup'
    return 'diger'
ev_ = A[A['Beceri kodu'].notna()].copy(); ev_['sablon'] = ev_[OBS].map(tmpl)
ev_ = ev_.merge(K[['Başvuru ID', KC, 'Aşama kodu']], on='Başvuru ID', suffixes=('', '_karar'))
ev_['karar_asamasi'] = ev_['Aşama kodu'] == ev_['Aşama kodu_karar']
print('\nŞablon x (karar, karar aşaması mı):\n', pd.crosstab(ev_['sablon'], [ev_[KC], ev_['karar_asamasi']]))
print(ev_[ev_['sablon'] == 'diger'][OBS].str[:100].value_counts().to_string())
print('\nKurum içi notlar:\n', I[I['Kurum içi not — dış paylaşıma kapalı'].notna()][['Kayıt ID', 'Kurum içi not — dış paylaşıma kapalı']].to_string())
print('\nKişilik/seviye kelimeleri:', A[A[OBS].str.contains(r'kişilik|seviye|CEFR|B2|içine kapanık|uyum', case=False, regex=True)][['Kayıt ID', 'Aşama kodu']].values.tolist())
print('İK gerekçesinde uyum/iletişim:', I[I['İK tarafından kaydedilen ret gerekçesi'].astype(str).str.contains('uyum|kişilik|iletişim', case=False)]['Kayıt ID'].tolist())
print('\nDL gözlem şablonları:', D[OBS].str[:60].value_counts().to_dict())
