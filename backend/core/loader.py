"""Excel dosyasını okur ve sayfaları teknik sütun adlarıyla DataFrame olarak döndürür."""
from dataclasses import dataclass, field

import pandas as pd

from core.schema import CODE_FIELDS, COLUMNS, ID_FIELDS, REQUIRED_SHEETS, SHEETS, column_lookup, sheet_lookup


@dataclass
class Veri:
    tablolar: dict = field(default_factory=dict)
    hatalar: list = field(default_factory=list)
    uyarilar: list = field(default_factory=list)

    def __getitem__(self, key):
        return self.tablolar[key]

    @property
    def gecerli(self):
        return not self.hatalar


def _temizle(df):
    for col in df.columns:
        if col in ID_FIELDS or col in CODE_FIELDS:
            df[col] = df[col].map(lambda v: None if pd.isna(v) else str(v).strip() or None)
    return df


def yukle(kaynak) -> Veri:
    """`kaynak`: dosya yolu ya da Streamlit'in yüklediği dosya nesnesi."""
    veri = Veri()
    try:
        ham = pd.read_excel(kaynak, sheet_name=None)
    except Exception as exc:  # bozuk ya da Excel olmayan dosya
        veri.hatalar.append(f"Dosya okunamadı: {exc}")
        return veri

    sayfalar = sheet_lookup(ham.keys())
    for key in REQUIRED_SHEETS:
        if key not in sayfalar:
            veri.hatalar.append(f"Zorunlu sayfa bulunamadı: {SHEETS[key]}")

    for key, ad in sayfalar.items():
        df = ham[ad]
        eslesme = column_lookup(key, df.columns)
        eksik = set(COLUMNS[key].values()) - set(eslesme.values())
        if eksik:
            hedef = veri.hatalar if key in REQUIRED_SHEETS else veri.uyarilar
            hedef.append(f"{ad}: eksik sütunlar {sorted(eksik)}")
        df = df[list(eslesme)].rename(columns=eslesme)
        df = df.dropna(how="all")
        veri.tablolar[key] = _temizle(df.reset_index(drop=True))
    return veri
