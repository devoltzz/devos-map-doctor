# Devo's Map Doctor

Removes the protection from Warcraft III maps and makes protected maps open in the World Editor again.

## Download

Get `DevosMapDoctor.exe` and `names.npz` from [Releases](https://github.com/devoltzz/devos-map-doctor/releases) and keep
them in the same folder. There is nothing to install, and the program lets you know when a new version is out.
`names.npz` is the file name index: with it, the Doctor names more of the files it finds in maps whose file tables are
damaged (the program offers to download it when it's missing).

## Usage

Open a map, or drag it onto the window or onto the exe. It is checked right away, and the header shows what was
found. Your original map is never changed: each result is saved as a new file next to it.

The check finds:

- a tampered or fake MPQ header, or a missing map header (why MPQ Editor opens the map read-only, or not at all)
- file tables that are scrambled, virtual or full (SProtect, PG2 and the like)
- fake files by the thousand, decoy names and files only the game can read
- scrambled object ids
- a script compiled for the KK platform
- data tables of an old SLK map that Warcraft III 3.0 no longer accepts
- what would stop the World Editor: missing editor files, counters inflated to hang it while loading, doodads whose
  id doesn't exist
- a file that is damaged rather than protected: a download that was cut short, or a copy taken from a compressed
  NTFS folder

### Fix map

Saves `<map>_fixed.w3x`: without the protection (MPQ Editor opens it in edit mode) and with what Warcraft III 3.0 no
longer accepts fixed. The extras, when you tick them: the imported models that crash the game, single player for maps
that end the game when played alone, your map card changes, a translation, and a smaller map that loses nothing.

### Open in World Editor

Saves `<map>_editor.w3x`. The triggers come back as GUI triggers you can click through (events, conditions and
actions), grouped by what fires them. A trigger only goes back as GUI when writing it back to script gives exactly
the code the map had. Otherwise it stays as custom text with its original code.

The rest of the script goes into the custom script, and the units, items, regions, cameras and sounds the script
creates are placed in the map, so the editor shows them. The map is saved with JassHelper turned on, which the World
Editor needs to build the script again.

It works with JASS and Lua maps, with scripts renamed by an obfuscator and with scripts a map optimizer squeezed into
`main`.

Every step of both actions is an option. The steps the World Editor cannot do without are locked and say why; the
defaults are the recommended ones, and presets keep your own choices.

### The other tabs

- Map card: name, author, description, loading screen, players and teams, minimap and preview, with a preview of the
  color codes and a gradient tool. What the map says about itself: chat commands, where it saves, its language.
- Runs on Reforged?: what the archive has measured that stops a map on Warcraft III 3.0.
- Files, Script and Triggers: the map's files with a preview and extract, the script with export, the trigger tree.
- Translation: every text a player sees in one file to translate, and the translation loaded back with the checks.
- Compare: what changed between two versions of a map.

## KK platform maps

Maps made for the KK platform work too. When the script is compiled (KKWE, `kkmap.jc`) or compiled and encrypted
(j2b, `war3map.bin`), button 3 first turns it back into JASS, and only accepts the result if compiling it again
gives the same instructions the map had.

One protection is left out: maps the platform encrypts outside the archive. That file only holds a loader, the real
map can only be decrypted by the KK client, and the Doctor tells you so instead of trying anything.

## Old SLK maps

Maps saved in SLK mode (KKWE, YDWE, w3x2lni) carry their own data tables, and Warcraft III 3.0 no longer accepts
some of what they hold: model paths in the `file` column (the game crashes when the first unit is created), ability
tables that stop at level 4, half written button positions, a stray `*/` in a frame file, ability lists ending in
`|n`. Buttons 2 and 3 fix these in the copy they save and change nothing else in those tables.

## Limits

File names a protector removed only come back when the map itself mentions them, or when the file gives them away (a
disabled button icon, the name a model carries inside). The World Editor drops unnamed files when it saves, and
button 3 tells you how many are left.

## Command line

```
DevosMapDoctor.exe --text map.w3x [--unprotect] [--editor]
```

## Building

```
pip install -r requirements.txt
python DevosMapDoctor.py
python build.py
```

`names.npz` is not in the repository: download it from the latest release into this folder. `build.py` writes
`dist/DevosMapDoctor.exe` and copies `names.npz` next to it. To publish, create a release tagged with the version
(`v1.0`) and attach both files; the updater reads the latest release.

## Credits

MPQ handling follows [StormLib](https://github.com/ladislav-zezula/StormLib) by Ladislav Zezula, and the PKWARE and
WAVE decompressors are ports of its code (see `THIRD_PARTY_NOTICES.md`).
