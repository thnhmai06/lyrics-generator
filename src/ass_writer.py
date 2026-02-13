from __future__ import annotations

from typing import List

from .config import AssConfig, StyleConfig, ass_style_line
from .model import Line, Lyrics, Syllable


_PUNCTUATION = set([",", ".", "!", "?", ":", ";", ")", "]", "}", "%", "\"", "'", "\u2014", "\u2026"])


def _format_time(seconds: float) -> str:
    total_cs = int(round(seconds * 100))
    cs = total_cs % 100
    total_sec = total_cs // 100
    s = total_sec % 60
    total_min = total_sec // 60
    m = total_min % 60
    h = total_min // 60
    return f"{h}:{m:02d}:{s:02d}.{cs:02d}"


def _escape_ass(text: str) -> str:
    return text.replace("\\", "\\\\").replace("{", "\\{").replace("}", "\\}")


def _needs_space(prev: Syllable, current_text: str, force_space: bool) -> bool:
    if force_space:
        return True
    if prev.is_part_of_word:
        return False
    if current_text and current_text[0] in _PUNCTUATION:
        return False
    return True


def _romanized_spacer(prev: Syllable, current_text: str) -> str:
    if current_text and current_text[0] in _PUNCTUATION:
        return ""
    return " " if prev.is_part_of_word else "  "


def _linear_segments(total_cs: int, count: int) -> List[int]:
    if count <= 0:
        return []
    if count == 1:
        return [total_cs]
    base = total_cs // count
    remainder = total_cs % count
    return [base + (1 if idx < remainder else 0) for idx in range(count)]


def _anchor_x(style: StyleConfig, config: AssConfig) -> int:
    if style.alignment in (1, 4, 7):
        return int(round(style.margin_l))
    if style.alignment in (3, 6, 9):
        return int(round(config.play_res_x - style.margin_r))
    return int(round(config.play_res_x / 2))


def _anchor_y(style: StyleConfig, config: AssConfig) -> int:
    if style.alignment in (7, 8, 9):
        return int(round(style.margin_v))
    if style.alignment in (1, 2, 3):
        return int(round(config.play_res_y - style.margin_v))
    return int(round(config.play_res_y / 2))


def _original_offset(style: StyleConfig | None) -> int:
    if not style:
        return 0
    return max(8, int(round(style.fontsize * 0.6)))


def _build_text(
    syllables: List[Syllable],
    use_romanized: bool,
    karaoke: bool,
    start_offset_cs: int = 0,
) -> str:
    parts: List[str] = []
    prev: Syllable | None = None

    if karaoke and start_offset_cs > 0:
        parts.append(f"{{\\k{start_offset_cs}}}")

    for s in syllables:
        text = s.romanized if use_romanized and s.romanized else s.text
        if prev:
            if use_romanized:
                spacer = _romanized_spacer(prev, text)
                if spacer:
                    text = spacer + text
            else:
                if _needs_space(prev, text, False):
                    text = " " + text
        text = _escape_ass(text)

        if karaoke:
            if prev:
                gap_cs = int(round((s.start - prev.end) * 100))
                if gap_cs > 0:
                    parts.append(f"{{\\k{gap_cs}}}")
            dur_cs = max(1, int(round((s.end - s.start) * 100)))
            leading = len(text) - len(text.lstrip(" "))
            if leading:
                parts.append(" " * leading)
                text = text[leading:]
            if text:
                segments = _linear_segments(dur_cs, len(text))
                for ch, seg in zip(text, segments):
                    parts.append(f"{{\\k{seg}}}{ch}")
        else:
            parts.append(text)
        prev = s

    return "".join(parts)


def _has_non_latin(line: Line) -> bool:
    for s in line.syllables:
        for ch in s.text:
            if ord(ch) > 127 and ch.isalpha():
                return True
    return False


def _style_header() -> str:
    return (
        "Format: Name,Fontname,Fontsize,PrimaryColour,SecondaryColour,OutlineColour,BackColour,"
        "Bold,Italic,Underline,StrikeOut,ScaleX,ScaleY,Spacing,Angle,BorderStyle,Outline,Shadow,"
        "Alignment,MarginL,MarginR,MarginV,Encoding"
    )


def _event_header() -> str:
    return "Format: Layer,Start,End,Style,Name,MarginL,MarginR,MarginV,Effect,Text"


def _dialogue_line(layer: int, start: float, end: float, style: StyleConfig, text: str) -> str:
    return ",".join(
        [
            f"Dialogue: {layer}",
            _format_time(start),
            _format_time(end),
            style.name,
            "",
            str(style.margin_l),
            str(style.margin_r),
            str(style.margin_v),
            "",
            text,
        ]
    )


def _override_tag(style: StyleConfig, x: int, y: int) -> str:
    parts = [f"\\pos({x},{y})"]
    fade_in = int(round(max(0.0, style.fade_in_ms)))
    fade_out = int(round(max(0.0, style.fade_out_ms)))
    if fade_in or fade_out:
        parts.append(f"\\fad({fade_in},{fade_out})")
    return "{" + "".join(parts) + "}"


def _end_with_fade(end: float, style: StyleConfig) -> float:
    fade_out_s = max(0.0, style.fade_out_ms) / 1000.0
    return end + fade_out_s


def _get_style(styles: dict[str, StyleConfig], *keys: str) -> StyleConfig:
    for key in keys:
        if key in styles:
            return styles[key]
    raise KeyError("No matching style keys found")


def generate_ass(lyrics: Lyrics, config: AssConfig) -> str:
    styles = config.styles
    current_lower = _get_style(
        styles,
        "latin_bottom",
        "latin_lower",
        "current_lower",
        "current_bottom",
        "current",
    )
    current_upper = _get_style(
        styles,
        "latin_top",
        "latin_upper",
        "current_upper",
        "current_top",
        "current",
    )
    original_below_lower = (
        styles.get("original_below_bottom")
        or styles.get("original_below_lower")
        or styles.get("original_above_lower")
        or styles.get("original")
    )
    original_below_upper = (
        styles.get("original_below_top")
        or styles.get("original_below_upper")
        or styles.get("original_above_upper")
        or styles.get("original")
    )
    background_style = styles.get("background") or styles.get("original_top")

    out: List[str] = []
    out.append("[Script Info]")
    out.append("ScriptType: v4.00+")
    out.append(f"PlayResX: {config.play_res_x}")
    out.append(f"PlayResY: {config.play_res_y}")
    out.append("ScaledBorderAndShadow: yes")
    out.append(f"WrapStyle: {config.wrap_style}")
    out.append("Timer: 100.0000")
    out.append("")

    out.append("[V4+ Styles]")
    out.append(_style_header())
    style_list = [current_lower, current_upper]
    if original_below_lower:
        style_list.append(original_below_lower)
    if original_below_upper:
        style_list.append(original_below_upper)
    if background_style:
        style_list.append(background_style)
    seen = set()
    for style in style_list:
        if style.name in seen:
            continue
        seen.add(style.name)
        out.append(f"Style: {ass_style_line(style)}")
    out.append("")

    out.append("[Events]")
    out.append(_event_header())

    line_list = list(lyrics.lead_lines)
    meta = []
    use_upper = True
    last_end_top = 0.0
    last_end_bottom = 0.0
    for idx, line in enumerate(line_list):
        has_romanized = any(s.romanized for s in line.syllables)
        non_latin = _has_non_latin(line)
        use_romanized = non_latin and has_romanized
        display_start = max(0.0, line.start - config.next_show_before_seconds)
        if idx > 0:
            gap = line.start - line_list[idx - 1].end
            if gap > config.next_show_before_seconds:
                use_upper = True
            elif config.alternate_positions:
                use_upper = not use_upper
        current_style = current_upper if use_upper else current_lower
        if use_upper:
            display_start = max(display_start, last_end_top)
        else:
            display_start = max(display_start, last_end_bottom)

        original_style = None
        if non_latin and has_romanized:
            original_style = original_below_upper if use_upper else original_below_lower
        current_end = _end_with_fade(line.end, current_style)
        original_end = _end_with_fade(line.end, original_style) if original_style else line.end
        effective_end = max(current_end, original_end)

        if use_upper:
            last_end_top = max(last_end_top, effective_end)
        else:
            last_end_bottom = max(last_end_bottom, effective_end)

        meta.append(
            (
                has_romanized,
                non_latin,
                use_romanized,
                use_upper,
                current_style,
                display_start,
                current_end,
                original_style,
                original_end,
            )
        )

    for idx, line in enumerate(line_list):
        (
            has_romanized,
            non_latin,
            use_romanized,
            use_upper,
            current_style,
            display_start,
            current_end,
            original_style,
            original_end,
        ) = meta[idx]
        offset_cs = int(round((line.start - display_start) * 100))

        base_x = _anchor_x(current_style, config)
        base_y = _anchor_y(current_style, config)
        original_offset = _original_offset(original_style)
        adjusted_y = base_y

        if use_upper:
            for neighbor in (idx - 1, idx + 1):
                if neighbor < 0 or neighbor >= len(line_list):
                    continue
                (
                    n_has_romanized,
                    n_non_latin,
                    _,
                    n_use_upper,
                    n_style,
                    n_display_start,
                    _,
                    n_original_style,
                    _,
                ) = meta[neighbor]
                if n_use_upper:
                    continue
                n_line = line_list[neighbor]
                if n_display_start >= line.end or n_line.end <= display_start:
                    continue
                n_base_y = _anchor_y(n_style, config)
                n_top = n_base_y - n_style.fontsize
                padding = max(10, int(round(current_style.fontsize * 0.4)))
                adjusted_y = min(adjusted_y, n_top - padding - original_offset)
                break

        current_text = _build_text(
            line.syllables,
            use_romanized,
            karaoke=True,
            start_offset_cs=offset_cs,
        )
        current_text = f"{_override_tag(current_style, base_x, adjusted_y)}{current_text}"
        out.append(_dialogue_line(1, display_start, current_end, current_style, current_text))

        if original_style:
            original_base_y = _anchor_y(original_style, config)
            original_text = _build_text(
                line.syllables,
                False,
                karaoke=True,
                start_offset_cs=offset_cs,
            )
            original_y = max(adjusted_y + original_offset, original_base_y)
            original_text = f"{_override_tag(original_style, base_x, original_y)}{original_text}"
            out.append(_dialogue_line(2, display_start, original_end, original_style, original_text))

    if background_style:
        active_bg: List[tuple[float, int]] = []
        for bg_line in lyrics.background_lines:
            bg_start = max(0.0, bg_line.start - config.next_show_before_seconds)
            bg_end = _end_with_fade(bg_line.end, background_style)
            offset_cs = int(round((bg_line.start - bg_start) * 100))
            bg_text = _build_text(bg_line.syllables, False, karaoke=True, start_offset_cs=offset_cs)
            bg_x = _anchor_x(background_style, config)
            bg_y = _anchor_y(background_style, config)
            padding = max(10, int(round(background_style.fontsize * 0.9)))
            active_bg = [(end, y) for end, y in active_bg if end > bg_start]
            for idx, lead_line in enumerate(line_list):
                if lead_line.end <= bg_start or lead_line.start >= bg_line.end:
                    continue
                (
                    has_romanized,
                    non_latin,
                    _,
                    use_upper,
                    _,
                    _,
                    _,
                    original_style,
                    _,
                ) = meta[idx]
                if not (non_latin and has_romanized):
                    continue
                if not original_style:
                    continue
                original_y = _anchor_y(original_style, config)
                bg_y = min(bg_y, original_y - padding)
            if active_bg:
                highest_y = min(y for _, y in active_bg)
                bg_y = min(bg_y, highest_y - padding)
            bg_y = max(0, bg_y)
            out.append(
                _dialogue_line(
                    3,
                    bg_start,
                    bg_end,
                    background_style,
                    f"{_override_tag(background_style, bg_x, bg_y)}{bg_text}",
                )
            )
            active_bg.append((bg_end, bg_y))

    return "\n".join(out) + "\n"
