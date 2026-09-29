# Devo's Map Doctor

Removes the protection from Warcraft III maps and makes protected maps open in the World Editor again.

## Download

Get `DevosMapDoctor.exe` and `names.npz` from [Releases](https://github.com/devoltzz/devos-map-doctor/releases) and keep
them in the same folder. There is nothing to install, and the program lets you know when a new version is out.
`names.npz` is the file name index: with it, the Doctor names more of the files it finds in maps whose file tables are
damaged (the program offers to download it when it's missing).

## Usage

Open a map (or drag it onto the exe) and click one of the buttons:

1. **Diagnose protection** shows what was done to the map. It only reads the file.
2. **Remove protection** saves `<map>_unprotected.w3x`, which MPQ Editor can open and edit.
3. **Make it open in World Editor** saves `<map>_editor.w3x`. The map script goes into the custom script, so keep
   JassHelper enabled when you save.

Your original map is never changed.

Maps encrypted by the KK platform can't be recovered, and file names a protector removed only come back when the map
itself mentions them.

From the command line:

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
