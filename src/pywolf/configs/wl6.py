'''
@author: Andrea Zoppi
'''

from ..graphics import rgbpalette_flatten


SAMPLED_SOUNDS_FREQUENCY = 7042


SOUNDS_PARTITIONS_MAP = {
    'buzzer':   (  0,  87),
    'adlib':    ( 87,  87),
    'digital':  (174,  87),
    'music':    (261,  27),
}


GRAPHICS_PARTITIONS_MAP = {
    'struct':   (  0,   1),
    'font':     (  1,   2),
    'fontm':    (  3,   0),
    'pics':     (  3, 132),
    'picm':     (135,   0),
    'sprites':  (135,   0),
    'tile8':    (135,  72),
    'tile8m':   (136,   0),
    'tile16':   (136,   0),
    'tile16m':  (136,   0),
    'tile32':   (136,   0),
    'tile32m':  (136,   0),
    'externs':  (136,  13),
}

GRAPHICS_PALETTE = (
    (0x00, 0x00, 0x00),  # 0x00
    (0x00, 0x00, 0xA8),  # 0x01
    (0x00, 0xA8, 0x00),  # 0x02
    (0x00, 0xA8, 0xA8),  # 0x03
    (0xA8, 0x00, 0x00),  # 0x04
    (0xA8, 0x00, 0xA8),  # 0x05
    (0xA8, 0x54, 0x00),  # 0x06
    (0xA8, 0xA8, 0xA8),  # 0x07
    (0x54, 0x54, 0x54),  # 0x08
    (0x54, 0x54, 0xFC),  # 0x09
    (0x54, 0xFC, 0x54),  # 0x0A
    (0x54, 0xFC, 0xFC),  # 0x0B
    (0xFC, 0x54, 0x54),  # 0x0C
    (0xFC, 0x54, 0xFC),  # 0x0D
    (0xFC, 0xFC, 0x54),  # 0x0E
    (0xFC, 0xFC, 0xFC),  # 0x0F

    (0xEC, 0xEC, 0xEC),  # 0x10
    (0xDC, 0xDC, 0xDC),  # 0x11
    (0xD0, 0xD0, 0xD0),  # 0x12
    (0xC0, 0xC0, 0xC0),  # 0x13
    (0xB4, 0xB4, 0xB4),  # 0x14
    (0xA8, 0xA8, 0xA8),  # 0x15
    (0x98, 0x98, 0x98),  # 0x16
    (0x8C, 0x8C, 0x8C),  # 0x17
    (0x7C, 0x7C, 0x7C),  # 0x18
    (0x70, 0x70, 0x70),  # 0x19
    (0x64, 0x64, 0x64),  # 0x1A
    (0x54, 0x54, 0x54),  # 0x1B
    (0x48, 0x48, 0x48),  # 0x1C
    (0x38, 0x38, 0x38),  # 0x1D
    (0x2C, 0x2C, 0x2C),  # 0x1E
    (0x20, 0x20, 0x20),  # 0x1F

    (0xFC, 0x00, 0x00),  # 0x20
    (0xEC, 0x00, 0x00),  # 0x21
    (0xE0, 0x00, 0x00),  # 0x22
    (0xD4, 0x00, 0x00),  # 0x23
    (0xC8, 0x00, 0x00),  # 0x24
    (0xBC, 0x00, 0x00),  # 0x25
    (0xB0, 0x00, 0x00),  # 0x26
    (0xA4, 0x00, 0x00),  # 0x27
    (0x98, 0x00, 0x00),  # 0x28
    (0x88, 0x00, 0x00),  # 0x29
    (0x7C, 0x00, 0x00),  # 0x2A
    (0x70, 0x00, 0x00),  # 0x2B
    (0x64, 0x00, 0x00),  # 0x2C
    (0x58, 0x00, 0x00),  # 0x2D
    (0x4C, 0x00, 0x00),  # 0x2E
    (0x40, 0x00, 0x00),  # 0x2F

    (0xFC, 0xD8, 0xD8),  # 0x30
    (0xFC, 0xB8, 0xB8),  # 0x31
    (0xFC, 0x9C, 0x9C),  # 0x32
    (0xFC, 0x7C, 0x7C),  # 0x33
    (0xFC, 0x5C, 0x5C),  # 0x34
    (0xFC, 0x40, 0x40),  # 0x35
    (0xFC, 0x20, 0x20),  # 0x36
    (0xFC, 0x00, 0x00),  # 0x37
    (0xFC, 0xA8, 0x5C),  # 0x38
    (0xFC, 0x98, 0x40),  # 0x39
    (0xFC, 0x88, 0x20),  # 0x3A
    (0xFC, 0x78, 0x00),  # 0x3B
    (0xE4, 0x6C, 0x00),  # 0x3C
    (0xCC, 0x60, 0x00),  # 0x3D
    (0xB4, 0x54, 0x00),  # 0x3E
    (0x9C, 0x4C, 0x00),  # 0x3F

    (0xFC, 0xFC, 0xD8),  # 0x40
    (0xFC, 0xFC, 0xB8),  # 0x41
    (0xFC, 0xFC, 0x9C),  # 0x42
    (0xFC, 0xFC, 0x7C),  # 0x43
    (0xFC, 0xF8, 0x5C),  # 0x44
    (0xFC, 0xF4, 0x40),  # 0x45
    (0xFC, 0xF4, 0x20),  # 0x46
    (0xFC, 0xF4, 0x00),  # 0x47
    (0xE4, 0xD8, 0x00),  # 0x48
    (0xCC, 0xC4, 0x00),  # 0x49
    (0xB4, 0xAC, 0x00),  # 0x4A
    (0x9C, 0x9C, 0x00),  # 0x4B
    (0x84, 0x84, 0x00),  # 0x4C
    (0x70, 0x6C, 0x00),  # 0x4D
    (0x58, 0x54, 0x00),  # 0x4E
    (0x40, 0x40, 0x00),  # 0x4F

    (0xD0, 0xFC, 0x5C),  # 0x50
    (0xC4, 0xFC, 0x40),  # 0x51
    (0xB4, 0xFC, 0x20),  # 0x52
    (0xA0, 0xFC, 0x00),  # 0x53
    (0x90, 0xE4, 0x00),  # 0x54
    (0x80, 0xCC, 0x00),  # 0x55
    (0x74, 0xB4, 0x00),  # 0x56
    (0x60, 0x9C, 0x00),  # 0x57
    (0xD8, 0xFC, 0xD8),  # 0x58
    (0xBC, 0xFC, 0xB8),  # 0x59
    (0x9C, 0xFC, 0x9C),  # 0x5A
    (0x80, 0xFC, 0x7C),  # 0x5B
    (0x60, 0xFC, 0x5C),  # 0x5C
    (0x40, 0xFC, 0x40),  # 0x5D
    (0x20, 0xFC, 0x20),  # 0x5E
    (0x00, 0xFC, 0x00),  # 0x5F

    (0x00, 0xFC, 0x00),  # 0x60
    (0x00, 0xEC, 0x00),  # 0x61
    (0x00, 0xE0, 0x00),  # 0x62
    (0x00, 0xD4, 0x00),  # 0x63
    (0x04, 0xC8, 0x00),  # 0x64
    (0x04, 0xBC, 0x00),  # 0x65
    (0x04, 0xB0, 0x00),  # 0x66
    (0x04, 0xA4, 0x00),  # 0x67
    (0x04, 0x98, 0x00),  # 0x68
    (0x04, 0x88, 0x00),  # 0x69
    (0x04, 0x7C, 0x00),  # 0x6A
    (0x04, 0x70, 0x00),  # 0x6B
    (0x04, 0x64, 0x00),  # 0x6C
    (0x04, 0x58, 0x00),  # 0x6D
    (0x04, 0x4C, 0x00),  # 0x6E
    (0x04, 0x40, 0x00),  # 0x6F

    (0xD8, 0xFC, 0xFC),  # 0x70
    (0xB8, 0xFC, 0xFC),  # 0x71
    (0x9C, 0xFC, 0xFC),  # 0x72
    (0x7C, 0xFC, 0xF8),  # 0x73
    (0x5C, 0xFC, 0xFC),  # 0x74
    (0x40, 0xFC, 0xFC),  # 0x75
    (0x20, 0xFC, 0xFC),  # 0x76
    (0x00, 0xFC, 0xFC),  # 0x77
    (0x00, 0xE4, 0xE4),  # 0x78
    (0x00, 0xCC, 0xCC),  # 0x79
    (0x00, 0xB4, 0xB4),  # 0x7A
    (0x00, 0x9C, 0x9C),  # 0x7B
    (0x00, 0x84, 0x84),  # 0x7C
    (0x00, 0x70, 0x70),  # 0x7D
    (0x00, 0x58, 0x58),  # 0x7E
    (0x00, 0x40, 0x40),  # 0x7F

    (0x5C, 0xBC, 0xFC),  # 0x80
    (0x40, 0xB0, 0xFC),  # 0x81
    (0x20, 0xA8, 0xFC),  # 0x82
    (0x00, 0x9C, 0xFC),  # 0x83
    (0x00, 0x8C, 0xE4),  # 0x84
    (0x00, 0x7C, 0xCC),  # 0x85
    (0x00, 0x6C, 0xB4),  # 0x86
    (0x00, 0x5C, 0x9C),  # 0x87
    (0xD8, 0xD8, 0xFC),  # 0x88
    (0xB8, 0xBC, 0xFC),  # 0x89
    (0x9C, 0x9C, 0xFC),  # 0x8A
    (0x7C, 0x80, 0xFC),  # 0x8B
    (0x5C, 0x60, 0xFC),  # 0x8C
    (0x40, 0x40, 0xFC),  # 0x8D
    (0x20, 0x24, 0xFC),  # 0x8E
    (0x00, 0x04, 0xFC),  # 0x8F

    (0x00, 0x00, 0xFC),  # 0x90
    (0x00, 0x00, 0xEC),  # 0x91
    (0x00, 0x00, 0xE0),  # 0x92
    (0x00, 0x00, 0xD4),  # 0x93
    (0x00, 0x00, 0xC8),  # 0x94
    (0x00, 0x00, 0xBC),  # 0x95
    (0x00, 0x00, 0xB0),  # 0x96
    (0x00, 0x00, 0xA4),  # 0x97
    (0x00, 0x00, 0x98),  # 0x98
    (0x00, 0x00, 0x88),  # 0x99
    (0x00, 0x00, 0x7C),  # 0x9A
    (0x00, 0x00, 0x70),  # 0x9B
    (0x00, 0x00, 0x64),  # 0x9C
    (0x00, 0x00, 0x58),  # 0x9D
    (0x00, 0x00, 0x4C),  # 0x9E
    (0x00, 0x00, 0x40),  # 0x9F

    (0x28, 0x28, 0x28),  # 0xA0
    (0xFC, 0xE0, 0x34),  # 0xA1
    (0xFC, 0xD4, 0x24),  # 0xA2
    (0xFC, 0xCC, 0x18),  # 0xA3
    (0xFC, 0xC0, 0x08),  # 0xA4
    (0xFC, 0xB4, 0x00),  # 0xA5
    (0xB4, 0x20, 0xFC),  # 0xA6
    (0xA8, 0x00, 0xFC),  # 0xA7
    (0x98, 0x00, 0xE4),  # 0xA8
    (0x80, 0x00, 0xCC),  # 0xA9
    (0x74, 0x00, 0xB4),  # 0xAA
    (0x60, 0x00, 0x9C),  # 0xAB
    (0x50, 0x00, 0x84),  # 0xAC
    (0x44, 0x00, 0x70),  # 0xAD
    (0x34, 0x00, 0x58),  # 0xAE
    (0x28, 0x00, 0x40),  # 0xAF

    (0xFC, 0xD8, 0xFC),  # 0xB0
    (0xFC, 0xB8, 0xFC),  # 0xB1
    (0xFC, 0x9C, 0xFC),  # 0xB2
    (0xFC, 0x7C, 0xFC),  # 0xB3
    (0xFC, 0x5C, 0xFC),  # 0xB4
    (0xFC, 0x40, 0xFC),  # 0xB5
    (0xFC, 0x20, 0xFC),  # 0xB6
    (0xFC, 0x00, 0xFC),  # 0xB7
    (0xE0, 0x00, 0xE4),  # 0xB8
    (0xC8, 0x00, 0xCC),  # 0xB9
    (0xB4, 0x00, 0xB4),  # 0xBA
    (0x9C, 0x00, 0x9C),  # 0xBB
    (0x84, 0x00, 0x84),  # 0xBC
    (0x6C, 0x00, 0x70),  # 0xBD
    (0x58, 0x00, 0x58),  # 0xBE
    (0x40, 0x00, 0x40),  # 0xBF

    (0xFC, 0xE8, 0xDC),  # 0xC0
    (0xFC, 0xE0, 0xD0),  # 0xC1
    (0xFC, 0xD8, 0xC4),  # 0xC2
    (0xFC, 0xD4, 0xBC),  # 0xC3
    (0xFC, 0xCC, 0xB0),  # 0xC4
    (0xFC, 0xC4, 0xA4),  # 0xC5
    (0xFC, 0xBC, 0x9C),  # 0xC6
    (0xFC, 0xB8, 0x90),  # 0xC7
    (0xFC, 0xB0, 0x80),  # 0xC8
    (0xFC, 0xA4, 0x70),  # 0xC9
    (0xFC, 0x9C, 0x60),  # 0xCA
    (0xF0, 0x94, 0x5C),  # 0xCB
    (0xE8, 0x8C, 0x58),  # 0xCC
    (0xDC, 0x88, 0x54),  # 0xCD
    (0xD0, 0x80, 0x50),  # 0xCE
    (0xC8, 0x7C, 0x4C),  # 0xCF

    (0xBC, 0x78, 0x48),  # 0xD0
    (0xB4, 0x70, 0x44),  # 0xD1
    (0xA8, 0x68, 0x40),  # 0xD2
    (0xA0, 0x64, 0x3C),  # 0xD3
    (0x9C, 0x60, 0x38),  # 0xD4
    (0x90, 0x5C, 0x34),  # 0xD5
    (0x88, 0x58, 0x30),  # 0xD6
    (0x80, 0x50, 0x2C),  # 0xD7
    (0x74, 0x4C, 0x28),  # 0xD8
    (0x6C, 0x48, 0x24),  # 0xD9
    (0x5C, 0x40, 0x20),  # 0xDA
    (0x54, 0x3C, 0x1C),  # 0xDB
    (0x48, 0x38, 0x18),  # 0xDC
    (0x40, 0x30, 0x18),  # 0xDD
    (0x38, 0x2C, 0x14),  # 0xDE
    (0x28, 0x20, 0x0C),  # 0xDF

    (0x60, 0x00, 0x64),  # 0xE0
    (0x00, 0x64, 0x64),  # 0xE1
    (0x00, 0x60, 0x60),  # 0xE2
    (0x00, 0x00, 0x1C),  # 0xE3
    (0x00, 0x00, 0x2C),  # 0xE4
    (0x30, 0x24, 0x10),  # 0xE5
    (0x48, 0x00, 0x48),  # 0xE6
    (0x50, 0x00, 0x50),  # 0xE7
    (0x00, 0x00, 0x34),  # 0xE8
    (0x1C, 0x1C, 0x1C),  # 0xE9
    (0x4C, 0x4C, 0x4C),  # 0xEA
    (0x5C, 0x5C, 0x5C),  # 0xEB
    (0x40, 0x40, 0x40),  # 0xEC
    (0x30, 0x30, 0x30),  # 0xED
    (0x34, 0x34, 0x34),  # 0xEE
    (0xD8, 0xF4, 0xF4),  # 0xEF

    (0xB8, 0xE8, 0xE8),  # 0xF0
    (0x9C, 0xDC, 0xDC),  # 0xF1
    (0x74, 0xC8, 0xC8),  # 0xF2
    (0x48, 0xC0, 0xC0),  # 0xF3
    (0x20, 0xB4, 0xB4),  # 0xF4
    (0x20, 0xB0, 0xB0),  # 0xF5
    (0x00, 0xA4, 0xA4),  # 0xF6
    (0x00, 0x98, 0x98),  # 0xF7
    (0x00, 0x8C, 0x8C),  # 0xF8
    (0x00, 0x84, 0x84),  # 0xF9
    (0x00, 0x7C, 0x7C),  # 0xFA
    (0x00, 0x78, 0x78),  # 0xFB
    (0x00, 0x74, 0x74),  # 0xFC
    (0x00, 0x70, 0x70),  # 0xFD
    (0x00, 0x6C, 0x6C),  # 0xFE
    (0x98, 0x00, 0x88),  # 0xFF
)

GRAPHICS_PALETTE_MAP = {
    ...: rgbpalette_flatten(GRAPHICS_PALETTE)
}

TEXTURE_DIMENSIONS = (64, 64)

TEXTURE_NAMES = (  # index // 2
    'grey_brick_1',
    'grey_brick_2',
    'grey_brick__flag',
    'grey_brick__hitler',
    'cell',
    'grey_brick__eagle',
    'cell__skeleton',
    'blue_brick_1',
    'blue_brick_2',
    'wood__eagle',
    'wood__hitler',
    'wood',
    'entrance_to_level',
    'steel__sign',
    'steel',
    'landscape',
    'red_brick',
    'red_brick__swastika',
    'purple',
    'red_brick__flag',
    'elevator',
    'fake_elevator',
    'wood__iron_cross',
    'dirty_brick_1',
    'purple__blood',
    'dirty_brick_2',
    'grey_brick_3',
    'grey_brick__sign',
    'brown_weave',
    'brown_weave__blood_2',
    'brown_weave__blood_3',
    'brown_weave__blood_1',
    'stained_glass',
    'blue_wall__skull',
    'grey_wall_1',
    'blue_wall__swastika',
    'grey_wall__vent',
    'multicolor_brick',
    'grey_wall_2',
    'blue_wall',
    'blue_brick__sign',
    'brown_marble_1',
    'grey_wall__map',
    'brown_stone_1',
    'brown_stone_2',
    'brown_marble_2',
    'brown_marble__flag',
    'wood_panel',
    'grey_wall__hitler',
    'fake_door',
    'door_excavation__side_of_door',
    'fake_locked_door',
    'elevator_wall',
    'door_vertical',
    'door_horizontal',
    'door_vertical__gold_key',
    'door_horizontal__gold_key',
    'door_vertical__silver_key',
    'door_horizontal__silver_key',
    'elevator_door__normal',
    'elevator_door__horizontal',
)

SPRITE_DIMENSIONS = (64, 64)

SPRITE_NAMES = (
    'demo',
    'death_cam',
    'water_pool',
    'oil_drum',
    'table__chairs',
    'lamp',
    'chandelier',
    'hanging_skeleton',
    'dog_food',
    'pillar',
    'green_plant',
    'skeleton',
    'sink',
    'brown_plant',
    'vase',
    'table',
    'ceiling_light',
    'utensils_brown',
    'armor',
    'cage',
    'cage__skeleton',
    'bones',
    'gold_key',
    'silver_key',
    'bed',
    'basket',
    'food',
    'medkit',
    'ammo',
    'machinegun',
    'chaingun',
    'cross',
    'chalace',
    'jewels',
    'crown',
    'extra_life',
    'bones__blood',
    'barrel',
    'well__water',
    'well',
    'blood_pool',
    'flag',
    'bones_1',
    'bones_2',
    'bones_3',
    'bones_4',
    'utensils_blue',
    'stove',
    'rack',
    'vines',

    'guard__stand_d0',
    'guard__stand_d1',
    'guard__stand_d2',
    'guard__stand_d3',
    'guard__stand_d4',
    'guard__stand_d5',
    'guard__stand_d6',
    'guard__stand_d7',
    'guard__walk_a0_d0',
    'guard__walk_a0_d1',
    'guard__walk_a0_d2',
    'guard__walk_a0_d3',
    'guard__walk_a0_d4',
    'guard__walk_a0_d5',
    'guard__walk_a0_d6',
    'guard__walk_a0_d7',
    'guard__walk_a1_d0',
    'guard__walk_a1_d1',
    'guard__walk_a1_d2',
    'guard__walk_a1_d3',
    'guard__walk_a1_d4',
    'guard__walk_a1_d5',
    'guard__walk_a1_d6',
    'guard__walk_a1_d7',
    'guard__walk_a2_d0',
    'guard__walk_a2_d1',
    'guard__walk_a2_d2',
    'guard__walk_a2_d3',
    'guard__walk_a2_d4',
    'guard__walk_a2_d5',
    'guard__walk_a2_d6',
    'guard__walk_a2_d7',
    'guard__walk_a3_d0',
    'guard__walk_a3_d1',
    'guard__walk_a3_d2',
    'guard__walk_a3_d3',
    'guard__walk_a3_d4',
    'guard__walk_a3_d5',
    'guard__walk_a3_d6',
    'guard__walk_a3_d7',
    'guard__pain_c1',
    'guard__death_a0',
    'guard__death_a1',
    'guard__death_a2',
    'guard__pain_c2',
    'guard__dead',
    'guard__attack_a0',
    'guard__attack_a1',
    'guard__attack_a2',

    'dog__walk_a0_d0',
    'dog__walk_a0_d1',
    'dog__walk_a0_d2',
    'dog__walk_a0_d3',
    'dog__walk_a0_d4',
    'dog__walk_a0_d5',
    'dog__walk_a0_d6',
    'dog__walk_a0_d7',
    'dog__walk_a1_d0',
    'dog__walk_a1_d1',
    'dog__walk_a1_d2',
    'dog__walk_a1_d3',
    'dog__walk_a1_d4',
    'dog__walk_a1_d5',
    'dog__walk_a1_d6',
    'dog__walk_a1_d7',
    'dog__walk_a2_d0',
    'dog__walk_a2_d1',
    'dog__walk_a2_d2',
    'dog__walk_a2_d3',
    'dog__walk_a2_d4',
    'dog__walk_a2_d5',
    'dog__walk_a2_d6',
    'dog__walk_a2_d7',
    'dog__walk_a3_d0',
    'dog__walk_a3_d1',
    'dog__walk_a3_d2',
    'dog__walk_a3_d3',
    'dog__walk_a3_d4',
    'dog__walk_a3_d5',
    'dog__walk_a3_d6',
    'dog__walk_a3_d7',
    'dog__death_a0',
    'dog__death_a1',
    'dog__death_a2',
    'dog__dead',
    'dog__attack_a0',
    'dog__attack_a1',
    'dog__attack_a2',

    'ss__stand_d0',
    'ss__stand_d1',
    'ss__stand_d2',
    'ss__stand_d3',
    'ss__stand_d4',
    'ss__stand_d5',
    'ss__stand_d6',
    'ss__stand_d7',
    'ss__walk_a0_d0',
    'ss__walk_a0_d1',
    'ss__walk_a0_d2',
    'ss__walk_a0_d3',
    'ss__walk_a0_d4',
    'ss__walk_a0_d5',
    'ss__walk_a0_d6',
    'ss__walk_a0_d7',
    'ss__walk_a1_d0',
    'ss__walk_a1_d1',
    'ss__walk_a1_d2',
    'ss__walk_a1_d3',
    'ss__walk_a1_d4',
    'ss__walk_a1_d5',
    'ss__walk_a1_d6',
    'ss__walk_a1_d7',
    'ss__walk_a2_d0',
    'ss__walk_a2_d1',
    'ss__walk_a2_d2',
    'ss__walk_a2_d3',
    'ss__walk_a2_d4',
    'ss__walk_a2_d5',
    'ss__walk_a2_d6',
    'ss__walk_a2_d7',
    'ss__walk_a3_d0',
    'ss__walk_a3_d1',
    'ss__walk_a3_d2',
    'ss__walk_a3_d3',
    'ss__walk_a3_d4',
    'ss__walk_a3_d5',
    'ss__walk_a3_d6',
    'ss__walk_a3_d7',
    'ss__pain_c1',
    'ss__death_a0',
    'ss__death_a1',
    'ss__death_a2',
    'ss__pain_c2',
    'ss__dead',
    'ss__attack_a0',
    'ss__attack_a1',
    'ss__attack_a2',

    'mutant__stand_d0',
    'mutant__stand_d1',
    'mutant__stand_d2',
    'mutant__stand_d3',
    'mutant__stand_d4',
    'mutant__stand_d5',
    'mutant__stand_d6',
    'mutant__stand_d7',
    'mutant__walk_a0_d0',
    'mutant__walk_a0_d1',
    'mutant__walk_a0_d2',
    'mutant__walk_a0_d3',
    'mutant__walk_a0_d4',
    'mutant__walk_a0_d5',
    'mutant__walk_a0_d6',
    'mutant__walk_a0_d7',
    'mutant__walk_a1_d0',
    'mutant__walk_a1_d1',
    'mutant__walk_a1_d2',
    'mutant__walk_a1_d3',
    'mutant__walk_a1_d4',
    'mutant__walk_a1_d5',
    'mutant__walk_a1_d6',
    'mutant__walk_a1_d7',
    'mutant__walk_a2_d0',
    'mutant__walk_a2_d1',
    'mutant__walk_a2_d2',
    'mutant__walk_a2_d3',
    'mutant__walk_a2_d4',
    'mutant__walk_a2_d5',
    'mutant__walk_a2_d6',
    'mutant__walk_a2_d7',
    'mutant__walk_a3_d0',
    'mutant__walk_a3_d1',
    'mutant__walk_a3_d2',
    'mutant__walk_a3_d3',
    'mutant__walk_a3_d4',
    'mutant__walk_a3_d5',
    'mutant__walk_a3_d6',
    'mutant__walk_a3_d7',
    'mutant__pain_c1',
    'mutant__death_a0',
    'mutant__death_a1',
    'mutant__death_a2',
    'mutant__pain_c2',
    'mutant__death_3',
    'mutant__dead',
    'mutant__attack_a0',
    'mutant__attack_a1',
    'mutant__attack_a2',
    'mutant__attack_a3',

    'officer__stand_d0',
    'officer__stand_d1',
    'officer__stand_d2',
    'officer__stand_d3',
    'officer__stand_d4',
    'officer__stand_d5',
    'officer__stand_d6',
    'officer__stand_d7',
    'officer__walk_a0_d0',
    'officer__walk_a0_d1',
    'officer__walk_a0_d2',
    'officer__walk_a0_d3',
    'officer__walk_a0_d4',
    'officer__walk_a0_d5',
    'officer__walk_a0_d6',
    'officer__walk_a0_d7',
    'officer__walk_a1_d0',
    'officer__walk_a1_d1',
    'officer__walk_a1_d2',
    'officer__walk_a1_d3',
    'officer__walk_a1_d4',
    'officer__walk_a1_d5',
    'officer__walk_a1_d6',
    'officer__walk_a1_d7',
    'officer__walk_a2_d0',
    'officer__walk_a2_d1',
    'officer__walk_a2_d2',
    'officer__walk_a2_d3',
    'officer__walk_a2_d4',
    'officer__walk_a2_d5',
    'officer__walk_a2_d6',
    'officer__walk_a2_d7',
    'officer__walk_a3_d0',
    'officer__walk_a3_d1',
    'officer__walk_a3_d2',
    'officer__walk_a3_d3',
    'officer__walk_a3_d4',
    'officer__walk_a3_d5',
    'officer__walk_a3_d6',
    'officer__walk_a3_d7',
    'officer__pain_c1',
    'officer__death_a0',
    'officer__death_a1',
    'officer__death_a2',
    'officer__pain_c2',
    'officer__death_a3',
    'officer__dead',
    'officer__attack_a0',
    'officer__attack_a1',
    'officer__attack_a2',

    'ghost_blinky__walk_a0',
    'ghost_blinky__walk_a1',
    'ghost_pinky__walk_a0',
    'ghost_pinky__walk_a1',
    'ghost_clyde__walk_a0',
    'ghost_clyde__walk_a1',
    'ghost_inky__walk_a0',
    'ghost_inky__walk_a1',

    'hans__walk_a0',
    'hans__walk_a1',
    'hans__walk_a2',
    'hans__walk_a3',
    'hans__attack_a0',
    'hans__attack_a1',
    'hans__attack_a2',
    'hans__dead',
    'hans__death_a0',
    'hans__death_a1',
    'hans__death_a2',

    'schabbs__walk_a0',
    'schabbs__walk_a1',
    'schabbs__walk_a2',
    'schabbs__walk_a3',
    'schabbs__attack_a0',
    'schabbs__attack_a1',
    'schabbs__attack_a2',
    'schabbs__death_a0',
    'schabbs__death_a1',
    'schabbs__death_a2',
    'schabbs__dead',
    'needle__fly_a0',
    'needle__fly_a1',
    'needle__fly_a2',
    'needle__fly_a3',

    'robed_fake__walk_a0',
    'robed_fake__walk_a1',
    'robed_fake__walk_a2',
    'robed_fake__walk_a3',
    'robed_fake__attack_a0',
    'fire__fly_a0',
    'fire__fly_a1',
    'robed_fake__death_a0',
    'robed_fake__death_a1',
    'robed_fake__death_a2',
    'robed_fake__death_a3',
    'robed_fake__death_a4',
    'robed_fake__dead',

    'mecha_hitler__walk_a0',
    'mecha_hitler__walk_a1',
    'mecha_hitler__walk_a2',
    'mecha_hitler__walk_a3',
    'mecha_hitler__attack_a0',
    'mecha_hitler__attack_a1',
    'mecha_hitler__attack_a2',
    'mecha_hitler__dead',
    'mecha_hitler__death_a0',
    'mecha_hitler__death_a1',
    'mecha_hitler__death_a2',

    'hitler__walk_a0',
    'hitler__walk_a1',
    'hitler__walk_a2',
    'hitler__walk_a3',
    'hitler__attack_a0',
    'hitler__attack_a1',
    'hitler__attack_a2',
    'hitler__dead',
    'hitler__death_a0',
    'hitler__death_a1',
    'hitler__death_a2',
    'hitler__death_a3',
    'hitler__death_a4',
    'hitler__death_a5',
    'hitler__death_a6',

    'otto__walk_a0',
    'otto__walk_a1',
    'otto__walk_a2',
    'otto__walk_a3',
    'otto__attack_a0',
    'otto__attack_a1',
    'otto__death_a0',
    'otto__death_a1',
    'otto__death_a2',
    'otto__dead',
    'rocket__fly_d0',
    'rocket__fly_d1',
    'rocket__fly_d2',
    'rocket__fly_d3',
    'rocket__fly_d7',
    'rocket__fly_d6',
    'rocket__fly_d5',
    'rocket__fly_d4',
    'smoke__fly_a0',
    'smoke__fly_a1',
    'smoke__fly_a2',
    'smoke__fly_a3',
    'boom__fly_a0',
    'boom__fly_a1',
    'boom__fly_a2',

    'gretel__walk_a0',
    'gretel__walk_a1',
    'gretel__walk_a2',
    'gretel__walk_a3',
    'gretel__attack_a0',
    'gretel__attack_a1',
    'gretel__attack_a2',
    'gretel__dead',
    'gretel__death_a0',
    'gretel__death_a1',
    'gretel__death_a2',

    'fettgesicht__walk_a0',
    'fettgesicht__walk_a1',
    'fettgesicht__walk_a2',
    'fettgesicht__walk_a3',
    'fettgesicht__attack_a0',
    'fettgesicht__attack_a1',
    'fettgesicht__attack_a2',
    'fettgesicht__attack_a3',
    'fettgesicht__death_a0',
    'fettgesicht__death_a1',
    'fettgesicht__death_a2',
    'fettgesicht__dead',

    'bj__walk_a0',
    'bj__walk_a1',
    'bj__walk_a2',
    'bj__walk_a3',
    'bj__jump_a0',
    'bj__jump_a1',
    'bj__jump_a2',
    'bj__jump_a3',

    'knife__ready',
    'knife__attack_a0',
    'knife__attack_a1',
    'knife__attack_a2',
    'knife__attack_a3',

    'pistol__ready',
    'pistol__attack_a0',
    'pistol__attack_a1',
    'pistol__attack_a2',
    'pistol__attack_a3',

    'machinegun__ready',
    'machinegun__attack_a0',
    'machinegun__attack_a1',
    'machinegun__attack_a2',
    'machinegun__attack_a3',

    'chaingun__ready',
    'chaingun__attack_a0',
    'chaingun__attack_a1',
    'chaingun__attack_a2',
    'chaingun__attack_a3',
)


SAMPLED_SOUND_NAMES = (
    'guard__wake',
    'dog__wake',
    'door__close',
    'door__open',
    'machinegun__attack',
    'pistol__attack',
    'chaingun__attack',
    'ss__wake',
    'hans__wake',
    'hans__death',
    'boss_gun__attack',
    'ss__attack',
    'guard__death_1',
    'guard__death_2',
    'guard__death_3',
    'pushwall__move',
    'dog__death',
    'mutant__death',
    'hitler__wake',
    'hitler__death',
    'ss__death',
    'guard__attack',
    'blood__slurpie',
    'robed_fake__wake',
    'schabbs__death',
    'schabbs__wake',
    'robed_fake__death',
    'officer__wake',
    'officer__death',
    'dog__attack',
    'elevator__use',
    'mecha_hitler__step',
    'bj__yeah',
    'mecha_hitler__death',
    'guard__death_4',
    'guard__death_5',
    'otto__death',
    'otto__wake',
    'fettgesicht__wake',
    'secret__death',
    'guard__death_6',
    'guard__death_7',
    'guard__death_8',
    'gretel__wake',
    'gretel__death',
    'fettgesicht__death',
)

MUSIC_NAMES = (
    'Enemy Around the Corner',
    'Into the Dungeons',
    'The March to War',
    'Get Them Before They Get You',
    'Pounding Headache',
    'Hitler Waltz',
    'Kill the S.O.B.',
    'Horst-Wessel-Lied',
    'Nazi Anthem',
    'P.O.W.',
    'Salute',
    'Searching For the Enemy',
    'Suspense',
    'Victors',
    'Wondering About My Loved Ones',
    'Funk You!',
    'End of Level',
    'Going After Hitler',
    'Lurking...',
    'The Ultimate Challenge',
    'The Nazi Rap',
    'Zero Hour',
    'Twelfth Hour',
    'Roster',
    'U R A Hero',
    'Victory March',
    'Wolf Pac',
)

BUZZER_SOUND_NAMES = (  # TODO
    '',
)

ADLIB_SOUND_NAMES = BUZZER_SOUND_NAMES
