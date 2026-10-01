# Reads and changes the name a map shows in the game list (the HM3W header).
import io
import struct


TAM = 512
OFF_NAME = 8


def renomeia(file_path, fname, escrever=True):
    with open(file_path, 'r+b') as f:
        header = f.read(TAM)
        if header[:4] != b'HM3W':
            raise ValueError('%s does not start with HM3W' % file_path)
        end_pos = header.index(b'\x00', OFF_NAME)
        before = header[OFF_NAME:end_pos].decode('utf-8', 'replace')
        if before == fname:
            return False, before
        flags = header[end_pos + 1:end_pos + 5]
        new = fname.encode('utf-8')
        fields = header[end_pos:end_pos + 9]
        end_old = end_pos + 9
        end_new = OFF_NAME + len(new) + 9
        if end_new > TAM:
            raise ValueError('the name %r leaves no room for flags/max_players' % fname)
        if end_new > end_old and any(header[end_old:end_new]):
            raise ValueError('the name %r would push nonzero bytes out of the HM3W' % fname)
        body = header[:OFF_NAME] + new + fields
        body += b'\x00' * max(0, end_old - end_new)
        body += header[len(body):]
        fim2 = body.index(b'\x00', OFF_NAME)
        if body[fim2 + 1:fim2 + 5] != flags:
            raise ValueError('the HM3W flags changed (%r -> %r)' % (flags, body[fim2 + 1:fim2 + 5]))
        if escrever:
            f.seek(0)
            f.write(body)
        return True, before


def name_hm3w(p):
    with io.open(p, 'rb') as f:
        header = f.read(0x200)
    if header[:4] != b'HM3W':
        return '(no HM3W: %r)' % header[:4]
    n = struct.unpack_from('<I', header, 4)[0] if False else None
    end_pos = header.index(b'\x00', 8)
    return header[8:end_pos].decode('utf-8', 'replace')
