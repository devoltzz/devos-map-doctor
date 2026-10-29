# Command line and the `--json` contract

Devo's Map Doctor runs every job of the window from a terminal. On Windows, `doctor.exe` (it appears next to the program
the first time you open it) is the console launcher; `DevosMapDoctor.exe <command> ...` works too. On Linux the program
itself takes the commands.

```
doctor <command> <map> [options]
doctor --help
doctor --json-schema          # the contract below, as JSON (also: doctor schema)
```

The report goes to stdout, the progress to stderr. `--quiet` drops the progress. The map you give is never written:
every output is a new file next to it (`<map>_fixed.w3x`, `<map>_editor.w3x`, `<map>_reforged.w3x`...).

## Exit codes

| code | meaning |
|---:|---|
| 0 | done, or nothing to do |
| 1 | failed |
| 2 | wrong command line (unknown command or option, missing file) |
| 3 | done with leftovers (`outcome` is `partial`) |
| 130 | cancelled |

## `--json`

With `--json`, stdout carries exactly one JSON object (UTF-8) and nothing else. Since 1.10.0 every object has these
keys on top:

| key | type | what |
|---|---|---|
| `schema` | integer | the version of this contract (now `1`) |
| `doctor_version` | string | the program that answered, such as `1.10.0` |
| `command` | string | the command as the contract names it: `fix`, `check`, `translation export`, `extract all`, `qol apply`, `replay list`... |
| `exit_code` | integer | the exit code the process returns |

The rest of the object is what the job returned, at the top level, as in 1.7.6 and every version since: a program that
read `outcome` or `file` before keeps working. A job that writes a map has `outcome` (`ok`, `nothing`, `partial` or
`failed`), `file` (the copy written, or `null`) and `lines` (the report, as `[style, text]` pairs).

When the command line is wrong (exit 2), the job raises (exit 1) or it is cancelled (exit 130), `--json` still prints
one object: the four keys above plus `outcome: "failed"`, `error` (the message) and `error_kind` (`usage`,
`exception` or `cancelled`). The same message also goes to stderr.

A map the author marked "not allowed to edit", or an art package given to a command that needs a map, answers with
`error`, `outcome` and `no_edit: true` or `package: true` instead of the command's keys.

`doctor --version --json` prints only the four keys (`command` is `version`): a cheap way to find out what you are
running before anything else.

## The contract (`--json-schema`)

`doctor --json-schema` prints the whole contract, generated from the same tables the command line uses:

- `envelope`, `failure`, `refusal`: the keys above.
- `outcomes`, `exit_codes`, `global_options` (`--json`, `--quiet`, `--help`, `--version`, `--json-schema`).
- `commands`: for each command, its `usage`, its `options` and its `result`.
  - an option has a `kind`: `flag` (`--x`), `value` (`--x=<v>`), `flag-or-value`, `repeat` (`--set <key>=<value>`,
    more than once) or `step` (a step of fix / editor: naming steps runs only those, `--no-<step>` drops one); some
    have `values` (the accepted ones) and `about`.
  - `aliases`: older option names that still work (`check --version=1.27` is `--game=1.27`).
  - `result`: the keys a result is guaranteed to have, with their type: `string`, `integer`, `number`, `boolean`,
    `array`, `object`; `x|null` may be `null`; a trailing `?` means the key may be missing. A result can have more
    keys than the contract lists.

The command line accepts only the options the contract lists for a command: anything else is refused with exit 2
(in `fix` and `editor` it is a warning on stderr, since the steps a map offers depend on the map). So what
`--json-schema` prints is what runs.

## Compatibility promise

`schema` changes (to `2`, and so on) only when a program reading `--json` would break:

- a key the contract lists is removed, renamed, or changes its type (an `integer` becoming a `string`; a key that was
  never `null` becoming `null`);
- an option is removed, or a value an option took is refused;
- an exit code or an `outcome` value changes its meaning;
- the four keys on top change.

These can change in any version **without** a new `schema`:

- new commands, new options, new keys in a result, new values of `error_kind` or of a key the contract types only as
  `string`;
- the text of the report (`lines`), of `error`, of the usage and of the progress on stderr;
- the order of the keys, the indentation of the JSON;
- keys a result has that the contract does not list (read them if they help, but they are not promised);
- the steps a given map offers (they depend on the map and on what the engine finds).

A renamed option keeps its old name as an alias (listed under `aliases`) for at least the rest of that `schema`.
From 1.7.6 to 1.10.0 no option was renamed: every option of 1.7.6 still works with its meaning.

## Writing a wrapper

- Run `<command> <map> ... --json --quiet` and parse stdout as one object; read stderr only for the message of a
  failure.
- Check `schema` first: refuse (or warn) on a number you were not written for, instead of pinning one build.
- `doctor --json-schema` lists the options of `fix` (its steps and extras) for the version installed; a wrapper can
  build its allow-list from it instead of a fixed copy of `--help`.
- `fix` writes `<map>_fixed.<ext>` next to the map it was given (`<map>_fixed (2).<ext>` and so on when that name is
  taken: nothing is overwritten); read the path from `file` in the result rather than guessing it (`null` when
  `outcome` is `nothing`).
