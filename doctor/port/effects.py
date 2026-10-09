# Rewrites the effect calls of a map so the layer records where each effect was created.

from doctor.port import swap_calls as T


SWAPS = {
    'AddSpecialEffect': 'DB_efx_cria',
    'AddSpecialEffectLoc': 'DB_efx_cria_loc',
    'AddSpecialEffectTarget': 'DB_efx_cria_alvo',
    'AddSpecialEffectLocBJ': 'DB_efx_cria_loc_bj',
    'AddSpecialEffectTargetUnitBJ': 'DB_efx_cria_alvo_bj',
    'DestroyEffect': 'DB_efx_destroi',
}
LABEL_TEXT = 'effects annotated at creation'
def pluralize(body_text):
    return T.pluralize(body_text, SWAPS)


def applies(body_text, expected_count=None, to_report=False):
    new, info = T.applies(body_text, SWAPS, expected_count=expected_count)
    if to_report and not info['failures']:
        T.report_data(info, LABEL_TEXT)
    return new, info

