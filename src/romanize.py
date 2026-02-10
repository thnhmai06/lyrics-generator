from __future__ import annotations

from typing import List, Optional

from .model import Line, Lyrics, Syllable

try:
    from pykakasi import kakasi
except ImportError:  # pragma: no cover
    kakasi = None


def _has_japanese(text: str) -> bool:
    for ch in text:
        code = ord(ch)
        if 0x3040 <= code <= 0x309F:
            return True
        if 0x30A0 <= code <= 0x30FF:
            return True
        if 0x31F0 <= code <= 0x31FF:
            return True
        if 0xFF66 <= code <= 0xFF9D:
            return True
        if 0x4E00 <= code <= 0x9FFF:
            return True
    return False


def _romanize_text(text: str) -> Optional[str]:
    if kakasi is None:
        return None
    kks = kakasi()
    kks.setMode("H", "a")
    kks.setMode("K", "a")
    kks.setMode("J", "a")
    converter = kks.getConverter()
    return converter.do(text)


def _romanize_lines(lines: List[Line]) -> List[Line]:
    updated: List[Line] = []
    for line in lines:
        syllables: List[Syllable] = []
        for s in line.syllables:
            romanized = s.romanized
            if romanized is None and _has_japanese(s.text):
                romanized = _romanize_text(s.text)
            syllables.append(
                Syllable(
                    text=s.text,
                    start=s.start,
                    end=s.end,
                    is_part_of_word=s.is_part_of_word,
                    romanized=romanized,
                )
            )
        updated.append(Line(syllables=syllables, start=line.start, end=line.end))
    return updated


def auto_romanize(lyrics: Lyrics) -> Lyrics:
    return Lyrics(
        lead_lines=_romanize_lines(lyrics.lead_lines),
        background_lines=_romanize_lines(lyrics.background_lines),
    )
