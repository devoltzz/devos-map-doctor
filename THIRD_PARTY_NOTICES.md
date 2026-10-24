# Third-party notices

## StormLib

https://github.com/ladislav-zezula/StormLib

The MPQ rules this program follows come from StormLib, and `doctor/mpq/pkware.py` and `doctor/mpq/mpq_wave.py` are Python
ports of its PKWARE DCL ("implode") and WAVE (Huffman/ADPCM) decompressors.

```
The MIT License (MIT)

Copyright (c) 1999-2013 Ladislav Zezula

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in
all copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN
THE SOFTWARE.
```

## pjass

https://github.com/lep/pjass

The executable bundles `pjass.exe`, which checks the script of a ported map; the site runs the same source built as
WebAssembly (`web/build_pjass.py`).

```
BSD 2-Clause License (http://www.opensource.org/licenses/bsd-license.php)

Redistribution and use in source and binary forms, with or without
modification, are permitted provided that the following conditions are
met:

   * Redistributions of source code must retain the above copyright
notice, this list of conditions and the following disclaimer.
   * Redistributions in binary form must reproduce the above
copyright notice, this list of conditions and the following disclaimer
in the documentation and/or other materials provided with the
distribution.

THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS
"AS IS" AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT
LIMITED TO, THE IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR
A PARTICULAR PURPOSE ARE DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT
OWNER OR CONTRIBUTORS BE LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL,
SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT
LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES; LOSS OF USE,
DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON ANY
THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT
(INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE
OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.
```

## The Rust standard library

https://github.com/rust-lang/rust

`doctor/script/jass_checks.dll` (`jass_checks.so` on Linux), built from `native/jass_checks`, links the Rust standard
library, licensed MIT OR Apache-2.0; under the MIT terms:

```
Copyright (c) The Rust Project Contributors

Permission is hereby granted, free of charge, to any person obtaining a copy of this software and associated
documentation files (the "Software"), to deal in the Software without restriction, including without limitation the
rights to use, copy, modify, merge, publish, distribute, sublicense, and/or sell copies of the Software, and to permit
persons to whom the Software is furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all copies or substantial portions of the
Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE
WARRANTIES OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR
COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR
OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.
```

## Lupa and Lua

https://github.com/scoder/lupa, https://www.lua.org

The executable bundles Lupa's Lua 5.3 and Lua 5.4 runtimes, which check the Lua script of a ported map and of a map
opened in the World Editor.

```
Lupa: Copyright (c) 2010-2017 Stefan Behnel. All rights reserved.
Lua: Copyright (c) 1994-2017 Lua.org, PUC-Rio.

Both under the same terms:

Permission is hereby granted, free of charge, to any person obtaining a copy of this software and associated
documentation files (the "Software"), to deal in the Software without restriction, including without limitation the
rights to use, copy, modify, merge, publish, distribute, sublicense, and/or sell copies of the Software, and to permit
persons to whom the Software is furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all copies or substantial portions of the
Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE
WARRANTIES OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR
COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR
OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.
```

## UjAPI

https://github.com/UnryzeC/UjAPI

`doctor/port/.../ujapi_api.j` lists the types, constants and native declarations of the UjAPI `common.j` (the map
porter reads it to port maps made for the UjAPI); it is derived from the UjAPI files, under the MIT License:

```
MIT License

Copyright (c) 2022 Sandro Takaishvili

Permission is hereby granted, free of charge, to any person obtaining a copy of this software and associated
documentation files (the "Software"), to deal in the Software without restriction, including without limitation the
rights to use, copy, modify, merge, publish, distribute, sublicense, and/or sell copies of the Software, and to permit
persons to whom the Software is furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all copies or substantial portions of the
Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE
WARRANTIES OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR
COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR
OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.
```

## MemHackAPI

https://github.com/UnryzeC/MemHackAPI

`doctor/port/memhack_api.json` is a catalog of the MemHackAPI functions (name, parameter and return types, library,
file), taken from its source so the map porter can recognize the library inside a map (interoperability); the porter's
translation of those functions to Warcraft III 3.0 natives is this program's own code. The repository has no license
file. Credits, from its README: Unryze, leandrotp, Dracol1ch, Karaul0v, ENAlexey, Lord of the Ding, Aniki, LeP and
Vexorian.

## DzAPIConverter

https://github.com/garden-hose/DzAPIConverter

The bodies of the twelve `EX*` data natives in the port layer (`doctor/port/compat/part_natives.j`: the event damage
data, the item data strings and the ability data reads and writes) are adapted from `lib/DzCompat_YDWE_EX.j` of
DzAPIConverter, under the MIT License:

```
MIT License

Copyright (c) 2026 garden-hose

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
```

## Tinker

Tinker, by DooMWhite, reimplements the Warcraft Feature Extender for Warcraft III 1.26 and 1.28. The map size limits
of the classic game in `doctor/data/map_size.py` (where Game.dll checks the size of a map, and that the check only
applies to a game with other players) come from DooMWhite's reverse engineering in Tinker, used with permission.

## JassNative Editor and UMSWE

`doctor/ref/jn/TriggerData.txt` is the `UI\TriggerData.txt` of the JassNative Editor 2.2 (JassNative World Editor,
Copyright (c) BlacklightsC (평타천국) 2020-2021), unchanged: the trigger data of the Warcraft III 1.27 World Editor
(Blizzard Entertainment) with the additions of UMSWE 5.0 (by PitzerMike, after Scio and Starcraftfreak; Grimoire by
PipeDream) and of the JassNative Editor. "Open in World Editor" reads it only when the map is written for that editor
(the "JassNative Editor" choice, `--editor-version=jn`), so the triggers can use the functions and the variable types
that editor has. Neither editor ships a license for this file; it is included for interoperability, and no program code
of either editor is part of this program.

## The local machine translation: CTranslate2, SentencePiece and OPUS-MT

https://github.com/OpenNMT/CTranslate2 (MIT), https://github.com/google/sentencepiece (Apache-2.0),
https://github.com/Helsinki-NLP/Opus-MT

The program bundles CTranslate2 and SentencePiece (their license texts are below, with the other Python packages), which
run the translation models of "Local machine translation" (the Translation tab, `doctor/translation/machine_translate.py`).
The models are not in the program: the one a map needs is downloaded the first time, from the release
`translation-models` of this repository. They are the OPUS-MT models of the University of Helsinki (Joerg Tiedemann and
the OPUS-MT team), converted to the CTranslate2 format with their weights unchanged; each comes with its model card and
license (CC-BY 4.0 or Apache-2.0) inside its zip file. Tiedemann, J. and Thottingal, S. (2020): OPUS-MT - Building open
translation services for the World (EAMT 2020).

## The text in images: onnxruntime and PaddleOCR

https://github.com/microsoft/onnxruntime (MIT), https://github.com/PaddlePaddle/PaddleOCR (Apache-2.0),
https://github.com/RapidAI/RapidOCR (Apache-2.0)

The program bundles onnxruntime (its license is below, with the other Python packages), which runs the text reader of
"Also read the text in the images" (`doctor/translation/image_ocr.py`, `image_translate.py`). The models are not in the
program: they are downloaded the first time, from the release `translation-models` of this repository. They are the
PaddleOCR models (PP-OCRv6 small, PP-OCRv5 mobile) in the ONNX format published by RapidOCR, unchanged, under the
Apache License 2.0 (inside each zip). The text is drawn with the font Pillow carries, Aileron (SIL Open Font License).

## Projects used by 1.7.9 (MIT License)

Each item below is under the MIT License (the text follows the list), with its own copyright line:

- war3-model 4.0.1, https://github.com/4eb0da/war3-model, Copyright (c) 2017-2023 4eb0da: `ui/vendor/war3-model.browser.js`
  (the MDX/MDL parser and WebGL renderer of the 3D model preview), unchanged. It bundles gl-matrix 3.3.0,
  https://github.com/toji/gl-matrix, Copyright (c) 2015-2020 Brandon Jones, Colin MacKenzie IV. Their license files are
  next to it in `ui/vendor/`.
- w3gjs, https://github.com/PBug90/w3gjs, Copyright (c) 2018-2026 PBug90: `replay_read` is a Python port of its replay
  parsers (the header and block layout, the encoded game settings, the Reforged player records, the game data blocks and
  the action table).
- Tasyen/FDF, https://github.com/Tasyen/FDF, Copyright (c) 2020 Tasyen: the frame type and keyword lists and the rules of
  `fdf_lint`.
- War3Net, https://github.com/Drake53/War3Net, Copyright (c) Drake53 and Contributors: `doctor/ref/game_builds.json` is
  its `GameBuilds.json`.
- WC3MapDeprotector, https://github.com/speige/WC3MapDeprotector, Copyright (c) 2023 WC3MapRepacker: the methods of
  `slk_objects` (ObjectEditor.cs) and of the folder by name scan and the extension families of the name recovery; the
  code is new.
- warcraft-3-mcp-server, https://github.com/YElwiddi/warcraft-3-mcp-server, Copyright (c) 2026 YElwiddi: the sentinel
  scheme of `durable_wct` (src/durable.ts); the code is new.
- mdx-m3-viewer, https://github.com/flowtsohg/mdx-m3-viewer, Copyright (c) 2013-2021 Chananya Freiman; W3ModelViewer,
  https://github.com/Darithos/W3ModelViewer, Copyright (c) 2026 Darithos; ReterasModelStudio,
  https://github.com/Retera/ReterasModelStudio, Copyright (c) 2023 Retera: the checks of `mdx_sanity` and `blp_check`,
  the model layouts by version (1800 included) and the key reduction of `mdx_optimize`, reimplemented.
- jass-minifier, https://github.com/flowtsohg/jass-minifier, and JASS-Constant-Inliner,
  https://github.com/Son-Guhun/JASS-Constant-Inliner: the approach of `jass_minify`, reimplemented.

```
MIT License

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
```

## wc3ctl and 5211MapCheck (Apache License 2.0)

- wc3ctl, https://github.com/GodMephisto/wc3ctl, Copyright 2026 GodMephisto: the ten natives renamed in patch 1.29
  (`script_lint.NATIVE_RENAMES`, from NativeRenames.cs), changed into a Python table; the other checks taken from it
  (the inherited requirement, the abilities kept on the object, the model paths, the loops, the leaks, the portrait
  versions, the load markers) are reimplemented from its descriptions.
- 5211MapCheck, https://github.com/sumneko/5211MapCheck, Copyright sumneko: the six signatures of `cheat_signs`
  (src/check.lua), changed into a Python table; the lobby rule of `map_rules` is reimplemented.

Both are licensed under the Apache License, Version 2.0 (https://www.apache.org/licenses/LICENSE-2.0); the copied
tables were changed in form (Lua and C# to Python) by this program.

## jasshelper (zlib License)

https://github.com/shuen4/jasshelper (Vexorian's jasshelper): the six type names that `common.j` declares as handles but
the engine counts by reference, and the way a returned local goes through a global (`handle_nulls`), rewritten in
Python. Copyright (c) 2006 Vexorian. This software is provided 'as-is', without any express or implied warranty; the
origin of the software must not be misrepresented; altered versions must be plainly marked as such (this is one: a
rewrite in Python); this notice may not be removed or altered from any source distribution.

## The site

The site (`web/build_site.py`) ships, unchanged, Pyodide (https://github.com/pyodide/pyodide, MPL-2.0) with its CPython
(PSF License), numpy (BSD-3-Clause) and Pillow (MIT-CMU), as published by the Pyodide project; their license texts come
inside the files the site serves (`pyodide/`).
