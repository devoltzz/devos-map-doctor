# Devo's Map Doctor

A desktop tool for Warcraft III maps. It opens protected maps, repairs what stops them on Reforged 3.0, rebuilds the
World Editor files, ports the maps of the Chinese KK and Korean M16 platforms, and shows what a map carries before
anything is written. It never runs the game.

## Download

Get `DevosMapDoctor.exe` and `names.npz` from [Releases](https://github.com/devoltzz/devos-map-doctor/releases) and keep
them in the same folder. Nothing to install; the program tells you when a new version is out.

## What it does

- **Fix map**: removes the protection and repairs the map (fake file tables, scrambled ids, data the 3.0 engine
  refuses, broken SLK tables, models that crash the game, portrait cameras, data pointers, ability lists, single
  player), with extras for the map card, the translation and the size.
- **Open in World Editor**: writes a copy the editor opens, with the GUI triggers rebuilt from the script when the
  round trip proves them.
- **Port to Reforged**: KK, KKWE, DzAPI, YDWE and j2b maps get their natives implemented and their scripts back in JASS.
- **Tabs**: map card, "Runs on Reforged?", files (previews, raw codes), script and its checks, triggers, translation
  export and import, compare two versions, cheat packs.

## Limits

Nothing touches the file you opened: a new one is written next to it, and every output is checked file by file. Some
protections can only be partly undone; the report says what was left. Test the map in game before sharing it.

## Building

`pip install -r requirements.txt`, then `python build.py` writes `dist/DevosMapDoctor.exe`. Third-party code is listed
in `THIRD_PARTY_NOTICES.md`.

## Problems

Use "Report a problem" in the window: it opens an issue here with the report filled in.
