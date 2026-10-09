# Scales the life, damage, mana, armor and attributes of a ported map down so the biggest fit the integer limit of the game, keeping the proportions, and converts the script calls.
import io
import math
import os
import re


INT_MAX = 2147483647
HEADROOM = 2.0
ITEM_SLOTS = 6
DIMENSIONS = ('combat', 'armor', 'attribute')

MISC_DEFAULT = {'StrHitPointBonus': 25.0, 'StrRegenBonus': 0.05, 'IntManaBonus': 15.0, 'IntRegenBonus': 0.05,
                'StrAttackBonus': 1.0, 'AgiDefenseBonus': 0.3, 'AgiDefenseBase': -2.0, 'AgiAttackSpeedBonus': 0.02,
                'AgiMoveBonus': 0.0, 'DefenseArmor': 0.06, 'MaxHeroLevel': 10.0}
MISC_RULE = {'StrHitPointBonus': ('attribute', 'combat'), 'StrRegenBonus': ('attribute', 'combat'),
             'IntManaBonus': ('attribute', 'combat'), 'IntRegenBonus': ('attribute', 'combat'),
             'StrAttackBonus': ('attribute', 'combat'), 'AgiDefenseBonus': ('attribute', 'armor'),
             'AgiDefenseBase': (None, 'armor'), 'AgiAttackSpeedBonus': ('attribute', None),
             'AgiMoveBonus': ('attribute', None), 'DefenseArmor': ('armor', None)}

UNIT_FIELDS = {
    'uhpm': ('UnitBalance', 'HP', 'combat', 0, 'hp'), 'umpm': ('UnitBalance', 'manaN', 'combat', 0, 'mana'),
    'umpi': ('UnitBalance', 'mana0', 'combat', 0, None), 'uhpr': ('UnitBalance', 'regenHP', 'combat', 2, None),
    'umpr': ('UnitBalance', 'regenMana', 'combat', 2, None),
    'ua1b': ('UnitWeapons', 'dmgplus1', 'combat', 0, 'damage1'), 'ua2b': ('UnitWeapons', 'dmgplus2', 'combat', 0,
                                                                          'damage2'),
    'ua1d': ('UnitWeapons', 'dice1', None, 0, 'dice1'), 'ua2d': ('UnitWeapons', 'dice2', None, 0, 'dice2'),
    'ua1s': ('UnitWeapons', 'sides1', 'sides', 0, 'sides1'), 'ua2s': ('UnitWeapons', 'sides2', 'sides', 0, 'sides2'),
    'udu1': ('UnitWeapons', 'dmgUp1', 'combat', 0, None), 'udu2': ('UnitWeapons', 'dmgUp2', 'combat', 0, None),
    'ustr': ('UnitBalance', 'STR', 'attribute', 0, 'attr'), 'uagi': ('UnitBalance', 'AGI', 'attribute', 0, 'attr'),
    'uint': ('UnitBalance', 'INT', 'attribute', 0, 'attr'),
    'ustp': ('UnitBalance', 'STRplus', 'attribute', 2, 'attr_level'),
    'uagp': ('UnitBalance', 'AGIplus', 'attribute', 2, 'attr_level'),
    'uinp': ('UnitBalance', 'INTplus', 'attribute', 2, 'attr_level'),
    'udef': ('UnitBalance', 'def', 'armor', 0, 'armor'), 'udup': ('UnitBalance', 'defUp', 'armor', 0, None),
}
ITEM_FIELDS = {'ihtp': ('ItemData', 'HP', 'combat', 0, None)}
DESTRUCTABLE_FIELDS = {'bhps': ('DestructableData', 'HP', 'combat', 2, None)}
UPGRADE_EFFECTS = {'rhpx': 'combat', 'rmnx': 'combat', 'ratx': 'combat', 'rspi': 'combat', 'rarm': 'armor'}
BONUS_ROLE = {'Ilif': 'hp_bonus', 'Iman': 'mana_bonus', 'Iatt': 'damage_bonus', 'Istr': 'attr_bonus',
              'Iagi': 'attr_bonus', 'Iint': 'attr_bonus', 'Idef': 'armor_bonus'}

SPECIES = {
    'unit': ('war3map.w3u', False, ('UnitBalance', 'UnitWeapons'), UNIT_FIELDS),
    'item': ('war3map.w3t', False, ('ItemData',), ITEM_FIELDS),
    'destructable': ('war3map.w3b', False, ('DestructableData',), DESTRUCTABLE_FIELDS),
    'ability': ('war3map.w3a', True, ('AbilityData',), None),
    'upgrade': ('war3map.w3q', True, ('UpgradeData',), None),
}
ABILITY_FIELDS = {
    'Adm1': (
        'combat',
        1,
        2,
        (
            'Aadm',
            'ACdm',
            'Adis',
            'Adsm',
            'Adch',
        ),
    ),
    'Adm2': (
        'combat',
        2,
        2,
        (
            'Aadm',
            'ACdm',
            'Adis',
            'Adsm',
            'Adch',
        ),
    ),
    'Ams1': (
        'combat',
        1,
        2,
        (
            'Aams',
            'ACam',
        ),
    ),
    'Ams3': (
        'combat',
        3,
        0,
        (
            'Aams',
            'ACam',
            'AIxs',
        ),
    ),
    'Ams4': (
        'combat',
        4,
        0,
        (
            'Aams',
            'ACam',
            'AIxs',
            'Aam2',
        ),
    ),
    'Apl2': (
        'combat',
        2,
        2,
        (
            'Aapl',
            'Aap1',
            'Aap2',
            'Aap3',
            'Aap4',
            'Aap5',
        ),
    ),
    'Can1': (
        'combat',
        1,
        2,
        (
            'Acan',
            'ACcn',
        ),
    ),
    'Can2': (
        'combat',
        2,
        2,
        (
            'Acan',
            'ACcn',
        ),
    ),
    'Chd3': ('combat', 3, 2, ('Achd',)),
    'Cor1': ('combat', 1, 2, ('Acor',)),
    'Ctb1': ('combat', 1, 2, ('ACtb',)),
    'Ctc1': (
        'combat',
        1,
        2,
        (
            'ACtc',
            'ACt2',
        ),
    ),
    'Ctc2': (
        'combat',
        2,
        2,
        (
            'ACtc',
            'ACt2',
        ),
    ),
    'Dda2': (
        'combat',
        2,
        2,
        (
            'Adda',
            'Amnx',
            'Amnz',
            'Asds',
            'Auco',
        ),
    ),
    'Dda4': (
        'combat',
        4,
        2,
        (
            'Adda',
            'Amnx',
            'Amnz',
            'Asds',
            'Auco',
        ),
    ),
    'Dev2': ('combat', 2, 2, ('Advc',)),
    'Dtn1': ('combat', 1, 2, ('Adtn',)),
    'Dtn2': ('combat', 2, 2, ('Adtn',)),
    'Eat3': ('combat', 3, 2, ('Aeat',)),
    'Eer1': (
        'combat',
        1,
        2,
        (
            'AEer',
            'Aenr',
            'Aenw',
        ),
    ),
    'Efk1': (
        'combat',
        1,
        2,
        (
            'AEfk',
            'Aroc',
        ),
    ),
    'Efk2': (
        'combat',
        2,
        2,
        (
            'AEfk',
            'Aroc',
        ),
    ),
    'Eim2': (
        'combat',
        2,
        2,
        (
            'AEim',
            'ACim',
            'ANpi',
            'Apmf',
            'Apig',
        ),
    ),
    'Eim3': (
        'combat',
        3,
        2,
        (
            'AEim',
            'ACim',
            'ANpi',
            'Apmf',
            'Apig',
        ),
    ),
    'Emb1': (
        'combat',
        1,
        2,
        (
            'AEmb',
            'Amnb',
            'Ambd',
        ),
    ),
    'Eme5': (
        'combat',
        5,
        2,
        (
            'AEme',
            'AEIl',
            'AEvi',
        ),
    ),
    'Esf1': (
        'combat',
        1,
        2,
        (
            'AEsf',
            'AEsb',
            'ANmo',
            'ACmo',
        ),
    ),
    'Esh1': (
        'combat',
        1,
        2,
        (
            'AEsh',
            'ACss',
        ),
    ),
    'Esh5': (
        'combat',
        5,
        2,
        (
            'AEsh',
            'ACss',
        ),
    ),
    'Etq1': ('combat', 1, 2, ('AEtq',)),
    'Fae1': (
        'armor',
        1,
        0,
        (
            'Afae',
            'Afa2',
            'ACff',
        ),
    ),
    'Hab1': (
        'combat',
        1,
        2,
        (
            'AHab',
            'ACba',
            'AIba',
        ),
    ),
    'Had1': (
        'armor',
        1,
        2,
        (
            'AHad',
            'AIad',
            'ACav',
        ),
    ),
    'Hav1': ('armor', 1, 2, ('AHav',)),
    'Hav2': ('combat', 2, 2, ('AHav',)),
    'Hav3': ('combat', 3, 2, ('AHav',)),
    'Hbh3': (
        'combat',
        3,
        2,
        (
            'AHbh',
            'ACbh',
        ),
    ),
    'Hbz2': (
        'combat',
        2,
        2,
        (
            'AHbz',
            'ACbz',
            'ANrf',
            'ACrf',
        ),
    ),
    'Hbz5': (
        'combat',
        5,
        2,
        (
            'AHbz',
            'ACbz',
            'ANrf',
            'ACrf',
        ),
    ),
    'Hbz6': (
        'combat',
        6,
        2,
        (
            'AHbz',
            'ACbz',
            'ANrf',
            'ACrf',
        ),
    ),
    'Hca1': (
        'combat',
        1,
        2,
        (
            'AHca',
            'ACcw',
            'ANfa',
        ),
    ),
    'Hea1': (
        'combat',
        1,
        2,
        (
            'Ahea',
            'Anh1',
            'Anh2',
            'Anhe',
        ),
    ),
    'Hfa1': (
        'combat',
        1,
        2,
        (
            'AHfa',
            'ACsa',
        ),
    ),
    'Hfs1': (
        'combat',
        1,
        2,
        (
            'AHfs',
            'ACfs',
            'Abof',
        ),
    ),
    'Hfs3': (
        'combat',
        3,
        2,
        (
            'AHfs',
            'ACfs',
            'Abof',
        ),
    ),
    'Hfs6': (
        'combat',
        6,
        2,
        (
            'AHfs',
            'ACfs',
            'Abof',
        ),
    ),
    'Hhb1': ('combat', 1, 2, ('AHhb',)),
    'Hsb1': ('combat', 1, 2, ('Ahsb',)),
    'Htb1': (
        'combat',
        1,
        2,
        (
            'AHtb',
            'ANfb',
            'Awfb',
            'ACfb',
            'ACcb',
        ),
    ),
    'Htc1': ('combat', 1, 2, ('AHtc',)),
    'Htc2': ('combat', 2, 2, ('AHtc',)),
    'Htc5': ('combat', 5, 2, ('AHtc',)),
    'Iagi': (
        'attribute',
        1,
        0,
        (
            'Aamk',
            'AIab',
            'AIa1',
            'AIa3',
            'AIa4',
            'AIa5',
            'AIa6',
            'AIx5',
            'AIx1',
            'AIx2',
            'AIx3',
            'AIx4',
            'AIs1',
            'AIs3',
            'AIs4',
            'AIs5',
            'AIs6',
            'AIi1',
            'AIi3',
            'AIi4',
            'AIi5',
            'AIi6',
            'AIxm',
            'AIam',
            'AIim',
            'AIsm',
            'AIgm',
            'AItm',
            'AInm',
        ),
    ),
    'Iarp': ('armor', 2, 0, ('AIcb',)),
    'Icfm': ('combat', 2, 0, ('AIcf',)),
    'Icfx': ('combat', 3, 0, ('AIcf',)),
    'Idam': (
        'combat',
        1,
        2,
        (
            'AIdf',
            'AIfb',
            'AIzb',
            'AIob',
            'AIll',
            'AIlb',
            'AIsb',
            'AIpb',
            'AIf2',
        ),
    ),
    'Idef': (
        'armor',
        1,
        0,
        (
            'AIde',
            'AId1',
            'AId2',
            'AId3',
            'AId4',
            'AId5',
            'AIda',
            'AIdb',
        ),
    ),
    'Idid': (
        'combat',
        2,
        0,
        (
            'AIdi',
            'AIds',
        ),
    ),
    'Idim': (
        'combat',
        1,
        0,
        (
            'AIdi',
            'AIds',
        ),
    ),
    'Idps': ('combat', 1, 2, ('AIls',)),
    'Ihp2': (
        'combat',
        2,
        0,
        (
            'AIda',
            'AIdb',
        ),
    ),
    'Ihpg': (
        'combat',
        1,
        0,
        (
            'AIhe',
            'AIh1',
            'AIh2',
            'AIh3',
            'AIha',
            'AIhb',
            'AIdg',
            'AIg2',
        ),
    ),
    'Ihpr': (
        'combat',
        1,
        0,
        (
            'Arel',
            'Arll',
        ),
    ),
    'Ihps': (
        'combat',
        1,
        0,
        (
            'AIre',
            'AIra',
        ),
    ),
    'Iint': (
        'attribute',
        2,
        0,
        (
            'Aamk',
            'AIab',
            'AIa1',
            'AIa3',
            'AIa4',
            'AIa5',
            'AIa6',
            'AIx5',
            'AIx1',
            'AIx2',
            'AIx3',
            'AIx4',
            'AIs1',
            'AIs3',
            'AIs4',
            'AIs5',
            'AIs6',
            'AIi1',
            'AIi3',
            'AIi4',
            'AIi5',
            'AIi6',
            'AIxm',
            'AIam',
            'AIim',
            'AIsm',
            'AIgm',
            'AItm',
            'AInm',
        ),
    ),
    'Ilif': (
        'combat',
        1,
        0,
        (
            'AIml',
            'AImi',
            'AIlf',
            'AIl1',
            'AIl2',
            'AImh',
        ),
    ),
    'Iman': (
        'combat',
        1,
        0,
        (
            'AImm',
            'AImb',
            'AIbm',
        ),
    ),
    'Imp2': (
        'combat',
        3,
        0,
        (
            'AIda',
            'AIdb',
        ),
    ),
    'Impg': (
        'combat',
        1,
        0,
        (
            'AIm1',
            'AIm2',
            'AImr',
        ),
    ),
    'Imps': (
        'combat',
        2,
        0,
        (
            'AIre',
            'AIra',
        ),
    ),
    'Inf2': (
        'armor',
        2,
        0,
        (
            'Ainf',
            'ACif',
        ),
    ),
    'Inf4': (
        'combat',
        4,
        2,
        (
            'Ainf',
            'ACif',
        ),
    ),
    'Istr': (
        'attribute',
        3,
        0,
        (
            'Aamk',
            'AIab',
            'AIa1',
            'AIa3',
            'AIa4',
            'AIa5',
            'AIa6',
            'AIx5',
            'AIx1',
            'AIx2',
            'AIx3',
            'AIx4',
            'AIs1',
            'AIs3',
            'AIs4',
            'AIs5',
            'AIs6',
            'AIi1',
            'AIi3',
            'AIi4',
            'AIi5',
            'AIi6',
            'AIxm',
            'AIam',
            'AIim',
            'AIsm',
            'AIgm',
            'AItm',
            'AInm',
        ),
    ),
    'Ixs1': ('combat', 1, 2, ('AIxs',)),
    'Lsh1': (
        'combat',
        1,
        2,
        (
            'Alsh',
            'ACls',
        ),
    ),
    'Nab3': ('armor', 3, 0, ('ANab',)),
    'Nab4': ('combat', 4, 2, ('ANab',)),
    'Nab5': ('combat', 5, 2, ('ANab',)),
    'Nba1': (
        'combat',
        1,
        2,
        (
            'ANba',
            'ANbs',
        ),
    ),
    'Nbf5': (
        'combat',
        5,
        2,
        (
            'ANbf',
            'ACbc',
            'ACbf',
        ),
    ),
    'Nbr1': ('combat', 1, 2, ('ANbr',)),
    'Ncs1': (
        'combat',
        1,
        2,
        (
            'ANhs',
            'ANcs',
            'ANc1',
            'ANc2',
            'ANc3',
        ),
    ),
    'Ncs4': (
        'combat',
        4,
        2,
        (
            'ANhs',
            'ANcs',
            'ANc1',
            'ANc2',
            'ANc3',
        ),
    ),
    'Ndo1': ('combat', 1, 2, ('ANdo',)),
    'Ndr1': (
        'combat',
        1,
        2,
        (
            'ANdr',
            'AHdr',
        ),
    ),
    'Ndr2': (
        'combat',
        2,
        2,
        (
            'ANdr',
            'AHdr',
        ),
    ),
    'Ndr4': (
        'combat',
        4,
        2,
        (
            'ANdr',
            'AHdr',
            'ACdr',
            'ACsm',
        ),
    ),
    'Ndr5': (
        'combat',
        5,
        2,
        (
            'ANdr',
            'AHdr',
            'ACdr',
            'ACsm',
        ),
    ),
    'Ndr7': (
        'combat',
        7,
        2,
        (
            'ANdr',
            'AHdr',
            'ACdr',
            'ACsm',
        ),
    ),
    'Ndr9': (
        'combat',
        9,
        2,
        (
            'ANdr',
            'AHdr',
            'ACdr',
            'ACsm',
        ),
    ),
    'Neg2': ('combat', 2, 2, ('ANeg',)),
    'Nfd3': ('combat', 3, 2, ('ANfd',)),
    'Nic2': ('combat', 2, 2, ('ANic',)),
    'Nic4': ('combat', 4, 2, ('ANic',)),
    'Nmr1': ('combat', 1, 2, ('ANmr',)),
    'Nrg5': (
        'attribute',
        5,
        0,
        (
            'ANrg',
            'ANg1',
            'ANg2',
            'ANg3',
        ),
    ),
    'Nrg6': (
        'armor',
        6,
        0,
        (
            'ANrg',
            'ANg1',
            'ANg2',
            'ANg3',
        ),
    ),
    'Nsa5': ('combat', 5, 2, ('ANsa',)),
    'Nso1': ('combat', 1, 2, ('ANso',)),
    'Nst3': ('combat', 3, 2, ('ANst',)),
    'Nvc5': ('combat', 5, 2, ('ANvc',)),
    'Ocl1': (
        'combat',
        1,
        2,
        (
            'AOcl',
            'AOhw',
            'ACcl',
            'AChv',
            'ANfl',
        ),
    ),
    'Ocr3': (
        'combat',
        3,
        2,
        (
            'AOcr',
            'ACct',
            'ANdb',
        ),
    ),
    'Oeq2': (
        'combat',
        2,
        2,
        (
            'AOeq',
            'SNeq',
        ),
    ),
    'Osh1': (
        'combat',
        1,
        2,
        (
            'AOsh',
            'ACsh',
            'ACst',
        ),
    ),
    'Osh2': (
        'combat',
        2,
        2,
        (
            'AOsh',
            'ACsh',
            'ACst',
        ),
    ),
    'Owk3': ('combat', 3, 2, ('AOwk',)),
    'Oww1': ('combat', 1, 2, ('AOww',)),
    'Poa1': ('combat', 1, 2, ('AEpa',)),
    'Poi1': (
        'combat',
        1,
        2,
        (
            'Apoi',
            'Apo2',
            'Aven',
            'ACvs',
            'ANpa',
        ),
    ),
    'Prg3': (
        'combat',
        3,
        2,
        (
            'Aprg',
            'ACpu',
            'AIlp',
            'AIpg',
        ),
    ),
    'Prg6': (
        'combat',
        6,
        0,
        (
            'Aprg',
            'ACpu',
            'AIlp',
            'AIpg',
            'Apg2',
        ),
    ),
    'Rej1': (
        'combat',
        1,
        2,
        (
            'Arej',
            'ACrj',
            'ACr2',
            'Arpb',
            'Arpl',
        ),
    ),
    'Rej2': (
        'combat',
        2,
        2,
        (
            'Arej',
            'ACrj',
            'ACr2',
            'Arpb',
            'Arpm',
        ),
    ),
    'Roa2': (
        'armor',
        2,
        0,
        (
            'Aroa',
            'Ara2',
            'ACro',
            'ACr1',
            'AIrr',
            'ANht',
            'ANbr',
        ),
    ),
    'Roa3': (
        'combat',
        3,
        2,
        (
            'Aroa',
            'Ara2',
            'ACro',
            'ACr1',
            'AIrr',
            'ANht',
            'ANbr',
        ),
    ),
    'Roa4': (
        'combat',
        4,
        2,
        (
            'Aroa',
            'Ara2',
            'ACro',
            'ACr1',
            'AIrr',
            'ANht',
            'ANbr',
            'Ahnl',
        ),
    ),
    'Rpb3': (
        'combat',
        3,
        2,
        (
            'Arpb',
            'Arpl',
        ),
    ),
    'Rpb4': (
        'combat',
        4,
        2,
        (
            'Arpb',
            'Arpm',
        ),
    ),
    'Spo1': ('combat', 1, 2, ('Aspo',)),
    'Ssk2': (
        'combat',
        2,
        2,
        (
            'Assk',
            'AHss',
        ),
    ),
    'Ssk3': (
        'combat',
        3,
        2,
        (
            'Assk',
            'AHss',
        ),
    ),
    'Tau6': ('armor', 6, 2, ('AHnt',)),
    'Tdg1': ('combat', 1, 2, ('Atdg',)),
    'Tdg3': ('combat', 3, 2, ('Atdg',)),
    'Tdg5': ('combat', 5, 2, ('Atdg',)),
    'Uco5': ('combat', 5, 2, ('Auco',)),
    'Ucs1': (
        'combat',
        1,
        2,
        (
            'AUcs',
            'ANbf',
            'ACbc',
            'ACbf',
            'ACca',
            'ACcv',
        ),
    ),
    'Ucs2': (
        'combat',
        2,
        2,
        (
            'AUcs',
            'ANbf',
            'ACbc',
            'ACbf',
            'ACca',
            'ACcv',
        ),
    ),
    'Udc1': (
        'combat',
        1,
        2,
        (
            'AUdc',
            'ACdc',
        ),
    ),
    'Ufa2': (
        'armor',
        2,
        2,
        (
            'AUfa',
            'AUfu',
            'ACfa',
        ),
    ),
    'Ufn1': (
        'combat',
        1,
        2,
        (
            'AUfn',
            'ACfn',
        ),
    ),
    'Ufn2': (
        'combat',
        2,
        2,
        (
            'AUfn',
            'ACfn',
        ),
    ),
    'Ufn5': (
        'combat',
        5,
        2,
        (
            'AUfn',
            'ACfn',
        ),
    ),
    'Uhf2': (
        'combat',
        2,
        2,
        (
            'Auhf',
            'Suhf',
            'ACuf',
        ),
    ),
    'Uim3': (
        'combat',
        3,
        2,
        (
            'AUim',
            'ACmp',
        ),
    ),
    'Uin1': (
        'combat',
        1,
        2,
        (
            'AUin',
            'ANin',
            'SNin',
            'AIin',
        ),
    ),
    'Uls5': (
        'combat',
        5,
        2,
        (
            'AUls',
            'AUwc',
        ),
    ),
    'Uts3': (
        'armor',
        3,
        2,
        (
            'AUts',
            'ANth',
            'AUss',
        ),
    ),
    'War2': (
        'combat',
        2,
        2,
        (
            'Awar',
            'ACpv',
        ),
    ),
    'Wrs1': (
        'combat',
        1,
        2,
        (
            'Awrs',
            'Ahrs',
            'Awrh',
            'Awrg',
            'AOws',
        ),
    ),
    'abs1': ('combat', 1, 2, ('Aabs',)),
    'abs2': ('combat', 2, 2, ('Aabs',)),
    'amcs': ('combat', 0, 0, None),
    'ave5': (
        'combat',
        5,
        2,
        (
            'Aave',
            'Astn',
        ),
    ),
    'bld7': ('combat', 7, 2, ('AHbd',)),
    'bns6': ('combat', 6, 2, ('AUwc',)),
    'chr2': (
        'combat',
        2,
        2,
        (
            'AHch',
            'AUbr',
            'ANcp',
        ),
    ),
    'dvm1': ('combat', 1, 2, ('Advm',)),
    'dvm2': ('combat', 2, 2, ('Advm',)),
    'dvm3': ('combat', 3, 2, ('Advm',)),
    'dvm4': ('combat', 4, 2, ('Advm',)),
    'dvm5': ('combat', 5, 2, ('Advm',)),
    'fak1': ('combat', 1, 2, ('Afak',)),
    'fbk1': ('combat', 1, 2, ('Afbk',)),
    'fbk3': ('combat', 3, 2, ('Afbk',)),
    'fbk5': (
        'combat',
        5,
        2,
        (
            'Afbk',
            'Afbt',
            'Afbb',
        ),
    ),
    'flk3': (
        'combat',
        3,
        2,
        (
            'Aflk',
            'Afsh',
        ),
    ),
    'flk4': (
        'combat',
        4,
        2,
        (
            'Aflk',
            'Afsh',
        ),
    ),
    'flk5': (
        'combat',
        5,
        2,
        (
            'Aflk',
            'Afsh',
        ),
    ),
    'hcl1': ('combat', 1, 2, ('AHcl',)),
    'hcl2': ('combat', 2, 2, ('AHcl',)),
    'hcl7': ('combat', 7, 2, ('AHcl',)),
    'hcr1': ('combat', 1, 2, ('AHcr',)),
    'hcr2': ('combat', 2, 2, ('AHcr',)),
    'hgh6': ('combat', 6, 2, ('AHgh',)),
    'hgr1': ('armor', 1, 2, ('AHgr',)),
    'hgr2': ('armor', 2, 2, ('AHgr',)),
    'hhc1': ('combat', 6, 2, ('AHhc',)),
    'hhc4': ('armor', 9, 2, ('AHhc',)),
    'hhr1': ('combat', 1, 2, ('AHhr',)),
    'hic1': ('armor', 1, 2, ('AHic',)),
    'hic4': ('combat', 4, 2, ('AHic',)),
    'hmc2': ('combat', 2, 2, ('AHmc',)),
    'hsa7': ('combat', 7, 2, ('AHas',)),
    'hsf1': ('combat', 1, 2, ('AHsf',)),
    'hsf3': ('combat', 3, 2, ('AHsf',)),
    'hsf4': ('combat', 4, 2, ('AHsf',)),
    'hsl1': ('combat', 1, 2, ('AHhs',)),
    'idc1': ('combat', 1, 2, ('AIdc',)),
    'idc2': ('combat', 2, 2, ('AIdc',)),
    'ipv1': ('combat', 1, 2, ('AIpv',)),
    'irc2': ('combat', 2, 0, ('AIrc',)),
    'irc3': ('combat', 3, 0, ('AIrc',)),
    'irl1': (
        'combat',
        1,
        2,
        (
            'AIrl',
            'AIpr',
            'AIsl',
            'AIpl',
            'AIp1',
            'AIp2',
            'AIp3',
            'AIp4',
            'AIp5',
            'AIp6',
        ),
    ),
    'irl2': (
        'combat',
        2,
        2,
        (
            'AIrl',
            'AIpr',
            'AIsl',
            'AIpl',
            'AIp1',
            'AIp2',
            'AIp3',
            'AIp4',
            'AIp5',
            'AIp6',
        ),
    ),
    'isr1': (
        'combat',
        1,
        2,
        (
            'AIsr',
            'AIss',
        ),
    ),
    'liq1': ('combat', 1, 2, ('Aliq',)),
    'mfl3': ('combat', 3, 2, ('Amfl',)),
    'mfl4': ('combat', 4, 2, ('Amfl',)),
    'mls1': ('combat', 1, 2, ('Amls',)),
    'pbl1': ('combat', 1, 2, ('AHpb',)),
    'pbl6': ('combat', 5, 2, ('AHpb',)),
    'pxf1': ('combat', 1, 2, ('Apxf',)),
    'pxf2': ('combat', 2, 2, ('Apxf',)),
    'sol1': ('combat', 1, 2, ('AHsl',)),
    'sol2': ('combat', 2, 2, ('AHsl',)),
    'sol3': ('combat', 3, 2, ('AHsl',)),
    'swp1': ('combat', 1, 2, ('AHsw',)),
    'swp6': ('combat', 5, 2, ('AHsw',)),
    'swp8': ('armor', 7, 2, ('AHsw',)),
    'ubr1': ('combat', 7, 2, ('AUbr',)),
    'udb1': ('combat', 1, 2, ('AUdb',)),
    'ula1': ('combat', 1, 2, ('AUla',)),
    'ula2': ('combat', 2, 2, ('AUla',)),
    'ula7': ('combat', 7, 2, ('AUla',)),
    'ula8': ('combat', 8, 2, ('AUla',)),
    'uvg2': (
        'attribute',
        2,
        0,
        (
            'AUvg',
            'AHal',
        ),
    ),
    'uvg7': ('combat', 7, 2, ('AHal',)),
    'uwf3': ('combat', 3, 2, ('AUwf',)),
    'uwf4': ('armor', 4, 0, ('AUwf',)),
}

RX_COMBAT = re.compile(r'(?i)damage|hit ?points?|\blife\b|heal|health|\bmana\b|strength|agility|intelligence|'
                       r'absorbed|regenerat|drained|\bshield (?:life|health)')
RX_ARMOR = re.compile(r'(?i)armor|defense')
RX_NOT = re.compile(r'(?i)interval|radius|area(?! of effect damage)|delay|duration|frequency|period|cooldown|'
                    r'lifetime|type|amplification|factor|%|percent|chance|multipl|fraction|efficiency|per mana point|'
                    r'per hit ?point|per summoned hitpoint|allowed|include|exclude|applies|dispel|split|only at night|'
                    r'taken increase|converted|max health|resistance|damage reduction|magic damage|target count|'
                    r'steal|stolen|range|distance|speed|\bcount\b|number of|level|\btime\b')
RX_ATTRIBUTE = re.compile(r'(?i)strength|agility|intelligence')
NOT_AMOUNT = frozenset(('Cac1', 'Akb1', 'Har1', 'Cmg3', 'Nms1', 'Eah1', 'Nso3', 'Arm1', 'Oar1', 'Def7', 'Def8',
                        'Mbt1', 'Mbt2', 'Idic'))


def classify(display_name, field_id):
    if field_id in NOT_AMOUNT or RX_NOT.search(display_name or ''):
        return None
    if RX_ATTRIBUTE.search(display_name):
        return 'attribute'
    if RX_ARMOR.search(display_name) and not re.search(r'(?i)damage', display_name):
        return 'armor'
    if RX_COMBAT.search(display_name):
        return 'combat'
    return None


def factor_for(stack, headroom=HEADROOM):
    need = float(stack) * headroom / INT_MAX
    if need <= 1.0:
        return 1
    e = 10 ** int(math.floor(math.log10(need)))
    for m in (1, 2, 5, 10):
        if m * e >= need * (1 - 1e-12):
            return int(m * e)
    return int(10 * e)


def scale_value(v, typ, factor, dim, stats=None):
    x = float(v) / factor
    if typ != 0:
        return x
    sign = -1 if x < 0 else 1
    r = sign * int(math.floor(abs(x) + 0.5))
    if r == 0 and v != 0:
        r = sign
        if stats is not None:
            stats['rounded_to_one'] = stats.get('rounded_to_one', 0) + 1
    elif stats is not None and x and abs(r - x) / abs(x) > 0.1:
        stats['imprecise'] = stats.get('imprecise', 0) + 1
    if dim == 'sides' and r < 1 and v > 0:
        r = 1
    return max(-INT_MAX, min(INT_MAX, r))


def _num(text):
    if text is None:
        return None
    t = str(text).strip().strip('"')
    if not t or t in ('-', '_'):
        return None
    try:
        return float(t)
    except ValueError:
        return None


def _text(v, typ):
    from doctor.data import objects
    if typ == 0:
        return str(int(v))
    return objects.short_real(float(v))


def _parts(body):
    out, buf = [], None
    for p in body.split(';'):
        if buf is not None:
            buf += ';' + p
            if buf.count('"') % 2 == 0:
                out.append(buf)
                buf = None
            continue
        if p.startswith('K"') and p.count('"') % 2 == 1:
            buf = p
            continue
        out.append(p)
    if buf is not None:
        out.append(buf)
    return out


class Sheet(object):
    def __init__(self, raw, path=None, name=''):
        self.raw = raw
        self.path = path
        self.name = name
        self.lines = raw.decode('utf-8', 'surrogateescape').split('\n')
        self.cells = {}
        y = 0
        for i, line in enumerate(self.lines):
            if not line.startswith('C;'):
                continue
            x = k = None
            for p in _parts(line.rstrip('\r')[2:]):
                try:
                    if p.startswith('X'):
                        x = int(p[1:])
                    elif p.startswith('Y'):
                        y = int(p[1:])
                    elif p.startswith('K'):
                        k = p[1:]
                except ValueError:
                    pass
            if x is None or k is None:
                continue
            quoted = len(k) >= 2 and k[0] == '"' and k[-1] == '"'
            self.cells[(y, x)] = (i, k[1:-1] if quoted else k, quoted)
        self.columns = dict((v, x) for (yy, x), (_i, v, _q) in self.cells.items() if yy == 1 and v)
        self.rows = {}
        for (yy, x), (_i, v, _q) in sorted(self.cells.items()):
            if x == 1 and yy != 1:
                self.rows.setdefault(v, yy)
        self.changed = 0

    def get(self, row, column):
        y, x = self.rows.get(row), self.columns.get(column)
        if y is None or x is None:
            return None
        c = self.cells.get((y, x))
        return c[1] if c else None

    def set(self, row, column, text):
        y, x = self.rows.get(row), self.columns.get(column)
        i, old, quoted = self.cells[(y, x)]
        if old == text:
            return
        line = self.lines[i]
        cr = '\r' if line.endswith('\r') else ''
        parts = _parts(line.rstrip('\r')[2:])
        parts = [('K"%s"' % text if quoted else 'K' + text) if p.startswith('K') else p for p in parts]
        self.lines[i] = 'C;' + ';'.join(parts) + cr
        self.cells[(y, x)] = (i, text, quoted)
        self.changed += 1

    def to_bytes(self):
        return '\n'.join(self.lines).encode('utf-8', 'surrogateescape') if self.changed else self.raw


class ObjectFile(object):
    def __init__(self, raw, name, path=None):
        from doctor.data import objects
        self.name = name
        self.path = path
        self.levels = objects.uses_levels(name)
        self.raw = raw
        if raw is None:
            self.version, objs, self.tail = 2, [], b''
        else:
            self.version, objs, pos = objects.read_objects_bytes(raw, self.levels, name, with_end=True)
            self.tail = raw[pos:]
        self.objects = [[t, o, n, objects.with_item_sets([list(m) for m in mods], mods)] for t, o, n, mods in objs]
        self.index = {}
        for ob in self.objects:
            self.index[ob[2] if ob[2].strip('\0') else ob[1]] = ob
        self.changed = 0

    def mods(self, ob):
        return dict(((m[0], m[2] if self.levels else 0), m) for m in ob[3])

    def obj(self, oid):
        ob = self.index.get(oid)
        if ob is None:
            ob = [0, oid, '\0\0\0\0', []]
            self.objects.append(ob)
            self.index[oid] = ob
        return ob

    def set_mod(self, mod, value):
        if mod[1] == 0:
            value = int(value)
        if mod[4] != value:
            mod[4] = value
            self.changed += 1

    def add_mod(self, oid, field, typ, level, data, value):
        ob = self.obj(oid)
        ob[3].append([field, typ, level, data, int(value) if typ == 0 else float(value), b'\0\0\0\0'])
        self.changed += 1

    def to_bytes(self):
        from doctor.data import objects
        if not self.changed:
            return self.raw
        objs = [(t, o, n, objects.with_item_sets([tuple(m) for m in mods], mods)) for t, o, n, mods in self.objects]
        return objects.write_objects_bytes(self.version, objs, self.levels) + self.tail


class Work(object):
    def __init__(self, data_dir, sources=(), base='auto', script=None, headroom=HEADROOM, pjass_root=None,
                 pjass_tmp=None, write=True):
        self.data_dir = data_dir
        self.sources = list(sources)
        self.base = base
        self.script = script
        self.headroom = headroom
        self.pjass_root = pjass_root
        self.pjass_tmp = pjass_tmp
        self.write = write

    def find(self, name):
        parts = name.replace('/', '\\').split('\\')
        dst = os.path.join(self.data_dir, *parts) if self.data_dir else None
        for src in ([self.data_dir] if self.data_dir else []) + self.sources:
            if callable(src):
                d = src(name)
                if d:
                    return d, dst
                continue
            p = _find_ci(src, parts)
            if p and os.path.getsize(p):
                if dst and src == self.data_dir:
                    dst = p
                elif dst:
                    dst = os.path.join(self.data_dir, *(parts[:-1] + [os.path.basename(p)]))
                return open(p, 'rb').read(), dst
        return None, dst

    def game(self):
        if callable(self.base) or self.base is None:
            return self.base
        try:
            from doctor.data import objects
            b = objects.GameBase(balance=None)
        except Exception:
            self.base = None
            return None

        def read(name):
            cam = b.resolve('units\\%s.slk' % name.lower())
            return b.casc.read_data(cam) if cam else None
        self.base = read
        return read


def _find_ci(folder, parts):
    cur = folder
    for part in parts:
        if not os.path.isdir(cur):
            return None
        hit = next((f for f in os.listdir(cur) if f.lower() == part.lower()), None)
        if hit is None:
            return None
        cur = os.path.join(cur, hit)
    return cur if os.path.isfile(cur) else None


class Value(object):
    __slots__ = ('species', 'oid', 'field', 'level', 'value', 'typ', 'dim', 'role', 'write')

    def __init__(self, species, oid, field, level, value, typ, dim, role, write):
        self.species, self.oid, self.field, self.level = species, oid, field, level
        self.value, self.typ, self.dim, self.role, self.write = value, typ, dim, role, write


def _sheets(work, warnings):
    game = None
    out = {}
    for name in ('UnitBalance', 'UnitWeapons', 'ItemData', 'DestructableData', 'AbilityData', 'UpgradeData'):
        raw, dst = work.find('Units\\%s.slk' % name)
        if raw:
            out[name] = Sheet(raw, dst, name)
            continue
        if game is None:
            game = work.game() or False
            if not game:
                warnings.append('the game data could not be read (Warcraft III not installed?): the objects the map '
                                'does not change keep the game values, unscaled')
        d = game(name) if game else None
        if d:
            out[name] = Sheet(d, None, name)
    return out


def _writer_sheet(sheet, row, column):
    def w(v, typ):
        sheet.set(row, column, _text(v, typ))
    return w


def _writer_mod(f, mod):
    def w(v, typ):
        f.set_mod(mod, v)
    return w


def _writer_add(f, oid, field, typ, level, data):
    def w(v, _typ):
        f.add_mod(oid, field, typ, level, data, v)
    return w


def _base_value(sheet, row, column):
    return _num(sheet.get(row, column)) if sheet is not None else None


def _inherit(sh, f, oid, orig, fid, typ, level, data, column):
    if sh.path is not None:
        return _writer_sheet(sh, orig, column) if orig == oid else None
    return _writer_add(f, oid, fid, typ, level, data)


def _gather_flat(species, f, sheets, out):
    _fname, _lv, slks, fields = SPECIES[species]
    ids = set()
    for s in slks:
        if sheets.get(s):
            ids |= set(sheets[s].rows)
    ids |= set(f.index)
    dest = sheets.get('DestructableData')
    for oid in sorted(ids):
        ob = f.index.get(oid)
        orig = ob[1] if ob is not None else oid
        if species == 'destructable' and dest is not None and 'tree' in (dest.get(orig, 'targType') or '').lower():
            continue
        mods = f.mods(ob) if ob is not None else {}
        for fid, (slkname, column, dim, typ, role) in fields.items():
            m = mods.get((fid, 0))
            if m is not None:
                if m[1] != 3:
                    out.append(Value(species, oid, fid, 0, m[4], m[1], dim, role, _writer_mod(f, m)))
                continue
            sh = sheets.get(slkname)
            v = _base_value(sh, orig, column)
            if v is None:
                continue
            out.append(Value(species, oid, fid, 0, v, typ, dim, role,
                             _inherit(sh, f, oid, orig, fid, typ, 0, 0, column)))


def _gather_abilities(f, sheets, out, stats):
    sh = sheets.get('AbilityData')
    ids = set(sh.rows if sh else ()) | set(f.index)
    by_code = {}
    for fid, (_dim, _data, _typ, codes) in ABILITY_FIELDS.items():
        for c in codes or (None,):
            by_code.setdefault(c, []).append(fid)
    for oid in sorted(ids):
        ob = f.index.get(oid)
        orig = ob[1] if ob is not None else oid
        code = (sh.get(orig, 'code') if sh else None) or orig
        mods = f.mods(ob) if ob is not None else {}
        lv = mods.get(('alev', 0))
        levels = int(lv[4]) if lv is not None and lv[1] == 0 else int(_base_value(sh, orig, 'levels') or 1)
        levels = max(1, min(levels, 10000))
        for fid in by_code.get(code, []) + by_code.get(None, []):
            dim, data, typ, _codes = ABILITY_FIELDS[fid]
            column = ('Data%s' % chr(64 + data)) if data else 'Cost'
            role = BONUS_ROLE.get(fid)
            for level in range(1, levels + 1):
                m = mods.get((fid, level))
                if m is not None:
                    if m[1] != 3:
                        out.append(Value('ability', oid, fid, level, m[4], m[1], dim, role, _writer_mod(f, m)))
                    continue
                col = '%s%d' % (column, level)
                v = _base_value(sh, orig, col)
                if v is None:
                    if sh is not None and orig in sh.rows and col not in sh.columns:
                        stats['levels_without_base'] = stats.get('levels_without_base', 0) + 1
                    continue
                out.append(Value('ability', oid, fid, level, v, typ, dim, role,
                                 _inherit(sh, f, oid, orig, fid, typ, level, data, col)))


def _gather_upgrades(f, sheets, out):
    sh = sheets.get('UpgradeData')
    ids = set(sh.rows if sh else ()) | set(f.index)
    for oid in sorted(ids):
        ob = f.index.get(oid)
        orig = ob[1] if ob is not None else oid
        mods = f.mods(ob) if ob is not None else {}
        for i in '1234':
            m = mods.get(('gef' + i, 0))
            effect = m[4].decode('latin-1', 'replace') if m is not None and m[1] == 3 else \
                ((sh.get(orig, 'effect' + i) if sh else None) or '')
            dim = UPGRADE_EFFECTS.get(effect.strip())
            if not dim:
                continue
            for fid, column in (('gba' + i, 'base' + i), ('gmo' + i, 'mod' + i)):
                m = mods.get((fid, 0))
                if m is not None:
                    if m[1] != 3:
                        out.append(Value('upgrade', oid, fid, 0, m[4], m[1], dim, None, _writer_mod(f, m)))
                    continue
                v = _base_value(sh, orig, column)
                if v is None:
                    continue
                out.append(Value('upgrade', oid, fid, 0, v, 2, dim, None,
                                 _inherit(sh, f, oid, orig, fid, 2, 0, 0, column)))


def _misc(work):
    raw, dst = work.find('war3mapMisc.txt')
    vals = dict(MISC_DEFAULT)
    text = raw.decode('utf-8', 'surrogateescape') if raw else None
    if text:
        sec = None
        for line in text.split('\n'):
            s = line.strip()
            m = re.match(r'^\[(.+)\]$', s)
            if m:
                sec = m.group(1).strip().lower()
                continue
            if sec == 'misc' and '=' in s and not s.startswith('//'):
                k, v = s.split('=', 1)
                n = _num(v)
                if n is not None:
                    vals[k.strip()] = n
    return text, dst, vals


def stacks(values, misc):
    unit = {}
    top = dict((d, 0.0) for d in DIMENSIONS)
    bonus = {}
    for v in values:
        if v.dim:
            d = 'combat' if v.dim == 'sides' else v.dim
            top[d] = max(top[d], abs(float(v.value)))
        if v.species == 'unit':
            unit.setdefault(v.oid, {})[v.field] = float(v.value)
        elif v.role:
            bonus[v.role] = max(bonus.get(v.role, 0.0), float(v.value))
    levels = max(1.0, misc.get('MaxHeroLevel', 10.0))
    hp = mana = damage = armor = attr = 0.0
    for u in unit.values():
        hp = max(hp, u.get('uhpm', 0.0))
        mana = max(mana, u.get('umpm', 0.0))
        for i in '12':
            damage = max(damage, u.get('ua%sb' % i, 0.0) + u.get('ua%sd' % i, 0.0) * u.get('ua%ss' % i, 0.0))
        armor = max(armor, u.get('udef', 0.0))
        for a, p in (('ustr', 'ustp'), ('uagi', 'uagp'), ('uint', 'uinp')):
            attr = max(attr, u.get(a, 0.0) + max(0.0, u.get(p, 0.0)) * (levels - 1))
    s = ITEM_SLOTS
    a_stack = attr + s * bonus.get('attr_bonus', 0.0)
    parts = {
        'life': hp + s * bonus.get('hp_bonus', 0.0) + a_stack * max(0.0, misc['StrHitPointBonus']),
        'mana': mana + s * bonus.get('mana_bonus', 0.0) + a_stack * max(0.0, misc['IntManaBonus']),
        'damage': damage + s * bonus.get('damage_bonus', 0.0) + a_stack * max(0.0, misc['StrAttackBonus']),
        'armor': armor + s * bonus.get('armor_bonus', 0.0) + a_stack * max(0.0, misc['AgiDefenseBonus']),
        'attribute': a_stack,
    }
    out = {'combat': max(parts['life'], parts['mana'], parts['damage'], top['combat']),
           'armor': max(parts['armor'], top['armor']),
           'attribute': max(parts['attribute'], top['attribute'])}
    return out, parts


WRAPPERS = {
    'GetUnitState': ('combat', False, 'takes unit u, unitstate s returns real',
                     '    if devo_i32_vital(s) then\n        return GetUnitState(u, s) * F\n    endif\n'
                     '    return GetUnitState(u, s)'),
    'SetUnitState': ('combat', False, 'takes unit u, unitstate s, real v returns nothing',
                     '    if devo_i32_vital(s) then\n        set v = devo_i32_down(v, F, s == UNIT_STATE_LIFE)\n'
                     '    endif\n    call SetUnitState(u, s, v)'),
    'GetWidgetLife': ('combat', False, 'takes widget w returns real', '    return GetWidgetLife(w) * F'),
    'SetWidgetLife': ('combat', False, 'takes widget w, real v returns nothing',
                      '    call SetWidgetLife(w, devo_i32_down(v, F, true))'),
    'GetDestructableLife': ('combat', False, 'takes destructable d returns real',
                            '    return GetDestructableLife(d) * F'),
    'SetDestructableLife': ('combat', False, 'takes destructable d, real v returns nothing',
                            '    call SetDestructableLife(d, devo_i32_down(v, F, true))'),
    'GetDestructableMaxLife': ('combat', False, 'takes destructable d returns real',
                               '    return GetDestructableMaxLife(d) * F'),
    'SetDestructableMaxLife': ('combat', False, 'takes destructable d, real v returns nothing',
                               '    call SetDestructableMaxLife(d, devo_i32_down(v, F, true))'),
    'DestructableRestoreLife': ('combat', False, 'takes destructable d, real v, boolean birth returns nothing',
                                '    call DestructableRestoreLife(d, devo_i32_down(v, F, true), birth)'),
    'GetEventDamage': ('combat', False, 'takes nothing returns real', '    return GetEventDamage() * F'),
    'BlzSetEventDamage': ('combat', False, 'takes real v returns nothing', '    call BlzSetEventDamage(v / F)'),
    'UnitDamageTarget': ('combat', False, 'takes unit u, widget t, real v, boolean a, boolean r, attacktype at, '
                         'damagetype dt, weapontype wt returns boolean',
                         '    return UnitDamageTarget(u, t, v / F, a, r, at, dt, wt)'),
    'UnitDamagePoint': ('combat', False, 'takes unit u, real delay, real radius, real x, real y, real v, boolean a, '
                        'boolean r, attacktype at, damagetype dt, weapontype wt returns boolean',
                        '    return UnitDamagePoint(u, delay, radius, x, y, v / F, a, r, at, dt, wt)'),
    'BlzGetUnitMaxHP': ('combat', False, 'takes unit u returns integer',
                        '    return devo_i32_int(I2R(BlzGetUnitMaxHP(u)) * F)'),
    'BlzSetUnitMaxHP': ('combat', False, 'takes unit u, integer v returns nothing',
                        '    call BlzSetUnitMaxHP(u, devo_i32_int(devo_i32_down(I2R(v), F, true)))'),
    'BlzGetUnitMaxMana': ('combat', False, 'takes unit u returns integer',
                          '    return devo_i32_int(I2R(BlzGetUnitMaxMana(u)) * F)'),
    'BlzSetUnitMaxMana': ('combat', False, 'takes unit u, integer v returns nothing',
                          '    call BlzSetUnitMaxMana(u, devo_i32_int(I2R(v) / F))'),
    'BlzGetUnitBaseDamage': ('combat', False, 'takes unit u, integer i returns integer',
                             '    return devo_i32_int(I2R(BlzGetUnitBaseDamage(u, i)) * F)'),
    'BlzSetUnitBaseDamage': ('combat', False, 'takes unit u, integer v, integer i returns nothing',
                             '    call BlzSetUnitBaseDamage(u, devo_i32_int(I2R(v) / F), i)'),
    'GetUnitStateSwap': ('combat', True, 'takes unitstate s, unit u returns real',
                         '    if devo_i32_vital(s) then\n        return GetUnitStateSwap(s, u) * F\n    endif\n'
                         '    return GetUnitStateSwap(s, u)'),
    'SetUnitLifeBJ': ('combat', True, 'takes unit u, real v returns nothing',
                      '    call SetUnitLifeBJ(u, devo_i32_down(v, F, true))'),
    'SetUnitManaBJ': ('combat', True, 'takes unit u, real v returns nothing', '    call SetUnitManaBJ(u, v / F)'),
    'UnitDamagePointLoc': ('combat', True, 'takes unit u, real delay, real radius, location l, real v, attacktype at, '
                           'damagetype dt returns boolean',
                           '    return UnitDamagePointLoc(u, delay, radius, l, v / F, at, dt)'),
    'UnitDamageTargetBJ': ('combat', True, 'takes unit u, unit t, real v, attacktype at, damagetype dt returns boolean',
                           '    return UnitDamageTargetBJ(u, t, v / F, at, dt)'),
    'SetDestructableMaxLifeBJ': ('combat', True, 'takes destructable d, real v returns nothing',
                                 '    call SetDestructableMaxLifeBJ(d, devo_i32_down(v, F, true))'),
    'BlzGetUnitArmor': ('armor', False, 'takes unit u returns real', '    return BlzGetUnitArmor(u) * F'),
    'BlzSetUnitArmor': ('armor', False, 'takes unit u, real v returns nothing', '    call BlzSetUnitArmor(u, v / F)'),
    'GetHeroStr': ('attribute', False, 'takes unit u, boolean b returns integer',
                   '    return devo_i32_int(I2R(GetHeroStr(u, b)) * F)'),
    'GetHeroAgi': ('attribute', False, 'takes unit u, boolean b returns integer',
                   '    return devo_i32_int(I2R(GetHeroAgi(u, b)) * F)'),
    'GetHeroInt': ('attribute', False, 'takes unit u, boolean b returns integer',
                   '    return devo_i32_int(I2R(GetHeroInt(u, b)) * F)'),
    'SetHeroStr': ('attribute', False, 'takes unit u, integer v, boolean p returns nothing',
                   '    call SetHeroStr(u, devo_i32_int(I2R(v) / F), p)'),
    'SetHeroAgi': ('attribute', False, 'takes unit u, integer v, boolean p returns nothing',
                   '    call SetHeroAgi(u, devo_i32_int(I2R(v) / F), p)'),
    'SetHeroInt': ('attribute', False, 'takes unit u, integer v, boolean p returns nothing',
                   '    call SetHeroInt(u, devo_i32_int(I2R(v) / F), p)'),
    'GetHeroStatBJ': ('attribute', True, 'takes integer w, unit u, boolean b returns integer',
                      '    return devo_i32_int(I2R(GetHeroStatBJ(w, u, b)) * F)'),
    'SetHeroStat': ('attribute', True, 'takes unit u, integer w, integer v returns nothing',
                    '    call SetHeroStat(u, w, devo_i32_int(I2R(v) / F))'),
    'ModifyHeroStat': ('attribute', True, 'takes integer w, unit u, integer m, integer v returns nothing',
                       '    call ModifyHeroStat(w, u, m, devo_i32_int(I2R(v) / F))'),
}
NOT_CONVERTED = ('BlzSetUnitRealField', 'BlzSetUnitIntegerField', 'BlzSetAbilityRealLevelField',
                 'BlzSetAbilityIntegerLevelField', 'BlzSetAbilityRealLevelArrayField',
                 'BlzSetAbilityIntegerLevelArrayField', 'BlzSetItemRealField', 'BlzSetItemIntegerField',
                 'EXSetAbilityDataReal', 'EXSetAbilityDataInteger', 'EXSetUnitInteger', 'EXSetUnitReal')
PREFIX = 'devo_i32_'
RX_SKIP = re.compile(r'"(?:[^"\\\n]|\\.)*"|//[^\n]*|\'[^\'\n]*\'')
HELPERS = '''// [Devo's Map Doctor] the map's numbers were scaled down to fit the integer limit (int32_balance.py): the script
// keeps its own numbers, these convert what crosses to the engine
function devo_i32_int takes real x returns integer
    if x >= 2147483000.0 then
        return 2147483647
    elseif x <= -2147483000.0 then
        return -2147483647
    elseif x >= 0.0 then
        return R2I(x + 0.5)
    endif
    return R2I(x - 0.5)
endfunction
function devo_i32_down takes real v, real f, boolean life returns real
    local real x = v / f
    if life and v >= 1.0 and x < 1.0 then
        return 1.0
    endif
    return x
endfunction
function devo_i32_vital takes unitstate s returns boolean
    return s == UNIT_STATE_LIFE or s == UNIT_STATE_MAX_LIFE or s == UNIT_STATE_MANA or s == UNIT_STATE_MAX_MANA
endfunction
'''


def _real(f):
    return '%d.0' % f if float(f) == int(f) else repr(float(f))


def _body(body, factor):
    return re.sub(r'(?<![\w.])F(?![\w(])', _real(factor), body)


def rewrite_script(text, factors):
    defined = set(re.findall(r'(?m)^\s*function\s+(\w+)\s+takes', text))
    names = [n for n, (dim, bj, _s, _b) in WRAPPERS.items()
             if factors.get(dim, 1) != 1 and not (bj and n in defined)]
    counts, other = {}, {}
    if not names:
        return text, counts, other
    rx = re.compile(r'\b(%s)(\s*\()' % '|'.join(sorted(names, key=len, reverse=True)))
    rx_other = re.compile(r'\b(%s)\s*\(' % '|'.join(NOT_CONVERTED))
    out, pos = [], 0

    def code(seg):
        for m in rx_other.finditer(seg):
            other[m.group(1)] = other.get(m.group(1), 0) + 1

        def sub(m):
            counts[m.group(1)] = counts.get(m.group(1), 0) + 1
            return PREFIX + m.group(1) + m.group(2)
        return rx.sub(sub, seg)
    for m in RX_SKIP.finditer(text):
        out.append(code(text[pos:m.start()]))
        out.append(m.group(0))
        pos = m.end()
    out.append(code(text[pos:]))
    new = ''.join(out)
    first = re.search(r'(?m)^function\s', new)
    if not counts or not first:
        return text, {}, other
    block = [HELPERS]
    for n in sorted(counts):
        dim, _bj, sig, body = WRAPPERS[n]
        block.append('function %s%s %s\n%s\nendfunction\n' % (PREFIX, n, sig, _body(body, factors[dim])))
    nl = '\r\n' if '\r\n' in new[:65536] else '\n'
    ins = ''.join(block).replace('\n', nl)
    return new[:first.start()] + ins + new[first.start():], counts, other


def _pjass_errors(path, root, tmp):
    import contextlib
    from doctor.script import pjass
    buf = io.StringIO()
    with contextlib.redirect_stdout(buf):
        try:
            rc = pjass.main(['--j=' + path], root=root, tmp=tmp)
        except SystemExit as e:
            rc = e.code if isinstance(e.code, int) else 1
    msgs = []
    for line in buf.getvalue().splitlines():
        m = re.search(r'\.j:\d+(?: \(de \d+\))?: (.+)$', line)
        if m and m.group(1) not in msgs:
            msgs.append(m.group(1))
    return rc, msgs


def apply(work, log=None):
    log = log or (lambda s: None)
    info = {'state': 'failed', 'factors': dict((d, 1) for d in DIMENSIONS), 'changed': {}, 'files': [], 'misc': [],
            'calls': {}, 'not_converted': {}, 'warnings': [], 'headroom': work.headroom}
    stats = {}
    sheets = _sheets(work, info['warnings'])
    files = {}
    values = []
    for species, (fname, _lv, _slks, _fields) in SPECIES.items():
        raw, dst = work.find(fname)
        try:
            f = ObjectFile(raw, fname, dst)
        except Exception as e:
            info['warnings'].append('%s could not be read (%s): its values were left as they are' % (fname, e))
            f = ObjectFile(None, fname, None)
        files[fname] = f
        if species == 'ability':
            _gather_abilities(f, sheets, values, stats)
        elif species == 'upgrade':
            _gather_upgrades(f, sheets, values)
        else:
            _gather_flat(species, f, sheets, values)
    misc_text, misc_dst, misc = _misc(work)
    st, parts = stacks(values, misc)
    factors = dict((d, factor_for(st[d], work.headroom)) for d in DIMENSIONS)
    largest = {}
    for v in values:
        if v.dim:
            d = 'combat' if v.dim == 'sides' else v.dim
            largest[d] = max(largest.get(d, 0.0), abs(float(v.value)))
    info.update(stacks=st, parts=parts, factors=factors, values=len(values), largest=largest)
    log('6. huge numbers: worst stack combat %.4g, armor %.4g, attribute %.4g -> factors %s'
        % (st['combat'], st['armor'], st['attribute'], ', '.join('%s %d' % (d, factors[d]) for d in DIMENSIONS)))
    if all(factors[d] == 1 for d in DIMENSIONS):
        info['state'] = 'nothing'
        return info
    if not work.write:
        info['state'] = 'measured'
        return info
    for v in values:
        if not v.dim or v.write is None:
            continue
        fac = factors['combat' if v.dim == 'sides' else v.dim]
        if fac == 1:
            continue
        new = scale_value(v.value, v.typ, fac, v.dim, stats)
        if new != v.value:
            v.write(new, v.typ)
            info['changed'][v.species] = info['changed'].get(v.species, 0) + 1
    misc_new = {}
    for key, (up, down) in MISC_RULE.items():
        old = misc.get(key, MISC_DEFAULT[key])
        new = old * (factors[up] if up else 1) / (factors[down] if down else 1)
        if old and abs(new - old) > 1e-12 * max(1.0, abs(old)):
            misc_new[key] = new
            info['misc'].append((key, old, new))
    writes = []
    if work.script:
        text = open(work.script, 'rb').read().decode('latin-1')
        new_text, calls, other = rewrite_script(text, factors)
        info['calls'], info['not_converted'] = calls, other
        if calls:
            tmp_dir = work.pjass_tmp or os.path.join(os.path.dirname(work.script), '_int32')
            os.makedirs(tmp_dir, exist_ok=True)
            trial = os.path.join(tmp_dir, 'war3map.j')
            with open(trial, 'wb') as fh:
                fh.write(new_text.encode('latin-1'))
            rc, msgs = _pjass_errors(trial, work.pjass_root, os.path.join(tmp_dir, 'pjass'))
            if rc:
                _rc0, msgs0 = _pjass_errors(work.script, work.pjass_root, os.path.join(tmp_dir, 'pjass0'))
                novos = sorted(set(msgs) - set(msgs0))
                if not _rc0 or novos:
                    info['warnings'].append('the huge numbers were NOT balanced: the script with the conversions did '
                                            'not pass the compiler check (%s)' % '; '.join(novos[:3] or msgs[:3]))
                    info['state'] = 'failed'
                    return info
            info['script_checked'] = True
            writes.append((work.script, new_text.encode('latin-1'), True))
    for sh in sheets.values():
        if sh.path and sh.changed:
            writes.append((sh.path, sh.to_bytes(), False))
    for f in files.values():
        if f.changed and f.path:
            writes.append((f.path, f.to_bytes(), False))
    if misc_new and misc_dst:
        writes.append((misc_dst, _misc_text(misc_text, misc_new).encode('utf-8', 'surrogateescape'), False))
    for path, data, is_script in writes:
        if is_script:
            keep = os.path.splitext(path)[0] + '_before_int32.j'
            if not os.path.exists(keep):
                os.replace(path, keep)
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, 'wb') as fh:
            fh.write(data)
        info['files'].append(os.path.basename(path) if is_script or not work.data_dir else
                             os.path.relpath(path, work.data_dir))
    info.update(rounded_to_one=stats.get('rounded_to_one', 0), imprecise=stats.get('imprecise', 0),
                levels_without_base=stats.get('levels_without_base', 0), state='scaled')
    log('6. huge numbers: %d value(s) scaled, %d script call(s) converted'
        % (sum(info['changed'].values()), sum(info['calls'].values())))
    return info


def _misc_text(text, new):
    from doctor.data import objects
    lines = text.split('\n') if text else []
    done = set()
    sec = None
    last_misc = None
    for i, line in enumerate(lines):
        s = line.strip()
        m = re.match(r'^\[(.+)\]$', s)
        if m:
            sec = m.group(1).strip().lower()
            if sec == 'misc':
                last_misc = i
            continue
        if sec == 'misc':
            if s:
                last_misc = i
            if '=' in s and not s.startswith('//'):
                k = s.split('=', 1)[0].strip()
                if k in new:
                    cr = '\r' if line.endswith('\r') else ''
                    lines[i] = '%s=%s%s' % (k, objects.short_real(new[k]), cr)
                    done.add(k)
    cr = '\r' if any(line.endswith('\r') for line in lines) else ''
    add = ['%s=%s%s' % (k, objects.short_real(new[k]), cr) for k in sorted(new) if k not in done]
    if add:
        if last_misc is None:
            if lines and lines[-1] == '':
                lines.pop()
            lines += ['[Misc]' + cr] + add + ['']
        else:
            lines[last_misc + 1:last_misc + 1] = add
    return '\n'.join(lines)


def port_step(r, extract, log=None, headroom=HEADROOM):
    work = Work(r.DATA, [os.path.join(r.ROOT, 'port', 'out', 'extract_en'), extract], base='auto',
                script=os.path.join(r.OUT, 'war3map.j'), headroom=headroom, pjass_root=r.ROOT,
                pjass_tmp=os.path.join(r.OUT, '_int32'))
    try:
        return apply(work, log)
    except Exception as e:
        return {'state': 'failed', 'factors': dict((d, 1) for d in DIMENSIONS),
                'warnings': ['the huge numbers were NOT balanced: %s: %s' % (type(e).__name__, e)]}


def _n(x):
    return '{:,.0f}'.format(x) if abs(x) >= 1 else '%g' % x


def report_lines(info):
    L = ['Huge numbers (scaled to fit the integer limit, 2,147,483,647)', '-' * 30]
    f = info.get('factors') or {}
    st = info.get('stacks') or {}
    state = info.get('state')
    if state == 'failed':
        return L + ['- not done: ' + ((info.get('warnings') or ['see the warnings'])[-1])]
    if state == 'nothing':
        return L + ['- nothing to do: the largest stack of life, damage and mana (%s), of armor (%s) and of '
                    'attributes (%s) fits with the margin'
                    % (_n(st.get('combat', 0)), _n(st.get('armor', 0)), _n(st.get('attribute', 0)))]
    names = {'combat': 'life, mana, damage, healing', 'armor': 'armor', 'attribute': 'strength, agility, intelligence'}
    for d in DIMENSIONS:
        if f.get(d, 1) != 1:
            L.append('- %s: divided by %s (the largest stack, %s, becomes %s)'
                     % (names[d], _n(f[d]), _n(st.get(d, 0)), _n(st.get(d, 0) / f[d])))
        else:
            L.append('- %s: unchanged (the largest stack, %s, fits)' % (names[d], _n(st.get(d, 0))))
    ch = info.get('changed') or {}
    if ch:
        L.append('- values changed: %s' % ', '.join('%s %d' % (k, ch[k]) for k in sorted(ch)))
    for k, old, new in info.get('misc') or []:
        L.append('- gameplay constant %s: %s -> %s' % (k, '%g' % old, '%g' % new))
    calls = info.get('calls') or {}
    if calls:
        L.append('- script: %d call(s) converted, so the script keeps its own numbers (%s)'
                 % (sum(calls.values()), ', '.join('%s %d' % (k, calls[k]) for k in sorted(calls)[:12])))
    other = info.get('not_converted') or {}
    if other:
        L.append('- script: %d call(s) that write object fields at run time are NOT converted (%s): check those '
                 'values in game' % (sum(other.values()), ', '.join('%s %d' % (k, other[k]) for k in sorted(other))))
    if info.get('rounded_to_one'):
        L.append('- %d small whole value(s) became 1 instead of 0 (the precision lost by the division)'
                 % info['rounded_to_one'])
    L.append('- the numbers written in tooltips and names were not changed')
    return L

