<div align="center">

<img src="docs/images/icon.png" width="96" alt="">

# Devo's Map Doctor

Open, fix and port Warcraft III maps for Reforged.

[![Latest release](https://img.shields.io/github/v/release/devoltzz/devos-map-doctor?label=release)](https://github.com/devoltzz/devos-map-doctor/releases/latest)
[![Downloads](https://img.shields.io/github/downloads/devoltzz/devos-map-doctor/total)](https://github.com/devoltzz/devos-map-doctor/releases)
[![License: MIT](https://img.shields.io/badge/license-MIT-blue)](LICENSE)
[![Platforms](https://img.shields.io/badge/platforms-Windows%20%7C%20Linux%20%7C%20Web-informational)](#get-it)

**[Download](https://github.com/devoltzz/devos-map-doctor/releases/latest)** ·
**[Use it in the browser](https://doctor.devoltz.party)** ·
**[Report a problem](https://github.com/devoltzz/devos-map-doctor/issues/new)**

<img src="docs/images/tour.gif" width="900" alt="A map opened in the Doctor: diagnosis, Fix map, Runs on Reforged?, map card, Port to Reforged, translation and cheat packs">

</div>

## What it does

The Doctor opens protected maps, repairs what stops them on Reforged 3.0, rebuilds the World Editor files and ports
the maps of the Chinese KK and Korean M16 platforms. It shows what a map carries before anything is written, and it
never runs the game.

| Action | What it does |
|---|---|
| **Fix map** | Removes the protection and repairs the map: fake file tables, scrambled ids, data the 3.0 engine refuses, broken SLK tables, models that crash the game, portrait cameras, data pointers, ability lists, single player. Extras for the map card, the translation and the size. |
| **Open in World Editor** | Writes a copy the editor opens, with the GUI triggers rebuilt from the script when the round trip proves them. |
| **Port to Reforged** | KK, KKWE, DzAPI, YDWE and j2b maps get their natives implemented and their scripts back in JASS. Maps whose game runs on the YDWE Lua engine become Reforged Lua maps (their Lua 5.3 bytecode translated to source). |
| **QoL** | A quality of life version of the map: more experience, gold, lumber, item drops and craft success, a faster hero revive and monster respawn, a -noshake command, the map revealed, VIP for everyone. |
| **Tabs** | Map card, "Runs on Reforged?", files (previews, raw codes), script and its checks, triggers, translation export and import, local machine translation into English, compare two versions, cheat packs. |

How to translate a map, every way step by step: [README-translation.md](README-translation.md).

<table>
<tr>
<td width="50%"><img src="docs/images/diagnosis.png" alt="The diagnosis of a protected map"></td>
<td width="50%"><img src="docs/images/port-report.png" alt="The report of a KK map ported to Reforged"></td>
</tr>
<tr>
<td align="center">The diagnosis, as soon as a map opens</td>
<td align="center">A KK map ported, with both compiler gates passed</td>
</tr>
</table>

### New in 1.7.8

- Art packages: `.mix`, `.asi`, `.dll`, `.mpq` and `.w3mod` files (any file with an MPQ inside that is not a map) open as art packages instead of being taken for a protected map. The Files tab has a select-all box, Extract all and Extract models (each model with the textures and particle models it uses, at the paths it expects); from the command line, `doctor extract <file> --all` or `--models` (issue 29).
- Port to Reforged: the hero selection screen of Gutsy Geoid Game builds again. Its start-up ran past the game's per-thread instruction limit because of the port's own frame checks, which are now constant-time; the screen closes, the countdown runs and heroes are picked from the interface (issue 28).
- Port to Reforged: the map's own skill bar shows every skill (the E and Z icons), the attack slot and the attack value, the skill that replaces another one (Raiden's RR, Iori's versions of R) with its cooldown, and the items (issue 28).
- Port to Reforged: effects that turn around their axis point where the skill goes (Reforged 3.0 does not turn many effect models; the port turns a helper unit instead).
- Translation: a translation file still applies after the map is ported again, even when the port stores a data file with other upper and lower case.

## Get it

### In the browser

[doctor.devoltz.party](https://doctor.devoltz.party) is the same program, run in your browser. Your map never leaves
your computer, and the page works offline after the first visit. Chrome, Edge and Firefox on a computer; maps up to
450 MB.

### Windows

Get `DevosMapDoctor.exe` and `names.npz` from [Releases](https://github.com/devoltzz/devos-map-doctor/releases) and keep them in the same
folder. Nothing to install. The program tells you when a new version is out.

### Linux

Get `DevosMapDoctor-linux-x86_64` and `names.npz`, keep them in the same folder, then:

```
chmod +x DevosMapDoctor-linux-x86_64
```

One file, for x86-64 systems with glibc 2.35 or newer (Ubuntu 22.04+, Debian 12+, Fedora 36+, Mint 21+). The window
uses the system's GTK and WebKitGTK, as the Windows one uses WebView2:

```
sudo apt install gir1.2-webkit2-4.1     # Debian, Ubuntu
sudo dnf install webkit2gtk4.1          # Fedora
```

The command line needs nothing. To port maps, point `WC3_GAME` at the Warcraft III 3.0 folder (under Wine or Lutris).

### Command line

The same jobs as the window: `doctor <command> <map> [options]`. On Windows, `doctor.exe` appears next to the program
the first time you open it. On Linux it is the program itself (`./DevosMapDoctor-linux-x86_64 fix map.w3x`). The page
shows the command of each action under its button.

```
doctor diag map.w3x
doctor fix map.w3x --unprotect --listfile --portraits
doctor editor map.w3x
doctor editor map.w3x --editor-version=1.27
doctor port map.w3x
doctor check map.w3x
doctor check map.w3x --game=1.27
doctor cheatpacks map.w3x
doctor cheat map.w3x --pack=nzcp --set activator=-cheat
doctor qol map.w3x --xp=2 --gold=2 --drop=2 --respawn=0.5
doctor translation export map.w3x texts.txt
doctor translation machine map.w3x english.json
doctor fix map.w3x --translation=texts.txt
doctor files map.w3x
doctor recipes map.w3x --out=recipes.csv
doctor extract map.w3x war3map.j --to=out
doctor --help
```

The report goes to the output and the progress to stderr (`--quiet`: none). `--json` prints what the job returned.

| Exit code | Meaning |
|---|---|
| 0 | done |
| 1 | failed |
| 2 | wrong command line |
| 3 | done with leftovers |

## Limits

Nothing touches the file you opened: a new one is written next to it, and every output is checked file by file. Some
protections can only be partly undone; the report says what was left. Test the map in game before sharing it.

## Building

`pip install -r requirements.txt`, then `python build.py` writes `dist/DevosMapDoctor.exe` and the `doctor.exe` it
carries (from `launcher/doctor_launcher.c`). With Rust installed, `cargo` also builds the script checks of
`native/jass_checks`, which otherwise run in Python.

`python build_linux.py` writes `dist/DevosMapDoctor-linux-x86_64` in a Docker container (`linux/Dockerfile`), from
Windows or Linux.

The site is built from the same code by `web/build_site.py`. The `site` workflow attaches it to each release, and
`deploy/` serves it.

## Problems

Use "Report a problem" in the window: it opens an issue here with the report filled in.

## Thanks

- [caiohsr14](https://github.com/caiohsr14), for the exact models of `DzSetUnitModel` and the unique ASCII names of
  models whose names are not UTF-8 (#9).
- sangje_wc3 ([hachamacha106](https://github.com/hachamacha106)), whose
  [w3x2lni-reforged](https://github.com/hachamacha106/w3x2lni-reforged), the w3x2lni fork for Warcraft III 3.0 maps,
  pointed out gaps the Doctor now covers in its own code.
- [Unryze](https://github.com/UnryzeC), for the [UjAPI](https://github.com/UnryzeC/UjAPI), whose declarations the
  porter reads for maps made for it, the [MemHackAPI](https://github.com/UnryzeC/MemHackAPI), whose catalog lets the
  porter recognize the interface memory hacks, and [WFE](https://github.com/UnryzeC/WFE-Release).
- [garden-hose](https://github.com/garden-hose), whose [DzAPIConverter](https://github.com/garden-hose/DzAPIConverter)
  gave the base of the `EX*` data natives of the port layer (MIT).

## License

MIT, see [LICENSE](LICENSE). Third-party code is listed in [THIRD_PARTY_NOTICES.md](THIRD_PARTY_NOTICES.md).
