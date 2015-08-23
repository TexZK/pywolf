'''
@author: Andrea Zoppi
'''

import sys
import argparse
import os
import io
import logging
import zipfile
from PIL import Image

import pywolf.persistence
import pywolf.configs.wl6 as CONFIG_WL6
from pywolf.graphics import write_targa_rgbx, build_color_image
from pywolf.audio import samples_upsample, wave_write


TEXTURE_SHADER_TEMPLATE = '''
{!s}
{{
    {{
        map $lightmap
        rgbGen identity
    }}
    {{
        map {!s}
        blendFunc GL_DST_COLOR GL_ZERO
        rgbGen identity
    }}
}}
'''

SPRITE_SHADER_TEMPLATE = '''
{!s}
{{
    {{
        map {!s}
        blendFunc GL_SRC_ALPHA GL_ONE_MINUS_SRC_ALPHA
        rgbGen identity
    }}
}}
'''  # TODO: sprite Z-axis freedom


def build_argument_parser():
    parser = argparse.ArgumentParser()

    group = parser.add_argument_group('input paths')
    group.add_argument('--input-folder', default='.')
    group.add_argument('--vswap-data', required=True)  # TODO
    group.add_argument('--graphics-data', required=True)  # TODO
    group.add_argument('--graphics-header', required=True)  # TODO
    group.add_argument('--graphics-huffman', required=True)  # TODO
    group.add_argument('--audio-data', required=True)  # TODO
    group.add_argument('--audio-header', required=True)  # TODO
    group.add_argument('--maps-data', required=True)  # TODO
    group.add_argument('--maps-header', required=True)  # TODO
    group.add_argument('--palette')  # TODO

    group = parser.add_argument_group('output paths')
    group.add_argument('--output-folder', default='.')
    group.add_argument('--output-pk3', required=True)  # TODO

    group = parser.add_argument_group('settings')  # TODO
    group.add_argument('--config', default='wl6')
    group.add_argument('--wave-frequency', default=22050, type=int)

    return parser


def export_textures(params, config, zip_file, vswap_chunks_handler):
    logger = logging.getLogger()
    logger.info('Exporting textures')

    start = 0
    count = vswap_chunks_handler.sprites_start - start
    texture_manager = pywolf.graphics.TextureManager(vswap_chunks_handler,
                                                     config.GRAPHICS_PALETTE_MAP[...],
                                                     config.SPRITE_DIMENSIONS,
                                                     start, count)

    for i, texture in enumerate(texture_manager):
        name = config.TEXTURE_NAMES[i >> 1]
        path = 'textures/wolf3d/{}__{}.tga'.format(name, (i & 1))
        logger.info('Texture [%d/%d]: %r', (i + 1), count, path)
        pixels_bgr = bytes(x for pixel in texture.image.convert('RGB').getdata() for x in reversed(pixel))
        texture_stream = io.BytesIO()
        write_targa_rgbx(texture_stream, config.TEXTURE_DIMENSIONS, 24, pixels_bgr)
        zip_file.writestr(path, texture_stream.getbuffer())

    palette = config.GRAPHICS_PALETTE
    for i, color in enumerate(palette):
        path = 'textures/wolf3d/palette_0x{:02X}.tga'.format(i)
        logger.info('Texture palette color [%d/%d]: (0x%02X, 0x%02X, 0x%02X)',
                    (i + 1), len(palette), *color)
        image = build_color_image(config.TEXTURE_DIMENSIONS, color)
        pixels_bgr = bytes(x for pixel in image.getdata() for x in reversed(pixel))
        texture_stream = io.BytesIO()
        write_targa_rgbx(texture_stream, config.TEXTURE_DIMENSIONS, 24, pixels_bgr)
        zip_file.writestr(path, texture_stream.getbuffer())


def write_texture_shaders(params, config, shader_file):
    for name in config.TEXTURE_NAMES:
        for j in range(2):
            shader_name = 'textures/wolf3d/{}__{}'.format(name, j)
            path = shader_name + '.tga'
            shader_file.write(TEXTURE_SHADER_TEMPLATE.format(shader_name, path))

    palette = config.GRAPHICS_PALETTE
    for i in range(len(palette)):
        shader_name = 'textures/wolf3d/palette_0x{:02X}.tga'.format(i)
        path = shader_name + '.tga'
        shader_file.write(TEXTURE_SHADER_TEMPLATE.format(shader_name, path))


def write_sprite_shaders(params, config, shader_file):
    pass  # TODO


def export_shaders(params, config, zip_file):
    logger = logging.getLogger()
    logger.info('Exporting shaders')

    shader_text = io.StringIO()
    write_texture_shaders(params, config, shader_text)
    zip_file.writestr('scripts/wolf3d.shader', shader_text.getvalue().encode())

    with open(os.path.join(params.output_folder, 'scripts', 'wolf3d.shader'), 'wt') as shader_file:
        shader_file.write(shader_text.getvalue())

    # TODO: sprites


def export_sprites(params, config, zip_file, vswap_chunks_handler):
    logger = logging.getLogger()
    logger.info('Exporting sprites')

    start = vswap_chunks_handler.sprites_start
    count = vswap_chunks_handler.sounds_start - start
    sprite_manager = pywolf.graphics.SpriteManager(vswap_chunks_handler,
                                                   config.GRAPHICS_PALETTE_MAP[...],
                                                   config.SPRITE_DIMENSIONS,
                                                   start, count)

    for i, sprite in enumerate(sprite_manager):
        name = config.SPRITE_NAMES[i]
        path = 'sprites/{}.tga'.format(name)
        logger.info('Sprite [%d/%d]: %r', (i + 1), count, path)
        pixels_abgr = bytes(x for pixel in sprite.image.convert('RGBA').getdata() for x in reversed(pixel))
        sprite_stream = io.BytesIO()
        write_targa_rgbx(sprite_stream, config.SPRITE_DIMENSIONS, 32, pixels_abgr)
        zip_file.writestr(path, sprite_stream.getvalue())


def export_fonts(params, config, zip_file, graphics_chunks_handler):
    logger = logging.getLogger()
    logger.info('Exporting sprites')

    partitions_map = config.GRAPHICS_PARTITIONS_MAP
    palette = config.GRAPHICS_PALETTE_MAP[...]
    start, count = partitions_map['font']
    font_manager = pywolf.graphics.FontManager(graphics_chunks_handler, palette, start, count)

    for i, font in enumerate(font_manager):
        assert font.height * 16 <= 256
        path = 'fonts/fontImage_0_{}.tga'.format(font.height)
        logger.info('Font [%d/%d]: %r', (i + 1), count, path)
        assert max(font.widths) * 16 <= 256
        image = Image.new('RGB', (256, 256))

        for j, glyph_image in enumerate(font.images):
            if glyph_image is not None:
                corner = ((j % 16) * 16, (j // 16) * 16)
                image.paste(glyph_image, corner)

        pixels_bgr = bytes(x for pixel in image.getdata() for x in reversed(pixel))
        font_stream = io.BytesIO()
        write_targa_rgbx(font_stream, (256, 256), 24, pixels_bgr)
        zip_file.writestr(path, font_stream.getvalue())

        # TODO: *.dat file


def export_sampled_sounds(params, config, zip_file, vswap_chunks_handler):
    logger = logging.getLogger()
    logger.info('Exporting sampled sounds')

    start = vswap_chunks_handler.sounds_start
    count = len(vswap_chunks_handler.sounds_infos)
    sample_manager = pywolf.audio.SampledSoundManager(vswap_chunks_handler,
                                                      config.SAMPLED_SOUNDS_FREQUENCY,
                                                      start, count)
    scale_factor = params.wave_frequency / config.SAMPLED_SOUNDS_FREQUENCY

    for i, sampled_sound in enumerate(sample_manager):
        name = config.SAMPLED_SOUND_NAMES[i]
        path = 'sound/{}.wav'.format(name)
        logger.info('Sampled sound [%d/%d]: %r', (i + 1), count, path)
        samples = bytes(samples_upsample(sampled_sound.samples, scale_factor))
        wave_file = io.BytesIO()
        wave_write(wave_file, params.wave_frequency, samples)
        zip_file.writestr(path, wave_file.getbuffer())


def main(*args):  # TODO
    logger = logging.getLogger()
    stdout_handler = logging.StreamHandler(sys.stdout)
    stdout_handler.setLevel(logging.DEBUG)
    logger.addHandler(stdout_handler)
    logger.setLevel(logging.DEBUG)

    print(args)
    parser = build_argument_parser()
    params = parser.parse_args(args)

    config = CONFIG_WL6  # TODO: import from XML?

    vswap_chunks_handler = pywolf.persistence.PrecachedVSwapChunksHandler()
    with open(os.path.join(params.input_folder, params.vswap_data), 'rb') as data_file:
        vswap_chunks_handler.load(data_file)

    audio_chunks_handler = pywolf.persistence.PrecachedAudioChunksHandler()
    with open(os.path.join(params.input_folder, params.audio_header), 'rb') as (header_file
    ),   open(os.path.join(params.input_folder, params.audio_data), 'rb') as data_file:
        audio_chunks_handler.load(data_file, header_file)

    graphics_chunks_handler = pywolf.persistence.PrecachedGraphicsChunksHandler()
    with open(os.path.join(params.input_folder, params.graphics_header), 'rb') as (header_file
    ),   open(os.path.join(params.input_folder, params.graphics_data), 'rb') as (data_file
    ),   open(os.path.join(params.input_folder, params.graphics_huffman), 'rb') as huffman_file:
        graphics_chunks_handler.load(data_file, header_file, huffman_file,
                                     config.GRAPHICS_PARTITIONS_MAP)

#     map_chunks_handler = pywolf.persistence.PrecachedMapChunksHandler()
#     with open(os.path.join(params.input_folder, params.maps_header), 'rb') as (header_file
#     ),   open(os.path.join(params.input_folder, params.maps_data), 'rb') as data_file:
#         map_chunks_handler.load(data_file, header_file)

    with zipfile.ZipFile(os.path.join(params.output_folder, params.output_pk3), 'w', zipfile.ZIP_DEFLATED) as zip_file:
        export_shaders(params, config, zip_file)
        export_textures(params, config, zip_file, vswap_chunks_handler)
        export_sprites(params, config, zip_file, vswap_chunks_handler)
        export_fonts(params, config, zip_file, graphics_chunks_handler)
        # TODO: export_pictures(params, config, zip_file, graphics_chunks_handler)
        # TODO: export_tile8(params, config, zip_file, graphics_chunks_handler)

        export_sampled_sounds(params, config, zip_file, vswap_chunks_handler)
        # TODO: export_musics(params, config, zip_file, audio_chunks_handler)
        # TODO: export_adlib_sounds(params, config, zip_file, audio_chunks_handler)
        # TODO: export_buzzer_sounds(params, config, zip_file, audio_chunks_handler)

        # TODO: export_maps(params, config, zip_file, map_chunks_handler)
        # TODO: export_models(params, config, zip_file, ?)

        # TODO: export_texts(params, config, zip_file, ?)

    pass


if __name__ == '__main__':
    main(*sys.argv[1:])
