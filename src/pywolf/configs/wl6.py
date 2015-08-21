'''
@author: Andrea Zoppi
'''

from pywolf.audio import SAMPLE_RATE
from pywolf.graphics import rgbpalette_flatten
from pywolf.persistence import jascpal_read


def _load_flat_jascpal(path):
    with open(path, 'rt') as palette_stream:
        return rgbpalette_flatten(jascpal_read(palette_stream))


GRAPHICS_PARTITIONS_MAP = {
    # 'partition': (start_index, count)
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


GRAPHICS_PALETTE_MAP = {
    ...: _load_flat_jascpal('../data/palettes/wolf.pal')
}


SOUNDS_FREQUENCY = SAMPLE_RATE
