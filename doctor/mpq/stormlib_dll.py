# Opens an archive with the StormLib DLL when it is there, as an independent check.
import ctypes
import os
import struct


HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
DLL_DEFAULT = os.path.join(ROOT, 'terceiros', 'WC3MapDeprotector', 'WC3MapRepacker', 'StormLib_x64.dll')

MPQ_OPEN_READ_ONLY = 0x00000100
MPQ_OPEN_NO_LISTFILE = 0x00010000
MPQ_OPEN_NO_ATTRIBUTES = 0x00020000
MPQ_FLAG_READ_ONLY = 0x00000001
MPQ_FLAG_MALFORMED = 0x00000004
SFileMpqHeaderOffset = 5
SFileMpqHashTableSize = 18
SFileMpqBlockTableSize = 22
SFileMpqSectorSize = 35
SFileMpqNumberOfFiles = 36
SFileMpqFlags = 39

_dll = None
_error_dll = None


def dll(file_path=None):
    global _dll, _error_dll
    if _dll is not None or _error_dll is not None:
        return _dll
    p = file_path or os.environ.get('STORMLIB_DLL') or DLL_DEFAULT
    if struct.calcsize('P') != 8 or not os.path.isfile(p):
        _error_dll = 'no_dll'
        return None
    try:
        d = ctypes.WinDLL(p, use_last_error=True)
    except OSError as e:
        _error_dll = 'sem_dll: %s' % e
        return None
    d.SFileOpenArchive.argtypes = [ctypes.c_wchar_p, ctypes.c_uint, ctypes.c_uint, ctypes.POINTER(ctypes.c_void_p)]
    d.SFileOpenArchive.restype = ctypes.c_bool
    d.SFileCloseArchive.argtypes = [ctypes.c_void_p]
    d.SFileCloseArchive.restype = ctypes.c_bool
    d.SFileGetFileInfo.argtypes = [ctypes.c_void_p, ctypes.c_int, ctypes.c_void_p, ctypes.c_uint,
                                   ctypes.POINTER(ctypes.c_uint)]
    d.SFileGetFileInfo.restype = ctypes.c_bool
    d.SFileOpenFileEx.argtypes = [ctypes.c_void_p, ctypes.c_char_p, ctypes.c_uint, ctypes.POINTER(ctypes.c_void_p)]
    d.SFileOpenFileEx.restype = ctypes.c_bool
    d.SFileReadFile.argtypes = [ctypes.c_void_p, ctypes.c_void_p, ctypes.c_uint, ctypes.POINTER(ctypes.c_uint),
                                ctypes.c_void_p]
    d.SFileReadFile.restype = ctypes.c_bool
    d.SFileCloseFile.argtypes = [ctypes.c_void_p]
    d.SFileCloseFile.restype = ctypes.c_bool
    d.SFileGetFileSize.argtypes = [ctypes.c_void_p, ctypes.POINTER(ctypes.c_uint)]
    d.SFileGetFileSize.restype = ctypes.c_uint
    d.SFileHasFile.argtypes = [ctypes.c_void_p, ctypes.c_char_p]
    d.SFileHasFile.restype = ctypes.c_bool
    _dll = d
    return d


def _info(d, h, classe, fmt):
    buf = ctypes.create_string_buffer(struct.calcsize(fmt))
    n = ctypes.c_uint(0)
    if not d.SFileGetFileInfo(h, classe, buf, len(buf.raw), ctypes.byref(n)):
        return None
    return struct.unpack(fmt, buf.raw)[0]


def _open_handle(d, file_path):
    h = ctypes.c_void_p()
    ok = d.SFileOpenArchive(os.path.abspath(file_path), 0,
                            MPQ_OPEN_READ_ONLY | MPQ_OPEN_NO_LISTFILE | MPQ_OPEN_NO_ATTRIBUTES, ctypes.byref(h))
    if not ok:
        return None, ctypes.get_last_error()
    return h, 0


def opens(file_path, dll_path=None):
    d = dll(dll_path)
    if d is None:
        return {'opens': None, 'err': _error_dll or 'no_dll'}
    h, err = _open_handle(d, file_path)
    if h is None:
        return {'opens': False, 'err': 'SFileOpenArchive: error %d' % err}
    try:
        flags = _info(d, h, SFileMpqFlags, '<I')
        sector_bytes = _info(d, h, SFileMpqSectorSize, '<I')
        off = _info(d, h, SFileMpqHeaderOffset, '<Q')
        r = {'opens': True, 'err': None, 'flags': flags, 'sector_bytes': sector_bytes, 'offset_header': off,
             'hash_n': _info(d, h, SFileMpqHashTableSize, '<I'), 'block_n': _info(d, h, SFileMpqBlockTableSize, '<I'),
             'file_set': _info(d, h, SFileMpqNumberOfFiles, '<I')}
        if off is None or sector_bytes is None or sector_bytes & (sector_bytes - 1) or sector_bytes < 512:
            r['err'] = 'enum_divergente'
            r['is_malformed'] = None
        else:
            r['is_malformed'] = bool(flags & MPQ_FLAG_MALFORMED) if flags is not None else None
            r['read_only'] = bool(flags & MPQ_FLAG_READ_ONLY) if flags is not None else None
        return r
    finally:
        d.SFileCloseArchive(h)


def read_data(file_path, name_list, dll_path=None, cap=256 << 20):
    d = dll(dll_path)
    if d is None:
        return dict((n, None) for n in name_list)
    h, _err = _open_handle(d, file_path)
    if h is None:
        return dict((n, None) for n in name_list)
    out = {}
    try:
        for n in name_list:
            f = ctypes.c_void_p()
            if not d.SFileOpenFileEx(h, n.encode('utf-8', 'surrogateescape'), 0, ctypes.byref(f)):
                out[n] = None
                continue
            try:
                high = ctypes.c_uint(0)
                sz = d.SFileGetFileSize(f, ctypes.byref(high))
                if sz == 0xFFFFFFFF or high.value or sz > cap:
                    out[n] = None
                    continue
                buf = ctypes.create_string_buffer(max(sz, 1))
                read_count = ctypes.c_uint(0)
                ok = d.SFileReadFile(f, buf, sz, ctypes.byref(read_count), None)
                out[n] = (
                    buf.raw[: read_count.value] if (ok or read_count.value == sz) and read_count.value == sz else None
                )
            finally:
                d.SFileCloseFile(f)
    finally:
        d.SFileCloseArchive(h)
    return out
