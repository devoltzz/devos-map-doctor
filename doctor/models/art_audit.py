# Lists the art a map asks for and where it is: in the map, in the game, or nowhere.
import struct



B = chr(92)
def emitters(d):
    out = []
    p = 4
    while p + 8 <= len(d):
        tag = d[p:p + 4]
        n = struct.unpack_from('<I', d, p + 4)[0]
        if tag == b'PREM':
            q, end_pos = p + 8, p + 8 + n
            while q + 8 <= end_pos:
                sz, no = struct.unpack_from('<II', d, q)
                r = q + 4 + no + 16
                if sz <= 0 or no < 96 or r + 260 > q + sz:
                    break
                cpath = d[r:r + 260].split(b'\0')[0].decode('latin-1')
                if cpath:
                    out.append(cpath)
                q += sz
        p += 8 + n
    return out

