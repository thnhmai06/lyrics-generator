from dataclasses import dataclass
from typing import List, Optional


@dataclass(frozen=True)
class Syllable:
    text: str
    start: float
    end: float
    is_part_of_word: bool
    romanized: Optional[str] = None


@dataclass(frozen=True)
class Line:
    syllables: List[Syllable]
    start: float
    end: float

    @property
    def text(self) -> str:
        return "".join(s.text for s in self.syllables)


@dataclass(frozen=True)
class Lyrics:
    lead_lines: List[Line]
    background_lines: List[Line]
