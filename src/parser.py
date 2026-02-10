import json
from typing import List, Optional

from .model import Line, Lyrics, Syllable


def _extract_content(data: dict) -> list:
    content = data.get("Content") or []
    return [c for c in content if c.get("Type") == "Vocal" and c.get("Lead")]


def _build_line(source: dict) -> Optional[Line]:
    syllables = []
    for s in source.get("Syllables", []):
        syllables.append(
            Syllable(
                text=str(s.get("Text", "")),
                start=float(s.get("StartTime", 0.0)),
                end=float(s.get("EndTime", 0.0)),
                is_part_of_word=bool(s.get("IsPartOfWord", False)),
            )
        )
    if not syllables:
        return None
    start = float(source.get("StartTime", syllables[0].start))
    end = float(source.get("EndTime", syllables[-1].end))
    return Line(syllables=syllables, start=start, end=end)


def load_lyrics(path: str) -> Lyrics:
    with open(path, "r", encoding="utf-8") as f:
        raw = json.load(f)

    queries = raw.get("queries") or []
    if not queries:
        raise ValueError("No queries in lyric.json")

    data = queries[0].get("result", {}).get("data", {})
    content = _extract_content(data)
    lead_lines: List[Line] = []
    background_lines: List[Line] = []

    for item in content:
        lead = item["Lead"]
        lead_line = _build_line(lead)
        if lead_line:
            lead_lines.append(lead_line)

        for bg in item.get("Background", []) or []:
            bg_line = _build_line(bg)
            if bg_line:
                background_lines.append(bg_line)

    return Lyrics(lead_lines=lead_lines, background_lines=background_lines)
