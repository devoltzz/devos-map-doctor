# Devo's Map Doctor

Removes the protection from Warcraft III maps, makes protected maps open in the World Editor again, and ports maps
made for the KK and M16 platforms to Warcraft III 3.0.

## Download

Get `DevosMapDoctor.exe` and `names.npz` from [Releases](https://github.com/devoltzz/devos-map-doctor/releases) and keep
them in the same folder. There is nothing to install, and the program lets you know when a new version is out.
`names.npz` is the file name index: with it, the Doctor names more of the files it finds in maps whose file tables are
damaged (the program offers to download it when it's missing).

## Speed

1.5.5 decodes the sound compression of the archive (the Huffman tables of the imported music and sounds) with a
lookup table instead of one bit at a time, and every archive block is checked once per job instead of several times.
A map whose content is mostly imported sound (a 94 MB map of music) takes about half the time it took in 1.5.4.

1.5.4 counts a file name repeated in the file table as one name, so maps whose table the Doctor itself grew no
longer end up as "partially fixed", and the translation export no longer slows down on maps with very long lines.

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

New in 1.5.7: the "Cheatpacks" tab.

- It injects one of the cheat packs of `common/cheatpacks` (JJCP NewGen, NZCP, Devo's CP and OzzyCP) into the map
  script, always obfuscated, and writes the edited script back into the map with `mpqadd` (the file is not rebuilt).
  A Lua map is only offered the Lua packs, a JASS map only the JASS ones.
- The activation of each pack is yours: the page shows the options the pack itself documents (the activation string, the
  arrow sequence, the player name that activates it, the command prefix, the key sequence...) with the pack's own
  defaults, and the ones you set are written into the pack before it goes in.
- JASS: the pack goes into the map's globals, its functions before the map's `main` and its start-up call inside `main`
  (pjass is not able to call a function declared further down, so the order matters), and the whole script then goes
  through the release obfuscator (`ofusca_jass.py`: no comment, every name renamed, every string and raw code
  encrypted and decrypted as the first instruction of `main`), with pjass checking the result.
- Lua: the OzzyCP body already is an obfuscated build; the comments (including the header that explains the options,
  which the page shows instead) are taken out, and the code is proved untouched by comparing the parsed form before and
  after.
- The syntax of the injected script is checked either way, and the map is only written when it passes. Test the map in
  game before sharing it: the Doctor does not run the game.

New in 1.5.6, offered when the map needs it:

- Give the models their name back: maps protected with the "Model_Encrypt" tool have their imported models renamed
  (`Foo.mdx` becomes `Foo体.mdx`) and the map rewritten to cite the new name, so a tool that looks for the model by the
  name it had finds nothing. The Doctor renames them back (the portrait of each model goes along) and rewrites every
  file that cites them.

New in 1.5.3, offered when the map needs them:

- Fix black portraits: removes the old camera from the portrait models reported to show a black portrait on 3.0
  (check in game).
- Fix the levelled data pointers: an object field whose levels point to different data columns gets the column its
  other levels use.
- Move the unit ability lists to the script: the normal ability lists of the unit types are given to each unit by the
  script as it is created. Players report that lists with about 2,000 distinct abilities drop games on Reforged (check
  in game, and test the map before sharing it).
- Load the first seconds under the loading screen: the units and abilities the map uses right after the start are
  loaded before play begins, so the game does not freeze then (check in game).

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
- Runs on Reforged?: what the archive has measured that stops a map on Warcraft III 3.0, now also the portrait models
  with an old camera, the levelled data pointers, long unit ability lists and the imported files to look at.
- Files, Script and Triggers: the map's files with a preview and extract, the script with export, the trigger tree.
  The files tab marks each imported file the World Editor would drop, the game would never load, or that replaces a
  game file. Script checks lists the handle leaks of a JASS script by how often the code runs, the start-up functions
  it never calls and the globals it never sets.
- Translation: every text a player sees in one file to translate, and the translation loaded back with the checks.
  The export can also be an HTML page for machine translation (Google Translate, DeepL): the color codes and line
  breaks are marked so the translator leaves them alone, and the translated page loads back with the same checks.
- Compare: what changed between two versions of a map.

## KK platform maps

Maps made for the KK platform work too. When the script is compiled (KKWE, `kkmap.jc`) or compiled and encrypted
(j2b, `war3map.bin`), button 3 first turns it back into JASS, and only accepts the result if compiling it again
gives the same instructions the map had.

One protection is left out: maps the platform encrypts outside the archive. That file only holds a loader, the real
map can only be decrypted by the KK client, and the Doctor tells you so instead of trying anything.

## Port to Reforged

Maps made for the Chinese KK platform (DzAPI, japi) and for the Korean M16/JN platform call functions that only exist
on those platforms, and Warcraft III 3.0 refuses to load them. The Port to Reforged tab turns such a map into one that
runs on 3.0 and saves `<map>_reforged.w3x` next to it, with `<map>_reforged.report.txt`.

What the port does:

- the platform functions get a body written in JASS: the platform save becomes a local save that every player loads
  without desyncing, the platform frames become game frames, and the shop, level and VIP queries answer as a player
  with everything unlocked would see them
- a compiled script (KKWE, j2b) is turned back into JASS first, and proved
- the code that would desync a multiplayer game on 3.0 is fixed, and the data tables of SLK maps too
- the script that comes out has to pass pjass, the JASS checker, with the game scripts, or the port stops and says why
- the memory hacks of patch 1.2x (JN maps that read and write the memory of the old game): the typecasts and the
  special effect functions get their Reforged equivalent; with "Neutralize memory hacks" ticked (the default), what
  only the old game's memory did stops working and the map compiles, and the report lists what was neutralized
- the report warns when the unit ability lists are long enough to drop games, and lists the Script checks of the
  ported script

Some platform functions have no equivalent on 3.0 (the platform shop, the online ranking): they stay as stubs that
compile and return an empty value. The report lists each stub the map calls, with the functions and triggers that
call it, so you know which features to check in game.

Some maps ask for art that only the platform client has (its `.mix`, `.asi` or `.mpq` packages). Add those packages
to the port and the art the map asks for is imported from them. The packages are read as data, never run.

Warcraft III 3.0 has to be installed: the port reads the game scripts from it.

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

`names.npz` is not in the repository: download it from the latest release into this folder. The port checks scripts with
[pjass](https://github.com/lep/pjass): put `pjass.exe` in `doctor/script/` (or point the `PJASS` variable to it) and
`build.py` bundles it. `build.py` writes `dist/DevosMapDoctor.exe` and copies `names.npz` next to it. To publish, create
a release tagged with the version (`v1.0`) and attach both files; the updater reads the latest release.

## Credits

MPQ handling follows [StormLib](https://github.com/ladislav-zezula/StormLib) by Ladislav Zezula, and the PKWARE and
WAVE decompressors are ports of its code (see `THIRD_PARTY_NOTICES.md`).
