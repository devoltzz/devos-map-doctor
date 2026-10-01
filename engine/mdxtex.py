# Reads the texture chunk of an MDX model, in both formats.
def mdx_textures(data):
    out = []
    if data[:4] != b'MDLX':
        return out
    p, n = 4, len(data)
    while p + 8 <= n:
        tag = data[p:p + 4]
        size = int.from_bytes(data[p + 4:p + 8], 'little')
        body = p + 8
        if body + size > n:
            break
        if tag == b'TEXS':
            q, end = body, body + size
            fixed_fields = size % 268 == 0
            while q + 4 <= end:
                ln = int.from_bytes(data[q:q + 4], 'little')
                if not fixed_fields and 4 <= ln <= end - q:
                    raw = data[q + 4:q + ln]
                    q += ln
                elif q + 268 <= end:
                    raw = data[q + 4:q + 264]
                    q += 268
                else:
                    break
                fname = raw.split(b'\0')[0].decode('utf-8', 'replace')
                if fname:
                    out.append(fname)
        p = body + size
    return out
