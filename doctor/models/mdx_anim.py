# Reads the sequences and geoset animations of an MDX model.
import struct

from doctor.models.mdx_tex import cstr



def read_sequences(data, off, n):
    output = []
    for i in range(n // 132):
        p = off + i * 132
        fname = cstr(data[p:p + 80])
        begin, end_pos = struct.unpack_from('<2I', data, p + 80)
        mov, laco, rarity = struct.unpack_from('<fII', data, p + 88)
        output.append({'i': i, 'fname': fname, 'begin': begin, 'end_pos': end_pos,
                       'mov': mov, 'laco': laco, 'rarity': rarity})
    return output

