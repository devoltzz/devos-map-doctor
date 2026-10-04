# Devo's Map Doctor

Opens Warcraft III maps that are protected, repairs what keeps them from running on 3.0, and ports the maps made for
the KK and M16 platforms. It never runs the game: it reads and writes the files of the archive.

## Download

Get `DevosMapDoctor.exe` and `names.npz` from [Releases](https://github.com/devoltzz/devos-map-doctor/releases) and keep
them in the same folder. There is nothing to install, and the program tells you when a new version is out. `names.npz`
is the file name index: with it the Doctor names more of the files inside maps whose tables are damaged. The program
offers to download it when it is missing.

## Using it

Open a map (or drop it on the window) and press one of the two buttons:

- **Fix map** -- takes the protection out and repairs the map: the fake and inflated file tables, the shuffled object
  ids, the doodads and strings the 3.0 engine refuses, the broken SLK tables, the models that crash or hang the game,
  the portraits with an old camera, the levelled data pointers, the unit ability lists, the names a protection tool
  renamed, single player, the translation and the map card.
- **Open in World Editor** -- writes a copy the editor opens, with the GUI triggers rebuilt from the script wherever
  that can be proved.

The tabs show what the map carries before anything is written: the map card, "Runs on Reforged?" (what would stop it on
3.0), the file list, the script (JASS or Lua, with an export button), the triggers, a translation export, a comparison
with another map, the port to Reforged, and **Cheatpacks** (inject one of the packs into the map script, obfuscated).

## Port to Reforged

Maps from the Chinese platforms (KK, KKWE, DzAPI, YDWE, j2b) are ported: the platform natives get an implementation,
the encrypted scripts come back to JASS or Lua, and the art a map asks for can come from the platform's packages.

## Limits

- It repairs; it does not run the map, and nothing it changes touches the file you opened (a new one is written).
- Some protections can only be partly undone (a full file table with no names, a script compiled outside the map): the
  report always says what was left.
- Test the map in game before sharing it.

## Building

`pip install -r requirements.txt`, then `python build.py` for a single `dist/DevosMapDoctor.exe`. The name index is not
in the repository: `build.py` copies `names.npz` from this folder into `dist/`. The program ships StormLib and pjass and
reads the game's `common.j`/`Blizzard.j` for its JASS checks; all of it is listed in `THIRD_PARTY_NOTICES.md`.

## Credits

StormLib (Ladislav Zezula) for the archive work, pjass for the script gate. Found a problem with a map? Use the
"Report a problem" button in the window: it copies the report and opens an issue here.
