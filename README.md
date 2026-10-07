# Devo's Map Doctor

A desktop tool for Warcraft III maps. It opens protected maps, repairs what stops them on Reforged 3.0, rebuilds the
World Editor files, ports the maps of the Chinese KK and Korean M16 platforms, and shows what a map carries before
anything is written. It never runs the game.

## Use it

- **In the browser**: [doctor.devoltz.party](https://doctor.devoltz.party). The same program, run in your browser:
  your map never leaves your computer, and the page works offline after the first visit. Chrome, Edge and Firefox on
  a computer; maps up to 450 MB.
- **On Windows**: get `DevosMapDoctor.exe` and `names.npz` from [Releases](https://github.com/devoltzz/devos-map-doctor/releases) and
  keep them in the same folder. Nothing to install; the program tells you when a new version is out.
- **On Linux**: get `DevosMapDoctor-linux-x86_64` and `names.npz`, keep them in the same folder and
  `chmod +x DevosMapDoctor-linux-x86_64`. One file, for x86-64 systems with glibc 2.35 or newer (Ubuntu 22.04+,
  Debian 12+, Fedora 36+, Mint 21+). The window uses the system's GTK and WebKitGTK, as the Windows one uses WebView2:
  `sudo apt install gir1.2-webkit2-4.1` (Debian, Ubuntu), `sudo dnf install webkit2gtk4.1` (Fedora). The command line
  needs nothing. To port maps, point `WC3_GAME` at the Warcraft III 3.0 folder (under Wine or Lutris).
- **In a terminal**: the same jobs as the window, `doctor <command> <map> [options]`. On Windows `doctor.exe` appears
  next to the program the first time you open it; on Linux it is the program itself
  (`./DevosMapDoctor-linux-x86_64 fix map.w3x`). The page shows the command of each action under its button:

  ```
  doctor diag map.w3x
  doctor fix map.w3x --unprotect --listfile --portraits
  doctor editor map.w3x
  doctor port map.w3x
  doctor check map.w3x
  doctor cheatpacks map.w3x
  doctor cheat map.w3x --pack=nzcp --set activator=-cheat
  doctor translation export map.w3x texts.txt
  doctor fix map.w3x --translation=texts.txt
  doctor files map.w3x
  doctor extract map.w3x war3map.j --to=out
  doctor --help
  ```

  The report goes to the output, the progress to stderr (`--quiet`: none), `--json` prints what the job returned. Exit
  code 0 done, 1 failed, 2 wrong command line, 3 done with leftovers.

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

`pip install -r requirements.txt`, then `python build.py` writes `dist/DevosMapDoctor.exe` (and the `doctor.exe` it
carries, from `launcher/doctor_launcher.c`). `python build_linux.py` writes `dist/DevosMapDoctor-linux-x86_64` in a
Docker container (`linux/Dockerfile`), from Windows or Linux. The site is built from the same code by
`web/build_site.py` (the `site` workflow attaches it to each release; `deploy/` serves it). Third-party code is listed
in `THIRD_PARTY_NOTICES.md`.

## Problems

Use "Report a problem" in the window: it opens an issue here with the report filled in.
