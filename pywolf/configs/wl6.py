def _rgbpalette_flatten(palette_colors):
    flat_palette = []
    for color in palette_colors:
        assert len(color) == 3
        flat_palette += color
    return flat_palette


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

    'externs':  (136,  13),  # includes the ones below
    'screens':  (136,   2),
    'helpart':  (138,   1),
    'demos':    (139,   4),
    'endart':   (143,   6),
}

GRAPHICS_PALETTE = [
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
]


GRAPHICS_PALETTE_MAP = {
    ...: _rgbpalette_flatten(GRAPHICS_PALETTE)
}

TILE8_NAMES = [str(i) for i in range(GRAPHICS_PARTITIONS_MAP['tile8'][1])]  # TODO

PICTURE_LABELS = [
    'H_BJPIC',
    'H_CASTLEPIC',
    'H_BLAZEPIC',
    'H_TOPWINDOWPIC',
    'H_LEFTWINDOWPIC',
    'H_RIGHTWINDOWPIC',
    'H_BOTTOMINFOPIC',

    'C_OPTIONSPIC',
    'C_CURSOR1PIC',
    'C_CURSOR2PIC',
    'C_NOTSELECTEDPIC',
    'C_SELECTEDPIC',
    'C_FXTITLEPIC',
    'C_DIGITITLEPIC',
    'C_MUSICTITLEPIC',
    'C_MOUSELBACKPIC',
    'C_BABYMODEPIC',
    'C_EASYPIC',
    'C_NORMALPIC',
    'C_HARDPIC',
    'C_LOADSAVEDISKPIC',
    'C_DISKLOADING1PIC',
    'C_DISKLOADING2PIC',
    'C_CONTROLPIC',
    'C_CUSTOMIZEPIC',
    'C_LOADGAMEPIC',
    'C_SAVEGAMEPIC',
    'C_EPISODE1PIC',
    'C_EPISODE2PIC',
    'C_EPISODE3PIC',
    'C_EPISODE4PIC',
    'C_EPISODE5PIC',
    'C_EPISODE6PIC',
    'C_CODEPIC',
    'C_TIMECODEPIC',
    'C_LEVELPIC',
    'C_NAMEPIC',
    'C_SCOREPIC',
    'C_JOY1PIC',
    'C_JOY2PIC',

    'L_GUYPIC',
    'L_COLONPIC',
    'L_NUM0PIC',
    'L_NUM1PIC',
    'L_NUM2PIC',
    'L_NUM3PIC',
    'L_NUM4PIC',
    'L_NUM5PIC',
    'L_NUM6PIC',
    'L_NUM7PIC',
    'L_NUM8PIC',
    'L_NUM9PIC',
    'L_PERCENTPIC',
    'L_APIC',
    'L_BPIC',
    'L_CPIC',
    'L_DPIC',
    'L_EPIC',
    'L_FPIC',
    'L_GPIC',
    'L_HPIC',
    'L_IPIC',
    'L_JPIC',
    'L_KPIC',
    'L_LPIC',
    'L_MPIC',
    'L_NPIC',
    'L_OPIC',
    'L_PPIC',
    'L_QPIC',
    'L_RPIC',
    'L_SPIC',
    'L_TPIC',
    'L_UPIC',
    'L_VPIC',
    'L_WPIC',
    'L_XPIC',
    'L_YPIC',
    'L_ZPIC',
    'L_EXPOINTPIC',
    'L_APOSTROPHEPIC',
    'L_GUY2PIC',
    'L_BJWINSPIC',
    'STATUSBARPIC',
    'TITLEPIC',
    'PG13PIC',
    'CREDITSPIC',
    'HIGHSCORESPIC',

    'KNIFEPIC',
    'GUNPIC',
    'MACHINEGUNPIC',
    'GATLINGGUNPIC',
    'NOKEYPIC',
    'GOLDKEYPIC',
    'SILVERKEYPIC',
    'N_BLANKPIC',
    'N_0PIC',
    'N_1PIC',
    'N_2PIC',
    'N_3PIC',
    'N_4PIC',
    'N_5PIC',
    'N_6PIC',
    'N_7PIC',
    'N_8PIC',
    'N_9PIC',
    'FACE1APIC',
    'FACE1BPIC',
    'FACE1CPIC',
    'FACE2APIC',
    'FACE2BPIC',
    'FACE2CPIC',
    'FACE3APIC',
    'FACE3BPIC',
    'FACE3CPIC',
    'FACE4APIC',
    'FACE4BPIC',
    'FACE4CPIC',
    'FACE5APIC',
    'FACE5BPIC',
    'FACE5CPIC',
    'FACE6APIC',
    'FACE6BPIC',
    'FACE6CPIC',
    'FACE7APIC',
    'FACE7BPIC',
    'FACE7CPIC',
    'FACE8APIC',
    'GOTGATLINGPIC',
    'MUTANTBJPIC',
    'PAUSEDPIC',
    'GETPSYCHEDPIC',
]

PICTURE_NAMES = PICTURE_LABELS  # TODO


TEXTURE_DIMENSIONS = (64, 64)

TEXTURE_NAMES = [  # index // 2
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
    'door_panel',
    'door_hinge',
    'door_elevator',
    'door_locked',
]


SPRITE_DIMENSIONS = (64, 64)

SPRITE_LABELS = [
    'SPR_DEMO',
    'SPR_DEATHCAM',
    'SPR_STAT_0',
    'SPR_STAT_1',
    'SPR_STAT_2',
    'SPR_STAT_3',
    'SPR_STAT_4',
    'SPR_STAT_5',
    'SPR_STAT_6',
    'SPR_STAT_7',
    'SPR_STAT_8',
    'SPR_STAT_9',
    'SPR_STAT_10',
    'SPR_STAT_11',
    'SPR_STAT_12',
    'SPR_STAT_13',
    'SPR_STAT_14',
    'SPR_STAT_15',
    'SPR_STAT_16',
    'SPR_STAT_17',
    'SPR_STAT_18',
    'SPR_STAT_19',
    'SPR_STAT_20',
    'SPR_STAT_21',
    'SPR_STAT_22',
    'SPR_STAT_23',
    'SPR_STAT_24',
    'SPR_STAT_25',
    'SPR_STAT_26',
    'SPR_STAT_27',
    'SPR_STAT_28',
    'SPR_STAT_29',
    'SPR_STAT_30',
    'SPR_STAT_31',
    'SPR_STAT_32',
    'SPR_STAT_33',
    'SPR_STAT_34',
    'SPR_STAT_35',
    'SPR_STAT_36',
    'SPR_STAT_37',
    'SPR_STAT_38',
    'SPR_STAT_39',
    'SPR_STAT_40',
    'SPR_STAT_41',
    'SPR_STAT_42',
    'SPR_STAT_43',
    'SPR_STAT_44',
    'SPR_STAT_45',
    'SPR_STAT_46',
    'SPR_STAT_47',

    'SPR_GRD_S_1',
    'SPR_GRD_S_2',
    'SPR_GRD_S_3',
    'SPR_GRD_S_4',
    'SPR_GRD_S_5',
    'SPR_GRD_S_6',
    'SPR_GRD_S_7',
    'SPR_GRD_S_8',
    'SPR_GRD_W1_1',
    'SPR_GRD_W1_2',
    'SPR_GRD_W1_3',
    'SPR_GRD_W1_4',
    'SPR_GRD_W1_5',
    'SPR_GRD_W1_6',
    'SPR_GRD_W1_7',
    'SPR_GRD_W1_8',
    'SPR_GRD_W2_1',
    'SPR_GRD_W2_2',
    'SPR_GRD_W2_3',
    'SPR_GRD_W2_4',
    'SPR_GRD_W2_5',
    'SPR_GRD_W2_6',
    'SPR_GRD_W2_7',
    'SPR_GRD_W2_8',
    'SPR_GRD_W3_1',
    'SPR_GRD_W3_2',
    'SPR_GRD_W3_3',
    'SPR_GRD_W3_4',
    'SPR_GRD_W3_5',
    'SPR_GRD_W3_6',
    'SPR_GRD_W3_7',
    'SPR_GRD_W3_8',
    'SPR_GRD_W4_1',
    'SPR_GRD_W4_2',
    'SPR_GRD_W4_3',
    'SPR_GRD_W4_4',
    'SPR_GRD_W4_5',
    'SPR_GRD_W4_6',
    'SPR_GRD_W4_7',
    'SPR_GRD_W4_8',
    'SPR_GRD_PAIN_1',
    'SPR_GRD_DIE_1',
    'SPR_GRD_DIE_2',
    'SPR_GRD_DIE_3',
    'SPR_GRD_PAIN_2',
    'SPR_GRD_DEAD',
    'SPR_GRD_SHOOT1',
    'SPR_GRD_SHOOT2',
    'SPR_GRD_SHOOT3',

    'SPR_DOG_W1_1',
    'SPR_DOG_W1_2',
    'SPR_DOG_W1_3',
    'SPR_DOG_W1_4',
    'SPR_DOG_W1_5',
    'SPR_DOG_W1_6',
    'SPR_DOG_W1_7',
    'SPR_DOG_W1_8',
    'SPR_DOG_W2_1',
    'SPR_DOG_W2_2',
    'SPR_DOG_W2_3',
    'SPR_DOG_W2_4',
    'SPR_DOG_W2_5',
    'SPR_DOG_W2_6',
    'SPR_DOG_W2_7',
    'SPR_DOG_W2_8',
    'SPR_DOG_W3_1',
    'SPR_DOG_W3_2',
    'SPR_DOG_W3_3',
    'SPR_DOG_W3_4',
    'SPR_DOG_W3_5',
    'SPR_DOG_W3_6',
    'SPR_DOG_W3_7',
    'SPR_DOG_W3_8',
    'SPR_DOG_W4_1',
    'SPR_DOG_W4_2',
    'SPR_DOG_W4_3',
    'SPR_DOG_W4_4',
    'SPR_DOG_W4_5',
    'SPR_DOG_W4_6',
    'SPR_DOG_W4_7',
    'SPR_DOG_W4_8',
    'SPR_DOG_DIE_1',
    'SPR_DOG_DIE_2',
    'SPR_DOG_DIE_3',
    'SPR_DOG_DEAD',
    'SPR_DOG_JUMP1',
    'SPR_DOG_JUMP2',
    'SPR_DOG_JUMP3',

    'SPR_SS_S_1',
    'SPR_SS_S_2',
    'SPR_SS_S_3',
    'SPR_SS_S_4',
    'SPR_SS_S_5',
    'SPR_SS_S_6',
    'SPR_SS_S_7',
    'SPR_SS_S_8',
    'SPR_SS_W1_1',
    'SPR_SS_W1_2',
    'SPR_SS_W1_3',
    'SPR_SS_W1_4',
    'SPR_SS_W1_5',
    'SPR_SS_W1_6',
    'SPR_SS_W1_7',
    'SPR_SS_W1_8',
    'SPR_SS_W2_1',
    'SPR_SS_W2_2',
    'SPR_SS_W2_3',
    'SPR_SS_W2_4',
    'SPR_SS_W2_5',
    'SPR_SS_W2_6',
    'SPR_SS_W2_7',
    'SPR_SS_W2_8',
    'SPR_SS_W3_1',
    'SPR_SS_W3_2',
    'SPR_SS_W3_3',
    'SPR_SS_W3_4',
    'SPR_SS_W3_5',
    'SPR_SS_W3_6',
    'SPR_SS_W3_7',
    'SPR_SS_W3_8',
    'SPR_SS_W4_1',
    'SPR_SS_W4_2',
    'SPR_SS_W4_3',
    'SPR_SS_W4_4',
    'SPR_SS_W4_5',
    'SPR_SS_W4_6',
    'SPR_SS_W4_7',
    'SPR_SS_W4_8',
    'SPR_SS_PAIN_1',
    'SPR_SS_DIE_1',
    'SPR_SS_DIE_2',
    'SPR_SS_DIE_3',
    'SPR_SS_PAIN_2',
    'SPR_SS_DEAD',
    'SPR_SS_SHOOT1',
    'SPR_SS_SHOOT2',
    'SPR_SS_SHOOT3',

    'SPR_MUT_S_1',
    'SPR_MUT_S_2',
    'SPR_MUT_S_3',
    'SPR_MUT_S_4',
    'SPR_MUT_S_5',
    'SPR_MUT_S_6',
    'SPR_MUT_S_7',
    'SPR_MUT_S_8',
    'SPR_MUT_W1_1',
    'SPR_MUT_W1_2',
    'SPR_MUT_W1_3',
    'SPR_MUT_W1_4',
    'SPR_MUT_W1_5',
    'SPR_MUT_W1_6',
    'SPR_MUT_W1_7',
    'SPR_MUT_W1_8',
    'SPR_MUT_W2_1',
    'SPR_MUT_W2_2',
    'SPR_MUT_W2_3',
    'SPR_MUT_W2_4',
    'SPR_MUT_W2_5',
    'SPR_MUT_W2_6',
    'SPR_MUT_W2_7',
    'SPR_MUT_W2_8',
    'SPR_MUT_W3_1',
    'SPR_MUT_W3_2',
    'SPR_MUT_W3_3',
    'SPR_MUT_W3_4',
    'SPR_MUT_W3_5',
    'SPR_MUT_W3_6',
    'SPR_MUT_W3_7',
    'SPR_MUT_W3_8',
    'SPR_MUT_W4_1',
    'SPR_MUT_W4_2',
    'SPR_MUT_W4_3',
    'SPR_MUT_W4_4',
    'SPR_MUT_W4_5',
    'SPR_MUT_W4_6',
    'SPR_MUT_W4_7',
    'SPR_MUT_W4_8',
    'SPR_MUT_PAIN_1',
    'SPR_MUT_DIE_1',
    'SPR_MUT_DIE_2',
    'SPR_MUT_DIE_3',
    'SPR_MUT_PAIN_2',
    'SPR_MUT_DIE_4',
    'SPR_MUT_DEAD',
    'SPR_MUT_SHOOT1',
    'SPR_MUT_SHOOT2',
    'SPR_MUT_SHOOT3',
    'SPR_MUT_SHOOT4',

    'SPR_OFC_S_1',
    'SPR_OFC_S_2',
    'SPR_OFC_S_3',
    'SPR_OFC_S_4',
    'SPR_OFC_S_5',
    'SPR_OFC_S_6',
    'SPR_OFC_S_7',
    'SPR_OFC_S_8',
    'SPR_OFC_W1_1',
    'SPR_OFC_W1_2',
    'SPR_OFC_W1_3',
    'SPR_OFC_W1_4',
    'SPR_OFC_W1_5',
    'SPR_OFC_W1_6',
    'SPR_OFC_W1_7',
    'SPR_OFC_W1_8',
    'SPR_OFC_W2_1',
    'SPR_OFC_W2_2',
    'SPR_OFC_W2_3',
    'SPR_OFC_W2_4',
    'SPR_OFC_W2_5',
    'SPR_OFC_W2_6',
    'SPR_OFC_W2_7',
    'SPR_OFC_W2_8',
    'SPR_OFC_W3_1',
    'SPR_OFC_W3_2',
    'SPR_OFC_W3_3',
    'SPR_OFC_W3_4',
    'SPR_OFC_W3_5',
    'SPR_OFC_W3_6',
    'SPR_OFC_W3_7',
    'SPR_OFC_W3_8',
    'SPR_OFC_W4_1',
    'SPR_OFC_W4_2',
    'SPR_OFC_W4_3',
    'SPR_OFC_W4_4',
    'SPR_OFC_W4_5',
    'SPR_OFC_W4_6',
    'SPR_OFC_W4_7',
    'SPR_OFC_W4_8',
    'SPR_OFC_PAIN_1',
    'SPR_OFC_DIE_1',
    'SPR_OFC_DIE_2',
    'SPR_OFC_DIE_3',
    'SPR_OFC_PAIN_2',
    'SPR_OFC_DIE_4',
    'SPR_OFC_DEAD',
    'SPR_OFC_SHOOT1',
    'SPR_OFC_SHOOT2',
    'SPR_OFC_SHOOT3',

    'SPR_BLINKY_W1',
    'SPR_BLINKY_W2',
    'SPR_PINKY_W1',
    'SPR_PINKY_W2',
    'SPR_CLYDE_W1',
    'SPR_CLYDE_W2',
    'SPR_INKY_W1',
    'SPR_INKY_W2',

    'SPR_BOSS_W1',
    'SPR_BOSS_W2',
    'SPR_BOSS_W3',
    'SPR_BOSS_W4',
    'SPR_BOSS_SHOOT1',
    'SPR_BOSS_SHOOT2',
    'SPR_BOSS_SHOOT3',
    'SPR_BOSS_DEAD',
    'SPR_BOSS_DIE1',
    'SPR_BOSS_DIE2',
    'SPR_BOSS_DIE3',

    'SPR_SCHABB_W1',
    'SPR_SCHABB_W2',
    'SPR_SCHABB_W3',
    'SPR_SCHABB_W4',
    'SPR_SCHABB_SHOOT1',
    'SPR_SCHABB_SHOOT2',
    'SPR_SCHABB_DIE1',
    'SPR_SCHABB_DIE2',
    'SPR_SCHABB_DIE3',
    'SPR_SCHABB_DEAD',
    'SPR_HYPO1',
    'SPR_HYPO2',
    'SPR_HYPO3',
    'SPR_HYPO4',

    'SPR_FAKE_W1',
    'SPR_FAKE_W2',
    'SPR_FAKE_W3',
    'SPR_FAKE_W4',
    'SPR_FAKE_SHOOT',
    'SPR_FIRE1',
    'SPR_FIRE2',
    'SPR_FAKE_DIE1',
    'SPR_FAKE_DIE2',
    'SPR_FAKE_DIE3',
    'SPR_FAKE_DIE4',
    'SPR_FAKE_DIE5',
    'SPR_FAKE_DEAD',

    'SPR_MECHA_W1',
    'SPR_MECHA_W2',
    'SPR_MECHA_W3',
    'SPR_MECHA_W4',
    'SPR_MECHA_SHOOT1',
    'SPR_MECHA_SHOOT2',
    'SPR_MECHA_SHOOT3',
    'SPR_MECHA_DEAD',
    'SPR_MECHA_DIE1',
    'SPR_MECHA_DIE2',
    'SPR_MECHA_DIE3',

    'SPR_HITLER_W1',
    'SPR_HITLER_W2',
    'SPR_HITLER_W3',
    'SPR_HITLER_W4',
    'SPR_HITLER_SHOOT1',
    'SPR_HITLER_SHOOT2',
    'SPR_HITLER_SHOOT3',
    'SPR_HITLER_DEAD',
    'SPR_HITLER_DIE1',
    'SPR_HITLER_DIE2',
    'SPR_HITLER_DIE3',
    'SPR_HITLER_DIE4',
    'SPR_HITLER_DIE5',
    'SPR_HITLER_DIE6',
    'SPR_HITLER_DIE7',

    'SPR_GIFT_W1',
    'SPR_GIFT_W2',
    'SPR_GIFT_W3',
    'SPR_GIFT_W4',
    'SPR_GIFT_SHOOT1',
    'SPR_GIFT_SHOOT2',
    'SPR_GIFT_DIE1',
    'SPR_GIFT_DIE2',
    'SPR_GIFT_DIE3',
    'SPR_GIFT_DEAD',
    'SPR_ROCKET_1',
    'SPR_ROCKET_2',
    'SPR_ROCKET_3',
    'SPR_ROCKET_4',
    'SPR_ROCKET_5',
    'SPR_ROCKET_6',
    'SPR_ROCKET_7',
    'SPR_ROCKET_8',
    'SPR_SMOKE_1',
    'SPR_SMOKE_2',
    'SPR_SMOKE_3',
    'SPR_SMOKE_4',
    'SPR_BOOM_1',
    'SPR_BOOM_2',
    'SPR_BOOM_3',

    'SPR_GRETEL_W1',
    'SPR_GRETEL_W2',
    'SPR_GRETEL_W3',
    'SPR_GRETEL_W4',
    'SPR_GRETEL_SHOOT1',
    'SPR_GRETEL_SHOOT2',
    'SPR_GRETEL_SHOOT3',
    'SPR_GRETEL_DEAD',
    'SPR_GRETEL_DIE1',
    'SPR_GRETEL_DIE2',
    'SPR_GRETEL_DIE3',

    'SPR_FAT_W1',
    'SPR_FAT_W2',
    'SPR_FAT_W3',
    'SPR_FAT_W4',
    'SPR_FAT_SHOOT1',
    'SPR_FAT_SHOOT2',
    'SPR_FAT_SHOOT3',
    'SPR_FAT_SHOOT4',
    'SPR_FAT_DIE1',
    'SPR_FAT_DIE2',
    'SPR_FAT_DIE3',
    'SPR_FAT_DEAD',

    'SPR_BJ_W1',
    'SPR_BJ_W2',
    'SPR_BJ_W3',
    'SPR_BJ_W4',
    'SPR_BJ_JUMP1',
    'SPR_BJ_JUMP2',
    'SPR_BJ_JUMP3',
    'SPR_BJ_JUMP4',

    'SPR_KNIFEREADY',
    'SPR_KNIFEATK1',
    'SPR_KNIFEATK2',
    'SPR_KNIFEATK3',
    'SPR_KNIFEATK4',

    'SPR_PISTOLREADY',
    'SPR_PISTOLATK1',
    'SPR_PISTOLATK2',
    'SPR_PISTOLATK3',
    'SPR_PISTOLATK4',

    'SPR_MACHINEGUNREADY',
    'SPR_MACHINEGUNATK1',
    'SPR_MACHINEGUNATK2',
    'SPR_MACHINEGUNATK3',
    'SPR_MACHINEGUNATK4',

    'SPR_CHAINREADY',
    'SPR_CHAINATK1',
    'SPR_CHAINATK2',
    'SPR_CHAINATK3',
    'SPR_CHAINATK4',
]

SPRITE_NAMES = [
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
    'bones_1',
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
    'chalice',
    'jewels',
    'crown',
    'extra_life',
    'bones__blood',
    'barrel',
    'well__water',
    'well',
    'blood_pool',
    'flag',
    'bones_5',
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

    'bj__run_a0',
    'bj__run_a1',
    'bj__run_a2',
    'bj__run_a3',
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
]


SCREEN_NAMES = [
    'exit',
    'error',
]


AUDIO_PARTITIONS_MAP = {
    'buzzer':   (  0,  87),
    'adlib':    ( 87,  87),
    'digital':  (174,  87),
    'music':    (261,  27),
}

SOUND_LABELS = [
    'HITWALLSND',
    'SELECTWPNSND',
    'SELECTITEMSND',
    'HEARTBEATSND',
    'MOVEGUN2SND',
    'MOVEGUN1SND',
    'NOWAYSND',
    'NAZIHITPLAYERSND',
    'SCHABBSTHROWSND',
    'PLAYERDEATHSND',
    'DOGDEATHSND',
    'ATKGATLINGSND',
    'GETKEYSND',
    'NOITEMSND',
    'WALK1SND',
    'WALK2SND',
    'TAKEDAMAGESND',
    'GAMEOVERSND',
    'OPENDOORSND',
    'CLOSEDOORSND',
    'DONOTHINGSND',
    'HALTSND',
    'DEATHSCREAM2SND',
    'ATKKNIFESND',
    'ATKPISTOLSND',
    'DEATHSCREAM3SND',
    'ATKMACHINEGUNSND',
    'HITENEMYSND',
    'SHOOTDOORSND',
    'DEATHSCREAM1SND',
    'GETMACHINESND',
    'GETAMMOSND',
    'SHOOTSND',
    'HEALTH1SND',
    'HEALTH2SND',
    'BONUS1SND',
    'BONUS2SND',
    'BONUS3SND',
    'GETGATLINGSND',
    'ESCPRESSEDSND',
    'LEVELDONESND',
    'DOGBARKSND',
    'ENDBONUS1SND',
    'ENDBONUS2SND',
    'BONUS1UPSND',
    'BONUS4SND',
    'PUSHWALLSND',
    'NOBONUSSND',
    'PERCENT100SND',
    'BOSSACTIVESND',
    'MUTTISND',
    'SCHUTZADSND',
    'AHHHGSND',
    'DIESND',
    'EVASND',
    'GUTENTAGSND',
    'LEBENSND',
    'SCHEISTSND',
    'NAZIFIRESND',
    'BOSSFIRESND',
    'SSFIRESND',
    'SLURPIESND',
    'TOT_HUNDSND',
    'MEINGOTTSND',
    'SCHABBSHASND',
    'HITLERHASND',
    'SPIONSND',
    'NEINSOVASSND',
    'DOGATTACKSND',
    'FLAMETHROWERSND',
    'MECHSTEPSND',
    'GOOBSSND',
    'YEAHSND',
    'DEATHSCREAM4SND',
    'DEATHSCREAM5SND',
    'DEATHSCREAM6SND',
    'DEATHSCREAM7SND',
    'DEATHSCREAM8SND',
    'DEATHSCREAM9SND',
    'DONNERSND',
    'EINESND',
    'ERLAUBENSND',
    'KEINSND',
    'MEINSND',
    'ROSESND',
    'MISSILEFIRESND',
    'MISSILEHITSND',
]

SOUND_NAMES = [
    'player__wall_hit',
    '_SELECTWPNSND',
    '_SELECTITEMSND',
    '_HEARTBEATSND',
    'menu__half_step',
    'menu__step',
    'player__no_way',
    '_NAZIHITPLAYERSND',
    'schabbs__attack',
    'player__death',
    'dog__death',
    'chaingun__attack',
    'pickup__key',
    '_NOITEMSND',
    '_WALK1SND',
    '_WALK2SND',
    '_TAKEDAMAGESND',
    '_GAMEOVERSND',
    'door__open',
    'door__close',
    'player__do_nothing',
    'guard__wake',
    'guard__death_2',
    'knife__attack',
    'pistol__attack',
    'guard__death_3',
    'machinegun__attack',
    '_HITENEMYSND',
    'menu__bind',
    'guard__death_1',
    'pickup__machinegun',
    'pickup__ammo',
    'menu__select',
    'pickup__food',
    'pickup__medkit',
    'pickup__cross',
    'pickup__chalice',
    'pickup__jewels',
    'pickup__chaingun',
    'menu__exit',
    'elevator__use',
    'dog__wake',
    'score__bonus_tens',
    'score__bonus_got',
    'pickup__extra_life',
    'pickup__crown',
    'pushwall__move',
    'score__no_bonus',
    'score__100',
    '_BOSSACTIVESND',
    'hans__death',
    'ss__wake',
    'mutant__death',
    'hitler__wake',
    'hitler__death',
    'hans__wake',
    'ss__death',
    'mecha_hitler__death',
    'guard__attack',
    'boss__gun_attack',
    'ss__attack',
    'blood__slurpie',
    'robed_fake__wake',
    'schabbs__death',
    'schabbs__wake',
    'robed_fake__death',
    'officer__wake',
    'officer__death',
    'dog__attack',
    'robed_fake__attack',
    'mecha_hitler__step',
    '_GOOBSSND',
    'bj__yeah',
    'guard__death_4',
    'guard__death_5',
    'secret__death',
    'guard__death_6',
    'guard__death_7',
    'guard__death_8',
    'otto__death',
    'otto__wake',
    'fettgesicht__wake',
    'gretel__wake',
    'gretel__death',
    'fettgesicht__death',
    'boss__missile_attack',
    'missile__hit',
]


SAMPLED_SOUND_FREQUENCY = 7042

SAMPLED_SOUND_LABELS = [
    'HALTSND',
    'DOGBARKSND',
    'CLOSEDOORSND',
    'OPENDOORSND',
    'ATKMACHINEGUNSND',
    'ATKPISTOLSND',
    'ATKGATLINGSND',
    'SCHUTZADSND',
    'GUTENTAGSND',
    'MUTTISND',
    'BOSSFIRESND',
    'SSFIRESND',
    'DEATHSCREAM1SND',
    'DEATHSCREAM2SND',
    'DEATHSCREAM3SND',
    'PUSHWALLSND',
    'DOGDEATHSND',
    'AHHHGSND',
    'DIESND',
    'EVASND',
    'LEBENSND',
    'NAZIFIRESND',
    'SLURPIESND',
    'TOT_HUNDSND',
    'MEINGOTTSND',
    'SCHABBSHASND',
    'HITLERHASND',
    'SPIONSND',
    'NEINSOVASSND',
    'DOGATTACKSND',
    'LEVELDONESND',
    'MECHSTEPSND',
    'YEAHSND',
    'SCHEISTSND',
    'DEATHSCREAM4SND',
    'DEATHSCREAM5SND',
    'DONNERSND',
    'EINESND',
    'ERLAUBENSND',
    'DEATHSCREAM6SND',
    'DEATHSCREAM7SND',
    'DEATHSCREAM8SND',
    'DEATHSCREAM9SND',
    'KEINSND',
    'MEINSND',
    'ROSESND',
]

SAMPLED_SOUND_INDICES = [SOUND_LABELS.index(label) for label in SAMPLED_SOUND_LABELS]
SAMPLED_SOUND_NAMES = [SOUND_NAMES[i] for i in SAMPLED_SOUND_INDICES]


BUZZER_SOUND_LABELS = SOUND_LABELS
BUZZER_SOUND_INDICES = tuple(range(len(SOUND_LABELS)))
BUZZER_SOUND_NAMES = SOUND_NAMES


ADLIB_SOUND_LABELS = BUZZER_SOUND_LABELS
ADLIB_SOUND_INDICES = BUZZER_SOUND_INDICES
ADLIB_SOUND_NAMES = BUZZER_SOUND_NAMES


MUSIC_LABELS = [
    'CORNER_MUS',
    'DUNGEON_MUS',
    'WARMARCH_MUS',
    'GETTHEM_MUS',
    'HEADACHE_MUS',
    'HITLWLTZ_MUS',
    'INTROCW3_MUS',
    'NAZI_NOR_MUS',
    'NAZI_OMI_MUS',
    'POW_MUS',
    'SALUTE_MUS',
    'SEARCHN_MUS',
    'SUSPENSE_MUS',
    'VICTORS_MUS',
    'WONDERIN_MUS',
    'FUNKYOU_MUS',
    'ENDLEVEL_MUS',
    'GOINGAFT_MUS',
    'PREGNANT_MUS',
    'ULTIMATE_MUS',
    'NAZI_RAP_MUS',
    'ZEROHOUR_MUS',
    'TWELFTH_MUS',
    'ROSTER_MUS',
    'URAHERO_MUS',
    'VICMARCH_MUS',
    'PACMAN_MUS',
]

MUSIC_NAMES = [
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
]


TILE_PARTITION_MAP = {
    'wall':             (  1,  49),

    'door_panel':       ( 50,   1),
    'door_hinge':       ( 51,   1),
    'door_locked':      ( 53,   1),

    'door':             ( 90,   2),
    'door_silver':      ( 92,   2),
    'door_gold':        ( 94,   2),
    'door_elevator':    (100,   2),

    'floor':            (106,  38),  # includes the ones below
    'deaf':             (106,   1),
    'secret':           (107,   1),
    'area':             (107,  36),
}

DOOR_MAP = {  # {tile: (name, vertical)}
    90:  ('door',          'door_panel',    True),
    91:  ('door',          'door_panel',    False),
    92:  ('door_silver',   'door_locked',   True),
    93:  ('door_silver',   'door_locked',   False),
    94:  ('door_gold',     'door_locked',   True),
    95:  ('door_gold',     'door_locked',   False),
    100: ('door_elevator', 'door_elevator', True),
    101: ('door_elevator', 'door_elevator', False),
}

ENTITY_PARTITION_MAP = {  # TODO
    'start':        ( 19,   4),
    'turn':         ( 90,   8),
    'pushwall':     ( 98,   1),
    'endgame':      ( 99,   1),
    'object':       ( 23,  48),
    'enemy':        (100, 200),  # broad range
    'dead_guard':   (124,   1),  # inside of enemies, whatever...
}

ENTITY_OBJECT_MAP = {
    23: 'water_pool',
    24: 'oil_drum',
    25: 'table__chairs',
    26: 'lamp',
    27: 'chandelier',
    28: 'hanging_skeleton',
    30: 'pillar',
    31: 'green_plant',
    32: 'skeleton',
    33: 'sink',
    34: 'brown_plant',
    35: 'vase',
    36: 'table',
    37: 'ceiling_light',
    38: 'utensils_brown',
    39: 'armor',
    40: 'cage',
    41: 'cage__skeleton',
    42: 'bones_1',
    45: 'bed',
    46: 'basket',
    57: 'bones__blood',
    58: 'barrel',
    59: 'well__water',
    60: 'well',
    61: 'blood_pool',
    62: 'flag',
    63: 'aardwolf',
    64: 'bones_2',
    65: 'bones_3',
    66: 'bones_4',
    67: 'utensils_blue',
    68: 'stove',
    69: 'rack',
    70: 'vines',

    29: 'dog_food',
    43: 'gold_key',
    44: 'silver_key',
    47: 'food',
    48: 'medkit',
    49: 'ammo',
    50: 'machinegun',
    51: 'chaingun',
    52: 'cross',
    53: 'chalice',
    54: 'jewels',
    55: 'crown',
    56: 'extra_life',

    124: 'guard__dead',
}


ENEMY_MAP = {  # {'name', direction_index, moving, level}
    180: ('guard', 0, False, 3),
    181: ('guard', 1, False, 3),
    182: ('guard', 2, False, 3),
    183: ('guard', 3, False, 3),
    144: ('guard', 0, False, 2),
    145: ('guard', 1, False, 2),
    146: ('guard', 2, False, 2),
    147: ('guard', 3, False, 2),
    108: ('guard', 0, False, 0),
    109: ('guard', 1, False, 0),
    110: ('guard', 2, False, 0),
    111: ('guard', 3, False, 0),
    184: ('guard', 0, True,  3),
    185: ('guard', 1, True,  3),
    186: ('guard', 2, True,  3),
    187: ('guard', 3, True,  3),
    148: ('guard', 0, True,  2),
    149: ('guard', 1, True,  2),
    150: ('guard', 2, True,  2),
    151: ('guard', 3, True,  2),
    112: ('guard', 0, True,  0),
    113: ('guard', 1, True,  0),
    114: ('guard', 2, True,  0),
    115: ('guard', 3, True,  0),

    188: ('officer', 0, False, 3),
    189: ('officer', 1, False, 3),
    190: ('officer', 2, False, 3),
    191: ('officer', 3, False, 3),
    152: ('officer', 0, False, 2),
    153: ('officer', 1, False, 2),
    154: ('officer', 2, False, 2),
    155: ('officer', 3, False, 2),
    116: ('officer', 0, False, 0),
    117: ('officer', 1, False, 0),
    118: ('officer', 2, False, 0),
    119: ('officer', 3, False, 0),
    192: ('officer', 0, True,  3),
    193: ('officer', 1, True,  3),
    194: ('officer', 2, True,  3),
    195: ('officer', 3, True,  3),
    156: ('officer', 0, True,  2),
    157: ('officer', 1, True,  2),
    158: ('officer', 2, True,  2),
    159: ('officer', 3, True,  2),
    120: ('officer', 0, True,  0),
    121: ('officer', 1, True,  0),
    122: ('officer', 2, True,  0),
    123: ('officer', 3, True,  0),

    198: ('ss', 0, False, 3),
    199: ('ss', 1, False, 3),
    200: ('ss', 2, False, 3),
    201: ('ss', 3, False, 3),
    162: ('ss', 0, False, 2),
    163: ('ss', 1, False, 2),
    164: ('ss', 2, False, 2),
    165: ('ss', 3, False, 2),
    126: ('ss', 0, False, 0),
    127: ('ss', 1, False, 0),
    128: ('ss', 2, False, 0),
    129: ('ss', 3, False, 0),
    202: ('ss', 0, True,  3),
    203: ('ss', 1, True,  3),
    204: ('ss', 2, True,  3),
    205: ('ss', 3, True,  3),
    166: ('ss', 0, True,  2),
    167: ('ss', 1, True,  2),
    168: ('ss', 2, True,  2),
    169: ('ss', 3, True,  2),
    130: ('ss', 0, True,  0),
    131: ('ss', 1, True,  0),
    132: ('ss', 2, True,  0),
    133: ('ss', 3, True,  0),

    210: ('dog', 0, True, 3),
    211: ('dog', 1, True, 3),
    212: ('dog', 2, True, 3),
    213: ('dog', 3, True, 3),
    174: ('dog', 0, True, 2),
    175: ('dog', 1, True, 2),
    176: ('dog', 2, True, 2),
    177: ('dog', 3, True, 2),
    138: ('dog', 0, True, 0),
    139: ('dog', 1, True, 0),
    140: ('dog', 2, True, 0),
    141: ('dog', 3, True, 0),

    252: ('mutant', 0, False, 3),
    253: ('mutant', 1, False, 3),
    254: ('mutant', 2, False, 3),
    255: ('mutant', 3, False, 3),
    234: ('mutant', 0, False, 2),
    235: ('mutant', 1, False, 2),
    236: ('mutant', 2, False, 2),
    237: ('mutant', 3, False, 2),
    216: ('mutant', 0, False, 0),
    217: ('mutant', 1, False, 0),
    218: ('mutant', 2, False, 0),
    219: ('mutant', 3, False, 0),
    256: ('mutant', 0, True,  3),
    257: ('mutant', 1, True,  3),
    258: ('mutant', 2, True,  3),
    259: ('mutant', 3, True,  3),
    238: ('mutant', 0, True,  2),
    239: ('mutant', 1, True,  2),
    240: ('mutant', 2, True,  2),
    241: ('mutant', 3, True,  2),
    220: ('mutant', 0, True,  0),
    221: ('mutant', 1, True,  0),
    222: ('mutant', 2, True,  0),
    223: ('mutant', 3, True,  0),

    224: ('ghost_blinky', 4, True, 0),
    226: ('ghost_pinky',  4, True, 0),
    225: ('ghost_clyde',  4, True, 0),
    227: ('ghost_inky',   4, True, 0),

    214: ('hans', 4, True, 0),
    197: ('gretel', 4, True, 0),
    179: ('fettgesicht', 4, True, 0),
    160: ('robed_fake', 4, True, 0),
    196: ('schabbs', 4, True, 0),
    215: ('otto', 4, True, 0),
    178: ('hitler', 4, True, 0),
}


TILEMAP_MUSIC_LABELS = [
    'GETTHEM_MUS',
    'SEARCHN_MUS',
    'POW_MUS',
    'SUSPENSE_MUS',
    'GETTHEM_MUS',
    'SEARCHN_MUS',
    'POW_MUS',
    'SUSPENSE_MUS',
    'WARMARCH_MUS',
    'CORNER_MUS',

    'NAZI_OMI_MUS',
    'PREGNANT_MUS',
    'GOINGAFT_MUS',
    'HEADACHE_MUS',
    'NAZI_OMI_MUS',
    'PREGNANT_MUS',
    'HEADACHE_MUS',
    'GOINGAFT_MUS',
    'WARMARCH_MUS',
    'DUNGEON_MUS',

    'INTROCW3_MUS',
    'NAZI_RAP_MUS',
    'TWELFTH_MUS',
    'ZEROHOUR_MUS',
    'INTROCW3_MUS',
    'NAZI_RAP_MUS',
    'TWELFTH_MUS',
    'ZEROHOUR_MUS',
    'ULTIMATE_MUS',
    'PACMAN_MUS',

    'GETTHEM_MUS',
    'SEARCHN_MUS',
    'POW_MUS',
    'SUSPENSE_MUS',
    'GETTHEM_MUS',
    'SEARCHN_MUS',
    'POW_MUS',
    'SUSPENSE_MUS',
    'WARMARCH_MUS',
    'CORNER_MUS',

    'NAZI_OMI_MUS',
    'PREGNANT_MUS',
    'GOINGAFT_MUS',
    'HEADACHE_MUS',
    'NAZI_OMI_MUS',
    'PREGNANT_MUS',
    'HEADACHE_MUS',
    'GOINGAFT_MUS',
    'WARMARCH_MUS',
    'DUNGEON_MUS',

    'INTROCW3_MUS',
    'NAZI_RAP_MUS',
    'TWELFTH_MUS',
    'ZEROHOUR_MUS',
    'INTROCW3_MUS',
    'NAZI_RAP_MUS',
    'TWELFTH_MUS',
    'ZEROHOUR_MUS',
    'ULTIMATE_MUS',
    'FUNKYOU_MUS',
]

TILEMAP_MUSIC_INDICES = [MUSIC_LABELS.index(label) for label in TILEMAP_MUSIC_LABELS]

EPISODES = [  # (start, count, name)
    ( 0, 10, 'Escape from Wolfenstein'),
    (10, 10, 'Operation: Eisenfaust'),
    (20, 10, 'Die, Fuhrer, Die!'),
    (30, 10, 'A Dark Secret'),
    (40, 10, 'Trail of the Madman'),
    (50, 10, 'Confrontation'),
]

FLOOR_COLORS = [0x19] * (10 * 6)

CEILING_COLORS = [
    0x1D, 0x1D, 0x1D, 0x1D, 0x1D, 0x1D, 0x1D, 0x1D, 0x1D, 0xBF,
    0x4E, 0x4E, 0x4E, 0x1D, 0x8D, 0x4E, 0x1D, 0x2D, 0x1D, 0x8D,
    0x1D, 0x1D, 0x1D, 0x1D, 0x1D, 0x2D, 0xDD, 0x1D, 0x1D, 0x98,
    0x1D, 0x9D, 0x2D, 0xDD, 0xDD, 0x9D, 0x2D, 0x4D, 0x1D, 0xDD,
    0x7D, 0x1D, 0x2D, 0x2D, 0xDD, 0xD7, 0x1D, 0x1D, 0x1D, 0x2D,
    0x1D, 0x1D, 0x1D, 0x1D, 0xDD, 0xDD, 0x7D, 0xDD, 0xDD, 0xDD,
]


STATIC_OBJECT_NAMES = [
    'armor',
    'barrel',
    'basket',
    'bed',
    'blood_pool',
    'bones__blood',
    'bones_1',
    'bones_2',
    'bones_3',
    'bones_4',
    'bones_5',
    'brown_plant',
    'cage',
    'cage__skeleton',
    'ceiling_light',
    'chandelier',
    'flag',
    'green_plant',
    'guard__dead',
    'hanging_skeleton',
    'lamp',
    'oil_drum',
    'pillar',
    'rack',
    'sink',
    'skeleton',
    'stove',
    'table',
    'table__chairs',
    'utensils_blue',
    'utensils_brown',
    'vase',
    'vines',
    'water_pool',
    'well',
    'well__water',
]

SOLID_OBJECT_NAMES = [
    'armor',
    'barrel',
    'bed',
    'brown_plant',
    'cage',
    'cage__skeleton',
    'flag',
    'green_plant',
    'hanging_skeleton',
    'lamp',
    'oil_drum',
    'pillar',
    'rack',
    'sink',
    'stove',
    'table',
    'table__chairs',
    'vase',
    'well',
    'well__water',
]

COLLECTABLE_OBJECT_NAMES = [
    'ammo',
    'ammo_used',
    'chaingun',
    'chalice',
    'cross',
    'crown',
    'dog_food',
    'extra_life',
    'food',
    'gold_key',
    'jewels',
    'machinegun',
    'medkit',
    'silver_key',
]

COLLECTABLE_PICKUP_SOUNDS = {
    'ammo':       'pickup__ammo',
    'ammo_used':  'pickup__ammo',
    'chaingun':   'pickup__chaingun',
    'chalice':    'pickup__chalice',
    'cross':      'pickup__cross',
    'crown':      'pickup__crown',
    'dog_food':   'pickup__medkit',
    'extra_life': 'pickup__extra_life',
    'food':       'pickup__food',
    'gold_key':   'pickup__key',
    'jewels':     'pickup__jewels',
    'machinegun': 'pickup__machinegun',
    'medkit':     'pickup__medkit',
    'silver_key': 'pickup__key',
}

# TODO: add 'speed'
ENEMY_DESCRIPTORS = {
    'dog': {
        'health': 1,
        'points': 200,
        'speed': 1500,
        'sounds': {
            'sight':  'DOGBARKSND',
            'attack': 'DOGATTACKSND',
            'death':  'DOGDEATHSND',
        },
    },
    'fettgesicht': {
        'health': [850, 950, 1050, 1200],
        'points': 5000,
        'sounds': {
            'sight':  'ERLAUBENSND',
            'attack': 'MISSILEFIRESND',
            'death':  'ROSESND',
        },
    },
    'ghost_blinky': {
        'health': 25,
    },
    'ghost_clyde': {
        'health': 25,
    },
    'ghost_inky': {
        'health': 25,
    },
    'ghost_pinky': {
        'health': 25,
    },
    'gretel': {
        'health': [850, 950, 1050, 1200],
        'points': 5000,
        'drop': 'key_silver',
        'sounds': {
            'sight':  'KEINSND',
            'attack': 'NAZIFIRESND',
            'death':  'MEINSND',
        },
    },
    'guard': {
        'health': 25,
        'points': 100,
        'drop': 'ammo_used',
        'sounds': {
            'sight': 'HALTSND',
            'attack': 'NAZIFIRESND',
            'death': [
                'DEATHSCREAM2SND',
                'DEATHSCREAM3SND',
                'DEATHSCREAM4SND',
                'DEATHSCREAM5SND',
                'DEATHSCREAM7SND',
                'DEATHSCREAM8SND',
                'DEATHSCREAM9SND'
            ],
        },
    },
    'hans': {
        'health': [850, 950, 1050, 1200],
        'points': 5000,
        'drop': 'silver_key',
        'sounds': {
            'sight':  'GUTENTAGSND',
            'attack': 'BOSSFIRESND',
            'death':  'MUTTISND',
        },
    },
    'hitler': {
        'health': [500, 700, 800, 900],
        'points': 5000,
        'sounds': {
            'sight':  'DIESND',
            'attack': 'BOSSFIRESND',
            'death':  'EVASND',
        },
    },
    'mecha_hitler': {
        'health': [800, 950, 1050, 1200],
        'points': 5000,
        'sounds': {
            'sight':  'DIESND',
            'attack': 'BOSSFIRESND',
            'death':  'SCHEISTSND',
        },
    },
    'mutant': {
        'health': [45, 55, 55, 65],
        'points': 700,
        'drop': 'ammo_used',
        'sounds': {
            'attack': 'NAZIFIRESND',
            'death':  'AHHHGSND',
        },
    },
    'officer': {
        'health': 50,
        'points': 400,
        'drop': 'ammo_used',
        'sounds': {
            'sight':  'SPIONSND',
            'attack': 'NAZIFIRESND',
            'death':  'NEINSOVASSND',
        },
    },
    'otto': {
        'health': [850, 950, 1050, 1200],
        'points': 5000,
        'sounds': {
            'sight':  'EINESND',
            'attack': 'MISSILEFIRESND',
            'death':  'DONNERSND',
        },
    },
    'robed_fake': {
        'health': [200, 300, 400, 500],
        'points': 2000,
        'sounds': {
            'sight':  'TOT_HUNDSND',
            'attack': 'FLAMETHROWERSND',
            'death':  'HITLERHASND',
        },
    },
    'schabbs': {
        'health': [850, 950, 1550, 2400],
        'points': 5000,
        'sounds': {
            'sight':  'SCHABBSHASND',
            'attack': 'SCHABBSTHROWSND',
            'death':  'MEINGOTTSND',
        },
    },
    'ss': {
        'health': 100,
        'points': 400,
        'drop': 'machinegun',
        'sounds': {
            'sight':  'SCHUTZADSND',
            'attack': 'SSFIRESND',
            'death':  'LEBENSND',
        },
    },
}

ENEMY_NAMES = list(sorted(ENEMY_DESCRIPTORS.keys()))

OBJECT_STATES = {  # (rotate, sprite, ticks, think, action, next)
    'boom': {
        'die1': (False, 'SPR_BOOM_1', 6, None, None, 'die2'),
        'die2': (False, 'SPR_BOOM_2', 6, None, None, 'die3'),
        'die3': (False, 'SPR_BOOM_3', 6, None, None, None),
    },
    'dog': {
        'path1':  (True, 'SPR_DOG_W1_1', 20, 'T_Path', None, 'path1s'),
        'path1s': (True, 'SPR_DOG_W1_1',  5, None,     None, 'path2'),
        'path2':  (True, 'SPR_DOG_W2_1', 15, 'T_Path', None, 'path3'),
        'path3':  (True, 'SPR_DOG_W3_1', 20, 'T_Path', None, 'path3s'),
        'path3s': (True, 'SPR_DOG_W3_1',  5, None,     None, 'path4'),
        'path4':  (True, 'SPR_DOG_W4_1', 15, 'T_Path', None, 'path1'),

        'jump1': (False, 'SPR_DOG_JUMP1', 10, None, None,     'jump2'),
        'jump2': (False, 'SPR_DOG_JUMP2', 10, None, 'T_Bite', 'jump3'),
        'jump3': (False, 'SPR_DOG_JUMP3', 10, None, None,     'jump4'),
        'jump4': (False, 'SPR_DOG_JUMP1', 10, None, None,     'jump5'),
        'jump5': (False, 'SPR_DOG_W1_1',  10, None, None,     'chase1'),

        'chase1':  (True, 'SPR_DOG_W1_1', 10, 'T_DogChase', None, 'chase1s'),
        'chase1s': (True, 'SPR_DOG_W1_1',  3, None,         None, 'chase2'),
        'chase2':  (True, 'SPR_DOG_W2_1',  8, 'T_DogChase', None, 'chase3'),
        'chase3':  (True, 'SPR_DOG_W3_1', 10, 'T_DogChase', None, 'chase3s'),
        'chase3s': (True, 'SPR_DOG_W3_1',  3, None,         None, 'chase4'),
        'chase4':  (True, 'SPR_DOG_W4_1',  8, 'T_DogChase', None, 'chase1'),

        'die1': (False, 'SPR_DOG_DIE_1', 15, None, 'A_DeathScream', 'die2'),
        'die2': (False, 'SPR_DOG_DIE_2', 15, None, None, 'die3'),
        'die3': (False, 'SPR_DOG_DIE_3', 15, None, None, 'dead'),
        'dead': (False, 'SPR_DOG_DEAD',  15, None, None, 'dead'),
    },
    'fettgesicht': {
        'stand': (False, 'SPR_FAT_W1', 0, 'T_Stand', None, 'stand'),

        'chase1':  (False, 'SPR_FAT_W1', 10, 'T_Fat', None, 'chase1s'),
        'chase1s': (False, 'SPR_FAT_W1',  3, None,    None, 'chase2'),
        'chase2':  (False, 'SPR_FAT_W2',  8, 'T_Fat', None, 'chase3'),
        'chase3':  (False, 'SPR_FAT_W3', 10, 'T_Fat', None, 'chase3s'),
        'chase3s': (False, 'SPR_FAT_W3',  3, None,    None, 'chase4'),
        'chase4':  (False, 'SPR_FAT_W4',  8, 'T_Fat', None, 'chase1'),

        'deathcam': (False, 'SPR_FAT_W1', 1, None, None, 'die1'),

        'die1': (False, 'SPR_FAT_W1',    1, None, 'A_DeathScream',   'die2'),
        'die2': (False, 'SPR_FAT_W1',   10, None, None,              'die3'),
        'die3': (False, 'SPR_FAT_DIE1', 10, None, None,              'die4'),
        'die4': (False, 'SPR_FAT_DIE2', 10, None, None,              'die5'),
        'die5': (False, 'SPR_FAT_DIE3', 10, None, None,              'die6'),
        'die6': (False, 'SPR_FAT_DEAD', 20, None, 'A_StartDeathCam', 'die6'),

        'shoot1': (False, 'SPR_FAT_SHOOT1', 30, None, None,          'shoot2'),
        'shoot2': (False, 'SPR_FAT_SHOOT2', 10, None, 'T_GiftThrow', 'shoot3'),
        'shoot3': (False, 'SPR_FAT_SHOOT3', 10, None, 'T_Shoot',     'shoot4'),
        'shoot4': (False, 'SPR_FAT_SHOOT4', 10, None, 'T_Shoot',     'shoot5'),
        'shoot5': (False, 'SPR_FAT_SHOOT3', 10, None, 'T_Shoot',     'shoot6'),
        'shoot6': (False, 'SPR_FAT_SHOOT4', 10, None, 'T_Shoot',     'chase1'),
    },
    'ghost_blinky': {
        'chase1':  (False, 'SPR_BLINKY_W1', 10, 'T_Ghosts', None, 'chase2'),
        'chase2':  (False, 'SPR_BLINKY_W2', 10, 'T_Ghosts', None, 'chase1'),
    },
    'ghost_clyde': {
        'chase1':  (False, 'SPR_CLYDE_W1', 10, 'T_Ghosts', None, 'chase2'),
        'chase2':  (False, 'SPR_CLYDE_W2', 10, 'T_Ghosts', None, 'chase1'),
    },
    'ghost_inky': {
        'chase1':  (False, 'SPR_INKY_W1', 10, 'T_Ghosts', None, 'chase2'),
        'chase2':  (False, 'SPR_INKY_W2', 10, 'T_Ghosts', None, 'chase1'),
    },
    'ghost_pinky': {
        'chase1':  (False, 'SPR_PINKY_W1', 10, 'T_Ghosts', None, 'chase2'),
        'chase2':  (False, 'SPR_PINKY_W2', 10, 'T_Ghosts', None, 'chase1'),
    },
    'gretel': {
        'stand': (False, 'SPR_GRETEL_W1', 0, 'T_Stand', None, 'stand'),

        'chase1':  (False, 'SPR_GRETEL_W1', 10, 'T_Chase', None, 'chase1s'),
        'chase1s': (False, 'SPR_GRETEL_W1',  3, None,      None, 'chase2'),
        'chase2':  (False, 'SPR_GRETEL_W2',  8, 'T_Chase', None, 'chase3'),
        'chase3':  (False, 'SPR_GRETEL_W3', 10, 'T_Chase', None, 'chase3s'),
        'chase3s': (False, 'SPR_GRETEL_W3',  3, None,      None, 'chase4'),
        'chase4':  (False, 'SPR_GRETEL_W4',  8, 'T_Chase', None, 'chase1'),

        'die1': (False, 'SPR_GRETEL_DIE1', 15, None, 'A_DeathScream', 'die2'),
        'die2': (False, 'SPR_GRETEL_DIE2', 15, None, None,            'die3'),
        'die3': (False, 'SPR_GRETEL_DIE3', 15, None, None,            'die4'),
        'die4': (False, 'SPR_GRETEL_DEAD',  0, None, None,            'die4'),

        'shoot1': (False, 'SPR_GRETEL_SHOOT1', 30, None, None,      'shoot2'),
        'shoot2': (False, 'SPR_GRETEL_SHOOT2', 10, None, 'T_Shoot', 'shoot3'),
        'shoot3': (False, 'SPR_GRETEL_SHOOT3', 10, None, 'T_Shoot', 'shoot4'),
        'shoot4': (False, 'SPR_GRETEL_SHOOT2', 10, None, 'T_Shoot', 'shoot5'),
        'shoot5': (False, 'SPR_GRETEL_SHOOT3', 10, None, 'T_Shoot', 'shoot6'),
        'shoot6': (False, 'SPR_GRETEL_SHOOT2', 10, None, 'T_Shoot', 'shoot7'),
        'shoot7': (False, 'SPR_GRETEL_SHOOT3', 10, None, 'T_Shoot', 'shoot8'),
        'shoot8': (False, 'SPR_GRETEL_SHOOT1', 10, None, None,      'chase1'),
    },
    'guard': {
        'stand': (True, 'SPR_GRD_S_1', 0, 'T_Stand', None, 'stand'),

        'path1':  (True, 'SPR_GRD_W1_1', 20, 'T_Path', None, 'path1s'),
        'path1s': (True, 'SPR_GRD_W1_1',  5, None,     None, 'path2'),
        'path2':  (True, 'SPR_GRD_W2_1', 15, 'T_Path', None, 'path3'),
        'path3':  (True, 'SPR_GRD_W3_1', 20, 'T_Path', None, 'path3s'),
        'path3s': (True, 'SPR_GRD_W3_1',  5, None,     None, 'path4'),
        'path4':  (True, 'SPR_GRD_W4_1', 15, 'T_Path', None, 'path1'),

        'pain':  (False, 'SPR_GRD_PAIN_1', 10, None, None, 'chase1'),
        'pain1': (False, 'SPR_GRD_PAIN_2', 10, None, None, 'chase1'),

        'shoot1': (False, 'SPR_GRD_SHOOT1', 20, None, None,      'shoot2'),
        'shoot2': (False, 'SPR_GRD_SHOOT2', 20, None, 'T_Shoot', 'shoot3'),
        'shoot3': (False, 'SPR_GRD_SHOOT3', 20, None, None,      'chase1'),

        'chase1':  (True, 'SPR_GRD_W1_1', 10, 'T_Chase', None, 'chase1s'),
        'chase1s': (True, 'SPR_GRD_W1_1',  3, None,      None, 'chase2'),
        'chase2':  (True, 'SPR_GRD_W2_1',  8, 'T_Chase', None, 'chase3'),
        'chase3':  (True, 'SPR_GRD_W3_1', 10, 'T_Chase', None, 'chase3s'),
        'chase3s': (True, 'SPR_GRD_W3_1',  3, None,      None, 'chase4'),
        'chase4':  (True, 'SPR_GRD_W4_1',  8, 'T_Chase', None, 'chase1'),

        'die1': (False, 'SPR_GRD_DIE_1', 15, None, 'A_DeathScream', 'die2'),
        'die2': (False, 'SPR_GRD_DIE_2', 15, None, None,            'die3'),
        'die3': (False, 'SPR_GRD_DIE_3', 15, None, None,            'die4'),
        'die4': (False, 'SPR_GRD_DEAD',   0, None, None,            'die4'),
    },
    'hans': {
        'stand': (False, 'SPR_BOSS_W1', 0, 'T_Stand', None, 'stand'),

        'chase1':  (False, 'SPR_BOSS_W1', 10, 'T_Chase', None, 'chase1s'),
        'chase1s': (False, 'SPR_BOSS_W1',  3, None,      None, 'chase2'),
        'chase2':  (False, 'SPR_BOSS_W2',  8, 'T_Chase', None, 'chase3'),
        'chase3':  (False, 'SPR_BOSS_W3', 10, 'T_Chase', None, 'chase3s'),
        'chase3s': (False, 'SPR_BOSS_W3',  3, None,      None, 'chase4'),
        'chase4':  (False, 'SPR_BOSS_W4',  8, 'T_Chase', None, 'chase1'),

        'die1': (False, 'SPR_BOSS_DIE1', 15, None, 'A_DeathScream', 'die2'),
        'die2': (False, 'SPR_BOSS_DIE2', 15, None, None,            'die3'),
        'die3': (False, 'SPR_BOSS_DIE3', 15, None, None,            'die4'),
        'die4': (False, 'SPR_BOSS_DEAD',  0, None, None,            'die4'),

        'shoot1': (False, 'SPR_BOSS_SHOOT1', 30, None, None,      'shoot2'),
        'shoot2': (False, 'SPR_BOSS_SHOOT2', 10, None, 'T_Shoot', 'shoot3'),
        'shoot3': (False, 'SPR_BOSS_SHOOT3', 10, None, 'T_Shoot', 'shoot4'),
        'shoot4': (False, 'SPR_BOSS_SHOOT2', 10, None, 'T_Shoot', 'shoot5'),
        'shoot5': (False, 'SPR_BOSS_SHOOT3', 10, None, 'T_Shoot', 'shoot6'),
        'shoot6': (False, 'SPR_BOSS_SHOOT2', 10, None, 'T_Shoot', 'shoot7'),
        'shoot7': (False, 'SPR_BOSS_SHOOT3', 10, None, 'T_Shoot', 'shoot8'),
        'shoot8': (False, 'SPR_BOSS_SHOOT1', 10, None, None,      'chase1'),
    },
    'hitler': {
        'chase1':  (False, 'SPR_HITLER_W1', 6, 'T_Chase', None, 'chase1s'),
        'chase1s': (False, 'SPR_HITLER_W1', 4, None,      None, 'chase2'),
        'chase2':  (False, 'SPR_HITLER_W2', 2, 'T_Chase', None, 'chase3'),
        'chase3':  (False, 'SPR_HITLER_W3', 6, 'T_Chase', None, 'chase3s'),
        'chase3s': (False, 'SPR_HITLER_W3', 4, None,      None, 'chase4'),
        'chase4':  (False, 'SPR_HITLER_W4', 2, 'T_Chase', None, 'chase1'),

        'deathcam': (False, 'SPR_HITLER_W1', 10, None, None, 'die1'),

        'die1':  (False, 'SPR_HITLER_W1',    1, None, 'A_DeathScream',   'die2'),
        'die2':  (False, 'SPR_HITLER_W1',   10, None, None,              'die3'),
        'die3':  (False, 'SPR_HITLER_DIE1', 10, None, 'A_Slurpie',       'die4'),
        'die4':  (False, 'SPR_HITLER_DIE2', 10, None, None,              'die5'),
        'die5':  (False, 'SPR_HITLER_DIE3', 10, None, None,              'die6'),
        'die6':  (False, 'SPR_HITLER_DIE4', 10, None, None,              'die7'),
        'die7':  (False, 'SPR_HITLER_DIE5', 10, None, None,              'die8'),
        'die8':  (False, 'SPR_HITLER_DIE6', 10, None, None,              'die9'),
        'die9':  (False, 'SPR_HITLER_DIE7', 10, None, None,              'die10'),
        'die10': (False, 'SPR_HITLER_DEAD', 20, None, 'A_StartDeathCam', 'die10'),

        'shoot1': (False, 'SPR_HITLER_SHOOT1', 30, None, None,      'shoot2'),
        'shoot2': (False, 'SPR_HITLER_SHOOT2', 10, None, 'T_Shoot', 'shoot3'),
        'shoot3': (False, 'SPR_HITLER_SHOOT3', 10, None, 'T_Shoot', 'shoot4'),
        'shoot4': (False, 'SPR_HITLER_SHOOT2', 10, None, 'T_Shoot', 'shoot5'),
        'shoot5': (False, 'SPR_HITLER_SHOOT3', 10, None, 'T_Shoot', 'shoot6'),
        'shoot6': (False, 'SPR_HITLER_SHOOT2', 10, None, 'T_Shoot', 'chase1'),
    },
    'mecha_hitler': {
        'stand': (False, 'SPR_MECHA_W1', 0, 'T_Stand', None, 'stand'),

        'chase1':  (False, 'SPR_MECHA_W1', 10, 'T_Chase', 'A_MechaSound', 'chase1s'),
        'chase1s': (False, 'SPR_MECHA_W1',  6, None,      None,           'chase2'),
        'chase2':  (False, 'SPR_MECHA_W2',  8, 'T_Chase', None,           'chase3'),
        'chase3':  (False, 'SPR_MECHA_W3', 10, 'T_Chase', 'A_MechaSound', 'chase3s'),
        'chase3s': (False, 'SPR_MECHA_W3',  6, None,      None,           'chase4'),
        'chase4':  (False, 'SPR_MECHA_W4',  8, 'T_Chase', None,           'chase1'),

        'die1': (False, 'SPR_MECHA_DIE1', 10, None, 'A_DeathScream', 'die2'),
        'die2': (False, 'SPR_MECHA_DIE2', 10, None, None,            'die3'),
        'die3': (False, 'SPR_MECHA_DIE3', 10, None, 'A_HitlerMorph', 'die4'),
        'die4': (False, 'SPR_MECHA_DEAD',  0, None, None,            'die4'),

        'shoot1': (False, 'SPR_MECHA_SHOOT1', 30, None, None,      'shoot2'),
        'shoot2': (False, 'SPR_MECHA_SHOOT2', 10, None, 'T_Shoot', 'shoot3'),
        'shoot3': (False, 'SPR_MECHA_SHOOT3', 10, None, 'T_Shoot', 'shoot4'),
        'shoot4': (False, 'SPR_MECHA_SHOOT2', 10, None, 'T_Shoot', 'shoot5'),
        'shoot5': (False, 'SPR_MECHA_SHOOT3', 10, None, 'T_Shoot', 'shoot6'),
        'shoot6': (False, 'SPR_MECHA_SHOOT2', 10, None, 'T_Shoot', 'chase1'),
    },
    'mutant': {
        'stand': (True, 'SPR_MUT_S_1', 0, 'T_Stand', None, 'stand'),

        'path1':  (True, 'SPR_MUT_W1_1', 20, 'T_Path', None, 'path1s'),
        'path1s': (True, 'SPR_MUT_W1_1',  5, None,     None, 'path2'),
        'path2':  (True, 'SPR_MUT_W2_1', 15, 'T_Path', None, 'path3'),
        'path3':  (True, 'SPR_MUT_W3_1', 20, 'T_Path', None, 'path3s'),
        'path3s': (True, 'SPR_MUT_W3_1',  5, None,     None, 'path4'),
        'path4':  (True, 'SPR_MUT_W4_1', 15, 'T_Path', None, 'path1'),

        'pain':  (False, 'SPR_MUT_PAIN_1', 10, None, None, 'chase1'),
        'pain1': (False, 'SPR_MUT_PAIN_2', 10, None, None, 'chase1'),

        'shoot1': (False, 'SPR_MUT_SHOOT1',  6, None, 'T_Shoot', 'shoot2'),
        'shoot2': (False, 'SPR_MUT_SHOOT2', 20, None, None,      'shoot3'),
        'shoot3': (False, 'SPR_MUT_SHOOT3', 10, None, 'T_Shoot', 'shoot4'),
        'shoot4': (False, 'SPR_MUT_SHOOT4', 20, None, None,      'chase1'),

        'chase1':  (True, 'SPR_MUT_W1_1', 10, 'T_Chase', None, 'chase1s'),
        'chase1s': (True, 'SPR_MUT_W1_1',  3, None,      None, 'chase2'),
        'chase2':  (True, 'SPR_MUT_W2_1',  8, 'T_Chase', None, 'chase3'),
        'chase3':  (True, 'SPR_MUT_W3_1', 10, 'T_Chase', None, 'chase3s'),
        'chase3s': (True, 'SPR_MUT_W3_1',  3, None,      None, 'chase4'),
        'chase4':  (True, 'SPR_MUT_W4_1',  8, 'T_Chase', None, 'chase1'),

        'die1': (False, 'SPR_MUT_DIE_1', 7, None, 'A_DeathScream', 'die2'),
        'die2': (False, 'SPR_MUT_DIE_2', 7, None, None,            'die3'),
        'die3': (False, 'SPR_MUT_DIE_3', 7, None, None,            'die4'),
        'die4': (False, 'SPR_MUT_DIE_4', 7, None, None,            'die5'),
        'die5': (False, 'SPR_MUT_DEAD',  0, None, None,            'die5'),
    },
    'needle': {
        'fly1': (False, 'SPR_HYPO1', 6, 'T_Projectile', None, 'fly2'),
        'fly2': (False, 'SPR_HYPO2', 6, 'T_Projectile', None, 'fly3'),
        'fly3': (False, 'SPR_HYPO3', 6, 'T_Projectile', None, 'fly4'),
        'fly4': (False, 'SPR_HYPO4', 6, 'T_Projectile', None, 'fly1'),
    },
    'officer': {
        'stand': (True, 'SPR_OFC_S_1', 0, 'T_Stand', None, 'stand'),

        'path1':  (True, 'SPR_OFC_W1_1', 20, 'T_Path', None, 'path1s'),
        'path1s': (True, 'SPR_OFC_W1_1',  5, None,     None, 'path2'),
        'path2':  (True, 'SPR_OFC_W2_1', 15, 'T_Path', None, 'path3'),
        'path3':  (True, 'SPR_OFC_W3_1', 20, 'T_Path', None, 'path3s'),
        'path3s': (True, 'SPR_OFC_W3_1',  5, None,     None, 'path4'),
        'path4':  (True, 'SPR_OFC_W4_1', 15, 'T_Path', None, 'path1'),

        'pain':  (False, 'SPR_OFC_PAIN_1', 10, None, None, 'chase1'),
        'pain1': (False, 'SPR_OFC_PAIN_2', 10, None, None, 'chase1'),

        'shoot1': (False, 'SPR_OFC_SHOOT1',  6, None, None,      'shoot2'),
        'shoot2': (False, 'SPR_OFC_SHOOT2', 20, None, 'T_Shoot', 'shoot3'),
        'shoot3': (False, 'SPR_OFC_SHOOT3', 10, None, None,      'chase1'),

        'chase1':  (True, 'SPR_OFC_W1_1', 10, 'T_Chase', None, 'chase1s'),
        'chase1s': (True, 'SPR_OFC_W1_1',  3, None,      None, 'chase2'),
        'chase2':  (True, 'SPR_OFC_W2_1',  8, 'T_Chase', None, 'chase3'),
        'chase3':  (True, 'SPR_OFC_W3_1', 10, 'T_Chase', None, 'chase3s'),
        'chase3s': (True, 'SPR_OFC_W3_1',  3, None,      None, 'chase4'),
        'chase4':  (True, 'SPR_OFC_W4_1',  8, 'T_Chase', None, 'chase1'),

        'die1': (False, 'SPR_OFC_DIE_1', 11, None, 'A_DeathScream', 'die2'),
        'die2': (False, 'SPR_OFC_DIE_2', 11, None, None,            'die3'),
        'die3': (False, 'SPR_OFC_DIE_3', 11, None, None,            'die4'),
        'die4': (False, 'SPR_OFC_DIE_4', 11, None, None,            'die5'),
        'die5': (False, 'SPR_OFC_DEAD',   0, None, None,            'die5'),
    },
    'otto': {
        'stand': (False, 'SPR_GIFT_W1', 0, 'T_Stand', None, 'stand'),

        'chase1':  (False, 'SPR_GIFT_W1', 10, 'T_Gift', None, 'chase1s'),
        'chase1s': (False, 'SPR_GIFT_W1',  3, None,     None, 'chase2'),
        'chase2':  (False, 'SPR_GIFT_W2',  8, 'T_Gift', None, 'chase3'),
        'chase3':  (False, 'SPR_GIFT_W3', 10, 'T_Gift', None, 'chase3s'),
        'chase3s': (False, 'SPR_GIFT_W3',  3, None,     None, 'chase4'),
        'chase4':  (False, 'SPR_GIFT_W4',  8, 'T_Gift', None, 'chase1'),

        'deathcam': (False, 'SPR_GIFT_W1', 1, None, None, 'die1'),

        'die1': (False, 'SPR_GIFT_W1',    1, None, 'A_DeathScream',   'die2'),
        'die2': (False, 'SPR_GIFT_W1',   10, None, None,              'die3'),
        'die3': (False, 'SPR_GIFT_DIE1', 10, None, None,              'die4'),
        'die4': (False, 'SPR_GIFT_DIE2', 10, None, None,              'die5'),
        'die5': (False, 'SPR_GIFT_DIE3', 10, None, None,              'die6'),
        'die6': (False, 'SPR_GIFT_DEAD', 20, None, 'A_StartDeathCam', 'die6'),

        'shoot1': (False, 'SPR_GIFT_SHOOT1', 30, None, None,          'shoot2'),
        'shoot2': (False, 'SPR_GIFT_SHOOT2', 10, None, 'T_GiftThrow', 'chase1'),
    },
    'robed_fake': {
        'stand': (False, 'SPR_FAKE_W1', 0, 'T_Stand', None, 'stand'),

        'chase1':  (False, 'SPR_FAKE_W1', 10, 'T_Fake', None, 'chase1s'),
        'chase1s': (False, 'SPR_FAKE_W1',  3, None,     None, 'chase2'),
        'chase2':  (False, 'SPR_FAKE_W2',  8, 'T_Fake', None, 'chase3'),
        'chase3':  (False, 'SPR_FAKE_W3', 10, 'T_Fake', None, 'chase3s'),
        'chase3s': (False, 'SPR_FAKE_W3',  3, None,     None, 'chase4'),
        'chase4':  (False, 'SPR_FAKE_W4',  8, 'T_Fake', None, 'chase1'),

        'die1': (False, 'SPR_FAKE_DIE1', 10, None, 'A_DeathScream', 'die2'),
        'die2': (False, 'SPR_FAKE_DIE2', 10, None, None,            'die3'),
        'die3': (False, 'SPR_FAKE_DIE3', 10, None, None,            'die4'),
        'die4': (False, 'SPR_FAKE_DIE4', 10, None, None,            'die5'),
        'die5': (False, 'SPR_FAKE_DIE5', 10, None, None,            'die6'),
        'die6': (False, 'SPR_FAKE_DEAD',  0, None, None,            'die6'),

        'shoot1': (False, 'SPR_FAKE_SHOOT', 8, None, 'T_FakeFire', 'shoot2'),
        'shoot2': (False, 'SPR_FAKE_SHOOT', 8, None, 'T_FakeFire', 'shoot3'),
        'shoot3': (False, 'SPR_FAKE_SHOOT', 8, None, 'T_FakeFire', 'shoot4'),
        'shoot4': (False, 'SPR_FAKE_SHOOT', 8, None, 'T_FakeFire', 'shoot5'),
        'shoot5': (False, 'SPR_FAKE_SHOOT', 8, None, 'T_FakeFire', 'shoot6'),
        'shoot6': (False, 'SPR_FAKE_SHOOT', 8, None, 'T_FakeFire', 'shoot7'),
        'shoot7': (False, 'SPR_FAKE_SHOOT', 8, None, 'T_FakeFire', 'shoot8'),
        'shoot8': (False, 'SPR_FAKE_SHOOT', 8, None, 'T_FakeFire', 'shoot9'),
        'shoot9': (False, 'SPR_FAKE_SHOOT', 8, None, None,         'chase1'),
    },
    'rocket': {
        'fly': (True, 'SPR_ROCKET_1', 3, 'T_Projectile', 'A_Smoke', 'fly'),
    },
    'schabbs': {
        'stand': (False, 'SPR_SCHABB_W1',0, 'T_Stand', None, 'stand'),

        'chase1':  (False, 'SPR_SCHABB_W1', 10, 'T_Schabb', None, 'chase1s'),
        'chase1s': (False, 'SPR_SCHABB_W1',  3, None,       None, 'chase2'),
        'chase2':  (False, 'SPR_SCHABB_W2',  8, 'T_Schabb', None, 'chase3'),
        'chase3':  (False, 'SPR_SCHABB_W3', 10, 'T_Schabb', None, 'chase3s'),
        'chase3s': (False, 'SPR_SCHABB_W3',  3, None,       None, 'chase4'),
        'chase4':  (False, 'SPR_SCHABB_W4',  8, 'T_Schabb', None, 'chase1'),

        'deathcam': (False, 'SPR_SCHABB_W1', 1, None, 'die1'),

        'die1': (False, 'SPR_SCHABB_W1',   10, None, 'A_DeathScream',   'die2'),
        'die2': (False, 'SPR_SCHABB_W1',   10, None, None,              'die3'),
        'die3': (False, 'SPR_SCHABB_DIE1', 10, None, None,              'die4'),
        'die4': (False, 'SPR_SCHABB_DIE2', 10, None, None,              'die5'),
        'die5': (False, 'SPR_SCHABB_DIE3', 10, None, None,              'die6'),
        'die6': (False, 'SPR_SCHABB_DEAD', 20, None, 'A_StartDeathCam', 'die6'),

        'shoot1': (False, 'SPR_SCHABB_SHOOT1',30, None, 'shoot2'),
        'shoot2': (False, 'SPR_SCHABB_SHOOT2',10, None,'T_SchabbThrow', 'chase1'),
    },
    'smoke': {
        'die1': (False, 'SPR_SMOKE_1', 3, None, None, 'die2'),
        'die2': (False, 'SPR_SMOKE_2', 3, None, None, 'die3'),
        'die3': (False, 'SPR_SMOKE_3', 3, None, None, 'die4'),
        'die4': (False, 'SPR_SMOKE_4', 3, None, None, None),
    },
    'ss': {
        'stand': (True, 'SPR_SS_S_1', 0, 'T_Stand', None, 'stand'),

        'path1':  (True, 'SPR_SS_W1_1', 20, 'T_Path', None, 'path1s'),
        'path1s': (True, 'SPR_SS_W1_1',  5, None,     None, 'path2'),
        'path2':  (True, 'SPR_SS_W2_1', 15, 'T_Path', None, 'path3'),
        'path3':  (True, 'SPR_SS_W3_1', 20, 'T_Path', None, 'path3s'),
        'path3s': (True, 'SPR_SS_W3_1',  5, None,     None, 'path4'),
        'path4':  (True, 'SPR_SS_W4_1', 15, 'T_Path', None, 'path1'),

        'pain':  (False, 'SPR_SS_PAIN_1', 10, None, None, 'chase1'),
        'pain1': (False, 'SPR_SS_PAIN_2', 10, None, None, 'chase1'),

        'shoot1': (False, 'SPR_SS_SHOOT1', 20, None, None,      'shoot2'),
        'shoot2': (False, 'SPR_SS_SHOOT2', 20, None, 'T_Shoot', 'shoot3'),
        'shoot3': (False, 'SPR_SS_SHOOT3', 10, None, None,      'shoot4'),
        'shoot4': (False, 'SPR_SS_SHOOT2', 10, None, 'T_Shoot', 'shoot5'),
        'shoot5': (False, 'SPR_SS_SHOOT3', 10, None, None,      'shoot6'),
        'shoot6': (False, 'SPR_SS_SHOOT2', 10, None, 'T_Shoot', 'shoot7'),
        'shoot7': (False, 'SPR_SS_SHOOT3', 10, None, None,      'shoot8'),
        'shoot8': (False, 'SPR_SS_SHOOT2', 10, None, 'T_Shoot', 'shoot9'),
        'shoot9': (False, 'SPR_SS_SHOOT3', 10, None, None,      'chase1'),

        'chase1':  (True, 'SPR_SS_W1_1', 10, 'T_Chase', None, 'chase1s'),
        'chase1s': (True, 'SPR_SS_W1_1',  3, None,      None, 'chase2'),
        'chase2':  (True, 'SPR_SS_W2_1',  8, 'T_Chase', None, 'chase3'),
        'chase3':  (True, 'SPR_SS_W3_1', 10, 'T_Chase', None, 'chase3s'),
        'chase3s': (True, 'SPR_SS_W3_1',  3, None,      None, 'chase4'),
        'chase4':  (True, 'SPR_SS_W4_1',  8, 'T_Chase', None, 'chase1'),

        'die1': (False, 'SPR_SS_DIE_1', 15, None, 'A_DeathScream', 'die2'),
        'die2': (False, 'SPR_SS_DIE_2', 15, None, None,            'die3'),
        'die3': (False, 'SPR_SS_DIE_3', 15, None, None,            'die4'),
        'die4': (False, 'SPR_SS_DEAD',   0, None, None,            'die4'),
    },
}
