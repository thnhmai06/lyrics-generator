from __future__ import annotations

import argparse

from .generator import generate


def main() -> None:
    parser = argparse.ArgumentParser(description="Generate karaoke .ass from lyric.json")
    parser.add_argument("-i", "--input", required=True, help="Path to lyric.json")
    parser.add_argument("-o", "--output", required=True, help="Path to output .ass")
    parser.add_argument("--config", default=None, help="Path to JSON config")
    args = parser.parse_args()

    generate(args.input, args.output, args.config)
