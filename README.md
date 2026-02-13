# Karaoke Generator

Generate Aegisub-compatible .ass karaoke subtitles from lyric.json files.

## Examples
- Machine Love: [Video](http://youtu.be/sVjO3nAIKow)
- Birdbrain: [Video](https://youtu.be/0iVlSNpq8i8)

## Quick start

```bash
python -m src \
  --input "Lyrics/Birdbrain/lyric.json" \
  --output "Lyrics/Birdbrain/lyrics.ass" \
  --config "config.example.json"
```

## Options

- `--config`: path to a JSON file to override styles, margins, and colors.

## Notes

- The generator expects syllable timing in seconds.
- Current line uses karaoke timing; next line is displayed as a guide.
- For Japanese lyrics, romaji is generated automatically when `pykakasi` is available.
- `next_show_before_seconds` controls how early the next line appears and how long the previous line remains during gaps.
- Style overrides can include `fade_in_ms` and `fade_out_ms` to fade text in/out.

## YouTube styling constraints

- Subtitle styling is designed to be compatible with [YTSubConverter](https://raw.githubusercontent.com/arcusmaximus/YTSubConverter/refs/heads/master/README.md).

## Config schema

The config structure is described by [config.schema.json](config.schema.json). The example config already references it via `$schema`.

## Dependency

```bash
pip install -r requirements.txt
```
