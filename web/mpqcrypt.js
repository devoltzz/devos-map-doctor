// mpqcrypt.js - the MPQ decryption in native code (the engine's mpqcrypt.c, built as WebAssembly by build_site.py):
// mpqDecryptor(wasm bytes) -> (bytes, key) => decrypted bytes. The worker gives it to the engine as `mpqDecrypt`
// (mpqcrypt.py hands it to mpqlib.decrypt_bytes): ~200x the Python loop, the same bytes. The block is copied into the
// module's memory, decrypted there and copied out; one block at a time, the memory grows to the biggest one.
export function mpqDecryptor(wasmBytes) {
  const mod = new WebAssembly.Module(wasmBytes);
  const { memory, mpq_buffer: buffer, mpq_decrypt: decrypt } = new WebAssembly.Instance(mod, {}).exports;
  return (data, key) => {
    const ptr = buffer(data.length);
    new Uint8Array(memory.buffer, ptr, data.length).set(data);
    decrypt(ptr, data.length, key);
    return new Uint8Array(memory.buffer, ptr, data.length).slice();
  };
}
