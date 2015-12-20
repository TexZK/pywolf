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
import pywolf.game
from pywolf.graphics import write_targa_bgrx, build_color_image
import pywolf.persistence
from pywolf.utils import stream_pack, find_partition, load_as_module


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
    sort seeThrough
    {{
        clampmap {1!s}
        blendFunc blend
        rgbGen identity
    }}
}}
'''


NORTH  = 0
EAST   = 1
SOUTH  = 2
WEST   = 3
TOP    = 4
BOTTOM = 5

DIR_TO_DISPL = [
    ( 0, -1,  0),
    ( 1,  0,  0),
    ( 0,  1,  0),
    (-1,  0,  0),
    ( 0,  0,  1),
    ( 0,  0, -1),
]

DIR_TO_YAW = [
    90,
    0,
    270,
    180,
    0,
    0,
]

ENEMY_INDEX_TO_DIR = [
    EAST,
    NORTH,
    WEST,
    SOUTH,
]

TURN_TO_YAW = [
    0,
    45,
    90,
    135,
    180,
    225,
    270,
    315,
]

TURN_TO_DISPL = [
    (  1,  0),
    (  1, -1),
    (  0, -1),
    ( -1, -1),
    ( -1,  0),
    ( -1,  1),
    (  0,  1),
    (  1,  1),
]


def build_cuboid_vertices(extreme_a, extreme_b):
    xa, ya, za = extreme_a
    xb, yb, zb = extreme_b
    return [[(xb, yb, zb), (xa, yb, zb), (xa, yb, za), (xb, yb, za)],
            [(xb, ya, zb), (xb, yb, zb), (xb, yb, za), (xb, ya, za)],
            [(xa, ya, zb), (xb, ya, zb), (xb, ya, za), (xa, ya, za)],
            [(xa, yb, zb), (xa, ya, zb), (xa, ya, za), (xa, yb, za)],
            [(xa, yb, zb), (xb, yb, zb), (xb, ya, zb), (xa, ya, zb)],
            [(xb, yb, za), (xa, yb, za), (xa, ya, za), (xb, ya, za)]]


def describe_cuboid_brush(face_vertices, face_shaders, shader_scales, format_line=None,
                          flip_directions=(NORTH, WEST)):
    if format_line is None:
        format_line = ('( {0[0]:.0f} {0[1]:.0f} {0[2]:.0f} ) '
                       '( {1[0]:.0f} {1[1]:.0f} {1[2]:.0f} ) '
                       '( {2[0]:.0f} {2[1]:.0f} {2[2]:.0f} ) '
                       '"{3!s}" 0 0 0 {4:f} {5:f} 0 0 0')
    lines = ['{']
    for direction, shader_name, vertices in zip(range(len(face_vertices)), face_shaders, face_vertices):
        scale_u = shader_scales[0]
        scale_v = shader_scales[1]
        if direction in flip_directions:
            scale_u = -scale_u
        line = format_line.format(vertices[0], vertices[1], vertices[2], shader_name, scale_u, scale_v)
        lines.append(line)
    lines.append('}')
    return lines


class MapExporter(object):  # TODO

    def __init__(self, params, cfg, tilemap, tilemap_index):
        self.params = params
        self.cfg = cfg
        self.tilemap = tilemap
        self.tilemap_index = tilemap_index

        dimensions = tilemap.dimensions
        half_units = params.tile_units / 2
        self.unit_offsets = ((-half_units * dimensions[0]), (half_units * dimensions[1]), 0)

    def tile_to_unit_coords(self, tile_coords):
        tile_units = self.params.tile_units
        return [
            (tile_coords[0] *  tile_units),
            (tile_coords[1] * -tile_units),
        ]

    def center_units(self, tile_coords, unit_offsets=(0, 0, 0), center_z=False):
        units = self.tile_to_unit_coords(tile_coords)
        half = self.params.tile_units / 2
        return [(unit_offsets[0] + units[0] + half),
                (unit_offsets[1] + units[1] + half),
                (unit_offsets[2] + (half if center_z else 0))]

    def describe_textured_cube(self, tile_coords, face_shaders, unit_offsets=(0, 0, 0)):
        center_x, center_y, center_z = self.center_units(tile_coords, unit_offsets, center_z=True)
        half = self.params.tile_units / 2
        extreme_a = ((center_x - half), (center_y - half), (center_z - half))
        extreme_b = ((center_x + half), (center_y + half), (center_z + half))
        face_vertices = build_cuboid_vertices(extreme_a, extreme_b)
        shader_scales = [self.params.texture_scale, self.params.texture_scale]
        return describe_cuboid_brush(face_vertices, face_shaders, shader_scales)

    def describe_textured_sprite(self, tile_coords, face_shader, unit_offsets=(0, 0, 0)):
        center_x, center_y, center_z = self.center_units(tile_coords, unit_offsets, center_z=True)
        half = self.params.tile_units / 2
        extreme_a = ((center_x - (half - 1)), (center_y - 1), (center_z - half))
        extreme_b = ((center_x + (half - 1)), (center_y + 0), (center_z + half))
        face_vertices = build_cuboid_vertices(extreme_a, extreme_b)
        face_shaders = [
            face_shader,
            'common/nodraw',
            'common/nodraw',
            'common/nodraw',
            'common/nodraw',
            'common/nodraw',
        ]
        shader_scales = [self.params.texture_scale, self.params.texture_scale]
        return describe_cuboid_brush(face_vertices, face_shaders, shader_scales)

    def describe_area_brushes(self, tile_coords):  # TODO: support for all floor/ceiling modes of ChaosEdit
        params = self.params
        cfg = self.cfg
        tilemap_index = self.tilemap_index
        tile_units = params.tile_units
        format_palette_texture = '{}_palette/color_0x{:02x}'.format
        lines = []

        face_shaders = [
            'common/caulk',
            'common/caulk',
            'common/caulk',
            'common/caulk',
            'common/caulk',
            format_palette_texture(params.short_name, cfg.CEILING_COLORS[tilemap_index]),
        ]
        offsets = list(self.unit_offsets)
        offsets[2] += tile_units
        lines.extend(self.describe_textured_cube(tile_coords, face_shaders, offsets))

        face_shaders = [
            'common/caulk',
            'common/caulk',
            'common/caulk',
            'common/caulk',
            format_palette_texture(params.short_name, cfg.FLOOR_COLORS[tilemap_index]),
            'common/caulk',
        ]
        offsets = list(self.unit_offsets)
        offsets[2] -= tile_units
        lines.extend(self.describe_textured_cube(tile_coords, face_shaders, offsets))

        return lines

    def describe_wall_brush(self, tile_coords):
        params = self.params
        cfg = self.cfg
        tilemap = self.tilemap
        x, y = tile_coords
        tile = tilemap[x, y]
        partition_map = cfg.TILE_PARTITION_MAP
        pushwall_entity = cfg.ENTITY_PARTITION_MAP['pushwall'][0]
        face_shaders = []

        for direction, displacement in enumerate(DIR_TO_DISPL[:4]):
            facing_coords = [(x + displacement[0]), (y + displacement[1])]
            facing = tilemap.get(facing_coords)
            if facing is None:
                shader = 'common/caulk'
            else:
                if facing[1] == pushwall_entity:
                    facing_partition = 'floor'
                else:
                    facing_partition = find_partition(facing[0], partition_map, count_sign=1)

                if facing_partition == 'wall':
                    shader = 'common/caulk'
                else:
                    if facing_partition == 'floor':
                        texture = tile[0] - partition_map['wall'][0]
                    elif facing_partition in ('door', 'door_elevator', 'door_silver', 'door_gold'):
                        texture = partition_map['door_hinge'][0] - partition_map['wall'][0]
                    else:
                        raise ValueError((tile_coords, facing_partition))

                    shader = '{}_wall/{}__{}'.format(params.short_name, cfg.TEXTURE_NAMES[texture],
                                                     (direction & 1))
            face_shaders.append(shader)

        face_shaders.append('common/caulk')
        face_shaders.append('common/caulk')

        if any(shader != 'common/caulk' for shader in face_shaders):
            return self.describe_textured_cube(tile_coords, face_shaders, self.unit_offsets)
        else:
            return ()

    def describe_sprite(self, tile_coords):
        params = self.params
        cfg = self.cfg
        entity = self.tilemap[tile_coords][1]
        name = cfg.ENTITY_OBJECT_MAP[entity]
        lines = []

        if name in cfg.SOLID_OBJECT_NAMES:
            face_shaders = ['common/clip'] * 6
            lines.extend(self.describe_textured_cube(tile_coords, face_shaders, self.unit_offsets))

        face_shader = '{}_static/{}'.format(params.short_name, name)
        lines.extend(self.describe_textured_sprite(tile_coords, face_shader, self.unit_offsets))

        return lines

    def describe_door(self, tile_coords):
        params = self.params
        cfg = self.cfg
        tile = self.tilemap[tile_coords][0]
        _, texture_name, vertical = cfg.DOOR_MAP[tile]

        trigger_begin = [
            '{',
            'classname func_invisible_user',
            'spawnflags 8  // not_kickable',
            'target door_{:.0f}_{:.0f}'.format(*tile_coords),
            'cursorhint HINT_DOOR',
        ]
        trigger_end = ['}']

        face_shaders = ['common/trigger'] * 6
        trigger_brush = self.describe_textured_cube(tile_coords, face_shaders, self.unit_offsets)

        door_begin = [
            '{',
            'classname func_door',
            'targetname door_{:.0f}_{:.0f}'.format(*tile_coords),
            'angle {:.0f}'.format(270 if vertical else 0),
            'lip 0',
            'dmg 0',
            'speed 64',
            'wait 5',
            'type 1  // needs overridden metallic sounds!',
        ]
        door_end = ['}']

        face_shaders = ['common/clip'] * 6
        clip_lines = self.describe_textured_cube(tile_coords, face_shaders, self.unit_offsets)

        face_shader = '{}_wall/{}__{}'.format(params.short_name, texture_name, int(vertical))
        center_x, center_y, center_z = self.center_units(tile_coords, self.unit_offsets, center_z=True)
        half = self.params.tile_units / 2
        if vertical:
            extreme_a = ((center_x - 1), (center_y - half), (center_z - half))
            extreme_b = ((center_x + 1), (center_y + half), (center_z + half))
        else:
            extreme_a = ((center_x - half), (center_y - 1), (center_z - half))
            extreme_b = ((center_x + half), (center_y + 1), (center_z + half))
        face_vertices = build_cuboid_vertices(extreme_a, extreme_b)
        face_shaders = [
            face_shader,
            face_shader,
            face_shader,
            face_shader,
            'common/nodraw',
            'common/nodraw',
        ]
        shader_scales = [self.params.texture_scale, self.params.texture_scale]
        panel_lines = describe_cuboid_brush(face_vertices, face_shaders, shader_scales,
                                            flip_directions=(EAST, WEST))

        return (trigger_begin + trigger_brush + trigger_end +
                door_begin + clip_lines + panel_lines + door_end)

    def describe_worldspawn(self):
        params = self.params
        cfg = self.cfg
        dimensions = self.tilemap.dimensions
        tilemap = self.tilemap
        pushwall_entity = cfg.ENTITY_PARTITION_MAP['pushwall'][0]
        music_name = cfg.MUSIC_NAMES[cfg.TILEMAP_MUSIC_INDICES[self.tilemap_index]]

        lines = ['{',
                 'classname worldspawn',
                 'message "{}"'.format(tilemap.name),
                 'music "music/{}/{}"'.format(params.short_name, music_name),
                 'ambient 100',
                 '_color "1 1 1"']

        for tile_y in range(dimensions[1]):
            for tile_x in range(dimensions[0]):
                tile_coords = (tile_x, tile_y)
                tile = tilemap[tile_coords]

                if tile[0]:
                    partition = find_partition(tile[0], cfg.TILE_PARTITION_MAP, count_sign=1)
                    lines.append('// {} @ {!r} = tile 0x{:04X}'.format(partition, tile_coords, tile[0]))

                    if (partition in ('floor', 'door', 'door_silver', 'door_gold', 'door_elevator') or
                        tile[1] == pushwall_entity):
                        lines.extend(self.describe_area_brushes(tile_coords))
                    elif partition == 'wall':
                        lines.extend(self.describe_wall_brush(tile_coords))
                    else:
                        raise ValueError((tile_coords, partition))

                if tile[1]:
                    object_name = cfg.ENTITY_OBJECT_MAP.get(tile[1])
                    if object_name and object_name in cfg.STATIC_OBJECT_NAMES:
                        lines += self.describe_sprite(tile_coords)

        lines.append('}  // worldspawn')
        return lines

    def describe_player_start(self, tile_coords):
        tile = self.tilemap[tile_coords]
        index = tile[1] - self.cfg.ENTITY_PARTITION_MAP['start'][0]
        origin = self.center_units(tile_coords, self.unit_offsets)
        origin[2] += 32
        return [
            '{',
            'classname info_player_start',
            'origin "{:.0f} {:.0f} {:.0f}"'.format(*origin),
            'angle {:.0f}'.format(DIR_TO_YAW[index]),
            '}',
        ]

    def describe_turn(self, tile_coords, turn_coords):
        tilemap = self.tilemap
        index = tilemap[tile_coords][1] - self.cfg.ENTITY_PARTITION_MAP['turn'][0]
        origin = self.center_units(tile_coords, self.unit_offsets, center_z=True)
        step = TURN_TO_DISPL[index]
        target_coords = [(tile_coords[0] + step[0]), (tile_coords[1] + step[1])]
        lines = []

        found = False
        while tilemap.check_coords(target_coords):
            for coords in turn_coords:
                if coords[0] == target_coords[0] and coords[1] == target_coords[1]:
                    found = True
                    break
            else:
                target_coords[0] += step[0]
                target_coords[1] += step[1]
            if found:
                break
        else:
            raise ValueError('no target turning point for the one at {!r}'.format(tile_coords))

        # TODO: ai_target

        lines += [
            '{',
            'classname path_corner',
            'origin "{:.0f} {:.0f} {:.0f}"'.format(*origin),
            'angle {:.0f}'.format(TURN_TO_YAW[index]),
            'targetname corner_{:.0f}_{:.0f}'.format(*tile_coords),
            'target corner_{:.0f}_{:.0f}'.format(*target_coords),
            '}',
        ]

        return lines

    def describe_enemy(self, tile_coords, turn_tiles):
        return ()  # TODO

    def describe_object(self, tile_coords):
        return ()  # TODO

    def describe_pushwall(self, tile_coords):
        return ()  # TODO

    def describe_entities(self):  # TODO
        cfg = self.cfg
        dimensions = self.tilemap.dimensions
        tilemap = self.tilemap
        lines = []
        turn_coords = []
        enemy_coords = []

        for tile_y in range(dimensions[1]):
            for tile_x in range(dimensions[0]):
                tile_coords = (tile_x, tile_y)
                tile = tilemap[tile_coords]

                if tile[1]:
                    partition = find_partition(tile[1], cfg.ENTITY_PARTITION_MAP, count_sign=-1)
                    lines.append('// {} @ {!r} = entity 0x{:04X}'.format(partition, tile_coords, tile[1]))

                    if partition == 'start':
                        lines += self.describe_player_start(tile_coords)
                    elif partition == 'turn':
                        turn_coords.append(tile_coords)
                    elif partition == 'enemy':
                        enemy_coords.append(tile_coords)
                    elif partition == 'pushwall':
                        lines += self.describe_pushwall(tile_coords)
                    elif partition == 'object' and cfg.ENTITY_OBJECT_MAP[tile[1]] in cfg.COLLECTABLE_OBJECT_NAMES:
                        lines += self.describe_object(tile_coords)

                if tile[0]:
                    if tile[0] in cfg.DOOR_MAP:
                        lines.append('// {} @ {!r} = door 0x{:04X}'.format(partition, tile_coords, tile[0]))
                        lines += self.describe_door(tile_coords)

        for coords in turn_coords:
            lines += self.describe_turn(coords, turn_coords)

        for coords in enemy_coords:
            lines += self.describe_enemy(coords, turn_coords)

        return lines

    def describe_tilemap(self):
        tilemap = self.tilemap
        tilemap_index = self.tilemap_index
        lines = ['// map #{}: "{}"'.format(tilemap_index, tilemap.name)]
        lines += self.describe_worldspawn()
        lines += self.describe_entities()
        return lines


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
    group.add_argument('--cfg')
    group.add_argument('--short-name', default='wolf3d')
    group.add_argument('--wave-rate', default=44100, type=int)
    group.add_argument('--imf-rate', default=700, type=int)
    group.add_argument('--imf2wav-path', default=IMF2WAV_PATH)
    group.add_argument('--tile-units', default=96, type=int)
    group.add_argument('--texture-scale', default=1.5, type=float)

    return parser


def _sep():
    logger = logging.getLogger()
    logger.info('-' * 80)


def export_textures(params, cfg, zip_file, vswap_chunks_handler):
    logger = logging.getLogger()
    logger.info('Exporting textures')

    start = 0
    count = vswap_chunks_handler.sprites_start - start
    texture_manager = pywolf.graphics.TextureManager(vswap_chunks_handler,
                                                     cfg.GRAPHICS_PALETTE_MAP[...],
                                                     cfg.SPRITE_DIMENSIONS,
                                                     start, count)

    for i, texture in enumerate(texture_manager):
        name = cfg.TEXTURE_NAMES[i >> 1]
        path = 'textures/{}_wall/{}__{}.tga'.format(params.short_name, name, (i & 1))
        logger.info('Texture [%d/%d]: %r', (i + 1), count, path)
        top_bottom_rgb_image = texture.image.transpose(Image.FLIP_TOP_BOTTOM).convert('RGB')
        pixels_bgr = bytes(x for pixel in top_bottom_rgb_image.getdata() for x in reversed(pixel))
        texture_stream = io.BytesIO()
        write_targa_bgrx(texture_stream, cfg.TEXTURE_DIMENSIONS, 24, pixels_bgr)
        zip_file.writestr(path, texture_stream.getbuffer())

    palette = cfg.GRAPHICS_PALETTE
    for i, color in enumerate(palette):
        path = 'textures/{}_palette/color_0x{:02x}.tga'.format(params.short_name, i)
        logger.info('Texture palette color [%d/%d]: %r, (0x%02X, 0x%02X, 0x%02X)',
                    (i + 1), len(palette), path, *color)
        image = build_color_image(cfg.TEXTURE_DIMENSIONS, color)
        top_bottom_rgb_image = image.transpose(Image.FLIP_TOP_BOTTOM).convert('RGB')
        pixels_bgr = bytes(x for pixel in top_bottom_rgb_image.getdata() for x in reversed(pixel))
        texture_stream = io.BytesIO()
        write_targa_bgrx(texture_stream, cfg.TEXTURE_DIMENSIONS, 24, pixels_bgr)
        zip_file.writestr(path, texture_stream.getbuffer())

    logger.info('Done')
    _sep()


def write_texture_shaders(params, cfg, shader_file):
    for name in cfg.TEXTURE_NAMES:
        for j in range(2):
            shader_name = 'textures/{}_wall/{}__{}'.format(params.short_name, name, j)
            path = shader_name + '.tga'
            shader_file.write(TEXTURE_SHADER_TEMPLATE.format(shader_name, path))

    palette = cfg.GRAPHICS_PALETTE
    for i in range(len(palette)):
        shader_name = 'textures/{}_palette/color_0x{:02x}'.format(params.short_name, i)
        path = shader_name + '.tga'
        shader_file.write(TEXTURE_SHADER_TEMPLATE.format(shader_name, path))


def write_static_shaders(params, cfg, shader_file):
    for name in cfg.STATIC_OBJECT_NAMES:
        shader_name = 'textures/{}_static/{}'.format(params.short_name, name)
        path = 'sprites/{}/{}.tga'.format(params.short_name, name)
        shader_file.write(SPRITE_SHADER_TEMPLATE.format(shader_name, path))


def export_shaders(params, cfg, zip_file):  # TODO: split shaders
    logger = logging.getLogger()
    logger.info('Exporting shaders')

    script_name = '{}_static.shader'.format(params.short_name)
    shader_text_stream = io.StringIO()
    write_static_shaders(params, cfg, shader_text_stream)
    zip_file.writestr('scripts/{}'.format(script_name), shader_text_stream.getvalue().encode())
    folder = os.path.join(params.output_folder, 'scripts')
    os.makedirs(folder, exist_ok=True)
    with open(os.path.join(folder, script_name), 'wt') as shader_file:
        shader_file.write(shader_text_stream.getvalue())

    logger.info('Done')
    _sep()


def export_sprites(params, cfg, zip_file, vswap_chunks_handler):
    logger = logging.getLogger()
    logger.info('Exporting sprites')

    start = vswap_chunks_handler.sprites_start
    count = vswap_chunks_handler.sounds_start - start
    sprite_manager = pywolf.graphics.SpriteManager(vswap_chunks_handler,
                                                   cfg.GRAPHICS_PALETTE_MAP[...],
                                                   cfg.SPRITE_DIMENSIONS,
                                                   start, count)

    for i, sprite in enumerate(sprite_manager):
        name = cfg.SPRITE_NAMES[i]
        path = 'sprites/{}/{}.tga'.format(params.short_name, name)
        logger.info('Sprite [%d/%d]: %r', (i + 1), count, path)
        top_bottom_rgba_image = sprite.image.transpose(Image.FLIP_TOP_BOTTOM).convert('RGBA')
        pixels_bgra = bytes(x for pixel in top_bottom_rgba_image.getdata()
                            for x in [pixel[2], pixel[1], pixel[0], pixel[3]])
        sprite_stream = io.BytesIO()
        write_targa_bgrx(sprite_stream, cfg.SPRITE_DIMENSIONS, 32, pixels_bgra)
        zip_file.writestr(path, sprite_stream.getbuffer())

    logger.info('Done')
    _sep()


# TODO: compact+paged glyph placement
def export_fonts(params, cfg, zip_file, graphics_chunks_handler, missing_char='?',
                 texture_dimensions=(256, 256)):

    logger = logging.getLogger()
    logger.info('Exporting fonts')

    partitions_map = cfg.GRAPHICS_PARTITIONS_MAP
    palette = cfg.GRAPHICS_PALETTE_MAP[...]
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


def export_pictures(params, cfg, zip_file, graphics_chunks_handler):
    logger = logging.getLogger()
    logger.info('Exporting pictures')

    partitions_map = cfg.GRAPHICS_PARTITIONS_MAP
    palette_map = cfg.GRAPHICS_PALETTE_MAP
    start, count = partitions_map['pics']
    picture_manager = pywolf.graphics.PictureManager(graphics_chunks_handler, palette_map, start, count)

    for i, picture in enumerate(picture_manager):
        path = 'gfx/{}/{}.tga'.format(params.short_name, cfg.PICTURE_NAMES[i])
        logger.info('Picture [%d/%d]: %r', (i + 1), count, path)
        top_bottom_rgb_image = picture.image.transpose(Image.FLIP_TOP_BOTTOM).convert('RGB')
        pixels_bgr = bytes(x for pixel in top_bottom_rgb_image.getdata() for x in reversed(pixel))
        picture_stream = io.BytesIO()
        write_targa_bgrx(picture_stream, picture.dimensions, 24, pixels_bgr)
        zip_file.writestr(path, picture_stream.getbuffer())

    logger.info('Done')
    _sep()


def export_tile8(params, cfg, zip_file, graphics_chunks_handler):
    logger = logging.getLogger()
    logger.info('Exporting tile8')

    partitions_map = cfg.GRAPHICS_PARTITIONS_MAP
    palette_map = cfg.GRAPHICS_PALETTE_MAP
    start, count = partitions_map['tile8']
    tile8_manager = pywolf.graphics.Tile8Manager(graphics_chunks_handler, palette_map, start, count)

    for i, tile8 in enumerate(tile8_manager):
        path = 'gfx/{}/tile8__{}.tga'.format(params.short_name, cfg.TILE8_NAMES[i])
        logger.info('Tile8 [%d/%d]: %r', (i + 1), count, path)
        top_bottom_rgb_image = tile8.image.transpose(Image.FLIP_TOP_BOTTOM).convert('RGB')
        pixels_bgr = bytes(x for pixel in top_bottom_rgb_image.getdata() for x in reversed(pixel))
        tile8_stream = io.BytesIO()
        write_targa_bgrx(tile8_stream, tile8.dimensions, 24, pixels_bgr)
        zip_file.writestr(path, tile8_stream.getbuffer())

    logger.info('Done')
    _sep()


def export_screens(params, cfg, zip_file, graphics_chunks_handler):
    logger = logging.getLogger()
    logger.info('Exporting DOS screens')

    partitions_map = cfg.GRAPHICS_PARTITIONS_MAP
    start, count = partitions_map['screens']
    screen_manager = pywolf.graphics.DOSScreenManager(graphics_chunks_handler, start, count)

    for i, screen in enumerate(screen_manager):
        path = 'texts/{}/screens/{}.scr'.format(params.short_name, cfg.SCREEN_NAMES[i])
        logger.info('DOS Screen [%d/%d]: %r', (i + 1), count, path)
        zip_file.writestr(path, screen.data)

    logger.info('Done')
    _sep()


def export_helparts(params, cfg, zip_file, graphics_chunks_handler):
    logger = logging.getLogger()
    logger.info('Exporting HelpArt texts')

    partitions_map = cfg.GRAPHICS_PARTITIONS_MAP
    start, count = partitions_map['helpart']
    helpart_manager = pywolf.graphics.TextArtManager(graphics_chunks_handler, start, count)

    for i, helpart in enumerate(helpart_manager):
        path = 'texts/{}/helpart/helpart_{}.txt'.format(params.short_name, i)
        logger.info('HelpArt [%d/%d]: %r', (i + 1), count, path)
        zip_file.writestr(path, helpart.encode('ascii'))

    logger.info('Done')
    _sep()


def export_endarts(params, cfg, zip_file, graphics_chunks_handler):
    logger = logging.getLogger()
    logger.info('Exporting EndArt texts')

    partitions_map = cfg.GRAPHICS_PARTITIONS_MAP
    start, count = partitions_map['endart']
    endart_manager = pywolf.graphics.TextArtManager(graphics_chunks_handler, start, count)

    for i, endart in enumerate(endart_manager):
        path = 'texts/{}/endart/endart_{}.txt'.format(params.short_name, i)
        logger.info('EndArt [%d/%d]: %r', (i + 1), count, path)
        zip_file.writestr(path, endart.encode('ascii'))

    logger.info('Done')
    _sep()


def export_sampled_sounds(params, cfg, zip_file, vswap_chunks_handler):
    logger = logging.getLogger()
    logger.info('Exporting sampled sounds')

    start = vswap_chunks_handler.sounds_start
    count = len(vswap_chunks_handler.sounds_infos)
    sample_manager = pywolf.audio.SampledSoundManager(vswap_chunks_handler,
                                                      cfg.SAMPLED_SOUND_FREQUENCY,
                                                      start, count)
    scale_factor = params.wave_rate / cfg.SAMPLED_SOUND_FREQUENCY

    for i, sound in enumerate(sample_manager):
        name = cfg.SAMPLED_SOUND_NAMES[i]
        path = 'sound/{}/sampled/{}.wav'.format(params.short_name, name)
        logger.info('Sampled sound [%d/%d]: %r', (i + 1), count, path)
        samples = bytes(samples_upsample(sound.samples, scale_factor))
        wave_file = io.BytesIO()
        wave_write(wave_file, params.wave_rate, samples)
        zip_file.writestr(path, wave_file.getbuffer())

    logger.info('Done')
    _sep()


def export_musics(params, cfg, zip_file, audio_chunks_handler):
    logger = logging.getLogger()
    logger.info('Exporting musics')

    start, count = cfg.AUDIO_PARTITIONS_MAP['music']

    for i in range(count):
        chunk_index = start + i
        name = cfg.MUSIC_NAMES[i]
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


def export_adlib_sounds(params, cfg, zip_file, audio_chunks_handler):
    logger = logging.getLogger()
    logger.info('Exporting AdLib sounds')

    start, count = cfg.AUDIO_PARTITIONS_MAP['adlib']
    adlib_manager = pywolf.audio.AdLibSoundManager(audio_chunks_handler, start, count)

    for i, sound in enumerate(adlib_manager):
        name = cfg.ADLIB_SOUND_NAMES[i]
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


def export_buzzer_sounds(params, cfg, zip_file, audio_chunks_handler):
    logger = logging.getLogger()
    logger.info('Exporting buzzer sounds')

    start, count = cfg.AUDIO_PARTITIONS_MAP['buzzer']
    buzzer_manager = pywolf.audio.BuzzerSoundManager(audio_chunks_handler, start, count)

    for i, sound in enumerate(buzzer_manager):
        name = cfg.BUZZER_SOUND_NAMES[i]
        path = 'sound/{}/buzzer/{}.wav'.format(params.short_name, name)
        logger.info('Buzzer sound [%d/%d]: %r', (i + 1), count, path)
        wave_file = io.BytesIO()
        sound.wave_write(wave_file, params.wave_rate)
        zip_file.writestr(path, wave_file.getbuffer())

    logger.info('Done')
    _sep()


def export_tilemaps(params, cfg, zip_file, audio_chunks_handler):  # TODO
    logger = logging.getLogger()
    logger.info('Exporting tilemaps (Q3Map2 *.map + RTCW *.ai)')

    start, count = (0, 60)  # FIXME: replace with map descriptors
    tilemap_manager = pywolf.game.TileMapManager(audio_chunks_handler, start, count)

    for i, tilemap in enumerate(tilemap_manager):
        folder = os.path.join(params.output_folder, 'maps', params.short_name)
        os.makedirs(folder, exist_ok=True)
        path = os.path.join(folder, (tilemap.name + '.map'))
        logger.info('TileMap [%d/%d]: %r', (i + 1), count, path)

        exporter = MapExporter(params, cfg, tilemap, i)
        description = exporter.describe_tilemap()
        with open(path, 'wt') as map_file:
            for line in description:
                map_file.write(line)
                map_file.write('\n')

        break  # XXX: testing only map 1

        # TODO: *.ai

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

    cfg = load_as_module('cfg', params.cfg)

    vswap_data_path = os.path.join(params.input_folder, params.vswap_data)
    logger.info('Precaching VSwap chunks: <data>=%r', vswap_data_path)
    vswap_chunks_handler = pywolf.persistence.VSwapChunksHandler()
    with open(vswap_data_path, 'rb') as data_file:
        vswap_chunks_handler.load(data_file)
        vswap_chunks_handler = pywolf.persistence.PrecachedChunksHandler(vswap_chunks_handler)
    _sep()

    audio_data_path = os.path.join(params.input_folder, params.audio_data)
    audio_header_path = os.path.join(params.input_folder, params.audio_header)
    logger.info('Precaching audio chunks: <data>=%r, <header>=%r', audio_data_path, audio_header_path)
    audio_chunks_handler = pywolf.persistence.AudioChunksHandler()
    with open(audio_data_path, 'rb') as (data_file
    ),   open(audio_header_path, 'rb') as header_file:
        audio_chunks_handler.load(data_file, header_file)
        audio_chunks_handler = pywolf.persistence.PrecachedChunksHandler(audio_chunks_handler)
    _sep()

    graphics_data_path = os.path.join(params.input_folder, params.graphics_data)
    graphics_header_path = os.path.join(params.input_folder, params.graphics_header)
    graphics_huffman_path = os.path.join(params.input_folder, params.graphics_huffman)
    logger.info('Precaching graphics chunks: <data>=%r, <header>=%r, <huffman>=%r',
                graphics_data_path, graphics_header_path, graphics_huffman_path)
    graphics_chunks_handler = pywolf.persistence.GraphicsChunksHandler()
    with open(graphics_data_path, 'rb') as (data_file
    ),   open(graphics_header_path, 'rb') as (header_file
    ),   open(graphics_huffman_path, 'rb') as huffman_file:
        graphics_chunks_handler.load(data_file, header_file, huffman_file, cfg.GRAPHICS_PARTITIONS_MAP)
        graphics_chunks_handler = pywolf.persistence.PrecachedChunksHandler(graphics_chunks_handler)
    _sep()

    maps_data_path = os.path.join(params.input_folder, params.maps_data)
    maps_header_path = os.path.join(params.input_folder, params.maps_header)
    logger.info('Precaching map chunks: <data>=%r, <header>=%r', maps_data_path, maps_header_path)
    tilemap_chunks_handler = pywolf.persistence.MapChunksHandler()
    with open(maps_data_path, 'rb') as (data_file
    ),   open(maps_header_path, 'rb') as header_file:
        tilemap_chunks_handler.load(data_file, header_file)
        tilemap_chunks_handler = pywolf.persistence.PrecachedChunksHandler(tilemap_chunks_handler)
    _sep()

    pk3_path = os.path.join(params.output_folder, params.output_pk3)
    logger.info('Creating PK3 (ZIP/deflated) file: %r', pk3_path)
    with zipfile.ZipFile(pk3_path, 'w', zipfile.ZIP_DEFLATED) as pk3_file:  # TODO: split PK3 files
        _sep()
        export_tilemaps(params, cfg, pk3_file, tilemap_chunks_handler)  # FIXME: PK3 not needed
#XXX
        export_shaders(params, cfg, pk3_file)
        export_textures(params, cfg, pk3_file, vswap_chunks_handler)
        export_sprites(params, cfg, pk3_file, vswap_chunks_handler)
#XXX        export_fonts(params, cfg, pk3_file, graphics_chunks_handler)
        export_pictures(params, cfg, pk3_file, graphics_chunks_handler)
        export_tile8(params, cfg, pk3_file, graphics_chunks_handler)
#XXX        export_screens(params, cfg, pk3_file, graphics_chunks_handler)
#XXX        export_helparts(params, cfg, pk3_file, graphics_chunks_handler)
#XXX        export_endarts(params, cfg, pk3_file, graphics_chunks_handler)

        export_sampled_sounds(params, cfg, pk3_file, vswap_chunks_handler)
#XXX        export_musics(params, cfg, pk3_file, audio_chunks_handler)
        export_adlib_sounds(params, cfg, pk3_file, audio_chunks_handler)
        export_buzzer_sounds(params, cfg, pk3_file, audio_chunks_handler)

        # TODO: export_models(params, cfg, pk3_file, ?)

        pass  # TODO: remove line

    logger.info('PK3 archived successfully')


if __name__ == '__main__':
    main(*sys.argv[1:])
