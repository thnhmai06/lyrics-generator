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
                count = len(text)
                base = dur_cs // count
                remainder = dur_cs % count
                for idx, ch in enumerate(text):
                    seg = base + (1 if idx < remainder else 0)
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


def _original_pos(
    use_upper: bool,
    current_upper: StyleConfig,
    current_lower: StyleConfig,
    original_style: StyleConfig,
    config: AssConfig,
) -> tuple[int, int]:
    x = _anchor_x(current_upper if use_upper else current_lower, config)
    base_y = _anchor_y(current_upper if use_upper else current_lower, config)
    own_padding = max(8, int(round(original_style.fontsize * 0.6)))
    other_padding = max(14, int(round(original_style.fontsize * 1.1)))
    target_y = base_y + own_padding
    if use_upper:
        lower_y = _anchor_y(current_lower, config)
        target_y = min(target_y, lower_y - other_padding)
    return x, max(0, target_y)


def _get_style(styles: dict[str, StyleConfig], *keys: str) -> StyleConfig:
    for key in keys:
        if key in styles:
            return styles[key]
    raise KeyError("No matching style keys found")


def _append_preview(
    out: List[str],
    line: Line,
    start: float,
    end: float,
    preview_style: StyleConfig,
    use_romanized: bool,
    has_romanized: bool,
    non_latin: bool,
    original_style: StyleConfig | None,
    original_pos: tuple[int, int] | None,
) -> None:
    if end - start <= 0.01:
        return
    preview_text = _build_text(line.syllables, use_romanized, karaoke=False)
    out.append(_dialogue_line(0, start, end, preview_style, preview_text))
    if non_latin and has_romanized and original_style:
        preview_cs = int(round((end - start) * 100))
        original_preview = _build_text(
            line.syllables,
            False,
            karaoke=True,
            start_offset_cs=max(0, preview_cs),
        )
        if original_pos:
            x, y = original_pos
            original_preview = f"{{\\pos({x},{y})}}{original_preview}"
        out.append(_dialogue_line(0, start, end, original_style, original_preview))




def generate_ass(lyrics: Lyrics, config: AssConfig) -> str:
    styles = config.styles
    current_lower = _get_style(styles, "current_lower", "current_bottom", "current")
    current_upper = _get_style(styles, "current_upper", "current_top", "current")
    preview_lower = _get_style(styles, "preview_lower", "preview_bottom", "next")
    preview_upper = _get_style(styles, "preview_upper", "preview_top", "next")
    original_below_lower = (
        styles.get("original_below_lower")
        or styles.get("original_above_lower")
        or styles.get("original")
    )
    original_below_upper = (
        styles.get("original_below_upper")
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
    style_list = [current_lower, current_upper, preview_lower, preview_upper]
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
    for idx, line in enumerate(line_list):
        has_romanized = any(s.romanized for s in line.syllables)
        non_latin = _has_non_latin(line)
        use_romanized = non_latin and has_romanized
        if idx > 0:
            gap = line.start - line_list[idx - 1].end
            if gap > config.next_show_before_seconds:
                use_upper = True
            elif config.alternate_positions:
                use_upper = not use_upper
        current_style = current_upper if use_upper else current_lower
        preview_style = preview_upper if use_upper else preview_lower
        meta.append((has_romanized, non_latin, use_romanized, use_upper, current_style, preview_style))

    for idx, line in enumerate(line_list):
        has_romanized, non_latin, use_romanized, use_upper, current_style, preview_style = meta[idx]

        current_text = _build_text(line.syllables, use_romanized, karaoke=True)
        out.append(_dialogue_line(1, line.start, line.end, current_style, current_text))

        if non_latin and has_romanized:
            original_style = original_below_upper if use_upper else original_below_lower
            if original_style:
                original_text = _build_text(line.syllables, False, karaoke=True)
                x, y = _original_pos(use_upper, current_upper, current_lower, original_style, config)
                original_text = f"{{\\pos({x},{y})}}{original_text}"
                out.append(_dialogue_line(2, line.start, line.end, original_style, original_text))

        if idx + 1 < len(line_list):
            next_line = line_list[idx + 1]
            next_meta = meta[idx + 1]
            next_has_romanized, next_non_latin, next_use_romanized, next_use_upper, _, next_preview_style = next_meta
            next_original_style = original_below_upper if next_use_upper else original_below_lower
            next_original_pos = None
            if next_original_style:
                next_original_pos = _original_pos(
                    next_use_upper,
                    current_upper,
                    current_lower,
                    next_original_style,
                    config,
                )

            preview_start = max(line.start, next_line.start - config.next_show_before_seconds)
            preview_end = min(line.end, next_line.start)
            _append_preview(
                out,
                next_line,
                preview_start,
                preview_end,
                next_preview_style,
                next_use_romanized,
                next_has_romanized,
                next_non_latin,
                next_original_style,
                next_original_pos,
            )

        gap_start = 0.0 if idx == 0 else line_list[idx - 1].end
        gap_end = line.start
        if gap_end > gap_start:
            preview_start = max(gap_start, line.start - config.next_show_before_seconds)
            original_style = original_below_upper if use_upper else original_below_lower
            original_pos = None
            if original_style:
                original_pos = _original_pos(use_upper, current_upper, current_lower, original_style, config)
            _append_preview(
                out,
                line,
                preview_start,
                gap_end,
                preview_style,
                use_romanized,
                has_romanized,
                non_latin,
                original_style,
                original_pos,
            )

    if background_style:
        prev_bg_end = 0.0
        for bg_line in lyrics.background_lines:
            bg_start = max(0.0, bg_line.start - config.next_show_before_seconds)
            offset_cs = int(round((bg_line.start - bg_start) * 100))
            bg_text = _build_text(bg_line.syllables, False, karaoke=True, start_offset_cs=offset_cs)
            bg_x = _anchor_x(background_style, config)
            bg_y = _anchor_y(background_style, config)
            padding = max(10, int(round(background_style.fontsize * 0.9)))
            for idx, lead_line in enumerate(line_list):
                if lead_line.end <= bg_start or lead_line.start >= bg_line.end:
                    continue
                has_romanized, non_latin, _, use_upper, _, _ = meta[idx]
                if not (non_latin and has_romanized):
                    continue
                original_style = original_below_upper if use_upper else original_below_lower
                if not original_style:
                    continue
                _, original_y = _original_pos(use_upper, current_upper, current_lower, original_style, config)
                bg_y = min(bg_y, original_y - padding)
            bg_y = max(0, bg_y)
            out.append(_dialogue_line(3, bg_start, bg_line.end, background_style, f"{{\\pos({bg_x},{bg_y})}}{bg_text}"))

            prev_bg_end = max(prev_bg_end, bg_line.end)

    return "\n".join(out) + "\n"
