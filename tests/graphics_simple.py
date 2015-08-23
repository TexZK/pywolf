'''
@author: Andrea Zoppi
'''

import unittest
import sys
import logging

import pywolf.persistence
import pywolf.graphics
import pywolf.configs.wl6


class Test(unittest.TestCase):

    def setUp(self):
        logger = logging.getLogger()
        stdout_handler = logging.StreamHandler(sys.stdout)
        stdout_handler.setLevel(logging.DEBUG)
        logger.addHandler(stdout_handler)
        logger.setLevel(logging.DEBUG)
        self._stdout_handler = stdout_handler
        self._partition_map = pywolf.configs.wl6.GRAPHICS_PARTITIONS_MAP
        self._palette = pywolf.configs.wl6.GRAPHICS_PALETTE
        self._palette_map = pywolf.configs.wl6.GRAPHICS_PALETTE_MAP

    def tearDown(self):
        logger = logging.getLogger()
        logger.removeHandler(self._stdout_handler)

    def testPalette(self):
        logger = logging.getLogger()
        logger.info('testPalette')
        with open(r'../data/palettes/wolf.pal', 'rt') as jascpal_file:
            palette = pywolf.graphics.jascpal_read(jascpal_file)
        assert len(palette) == len(self._palette)
        for pc, rc in zip(palette, self._palette):
            assert len(pc) == len(rc)
            for pv, rv in zip(pc, rc):
                assert pv == rv

        with open(r'./outputs/wolf.pal', 'wt') as jascpal_file:
            pywolf.graphics.jascpal_write(jascpal_file, palette)

    def testTextures(self):
        logger = logging.getLogger()
        logger.info('testTextures')

        palette = self._palette_map[...]
        vswap_chunks_handler = pywolf.persistence.VSwapChunksHandler()

        with open(r'../data/wl6/vswap.wl6', 'rb') as data_file:
            vswap_chunks_handler.load(data_file)

            start = 0
            count = vswap_chunks_handler.sprites_start - start
            texture_manager = pywolf.graphics.TextureManager(vswap_chunks_handler, palette, (64, 64), start, count)

            for i, texture in enumerate(texture_manager):
                texture.image.save(r'./outputs/texture_{}.png'.format(i))

    def testSprites(self):
        logger = logging.getLogger()
        logger.info('testSprites')

        palette = self._palette_map[...]
        vswap_chunks_handler = pywolf.persistence.VSwapChunksHandler()

        with open(r'../data/wl6/vswap.wl6', 'rb') as data_file:
            vswap_chunks_handler.load(data_file)

            start = vswap_chunks_handler.sprites_start
            count = vswap_chunks_handler.sounds_start - start
            sprite_manager = pywolf.graphics.SpriteManager(vswap_chunks_handler, palette, (64, 64), start, count)

            for i, sprite in enumerate(sprite_manager):
                sprite.image.save(r'./outputs/sprite_{}.png'.format(i))

    def testPictures(self):
        logger = logging.getLogger()
        logger.info('testPictures')

        partition_map = self._partition_map
        palette_map = self._palette_map
        graphics_chunks_handler = pywolf.persistence.GraphicsChunksHandler()
        start, count = partition_map['pics']

        with open(r'../data/wl6/vgahead.wl6', 'rb') as (header_file
        ),   open(r'../data/wl6/vgagraph.wl6', 'rb') as (data_file
        ),   open(r'../data/wl6/vgadict.wl6', 'rb') as huffman_file:
            graphics_chunks_handler.load(data_file, header_file, huffman_file, partition_map)
            picture_manager = pywolf.graphics.PictureManager(graphics_chunks_handler, palette_map, start, count)

            for i, picture in enumerate(picture_manager):
                picture.image.save(r'./outputs/picture_{}.png'.format(i))

    def testTile8(self):
        logger = logging.getLogger()
        logger.info('testTile8')

        partition_map = self._partition_map
        palette_map = self._palette_map
        graphics_chunks_handler = pywolf.persistence.GraphicsChunksHandler()
        start, count = partition_map['tile8']

        with open(r'../data/wl6/vgahead.wl6', 'rb') as (header_file
        ),   open(r'../data/wl6/vgagraph.wl6', 'rb') as (data_file
        ),   open(r'../data/wl6/vgadict.wl6', 'rb') as huffman_file:
            graphics_chunks_handler.load(data_file, header_file, huffman_file, partition_map)
            tile8_manager = pywolf.graphics.Tile8Manager(graphics_chunks_handler, palette_map, start, count)

            for i, tile8 in enumerate(tile8_manager):
                tile8.image.save(r'./outputs/tile8_{}.png'.format(i))

    def testFonts(self):
        logger = logging.getLogger()
        logger.info('testFonts')

        partition_map = self._partition_map
        palette_map = self._palette_map
        graphics_chunks_handler = pywolf.persistence.GraphicsChunksHandler()
        start, count = partition_map['font']

        with open(r'../data/wl6/vgahead.wl6', 'rb') as (header_file
        ),   open(r'../data/wl6/vgagraph.wl6', 'rb') as (data_file
        ),   open(r'../data/wl6/vgadict.wl6', 'rb') as huffman_file:
            graphics_chunks_handler.load(data_file, header_file, huffman_file, partition_map)
            font_manager = pywolf.graphics.FontManager(graphics_chunks_handler, palette_map[...], start, count)

            for i, font in enumerate(font_manager):
                for j, image in enumerate(font.images):
                    if image is not None:
                        image.save(r'./outputs/font_{}_{}.png'.format(i, j))


if __name__ == "__main__":
    #import sys;sys.argv = ['', 'Test.testName']
    unittest.main()


