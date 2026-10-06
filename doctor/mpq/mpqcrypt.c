/* mpqcrypt.c - the MPQ block decryption (StormLib's DecryptMpqBlock, SBaseCommon.cpp) in native code, for
 * mpqlib.decrypt_bytes: the same arithmetic as the Python loop, about 200 times faster. Built by mpqcrypt.py as a
 * Windows DLL (the exe, through ctypes) and as WebAssembly (the site, through worker.js). The data is decrypted in
 * place, little-endian dwords; the bytes after the last whole dword are left as they are (as in the Python). */
#include <stdint.h>
#include <stddef.h>

static uint32_t table[0x500];
static int ready = 0;

static void prepare(void) {
    uint32_t seed = 0x00100001;
    for (int i = 0; i < 0x100; i++) {
        for (int idx = i; idx < 0x500; idx += 0x100) {
            seed = (seed * 125 + 3) % 0x2AAAAB;
            uint32_t t = (seed & 0xFFFF) << 16;
            seed = (seed * 125 + 3) % 0x2AAAAB;
            t |= seed & 0xFFFF;
            table[idx] = t;
        }
    }
    ready = 1;
}

#if defined(_WIN32)
#define EXPORT(name) __declspec(dllexport)
#elif defined(__wasm__)
#define EXPORT(name) __attribute__((export_name(name)))
#else
#define EXPORT(name) __attribute__((visibility("default")))
#endif

EXPORT("mpq_decrypt") void mpq_decrypt(uint8_t *data, size_t length, uint32_t key) {
    if (!ready)
        prepare();
    uint32_t seed = 0xEEEEEEEE;
    size_t n = length / 4;
    for (size_t i = 0; i < n; i++) {
        uint8_t *p = data + 4 * i;
        uint32_t v = (uint32_t)p[0] | ((uint32_t)p[1] << 8) | ((uint32_t)p[2] << 16) | ((uint32_t)p[3] << 24);
        seed += table[0x400 + (key & 0xFF)];
        v ^= key + seed;
        key = ((~key << 0x15) + 0x11111111) | (key >> 0x0B);
        seed = v + seed + (seed << 5) + 3;
        p[0] = (uint8_t)v;
        p[1] = (uint8_t)(v >> 8);
        p[2] = (uint8_t)(v >> 16);
        p[3] = (uint8_t)(v >> 24);
    }
}

#if defined(__wasm__)
/* WebAssembly: a buffer of `n` bytes after the program's data (the memory grows to fit); the page copies the block in,
 * calls mpq_decrypt on it and copies it out. One block at a time. */
extern unsigned char __heap_base;
EXPORT("mpq_buffer") uint8_t *mpq_buffer(size_t n) {
    size_t base = (size_t)&__heap_base;
    size_t have = __builtin_wasm_memory_size(0) * 65536;
    if (base + n > have)
        __builtin_wasm_memory_grow(0, (base + n - have + 65535) / 65536);
    return (uint8_t *)base;
}
#endif
