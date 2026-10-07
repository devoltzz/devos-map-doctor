// The MPQ hot loops (mpqcrypt.c as WebAssembly) handed to the engine.
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
  const keys = (enc0, enc1, d0) => {
    const ptr = buffer(2048);
    const n = mpq_key_candidates(enc0, enc1, d0, ptr);
    return new Uint32Array(memory.buffer, ptr, 2 * n).slice();
  };
  const output = (ptr, length, n) => (n < 0 ? undefined : new Uint8Array(memory.buffer, ptr + length, n).slice());
  const huffman = (data, cap) => {
    const ptr = copyIn(data, cap);
    return output(ptr, data.length, mpq_huffman(ptr, data.length, ptr + data.length, cap));
  };
  const adpcm = (data, channels, cap) => {
    const ptr = copyIn(data, cap);
    return output(ptr, data.length, mpq_adpcm(ptr, data.length, channels, ptr + data.length, cap));
  };
  const explode = (data, expected) => {
    const ptr = copyIn(data, expected);
    return output(ptr, data.length, mpq_explode(ptr, data.length, ptr + data.length, expected));
  };
  return { decrypt, keys: mpq_key_candidates ? keys : null, huffman: mpq_huffman ? huffman : null,
    adpcm: mpq_adpcm ? adpcm : null, explode: mpq_explode ? explode : null };
}
