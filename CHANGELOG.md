# Changelog

What each version of Devo's Map Doctor brought, the newest first. The downloads are on the
[Releases](https://github.com/devoltzz/devos-map-doctor/releases) page, with the notes of each version.

## 1.10.1 (2026-10-29)

### Fixed

- **Open in World Editor for an older editor (1.24 to 1.29, JassNative):** when the map was protected and an extra ran
  before the editor step, the copy for the old editor got the Reforged data fixes (the models moved to the skin files,
  which the classic game does not read). The old editor now gets the map without them, as it already did without the
  extras.
- **Object files made from the SLK tables for a classic game** came out with their fields in a different order each
  run (the same objects, other bytes). The order is fixed now, so the same map always gives the same file.
- **Fix map on a campaign** whose maps were all ready already ended as "failed" with an empty list. It now saves the
  unprotected campaign.
- **A leftover `.part` file next to your map** when a step failed on Windows (the file was still held open while it was
  removed), and a map named `X.part.w3x` saved as `X.w3x` could be overwritten by its own copy. Both are handled now.
- **An extra that answered "failed" but left a file** was counted as applied.
- **Window:**
  - two settings saves at the same moment could leave the settings file broken, and all settings were lost at the
    next start;
  - a damaged cached diagnosis made every job on that map fail until the map changed;
  - closing the window while a job was running left the `.part` file and the job folder in TEMP;
  - Cancel clicked just as a job finished replaced the saved map with "cancelled";
  - job folders left in TEMP by windows the system closed are removed when the program starts (only folders older
    than a day that no open window uses).
- **Page:**
  - a double click on Fix map, Port or QoL started two jobs on the same map;
  - Cancel of a job the program no longer knew left the page "running";
  - a lobby image picked and then cancelled ran Fix map without it, without a word;
  - the browser's harmless "ResizeObserver loop" notice showed as an error.
- **Site (doctor.devoltz.party):**
  - Cancel removed the files of the earlier jobs, and Download then failed with a read error; it now says why;
  - a read on an engine that was restarted never answered;
  - after a crash of the engine (out of memory), the next jobs went to the same broken engine;
  - a failed zip of the queue said "written".
- **Command line:**
  - `script --to` and `recipes --out` into a folder that does not exist gave a traceback, `script --to` with `--json`
    did not write the file, and a map that failed wrote an empty file;
  - the exported script keeps CRLF line ends when the map has them, and says when it was cut;
  - Ctrl+C or an error while `fix` and `editor` diagnose the map gave a traceback;
  - `files`, `card`, `rawcodes` and `translation groups` on an unreadable map printed nothing;
  - `DevosMapDoctor.exe` started without a console with a path that no longer exists did nothing: it opens the window.
- **Compare:** two long generated scripts took over a minute to compare (50,000 lines: 67 s, now 0.2 s).
- **Linux:** the check for a new version never worked outside Ubuntu (Fedora, Arch, openSUSE): the program did not find
  the system's certificates.

### Changed

- **Command line, the same defaults as the window:**
  - `fix` turns on by itself the extras the window ticks when its check finds them: the models that crash the game,
    the model names, the leveled data pointers, the KK textures, the green icons, the file checksums, the graphics
    modes, the requirements and the frame file lists. `--no-<extra>` leaves one out (`--no-models`);
  - `port` keeps the icons and the textures on, as the window does (`--no-icons`, `--no-textures`).
- **Command line, exit codes:** `diag` of a file that is not a map the Doctor can read (not a map, incomplete,
  unreadable) and `check` whose answer is "no" now exit with 1. `diag --json` says which in `state`.
- **Page:** the dialogs close with Escape and keep the keyboard focus, the notices are read by screen readers, a click
  on the text of an option ticks it, and the page fits a narrow window. The file table says "showing 3000 of N" when it
  cuts, a preview shown as bytes says why, a failed port offers its chain log, and the Triggers tab shows the custom
  script.

## 1.10.0 (2026-10-29)

### Fixed

- **Open in World Editor: 9.7 C03 crashed Warcraft III 1.28.5 at load** (issue 59): the SLK tables the object files are
  made from stayed in the map next to them. The game reads the map's SLK rows as its own objects and then applies the
  object files on top, so each new object was created twice and the game crashed while loading. The tables that were
  converted now leave the map, and what they held goes into the object files: the changes to the game's own objects,
  the rows of a new object the file already had, and the cells the table leaves empty (an empty cell is a value: a new
  unit with no abilities no longer gets its parent's). The 9.7 C03 made this way loads and plays in 1.28.5, and opens
  and saves in the JassNative Editor. A Reforged map keeps its tables as before.
- **Objects measured against the wrong game's tables** (issue 59): the object files made from a classic map's SLK
  tables were compared with Reforged's data. They are now measured against the tables of the game the map is for (the
  editor you chose in "Open in World Editor"; in the SLK option of "Fix map", the version the map was made for), with
  the balance layer the map asks for. I measured that layer in 1.28.5: a custom map uses the custom tables (the Knight
  has 800 hit points), the same map marked melee the melee ones (835). The report says which game it used.
- **JassNative Editor: "Identifier redeclared: nu" when saving** (issue 59): on FOCS ver192 the Doctor renamed a local
  variable named like a function or a global in the trigger text, but not in the map's `war3map.j`, which the editor
  also reads when it saves. It is renamed there too; the name of a local changes nothing in the game.
- **Port between game versions refused maps with a run-time pjass error they already had** (issues 62 and 63): Age of
  Myths 3.7F and Enmity Campaign Beta79b were refused to 1.24a, 1.27b and 1.29.2 because pjass found a local variable
  read before it gets a value. That error is in the original map too, and it does not stop the game from loading the
  script: only the thread that reaches that line stops, as before the port. The port now accepts the map when every
  pjass error is of that kind (a local read before it gets a value, or a text over 1023 characters) and was already in
  the original; the report lists them. Any other error, or one the port made, is still refused. "Runs on 1.2x?" shows
  these as a warning instead of a blocker.

### New

- **Maps made for one graphics mode** (Classic, Reforged or Definitive Edition): "Runs on Reforged?" says which game
  files the map uses are missing in the other modes, and the new "Fix map" option "Make the map work in every graphics
  mode" copies them from the game into the map at the same paths, as many as fit below 512 MB (the terrain first, then
  the models, then the textures); what did not fit is listed. Needs the game installed. A map that uses Definitive
  Edition art (the Lordaeron Capital tiles have no Classic texture at all) can lack 500 files in Classic.
- **KK maps with hidden files** (the "virtual MPQ" of the KK platform, StormLib issue 426): the map keeps most of its
  files after the MPQ archive, encrypted, where no MPQ tool sees them. The diagnosis now counts them, "files" lists
  them with the names the Doctor finds, and "extract --all" writes them (the real script included) under `hidden\`.
  Measured on a map from the KK servers: 5,058 hidden files, 404 MB. A playable copy outside the platform is not made
  from them: the game asks for the files without a known name by their real names.
- **Lua scripts obfuscated by WC3Fuscator 2.1**: the diagnosis names it, and "Open in World Editor" takes the loader
  layers off without running the map, so the script comes back as it was except the local names (they stay
  `__L0`...).
- **"Runs on Reforged?": a Lua script that creates handles while it loads, outside any function** (the desync reported
  by Luashine): a warning when a function later sets the same global again, a note otherwise. Also a note for a map that
  uses the Balnazzar/Tichondrius skin `Udrb`, which the 3.0 game data no longer has.
- **Save games:** `doctor save <file.w3z|file.w3v> [--to=<folder>]` reads a save (the container, its checks, the map
  and the game) and writes its parts.
- **Diagnosis:** a map whose script carries the "Map deprotected by WC3MapRepacker" line is named as repacked by it.
- **Shrink:** the report says why each removed or merged file went (no table entry points to it; the same bytes as
  another file).

### Changed

- **Maps with 512-byte MPQ sectors** are no longer reported as a protection: the MPQ Editor opens them since
  2026-10-03 (StormLib 744ec1d). "Fix map" still rewrites them to the usual sector size.
- **Command line, a versioned `--json`:** every `--json` result now carries `schema` (the contract version, `1`),
  `doctor_version`, `command` and `exit_code` on top of the same keys as before, and a wrong command line or a failed
  job also prints one JSON object (`outcome: "failed"`, `error`, `error_kind`). `doctor --json-schema` (or
  `doctor schema`) prints the contract: each command's options and the result keys with their types, made from the
  tables the command line itself uses. What may change without a new `schema`, and the old option names that keep
  working: [CLI.md](CLI.md). An option a command does not take is now refused everywhere (`files <map> --to=x` ran
  before and ignored it); in fix and editor it stays a warning.
- **Every report line the page shows** is in the 16 languages of the page, including the ones added since 1.9.0.

## 1.9.4 (2026-10-28)

### Fixed

- **Port between game versions, maps whose script ends its lines with a lone carriage return** (issue 61): Regicide
  v2.12 keeps its script with CR line ends and a byte order mark before `globals`, so the port to 1.29.2 and older saw
  the whole script as one line and converted nothing. The script is now prepared the way the port to Reforged already
  did it: to 1.24a, 1.26a, 1.27b, 1.28.5 and 1.29.2 it converts the 29 uses of the return bug and the compiler accepts
  every one.
- **Open in World Editor: abilities shown as "Unknown"** (issue 59): FOCS keeps the levels above 4 of some abilities as
  a change to a game ability that uses the id of a new ability from the map's SLK tables. I took that id as one the map
  already had and did not add the new ability. Those now become the new ability with the changes of the file on top
  (291 on FOCS ver192, 242 on 9.7 C03).

### Changed

- **Port to Reforged (KK and M16 maps):** loading a large local save is faster (a part is checked again only when its
  middle came back short).
- **Translation:** a key that `war3mapMisc.txt` or `war3mapSkin.txt` repeats in more than one section gets its section
  in the id, so each one is translated on its own; a translation made with the old ids still applies.

## 1.9.3 (2026-10-27)

### Changed

- **The line of the sites:** the program no longer shows the small line at the top of the left column that switched
  between the devoltz.party sites; only the site has it now. On the site it gained Home (devoltz.party), it opens the
  other sites in the same tab, and its items are a little narrower. Nothing else changed: the engine is the one of 1.9.1.

## 1.9.2 (2026-10-27)

### Changed

- **The look of the window and the site:** the Doctor now shares its colors, its frame and its buttons with the other
  devoltz.party sites (DevoProtect and the map releases), so the three look like one family. The top of the left
  column has a small line to switch between them (Doctor, Protect, Releases); in the program they open in your
  browser. The site has its own icon in the browser tab. Nothing else changed: the engine is the one of 1.9.1.

## 1.9.1 (2026-10-27)

### Fixed

- **Open in World Editor: the abilities made from the SLK tables, again** (issue 58). A tooltip the map keeps as one
  line split by commas (`Tip=level 1,level 2,level 3`) went whole into level 1 when the list had more parts than the
  ability has levels: on FOCS ver192, tooltips of up to 1,131 characters. Each level now gets its own part, as the game
  reads the list, and no ability gets a value for a level it does not have (983 of them on ver192). The JassNative
  Editor still closed with "not enough memory" on FOCS ver192 made by 1.9.0; the long tooltips were the one thing those
  abilities had that the ones of FOCS3, which opens, did not. I could not run that editor to confirm this was the
  cause.
- **Port to Reforged of maps of 1.23 and older:** 1.9.0 sent the vJass string cast (`SH2I`, a function that returns
  the global that holds its parameter) through the handle table instead of converting it by its type, as 1.8.9 did. It
  is converted by its type again; Regicide v2.12 and Neverwinter Nights RPG v2.2c still pass the compiler gates.
- **Port to Reforged (KK and M16 maps), from the ports of the last days:**
  - the local save of M16 maps writes a value with `;`, a backslash, a quote or a line break as an escaped record with
    no backslash at all (on a Korean RPG such values came back cut, and the backslashes doubled on every save); the
    saves without those characters stay byte for byte the same, and the load reads both;
  - the save records how many records it wrote: a load that comes back with fewer (a save the game cut) is kept for
    the game, and nothing writes over it in that game;
  - the save folder of a KK map: a player name the panel cut (a BattleTag of 6 digits or more) keeps the full account.

## 1.9.0 (2026-10-26)

### New

- **Port to an older game: Reforged 2.0.4.** A map made for Reforged 3.0 can now go back to 2.0.4 (build 23745, the
  last before 3.0), in the Port tab ("Reforged 2.0.4") or with `port <map> --to=2.0.4`. Every map the 3.0 editor
  saves calls natives 2.0.4 does not have, even an empty one (`SetPlayerRaceSkin`, `SetHDWaterParamsEx`), so it does
  not open there as it is. The port gives each native of 3.0 the 2.0.4 equivalent where there is one (the fog, the
  destructables with pitch and colour, the random item drops) and makes the rest neutral, in JASS and in Lua maps; it
  takes out the camera lines of 3.0; it writes the map info, the doodads, the units, the cameras and the regions in the
  formats 2.0.4 reads; it takes out the object fields only 3.0 has; and its report lists what the map uses that 2.0.4
  does not have (objects, terrain, weather, game files). A map saved by 2.0.x comes out the same. I have not tested the
  ported maps in 2.0.4 yet.
- **Translation: finish a translation done in parts.** `translation machine <map> <out.json> --keep=<your file>`
  keeps every text you already translated and sends only the empty ones to the translation model (issue 57).
- **Port to Reforged (KK and M16 maps): nothing on the loading screen.** The map's own start (its units, its triggers,
  the tables of the port layer) now runs right after the game starts, a piece per frame, instead of on the loading
  screen. On a big Korean RPG that stopped at 50 to 60% of the loading screen in multiplayer, the loading screen became
  almost instant.
- **Port to Reforged: a map AI that is a 1.2x memory exploit is switched off.** An AI script that reads and writes the
  memory of the old game at fixed addresses (to load a platform DLL) closed Reforged while loading.

### Fixed

- **Open in World Editor for the editors of 1.24 to 1.29 and the JassNative Editor: the placed units** (issue 49). The
  units made from the script went in with the neutral players numbered like the Reforged editor (27 for neutral
  passive), which a 12 player editor has no player for, the units whose model is a map file were left out (that filter
  is for the Reforged editor), and the file was in the Reign of Chaos layout. On FOCS3 9.7 C03 all 124 units now go in,
  the neutral ones as player 15, in the layout every Frozen Throne map has.
- **Open in World Editor: the abilities made from the SLK tables** (issue 49). Each column `DataA` to `DataI` of an
  ability is a different field for each ability, and every converted ability got the fields of Blizzard (1,049 on FOCS
  ver192). Now each one gets its own (Evasion's `Eev1`, and so on), for the parent the file names. The JassNative
  Editor closed with "not enough memory" on FOCS ver192 made by 1.8.9; I could not run that editor to confirm this
  was the cause.
- **Port to Reforged of maps of 1.23 and older** (issues 55 and 56): Regicide v2.12 and Neverwinter Nights RPG v2.2c
  now pass the compiler gates. A function that hands back a handle kept in a game cache as an integer goes through the
  handle table, the `return 0.0` after an integer return no longer gets `I2R`, and the real-in-a-location casts of the
  CSCache library are made neutral (the report lists them).
- **Port to Reforged (KK and M16 maps), from the ports of the last days:**
  - a map that turns a feature off when the platform server is missing (`if not JNUse() ... return`; on a Fate/Grand
    Order map, the hero choice) now gets the answer as if the server were there;
  - the black borders a map removes with a sum that gives 0 (`((0)*1.0)`, as the GUI writes it) are removed, so the
    console strip no longer takes the clicks on the map's buttons at the bottom of the screen;
  - a terrain of more than 65,536 height runs ports (it stopped at the compiler gates);
  - `DzGroupGetCount` skips the units already removed from the game, as the KK platform does (a boss phase that waited
    for its group to reach 0 never ended);
  - the SLK reads a Korean port wraps in a `pcall` are found;
  - the local save of M16 maps sizes each piece by its length in the file (a value with many `;` or quotes made the
    game cut the line and the save did not load), and a save part that does not load is left untouched.
- **Translation check: a number like `1,000,`** (the thousands followed by a sentence comma) reads as one number. The
  Korean `금괴 1,000, 당첨 3%` read as 1 and 000, and the right translation failed the check.
- **Translation: a Misc or Skin text file with mixed line endings** keeps every text on import.

## 1.8.9 (2026-10-24)

### New

- **Open in World Editor: JassNative Editor.** A new editor in the list (`--editor-version=jn` on the command line),
  for the Korean editor many classic maps were made with (World Editor 1.21b with Grimoire, JassHelper and UMSWE). It
  writes the map like the 1.27 target but reads that editor's own trigger data, which knows 246 more functions and
  types, so more triggers stay GUI: on FOCS3 9.7 C03, 1,042 GUI triggers and 5 custom text ones (1,016 and 31 with the
  1.27 target), and GUI variables of types like `boolexpr` stay GUI variables. The editor's trigger data comes with
  the Doctor, credited in the third-party notices. The diagnosis also says when a map was compiled in that editor.
- **Translation archive for M16** (`translation override <map> <file>`, and a new card in the Translation tab). For a
  map that has to stay the original, as in M16 rooms: the translation goes into `<map>_translation.mpq` and the map is
  not touched. Only files outside the map checksum go in, so the texts of the script and of the checksummed object
  files stay as they are, and the result says how many of your texts made it. On DragonBall RPG v21.08 the archive
  holds 14,913 of the 19,020 Korean texts; the 4,088 of the script stay in Korean. The Doctor does not make the loader
  that puts the archive over the map (the community "mix" files do that, and only the ones that open it above the map
  work). I have not tested it in the game.

### Fixed

- **Open in World Editor: saving in JassNative Editor failed** (issue 32). Two things in the map stopped the save,
  and I tested both fixes together in that editor: with a map made this way, Save and Save As both work.
  - A map that keeps its script only in `scripts\war3map.j` (FOC does) kept it there, and the editor looks for
    `war3map.j` when it saves ("could not access the file"). The script now goes to `war3map.j`, with the same bytes,
    for every editor target.
  - The line `constant boolean REFORGED_MODE = false` that JassNative Editor writes at every save was already in the
    map, in the custom script and in the old script, so the next save had it twice and the compile stopped. For the
    classic targets the line now leaves both places when nothing in the map reads it, and the report says so.
- **Three short values changed by my release build.** The step that turns the code into English also renamed the
  Japanese language code in the translation modules, the letter of the artifact item class in the random item IDs
  of the editor files, and a label of the game data layers in a report line. They are back as they should be, and the
  release build now stops on any short value it would change, and on a call whose argument name it would break (the
  cause of a 1.8.8 problem I fixed before publishing it).

## 1.8.8 (2026-10-24)

### New

- **Maps marked as not allowed to edit.** A map can now carry a mark that says its author does not allow edits,
  and the Doctor respects it. On a marked map it still says what protects the map, shows its card
  (read only) and checks whether it runs, but it does not unprotect, fix, port, translate or extract it: the window
  shows "Not allowed to edit", every other tab says why it is empty, and the command line answers with the same
  message and exit code 1. The three independent marks are a small file inside the map, a script comment and an MPQ
  header signature; any one of them is enough, even in a protected map with no file list.

- **Port to an older game.** The Port tab now also takes a map back to an older version: a Reforged map (or a map of
  a newer classic game) to 1.29.2 and down to 1.24a. What the older game does not have is written into the map's own
  script. Functions of the newer blizzard.j are copied in. Natives with an equivalent in the older game get it: the
  units, items and destructables created with a skin, the player count functions, the maximum life and mana, the group
  size, the bitwise functions, and the any-unit damage event of 1.31, done the classic way (every unit on the map gets
  the unit damage event). The rest become neutral: they compile and do nothing, and the report lists each one. The map
  info, the object data (with the skin files merged back in), the terrain and the doodads are written in the older
  formats; the triggers and the files only the World Editor reads are written the way the older editor reads them (a
  GUI trigger that uses a function the older editor does not know becomes custom text). Models of version 900 and later
  are written as version 800 (they keep only their diffuse texture), DDS textures become BLP, and FLAC and OGG sounds
  become MP3 when ffmpeg is installed. The script is checked with the game scripts of the target version before
  anything is saved. A Lua map, a map of a platform client (KK, M16) and a map with more players than the target has
  are refused. I could not test this in the game itself: what I checked is that the script compiles for the target,
  that every file reads back in the older format, and that "Runs on <version>?" and the older editor's checks pass.

### Fixed

- **Port to Reforged: a local variable declared twice in the same function** (issue 46, Age of Myths 3.7F). The old
  compiler accepted it, and from the second declaration on the name meant the new variable; the Reforged script
  checker stopped the port with "already defined". The second declaration and the lines after it now get their own
  name.
- **Map detection: scripts with old Mac line endings** (a carriage return only). A map made for 1.23 was read as one
  for 1.24 to 1.28, without the return bug; the natives such a script declares were also missed by the port's platform
  check.
- **Open in World Editor: custom skills shown as "Unknown"** (issue 32, FOC). A map that keeps its abilities in the
  AbilityData.slk table can also carry a small war3map.w3a with a few of them, and "Open in World Editor" only made the
  object files a map lacked, so the editor showed every ability missing from that file as "Unknown". The abilities only
  the table holds are now added to the map's own w3a, and what it had stays as it was: FOCS3 Another 9.7 C03 gets 877
  (445 different skills were "Unknown"), FOC Another 10.0 A06 1,041 (586 were). The step now also runs on a map that
  has its unit and item files and only the ability table.
- **QoL edits: "The map could not be written (MPQ v1 only)".** A map whose archive header a protector or another tool
  had changed could not take the edits: the Doctor only writes the standard MPQ header. The copy now gets the same
  header fix as Fix map first, every other file is checked to read back the same, and the report says so. The other
  steps that write into a map the same way (the editor object files from SLK tables, the lobby image, the object data
  as SLK tables, the port to an older game) get it too.
- **Local machine translation: Korean texts left untranslated** (reported on Discord with DragonBall RPG v21.08).
  A text whose translation fails the number check stays in the original, and several of my own steps made correct
  translations fail it: a compound number (`1억 4000만`) went to the model as two numbers and came back glued; a number
  the model wrote as a word right after a color code (`|rFive`), as "300 million" or as an ordinal ("second" for
  `2차`) was not put back in digits; and the check read a multiplier inside a color code with the code's own digits.
  The model also dropped the level at the end of a name (`Lv2`), which now stays out of it, and read the stat
  abbreviations `이속`/`공속`/`모능` as numbers ("2 speed"). A piece that still loses a number is now cut at its
  numbers, and only the words between them go to the model. On that map 18,981 of the 19,020 Korean texts are translated
  (18,488 before).
- **Port to Reforged, KK maps: a unit changed with `DzSetUnitID` lost its abilities.** That native only changes the
  unit's type and keeps its abilities, but the port made the change with a Chaos morph, which swaps the whole ability
  list for the new type's (in one map, changing a backpack's skin took every ability off it). The change now keeps the
  abilities the unit had.
- **Translation: a circled number before a Chinese multiplier** (`③千里眼`, the item 3 of a list) was read as 3000, so a
  correct translation was refused by the number check. A circled number is now read as the list number it is.
- **Command line: "not used" for step flags that were used** (issue 32). `doctor editor <map> --editor-files
  --gui-triggers --script-objects` printed that those flags were not used, while the job did use them.
- **Shrink: BLP textures with gaps between their mipmaps.** The lossless rewrite of BLP textures skipped a texture
  whose mipmaps had unused bytes between them or after the last one, a layout some exporters write. Those are now
  rewritten too, with the mipmaps back to back: the same pixels, checked one by one, and a smaller file (141 more
  textures on 12 test maps).

## 1.8.7 (2026-10-23)

### New

- **Port between versions and "Runs on 1.2x?": the real map size limit of each classic game.** I measured it in the
  Game.dll of every version from 1.24a to 1.28.5: 1.24a to 1.27a take maps up to 8 MB, and 1.27b and later up to
  128 MB. The Doctor had 4 MB for 1.24a and 8 MB up to 1.28, which was the World Editor's limit, not the game's. The
  limit also only applies to a game with other players (the host sending the map, a player looking for it on disk);
  played alone, or against computers only, a bigger map opens. So a big map is no longer refused by the port between
  versions, and "Runs on 1.2x?" shows it as a warning that says exactly that. The places where the game checks the size
  come from the reverse engineering DooMWhite did in Tinker, used with permission (credited in the third-party
  notices).

### Fixed

- **Port to Reforged, M16/JN maps: saves bigger than 8 KB.** The game cuts every string at 8192 bytes, and the port
  built the whole save in one string before splitting it: a big save came out cut, and the next load failed with "A data
  communication error occurred". The save is written in parts now (a part that did not change is not written again),
  and the load reads it back over several game ticks. A save of up to 8 KB is written byte for byte as before.
- **Port to Reforged, KK and M16 maps: hotkey buttons declared in the map's FDF files** (a `ControlShortcutKey` on a
  button with nothing to draw, the "hotkey board" of some Korean maps). Reforged does not press them; the port layer
  does now.
- **Port to Reforged: a frame callback the map keeps in a global variable** (the compiled vJass hotkey board). Like the
  callbacks the map registers directly, it now runs only for the player who acted, so it cannot desync the game.
- **Translation tab, images: small text stays sharp**, and the translated image is saved in the format of the original.

## 1.8.6 (2026-10-22)

### New

- **Port to Reforged: a `.zip` of the map's art as an art package.** Some authors ship the models of a map in a zip for
  the player to drop into the game folder ("Touhou Def of Omagun" has its heroes in `DefOmagan.zip`). Reforged does not
  load them from there, so the hero select showed white boxes you could not click. "Add an art package..." now takes the
  `.zip` too: it is read as data, nothing is extracted, and the files the map asks for go into the ported map.

### Fixed

- **Port to Reforged: the "Local Handle Vars" of patch 1.23 and older** (issue 41, "Enmity Campaign Beta 79b").
  - The function that reads a stored handle back is declared as returning a generic handle, and its caller hands that
    on as a unit. The Reforged compiler refuses that ("Cannot convert returned value from handle to unit") and the port
    stopped. The function now returns the type its callers use.
  - The port keeps the real handle in a table so a number can turn back into it. That only worked when every call
    stored a unit, a timer or another "agent", and one of the map's 123 calls stores a lightning effect: nothing was
    kept, and every handle the map read back came back empty. Each value is kept where the map stores it now.
- **Port to Reforged: the map's own Blizzard.j returning `0` from a function that returns a real** ("Touhou Def of
  Omagun"). The compiler gates stopped on it ("Cannot convert returned value from integer to real"). The fix that
  already ran on the map's script runs on its Blizzard.j too.
- **Fix map, "Let it run in single player": an anti-cheat armed only in single player** (issue 45, "FFERPG 0.9.7.5c").
  Maps from the LAN days count the players at the start and, with only one, turn on triggers that defeat everyone when
  they see a cheat code; in a LAN game you could play alone with that off. Reforged has no LAN, so playing alone is
  always single player. The option now finds that check (here the players are counted in a force the map fills itself)
  and makes the map take its multiplayer path, one line of the script.

## 1.8.5 (2026-10-21)

### Fixed

- **Open in World Editor: doodads and destructables whose ID a patch renamed.** Reforged renamed a few objects of the
  old game data and kept the same model and settings under a new ID: the "Ruined Blocks" doodad `ASbl` is `ASHB` now,
  the vertical Force Bridge `DTsb` is `DTs0` (the "Archway" `NSra` was already handled since 1.8.3). The game draws
  nothing for the old IDs and the editor of today crashes on them.
  - Before, the Ruined Blocks were taken out of the map. Now they get the new ID and stay where the map put them.
  - A map that also changes the properties of the old object kept the old ID as if it were valid, and the editor still
    crashed ("DotA Outland 4.6a" changes the Ruined Blocks and places 30 of them). Now those are renamed too, together
    with the map's changes.
  - A custom doodad or destructable based on one of the old IDs had no parent in Reforged ("Cyber RPG 7.804" has six
    based on the Ruined Blocks). It is based on the new ID now, with the same changes.
- **Open in World Editor, maps optimized to SLK: unit names.** When the map's own profile files did not set the name
  of a unit, the unit came back with its internal name (`footman`, `workshop`, `keep`) as its name. It keeps the
  game's name now.

Found while comparing the Doctor with a set of SLK fixes a friend made on top of W3x2lni Reforged.

## 1.8.4 (2026-10-21)

### New

- **Port to Reforged: items and units you could not click in Reforged graphics.** Some maps use an effect or a doodad
  of the game as the model of an item or a unit. In Classic graphics the click hits it; the Reforged graphics file of
  many of those models has nothing a click can hit (no collision shape, no geoset box), so the item or the unit could
  only be selected with a drag box. The port now points them at a copy of the classic model, which the click hits in
  both graphics, and "Runs on Reforged?" lists them.

### Fixed

- **Port to Reforged: what a KK map reads in its first seconds** (issue 39). On "尘封古域ORPG" a trigger at 0.01 s
  reads the save and puts the players in a group; another at 0.2 s goes through that group and reads the shop, the
  archives and the daily quotas. In a ported map the saves arrive over the network a moment after the start, so the
  first one waited for them and the second one ran on time with the group still empty: every archive slot was locked,
  the dungeons said "Not activated yet!!!" and the Tower of Babel had no runs left. Now every timed trigger of the
  start, from the first one that reads the save on, waits for the saves and then runs in the map's order, with the same
  gaps between them.
- **Port to Reforged: a shop item asked only to catch cheat clients** (issue 39). The same map asks the platform for a
  shop item nobody can buy, and whoever "has" it is marked as a cheater and never gets the archives activated. The port
  answers "owned" for every shop item, so it marked every player. It now also recognizes a question whose answer
  writes the same mark the map's cheater block writes, and a question with a nested player argument; for those it
  answers "not owned". The other shop items stay unlocked.
- **Port to Reforged: the map level ranking.** The port answers first place, so a map's archive or reward for the top
  of the ranking unlocks (a player has one place: the rewards for the other places stay locked, as on the platform).
- **Port to Reforged: maps of patch 1.23 and older** (issue 40, "DotA Outland 4.6a").
  - A script that starts with a byte order mark stopped the port at the injection step ("injeta.main returned 1"). The
    mark is removed now.
  - A map that hands back a group or an event through a `handle` variable (`set iK = g`, `set g = null`, `return iK`,
    the way maps of that time returned a handle without a leak) had those functions return nothing after the port:
    every "units in range" or "units in area" of the map came back empty. The variable is an `agent` now and the value
    comes back through the handle table.
- **Port to Reforged: a key or mouse event registered with a function** gets its own trigger. When the map passed a
  trigger of its own too, the key also ran that trigger's actions (on "Pride RPG" the TAB key ran the login sync out
  of turn, and the game closed or the save broke).
- **Port to Reforged, multiplayer: two players reading the save at the start.** A trigger that waits for the saves
  took the same slot of local variables for both players and read only the last one.

## 1.8.3 (2026-10-20)

### New

- **Translation: the texts of Lua code.** The export now takes the screen texts of Lua scripts too, with the rule it
  uses for JASS, one decision per copy of a text: a text goes out only when no copy of it is compared, used as a table
  index or key, cut or matched by position, passed to `require`, or passed where a function of the map does one of
  those with it. It reads the `war3map.lua` of a Lua map, the Lua modules a KK map of the YDWE Lua engine ships (all of
  them, also the ones the name list misses), and the modules a map ported by the Lua route keeps in its `war3map.lua`.
  The import writes each translation back into every copy, with the quotes each one had, and reads the script back
  token by token. On "尘封古域ORPG" the item tables, the exchange panels and the reward lists of its Lua modules come to
  4,132 texts.

### Fixed

- **Translation: the texts a script keeps in a table** (issue 37). A text the script saves under keys made by
  `StringHash` (`SaveStr(table, StringHash("52" + I2S(4)), StringHash("Name"), "Weekly Quest 4")`) was taken for a
  hash key and left out of the export, because a `StringHash(` came shortly before it on the line. Only a text inside
  `StringHash(...)` is a key now. The quest lists, bestiaries and item panels a map builds this way are in the file:
  on "尘封古域ORPG" the script texts go from 608 to 2,198.
- **Translation: file paths with a space in their name** were exported as texts (`war3mapImported\Earth Kill 1.mp3`,
  `...\01 Angel of Justice Wing.tga`), and a translated one broke the sound or the icon. They stay out now: up to 474
  of them on one test map.
- **Translation: a map ported by the Lua route** (issue 37). The texts of its converted script are not exported, and
  the Translation tab didn't say so: a KK map ported first and translated after kept its quests, dialogs and menus in
  Chinese. The tab says it now, with what to do: translate the original map (export, then Fix map with the translated
  file) and port the translated map, which keeps the translation. The QoL edits go the same way, on the original map.
- **Open in World Editor: the Archway doodad.** Patch 3.0.1.24371 renamed the game's Archway doodad from `NSra` to
  `NSr0`. A map that placed it had a doodad with no object for the game and for today's World Editor, which crashes
  on it, and "Open in World Editor" removed it. It gets the new ID now and stays on the map.
- **Port to Reforged: units that change type through a Chaos ability.** The port's layer checked the change right
  away and took the Chaos off, but the game changes the type on its next tick, so no unit changed (a guardian's
  Rooting, a Morpheus). The Chaos stays until the type changes now, and what the change wipes and the map had added
  (abilities, invulnerability, the life and mana of the old type) comes back. Measured in game.
- **Port to Reforged, M16/JN maps:** `JNR2I` took any value under 0.001 for zero (the game compares reals with that
  tolerance). It tests the exact zero now.
- **Open in World Editor, maps in SLK mode:** in the object files made from the SLK tables, the second part of a
  `Buttonpos` read the first one cut off, so every command button came out at row 0.
- **Cheat packs: the FSCP and haxorico packs.** Their locals went after the first statement of `main`, which the game
  refuses, and the check let it through as a warning. The locals go first now, a script with a byte order mark in the
  middle reads right, and any complaint about the map's script fails the check.
- **Make it single player: a lock kept in a file.** Some maps (the RPG Creator pattern) run a file of the map through
  `Preloader("<file>")`, and that file renames the players and ends the game in single player. The option finds that
  file now and makes it harmless; the script is not touched for it.
- **Runs on Reforged?: models.** A texture animation entry of 4 bytes is valid (it was reported as a texture animation
  that does not exist). A model with geosets and no node at all, and a texture whose mip chain has a dead tail, are
  listed as information.

### Changed

- **The game reference is Reforged 3.0.1.24371.** The checks of the port and "Runs on Reforged?" know its 4 new
  natives (`BlzUnitIsAlive`, `BlzSetHUDScale`, `BlzLockHUDScale`, `BlzUnlockHUDScale`), its 110 new ability fields and
  the 2 new `blizzard.j` functions, `UnitIsDeadBJ` and `UnitIsAliveBJ`: a map script that defines a function with one
  of those names no longer compiles in the game, and "Runs on Reforged?" says so. The site reads the game data of this
  version.
- **The name list:** the names of files of other games are out, and a community list came in: 5,251,623 names
  (`names.npz` 131.9 MB). The auto-update offers it to anyone with the old one.
- **Shrink** compresses on several threads in the program for Windows and Linux (it used one there; the source
  version already used several processes).

## 1.8.2 (2026-10-17)

### Fixed

- **Open in World Editor: the objects of a map in SLK mode** (issue 32). Since 1.8.0 the Doctor writes the editor's
  object files (`war3map.w3u`, `war3map.w3t`) from the SLK tables of an optimized map, so the classic editors show its
  units instead of "Object ID: U004". In the program and on the site this step always failed (an error in how the
  release is built; the report gave "Object files made from the SLK tables" as the reason), so the editor showed
  "Custom units (0)" and every placed custom unit as "Object ID". It works now: on "Fight Of Characters 9.7 C03" the
  editor gets 760 new and 311 changed units and 231 new items. When the step fails, the report gives the real reason.
- **Open in World Editor: the editor crashed loading the units of those maps** (issue 32). "Leave out the units that
  crash the editor" knows a unit's model only from the object files, and in a map in SLK mode those were made after it
  ran, so it left nothing out. They're made first now: on "Fight Of Characters 9.7 C03" it leaves out 46 units whose
  model is a file of the map.
- **Open in World Editor: "Undeclared variable" when saving** (issue 32). A map's own buff in "Unit - Add Expiration
  Timer" became that GUI action, which only takes the game's expiration timers; the 1.26/1.27 editor then wrote the
  buff without quotes (`B025`) and the save failed. Those lines stay as custom script now (46 in "Fight Of Characters
  9.7 C03").
- **Port to Reforged: players dropped in multiplayer** (issue 33). The port's layer created some of its tables and
  timers the first time they were needed, and its save engine could build part of itself again after a player's own
  save was read. Both could happen on one player's PC only (only that PC has that save, or only that player clicked a
  menu), and a game object made on one PC only makes Warcraft drop a player. The save engine is now built once at load
  on every PC, and everything the layer created "the first time" is created at load too. The save diagnostic file no
  longer goes to a "DreamS5" folder.
- **Open in World Editor for a classic editor: memory libraries** (issue 32). Since 1.8.0 a local variable with the
  name of a function or a global is renamed, because JassHelper refuses it. A memory library reads the address of a
  global array through a local with the same name, and renaming that local stopped the map in the game. That local
  keeps its name now, and the report says so.

## 1.8.1 (2026-10-15)

### New

- **Port between versions.** The "Port to Reforged" tab is now **Port**, with a **Port to:** picker: Reforged as
  before, or a newer version of the classic game (1.24a to 1.29.2) for a map made for an older one. The map's return
  bug gets its equivalent, the names the newer game also declares are renamed, and the script is checked with the
  scripts of that version; the rest of the map stays as it is. A map that already runs on the version you pick comes
  out unchanged. KK and M16 maps go to Reforged only, and the picker says why a version is not available for a map (a
  platform map, a map that needs a newer game, a map too big for that game, a protected map that Fix map has to open
  first). On the command line: `port <map> --to=<version>`.

### Fixed

- **Port to Reforged: tilted effects** (issue 31): an effect the map tilts up or down is drawn at its angle again. In
  1.8.0 the fire of the Hoshino R in gggf8952 went straight up instead of along the shot.
- **Port to Reforged: menu sounds in multiplayer** (issue 31): the hover sound of some menu cards played for every
  player when one of them moved the mouse over the card; now it plays only for that player.

## 1.8.0 (2026-10-15)

### New

- **Share new file names.** When a map has file names the shared name list does not know, a notification offers to
  share them: a GitHub issue opens in your browser with the names of the files inside the map only (never the map, its
  name or its folder), and you decide whether to send it. The names are merged into the list on their own, and the
  next release carries them. In the program for Windows and Linux.
- **Copies of the game's files** (issue 30): "Runs on Reforged?" says how many of the map files at the game's own paths
  are byte-for-byte copies of the game's file, and Fix map can take out only those copies (`--remove-game-copies`),
  which changes nothing the map shows. The port report counts the imported files that are copies of another file of
  the map, of an art package or of the game, and the art list next to the ported map (`<map>_reforged.art.tsv`) says
  which, for pruning.
- **Port to Reforged: "Classic look of the game effects"** (off by default; `--classic-effects`). Reforged shows many
  of the game's spell effects in their HD variant, which is another effect; with this option the ones the map uses keep
  their classic (SD) look: copied into the map under new names, the references rewritten.
- **Open in World Editor: "Make identical textures distinct"** (off by default; `--identical-textures`), the old
  workaround for a World Editor 3.0 crash, now a step you choose. The identical textures themselves are harmless.
- **Port to Reforged:** the report says the unit level cap it wrote when a unit type is above the map's MaxUnitLevel.

### Faster

- The local machine translation is about a third faster, with the same result: the text goes to the model in several
  batches at once.
- The text in the images reads two image sets at a time, about twice as fast, with about the same memory.

### A clearer window

- **Fix map and Open in World Editor:** what this map needs is in view; more options and the steps the map does not need
  are folded, and the window remembers what you opened.
- **Runs on Reforged?:** the answer in one line, a summary ("2 blockers, 3 warnings... Fix map takes care of 4"), what
  matters first, filters by severity and by "Fixed by Fix map", every detail one click away. Long reports (the
  diagnosis, the results, the port, Diagnose) get a "What matters" box and the same filters.
- **Port to Reforged:** the recommended options in view, the rest under "More options".
- Every notification has a close button. Compare says what it could not read. A tab loading in the background gives up
  after 5 minutes instead of waiting for ever.
- Clearer English (the messages name the buttons as the window shows them), and every text of the window in the 16
  languages, the report lines of the checks included.

### Fixed

An audit of the whole program found 385 problems, 24 of them serious: every serious one is fixed (one of them in
part), and most of the others too. The ones you could notice:

- **Open in World Editor:** without the game installed, every standard doodad was taken for an invalid one and removed.
  Units of a map in SLK mode showed as "Object ID: U004" in the classic editors: the object files are made by default
  now. Saving no longer stops with "Identifier redeclared" on obfuscated scripts. A step that failed now says so ("A
  step was skipped") instead of "Ready", and opening a map no longer tries a download.
- **Fix map:** a sound file with a long dialogue text was taken for an "inflated" one and replaced by an empty one,
  losing every sound. A shrunk texture left stale checksums and the game called the map corrupted. A unit edited by hand
  in the script no longer makes the editor copy fail. Minify kept a `constant real` as an integer, which changed
  divisions in the map.
- **Broken or hostile maps:** a map without a valid header lost its whole diagnosis; a cut compressed block gave a
  script with a zeroed tail, without an error; a tiny file declaring a huge size could take gigabytes of memory; a
  `war3map.wts` without a closing brace froze the window. All refused or read right now.
- **Map card:** the names and authors of GBK and Korean maps showed as garbage.
- **Runs on Reforged?:** a check that crashed vanished from the list, so the answer could be "yes" with a check that
  never ran; it is an item with the reason now. A commented `AbilityId("exec-lua:...")` no longer counts as one.
- **Models and textures:** a damaged or hostile model or texture could keep the Files tab, the checks or Shrink busy
  for minutes and fill the memory; it stops with an error now.
- **Triggers:** a timer trigger whose period comes from a variable got 0.0 after the restore to GUI; such triggers
  stay as they are now. A Lua map that loops for ever no longer freezes the trigger check. A map with raw vJass no
  longer loses its triggers to a check that cannot run on it.
- **Translation:** a script text that spans a line break was translated one line at a time, half of it left in the
  original. Scanning the images no longer keeps every picture of the map in memory (6.6 GB on a large map).
- **Port to Reforged:** setting a unit's life, mana or their maximum by number did nothing, so units could have no
  life; Chinese only in the script's texts was not found, so the Chinese fonts were left out and the text vanished.
  An art package that does not open stops the port with the reason, instead of being dropped in silence. A failed or
  canceled port leaves no temporary file beside your map.
- **Issue 31**, fixed in the port (the proof is in the game): Hoshino's W dash, the flames of Hoshino's R going
  sideways, the crash of Azusa's Q with a skin (a model tagged for Reforged on the old layout) and the menus that
  stuttered and repeated a sound. The game's tooltip box no longer stretches into a huge empty box or jumps between two
  places when a map moves it: it stays in the game's own place, in every port. The game's unit detail panel no longer
  shows under a map's own HUD, the skills of the M16 LoLHUD can be clicked, and a map that writes Korean gets fonts with
  Korean letters for the game's own messages and chat. A unit paused and transformed at the same moment no longer stays
  paused for ever. The port's own effect carrier is no longer counted as missing art (issue 30).
- **Diagnose:** a crash file was recognized by its name, so `Crash (1).txt`, a `.dmp` or a UTF-16 `Crash.txt` gave
  "Nothing the Doctor knows was found"; it is read by its content now. Files left by an earlier run show their date. A replay or
  log above 64 MB is refused (a hostile replay could inflate 1 MB into 1 GB). The text you copy hides your Windows
  user name.
- **The window and the site:** a job whose result never reached the page, or a browser worker out of memory, left
  "Working..." for ever; a save that failed on the site showed "Done"; a button whose call failed showed nothing. All of
  them end with a message now.
- **Command line:** a misspelled `--flag` ran the job with the defaults; unknown options are refused now (a warning for
  `fix` and `editor`).

### Thanks

- fratleyslaye, for the idea of comparing the contents of the files and not only their paths (issue 30).
- gggf8952, for the detailed reports from the game (issue 31).

## 1.7.9.1 (2026-10-14)

A small release on top of 1.7.9. If you are on 1.7.8 or 1.7.9, update: the buttons that open a map were broken.

### Fixed

- The buttons that open a map ("Open a map", "Open another map", and picking the other map in Compare) did nothing in
  1.7.8 and 1.7.9: only dragging a map onto the window opened it. The map filter of the open dialog had a character
  the window library refuses, so the dialog never appeared. The site was not affected.

### New

- **Port: a folder as an art package** (issue 30). Some maps leave their art out of the `.w3x`, to get past the size
  limit, and the game reads it from its own folder with "Allow Local Files" (`war3mapImported\...` next to the game).
  Next to "Add an art package..." there is now **"Add a folder..."**: pick the game folder that has `war3mapImported`
  inside, or the `war3mapImported` folder itself. The files the map uses from it stay OUT of the ported map, so the map
  stays under the game's 512 MiB, and the port writes them next to the ported map, in `<map>_reforged_local_files`,
  with a README: copy its `war3mapImported` folder into the game folder (`Warcraft III\_retail_`) and turn on
  "Allow Local Files". Every player needs the same files. From the command line, `--package=` takes a folder too.
  Tested on CWG RPG 3.96 with its art pack: 757 files (641 MB) stay outside, the ported map is 489 MiB (with
  everything inside it was 914 MiB); not tried in the game yet.

## 1.7.9 (2026-10-14)

### New

- **Diagnose**, a new section, to find out why a map fails in the game without one test per guess:
  - **Make a diagnostic copy**: a copy of the map whose script logs, once a second while you play it, to
    `Documents\Warcraft III\CustomMapData\DevosMapDoctor\<map>.pld`: the functions the game started and never finished
    (their thread probably stopped there: the instruction limit, a division by zero, a null value a native refuses), the Lua
    errors with the line of the map's script, and the last things that ran. "Mark every function" goes finer; "Load
    markers" writes one file per step of the load, at once, for a map that hangs on the loading screen.
  - **Read a diagnostic log** says what broke first.
  - **Read a crash report**: the game's own crash report and log (`Documents\Warcraft III\Errors`): the module it closed
    in, the models it could not create, the interface frames it refused (names over 62 characters), units set above
    their maximum level, the classic Crash.txt of 1.24 to 1.31, the desync files, and, for the crash in ClientSdk.dll,
    how many of the game's own textures the map carries at the game's paths.
  - **Read a replay** (.w3g): the players, who left and when (a burst of leaves is reported as a suspected desync), the
    chat, the sync and frame events, the state checksum of every turn; two replays compared give the first turn they
    disagree on.
  - From the command line: `doctor diagnose <map> [--all|--init]`, `doctor log`, `doctor crash`, `doctor replay`,
    `doctor replay-compare`.
- **Runs on Reforged?** checks more:
  - the start of a JASS script (config, main and the timers of the first 5 seconds) runs in the Doctor's own
    interpreter, and a thread that does much more work than the game lets one thread do is reported;
  - frame files (.fdf, .toc) with problems the game skips; map files at the game's own paths (3.0 has closed on maps
    that ship them); abilities locked by a requirement inherited from the base ability that the map does not define;
    model paths that resolve to nothing in the map or the game; the lobby (war3map.w3i) against the script's config();
    stale checksums in (attributes);
  - handle locals never set to null, the item type numbers of before 3.0, the natives renamed in 1.29, and signs of code
    grafted onto the editor's skeleton (shown as signs, never as a verdict);
  - the model and texture sanity (references, animation tracks, BLP mipmaps and headers), with the Reforged model format
    (version 1300 to 1800) read correctly;
  - for an older game (Runs on version X?): the models, textures and sounds that version does not load.
- **Fix map** extras: redo the file checksums; remove map files that replace the game's own (off by default); unlock
  abilities that require a tech the map lacks; fix frame file lists; null handle locals; minify the script; shrink
  models (lossless, or lossy within 0.05 units); make the editor object files from the SLK tables of an optimized map
  (needs the game installed); your own lobby image; two test variants of "Fix black portraits" (the model version 1800,
  and the 3.0 layout: untested in game, try one hero first); and, for a map still above the game's 512 MiB after the
  lossless shrink, smaller art (the biggest textures at half size, WAV sounds mono at 22 kHz). The Port has the same
  512 MiB option (`--lossy`).
- **Files tab:** a 3D preview of models (versions 800 to 1100; the Reforged 1800 models are not drawn yet).
- **Map card:** the World Editor that saved the map, by the build table. **Runs on version X?:** write the map info in
  that version's format (the first stage of taking a map back; the report lists what is not converted).
- **Cheat packs:** a readable copy in the map's triggers, so the pack can survive a save in the World Editor (the call to
  it needs a custom text trigger; not tried in the editor).
- **Names:** names the script builds while it runs, and names crossed with every folder of the map, are found; a name
  stored with `/` is found too.
- The progress bar follows the real work, so a long step no longer leaves it at 97%. Jobs start at once: two workers
  are kept ready (before, every job waited about 3 seconds for its worker on Windows). The window has an About.

### Fixed

- The Doctor's script interpreter (the map card's values, the cheat pack chat, the new checks) runs the start of
  Reforged scripts to the end: the game's player counts come from natives in Reforged's scripts, and its loops over the
  players never ended.
- The model readers (the model checks, the texture list, the deep model check) read the Reforged model format; the
  game's own models were all reported as an unknown version.
- The map info of format 27 is read with its game version; string files with `string` in lower case and a `}` inside a
  text are read right.
- The command line help: `translation export` writes `.json` (or `.html`), and art packages include `.w3mod`.

### Thanks

- The projects whose code, data or measurements these checks use, listed in THIRD_PARTY_NOTICES: GodMephisto's wc3ctl,
  sumneko's 5211MapCheck, w3champions, Tasyen's FDF, Drake53's War3Net and War3App, speige's WC3MapDeprotector, PBug90's
  w3gjs, scopatz's w3g notes, UnrealKaraulov's WC3CrashAnalyzer, 4eb0da's war3-model, flowtsohg, Darithos, Retera,
  Dr Super Good, WarRaft, Vexorian's jasshelper, Son-Guhun, YElwiddi and inwc3.

## 1.7.8 (2026-10-13)

### New

- Art packages: `.mix`, `.asi`, `.dll`, `.mpq` and `.w3mod` files, and any file with an MPQ archive inside that is not a
  map, open as art packages. Before, a model pack renamed to `.w3x` was taken for a protected map with scrambled
  tables. The diagnosis says what the package holds; Fix, Port and Open in World Editor explain that it is not a map
  (issue 29).
- Files tab: a select-all box (it selects what the filter shows), "Extract all..." and "Extract models...". Extract
  models writes every model together with the textures and particle models it uses, at the paths the model expects,
  so a model viewer opens them. From the command line: `doctor extract <file> --all` or `--models`.

### Fixed

- Port to Reforged, Gutsy Geoid Game: the hero selection screen builds again. Its start-up ran past the game's
  per-thread instruction limit because of the port's own checks on every frame call (thousands of them for about 200
  hero cards), so the screen stayed open under the mode screen, the select button stayed on "10" and the pick fell
  back to the tavern. Those checks are constant-time now and the start-up costs about 30% less (issue 28, checked in
  game).
- Port to Reforged, the map's own skill bar: every visible skill gets a button (the E and Z icons were missing), the
  skill that replaces another one by making it unavailable shows in its place with its cooldown (Raiden's RR, Iori's
  versions of R), the attack slot and the attack value show (the port's unit table was missing `showUI1`), and the
  item buttons are shown again (issue 28).
- Port to Reforged: effects that turn around their axis point where the skill goes. Reforged 3.0 does not turn many
  effect models; the port draws them on a helper unit and turns the unit (Jotaro's Q and R, issue 28).
- Port to Reforged: the text template for Chinese text is only used by maps that write Chinese or Japanese characters.
- Translation: a translation file still applies after the map is ported again, even when the port stores a data file
  with other upper and lower case in its name.

### Thanks

- Kroda2, for testing Gutsy Geoid Game again and again with screenshots (issue 28).
- coldblade01, for the art packs that started the art package support (issue 29).

## 1.7.7 (2026-10-12)

### New

- Port to Reforged: a new option, "Remove the game's own files" (off by default). Some maps carry old copies of the
  game's own icons, textures and interface models under the game's paths, and on Reforged they replace the game's
  files; the ported Naruto Castle Defense crashed on 1,486 of them. The option removes them from the ported map, and
  the port report always says how many the map has. From the command line: `port --remove-game-files`.
- Port to Reforged, KK maps on the Lua route (YDWE): many more maps start and play. The main module named in quotes
  (`exec-lua:"..."`) is found, the game start and damage events of the `MH*` platform API work, clicks reach the map's
  own buttons, the stats no longer show -0.00 (a number formatter overflowed in the game's 32-bit Lua), the data files
  the map loads through escaped paths are found, large RLE textures no longer show white, floating bars no longer move
  with the camera, and the platform shop "bait" items that mark cheaters answer "not owned" (issues 23, 24 and 26).
- Port to Reforged: maps that hide the default interface and then move the hero, item and minimap buttons into their
  own HUD now show those buttons (issue 21).
- Faster: "Open in World Editor" no longer compiles the same script several times, and a map whose script is cut off
  went from 12 minutes to 13 seconds; shrinking a map again reuses what was already compressed.

### Fixed

- Port to Reforged: the terrain height table of very large maps no longer stops the port (issue 27, EvolusionRPG).
- Open in World Editor: a script that starts with a UTF-8 byte order mark before its header comment is accepted
  (issue 22).
- Port to Reforged, KK maps: the map's own Chinese and Korean texts show in the interface (the port sets interface
  fonts with those characters when the map does not set its own), and the game panel no longer shows under the map's
  own panel (issue 23).

## 1.7.6 (2026-10-10)

### New

- Port to Reforged: maps that draw their own interface by reading the memory of the 1.28 game through the MemUI
  library (M16 maps like Gutsy Geoid Game and Blc1) now show it. The portrait unit, the mouse position, the tooltip
  frame, the frame layout and the skill bar the map reads from the command card are answered with Reforged natives.
  Before, the portrait read came back empty and the map hid its whole HUD. Checked in game (issue 20).
- Port to Reforged: a skill placed on the attack button slot keeps the slot and its hotkey on Reforged, and the hero
  still attacks on its own. Only the attack button is hidden, on the unit types that have a skill on that slot.
- Port to Reforged: formula tooltips built with `JNStringRegex` and many string replaces (which were native calls on
  1.28 and run as script on Reforged) are cached. A tooltip built again costs about a fifth of what it did, and the
  first build about a third, so the frame rate no longer drops over them.
- Port to Reforged, KK maps: the platform server is emulated a step further, from the design of the KK CloudScript
  runner: the backend logic requests answer with the sync messages a map waits for, the daily quota and the player
  GUID (stable per account) answer as the server would.

### Fixed

- Translation: words the map script looks for inside its own texts (like the formula keywords of the tooltips) and
  texts it compares with chat or uses as keys could be translated, which broke those features. The Doctor now follows
  each text through the map's own functions and variables, and keeps untranslated only what the script searches for,
  compares with something from outside (chat, object names, accounts) or uses as a fixed key. Everything else is
  translated as before. Thanks to the user who reported it with issue 20.
- Translation: a profile value with quotes that lost one in the translation is now refused by the check.
- The Translation tab listed the texts of a big map only after every other tab had loaded, so the export ran with
  nothing picked. The list now loads first, and the export waits for it.

## 1.7.5 (2026-10-10)

### New

- Item recipes. The Files tab has an "Item recipes" card: "Find recipes" lists the item combinations the map script
  makes, with the ids and names of the items, the gold, lumber or level a recipe asks for, and where in the script it
  is. It reads the recipes written as triggers (the block that takes the items and creates the new one) and the tables
  of the recipe libraries: ItemCombine, the vJass sjRecipe, the YDWE formula and DDItemCombine. "Save as..." writes
  them as .txt (one recipe per line), .json or .csv. Command line: `doctor recipes map.w3x --out=recipes.csv` (`--all`
  also lists one item swapped for another and the blocks that make several items). On my 110 test maps it found 6,901
  recipes in 34 maps, every item with its name. Recipes kept in a hashtable or in a compiled script (KKWE, j2b) are not
  seen. Asked for by a user.
- [README-translation.md](https://github.com/devoltzz/devos-map-doctor/blob/main/README-translation.md): a guide to
  every way of translating a map, step by step: the local machine translation, the file translated by hand, with an AI
  chat or with Google Translate or DeepL, reviewing a translation, the text in the images, applying it to the map, the
  file format, what the Doctor checks, what is never translated and why, common problems and the command line.

### Faster

The same output, byte for byte (each change was checked against the old code on my test maps), in less time. Some
hot loops now run in native code: C (`mpqcrypt`, the MPQ cipher and the JPEG layer of BLP textures, also on the site
as WebAssembly) and Rust (`jass_checks`: the JASS and Lua tokenizers, the SLK and INI readers). The Python code stays
as the fallback. CPU time measured on big maps (under Python's profiler, which slows everything down, so the program
itself runs faster than these numbers):

- QoL tab on a big Lua map (Castle Fight): about 17 minutes -> 80 s. "Runs on Reforged?" on it: 308 s -> 60 s,
  and "Runs on version X?" (1.27): 189 s -> 5 s.
- A big protected M16 map (Lusin): opening it 26.6 s -> 4.1 s, Fix map 75 s -> 22 s, six actions together
  450 s -> 149 s.
- Shrink of a map with many textures (Abyss): 315 s -> 133 s.
- Cheat packs 2 to 3 times faster (Forest Defense 10.6 s -> 3.8 s, FOCS3 25.8 s -> 9.9 s).
- Translation export, check and import about 1.5 to 2 times faster (export: Forest Defense 13.4 s -> 7.1 s, Lusin
  16.5 s -> 10.3 s).

### Fixed

- Issue 19: the machine translation of a map made for the classic game could make an object text longer than the 1023
  bytes the classic game reads, and that broke every item of the map (empty shops, no drops). On a classic map that
  keeps to that limit, a translation that is too long is now cut at a line break, or left untranslated when no cut
  keeps it whole, and the checks report a hand translation that is too long. A text the script compares with a player
  name stays untranslated.
- Port to Reforged: a KK map closed after picking a skill. The crash report points to a frame event, which Reforged
  sends over the network one turn later, reaching a frame the map had already destroyed (the skill picker). The port
  layer now hides the frame and destroys it 2 seconds later.
- "Open in World Editor" showed outdated placed units when the map script had been edited by hand: the editor's unit
  file is now rebuilt from the units the script creates.
- Shrink refused the Fix map output of maps whose archive sits after protector bytes.
- Cheat packs failed on maps with object ids made of non-ASCII bytes (LineageHardcore, DisRPG), and on a protected
  archive they now say so before working on it: "unprotect it first".
- The command line shown under Fix map wrote `--translation` without the file name.
- The Windows program shrank maps with zlib instead of zopfli (a library zopfli needs was missing from the exe), so
  its maps came out bigger than they should. Now it gives the same file as the Linux program and the source (Abyss
  RPG: 11.66 MB -> 11.57 MB); the shrink takes longer for it (Abyss: about 7 s -> 75 s).

### Thanks

- To the user who asked for the recipe export, and to [@nhammen](https://github.com/nhammen) for issue 19 and the
  maps that showed it.

## 1.7.4 (2026-10-10)

### New

The Doctor now works with maps of the classic game too, and keeps their version:

- "Runs on version X?": the "Runs on Reforged?" tab has a "Check against:" picker, from 1.24 to 1.29. The script is
  checked with pjass against the `common.j` and `Blizzard.j` of that version, so a native the version does not have
  shows up. Reforged 3.0 is still the default. Command line: `doctor check map.w3x --game=1.27`.
- "Made for": the diagnosis says which version a map was made for (before 1.24, 1.24 to 1.28, 1.29, or 1.30 and newer),
  with the reasons: the map info, the editor, the player count, the natives it uses, the return bug, Lua.
- "Open in World Editor" in the editor of the map's own version: the copy is written in the formats the World Editor
  of 1.24 to 1.29 reads, and the GUI triggers are rebuilt with the `TriggerData.txt` of that version. Command line:
  `doctor editor map.w3x --editor-version=1.27` (or `auto`).
- The game data of the old versions (the SLK tables, `TriggerData.txt` and the other text files) is not in the
  program. It is downloaded once from the site (4 MB) the first time an old version is needed, checked by size and
  sha256, and kept in your data folder. The script rulers of 1.24 and 1.29 come with the program.

Port to Reforged: a bridge for what the old game allowed and Reforged does not.

- The return bug of 1.23 and older is adapted, not just switched off. A variable that carried a handle disguised as
  another type gets its real type back (the Stone Prison of Wintermaul keeps its game cache), a `handle` parameter
  becomes `agent` so the handle table keeps the real handle, and a return of another type goes through the table.
- Names the newer game created after the map was made (a function of the map named like a Reforged global, a global
  named like a Reforged native) are renamed, and the report says since which patch Reforged has each one.
- The interface memory hacks of the 1.26 community (the MemHackAPI) are found and reported. 91 of its functions become
  Reforged natives by what they do: frames, special effects, unit and ability fields.
- Maps made for the UjAPI (the JASS API that extends 1.24e to 1.28f) port too: their types and constants are mapped to
  Reforged, 384 natives exist as they are, 190 have an equivalent and 97 are written in JASS. The rest do nothing, and
  the report lists the ones the map calls.

Port to Reforged: natives measured from the platforms' own clients.

- M16 (JN): the `JNString*` natives work as the client does them, `JNI2R`/`JNR2I` keep the bits of the real, and the
  DzAPI aligns text by bits and reads `DzGetColor` with the alpha first. Maps that raise the movement speed cap through
  memory get `MaxUnitSpeed` in their gameplay constants, and the report has a "Movement speed cap" section.
- KK: the same DzAPI alignment and colors, `DzIsKeyDown` (it was always false), key, click, move and wheel events
  registered by name, the japi unit states as the japi reads and writes them, `DzGetUnitNeededXP`, and the KK server
  emulated as if it were there (saved data, VIP, shop, daily quota, the RPG lobby).

### Fixed

- Cheat packs could not be added to a map with the return bug (Wintermaul Final Frontier): pjass already refused the
  map's own script, and that blocked the cheat pack. Now only a new complaint blocks it.
- Port to Reforged broke array indexes and long texts in some maps (13 of my 107 test maps, among them Gaia's ORPG,
  TKoK and BlackRoad): a hex number like `$b8` was read as the array `b8`, and the second line of a long text was read
  as code. Both fixed.

### Thanks

- Unryze ([github.com/UnryzeC](https://github.com/UnryzeC)), for [UjAPI](https://github.com/UnryzeC/UjAPI) (the porter
  reads its declarations), [MemHackAPI](https://github.com/UnryzeC/MemHackAPI) (the catalog the porter uses to
  recognize it) and [WFE](https://github.com/UnryzeC/WFE-Release).
- garden-hose ([github.com/garden-hose](https://github.com/garden-hose)), whose
  [DzAPIConverter](https://github.com/garden-hose/DzAPIConverter) is the base of the `EX*` data natives of the port
  layer since 1.5. This time I sent something back:
  [pull request #2](https://github.com/garden-hose/DzAPIConverter/pull/2).

## 1.7.3 (2026-10-09)

### New

Local machine translation, in the Translation tab:

- The texts of a map in Chinese, Korean, Japanese, Russian, Vietnamese or Thai are translated into English on your
  computer, with an open translation model (OPUS-MT, University of Helsinki). Nothing is sent anywhere.
- The model the map needs is downloaded once, from the release `translation-models` of this repository, and checked
  before it is used. "Best" is a bigger model that reads game texts better (Chinese, Korean and Russian, 200 to 220 MB);
  "Fast" is the small one (60 to 70 MB). A big RPG takes 2 to 4 minutes on a common processor.
- The model only translates sentences, so the program prepares each text for it: the color codes, line breaks, `%s`,
  numbers and tooltip data never go through the model, a name with one color per letter is translated as one name and
  recolored, lists of levels go level by level, common game words (stats, damage, cooldown, item slots) come from a
  word list, and a piece that loses a number is translated again until it keeps it.
- The result is the same translation file an export gives, already checked against the map: tick "Apply the
  translation" in Fix or Editor, or open the file, review it and load it again. What fails the checks keeps the
  original text.
- Command line: `doctor translation machine map.w3x english.json [--quality=best|fast]`.

A machine translation is a first pass: names and some game words come out literal.

The text in the images, with "Also read the text in the images" (the export and the local translation):

- Every image of the map (BLP, TGA, PNG, JPG) is read by a text reader (PaddleOCR, on this computer, its models
  downloaded the first time: 15 to 27 MB). The four parts of a loading screen are read as one picture; a title in two
  lines is translated as one sentence; the glyph sheets of a font are left alone; a lone character on a texture (what
  a text reader finds in leaves and stones) is ignored.
- "Review the images": each image as it is and as it will be, side by side; the English of every line can be
  corrected, or the line left out; "Update preview" redraws it and "Save the changes" writes the translation file.
- On a plain background the original text is erased and the English is written in its color; on a picture the English
  goes on an opaque band, so nothing of the original shows. The image is written back in its own format.
- Command line: `--images` on `doctor translation export` and `doctor translation machine`.

The text of the frame definitions (FDF files: the `Text` of each frame of a custom interface) now goes out with the
other texts of the export and comes back with the import.

### Fixed

Port to Reforged, for maps of the M16 (JN) platform (issues #17 and #18, both confirmed in game):

- A hero that could not move after being picked (#17): maps that read their data with the platform's text pattern
  function (`JNStringRegex`) now get its results, so the hero has its speed, life and range again, its monsters spawn
  in the hunting areas, items drop and the save validates.
- A new character could not start its first stage (#18): the port now gives the map the save reply it waits for when
  that reply travels over the network, so the "save before playing" lock ends; the village button works.
- Monsters that spawned already dead (#18): a unit with a huge life in the map's data (1,000,000,000) died when the map
  lowered it, because the game keeps the life with little precision at that size; the port now lowers it in steps.
- A white square over the interface (#18): the game's portrait, which the map hides by removing its anchors (the old
  game hid it that way, Reforged does not), now goes off screen.
- Also for these maps: the bottom black band of the interface is gone, the map measures the window right (the
  tooltips stay at the mouse), and unit states the map writes through a named constant reach the units.

- "Runs on Reforged?" stopped with an error (AttributeError) on any map that has a model. It came from how the program
  is assembled for release: one model check function got a new name in its own module, and the two modules that call
  it still used the old name. The same mistake had stopped "Compare two versions" since 1.6.8. The release build now checks every
  call between the program's modules and refuses to build when one points to a name that does not exist.
- Translation: the game cache keys of a script (`StoreInteger(cache, mission, key, value)` and the rest of that
  family, and their `...BJ` versions) were treated as if the key were the first two arguments, so the real key could
  be translated and the value stored under it was no longer found. They now stay as they are.

## 1.7.2 (2026-10-09)

### Fixed

Port to Reforged, for maps of the KK platform (issues #15 and #16):

- A map whose game runs on the YDWE Lua engine now gets its interface. These maps write the definitions of their
  frames while they run; the port collects them by running the map in a simulated game, and until now only the source
  version of the Doctor could do that, so the program left them out and the map started on a black screen. The
  simulator now ships with the program (#16). This was the known issue of 1.7.0 and 1.7.1.
- A map no longer closes during the loading screen when its interface anchors a frame to a background that grows with
  its own text (the text pinned to the bottom of the background, the top of the background pinned to the text). The
  old game resolved that loop point by point; Reforged closes without a log as soon as another frame is anchored to
  that background. The port now keeps the same layout without the loop (#15).

Both fixes turn on only where a map needs them; every other port comes out the same.

## 1.7.1 (2026-10-09)

### QoL: a quality of life version of a map

A new tab, QoL. Many old RPG maps were made for long sessions of grinding; a "QoL version" makes them easier to play,
and until now each one was edited by hand. The Doctor now makes it from the map's own script, with the multipliers you
choose, and writes an edited copy:

- Experience: the experience of every player from kills, and the experience the map's triggers give.
- Gold and lumber: every gain, from kills, triggers, mining or selling. A map with a save/load code gets a note: what
  a load gives back is a gain too.
- Item drop chance and craft success chance: the rolls of the script that decide whether an item comes are found and
  their chance multiplied (100% at most). A roll that picks between two items is left alone, and tiers stay tiers: a
  rare item stays rarer than a common one. The item tables of the World Editor (the drops set on a unit in the editor)
  are multiplied too: each item weighs more, and the "nothing" share gives up what they take. A roll on an item read
  from a loot table (a boss that drops one of its items) counts as a drop.
- Hero revive time: the waits and timers of the hero revive are shortened (0.5 is half the time), and so is a delay
  that the map passes to its revive function. The revive at an altar follows too (the map's gameplay constants). A
  duel timer that revives the heroes at its end is not a revive timer and is left alone.
- Monster respawn time: how long a dead monster takes to come back. The delay many RPGs keep in the unit's Point
  Value, a "creep respawn" trigger that makes the same unit again after a wait, and the timers of a respawn system
  are shortened; the Point Value itself stays, since maps also use it for other things.
- The -noshake chat command: each player turns the camera shakes of the map off and on, optionally off from the start.
- The whole map revealed from the start.
- VIP for everyone: the map's checks of a player name against its own list answer as for a listed name. The same
  checks may guard the author's commands, which open up too: the tab says so.

Maps ported from the KK platform are read too: a roll turned into a percentage before it is compared, a revive
through the port's helpers or a timer the YDWE keeps in its local slots, the success roll of an upgrade scroll.
Gold and lumber a load gives back from a save are not multiplied, so a save does not grow on every load.

The tab shows what the map has for each edit before anything is written (how many rolls, waits, calls), and the report
lists what was changed. The edited script is checked by pjass, and every other file of the map is read back the same.
On the RPGs measured, no script got a complaint it did not have before. Lua maps take every edit too, the rolls and
the revive waits of their code included. KK maps: Port to Reforged already unlocks the
mall items, the map level and the VIP of the platform; a KK map takes the QoL edits after the port. The command line
has it too: `doctor qol map.w3x` shows what the map has, `doctor qol map.w3x --xp=2 --gold=2 --drop=2 --respawn=0.5`
writes `map_qol.w3x`.

Test the map in game before sharing it.

### vJass

The Doctor's JASS parser now reads vJass too: libraries, scopes, structs, methods and operators, interfaces, modules,
static ifs, textmacros, block comments, member access with a dot. Plain JASS reads exactly as before. A map whose
script still has vJass that was never compiled gets a clearer report in "Runs on Reforged?" and in the QoL tab: what
the code declares (libraries, scopes, structs), since the game cannot run it until the World Editor compiles it.

### Also

- The pjass check of an edited script now runs in the program too. It was skipped there (only the archive ran it) for
  the single player lock removal, the early preload and the ability lists moved to the script.
- "VIP for everyone" leaves the "WorldEdit" name alone: it is the name of the player of a test run from the World
  Editor, which maps use for their test mode.

Known issue: Port to Reforged of a map whose game runs on the YDWE Lua engine does not yet add, in the program, the
frame definitions the map writes while it runs; the report says so, and the map's custom interface may not show.

### Fixed

Port to Reforged, for maps of the M16/JN and KK platforms (issues #10 to #14):

- A map that ended the game as soon as it loaded when the platform server was missing, or when the server plugin
  was older than the map asks for, now goes on (FWD RPG, Story RPG).
- The login of the platform save accepts a new account, so the character selection opens (NOX RPG, and the same
  login in twrpg).
- The minimum damage the platform reports now counts the hero's primary attribute: attacks no longer do 0 or 2-12
  damage (AnimalRPG S2, NOX RPG).
- Frame texts colored with `|c00` (an alpha the old game ignored) are visible again, a button made from the map's
  own frame definitions answers its click, the game's own Menu button is the one the map asks for, and a login that sends an empty sync message goes through (Blc).

Each fix turns on only for a map that needs it; every other port comes out the same.

### Thanks

- sangje_wc3 ([github.com/hachamacha106](https://github.com/hachamacha106)), for
  [w3x2lni-reforged](https://github.com/hachamacha106/w3x2lni-reforged), the community fork of w3x2lni updated for
  Warcraft III 3.0 maps. It showed the gaps the Doctor covers in its own code (no code of the fork is in the Doctor).

## 1.7.0 (2026-10-08)

### Port to Reforged: maps whose game runs on the YDWE Lua engine

Since 1.6.3 the Doctor recognized the KK maps whose game is Lua run by the YDWE Lua engine (a DLL only the old game
loaded) and stopped there. Now it ports them: the map becomes a Reforged Lua map.

- The map's JASS goes through the same port as before (the platform natives implemented, checked by pjass) and is then
  turned into Lua.
- The Lua modules of the map are found and named (the archive of these maps has no file list: the names come from the
  debug info, from the names the Lua itself cites and from the folders already seen). Their Lua 5.3 bytecode, which
  Reforged does not load, is translated back to Lua source, one statement per instruction, including the KK engine's
  shuffled opcodes.
- A runtime gives the modules what the engine gave them: `require` by the map's own paths, `jass.common`, `jass.japi`,
  `jass.slk`, `jass.storm` with the map's data files, `jass.bignum`, the key and mouse hook.
- The written `war3map.lua` is checked: it compiles with Lua 5.3 and its main chunk loads.
- On the Lua maps of our test folder (KKWE and j2b, obfuscated ones, UTF-8 identifiers) 83 to 99% of the modules load
  in our simulator with no error. What the old engine did in the game's memory, or with the platform's server, has no
  Reforged equivalent and stays out. Test the map in game: the simulator proves the script's path, not the screen.
- A game written as native code in a DLL the map ships cannot be ported; the report says so.
- Tested in game on a KK Lua map up to its custom interface: Reforged's Lua is 32-bit, so the runtime keeps every
  number and library call inside 32 bits; the frame files the map writes at run time are put in the map; the KK UI
  framework gets the mouse position, the per-frame update and the clicks it expects; and textures the old engine never
  drew stay invisible instead of green.

### Balance huge numbers

A new option of Port to Reforged. Some Chinese maps give units life, damage or attributes above what the game's integer
holds on Reforged (2,147,483,647), and the numbers wrap around. "Balance huge numbers" scales life, damage, mana, armor
and attributes down so the biggest stack fits, keeping the proportions, and converts the script's calls where the
script talks to the game. It works on the Lua route too.

### j2b: the newer encryption

Maps whose `war3map.bin` starts with `2SAJ3raw` are now decrypted. Their compiler also hides every function call
behind a token; the Doctor finds the target of most tokens by inference, without running anything of the map (the
game's scripts compiled as a reference, the number and the types of the arguments, the order of the functions). On the
measured map 79% of the tokens (95% of the calls) are found; the port still stops while some are open, and says how
many.

### Older KK maps

- Open in World Editor: the `return` statements the old compiler accepted and the 3.0 one refuses are fixed (the same
  fixes the port makes), including an integer returned from a function that returns real.
- KK maps compiled with `null` on the left of a comparison come back to JASS.
- A ported map that moved the game's message frames (chat, unit, top messages) crashed after the loading screen; those
  frames now keep the game layout.

### Translating a ported map

Issues #6, #7 and #8: maps ported by the Doctor worked, but after the translation they broke. Port to Reforged adds its
own code to `war3map.j` (the local save, the hash tables, the object data tables) and the translation treated it as map
text, so the save code was translated too. The port's code now stays out of the export and comes back byte for byte on
import. If you translated a ported map before, port the original map again and translate it with this version.

### Ported models

From pull request #9 by caiohsr14: every model a map gives to `DzSetUnitModel` gets a unit type of its own, so the
unit shows that exact model with neutral scale and color, and a unit going back to its own model uses its own skin.
Models whose names are not UTF-8 (an obfuscation of some Chinese maps) get unique names, so they no longer fold into
one.

### Object data of the 3.0 editor

Maps saved by the 3.0 World Editor write their object data in a newer format (version 3). The repairs that rewrite
object data (new object ids, Balance huge numbers, the classic data fixes) refused those maps; they work on them now.
The map info reader follows the published version thresholds, and the unit portrait and indexed models are checked
like the other models.

### Fix map

- New option "Remove the script indentation" (Fix map, Open in World Editor, Port to Reforged and cheat packs): the
  spaces and tabs at the start of each script line go, the code stays the same (checked token by token).
- The single player lock removal finds more locks: the count of human players, `bj_isSinglePlayer` and cheat code
  probes, punished by ending, restarting or crashing the game, or by disabling or breaking the save. A check that only
  shows a message or adapts the difficulty is left alone.

### Also

- Faster: the JASS and Lua parsers, the trigger proof and the SLK passes now run in native code (Rust), with the same
  results as before. Opening a big KK map in the World Editor took 83 s and now takes 71 s on our test map.
- A new README with a tour of the window.
- The reference game scripts are the ones of Reforged 3.0.1.
- The program now carries Lua 5.3 and 5.4 (Lupa), which check the Lua script of a ported map and of a map opened in the
  World Editor; before, the Lua of a ported map was written unchecked.
- The name search of the Lua modules runs in native code (Rust).

### Thanks

- caiohsr14, for pull request #9 (the models of `DzSetUnitModel` and the non UTF-8 model names).
- sangje_wc3, whose w3x2lni with Warcraft III 3.0 support pointed out the gaps above, now covered in the Doctor's own
  code.

https://doctor.devoltz.party has it too.

## 1.6.10 (2026-10-07)

### Translations: words glued together and numbers with commas

A report from Discord: after translating a map's file with an outside service and importing it back, some item names
showed with no spaces ("FireRainBow").

- In many Chinese maps each character of an item name has its own color. The translation keeps those color codes, and
  the service put them between the English words without a space, so the game showed the words glued. On import, a
  color code between two words now gets the space back ("Fire Rain Bow"). A name colored letter by letter stays as it
  is.
- A translation that wrote a number with a thousands separator ("100,000" for 10万 or 100000) was rejected. It is
  accepted now, except in the lists of levels, where the comma separates the levels.
- The exported file explains how to keep the codes between whole words.

https://doctor.devoltz.party has it too.

## 1.6.9 (2026-10-07)

### KK maps with a hand-patched script

Some KK maps had their compiled script edited after it was compiled: the platform calls (`DzAPI_Map_*`), in their
wrappers and inline, were replaced by fixed values, one comparison became a constant and one `if` lost its condition.
"Port to Reforged" stopped on them ("unexpected instruction POPN").

The decompiler now recognizes those patches and brings each one back to JASS as the constant it became. The functions
it touches are checked statement by statement; every other function is still checked instruction by instruction. The
port report lists them. Thanks to @caiohsr14 for the fix (#4).

https://doctor.devoltz.party has it too.

## 1.6.8 (2026-10-07)

### Faster on big maps

Measured on the largest test maps (260 to 470 MB), before and after:

| map, action | 1.6.7 | 1.6.8 |
|---|---|---|
| Anime Choice Arena (473 MB), Fix map | 44.1 s | 20.8 s |
| Anime Choice Arena, Open in World Editor | 72.4 s | 46.5 s |
| Twilight's Eve Evo RPG (332 MB), Fix map | 23.2 s | 13.6 s |
| Twilight's Eve Evo RPG, Open in World Editor | 42.8 s | 28.8 s |
| Aspect of Doom RPG (278 MB), Fix map | 19.4 s | 11.5 s |
| LineageHardcore (258 MB), Port to Reforged | 19.9 s | 17.0 s |
| Opening a map (diagnosis) | 2.4 to 6.0 s | 1.7 to 4.6 s |

What changed:

- Each file of the map is decompressed once per action, not 8 to 10 times: the checks after a fix compare the stored
  bytes when the file was copied as it was.
- The script checks (handle leaks, start-up functions, globals never set) run in native code, written in Rust: about
  12 times faster, the same results. The page on the site keeps the Python version.
- The MPQ name hashing runs in native code (C), in batches.
- The list of the game's doodad ids is read from the game once per game version, not on every map.

### Fixes

- "Apply the map card changes" and "Fix black portraits" failed on every map with an `(attributes)` file since 1.6.4
  ("The entry of block N changed in the new map"): their final check did not expect the `(attributes)` update that keeps
  the game from calling the map corrupted.

### Cleaner source

The public source has no long comments any more: every file carries one line on top saying what it is.

https://doctor.devoltz.party has it too.

## 1.6.7 (2026-10-07)

### Everything on screen in your language

With another language picked, parts of the window stayed in English: the reports (the diagnosis, the result of each
action, the port report), the "What changed" table, the cheat pack options and the file kinds. All of that is now
translated, in the 16 languages.

What you copy ("Copy report") and what "Report a problem" sends to GitHub stay in English, whatever the screen shows,
so every report reads the same.

The translations were made with AI. If something reads wrong in your language, open an issue with the text and a better
wording.

### Fixes

- A cheat pack option ("Player name that activates it") came out half translated.
- The map's own texts (its name, description and loading screen in the map card) are never translated.
- The page loads only the language you use, not all 16 at once.

https://doctor.devoltz.party has it too.

## 1.6.6 (2026-10-07)

### Linux

The Doctor now runs natively on Linux: `DevosMapDoctor-linux-x86_64`, one file, like the Windows exe. Keep it next to
`names.npz` and `chmod +x DevosMapDoctor-linux-x86_64`. It runs on x86-64 systems with glibc 2.35 or newer (Ubuntu
22.04+, Debian 12+, Fedora 36+, Mint 21+), and it writes the same bytes as the Windows exe (fix, editor, port and
translation checked on 17 test maps).

The window uses the system's GTK and WebKitGTK, as the Windows one uses WebView2. If they are missing, the program
says what to install (`sudo apt install gir1.2-webkit2-4.1` on Debian and Ubuntu). To port maps, point `WC3_GAME` at
your Warcraft III 3.0 folder (Wine, Lutris).

### Command line

Everything the window does now also runs in a terminal, with the same options:

```
doctor fix map.w3x --unprotect --listfile --portraits
doctor editor map.w3x
doctor port map.w3x
doctor cheat map.w3x --pack=nzcp --set activator=-cheat
doctor translation export map.w3x texts.txt
doctor --help
```

The command under each action in the window is the one to type. On Windows, `doctor.exe` appears next to the program
the first time you open it; on Linux the program is the command (`./DevosMapDoctor-linux-x86_64 fix map.w3x`). `--json`
gives the result as JSON, for scripts.

### 16 languages

French, German, Italian, Polish, Czech, Turkish, Ukrainian and Traditional Chinese join the eight of 1.6.5. Traditional
Chinese is picked for systems set to Taiwan, Hong Kong or Macau (they got Simplified before). The translations were
made with AI: if something reads wrong, open an issue with a better wording.

### Fixes

- Maps encrypted by the KK platform with the newer loader (the real map stored after the archive, hundreds of MB) were
  taken for ordinary KKWE maps and offered "Fix map". The Doctor now says the real map is encrypted outside the file and
  only the KK client opens it.
- The select boxes (language, presets) are drawn by the page in its dark colors.

https://doctor.devoltz.party has it too.

## 1.6.5 (2026-10-07)

### The Doctor in your language

The page now speaks Portuguese, Spanish, Russian, Chinese, Korean, Japanese, Vietnamese and Thai, besides English. It
opens in your system's language (English when it is not one of these) and the picker under the name changes it at any
time, without reloading; the choice is remembered (in the program's settings, or by the browser on the site).

What is translated is the page itself: the modes, buttons, steps, options, progress and messages. The reports the engine
writes (the diagnosis and the result of each action) stay in English for now, as do file names, raw codes and scripts.

The translations were made with AI. If something reads wrong in your language, open an issue with the text and a better
wording.

https://doctor.devoltz.party has it too.

## 1.6.4 (2026-10-07)

### Cheat packs on protected maps

A cheat pack added to a protected map could leave a map the game refused to start ("There was an error trying to load
the selected map. The map is unavailable or corrupted."). The script was fine: the map's `(attributes)` file, which keeps
a checksum of every file, still had the checksum of the old script. The Doctor now updates those checksums for every
file it writes, so this is fixed for everything that writes into a map without rebuilding it: cheat packs, translations,
the Fix map extras and the port. ([#1](https://github.com/devoltzz/devos-map-doctor/issues/1))

### KK maps with code pasted in by another tool

Some KK maps carry functions that another compiler made and someone pasted into the compiled script later; on the map
of [#2](https://github.com/devoltzz/devos-map-doctor/issues/2) they were chat commands that give gold and an item. Those
functions stopped the port ("`if` without the JUMP before the label"). The Doctor now turns them back into JASS too,
checks them statement by statement, and the port report lists them by name, so you can see what they do.

### Port: the two extras work in the program and on the site

"Decrypt the KK textures" and "Fix the green icons" in Port to Reforged failed in the program and on the site since
1.6.2 ("No module named ..."). They work now.

### Faster on maps compressed with PKWARE

Maps whose files are compressed with the old PKWARE method, each file in one big sector, opened slowly: a 291 MB map sat
about 3 minutes on "Checking for fake files". That decompression now runs in native code (the DLL in the program,
WebAssembly on the site), with the same output: the same map opens in under 5 seconds.

### Cheat packs

OzzyCP's "Search objects by numeric id" now says when it is needed: only for maps whose object ids are scrambled, and
not after Fix map restored them.

https://doctor.devoltz.party has it too.

## 1.6.3 (2026-10-06)

### A new look

The page (the program window and the site) is reorganized: the modes are buttons on the left, each one with its own
screen, so fixing a map and preparing it for the World Editor no longer share a page.

- **Fix**, **Editor**, **Port**, **Cheatpacks**, **Translation** and **Inspect** (files, script and compare).
- Each action shows the command its ticked options make (`$ doctor fix "map.w3x" --unprotect --listfile ...`).
- The cat in the corner sleeps; while a job runs it wakes up and shows a progress bar with the time left. The time is
  learned from your earlier runs of the same job, so the first run shows the time so far and the next ones an estimate.
- Same tick boxes everywhere, themed scrollbars, and the site reloads itself when a new version is out.

### Translation: pick what to export

The Translation tab lists where the map's texts come from (map info, trigger strings, the script, units, items,
abilities, buffs, the skin files...) with how many each has, and exports only what is ticked.

**Fixed:** the texts of the script never went into the exported file in the program (the release had a mismatch in how
it classified the script's strings). They do now: on one test map the script went from 0 to 380 texts.

### Raw codes with names

Inspect > Files > Raw codes lists every object id of the map with its name (as the Object Editor shows it), its kind
and the file it comes from, with a filter by kind and a search by id or name.

### Chat commands in a table

The map card lists the chat commands as a table: the command, how the game matches it (the whole message, or a message
that contains it) and how many triggers listen to it, plus the texts the script compares the chat message with.

### Maps whose game runs in the YDWE Lua engine

Some KK maps keep their whole game in Lua that a DLL inside the map runs (the YDWE Lua engine, loaded by a memory trick
of the old game). Reforged cannot load that DLL, so the map starts and nothing happens. The Doctor now says so in
"Runs on Reforged?" and the port stops with that reason, instead of porting a map that does nothing. When only part of
a map is Lua, both only warn.

### World Editor

- Map info of the newer editors (format 34 to 39) is read and written back.
- The cameras of 3.0 maps are rebuilt from the script, and the Undercity day/night models are kept.
- A campaign file shows its name, author and maps.

https://doctor.devoltz.party has it too.

## 1.6.2 (2026-10-06)

### No more green icons

Reforged draws a button GREEN where it shows it disabled (a dead hero, the items of another player's unit) when the
map imports the icon without its disabled art. Common in KK and M16 maps, often hundreds of icons. The Doctor now
makes that art from each icon:

- **Fix map**: the new extra "Fix the green icons" (on by default, offered when "Runs on Reforged?" finds them).
- **Port to Reforged**: the new option "Fix the green icons" (on by default).

### The KK platform's encrypted textures

Some KK maps keep their textures encrypted (BLX1), so only the platform's client shows them: on Reforged the models
come without their textures and the icons are green. The Doctor now decrypts them back into plain BLP: the new extra
"Decrypt the KK textures" in Fix map and the same option in Port to Reforged (both on by default). The image preview
reads them too.

### Cheat packs on several maps (site)

The "Several maps" card of the site has a new action, "Add a cheat pack": after picking the folder, each map shows the
packs its script can take and the pack's activators, with the defaults, so every map can get its own pack and
activators ("Same as the first map" copies the first one's choice to the others).

### More file names

The file name index (`names.npz`) now has 4.66 million names (it had 2.2 million), cleaned of junk entries, so more of
the files of protected maps get their name back.

### Faster on big maps

More of the work runs in native code (the DLL in the exe, WebAssembly on the site), with the very same output:

- maps with lots of sound in the old Storm compression: a 98 MB map that took minutes now opens in about 2 s and
  fixes in under 20 s;
- maps whose protector adds hundreds of thousands of junk entries: a 130 MB map that took minutes now opens in
  about 20 s and fixes in about 75 s.

https://doctor.devoltz.party has it too.

## 1.6.1 (2026-10-06)

### Much faster on encrypted maps

The MPQ decryption now runs in native code (a small DLL in the exe, WebAssembly on the site) instead of Python: about
200 times faster, with the very same output. Maps whose protector encrypts every file open and fix in seconds instead
of minutes — for example a 348 MB map: opening 69 s → 5 s, Fix map 10 min → 27 s (in the browser: 46 s).

https://doctor.devoltz.party has it too.

## 1.6.0 (2026-10-06)

### The Doctor in your browser

**https://doctor.devoltz.party** — the same program, run in your browser. Your map never leaves your computer; the
page works offline after the first visit. Chrome, Edge and Firefox on a computer; maps up to 450 MB (bigger ones need
this Windows program).

- Fix map, Open in World Editor, Port to Reforged and every tab, with the same results as the Windows program
  (checked file by file on 46 test maps).
- **Several maps at once**: one action on every map of a folder (Chrome and Edge save each result next to its map;
  Firefox gives one zip).

### Fixes

- **Port to Reforged stopped with "Cannot read properties of undefined (reading 'slice')"** on every map whose port
  left a called stub. Fixed.
- Port to Reforged stopped at the compiler gates with "Unrecognized character (ASCII 8)" on maps whose script has a
  stray control character outside a string (the old game skipped it). Fixed: it becomes a space.
- Port to Reforged stopped at the terrain step on maps saved by the World Editor of 1.32 and later, and on Reign of
  Chaos maps. Fixed.
- "Open in World Editor" and "Fix map" now read the doodads of Reign of Chaos maps.
