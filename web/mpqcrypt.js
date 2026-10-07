// mpqcrypt.js - the MPQ's hot loops in native code (the engine's mpqcrypt.c, built as WebAssembly by build_site.py):
// mpqNative(wasm bytes) -> {decrypt, keys, huffman, adpcm, explode}. The worker gives them to the engine as
// `mpqDecrypt`, `mpqKeys`, `mpqHuffman`, `mpqAdpcm` and `mpqExplode` (mpqcrypt.py hands them to mpqlib, mpqread,
// mpq_wave and pkware): the decryption ~200x the Python loop, the sound sectors ~100x, the imploded sectors ~120x, the
// same bytes. The input is copied into the module's memory (the output buffer right after it), worked on there and
// copied out; one call at a time, the memory grows to the biggest one.
export function mpqNative(wasmBytes) {
  const mod = new WebAssembly.Module(wasmBytes);
  const { memory, mpq_buffer: buffer, mpq_decrypt, mpq_key_candidates, mpq_huffman, mpq_adpcm, mpq_explode } =
    new WebAssembly.Instance(mod, {}).exports;
  const copyIn = (data, extra) => {
    const ptr = buffer(data.length + extra);
    new Uint8Array(memory.buffer, ptr, data.length).set(data);
    return ptr;
  };
  const decrypt = (data, key) => {
    const ptr = copyIn(data, 0);
    mpq_decrypt(ptr, data.length, key);
    return new Uint8Array(memory.buffer, ptr, data.length).slice();
  };
  // the candidate keys of a nameless encrypted file: the pairs (key, second dword) as a Uint32Array
  const keys = (enc0, enc1, d0) => {
    const ptr = buffer(2048);
    const n = mpq_key_candidates(enc0, enc1, d0, ptr);
    return new Uint32Array(memory.buffer, ptr, 2 * n).slice();
  };
  // the sound sectors: the output (at most `cap` bytes, right after the input) or undefined when the stream is invalid
  // (None in Python: it redoes the sector and raises its own error; a null would arrive as jsnull)
  const output = (ptr, length, n) => (n < 0 ? undefined : new Uint8Array(memory.buffer, ptr + length, n).slice());
  const huffman = (data, cap) => {
    const ptr = copyIn(data, cap);
    return output(ptr, data.length, mpq_huffman(ptr, data.length, ptr + data.length, cap));
  };
  const adpcm = (data, channels, cap) => {
    const ptr = copyIn(data, cap);
    return output(ptr, data.length, mpq_adpcm(ptr, data.length, channels, ptr + data.length, cap));
  };
  // 1.6.4: a PKWARE DCL (implode) sector of `expected` bytes
  const explode = (data, expected) => {
    const ptr = copyIn(data, expected);
    return output(ptr, data.length, mpq_explode(ptr, data.length, ptr + data.length, expected));
  };
  return { decrypt, keys: mpq_key_candidates ? keys : null, huffman: mpq_huffman ? huffman : null,
    adpcm: mpq_adpcm ? adpcm : null, explode: mpq_explode ? explode : null };
}
