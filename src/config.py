from __future__ import annotations

from dataclasses import dataclass, field
import json
from typing import Dict, Optional


@dataclass(frozen=True)
class StyleConfig:
    name: str
    fontname: str = "Roboto"
    fontsize: int = 48
    primary_color: str = "#FFD86B"
    secondary_color: str = "#FFFFFF"
    outline_color: str = "#000000"
    shadow_color: str = "#000000"
    bold: int = 0
    italic: int = 0
    underline: int = 0
    strikeout: int = 0
    scale_x: int = 100
    scale_y: int = 100
    spacing: float = 0.0
    angle: float = 0.0
    border_style: int = 1
    outline: float = 3.0
    shadow: float = 2.0
    alignment: int = 2
    margin_l: int = 120
    margin_r: int = 120
    margin_v: int = 80
    encoding: int = 1


@dataclass(frozen=True)
class AssConfig:
    play_res_x: int = 1920
    play_res_y: int = 1080
    wrap_style: int = 2
    alternate_positions: bool = True
    next_show_before_seconds: float = 3.0
    styles: Dict[str, StyleConfig] = field(default_factory=dict)


def _to_ass_color(value: str) -> str:
    v = value.strip()
    if v.upper().startswith("&H"):
        raw = v[2:]
        if len(raw) == 6:
            return f"&H00{raw}".upper()
        return v.upper()
    if v.startswith("#"):
        v = v[1:]
    if len(v) != 6:
        raise ValueError(f"Invalid color: {value}")
    r = v[0:2]
    g = v[2:4]
    b = v[4:6]
    return f"&H00{b}{g}{r}".upper()


def _build_style(name: str, data: dict, default: StyleConfig) -> StyleConfig:
    merged = {**default.__dict__, **data, "name": name}
    return StyleConfig(**merged)


def default_config() -> AssConfig:
    styles = {
        "latin_bottom": StyleConfig(name="LatinBottom", margin_v=70),
        "latin_top": StyleConfig(name="LatinTop", margin_v=120),
        "original_below_bottom": StyleConfig(name="OriginalBelowBottom", fontsize=34, margin_v=40),
        "original_below_top": StyleConfig(name="OriginalBelowTop", fontsize=34, margin_v=90),
        "background": StyleConfig(name="Background", fontsize=40, primary_color="#FFD86B", secondary_color="#FFFFFF", alignment=2, margin_v=210),
    }
    return AssConfig(styles=styles)


def load_config(path: Optional[str]) -> AssConfig:
    if not path:
        return default_config()
    with open(path, "r", encoding="utf-8") as f:
        raw = json.load(f)

    base = default_config()
    styles = {}
    raw_styles = raw.get("styles", {})
    for key, default_style in base.styles.items():
        style_data = raw_styles.get(key, {})
        style = _build_style(default_style.name, style_data, default_style)
        styles[key] = style

    play_res_x = int(raw.get("play_res_x", base.play_res_x))
    play_res_y = int(raw.get("play_res_y", base.play_res_y))
    wrap_style = int(raw.get("wrap_style", base.wrap_style))
    alternate_positions = bool(raw.get("alternate_positions", base.alternate_positions))
    next_show_before_seconds = float(raw.get("next_show_before_seconds", base.next_show_before_seconds))
    return AssConfig(
        play_res_x=play_res_x,
        play_res_y=play_res_y,
        wrap_style=wrap_style,
        alternate_positions=alternate_positions,
        next_show_before_seconds=next_show_before_seconds,
        styles=styles,
    )


def ass_style_line(style: StyleConfig) -> str:
    return ",".join(
        [
            style.name,
            style.fontname,
            str(style.fontsize),
            _to_ass_color(style.primary_color),
            _to_ass_color(style.secondary_color),
            _to_ass_color(style.outline_color),
            _to_ass_color(style.shadow_color),
            str(style.bold),
            str(style.italic),
            str(style.underline),
            str(style.strikeout),
            str(style.scale_x),
            str(style.scale_y),
            str(style.spacing),
            str(style.angle),
            str(style.border_style),
            str(style.outline),
            str(style.shadow),
            str(style.alignment),
            str(style.margin_l),
            str(style.margin_r),
            str(style.margin_v),
            str(style.encoding),
        ]
    )
