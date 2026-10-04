# Diagnoses a map, removes its protection and prepares it for the World Editor.
import contextlib
import io
import os
import re
import shutil
import sys
import tempfile

from doctor.mpq import mpqlib as M
from doctor.mpq import mpqread
from doctor.mpq import mpqdoctor
from doctor.mpq import mpqnames
from doctor.mpq import mpqadd
from doctor.mpq import mpq_rebuild
from doctor.fix import editor_prep
from doctor.fix import object_ids
from doctor.mpq import sprotect_fix
from doctor.fix import inflated_counts
from doctor.fix import doodads
from doctor.fix import duplicate_textures
from doctor.triggers import wtg_triggers
from doctor.mpq import ntfs_undo
from doctor.data import slk_patch

HERE = os.path.dirname(os.path.abspath(__file__))
KK = os.path.normpath(os.path.join(HERE, '..', 'kk'))

FREE, DELETED = 0xFFFFFFFF, 0xFFFFFFFE
MASK = mpqread.BLOCK_MASK
SPECIAL_FILES = ('(listfile)', '(attributes)', '(signature)')
EDITOR_FILES = ('war3map.wtg', 'war3map.wct', 'war3map.w3r', 'war3map.w3c', 'war3mapUnits.doo')
OBJECT_IDS_FILES = tuple('war3map.' + e for e, _n, _t in object_ids.TYPES) + ('war3map.j', 'scripts\\war3map.j')
HEADER_MARKS = {0x504F7856: 'vexorian', 0x00200102: 'w3p', 0x2E324750: 'pg2', 0x6F725053: 'sprotect'}
EDITOR_BLOCKERS = ('read_only', 'fake_header', 'missing_hm3w', 'virtual_tables', 'sprotect', 'kk_encrypted',
                   'scrambled_ids', 'locale_decoy', 'inflated_counts', 'invalid_doodad', 'unreadable_tables',
                   'script_kkwe', 'script_j2b')
BUTTON3_ONLY = ('inflated_counts', 'invalid_doodad', 'script_kkwe', 'script_j2b')
EDITOR_SCRIPTS = ('jass', 'lua', 'kkwe', 'j2b')
DATA_ONLY = ('slk_file_column', 'slk_levels', 'slk_buttonpos', 'fdf_stray_comment', 'slk_id_list', 'slk_quoted_numbers')
SLK_CODE = {'file_column': 'slk_file_column', 'levels': 'slk_levels', 'buttonpos': 'slk_buttonpos',
            'fdf_comment': 'fdf_stray_comment', 'id_lists': 'slk_id_list', 'quoted_numbers': 'slk_quoted_numbers'}


def _nothing(*_a, **_k):
    pass


def step_on(options, hash_key):
    return options is None or options.get(hash_key, True) is not False


def steps(diag):
    code_part = set(x['code'] for x in diag.get('protections') or [])
    mpq = code_part - set(BUTTON3_ONLY) - set(DATA_ONLY)
    ids = next((x for x in diag.get('protections') or [] if x['code'] == 'scrambled_ids'), None)
    ed = (diag.get('editor') or {}).get('status')
    out = []

    def place(action_code, hash_key, applies, locked=False, reason=None, default_on=True):
        out.append({'action_code': action_code, 'hash_key': hash_key, 'applies': bool(applies), 'locked': bool(locked),
                    'reason': reason if (locked or not applies) else None, 'default_on': bool(default_on and applies)})

    place('fix', 'mpq', mpq, reason=None if mpq else 'no_protection')
    place(
        'fix', 'fake_list', mpq and 'fake_files' in code_part, reason=None if 'fake_files' in code_part else 'no_fakes'
    )
    place('fix', 'listing', mpq and not has_virtual_tables(diag), reason=None if mpq else 'no_protection')
    place('fix', 'ids', ids and ids.get('fixable'), reason=None if ids else 'no_ids')
    for problem in slk_patch.PROBLEMS:
        present = SLK_CODE[problem] in code_part
        place('fix', 'dados:' + problem, present, reason=None if present else 'tables_ok')
    needs_work = ed == 'needs_work' or bool(code_part & set(DATA_ONLY))
    blocks_editor = code_part & set(EDITOR_BLOCKERS)
    place(
        'editor',
        'unprotection',
        blocks_editor,
        locked=True,
        reason='editor_requires' if blocks_editor else 'no_protection',
    )
    script = diag.get('script')
    place('editor', 'script_restore', script in ('kkwe', 'j2b'), locked=True,
          reason='editor_requires' if script in ('kkwe', 'j2b') else 'not_compiled')
    place('editor', 'editor_only_files', ed == 'needs_work', locked=True, reason='editor_requires' if ed == 'needs_work'
          else 'editor_is_ready')
    for code, hash_key in (('inflated_counts', 'inflated_counts'), ('invalid_doodad', 'invalid_doodads')):
        place(
            'editor',
            hash_key,
            code in code_part,
            locked=True,
            reason='editor_crashes' if code in code_part else 'not_needed',
        )
    for hash_key in ('gui_triggers', 'script_objects', 'safe_units'):
        place('editor', hash_key, ed == 'needs_work', reason=None if ed == 'needs_work' else 'editor_is_ready')
    for problem in slk_patch.PROBLEMS:
        present = SLK_CODE[problem] in code_part
        place('editor', 'dados:' + problem, present and needs_work, reason=None if present else 'tables_ok')
    return out


EXTRAS = ('models', 'model_names', 'portraits', 'data_pointers', 'uabi', 'preload', 'single_player', 'card',
          'translation', 'shrink')


def apply_extras(entry, output, extras, progress=None):
    p = progress or _nothing
    out = {'relatos': {}, 'failures': {}, 'output': None}
    tmp = tempfile.mkdtemp(prefix='devos_map_doctor_extras_')
    src = entry
    try:
        for i, extra in enumerate(EXTRAS):
            param = (extras or {}).get(extra)
            if not param:
                continue
            p('extra_' + extra)
            t = os.path.join(tmp, '%d_%s%s' % (i, extra, os.path.splitext(entry)[1] or '.w3x'))
            try:
                with quiet():
                    if extra == 'models':
                        from doctor.models import model_check
                        details = model_check.fix(src, t)
                    elif extra == 'model_names':
                        from doctor.fix import model_names
                        details = model_names.fix(src, t)
                    elif extra == 'portraits':
                        from doctor.models import model_check
                        details = model_check.fix(src, t, what=('portrait_camera',))
                    elif extra == 'data_pointers':
                        from doctor.fix import data_pointers
                        details = data_pointers.fix(src, t)
                    elif extra == 'uabi':
                        from doctor.fix import uabi_runtime
                        details = uabi_runtime.fix(src, t)
                    elif extra == 'preload':
                        from doctor.fix import early_preload
                        details = early_preload.fix(src, t)
                    elif extra == 'single_player':
                        from doctor.fix import single_player
                        details = single_player.unlock(src, t)
                    elif extra == 'card':
                        from doctor.viewers import map_card
                        details = map_card.write(src, t, param)
                    elif extra == 'translation':
                        from doctor.translation import translation_io
                        details = translation_io.import_(src, param, t)
                    else:
                        from doctor.fix import shrink
                        details = shrink.shrink(src, t, param if isinstance(param, dict) else None)
                if not os.path.isfile(t):
                    raise RuntimeError(
                        (details or {}).get('error') or (details or {}).get('reason') or 'nothing was written'
                    )
                out['relatos'][extra] = details
                src = t
            except (Exception, SystemExit) as e:
                out['failures'][extra] = _error(e)
        if src != entry:
            shutil.copyfile(src, output)
            out['output'] = output
    finally:
        shutil.rmtree(tmp, ignore_errors=True)
    return out


def deixados_de_proposito(codes, options):
    out = set(SLK_CODE[x] for x in slk_patch.PROBLEMS if not step_on(options, 'dados:' + x))
    if not step_on(options, 'mpq'):
        out |= set(codes) - set(BUTTON3_ONLY) - set(DATA_ONLY)
    if not step_on(options, 'ids'):
        out.add('scrambled_ids')
    if not step_on(options, 'fake_list'):
        out.add('fake_files')
    return out


def has_virtual_tables(diag):
    return 'virtual_tables' in set(x['code'] for x in diag.get('protections') or [])


class _Record(io.TextIOBase):
    def __init__(self):
        super().__init__()
        self.pieces = []

    def write(self, s):
        self.pieces.append(s)
        return len(s)

    def reconfigure(self, **_k):
        pass

    def body_text(self):
        return ''.join(self.pieces)


@contextlib.contextmanager
def quiet(reg=None):
    reg = _Record() if reg is None else reg
    old_streams = sys.stdout, sys.stderr
    sys.stdout = sys.stderr = reg
    try:
        yield reg
    finally:
        sys.stdout, sys.stderr = old_streams


def _read(a, fname):
    try:
        r = a.find_locale(fname) if a.find(fname) else None
        return a.read(fname, bi=r[1]) if r else None
    except Exception:
        return None


def _valid_for_game(a, fname):
    f = a.find(fname)
    if f and mpqnames.is_valid_name(a, f[1], fname):
        return f[1]
    if f:
        f2 = a.find_locale(fname)
        if f2 and f2[1] != f[1] and mpqnames.is_valid_name(a, f2[1], fname):
            return f2[1]
    return None


def _open(file_path):
    with quiet():
        return mpqread.Archive(file_path)


def map_name(d):
    if d[:4] != b'HM3W':
        return None
    end_pos = d.find(b'\0', 8, 8 + 512)
    n = d[8:end_pos if end_pos > 0 else 8 + 256].decode('utf-8', 'replace')
    return re.sub(r'\|[cC][0-9A-Fa-f]{8}|\|[rR]', '', n).strip() or None


def count_fake(a):
    n = 0
    for i in range(a.hash_n_read):
        bi = a.ht[i * 4 + 3]
        if bi != FREE and bi != DELETED and (bi & MASK) >= len(a.blocks):
            n += 1
    return n


def _live_blocks(a):
    live = set()
    for i in range(a.hash_n_read):
        bi = a.ht[i * 4 + 3]
        if bi == FREE or bi == DELETED:
            continue
        b = bi & MASK
        if b < len(a.blocks) and a.blocks[b][3] & 0x80000000:
            live.add(b)
    return live


def listfile_names(a):
    lf = _read(a, '(listfile)') or b''
    return [
        line.strip().replace('/', '\\') for line in lf.decode('utf-8', 'surrogateescape').splitlines() if line.strip()
    ]


def _listfile_status(a):
    live = _live_blocks(a)
    lf = _read(a, '(listfile)')
    named = set()
    for n in SPECIAL_FILES:
        f = a.find(n)
        if f:
            named.add(f[1])
    if lf:
        for line in lf.decode('utf-8', 'surrogateescape').splitlines():
            n = line.strip()
            if n:
                f = a.find(n)
                if f:
                    named.add(f[1])
    named &= live
    status = 'absent' if lf is None else ('ok' if len(named) >= len(live) else 'incomplete')
    return {'status': status, 'named': len(named), 'file_set': len(live)}


_RESTORED = {}
_RESTORED_FOLDER = []


def _restored_folder():
    if not _RESTORED_FOLDER:
        import atexit
        p = tempfile.mkdtemp(prefix='devos_map_doctor_ntfs_')
        _RESTORED_FOLDER.append(p)
        atexit.register(shutil.rmtree, p, True)
    return _RESTORED_FOLDER[0]


def restore_copy(file_path, d=None):
    try:
        hash_key = (os.path.abspath(file_path), os.path.getsize(file_path), os.path.getmtime(file_path))
    except OSError:
        hash_key = None
    if hash_key in _RESTORED and (_RESTORED[hash_key][0] is None or os.path.isfile(_RESTORED[hash_key][0])):
        return _RESTORED[hash_key]
    if d is None:
        with open(file_path, 'rb') as f:
            d = f.read()
    out, details = ntfs_undo.undo(d, file_path)
    res = (None, details)
    if out is not None:
        if details.get('lost'):
            from doctor.mpq import carver
            try:
                with quiet():
                    rep, rr = carver.repair_tables(out, len(out) - details['lost'], file_path)
            except Exception as e:
                rep, rr = None, {'err': _error(e)}
            details['tables'] = dict((k, v) for k, v in rr.items() if k not in ('name_list', 'inserted_names'))
            if rep is not None:
                out = rep
        ext = os.path.splitext(file_path)[1] or '.w3x'
        t = os.path.join(_restored_folder(), 'restored_%d%s' % (len(_RESTORED), ext))
        with open(t, 'wb') as f:
            f.write(out)
        res = (t, details)
    if hash_key:
        _RESTORED[hash_key] = res
    return res


def _diagnose_ntfs_copy(file_path, d, progress, depth, extra_ids):
    t, details = restore_copy(file_path, d)
    if t is None:
        return None
    r = diagnose(t, progress, depth, extra_ids, _ntfs=False)
    r['file_name'] = os.path.abspath(file_path)
    r['byte_size'] = len(d)
    r['restored'] = t
    info = dict((k, details.get(k)) for k in ('lznt1', 'lost', 'grown') if details.get(k))
    tab = details.get('tables') or {}
    info.update(dict(('tables_' + k, tab[k]) for k in ('lost_blocks', 'lost_slots', 'rebuilt', 'inserted',
                                                           'unnamed', 'err') if tab.get(k)))
    info['code'] = 'ntfs_copy'
    r['protections'].insert(0, info)
    if r['fixable'] == 'nothing':
        r['fixable'] = 'yes'
    if (r.get('editor') or {}).get('status') == 'ready':
        r['editor']['status'] = 'needs_work'
    return r


def diagnose(file_path, progress=None, depth=0, extra_ids=(), _ntfs=True):
    p = progress or _nothing
    r = {'file_name': os.path.abspath(file_path), 'byte_size': os.path.getsize(file_path), 'mpq': None, 'fname': None,
         'protections': [], 'warnings': [], 'script': None, 'listfile': None, 'editor': {}, 'err': None,
         'fixable': None}

    def prot(code, **info):
        info['code'] = code
        r['protections'].append(info)

    p('read_map')
    with open(file_path, 'rb') as f:
        d = f.read()
    if _ntfs and ntfs_undo.detect(d) is not None:
        rn = _diagnose_ntfs_copy(file_path, d, progress, depth, extra_ids)
        if rn is not None:
            return rn
    r['fname'] = map_name(d)
    with quiet():
        hdr, decoys = mpqdoctor.scan_header(d, file_path)
    if hdr is None:
        inc = incomplete_file(d, file_path)
        if inc:
            r['fixable'] = 'incomplete'
            r['incomplete'] = inc
        else:
            r['fixable'] = 'not_a_map'
        return r
    r['mpq'] = hdr
    fake_list = [o for o, why in decoys if o < hdr and why.startswith('FAKE header')]
    if fake_list:
        prot('fake_header', n=len(fake_list))
    if d[:4] != b'HM3W':
        prot('missing_hm3w', first_pos='mpq_at_zero' if hdr == 0 else ('user_data' if d[:4] == b'MPQ\x1b' else 'other'))
    h = M._v1_fields(M.Header(), d, hdr, len(d))
    reasons = []
    if h.version != 0:
        reasons.append(('version_num', h.version))
    if h.header_size != 0x20:
        reasons.append(('bad_header_size', h.header_size))
    if h.block_n > 1 and (h.hash_pos <= 0x20 or h.hash_pos & 0x80000000):
        reasons.append(('hash_position', h.hash_pos))
    if h.block_n > 1 and (h.block_pos <= 0x20 or h.block_pos & 0x80000000):
        reasons.append(('block_position', h.block_pos))
    if h.block_shift & 0xFF00:
        reasons.append(('sector_bytes', h.block_shift))
    if reasons:
        prot('read_only', reasons=reasons, mark=HEADER_MARKS.get(h.header_size))
    if h.block_shift == 0:
        prot('sector512')
    if h.archive_size != len(d) - hdr:
        r['warnings'].append({'code': 'declared_size'})
    del d
    p('tables')
    try:
        a = _open(file_path)
    except BaseException as e:
        if isinstance(e, KeyboardInterrupt):
            raise
        r['err'] = str(e) or type(e).__name__
        r['fixable'] = 'cannot_read'
        return r
    virtual = mpqdoctor.virtual_tables(a)
    if virtual:
        prot('virtual_tables', hash_entries=a.h.hash_n)
    sp, marked, used_entries = (False, 0, 0) if virtual else mpqdoctor.is_sprotect(a)
    if sp:
        prot('sprotect', marked=marked, used_entries=used_entries)
    if not virtual:
        decoys = mpqdoctor.locale_decoys(a, list(mpqdoctor.PROBES) + list(mpqnames.BASE_NAMES) +
                                         ['scripts\\war3map.j', 'war3map.lua'])
        if decoys:
            prot('locale_decoy', n=len(decoys), name_list=[x[0] for x in decoys])
    j = _read(a, 'war3map.j')
    if j is None:
        j = _read(a, 'scripts\\war3map.j')
    lua = a.find('war3map.lua')
    r['w3i_language'] = language = language_from_w3i(_read(a, 'war3map.w3i'))
    if lua and (language == 1 or not j):
        r['script'] = 'lua'
    elif j and script_j2b(a, j):
        r['script'] = 'j2b'
        prot('script_j2b', byte_size=a.blocks[a.find(J2B_FILE)[1]][2])
    elif j is not None and len(j) < 450 and a.find('kkmap.jc'):
        from doctor.script import kkwe
        try:
            loader = kkwe.is_loader(kkwe.Bytecode(kkwe.read_container(_read(a, 'kkmap.jc'))))[0]
        except Exception:
            loader = False
        if loader:
            outside, _t = mpqdoctor.outside_tables(a, r['byte_size'])
            prot('kk_encrypted', outside=outside)
            r['script'] = 'kk_encrypted'
        else:
            r['script'] = 'kkwe'
            prot('script_kkwe', byte_size=a.blocks[a.find('kkmap.jc')[1]][2])
    elif j:
        r['script'] = 'jass'
    if not virtual and r['script'] != 'kk_encrypted':
        x = mpqdoctor.analyze_tables(a)
        if x['free_slots'] == 0 and x['deleted'] == 0 and a.hash_n_read:
            prot('full_hash_table', hash_entries=a.hash_n_read)
        if a.hash_n_read and r['script'] is None and not a.find('war3map.w3i') and not a.find('war3campaign.w3f'):
            probe = carver_probe(file_path)
            prot(
                'unreadable_tables',
                hash_entries=a.hash_n_read,
                free_slots=x['free_slots'],
                live=x['live'],
                carver=probe,
            )
        if x['alias']:
            prot('alias', block_list=x['alias'], maximum=x['alias_max'])
        fake_count = count_fake(a)
        if fake_count:
            prot('fake_entries', n=fake_count)
        if not sp:
            p('fake_files')
            with quiet():
                st, nb = mpqdoctor.classify_blocks(a, listfile_names(a))
            junk = sum(1 for e, _m in st.values() if e == 'junk')
            if junk:
                prot('fake_files', n=junk, real_blocks=sum(1 for e, _m in st.values() if e == 'real'),
                     uncertain_items=sum(1 for e, _m in st.values() if e == 'uncertain'))
            game = [b for b, (e, m) in st.items() if e == 'real' and (m.startswith(mpqdoctor.GAME_ONLY_READS) or
                    m == mpqread.VALID_SLACK and (mpqread.end_by_sector_table(a, b, nb[b]) or 0) > a.blocks[b][1])]
            if game:
                prot('game_only_reads', n=len(game))
        if a.find('war3map.j') and a.find('scripts\\war3map.j'):
            try:
                with quiet():
                    a.read('scripts\\war3map.j')
            except Exception:
                prot('script_decoy')
        r['listfile'] = _listfile_status(a)
    p('counts')
    for x in inflated_counts.analyze_map(a, editor_only=False):
        prot('inflated_counts', **x)
    try:
        _bd = _read(a, 'war3map.doo')
        if _bd:
            _valid = doodads.game_ids() | doodads.map_ids(a) | set(extra_ids)
            if _valid:
                _bad = doodads.invalid_ids(_bd, _valid)
                if _bad:
                    prot('invalid_doodad', ids=[{'id': k, 'n': v} for k, v in _bad],
                         n=sum(v for _k, v in _bad), examples=[k for k, _v in _bad[:5]])
    except Exception:
        pass
    if r['script'] != 'kk_encrypted':
        scrambled, sums = scrambled_ids(a, j)
        if scrambled and sums:
            prot('scrambled_ids', n=scrambled, sums=sums, fixable=r['script'] == 'jass')
    if r['script'] != 'kk_encrypted':
        try:
            with quiet():
                file_set = slk_patch.table_files(listfile_names(a), lambda n: _read(a, n))
                r['slk'] = slk_patch.is_slk_map(file_set)
                _changed, slk_report = slk_patch.patch(file_set)
        except Exception:
            slk_report = {}
        for problem in slk_patch.PROBLEMS:
            per_file = slk_report.get(problem)
            if per_file:
                prot(SLK_CODE[problem], n=sum(per_file.values()), file_set=sorted(per_file))
    ed = r['editor']
    b3i = _read(a, 'war3map.w3i')
    if b3i is None:
        ed['w3i'] = 'missing'
    else:
        try:
            with quiet():
                new, w3i_report, _tail = editor_prep.fix_w3i(b3i)
            ed['w3i'] = 'new' if w3i_report.startswith('new_version') else ('ok' if new == b3i else 'truncated')
        except Exception:
            ed['w3i'] = 'unreadable'
    ed['missing_items'] = [n for n in EDITOR_FILES if not a.find(n)]
    ed['imp'] = bool(a.find('war3map.imp'))
    if a.find('war3map.wtg') and a.find('war3map.wct'):
        try:
            reason = wtg_triggers.needs_regeneration(_read(a, 'war3map.wtg'))
        except Exception:
            reason = None
        if reason:
            ed['trigger_list'] = reason
    if not virtual and r['script'] in EDITOR_SCRIPTS:
        try:
            lf = _read(a, '(listfile)') or b''
            lf_names = [line.strip() for line in lf.decode('utf-8', 'surrogateescape').splitlines() if line.strip()]
            with quiet():
                identical = duplicate_textures.clusters(a, lf_names)
        except Exception:
            identical = []
        if identical:
            ed['duplicate_textures'] = identical
    if a.find('war3campaign.w3f') and not a.find('war3map.w3i'):
        r['kind'] = 'campaign_info'
        try:
            r['campaign_info'] = diagnose_campaign_maps(a, depth=depth)
        except Exception as e:
            r['campaign_info'] = {'err': _error(e), 'map_list': []}
    codes = [x['code'] for x in r['protections']]
    carvable = is_carvable(r)
    if 'kk_encrypted' in codes:
        r['fixable'] = 'impossible'
    elif 'unreadable_tables' in codes and not carvable:
        r['fixable'] = 'unreadable'
    elif codes:
        r['fixable'] = 'yes'
    else:
        r['fixable'] = 'nothing'
    if 'kk_encrypted' in codes:
        ed['status'] = 'impossible'
    elif 'unreadable_tables' in codes:
        ed['status'] = 'needs_work' if carvable else 'unreadable'
    elif r.get('kind') == 'campaign_info':
        c = r.get('campaign_info') or {}
        statuses = [m.get('editor') for m in c.get('map_list') or []]
        if set(codes) & set(EDITOR_BLOCKERS) or c.get('err') or any(e != 'ready' for e in statuses):
            ed['status'] = 'campaign_needs_work'
        else:
            ed['status'] = 'ready'
    elif r['script'] not in EDITOR_SCRIPTS:
        ed['status'] = 'script_' + (r['script'] or 'none')
    elif ed['w3i'] in ('unreadable', 'missing'):
        ed['status'] = 'w3i_' + ed['w3i']
    elif ed['w3i'] in ('ok', 'new') and not ed['missing_items'] and not set(codes) & set(EDITOR_BLOCKERS) and \
            not ed.get('duplicate_textures') and not ed.get('trigger_list'):
        ed['status'] = 'ready'
    else:
        ed['status'] = 'needs_work'
    return r


_PROBES = {}


def carver_probe(file_path):
    try:
        hash_key = (os.path.abspath(file_path), os.path.getsize(file_path), os.path.getmtime(file_path))
    except OSError:
        hash_key = None
    if hash_key in _PROBES:
        return _PROBES[hash_key]
    try:
        from doctor.mpq import carver
        with quiet():
            rc = carver.carve(file_path, None)
        out = {
            'members': rc.get('members'),
            'encrypted_count': rc.get('encrypted_count'),
            'file_set': rc.get('file_set'),
            'w3i': not rc.get('missing_w3i'),
            'script': not rc.get('missing_script'),
            'unnamed': (rc.get('name_list') or {}).get('unnamed', 0),
            'holes': len(rc.get('holes') or []),
            'err': rc.get('err'),
        }
    except Exception as e:
        out = {'members': 0, 'w3i': False, 'script': False, 'err': _error(e)}
    if hash_key:
        _PROBES[hash_key] = out
    return out


def is_carvable(diag):
    p = next((x for x in diag.get('protections') or [] if x['code'] == 'unreadable_tables'), None)
    c = (p or {}).get('carver') or {}
    return bool(c.get('w3i') and c.get('script'))


def diagnose_campaign_maps(a, depth=0):
    lf = _read(a, '(listfile)') or b''
    name_list = [line.strip() for line in lf.decode('utf-8', 'surrogateescape').splitlines() if line.strip()]
    w3f = _read(a, 'war3campaign.w3f') or b''
    name_list += sorted(mpqnames.mine_bytes(w3f))
    map_list = []
    seen = set()
    for n in name_list:
        if n.lower().endswith(('.w3x', '.w3m')) and n.upper() not in seen and a.find(n):
            seen.add(n.upper())
            map_list.append(n)
    out = {'map_list': []}
    if depth:
        return out
    campaign_ids = doodads.map_ids(a, ('war3campaign.w3d', 'war3campaign.w3b'))
    tmp = tempfile.mkdtemp(prefix='devos_campaign_')
    try:
        for i, n in enumerate(map_list):
            item = {'fname': n}
            b = _read(a, n)
            item['bytes'] = len(b) if b else 0
            if not b:
                item['editor'] = 'unreadable'
                out['map_list'].append(item)
                continue
            t = os.path.join(tmp, '%03d%s' % (i, os.path.splitext(n)[1].lower()))
            with open(t, 'wb') as f:
                f.write(b)
            try:
                d = diagnose(t, depth=depth + 1, extra_ids=campaign_ids)
                item.update(fixable=d.get('fixable'), editor=(d.get('editor') or {}).get('status'),
                            protections=sorted(set(x['code'] for x in d.get('protections') or [])))
            except Exception as e:
                item.update(editor='err', err=_error(e))
            os.remove(t)
            out['map_list'].append(item)
    finally:
        shutil.rmtree(tmp, ignore_errors=True)
    return out


def incomplete_file(d, fname=None):
    h, skipped = M.find_header(d, fname)
    if h is not None:
        return None
    for o, reason in skipped:
        if not reason.startswith('FAKE header'):
            continue
        c = M._v1_fields(M.Header(), d, o, len(d))
        end_pos = max(c.hash_abs + 16 * c.hash_n, c.block_abs + 16 * c.block_n)
        if end_pos <= len(d):
            continue
        return {'offset': o, 'end_of_tables': end_pos, 'declared_size': o + c.archive_size, 'byte_size': len(d),
                'missing_items': end_pos - len(d)}
    return None


def language_from_w3i(b):
    if not b:
        return None
    try:
        from doctor.data import w3i
        m = w3i.parse(b)
    except Exception:
        return None
    return m.get('script_language')


J2B_FILE = 'war3map.bin'
RX_J2B = re.compile(rb'"war3map\.bin"')


def script_j2b(a, j):
    if not RX_J2B.search(j):
        return False
    r = a.find(J2B_FILE)
    if not r:
        return False
    try:
        v, begin_pos = a.validate_light(r[1], J2B_FILE)
    except Exception:
        return False
    return v == 'ok' and begin_pos[:4] == b'2SAJ'


def scrambled_ids(a, j):
    try:
        with quiet():
            files_ = object_ids.load_data(a)
    except Exception:
        return 0, 0
    outside = set()
    for _e, (_v, objs, _n, _d, _p) in files_.items():
        for o in objs:
            idb = o[2].encode('latin-1')
            if o[0] == 1 and object_ids.is_scrambled(idb):
                outside.add(object_ids.id_value(idb))
    if not outside or not j:
        return len(outside), 0
    sums = 0
    for m in object_ids.RX_SCRIPT.finditer(j):
        if m.group('sum_expr'):
            v = (object_ids.rawcode_value(object_ids.unescape(m.group('a'))) +
                 object_ids.rawcode_value(object_ids.unescape(m.group('b')))) & 0xFFFFFFFF
            if v in outside:
                sums += 1
    return len(outside), sums


def map_names(a):
    with quiet():
        closure = mpqnames.referenced_closure(a)
    canon = dict((n.upper(), n) for n in tuple(mpqnames.BASE_NAMES) + EDITOR_FILES)
    name_list = {}
    for n in sorted(closure):
        name_list.setdefault(n.upper(), canon.get(n.upper(), n))
    lf = _read(a, '(listfile)')
    if lf:
        for line in lf.decode('utf-8', 'surrogateescape').splitlines():
            n = line.strip().replace('/', '\\')
            if not n or n.upper() in name_list:
                continue
            try:
                with quiet():
                    if _valid_for_game(a, n) is not None:
                        name_list[n.upper()] = n
            except Exception:
                pass
    try:
        with quiet():
            derived = mpqnames.derived_names(a, sorted(name_list.values()))
    except Exception:
        derived = {}
    for n in sorted(derived):
        name_list.setdefault(n.upper(), n)
    return sorted((n.replace('/', '\\') for n in name_list.values() if n.lower() not in SPECIAL_FILES),
                  key=lambda n: (n.lower(), n))


def game_only_reads(a, name_list):
    out = []
    for n in name_list:
        f = a.find(n)
        if not f or f[1] >= len(a.blocks):
            continue
        cs, fs = a.blocks[f[1]][1:3]
        v, m = a.validate(f[1], n)
        if v == 'ok':
            end_pos = mpqread.end_by_sector_table(a, f[1], n) if m == mpqread.VALID_SLACK else None
            if not end_pos or end_pos <= cs:
                continue
        elif v != 'invalid':
            continue
        data_bytes = _read(a, n)
        if data_bytes is not None and len(data_bytes) == fs and mpqnames.content_matches(n, data_bytes):
            out.append((n, data_bytes))
    return out


def _listfile_and_fake(file_path, name_list):
    a = _open(file_path)
    current_names = {}
    lf = _read(a, '(listfile)')
    if lf:
        for line in lf.decode('utf-8', 'surrogateescape').splitlines():
            n = line.strip().replace('/', '\\')
            if n and a.find(n):
                current_names.setdefault(n.upper(), n)
    all_items = dict(current_names)
    for n in name_list:
        if a.find(n):
            all_items.setdefault(n.upper(), n)
    for k in [k for k, n in all_items.items() if n.lower() in SPECIAL_FILES]:
        del all_items[k]
    fake_count = count_fake(a)
    repl = []
    if set(all_items) - set(current_names):
        listing = sorted(all_items.values(), key=lambda n: (n.lower(), n))
        repl.append(('(listfile)', ('\r\n'.join(listing) + '\r\n').encode('utf-8', 'surrogateescape')))
    rewritten = game_only_reads(a, sorted(all_items.values(), key=lambda n: (n.lower(), n)))
    repl += rewritten
    to_delete = ['(attributes)'] if (repl or fake_count) and a.find('(attributes)') else []
    full = bool(a.hash_n_read) and not any(a.ht[4 * i + 3] in (FREE, DELETED) for i in range(a.hash_n_read))
    no_slot = []
    if repl or fake_count or to_delete or full:
        with quiet():
            mpqadd.add_files(file_path, repl, to_delete=to_delete, fake_count=True, log=_nothing, no_slot=no_slot,
                             grow=sorted(all_items.values(), key=lambda n: (n.lower(), n)), slack=1 if full else 0)
    return {
        'listfile': len(all_items) if any(n == '(listfile)' for n, _d in repl) and '(listfile)' not in no_slot else 0,
        'fake_count': fake_count,
        'attributes': bool(to_delete),
        'no_slot': no_slot,
        'rewritten': [n for n, _d in rewritten if n not in no_slot],
    }


def check_content(original, output, exclude=()):
    a = _open(original)
    b = _open(output)
    lf = _read(b, '(listfile)') or b''
    name_list = [line.strip() for line in lf.decode('utf-8', 'surrogateescape').splitlines() if line.strip()]
    name_list += list(mpqdoctor.PROBES) + list(mpqnames.BASE_NAMES)

    def _key(n):
        return n.replace('/', '\\').lower()

    outside = set(_key(x) for x in exclude) | set(SPECIAL_FILES)
    out = {'identical': 0, 'different': [], 'missing_items': [], 'empty_files': [], 'unreadable_items': 0}
    with quiet():
        for n in dict.fromkeys(name_list):
            if _key(n) in outside:
                continue
            try:
                r = a.find_locale(n) if a.find(n) else None
                x = a.read(n, bi=r[1]) if r else None
            except Exception:
                out['unreadable_items'] += 1
                continue
            if x is None:
                continue
            try:
                y = b.read(n) if b.find(n) else None
            except Exception:
                y = None
            if y is None:
                (out['empty_files'] if not x else out['missing_items']).append(n)
            elif x != y:
                out['different'].append(n)
            else:
                out['identical'] += 1
    return out


def _map_tables(file_path):
    a = _open(file_path)
    name_list = listfile_names(a)
    return name_list, slk_patch.table_files(name_list, lambda n: _read(a, n)), _read(a, '(listfile)')


def data_fixes(entry, output, only_problems=None):
    name_list, file_set, lf = _map_tables(entry)
    modified, report = slk_patch.patch(file_set, only_problems)
    out = {'report': report, 'modified': sorted(modified), 'new_ones': sorted(n for n in modified if n not in file_set)}
    if not modified:
        return out
    repl = sorted(modified.items())
    if out['new_ones'] and lf is not None:
        body_text = lf.decode('utf-8', 'surrogateescape')
        line_list = [x for x in body_text.replace('\r\n', '\n').split('\n') if x.strip()]
        existing = set(x.strip().lower() for x in line_list)
        line_list += [n for n in out['new_ones'] if n.lower() not in existing]
        end_pos = '\r\n' if '\r\n' in body_text or not body_text else '\n'
        repl.append(('(listfile)', (end_pos.join(line_list) + end_pos).encode('utf-8', 'surrogateescape')))
    shutil.copyfile(entry, output)
    no_slot = []
    with quiet():
        mpqadd.add_files(output, repl, log=_nothing, no_slot=no_slot, grow=name_list + out['new_ones'])
    if no_slot:
        raise RuntimeError('data fixes: no table entry for %s' % ', '.join(no_slot))
    b = _open(output)
    for n, data_bytes in modified.items():
        if _read(b, n) != data_bytes:
            raise RuntimeError('data fixes: %s did not read back the same' % n)
    return out


def _error(e):
    return '%s: %s' % (type(e).__name__, e) if str(e) else type(e).__name__


def _part(output):
    base, ext = os.path.splitext(output)
    return base + '.part' + (ext or '.w3x')


def unprotect(file_path, output, progress=None, diag=None, options=None):
    p = progress or _nothing
    diag = diag or diagnose(file_path, p)
    res = {
        'status': None,
        'output': None,
        'before': diag,
        'steps': {},
        'after_diag': None,
        'content': None,
        'err': None,
    }
    if diag['fixable'] != 'yes':
        res['status'] = {'nothing': 'nothing_to_do'}.get(diag['fixable'], diag['fixable'])
        return res
    codes = set(x['code'] for x in diag['protections'])
    res['for_button3'] = sorted(codes & set(BUTTON3_ONLY))
    if 'ntfs_copy' in codes:
        return _unprotect_ntfs_copy(file_path, output, p, diag, res)
    if not codes - set(BUTTON3_ONLY):
        res['status'] = 'nothing_to_do'
        return res
    if 'unreadable_tables' in codes:
        return _unprotect_by_carving(file_path, output, p, diag, res)
    remove_mpq = bool(codes - set(BUTTON3_ONLY) - set(DATA_ONLY)) and step_on(options, 'mpq')
    data_only = [x for x in slk_patch.PROBLEMS if SLK_CODE[x] in codes and step_on(options, 'dados:' + x)]
    prot_ids = next((x for x in diag['protections'] if x['code'] == 'scrambled_ids'), None)
    do_ids = bool(prot_ids and prot_ids.get('fixable')) and step_on(options, 'ids')
    if not (remove_mpq or data_only or do_ids):
        res['status'] = 'nothing_selected'
        return res
    tmp = tempfile.mkdtemp(prefix='devos_map_doctor_')
    try:
        src = file_path
        if 'sector512' in codes and remove_mpq:
            p('sector_bytes')
            t = os.path.join(tmp, '0_sector.w3x')
            a = _open(src)
            sector_names = map_names(a)
            del a
            reg = _Record()
            try:
                with quiet(reg):
                    rs = mpq_rebuild.rebuild(src, t, sector_names, sector_shift=3, level=6, log=_nothing)
            except SystemExit as e:
                raise RuntimeError('mpq_rebuild: %s' % e)
            if (rs or {}).get('error_list') or not os.path.isfile(t):
                raise RuntimeError('mpq_rebuild: %s' % ((rs or {}).get('error_list') or reg.body_text().strip()[-200:]))
            src = t
            res['steps']['sector_bytes'] = True
        if 'sprotect' in codes and remove_mpq:
            p('sprotect')
            t = os.path.join(tmp, '1_sprotect.w3x')
            reg = _Record()
            try:
                with quiet(reg):
                    sprotect_fix.CRYPT = sprotect_fix.init_crypt()
                    sprotect_fix.fix(src, t)
            except SystemExit as e:
                raise RuntimeError('sprotect_fix: %s' % e)
            src = t
            res['steps']['sprotect'] = True
        modified = []
        if remove_mpq or do_ids:
            a = _open(src)
            virtual = mpqdoctor.virtual_tables(a)
            name_list = []
            if not virtual:
                p('name_list')
                name_list = map_names(a)
            del a
        if remove_mpq:
            p('repair')
            t = os.path.join(tmp, '2_fix.w3x')
            details = {}
            reg = _Record()
            fake_list = step_on(options, 'fake_list')
            with quiet(reg):
                out = mpqdoctor.fix(
                    src,
                    t,
                    name_list=name_list,
                    clean_alias=True,
                    prefix_hm3w=True,
                    hide_junk=fake_list,
                    hide_copies=fake_list,
                    report=details,
                )
            if out is None or not os.path.isfile(t):
                raise RuntimeError('mpqdoctor.fix: %s' % reg.body_text().strip().splitlines()[-1:])
            res['steps']['repair'] = details
            src = t
            if not virtual and step_on(options, 'listing'):
                p('listing')
                res['steps']['listing'] = _listfile_and_fake(src, name_list)
        if do_ids:
            p('ids')
            t = os.path.join(tmp, '3_ids.w3x')
            reg = _Record()
            try:
                with quiet(reg):
                    rc = object_ids.main(['object_ids.py', src, t])
            except SystemExit as e:
                raise RuntimeError('object_ids: %s' % e)
            if rc or not os.path.isfile(t):
                raise RuntimeError('object_ids: %s' % reg.body_text().strip().splitlines()[-1:])
            res['steps']['ids'] = prot_ids['n']
            modified = list(OBJECT_IDS_FILES)
            src = t
        if data_only:
            p('data_bytes')
            t = os.path.join(tmp, '4_data.w3x')
            res['steps']['data_bytes'] = data_fixes(src, t, None if len(data_only) == len(slk_patch.PROBLEMS)
                                                         else data_only)
            if res['steps']['data_bytes']['modified']:
                modified += res['steps']['data_bytes']['modified']
                src = t
        p('save')
        part = _part(output)
        res['output'] = part
        shutil.copyfile(src, part)
        p('verify')
        res['after_diag'] = diagnose(part)
        res['content'] = c = check_content(file_path, part, exclude=modified)
        if c['different'] or c['missing_items']:
            raise RuntimeError('check: %d different file(s), %d missing'
                               % (len(c['different']), len(c['missing_items'])))
        os.replace(part, output)
        res['output'] = res['after_diag']['file_name'] = os.path.abspath(output)
        deixados = deixados_de_proposito(codes, options)
        res['deixados'] = sorted(set(x['code'] for x in res['after_diag']['protections']) & deixados)
        res['status'] = 'partial' if [x for x in res['after_diag']['protections'] if x['code'] not in BUTTON3_ONLY and
                                      x['code'] not in deixados] else 'done'
    except (Exception, SystemExit) as e:
        res['status'] = 'failed'
        res['err'] = _error(e)
        if res['output'] and os.path.isfile(res['output']):
            os.remove(res['output'])
        res['output'] = None
    finally:
        shutil.rmtree(tmp, ignore_errors=True)
    return res


def _unprotect_ntfs_copy(file_path, output, p, diag, res):
    p('ntfs')
    t, details = restore_copy(file_path)
    if t is None:
        res['status'] = 'failed'
        res['err'] = 'ntfs_desfaz: %s' % details.get('err')
        return res
    res['steps']['ntfs'] = dict((k, v) for k, v in details.items() if k in ('lznt1', 'lost', 'grown', 'tables'))
    r2 = unprotect(t, output, p, diagnose(t, _ntfs=False))
    if r2['status'] == 'nothing_to_do':
        try:
            p('save')
            part = _part(output)
            res['output'] = part
            shutil.copyfile(t, part)
            p('verify')
            res['after_diag'] = diagnose(part, _ntfs=False)
            os.replace(part, output)
            res['output'] = res['after_diag']['file_name'] = os.path.abspath(output)
            res['status'] = (
                'partial' if [x for x in res['after_diag']['protections'] if x['code'] not in BUTTON3_ONLY] else 'done'
            )
        except (Exception, SystemExit) as e:
            res['status'] = 'failed'
            res['err'] = _error(e)
            if res['output'] and os.path.isfile(res['output']):
                os.remove(res['output'])
            res['output'] = None
        return res
    for k in ('status', 'output', 'after_diag', 'content', 'err'):
        res[k] = r2.get(k)
    res['steps'].update(r2.get('steps') or {})
    return res


def _unprotect_by_carving(file_path, output, p, diag, res):
    from doctor.mpq import carver
    tmp = tempfile.mkdtemp(prefix='devos_map_doctor_')
    try:
        p('carver')
        t = os.path.join(tmp, '0_carved' + (os.path.splitext(output)[1] or '.w3x'))
        with quiet():
            rc = carver.carve(file_path, t)
        if rc.get('err') or rc.get('write_errors') or not os.path.isfile(t):
            raise RuntimeError('carver: %s' % (rc.get('err') or rc.get('write_errors')))
        if rc.get('missing_w3i') or rc.get('missing_script'):
            raise RuntimeError('carver: the %s was not found by content'
                               % ('war3map.w3i' if rc.get('missing_w3i') else 'script'))
        res['steps']['carver'] = dict(
            (k, rc.get(k))
            for k in (
                'members',
                'encrypted_count',
                'uncompressed',
                'name_list',
                'file_set',
                'holes',
                'unreadable_items',
                'default_value',
            )
        )
        p('save')
        part = _part(output)
        res['output'] = part
        shutil.copyfile(t, part)
        p('verify')
        res['after_diag'] = diagnose(part)
        res['content'] = {'identical': rc['file_set'], 'different': [], 'missing_items': [], 'empty_files': [],
                          'unreadable_items': rc.get('unreadable_items', 0), 'carved': True}
        os.replace(part, output)
        res['output'] = res['after_diag']['file_name'] = os.path.abspath(output)
        leftover = (rc.get('name_list') or {}).get('unnamed') or rc.get('holes') or rc.get('unreadable_items') or \
            [x for x in res['after_diag']['protections'] if x['code'] not in BUTTON3_ONLY]
        res['status'] = 'partial' if leftover else 'done'
    except (Exception, SystemExit) as e:
        res['status'] = 'failed'
        res['err'] = _error(e)
        if res['output'] and os.path.isfile(res['output']):
            os.remove(res['output'])
        res['output'] = None
    finally:
        shutil.rmtree(tmp, ignore_errors=True)
    return res


def prepare_for_editor(file_path, output, progress=None, diag=None, safe_units=True, unprotection=None, extra_ids=(),
                       options=None):
    p = progress or _nothing
    diag = diag or diagnose(file_path, p, extra_ids=extra_ids)
    if options is not None and 'safe_units' in options:
        safe_units = step_on(options, 'safe_units')
    res = {'status': None, 'output': None, 'before': diag, 'unprotection': None, 'editor': None, 'after_diag': None,
           'err': None}
    if diag['fixable'] in ('not_a_map', 'cannot_read', 'impossible', 'unreadable', 'incomplete'):
        res['status'] = diag['fixable']
        return res
    status = diag['editor'].get('status')
    if status == 'campaign_needs_work':
        return _prepare_campaign_for_editor(file_path, output, p, diag, res, safe_units, unprotection)
    data_bytes = set(SLK_CODE[x] for x in slk_patch.PROBLEMS if step_on(options, 'dados:' + x)) & \
        set(x['code'] for x in diag['protections'])
    if status != 'needs_work' and not (status == 'ready' and data_bytes):
        res['status'] = 'nothing_to_do' if status == 'ready' else status
        return res
    tmp = tempfile.mkdtemp(prefix='devos_map_doctor_')
    try:
        src = file_path
        name_list = None
        if set(x['code'] for x in diag['protections']):
            if unprotection is not None:
                r1 = unprotection
                t = r1.get('output')
                if r1.get('status') in ('done', 'partial') and not (t and os.path.isfile(t)):
                    raise RuntimeError('unprotect: the output %r of button 2 no longer exists' % t)
            else:
                t = os.path.join(tmp, '1_unprotected.w3x')
                r1 = unprotect(file_path, t, p, diag, options)
            res['unprotection'] = r1
            if r1['status'] in ('done', 'partial'):
                src = t
            elif r1['status'] not in ('nothing_to_do', 'nothing_selected'):
                raise RuntimeError('unprotect: %s' % (r1['err'] or r1['status']))
            if src != file_path:
                b = _open(src)
                lf = _read(b, '(listfile)') or b''
                name_list = [
                    line.strip() for line in lf.decode('utf-8', 'surrogateescape').splitlines() if line.strip()
                ] or None
                del b
        if diag.get('script') in editor_prep.COMPILED_SCRIPT:
            p('script')
            t = os.path.join(tmp, '2_script.w3x')
            with quiet():
                res['script'] = editor_prep.script_restore(src, t, diag['script'], log=_nothing)
            src = t
            name_list = None
        if name_list is None:
            p('name_list')
            name_list = map_names(_open(src))
        p('editor')
        part = _part(output)
        res['output'] = part
        with quiet():
            details, _assembled = editor_prep.prepare(src, part, name_list, log=_nothing, safe_units=safe_units,
                                                   extra_ids=extra_ids, options=options)
        if res.get('script'):
            details['script_restore'] = res['script']
        res['editor'] = details
        if details['failures']:
            raise RuntimeError('editor_prep: %s' % '; '.join(details['failures']))
        p('verify')
        res['after_diag'] = after_diag = diagnose(part, extra_ids=extra_ids)
        os.replace(part, output)
        res['output'] = after_diag['file_name'] = os.path.abspath(output)
        res['status'] = 'done' if after_diag['editor'].get('status') == 'ready' else 'partial'
    except (Exception, SystemExit) as e:
        res['status'] = 'script_cut_off' if isinstance(e, editor_prep.ScriptCutOff) else \
            'script_not_restored' if isinstance(e, editor_prep.ScriptNotRestored) else 'failed'
        res['err'] = str(e) if isinstance(e, editor_prep.ScriptNotRestored) else _error(e)
        if res['output'] and os.path.isfile(res['output']):
            os.remove(res['output'])
        res['output'] = None
    finally:
        shutil.rmtree(tmp, ignore_errors=True)
    return res


def _prepare_campaign_for_editor(file_path, output, p, diag, res, safe_units, unprotection):
    tmp = tempfile.mkdtemp(prefix='devos_map_doctor_')
    try:
        src = file_path
        if [x for x in diag['protections'] if x['code'] not in BUTTON3_ONLY]:
            r1 = unprotection
            if r1 is None:
                r1 = unprotect(file_path, os.path.join(tmp, '1_unprotected.w3n'), p, diag)
            res['unprotection'] = r1
            if r1['status'] in ('done', 'partial'):
                src = r1['output']
            elif r1['status'] != 'nothing_to_do':
                raise RuntimeError('unprotect: %s' % (r1['err'] or r1['status']))
        a = _open(src)
        campaign_ids = doodads.map_ids(a, ('war3campaign.w3d', 'war3campaign.w3b'))
        replacements = []
        map_list = []
        for i, m in enumerate((diag.get('campaign_info') or {}).get('map_list') or []):
            if m.get('editor') == 'ready':
                continue
            p('editor')
            ext = os.path.splitext(m['fname'])[1].lower()
            ent = os.path.join(tmp, 'map%03d%s' % (i, ext))
            out_path = os.path.join(tmp, 'map%03d_editor%s' % (i, ext))
            b = _read(a, m['fname'])
            if not b:
                map_list.append({'fname': m['fname'], 'status': 'unreadable'})
                continue
            with open(ent, 'wb') as f:
                f.write(b)
            r = prepare_for_editor(ent, out_path, safe_units=safe_units, extra_ids=campaign_ids)
            map_list.append({'fname': m['fname'], 'status': r['status'], 'err': r.get('err')})
            if r['status'] in ('done', 'partial') and os.path.isfile(out_path):
                with open(out_path, 'rb') as f:
                    replacements.append((m['fname'], f.read()))
        campaign_names = map_names(a)
        del a
        res['editor'] = {'map_list': map_list, 'failures': [], 'new_ones': [], 'campaign_info': True}
        if not replacements:
            raise RuntimeError('no campaign map could be prepared: %s'
                               % ', '.join('%s (%s)' % (x['fname'], x['status']) for x in map_list))
        part = _part(output)
        res['output'] = part
        shutil.copyfile(src, part)
        with quiet():
            mpqadd.add_files(part, replacements, log=_nothing, no_slot=[], fake_count=True, grow=campaign_names)
        p('verify')
        res['after_diag'] = after_diag = diagnose(part)
        b2 = _open(part)
        for fname, data_bytes in replacements:
            if _read(b2, fname) != data_bytes:
                res['content'] = {'different': [fname], 'missing_items': []}
                raise RuntimeError('check: %s read back differently in the campaign' % fname)
        del b2
        os.replace(part, output)
        res['output'] = after_diag['file_name'] = os.path.abspath(output)
        res['status'] = 'done' if after_diag['editor'].get('status') == 'ready' else 'partial'
    except (Exception, SystemExit) as e:
        res['status'] = 'failed'
        res['err'] = _error(e)
        if res['output'] and os.path.isfile(res['output']):
            os.remove(res['output'])
        res['output'] = None
    finally:
        shutil.rmtree(tmp, ignore_errors=True)
    return res


def free_output(file_path, suffix):
    base, ext = os.path.splitext(file_path)
    ext = ext if ext.lower() in ('.w3x', '.w3m', '.w3n') else '.w3x'
    cand = base + suffix + ext
    k = 2
    while os.path.exists(cand):
        cand = '%s%s (%d)%s' % (base, suffix, k, ext)
        k += 1
    return cand
