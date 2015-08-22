'''
@author: Andrea Zoppi
'''

import sys
import argparse
import os
import io
import logging

import pywolf.persistence
import pywolf.configs.wl6 as CONFIG_WL6
import zipfile


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
        path = 'textures/{}__{}.png'.format(name, (i & 1))
        logger.info('Texture [%d/%d]: %r', i, count, path)
        texture_file = io.BytesIO()
        texture.image.save(texture_file, format='PNG')
        zip_file.writestr(path, texture_file.getvalue())


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
        path = 'sprites/{}.png'.format(name)
        logger.info('Sprite [%d/%d]: %r', i, count, path)
        sprite_file = io.BytesIO()
        sprite.image.save(sprite_file, format='PNG')
        zip_file.writestr(path, sprite_file.getvalue())


def main(*args):  # TODO
    logger = logging.getLogger()
    stdout_handler = logging.StreamHandler(sys.stdout)
    stdout_handler.setLevel(logging.DEBUG)
    logger.addHandler(stdout_handler)
    logger.setLevel(logging.DEBUG)

    print(args)
    parser = build_argument_parser()
    params = parser.parse_args(args)

    config = CONFIG_WL6  # TODO

    vswap_chunks_handler = pywolf.persistence.PrecachedVSwapChunksHandler()
    with open(os.path.join(params.input_folder, params.vswap_data), 'rb') as data_file:
        vswap_chunks_handler.load(data_file)

#     audio_chunks_handler = pywolf.persistence.PrecachedAudioChunksHandler()
#     with open(os.path.join(params.input_folder, params.audio_header), 'rb') as (header_file
#     ),   open(os.path.join(params.input_folder, params.audio_data), 'rb') as data_file:
#         audio_chunks_handler.load(data_file, header_file)

#     graphics_chunks_handler = pywolf.persistence.PrecachedGraphicsChunksHandler()
#     with open(os.path.join(params.input_folder, params.graphics_header), 'rb') as (header_file
#     ),   open(os.path.join(params.input_folder, params.graphics_data), 'rb') as (data_file
#     ),   open(os.path.join(params.input_folder, params.graphics_huffman), 'rb') as huffman_file:
#         graphics_chunks_handler.load(data_file, header_file, huffman_file,
#                                      config.GRAPHICS_PARTITIONS_MAP)

#     map_chunks_handler = pywolf.persistence.PrecachedMapChunksHandler()
#     with open(os.path.join(params.input_folder, params.maps_header), 'rb') as (header_file
#     ),   open(os.path.join(params.input_folder, params.maps_data), 'rb') as data_file:
#         map_chunks_handler.load(data_file, header_file)

    with zipfile.ZipFile(os.path.join(params.output_folder, params.output_pk3), 'w', zipfile.ZIP_DEFLATED) as zip_file:
        export_textures(params, config, zip_file, vswap_chunks_handler)
        export_sprites(params, config, zip_file, vswap_chunks_handler)


    pass


if __name__ == '__main__':
    main(*sys.argv[1:])
