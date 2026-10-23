# The largest map each classic Warcraft III game sends to other players, and the warning for a map above it.

MIB = 1024 * 1024
STEPS = (((1, 24, 1), 8 * MIB), ((1, 27, 2), 128 * MIB))
OLD, NEW = STEPS[0][1], STEPS[-1][1]
def for_key(key):
    out = STEPS[0][1]
    for first, limit in STEPS:
        if tuple(key) >= first:
            out = limit
    return out


def _mb(n):
    return n / float(MIB)


def version_warning(size, version, limit):
    if not size or not limit or size <= limit:
        return None
    return ('The map is %.1f MB: Warcraft III %s sends and accepts maps up to %d MB in a game with other players. It '
            'still plays in single player and in a game with only computers.' % (_mb(size), version, limit // MIB))

