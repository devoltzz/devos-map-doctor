# Fixes the SLK tables of a ported map for Warcraft III 3.0.
import contextlib
import io
import os
import shutil
import sys
import traceback

from doctor.port import morph_chaos
from doctor.port import name_without_dot
from doctor.data import slk_normalize


KEY_NAMES = ('slk', 'fake_b', 'models', 'chaos')


def run_action(module, args):
    out, err = io.StringIO(), io.StringIO()
    argv = sys.argv
    sys.argv = [module.__name__ + '.py'] + list(args)
    rc = 0
    try:
        with contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
            try:
                v = module.main()
                rc = v if isinstance(v, int) else 0
            except SystemExit as e:
                rc = e.code if isinstance(e.code, int) else (0 if e.code is None else 1)
                if not isinstance(e.code, int) and e.code is not None:
                    err.write('%s\n' % e.code)
            except Exception:
                rc = 1
                err.write(traceback.format_exc())
    finally:
        sys.argv = argv
    return rc, out.getvalue() + err.getvalue()


def translate_txt(extract, tr_dir):
    if not tr_dir or not os.path.isfile(os.path.join(tr_dir, 'strings.json')):
        return {}, {}
    os.environ['TR_DIR'] = tr_dir
    from doctor.translation import tr_apply as ta
    if os.path.normcase(os.path.abspath(ta.TR)) != os.path.normcase(os.path.abspath(tr_dir)):
        raise SystemExit('tr_apply imported with another TR_DIR (%s)' % ta.TR)
    import json
    entries = json.load(open(os.path.join(tr_dir, 'strings.json'), encoding='utf-8'))
    tr = ta.load_translations()
    os.makedirs(ta.BUILD, exist_ok=True)
    stats = {}
    ta.apply_txt(extract, entries, tr, stats)
    ta.apply_misc(extract, entries, tr, stats)
    out = {}
    for details in ta.tx.STRING_FILES:
        p = os.path.join(ta.BUILD, *details.split('/'))
        if os.path.isfile(p):
            out[os.path.basename(p).lower()] = open(p, 'rb').read()
    return out, stats


def swap_no_dot(units, listing):
    by = {}
    for f in sorted(os.listdir(units)):
        if not f.lower().endswith(('.slk', '.txt')):
            continue
        p = os.path.join(units, f)
        new, tally = name_without_dot.swap(open(p, 'rb').read().decode('utf-8', 'surrogateescape'), listing,
                                           sep=chr(92))
        n = sum(tally.values())
        if n:
            open(p, 'wb').write(new.encode('utf-8', 'surrogateescape'))
            by[f] = n
    return sum(by.values()), by


def applies(extract, data_bytes, raw_data, segment, tr_dir=None, expected_count=None, no_dot=None, tolerant_mode=False):
    exp_len = dict((k, None) for k in KEY_NAMES)
    exp_len.update(expected_count or {})
    failures = []
    info = {}
    units = os.path.join(data_bytes, 'Units')
    if os.path.isdir(data_bytes):
        shutil.rmtree(data_bytes)
    os.makedirs(units)
    origin = os.path.join(extract, 'Units')
    translated, info['translation'] = translate_txt(extract, tr_dir)
    for f in sorted(os.listdir(origin)):
        p = os.path.join(origin, f)
        if os.path.getsize(p) and f.lower().endswith(('.slk', '.txt')):
            if f.lower() in translated:
                open(os.path.join(units, f), 'wb').write(translated[f.lower()])
            else:
                shutil.copyfile(p, os.path.join(units, f))
    n_slk = n_b = 0
    for f in sorted(os.listdir(units)):
        if not f.lower().endswith('.slk'):
            continue
        p = os.path.join(units, f)
        new, i = slk_normalize.normalize(open(p, 'rb').read())
        open(p, 'wb').write(new)
        n_slk += 1
        n_b += len(i['b_before']) - 1
    info['slk'], info['fake_b'] = n_slk, n_b
    from doctor.data import slk2skin
    rc, out = run_action(slk2skin, [units])
    if rc:
        failures.append('slk2skin: code %d: %s' % (rc, out[-300:]))
    models = {}
    for line in out.splitlines():
        p = line.split()
        if len(p) >= 4 and p[1] == '->' and p[3].isdigit():
            models[p[2]] = int(p[3])
    info['models'] = models
    fix = []
    for f in sorted(os.listdir(units)):
        if f.lower().endswith('.slk'):
            p = os.path.join(units, f)
            from doctor.data import slk_fix
            rc, out = run_action(slk_fix, [p, p])
            if rc:
                failures.append('slk_fix %s: %s' % (f, out[-200:]))
            fix.append((f, out.strip().splitlines()[-1] if out.strip() else ''))
    info['slk_fix'] = fix
    has_abil = os.path.isfile(os.path.join(units, 'AbilityData.slk'))
    info['warnings'] = []
    if has_abil:
        from doctor.data import slk_levels
        rc, out = run_action(slk_levels, [os.path.join(units, 'AbilityData.slk')])
        if rc:
            failures.append('slk_levels: %s' % out[-300:])
        info['slk_levels'] = out.strip().splitlines()[-3:]
    else:
        info['slk_levels'] = []
        info['warnings'].append(
            'the map has no Units\\AbilityData.slk: without levels 5 and 6 and without the Chaos abilities'
        )
    from doctor.data import buttonpos_fix
    rc, out = run_action(buttonpos_fix, [units, '--no-learn'])
    if rc:
        failures.append('buttonpos_fix: %s' % out[-300:])
    info['buttonpos'] = out.strip().splitlines()[-4:]
    body_text = open(raw_data, 'rb').read().decode('latin-1')
    targets, _sites, target_sites = morph_chaos.targets(body_text)
    if tolerant_mode:
        info['warnings'] += ['morph_chaos: ' + f for f in target_sites]
    else:
        failures += ['morph_chaos: ' + f for f in target_sites]
    slk = os.path.join(units, 'AbilityData.slk')
    strings = os.path.join(units, 'campaignabilitystrings.txt')
    if has_abil and targets:
        pairs = list(zip(morph_chaos.aliases(len(targets), morph_chaos.slk_ids(slk)), targets))
        if not os.path.isfile(strings):
            open(strings, 'wb').close()
        n_l, n_strings = morph_chaos.add_levels(slk, strings, pairs)
    else:
        pairs, n_l, n_strings = [], 0, 0
    open(segment, 'w', encoding='utf-8', newline='\n').write(morph_chaos.segment(pairs))
    info['chaos'] = len(pairs)
    info['chaos_lines'], info['chaos_sections'] = n_l, n_strings
    info['pairs'] = pairs
    info['medidas'] = dict((k, info[k]) for k in KEY_NAMES)
    for k in KEY_NAMES:
        if exp_len[k] is not None and exp_len[k] != info[k]:
            failures.append('%s: measured %s, expected %s' % (k, info[k], exp_len[k]))
    if no_dot:
        info['no_dot'], info['no_dot_by'] = swap_no_dot(units, no_dot)
        info['without_common_point'] = True
        info['medidas']['no_dot'] = info['no_dot']
        if exp_len.get('no_dot') is not None and exp_len['no_dot'] != info['no_dot']:
            failures.append('no_dot: measured %d %s, expected %s' % (info['no_dot'], info['no_dot_by'],
                                                                     exp_len['no_dot']))
    return failures, info


def report_data(info):
    if info.get('translation'):
        print('translation of the TXTs (port/tools/tr): %s' % {k: v for k, v in info['translation'].items()})
    print('data (port/out/kk/dados): %d SLK normalized (%d fake B records removed); models -> %s; Chaos: %d '
          'targets (%d rows in AbilityData.slk, %d sections in campaignabilitystrings.txt) -> port/kk/compat/'
          'kk_morph_chaos.j' % (info['slk'], info['fake_b'], info['models'], info['chaos'], info['chaos_lines'],
                                info['chaos_sections']))
    for k in ('slk_levels', 'buttonpos'):
        print('   %s: %s' % (k, ' | '.join(info[k])))
    print('   slk_fix: %s' % '; '.join('%s: %s' % x for x in info['slk_fix'] if x[1]))
    if info.get('without_common_point'):
        print('   model names with several dots -> the alias without a dot (port/tools/sem_ponto.py): %d %s'
              % (info['no_dot'], info['no_dot_by']))
