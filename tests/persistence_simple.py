'''
@author: Andrea Zoppi
'''

import logging
import sys
import unittest

import pywolf.configs.wl6
import pywolf.persistence


REFERENCE_PALETTE = pywolf.configs.wl6.GRAPHICS_PALETTE


class Test(unittest.TestCase):

    def setUp(self):
        logger = logging.getLogger()
        stdout_handler = logging.StreamHandler(sys.stdout)
        stdout_handler.setLevel(logging.DEBUG)
        logger.addHandler(stdout_handler)
        logger.setLevel(logging.DEBUG)
        logger.info('-' * 80)
        self._stdout_handler = stdout_handler

    def tearDown(self):
        logger = logging.getLogger()
        logger.removeHandler(self._stdout_handler)

    def testVSwap(self):
        logger = logging.getLogger()
        logger.info('testVSwap')

        vswap_chunks_handler = pywolf.persistence.VSwapChunksHandler()
        with open(r'../data/wl6/vswap.wl6', 'rb') as data_file:
            vswap_chunks_handler.load(data_file)
            vswap_chunks_handler = pywolf.persistence.PrecachedChunksHandler(vswap_chunks_handler)

        count = len(vswap_chunks_handler)
        for i, chunk in enumerate(vswap_chunks_handler):
            path = r'./outputs/vswap_{}.bin'.format(i)
            logger.info('VSwap chunk [%d/%d]: %r, 0x%X bytes', (i + 1), count, path, len(chunk))
            with open(path, 'wb') as chunk_file:
                chunk_file.write(chunk)

    def testAudio(self):
        logger = logging.getLogger()
        logger.info('testAudio')

        audio_chunks_handler = pywolf.persistence.AudioChunksHandler()
        with open(r'../data/wl6/audiohed.wl6', 'rb') as (header_file
        ),   open(r'../data/wl6/audiot.wl6', 'rb') as data_file:
            audio_chunks_handler.load(data_file, header_file)
            audio_chunks_handler = pywolf.persistence.PrecachedChunksHandler(audio_chunks_handler)

        count = len(audio_chunks_handler)
        for i, chunk in enumerate(audio_chunks_handler):
            path = r'./outputs/audio_{}.bin'.format(i)
            logger.info('Audio chunk [%d/%d]: %r, 0x%X bytes', (i + 1), count, path, len(chunk))
            with open(path, 'wb') as chunk_file:
                chunk_file.write(chunk)

    def testGraphics(self):
        logger = logging.getLogger()
        logger.info('testGraphics')

        graphics_chunks_handler = pywolf.persistence.GraphicsChunksHandler()
        with open(r'../data/wl6/vgahead.wl6', 'rb') as (header_file
        ),   open(r'../data/wl6/vgagraph.wl6', 'rb') as (data_file
        ),   open(r'../data/wl6/vgadict.wl6', 'rb') as huffman_file:
            graphics_chunks_handler.load(data_file, header_file, huffman_file,
                                         pywolf.configs.wl6.GRAPHICS_PARTITIONS_MAP)
            graphics_chunks_handler = pywolf.persistence.PrecachedChunksHandler(graphics_chunks_handler)

        count = len(graphics_chunks_handler)
        for i, chunk in enumerate(graphics_chunks_handler):
            path = r'./outputs/graphics_{}.bin'.format(i)
            logger.info('Graphics chunk [%d/%d]: %r, 0x%X bytes', (i + 1), count, path, len(chunk))
            with open(path, 'wb') as chunk_file:
                chunk_file.write(chunk)

    def testTileMaps(self):
        logger = logging.getLogger()
        logger.info('testTileMaps')

        tilemap_chunks_handler = pywolf.persistence.MapChunksHandler()
        with open(r'../data/wl6/maphead.wl6', 'rb') as (header_file
        ),   open(r'../data/wl6/gamemaps.wl6', 'rb') as data_file:
            tilemap_chunks_handler.load(data_file, header_file)
            tilemap_chunks_handler = pywolf.persistence.PrecachedChunksHandler(tilemap_chunks_handler)

        count = len(tilemap_chunks_handler)
        for i, item in enumerate(tilemap_chunks_handler):
            header, planes = item
            logger.info('TileMap chunk [%d/%d]:', (i + 1), count)
            if header is not None:
                header_bytes = header.to_bytes()
                path = r'./outputs/tilemap_{}_header.bin'.format(i)
                logger.info('... header: %r, 0x%X', path, len(header_bytes))
                with open(path, 'wb') as header_file:
                    header_file.write(header_bytes)

                for j, plane in enumerate(planes):
                    path = r'./outputs/tilemap_{}_plane{}.bin'.format(i, j)
                    logger.info('... plane [%d/%d]: %r, 0x%X bytes', (j + 1), len(planes), path, len(plane))
                    with open(path, 'wb') as chunk_file:
                        chunk_file.write(plane)


if __name__ == "__main__":
    # import sys;sys.argv = ['', 'Test.testName']
    unittest.main()


