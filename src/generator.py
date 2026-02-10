from __future__ import annotations

from pathlib import Path
from typing import Optional

from .ass_writer import generate_ass
from .config import load_config
from .parser import load_lyrics
from .romanize import auto_romanize


def generate(input_path: str, output_path: str, config_path: Optional[str]) -> None:
    lyrics = load_lyrics(input_path)
    lyrics = auto_romanize(lyrics)

    config = load_config(config_path)
    ass_text = generate_ass(lyrics, config)

    out_path = Path(output_path)
    out_path.write_text(ass_text, encoding="utf-8")
