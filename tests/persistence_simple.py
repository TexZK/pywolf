'''
@author: Andrea Zoppi
'''

import unittest
import sys
import logging

import pywolf.persistence
import pywolf.configs.wl6


REFERENCE_PALETTE = pywolf.configs.wl6.GRAPHICS_PALETTE


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


