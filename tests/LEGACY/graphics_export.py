import logging
import os
import sys
import unittest

from PIL import ImageFont
import pywolf.graphics
import pywolf.persistence

import pywolf.configs.wl6


class Test(unittest.TestCase):

    VGAHEAD_PATH = r'../data/wl6/vgahead.wl6'
    VGADICT_PATH = r'../data/wl6/vgadict.wl6'
    VGAGRAPH_PATH = r'../data/wl6/vgagraph.wl6'

    VSWAP_PATH = r'../data/wl6/vswap.wl6'

    PALETTE_PATH = r'../data/palettes/wolf.pal'

    OUTPUT_FOLDER = r'./outputs/graphics_tests'

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
        self._partition_map = pywolf.configs.wl6.GRAPHICS_PARTITIONS_MAP
        self._palette = pywolf.configs.wl6.GRAPHICS_PALETTE
        self._palette_map = pywolf.configs.wl6.GRAPHICS_PALETTE_MAP

    def tearDown(self):
        logger = logging.getLogger()
        logger.removeHandler(self._stdout_handler)

    def testPalette(self):
        logger = logging.getLogger()
        logger.info('testPalette')

        path = self.PALETTE_PATH
        logger.info('Input palette: %r', path)
        with open(path, 'rt') as jascpal_file:
            palette = pywolf.graphics.jascpal_read(jascpal_file)
        assert len(palette) == len(self._palette)
        for pc, rc in zip(palette, self._palette):
            assert len(pc) == len(rc)
            for pv, rv in zip(pc, rc):
                assert pv == rv

        path = r'{}/wolf.pal'.format(self.OUTPUT_FOLDER)
        with open(path, 'wt') as jascpal_file:
            logger.info('Output palette: %r, %d colors', path, len(palette))
            pywolf.graphics.jascpal_write(jascpal_file, palette)

    def testTextures(self):
        logger = logging.getLogger()
        logger.info('testTextures')

        palette = self._palette_map[...]
        vswap_chunks_handler = pywolf.persistence.VSwapChunksHandler()

        with open(self.VSWAP_PATH, 'rb') as data_file:
            vswap_chunks_handler.load(data_file)

            start = 0
            count = vswap_chunks_handler.sprites_start - start
            texture_manager = pywolf.graphics.TextureManager(vswap_chunks_handler, palette, (64, 64), start, count)

            for i, texture in enumerate(texture_manager):
                path = r'{}/texture_{:04d}.png'.format(self.OUTPUT_FOLDER, i)
                logger.info('Texture [%4d/%4d]: %r, %r', (i + 1), count, texture.size, path)
                texture.image.save(path)

    def testSprites(self):
        logger = logging.getLogger()
        logger.info('testSprites')

        palette = self._palette_map[...]
        vswap_chunks_handler = pywolf.persistence.VSwapChunksHandler()

        with open(self.VSWAP_PATH, 'rb') as data_file:
            vswap_chunks_handler.load(data_file)

            start = vswap_chunks_handler.sprites_start
            count = vswap_chunks_handler.sounds_start - start
            sprite_manager = pywolf.graphics.SpriteManager(vswap_chunks_handler, palette, (64, 64), start, count)

            for i, sprite in enumerate(sprite_manager):
                path = r'{}/sprite_{:04d}.png'.format(self.OUTPUT_FOLDER, i)
                logger.info('Sprite [%4d/%4d]: %r, %r', (i + 1), count, sprite.size, path)
                sprite.image.save(path)

    def testPictures(self):
        logger = logging.getLogger()
        logger.info('testPictures')

        partition_map = self._partition_map
        palette_map = self._palette_map
        graphics_chunks_handler = pywolf.persistence.GraphicsChunksHandler()
        start, count = partition_map['pics']

        with open(self.VGAHEAD_PATH, 'rb') as (header_file
        ), open(self.VGAGRAPH_PATH, 'rb') as (data_file
        ), open(self.VGADICT_PATH, 'rb') as huffman_file:
            graphics_chunks_handler.load(data_file, header_file, huffman_file, partition_map)
            picture_manager = pywolf.graphics.PictureManager(graphics_chunks_handler, palette_map, start, count)

            for i, picture in enumerate(picture_manager):
                path = r'{}/picture_{:04d}.png'.format(self.OUTPUT_FOLDER, i)
                logger.info('Picture [%4d/%4d]: %r, %r', (i + 1), count, picture.size, path)
                picture.image.save(path)

    def testTile8(self):
        logger = logging.getLogger()
        logger.info('testTile8')

        partition_map = self._partition_map
        palette_map = self._palette_map
        graphics_chunks_handler = pywolf.persistence.GraphicsChunksHandler()
        start, count = partition_map['tile8']

        with open(self.VGAHEAD_PATH, 'rb') as (header_file
        ), open(self.VGAGRAPH_PATH, 'rb') as (data_file
        ), open(self.VGADICT_PATH, 'rb') as huffman_file:
            graphics_chunks_handler.load(data_file, header_file, huffman_file, partition_map)
            tile8_manager = pywolf.graphics.Tile8Manager(graphics_chunks_handler, palette_map, start, count)

            for i, tile8 in enumerate(tile8_manager):
                path = r'{}/tile8_{:04d}.png'.format(self.OUTPUT_FOLDER, i)
                logger.info('Tile8 [%4d/%4d]: %r', (i + 1), count, path)
                tile8.image.save(path)

    def testFonts(self):
        logger = logging.getLogger()
        logger.info('testFonts')

        partition_map = self._partition_map
        palette_map = self._palette_map
        graphics_chunks_handler = pywolf.persistence.GraphicsChunksHandler()
        start, count = partition_map['font']

        with open(self.VGAHEAD_PATH, 'rb') as (header_file
        ), open(self.VGAGRAPH_PATH, 'rb') as (data_file
        ), open(self.VGADICT_PATH, 'rb') as huffman_file:
            graphics_chunks_handler.load(data_file, header_file, huffman_file, partition_map)
            font_manager = pywolf.graphics.FontManager(graphics_chunks_handler, palette_map[...], start, count)

            for i, font in enumerate(font_manager):
                for j, image in enumerate(font.images):
                    if image is not None:
                        path = r'{}/font_{:04d}_{}.png'.format(self.OUTPUT_FOLDER, i, j)
                        size = (font.widths[j], font.height)
                        logger.info('Font glyph [%4d/%4d][%4d/%4d]: %r %r',
                                    (i + 1), count, (j + 1), len(font.images), size, path)
                        image.save(path)

    def testDOSScreens(self):
        logger = logging.getLogger()
        logger.info('testScreens')

        partition_map = self._partition_map
        palette_map = self._palette_map
        graphics_chunks_handler = pywolf.persistence.GraphicsChunksHandler()
        start, count = partition_map['screens']
        font = ImageFont.truetype(r'../data/fonts/Px437_IBM_VGA9.ttf', 16)

        with open(self.VGAHEAD_PATH, 'rb') as (header_file
        ), open(self.VGAGRAPH_PATH, 'rb') as (data_file
        ), open(self.VGADICT_PATH, 'rb') as huffman_file:
            graphics_chunks_handler.load(data_file, header_file, huffman_file, partition_map)
            screen_manager = pywolf.graphics.DOSScreenManager(graphics_chunks_handler, font, start, count)

            for i, screen in enumerate(screen_manager):
                path = r'{}/screen_{:04d}.gif'.format(self.OUTPUT_FOLDER, i)
                frames = screen.frames
                logger.info('DOS Screen [%4d/%4d]: %r (%d frames)', (i + 1), count, path, len(frames))
                if len(frames) > 1:
                    frames[0].save(path, save_all=True, append_images=frames[1:], duration=1000, loop=0)
                else:
                    frames[0].save(path)

    def testHelpArts(self):
        logger = logging.getLogger()
        logger.info('testHelpArts')

        partition_map = self._partition_map
        palette_map = self._palette_map
        graphics_chunks_handler = pywolf.persistence.GraphicsChunksHandler()
        start, count = partition_map['helpart']

        with open(self.VGAHEAD_PATH, 'rb') as (header_file
        ), open(self.VGAGRAPH_PATH, 'rb') as (data_file
        ), open(self.VGADICT_PATH, 'rb') as huffman_file:
            graphics_chunks_handler.load(data_file, header_file, huffman_file, partition_map)
            helpart_manager = pywolf.graphics.TextArtManager(graphics_chunks_handler, start, count)

            for i, helpart in enumerate(helpart_manager):
                path = r'{}/helpart_{:04d}.txt'.format(self.OUTPUT_FOLDER, i)
                logger.info('HelpArt [%4d/%4d]: %r, %d chars', (i + 1), count, path, len(helpart))
                with open(path, 'wt') as helpart_file:
                    helpart_file.write(helpart)

    def testEndArts(self):
        logger = logging.getLogger()
        logger.info('testEndArts')

        partition_map = self._partition_map
        palette_map = self._palette_map
        graphics_chunks_handler = pywolf.persistence.GraphicsChunksHandler()
        start, count = partition_map['endart']

        with open(self.VGAHEAD_PATH, 'rb') as (header_file
        ), open(self.VGAGRAPH_PATH, 'rb') as (data_file
        ), open(self.VGADICT_PATH, 'rb') as huffman_file:
            graphics_chunks_handler.load(data_file, header_file, huffman_file, partition_map)
            endart_manager = pywolf.graphics.TextArtManager(graphics_chunks_handler, start, count)

            for i, endart in enumerate(endart_manager):
                path = r'{}/endart_{:04d}.txt'.format(self.OUTPUT_FOLDER, i)
                logger.info('EndArt [%4d/%4d]: %r, %d chars', (i + 1), count, path, len(endart))
                with open(path, 'wt') as endart_file:
                    endart_file.write(endart)


if __name__ == "__main__":
    unittest.main()


