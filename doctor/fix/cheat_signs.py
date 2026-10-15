# Signs of code grafted onto the editor skeleton of a JASS script (never a verdict).
import re

from doctor.script import jass_ast


SIGNATURES = ('hke_', 'efl_', '_feiba', 'WCDTOF', 'ou99_', '55you')
SKELETON = frozenset((
    'InitGlobals', 'InitCustomTriggers', 'RunInitializationTriggers', 'InitBlizzard', 'InitSounds', 'CreateRegions',
    'CreateCameras', 'InitUpgrades', 'InitTechTree', 'CreateAllDestructables', 'CreateAllItems', 'CreateAllUnits',
    'CreateNeutralHostile', 'CreateNeutralPassive', 'CreateNeutralVictim', 'CreateNeutralExtra',
    'CreatePlayerBuildings', 'CreatePlayerUnits', 'InitCustomPlayerSlots', 'InitCustomTeams', 'InitAllyPriorities',
    'InitCreeps', 'InitDestructables', 'InitItems', 'InitUnits', 'main', 'config'))
RX_SKELETON = re.compile(
    r'(?:Create(?:Buildings|Units)ForPlayer\d+|InitTrig_\w+|CreateNeutral\w*|Init\w*(?:Sounds?|Upgrades'
    r'|Tech\w*)|Create\w*(?:Regions|Cameras)\w*|gg_\w+)\Z'
)
LIST_MAX = 40


def _is_skeleton(name):
    return name in SKELETON or bool(RX_SKELETON.match(name))


def _lis_outside(seq):
    import bisect
    tails, tails_idx, prev = [], [], [-1] * len(seq)
    for i, v in enumerate(seq):
        k = bisect.bisect_left(tails, v)
        if k == len(tails):
            tails.append(v)
            tails_idx.append(i)
        else:
            tails[k] = v
            tails_idx[k] = i
        prev[i] = tails_idx[k - 1] if k else -1
    keep, i = set(), tails_idx[-1] if tails_idx else -1
    while i >= 0:
        keep.add(i)
        i = prev[i]
    return [i for i in range(len(seq)) if i not in keep]


def signs(text_or_tree, text=None):
    if isinstance(text_or_tree, jass_ast.Script):
        tree = text_or_tree
    else:
        text = text_or_tree
        try:
            tree = jass_ast.parse(text)
        except jass_ast.JassSyntaxError as e:
            return {'language': 'jass', 'error': 'The script does not parse (%s).' % e}
    funcs = dict((f.name, f) for f in tree.functions)
    out = {'language': 'jass', 'applicable': False,
           'init_trig': {'defined': 0, 'called': 0, 'not_called': [], 'not_defined': [], 'out_of_order': []},
           'outside': [], 'signatures': []}
    main = funcs.get('main')
    out['vjass'] = any('__' in n for n in funcs)
    skeleton_like = not out['vjass'] and main is not None and (
        'InitGlobals' in funcs or 'InitCustomTriggers' in funcs) and any(
        c.name in ('InitGlobals', 'InitCustomTriggers', 'InitBlizzard') for c in jass_ast.walk(main)
        if type(c) is jass_ast.Call)
    if skeleton_like:
        out['applicable'] = True
        defined = [f.name[9:] for f in tree.functions if f.name.startswith('InitTrig_')]
        called = []
        for f in tree.functions:
            for c in jass_ast.walk(f):
                if type(c) is jass_ast.Call and c.name.startswith('InitTrig_'):
                    called.append(c.name[9:])
                elif type(c) is jass_ast.FuncRef and c.name.startswith('InitTrig_'):
                    called.append(c.name[9:])
                elif type(c) is jass_ast.Literal and c.kind == 'string' and c.text.startswith('"InitTrig_'):
                    called.append(c.text[10:-1])
        it = out['init_trig']
        it['defined'], it['called'] = len(defined), len(called)
        dset, cset = set(defined), set(called)
        not_called = [n for n in defined if n not in cset]
        not_defined = [n for n in dict.fromkeys(called) if n not in dset]
        it['not_called'], it['not_defined'] = not_called[:LIST_MAX], not_defined[:LIST_MAX]
        pos = dict((n, i) for i, n in enumerate(defined))
        shared = [n for n in dict.fromkeys(called) if n in pos]
        out_of_order = [shared[i] for i in _lis_outside([pos[n] for n in shared])]
        it['out_of_order'] = out_of_order[:LIST_MAX]
        it['totals'] = {
            'not_called': len(not_called),
            'not_defined': len(not_defined),
            'out_of_order': len(out_of_order),
        }
        for fname in ('main', 'config', 'InitGlobals', 'InitCustomTriggers', 'RunInitializationTriggers'):
            f = funcs.get(fname)
            if f is None:
                continue
            for st in f.body:
                for c in ([st.call] if type(st) is jass_ast.CallStmt else []):
                    if c.name in funcs and not _is_skeleton(c.name):
                        out['outside'].append({'from': fname, 'call': c.name, 'line': st.line})
    if text is not None:
        for sig in SIGNATURES:
            n = text.count(sig)
            if n:
                line = text.count('\n', 0, text.find(sig)) + 1
                out['signatures'].append({'signature': sig, 'count': n, 'line': line})
    it = out['init_trig']
    tot = it.get('totals') or {}
    out['counts'] = {'not_called': tot.get('not_called', len(it['not_called'])),
                     'not_defined': tot.get('not_defined', len(it['not_defined'])),
                     'out_of_order': tot.get('out_of_order', len(it['out_of_order'])), 'outside': len(out['outside']),
                     'signatures': len(out['signatures'])}
    out['lines'] = summary(out)
    return out


def summary(r):
    if r.get('error'):
        return [r['error']]
    c = r['counts']
    out = []
    if c['out_of_order'] or c['not_called'] or c['not_defined']:
        out.append('The triggers do not follow one order: %d out of order, %d defined and never called, %d called and '
                   'never defined (%s). A trigger may have been added or moved after the editor wrote the script.' % (
                       c['out_of_order'], c['not_called'], c['not_defined'],
                       ', '.join((r['init_trig']['out_of_order'] + r['init_trig']['not_called'] +
                                  r['init_trig']['not_defined'])[:5])))
    if c['outside']:
        out.append('%d functions are called from the start-up code outside the editor\'s own steps (%s): code that may '
                   'have been added by hand or by a tool.' % (c['outside'], ', '.join(
                       '%s in %s' % (x['call'], x['from']) for x in r['outside'][:4])))
    if c['signatures']:
        out.append('The text holds %s, a name that known grafted code of the Chinese platform maps uses.' % ', '.join(
            x['signature'] for x in r['signatures']))
    if not out:
        out.append('No sign of code added after the editor wrote the script.' if r['applicable'] else
                   'The script does not follow the editor\'s skeleton%s: only the signatures were looked for.' % (
                       ' (JassHelper compiled it)' if r.get('vjass') else ''))
    return out


def reforged_items(r, item=None):
    if r.get('error'):
        return []
    c = r['counts']
    if not (c['outside'] or c['signatures'] or c['out_of_order'] or c['not_called'] or c['not_defined']):
        return []
    make = item or (lambda code, sev, text_, fix, **data: dict(code=code, severity=sev, text=text_, fix=fix, data=data))
    return [make('grafted_code_signs', 'info', ' '.join(r['lines']) + ' Only a sign: a script an optimizer or a plugin '
                 'rewrote looks the same.', 'none', counts=c)]


def check(path):
    if path.lower().endswith(('.j', '.ai')):
        return signs(jass_ast.read_script(path))
    from doctor.fix import single_player
    try:
        _a, sc, _s = single_player.read_map(path)
    except BaseException as e:
        if isinstance(e, KeyboardInterrupt):
            raise
        return {'error': 'The map cannot be read (%s).' % e, 'lines': ['The map cannot be read.']}
    if sc['bytes'] is None or sc['language'] != 'jass':
        return {'error': 'The map has no JASS script.', 'lines': ['The map has no JASS script.']}
    return signs(sc['bytes'].decode('latin-1'))
