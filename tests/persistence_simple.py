'''
@author: Andrea Zoppi
'''

import unittest
import sys
import logging

import pywolf.persistence
import pywolf.configs.wl6


REFERENCE_PALETTE = (
    (0, 0, 0),
    (0, 0, 168),
    (0, 168, 0),
    (0, 168, 168),
    (168, 0, 0),
    (168, 0, 168),
    (168, 84, 0),
    (168, 168, 168),
    (84, 84, 84),
    (84, 84, 252),
    (84, 252, 84),
    (84, 252, 252),
    (252, 84, 84),
    (252, 84, 252),
    (252, 252, 84),
    (252, 252, 252),
    (236, 236, 236),
    (220, 220, 220),
    (208, 208, 208),
    (192, 192, 192),
    (180, 180, 180),
    (168, 168, 168),
    (152, 152, 152),
    (140, 140, 140),
    (124, 124, 124),
    (112, 112, 112),
    (100, 100, 100),
    (84, 84, 84),
    (72, 72, 72),
    (56, 56, 56),
    (44, 44, 44),
    (32, 32, 32),
    (252, 0, 0),
    (236, 0, 0),
    (224, 0, 0),
    (212, 0, 0),
    (200, 0, 0),
    (188, 0, 0),
    (176, 0, 0),
    (164, 0, 0),
    (152, 0, 0),
    (136, 0, 0),
    (124, 0, 0),
    (112, 0, 0),
    (100, 0, 0),
    (88, 0, 0),
    (76, 0, 0),
    (64, 0, 0),
    (252, 216, 216),
    (252, 184, 184),
    (252, 156, 156),
    (252, 124, 124),
    (252, 92, 92),
    (252, 64, 64),
    (252, 32, 32),
    (252, 0, 0),
    (252, 168, 92),
    (252, 152, 64),
    (252, 136, 32),
    (252, 120, 0),
    (228, 108, 0),
    (204, 96, 0),
    (180, 84, 0),
    (156, 76, 0),
    (252, 252, 216),
    (252, 252, 184),
    (252, 252, 156),
    (252, 252, 124),
    (252, 248, 92),
    (252, 244, 64),
    (252, 244, 32),
    (252, 244, 0),
    (228, 216, 0),
    (204, 196, 0),
    (180, 172, 0),
    (156, 156, 0),
    (132, 132, 0),
    (112, 108, 0),
    (88, 84, 0),
    (64, 64, 0),
    (208, 252, 92),
    (196, 252, 64),
    (180, 252, 32),
    (160, 252, 0),
    (144, 228, 0),
    (128, 204, 0),
    (116, 180, 0),
    (96, 156, 0),
    (216, 252, 216),
    (188, 252, 184),
    (156, 252, 156),
    (128, 252, 124),
    (96, 252, 92),
    (64, 252, 64),
    (32, 252, 32),
    (0, 252, 0),
    (0, 252, 0),
    (0, 236, 0),
    (0, 224, 0),
    (0, 212, 0),
    (4, 200, 0),
    (4, 188, 0),
    (4, 176, 0),
    (4, 164, 0),
    (4, 152, 0),
    (4, 136, 0),
    (4, 124, 0),
    (4, 112, 0),
    (4, 100, 0),
    (4, 88, 0),
    (4, 76, 0),
    (4, 64, 0),
    (216, 252, 252),
    (184, 252, 252),
    (156, 252, 252),
    (124, 252, 248),
    (92, 252, 252),
    (64, 252, 252),
    (32, 252, 252),
    (0, 252, 252),
    (0, 228, 228),
    (0, 204, 204),
    (0, 180, 180),
    (0, 156, 156),
    (0, 132, 132),
    (0, 112, 112),
    (0, 88, 88),
    (0, 64, 64),
    (92, 188, 252),
    (64, 176, 252),
    (32, 168, 252),
    (0, 156, 252),
    (0, 140, 228),
    (0, 124, 204),
    (0, 108, 180),
    (0, 92, 156),
    (216, 216, 252),
    (184, 188, 252),
    (156, 156, 252),
    (124, 128, 252),
    (92, 96, 252),
    (64, 64, 252),
    (32, 36, 252),
    (0, 4, 252),
    (0, 0, 252),
    (0, 0, 236),
    (0, 0, 224),
    (0, 0, 212),
    (0, 0, 200),
    (0, 0, 188),
    (0, 0, 176),
    (0, 0, 164),
    (0, 0, 152),
    (0, 0, 136),
    (0, 0, 124),
    (0, 0, 112),
    (0, 0, 100),
    (0, 0, 88),
    (0, 0, 76),
    (0, 0, 64),
    (40, 40, 40),
    (252, 224, 52),
    (252, 212, 36),
    (252, 204, 24),
    (252, 192, 8),
    (252, 180, 0),
    (180, 32, 252),
    (168, 0, 252),
    (152, 0, 228),
    (128, 0, 204),
    (116, 0, 180),
    (96, 0, 156),
    (80, 0, 132),
    (68, 0, 112),
    (52, 0, 88),
    (40, 0, 64),
    (252, 216, 252),
    (252, 184, 252),
    (252, 156, 252),
    (252, 124, 252),
    (252, 92, 252),
    (252, 64, 252),
    (252, 32, 252),
    (252, 0, 252),
    (224, 0, 228),
    (200, 0, 204),
    (180, 0, 180),
    (156, 0, 156),
    (132, 0, 132),
    (108, 0, 112),
    (88, 0, 88),
    (64, 0, 64),
    (252, 232, 220),
    (252, 224, 208),
    (252, 216, 196),
    (252, 212, 188),
    (252, 204, 176),
    (252, 196, 164),
    (252, 188, 156),
    (252, 184, 144),
    (252, 176, 128),
    (252, 164, 112),
    (252, 156, 96),
    (240, 148, 92),
    (232, 140, 88),
    (220, 136, 84),
    (208, 128, 80),
    (200, 124, 76),
    (188, 120, 72),
    (180, 112, 68),
    (168, 104, 64),
    (160, 100, 60),
    (156, 96, 56),
    (144, 92, 52),
    (136, 88, 48),
    (128, 80, 44),
    (116, 76, 40),
    (108, 72, 36),
    (92, 64, 32),
    (84, 60, 28),
    (72, 56, 24),
    (64, 48, 24),
    (56, 44, 20),
    (40, 32, 12),
    (96, 0, 100),
    (0, 100, 100),
    (0, 96, 96),
    (0, 0, 28),
    (0, 0, 44),
    (48, 36, 16),
    (72, 0, 72),
    (80, 0, 80),
    (0, 0, 52),
    (28, 28, 28),
    (76, 76, 76),
    (92, 92, 92),
    (64, 64, 64),
    (48, 48, 48),
    (52, 52, 52),
    (216, 244, 244),
    (184, 232, 232),
    (156, 220, 220),
    (116, 200, 200),
    (72, 192, 192),
    (32, 180, 180),
    (32, 176, 176),
    (0, 164, 164),
    (0, 152, 152),
    (0, 140, 140),
    (0, 132, 132),
    (0, 124, 124),
    (0, 120, 120),
    (0, 116, 116),
    (0, 112, 112),
    (0, 108, 108),
    (152, 0, 136),
)


class Test(unittest.TestCase):

    def setUp(self):
        logger = logging.getLogger()
        stdout_handler = logging.StreamHandler(sys.stdout)
        stdout_handler.setLevel(logging.DEBUG)
        logger.addHandler(stdout_handler)
        logger.setLevel(logging.DEBUG)
        self._stdout_handler = stdout_handler

    def tearDown(self):
        logger = logging.getLogger()
        logger.removeHandler(self._stdout_handler)

    def testPalette(self):
        logger = logging.getLogger()
        logger.info('testPalette')
        with open(r'../data/palettes/wolf.pal', 'rt') as jascpal_file:
            palette = pywolf.persistence.jascpal_read(jascpal_file)
        assert len(palette) == len(REFERENCE_PALETTE)
        for pc, rc in zip(palette, REFERENCE_PALETTE):
            assert len(pc) == len(rc)
            for pv, rv in zip(pc, rc):
                assert pv == rv

        with open(r'./outputs/wolf.pal', 'wt') as jascpal_file:
            pywolf.persistence.jascpal_write(jascpal_file, palette)

    def testVSwap(self):
        logger = logging.getLogger()
        logger.info('testVSwap')

        vswap_chunks_handler = pywolf.persistence.PrecachedVSwapChunksHandler()
        with open(r'../data/wl6/vswap.wl6', 'rb') as data_file:
            vswap_chunks_handler.load(data_file)

        for i, chunk in enumerate(vswap_chunks_handler):
            with open(r'./outputs/vswap_{}.chunk'.format(i), 'wb') as chunk_file:
                chunk_file.write(chunk)

    def testAudio(self):
        logger = logging.getLogger()
        logger.info('testAudio')

        audio_chunks_handler = pywolf.persistence.PrecachedAudioChunksHandler()
        with open(r'../data/wl6/audiohed.wl6', 'rb') as (header_file
        ),   open(r'../data/wl6/audiot.wl6', 'rb') as data_file:
            audio_chunks_handler.load(data_file, header_file)

        for i, item in enumerate(audio_chunks_handler):
            header, chunk = item
            with open(r'./outputs/audio_{}.chunk'.format(i), 'wb') as chunk_file:
                chunk_file.write(chunk)

    def testGraphics(self):
        logger = logging.getLogger()
        logger.info('testGraphics')

        graphics_chunks_handler = pywolf.persistence.PrecachedGraphicsChunksHandler()
        with open(r'../data/wl6/vgahead.wl6', 'rb') as (header_file
        ),   open(r'../data/wl6/vgagraph.wl6', 'rb') as (data_file
        ),   open(r'../data/wl6/vgadict.wl6', 'rb') as huffman_file:
            graphics_chunks_handler.load(data_file, header_file, huffman_file,
                                         pywolf.configs.wl6.GRAPHICS_PARTITIONS_MAP)

        for i, chunk in enumerate(graphics_chunks_handler):
            with open(r'./outputs/graphics_{}.chunk'.format(i), 'wb') as chunk_file:
                chunk_file.write(chunk)

    def testMap(self):
        logger = logging.getLogger()
        logger.info('testMap')

        map_chunks_handler = pywolf.persistence.PrecachedMapChunksHandler()
        with open(r'../data/wl6/maphead.wl6', 'rb') as (header_file
        ),   open(r'../data/wl6/gamemaps.wl6', 'rb') as data_file:
            map_chunks_handler.load(data_file, header_file)

        for i, item in enumerate(map_chunks_handler):
            header, planes = item
            with open(r'./outputs/map_{}.chunk'.format(i), 'wb') as chunk_file:
                for plane in planes:
                    chunk_file.write(plane)


if __name__ == "__main__":
    #import sys;sys.argv = ['', 'Test.testName']
    unittest.main()


