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

## The site

The site (`web/build_site.py`) ships, unchanged, Pyodide (https://github.com/pyodide/pyodide, MPL-2.0) with its CPython
(PSF License), numpy (BSD-3-Clause) and Pillow (MIT-CMU), as published by the Pyodide project; their license texts come
inside the files the site serves (`pyodide/`).
