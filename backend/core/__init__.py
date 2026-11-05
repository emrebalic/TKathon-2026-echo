"""Geri bildirim MVP'sinin veri ve kural katmanı."""
import os
from pathlib import Path

from dotenv import load_dotenv

load_dotenv(Path(__file__).resolve().parents[2] / ".env")

# İstemde, model girdisinde ve çeviride geçen program adı; `.env` içinde PROGRAM_ADI ile değiştirilir.
PROGRAM_ADI = os.environ.get("PROGRAM_ADI", "Genç Yetenek Programı")
