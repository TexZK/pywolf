# TODO: create Exporter class(es)
# TODO: break export loops into single item calls with wrapping loop
# TODO: allow export to normal file, PK3 being an option (like with open(file_object|path))

'''
@author: Andrea Zoppi
'''

import argparse
import io
import logging
import os
import sys
import zipfile

from PIL import Image

from pywolf.audio import samples_upsample, wave_write, convert_imf_to_wave
import pywolf.configs.wl6 as CONFIG_WL6
from pywolf.graphics import write_targa_bgrx, build_color_image
import pywolf.persistence
from pywolf.utils import stream_pack


IMF2WAV_PATH = os.path.join('..', 'tools', 'imf2wav.exe')


TEXTURE_SHADER_TEMPLATE = '''
{0!s}
{{
    qer_editorimage {1!s}
    {{
        map $lightmap
        rgbGen identity
    }}
    {{
        clampmap {1!s}
        blendFunc GL_DST_COLOR GL_ZERO
        rgbGen identity
    }}
}}
'''

SPRITE_SHADER_TEMPLATE = '''
{0!s}
{{
    qer_editorimage {1!s}
    deformVertexes autoSprite2
    surfaceparm trans
    surfaceparm nomarks
    cull none
    {{
        clampmap {1!s}
        blendFunc blend
        rgbGen identity
    }}
}}
'''


class MapExporter(object):  # TODO

    NORTH  = 0
    EAST   = 1
    SOUTH  = 2
    WEST   = 3
    TOP    = 4
    BOTTOM = 5

    DIR_TO_DISPL = {
        NORTH:  ( 0, -1,  0),
        EAST:   ( 1,  0,  0),
        SOUTH:  ( 0,  1,  0),
        WEST:   (-1,  0,  0),
        TOP:    ( 0,  0,  1),
        BOTTOM: ( 0,  0, -1),
    }

    def __init__(self, params, config, tilemap):
        self.params = params
        self.config = config
        self.tilemap = tilemap

    def tile_to_unit_coords(self, tile_coords):
        tile_units = self.params.tile_units
        return [
            (tile_coords[0] *  tile_units),
            (tile_coords[1] * -tile_units),
            0,
        ]

    def describe_textured_cube(self, tile_coords, face_textures, unit_offsets=(0, 0, 0)):
        tile_units = self.params.tile_units
        half_units = tile_units * 0.5
        center = [offset + units + half_units
                  for units, offset in zip(self.tile_to_unit_coords(tile_coords), unit_offsets)]
        texture_scale = self.params.texture_scale
        format_line = ('( {0[0]} {0[1]} {0[2]} ) '
                       '( {1[0]} {1[1]} {1[2]} ) '
                       '( {2[0[} {2[1]} {2[2]} ) '
                       '{3} 0 0 0 {4} {4} 0 0 0').format

        face_vertices = [
            [
                [(center[0] + half_units), (center[1] + half_units), (center[2] + half_units)],
                [(center[0] - half_units), (center[1] + half_units), (center[2] + half_units)],
                [(center[0] - half_units), (center[1] + half_units), (center[2] - half_units)],
                [(center[0] + half_units), (center[1] + half_units), (center[2] - half_units)],
            ],
            [
                [(center[0] + half_units), (center[1] - half_units), (center[2] + half_units)],
                [(center[0] + half_units), (center[1] + half_units), (center[2] + half_units)],
                [(center[0] + half_units), (center[1] + half_units), (center[2] - half_units)],
                [(center[0] + half_units), (center[1] - half_units), (center[2] - half_units)],
            ],
            [
                [(center[0] - half_units), (center[1] - half_units), (center[2] + half_units)],
                [(center[0] + half_units), (center[1] - half_units), (center[2] + half_units)],
                [(center[0] + half_units), (center[1] - half_units), (center[2] - half_units)],
                [(center[0] - half_units), (center[1] - half_units), (center[2] - half_units)],
            ],
            [
                [(center[0] - half_units), (center[1] + half_units), (center[2] + half_units)],
                [(center[0] - half_units), (center[1] - half_units), (center[2] + half_units)],
                [(center[0] - half_units), (center[1] - half_units), (center[2] - half_units)],
                [(center[0] - half_units), (center[1] + half_units), (center[2] - half_units)],
            ],
            [
                [(center[0] - half_units), (center[1] + half_units), (center[2] + half_units)],
                [(center[0] + half_units), (center[1] + half_units), (center[2] + half_units)],
                [(center[0] + half_units), (center[1] - half_units), (center[2] + half_units)],
                [(center[0] - half_units), (center[1] - half_units), (center[2] + half_units)],
            ],
            [
                [(center[0] + half_units), (center[1] + half_units), (center[2] - half_units)],
                [(center[0] - half_units), (center[1] + half_units), (center[2] - half_units)],
                [(center[0] - half_units), (center[1] - half_units), (center[2] - half_units)],
                [(center[0] + half_units), (center[1] - half_units), (center[2] - half_units)],
            ],
        ]

        return '\n'.join(format_line(vertices[0], vertices[1], vertices[2], shader_name, texture_scale)
                         for shader_name, vertices in zip(face_textures, face_vertices))


def build_argument_parser():
    parser = argparse.ArgumentParser()

    group = parser.add_argument_group('input paths')
    group.add_argument('--input-folder', default='.')
    group.add_argument('--vswap-data', required=True)
    group.add_argument('--graphics-data', required=True)
    group.add_argument('--graphics-header', required=True)
    group.add_argument('--graphics-huffman', required=True)
    group.add_argument('--audio-data', required=True)
    group.add_argument('--audio-header', required=True)
    group.add_argument('--maps-data', required=True)
    group.add_argument('--maps-header', required=True)
    group.add_argument('--palette')  # TODO

    group = parser.add_argument_group('output paths')
    group.add_argument('--output-folder', default='.')
    group.add_argument('--output-pk3', required=True)

    group = parser.add_argument_group('settings')
    group.add_argument('--config', default='wl6')
    group.add_argument('--short-name', default='wolf3d')
    group.add_argument('--wave-rate', default=44100, type=int)
    group.add_argument('--imf-rate', default=700, type=int)
    group.add_argument('--imf2wav-path', default=IMF2WAV_PATH)
    group.add_argument('--tile-units', default=32, type=int)
    group.add_argument('--texture-scale', default=1.5, type=float)

    return parser


def _sep():
    logger = logging.getLogger()
    logger.info('-' * 80)


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
        path = 'textures/{}/walls/{}__{}.tga'.format(params.short_name, name, (i & 1))
        logger.info('Texture [%d/%d]: %r', (i + 1), count, path)
        top_bottom_rgb_image = texture.image.transpose(Image.FLIP_TOP_BOTTOM).convert('RGB')
        pixels_bgr = bytes(x for pixel in top_bottom_rgb_image.getdata() for x in reversed(pixel))
        texture_stream = io.BytesIO()
        write_targa_bgrx(texture_stream, config.TEXTURE_DIMENSIONS, 24, pixels_bgr)
        zip_file.writestr(path, texture_stream.getbuffer())

    palette = config.GRAPHICS_PALETTE
    for i, color in enumerate(palette):
        path = 'textures/{}/palette/color_0x{:02X}.tga'.format(params.short_name, i)
        logger.info('Texture palette color [%d/%d]: %r, (0x%02X, 0x%02X, 0x%02X)',
                    (i + 1), len(palette), path, *color)
        image = build_color_image(config.TEXTURE_DIMENSIONS, color)
        top_bottom_rgb_image = image.transpose(Image.FLIP_TOP_BOTTOM).convert('RGB')
        pixels_bgr = bytes(x for pixel in top_bottom_rgb_image.getdata() for x in reversed(pixel))
        texture_stream = io.BytesIO()
        write_targa_bgrx(texture_stream, config.TEXTURE_DIMENSIONS, 24, pixels_bgr)
        zip_file.writestr(path, texture_stream.getbuffer())

    logger.info('Done')
    _sep()


def write_texture_shaders(params, config, shader_file):
    for name in config.TEXTURE_NAMES:
        for j in range(2):
            shader_name = 'textures/{}/walls/{}__{}'.format(params.short_name, name, j)
            path = shader_name + '.tga'
            shader_file.write(TEXTURE_SHADER_TEMPLATE.format(shader_name, path))

    palette = config.GRAPHICS_PALETTE
    for i in range(len(palette)):
        shader_name = 'textures/{}/palette/color_0x{:02X}'.format(params.short_name, i)
        path = shader_name + '.tga'
        shader_file.write(TEXTURE_SHADER_TEMPLATE.format(shader_name, path))


def write_sprite_shaders(params, config, shader_file):
    for name_index in config.STATIC_SPRITE_INDICES:
        name = config.SPRITE_NAMES[name_index]
        shader_name = 'textures/{}/static_sprites/{}'.format(params.short_name, name)
        path = 'sprites/{}/{}.tga'.format(params.short_name, name)
        shader_file.write(SPRITE_SHADER_TEMPLATE.format(shader_name, path))


def export_shaders(params, config, zip_file):
    logger = logging.getLogger()
    logger.info('Exporting shaders')

    shader_text_stream = io.StringIO()
    # write_texture_shaders(params, config, shader_text_stream)  # FIXME: really needed for them?
    write_sprite_shaders(params, config, shader_text_stream)
    zip_file.writestr('scripts/{}.shader'.format(params.short_name),
                      shader_text_stream.getvalue().encode())

    with open(os.path.join(params.output_folder, 'scripts', 'wolf3d.shader'), 'wt') as shader_file:
        shader_file.write(shader_text_stream.getvalue())

    logger.info('Done')
    _sep()


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
        path = 'sprites/{}/{}.tga'.format(params.short_name, name)
        logger.info('Sprite [%d/%d]: %r', (i + 1), count, path)
        top_bottom_rgba_image = sprite.image.transpose(Image.FLIP_TOP_BOTTOM).convert('RGBA')
        pixels_bgra = bytes(x for pixel in top_bottom_rgba_image.getdata()
                            for x in [pixel[2], pixel[1], pixel[0], pixel[3]])
        sprite_stream = io.BytesIO()
        write_targa_bgrx(sprite_stream, config.SPRITE_DIMENSIONS, 32, pixels_bgra)
        zip_file.writestr(path, sprite_stream.getbuffer())

    logger.info('Done')
    _sep()


# TODO: compact+paged glyph placement
def export_fonts(params, config, zip_file, graphics_chunks_handler, missing_char='?',
                 texture_dimensions=(256, 256)):

    logger = logging.getLogger()
    logger.info('Exporting fonts')

    partitions_map = config.GRAPHICS_PARTITIONS_MAP
    palette = config.GRAPHICS_PALETTE_MAP[...]
    start, count = partitions_map['font']
    font_manager = pywolf.graphics.FontManager(graphics_chunks_handler, palette, start, count)

    for i, font in enumerate(font_manager):
        height = font.height
        assert texture_dimensions == (256, 256)
        assert max(font.widths) * 16 <= texture_dimensions[0]
        assert height * 16 <= texture_dimensions[1]
        image_path = 'fonts/fontImage_0_{}.tga'.format(height)
        info_path = 'fonts/fontImage_{}.dat'.format(height)
        logger.info('Font [%d/%d]: %r, %r', (i + 1), count, image_path, info_path)
        image = Image.new('RGB', texture_dimensions)
        info_stream = io.BytesIO()
        image_path_ascii = image_path.encode('ascii')

        for j, glyph_image in enumerate(font.images):
            if glyph_image is None and missing_char is not None:
                glyph_image = font.images[ord(missing_char)]
                width = font.widths[ord(missing_char)]
            else:
                width = font.widths[j]
            origin = (((j % 16) * 16), ((j // 16) * 16))

            if glyph_image is not None:
                image.paste(glyph_image, origin)

            stream_pack(info_stream, '<7l4fL32s',
                        height,  # height
                        0,  # top
                        height,  # bottom
                        width,  # pitch
                        width,  # xSkip
                        width,  # imageWidth
                        height,  # imageHeight
                        (origin[0] / texture_dimensions[0]),  # s
                        (origin[1] / texture_dimensions[1]),  # t
                        ((origin[0] + width) / texture_dimensions[0]),  # s2
                        ((origin[1] + height) / texture_dimensions[1]),  # t2
                        0,  # glyph
                        image_path_ascii)  # shaderName

        stream_pack(info_stream, '<f64s',
                    1.0,  # glyphScale
                    info_path.encode('ascii'))  # name
        zip_file.writestr(info_path, info_stream.getbuffer())

        pixels_bgr = bytes(x for pixel in image.transpose(Image.FLIP_TOP_BOTTOM).getdata() for x in reversed(pixel))
        font_stream = io.BytesIO()
        write_targa_bgrx(font_stream, texture_dimensions, 24, pixels_bgr)
        zip_file.writestr(image_path, font_stream.getbuffer())

    logger.info('Done')
    _sep()


def export_pictures(params, config, zip_file, graphics_chunks_handler):
    logger = logging.getLogger()
    logger.info('Exporting pictures')

    partitions_map = config.GRAPHICS_PARTITIONS_MAP
    palette_map = config.GRAPHICS_PALETTE_MAP
    start, count = partitions_map['pics']
    picture_manager = pywolf.graphics.PictureManager(graphics_chunks_handler, palette_map, start, count)

    for i, picture in enumerate(picture_manager):
        path = 'gfx/{}/{}.tga'.format(params.short_name, config.PICTURE_NAMES[i])
        logger.info('Picture [%d/%d]: %r', (i + 1), count, path)
        top_bottom_rgb_image = picture.image.transpose(Image.FLIP_TOP_BOTTOM).convert('RGB')
        pixels_bgr = bytes(x for pixel in top_bottom_rgb_image.getdata() for x in reversed(pixel))
        picture_stream = io.BytesIO()
        write_targa_bgrx(picture_stream, picture.dimensions, 24, pixels_bgr)
        zip_file.writestr(path, picture_stream.getbuffer())

    logger.info('Done')
    _sep()


def export_tile8(params, config, zip_file, graphics_chunks_handler):
    logger = logging.getLogger()
    logger.info('Exporting tile8')

    partitions_map = config.GRAPHICS_PARTITIONS_MAP
    palette_map = config.GRAPHICS_PALETTE_MAP
    start, count = partitions_map['tile8']
    tile8_manager = pywolf.graphics.Tile8Manager(graphics_chunks_handler, palette_map, start, count)

    for i, tile8 in enumerate(tile8_manager):
        path = 'gfx/{}/tile8__{}.tga'.format(params.short_name, config.TILE8_NAMES[i])
        logger.info('Tile8 [%d/%d]: %r', (i + 1), count, path)
        top_bottom_rgb_image = tile8.image.transpose(Image.FLIP_TOP_BOTTOM).convert('RGB')
        pixels_bgr = bytes(x for pixel in top_bottom_rgb_image.getdata() for x in reversed(pixel))
        tile8_stream = io.BytesIO()
        write_targa_bgrx(tile8_stream, tile8.dimensions, 24, pixels_bgr)
        zip_file.writestr(path, tile8_stream.getbuffer())

    logger.info('Done')
    _sep()


def export_screens(params, config, zip_file, graphics_chunks_handler):
    logger = logging.getLogger()
    logger.info('Exporting DOS screens')

    partitions_map = config.GRAPHICS_PARTITIONS_MAP
    start, count = partitions_map['screens']
    screen_manager = pywolf.graphics.DOSScreenManager(graphics_chunks_handler, start, count)

    for i, screen in enumerate(screen_manager):
        path = 'texts/{}/screens/{}.scr'.format(params.short_name, config.SCREEN_NAMES[i])
        logger.info('DOS Screen [%d/%d]: %r', (i + 1), count, path)
        zip_file.writestr(path, screen.data)

    logger.info('Done')
    _sep()


def export_helparts(params, config, zip_file, graphics_chunks_handler):
    logger = logging.getLogger()
    logger.info('Exporting HelpArt texts')

    partitions_map = config.GRAPHICS_PARTITIONS_MAP
    start, count = partitions_map['helpart']
    helpart_manager = pywolf.graphics.HelpArtManager(graphics_chunks_handler, start, count)

    for i, helpart in enumerate(helpart_manager):
        path = 'texts/{}/helpart/helpart_{}.txt'.format(params.short_name, i)
        logger.info('HelpArt [%d/%d]: %r', (i + 1), count, path)
        zip_file.writestr(path, helpart.encode('ascii'))

    logger.info('Done')
    _sep()


def export_endarts(params, config, zip_file, graphics_chunks_handler):
    logger = logging.getLogger()
    logger.info('Exporting EndArt texts')

    partitions_map = config.GRAPHICS_PARTITIONS_MAP
    start, count = partitions_map['endart']
    endart_manager = pywolf.graphics.EndArtManager(graphics_chunks_handler, start, count)

    for i, endart in enumerate(endart_manager):
        path = 'texts/{}/endart/endart_{}.txt'.format(params.short_name, i)
        logger.info('EndArt [%d/%d]: %r', (i + 1), count, path)
        zip_file.writestr(path, endart.encode('ascii'))

    logger.info('Done')
    _sep()


def export_sampled_sounds(params, config, zip_file, vswap_chunks_handler):
    logger = logging.getLogger()
    logger.info('Exporting sampled sounds')

    start = vswap_chunks_handler.sounds_start
    count = len(vswap_chunks_handler.sounds_infos)
    sample_manager = pywolf.audio.SampledSoundManager(vswap_chunks_handler,
                                                      config.SAMPLED_SOUND_FREQUENCY,
                                                      start, count)
    scale_factor = params.wave_rate / config.SAMPLED_SOUND_FREQUENCY

    for i, sound in enumerate(sample_manager):
        name = config.SAMPLED_SOUND_NAMES[i]
        path = 'sound/{}/sampled/{}.wav'.format(params.short_name, name)
        logger.info('Sampled sound [%d/%d]: %r', (i + 1), count, path)
        samples = bytes(samples_upsample(sound.samples, scale_factor))
        wave_file = io.BytesIO()
        wave_write(wave_file, params.wave_rate, samples)
        zip_file.writestr(path, wave_file.getbuffer())

    logger.info('Done')
    _sep()


def export_musics(params, config, zip_file, audio_chunks_handler):
    logger = logging.getLogger()
    logger.info('Exporting musics')

    start, count = config.AUDIO_PARTITIONS_MAP['music']

    for i in range(count):
        chunk_index = start + i
        name = config.MUSIC_NAMES[i]
        path = 'music/{}/{}.wav'.format(params.short_name, name)
        logger.info('Music [%d/%d]: %r', (i + 1), count, path)
        imf_chunk = audio_chunks_handler[chunk_index]
        wave_path = convert_imf_to_wave(imf_chunk, params.imf2wav_path,
                                        wave_rate=params.wave_rate, imf_rate=params.imf_rate)
        try:
            with open(wave_path, 'rb') as wave_file:
                wave_samples = wave_file.read()
            zip_file.writestr(path, wave_samples)
        finally:
            try:
                os.unlink(wave_path)
            except:
                pass

    logger.info('Done')
    _sep()


def export_adlib_sounds(params, config, zip_file, audio_chunks_handler):
    logger = logging.getLogger()
    logger.info('Exporting AdLib sounds')

    start, count = config.AUDIO_PARTITIONS_MAP['adlib']
    adlib_manager = pywolf.audio.AdLibSoundManager(audio_chunks_handler, start, count)

    for i, sound in enumerate(adlib_manager):
        name = config.ADLIB_SOUND_NAMES[i]
        path = 'sound/{}/adlib/{}.wav'.format(params.short_name, name)
        logger.info('AdLib sound [%d/%d]: %r', (i + 1), count, path)
        imf_chunk = sound.to_imf_chunk()
        wave_path = convert_imf_to_wave(imf_chunk, params.imf2wav_path,
                                        wave_rate=params.wave_rate, imf_rate=params.imf_rate)
        try:
            with open(wave_path, 'rb') as wave_file:
                wave_samples = wave_file.read()
            zip_file.writestr(path, wave_samples)
        finally:
            try:
                os.unlink(wave_path)
            except:
                pass

    logger.info('Done')
    _sep()


def export_buzzer_sounds(params, config, zip_file, audio_chunks_handler):
    logger = logging.getLogger()
    logger.info('Exporting buzzer sounds')

    start, count = config.AUDIO_PARTITIONS_MAP['buzzer']
    buzzer_manager = pywolf.audio.BuzzerSoundManager(audio_chunks_handler, start, count)

    for i, sound in enumerate(buzzer_manager):
        name = config.BUZZER_SOUND_NAMES[i]
        path = 'sound/{}/buzzer/{}.wav'.format(params.short_name, name)
        logger.info('Buzzer sound [%d/%d]: %r', (i + 1), count, path)
        wave_file = io.BytesIO()
        sound.wave_write(wave_file, params.wave_rate)
        zip_file.writestr(path, wave_file.getbuffer())

    logger.info('Done')
    _sep()


def main(*args):
    logger = logging.getLogger()
    stdout_handler = logging.StreamHandler(sys.stdout)
    stdout_handler.setLevel(logging.DEBUG)
    logger.addHandler(stdout_handler)
    logger.setLevel(logging.DEBUG)

    parser = build_argument_parser()
    params = parser.parse_args(args)

    logger.info('Command-line parameters:')
    for key, value in sorted(params.__dict__.items()):
        logger.info('%s = %r', key, value)
    _sep()

    config = CONFIG_WL6  # TODO: import from XML?

    vswap_data_path = os.path.join(params.input_folder, params.vswap_data)
    logger.info('Precaching VSwap chunks: <data>=%r', vswap_data_path)
    vswap_chunks_handler = pywolf.persistence.PrecachedVSwapChunksHandler()
    with open(vswap_data_path, 'rb') as data_file:
        vswap_chunks_handler.load(data_file)
    _sep()

    audio_data_path = os.path.join(params.input_folder, params.audio_data)
    audio_header_path = os.path.join(params.input_folder, params.audio_header)
    logger.info('Precaching audio chunks: <data>=%r, <header>=%r', audio_data_path, audio_header_path)
    audio_chunks_handler = pywolf.persistence.PrecachedAudioChunksHandler()
    with open(audio_data_path, 'rb') as (data_file
    ),   open(audio_header_path, 'rb') as header_file:
        audio_chunks_handler.load(data_file, header_file)
    _sep()

    graphics_data_path = os.path.join(params.input_folder, params.graphics_data)
    graphics_header_path = os.path.join(params.input_folder, params.graphics_header)
    graphics_huffman_path = os.path.join(params.input_folder, params.graphics_huffman)
    logger.info('Precaching graphics chunks: <data>=%r, <header>=%r, <huffman>=%r',
                graphics_data_path, graphics_header_path, graphics_huffman_path)
    graphics_chunks_handler = pywolf.persistence.PrecachedGraphicsChunksHandler()
    with open(graphics_data_path, 'rb') as (data_file
    ),   open(graphics_header_path, 'rb') as (header_file
    ),   open(graphics_huffman_path, 'rb') as huffman_file:
        graphics_chunks_handler.load(data_file, header_file, huffman_file,
                                     config.GRAPHICS_PARTITIONS_MAP)
    _sep()

    maps_data_path = os.path.join(params.input_folder, params.maps_data)
    maps_header_path = os.path.join(params.input_folder, params.maps_header)
    logger.info('Precaching map chunks: <data>=%r, <header>=%r', maps_data_path, maps_header_path)
    map_chunks_handler = pywolf.persistence.PrecachedMapChunksHandler()
    with open(maps_data_path, 'rb') as (data_file
    ),   open(maps_header_path, 'rb') as header_file:
        map_chunks_handler.load(data_file, header_file)
    _sep()

    pk3_path = os.path.join(params.output_folder, params.output_pk3)
    logger.info('Creating PK3 (ZIP/deflated) file: %r', pk3_path)
    with zipfile.ZipFile(pk3_path, 'w', zipfile.ZIP_DEFLATED) as pk3_file:
        _sep()
        export_shaders(params, config, pk3_file)
        export_textures(params, config, pk3_file, vswap_chunks_handler)
        export_sprites(params, config, pk3_file, vswap_chunks_handler)
        export_fonts(params, config, pk3_file, graphics_chunks_handler)
        export_pictures(params, config, pk3_file, graphics_chunks_handler)
        export_tile8(params, config, pk3_file, graphics_chunks_handler)
        export_screens(params, config, pk3_file, graphics_chunks_handler)
        export_helparts(params, config, pk3_file, graphics_chunks_handler)
        export_endarts(params, config, pk3_file, graphics_chunks_handler)

        export_sampled_sounds(params, config, pk3_file, vswap_chunks_handler)
        export_musics(params, config, pk3_file, audio_chunks_handler)
        export_adlib_sounds(params, config, pk3_file, audio_chunks_handler)
        export_buzzer_sounds(params, config, pk3_file, audio_chunks_handler)

        # TODO: export_maps(params, config, pk3_file, map_chunks_handler)
        # TODO: export_models(params, config, pk3_file, ?)

        pass  # TODO: remove line

    logger.info('PK3 archived successfully')


if __name__ == '__main__':
    main(*sys.argv[1:])
