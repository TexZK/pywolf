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
        logger.info('-' * 80)
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

        path = r'../data/palettes/wolf.pal'
        logger.info('Input palette: %r', path)
        with open(path, 'rt') as jascpal_file:
            palette = pywolf.graphics.jascpal_read(jascpal_file)
        assert len(palette) == len(self._palette)
        for pc, rc in zip(palette, self._palette):
            assert len(pc) == len(rc)
            for pv, rv in zip(pc, rc):
                assert pv == rv

        path = r'./outputs/wolf.pal'
        with open(path, 'wt') as jascpal_file:
            logger.info('Output palette: %r, %d colors', path, len(palette))
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
                path = r'./outputs/texture_{}.png'.format(i)
                logger.info('Texture [%d/%d]: %r, %r', (i + 1), count, texture.dimensions, path)
                texture.image.save(path)

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
                path = r'./outputs/sprite_{}.png'.format(i)
                logger.info('Sprite [%d/%d]: %r, %r', (i + 1), count, sprite.dimensions, path)
                sprite.image.save(path)

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
                path = r'./outputs/picture_{}.png'.format(i)
                logger.info('Picture [%d/%d]: %r, %r', (i + 1), count, picture.dimensions, path)
                picture.image.save(path)

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
                path = r'./outputs/tile8_{}.png'.format(i)
                logger.info('Tile8 [%d/%d]: %r', (i + 1), count, path)
                tile8.image.save(path)

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
                        path = r'./outputs/font_{}_{}.png'.format(i, j)
                        dimensions = (font.widths[j], font.height)
                        logger.info('Font glyph [%d/%d][%d/%d]: %r %r',
                                    (i + 1), count, (j + 1), len(font.images), dimensions, path)
                        image.save(path)

    def testDOSScreens(self):
        logger = logging.getLogger()
        logger.info('testScreens')

        partition_map = self._partition_map
        palette_map = self._palette_map
        graphics_chunks_handler = pywolf.persistence.GraphicsChunksHandler()
        start, count = partition_map['screens']

        with open(r'../data/wl6/vgahead.wl6', 'rb') as (header_file
        ),   open(r'../data/wl6/vgagraph.wl6', 'rb') as (data_file
        ),   open(r'../data/wl6/vgadict.wl6', 'rb') as huffman_file:
            graphics_chunks_handler.load(data_file, header_file, huffman_file, partition_map)
            screen_manager = pywolf.graphics.DOSScreenManager(graphics_chunks_handler, start, count)

            for i, screen in enumerate(screen_manager):
                path = r'./outputs/screen_{}.scr'.format(i)
                logger.info('DOS Screen [%d/%d]: %r', (i + 1), count, path)
                with open(path, 'wb') as screen_file:
                    screen_file.write(screen.data)

    def testHelpArts(self):
        logger = logging.getLogger()
        logger.info('testHelpArts')

        partition_map = self._partition_map
        palette_map = self._palette_map
        graphics_chunks_handler = pywolf.persistence.GraphicsChunksHandler()
        start, count = partition_map['helpart']

        with open(r'../data/wl6/vgahead.wl6', 'rb') as (header_file
        ),   open(r'../data/wl6/vgagraph.wl6', 'rb') as (data_file
        ),   open(r'../data/wl6/vgadict.wl6', 'rb') as huffman_file:
            graphics_chunks_handler.load(data_file, header_file, huffman_file, partition_map)
            helpart_manager = pywolf.graphics.HelpArtManager(graphics_chunks_handler, start, count)

            for i, helpart in enumerate(helpart_manager):
                path = r'./outputs/helpart_{}.txt'.format(i)
                logger.info('HelpArt [%d/%d]: %r, %d chars', (i + 1), count, path, len(helpart))
                with open(path, 'wt') as helpart_file:
                    helpart_file.write(helpart)

    def testEndArts(self):
        logger = logging.getLogger()
        logger.info('testEndArts')

        partition_map = self._partition_map
        palette_map = self._palette_map
        graphics_chunks_handler = pywolf.persistence.GraphicsChunksHandler()
        start, count = partition_map['endart']

        with open(r'../data/wl6/vgahead.wl6', 'rb') as (header_file
        ),   open(r'../data/wl6/vgagraph.wl6', 'rb') as (data_file
        ),   open(r'../data/wl6/vgadict.wl6', 'rb') as huffman_file:
            graphics_chunks_handler.load(data_file, header_file, huffman_file, partition_map)
            endart_manager = pywolf.graphics.EndArtManager(graphics_chunks_handler, start, count)

            for i, endart in enumerate(endart_manager):
                path = r'./outputs/endart_{}.txt'.format(i)
                logger.info('EndArt [%d/%d]: %r, %d chars', (i + 1), count, path, len(endart))
                with open(path, 'wt') as endart_file:
                    endart_file.write(endart)


if __name__ == "__main__":
    # import sys;sys.argv = ['', 'Test.testName']
    unittest.main()


