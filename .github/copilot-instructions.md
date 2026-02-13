# Copilot Instructions

- Use Python 3.10+.
- Keep code clean and minimal; avoid unnecessary comments.
- Prefer configuration via JSON files in the project root (validate against config.schema.json when relevant).
- Input lyrics from lyric.json and output subtitles in Aegisub-compatible .ass format (UTF-8).
- Respect safe-zone layout for on-screen text and keep margins/alignment consistent with styles.
- Preserve timing semantics: syllable timing is in seconds; current line uses karaoke timing; next line is a guide.
- Keep romaji auto-generation optional; only rely on pykakasi when available.
- Keep subtitle styling compatible with [YTSubConverter](https://raw.githubusercontent.com/arcusmaximus/YTSubConverter/refs/heads/master/README.md).
