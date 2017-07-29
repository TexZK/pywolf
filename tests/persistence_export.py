import logging
import os
import sys
import unittest

import pywolf.persistence

import pywolf.configs.wl6


class Test(unittest.TestCase):

    AUDIOHED_PATH = r'../data/wl6/audiohed.wl6'
    AUDIOT_PATH = r'../data/wl6/audiot.wl6'

    MAPHEAD_PATH = r'../data/wl6/maphead.wl6'
    GAMEMAPS_PATH = r'../data/wl6/gamemaps.wl6'

    VGAHEAD_PATH = r'../data/wl6/vgahead.wl6'
    VGADICT_PATH = r'../data/wl6/vgadict.wl6'
    VGAGRAPH_PATH = r'../data/wl6/vgagraph.wl6'

    VSWAP_PATH = r'../data/wl6/vswap.wl6'

    OUTPUT_FOLDER = r'./outputs/persistence_tests'

    @classmethod
    def setUpClass(cls):
        super(Test, cls).setUpClass()
        os.makedirs(cls.OUTPUT_FOLDER, exist_ok=True)

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
        with open(self.VSWAP_PATH, 'rb') as data_file:
            vswap_chunks_handler.load(data_file)
            vswap_chunks_handler = pywolf.persistence.PrecachedChunksHandler(vswap_chunks_handler)

        count = len(vswap_chunks_handler)
        for i, chunk in enumerate(vswap_chunks_handler):
            path = r'{}/vswap_{:04d}.bin'.format(self.OUTPUT_FOLDER, i)
            logger.info('VSwap chunk [%4d/%4d]: %r, 0x%04X bytes', (i + 1), count, path, len(chunk))
            with open(path, 'wb') as chunk_file:
                chunk_file.write(chunk)

    def testAudio(self):
        logger = logging.getLogger()
        logger.info('testAudio')

        audio_chunks_handler = pywolf.persistence.AudioChunksHandler()
        with open(self.AUDIOHED_PATH, 'rb') as (header_file
        ), open(self.AUDIOT_PATH, 'rb') as data_file:
            audio_chunks_handler.load(data_file, header_file)
            audio_chunks_handler = pywolf.persistence.PrecachedChunksHandler(audio_chunks_handler)

        count = len(audio_chunks_handler)
        for i, chunk in enumerate(audio_chunks_handler):
            path = r'{}/audio_{:04d}.bin'.format(self.OUTPUT_FOLDER, i)
            logger.info('Audio chunk [%4d/%4d]: %r, 0x%04X bytes', (i + 1), count, path, len(chunk))
            with open(path, 'wb') as chunk_file:
                chunk_file.write(chunk)

    def testGraphics(self):
        logger = logging.getLogger()
        logger.info('testGraphics')

        graphics_chunks_handler = pywolf.persistence.GraphicsChunksHandler()
        with open(self.VGAHEAD_PATH, 'rb') as (header_file
        ), open(self.VGAGRAPH_PATH, 'rb') as (data_file
        ), open(self.VGADICT_PATH, 'rb') as huffman_file:
            graphics_chunks_handler.load(data_file, header_file, huffman_file,
                                         pywolf.configs.wl6.GRAPHICS_PARTITIONS_MAP)
            graphics_chunks_handler = pywolf.persistence.PrecachedChunksHandler(graphics_chunks_handler)

        count = len(graphics_chunks_handler)
        for i, chunk in enumerate(graphics_chunks_handler):
            path = r'{}/graphics_{:04d}.bin'.format(self.OUTPUT_FOLDER, i)
            logger.info('Graphics chunk [%4d/%4d]: %r, 0x%04X bytes', (i + 1), count, path, len(chunk))
            with open(path, 'wb') as chunk_file:
                chunk_file.write(chunk)

    def testTileMaps(self):
        logger = logging.getLogger()
        logger.info('testTileMaps')

        tilemap_chunks_handler = pywolf.persistence.MapChunksHandler()
        with open(self.MAPHEAD_PATH, 'rb') as (header_file
        ), open(self.GAMEMAPS_PATH, 'rb') as data_file:
            tilemap_chunks_handler.load(data_file, header_file)
            tilemap_chunks_handler = pywolf.persistence.PrecachedChunksHandler(tilemap_chunks_handler)

        count = len(tilemap_chunks_handler)
        for i, item in enumerate(tilemap_chunks_handler):
            header, planes = item
            logger.info('TileMap chunk [%4d/%4d]:', (i + 1), count)
            if header is not None:
                header_bytes = header.to_bytes()
                path = r'{}/tilemap_{:04d}_header.bin'.format(self.OUTPUT_FOLDER, i)
                logger.info('... header: %r, 0x%04X bytes', path, len(header_bytes))
                with open(path, 'wb') as header_file:
                    header_file.write(header_bytes)

                for j, plane in enumerate(planes):
                    path = r'{}/tilemap_{:04d}_plane{}.bin'.format(self.OUTPUT_FOLDER, i, j)
                    logger.info('... plane [%d/%d]: %r, 0x%04X bytes', (j + 1), len(planes), path, len(plane))
                    with open(path, 'wb') as chunk_file:
                        chunk_file.write(plane)


if __name__ == "__main__":
    unittest.main()


