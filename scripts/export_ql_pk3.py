# TODO: create Exporter class(es)
# TODO: break export loops into single item calls with wrapping loop
# TODO: allow export to normal file, PK3 being an option (like with open(file_object|path))
'''
@author: Andrea Zoppi
'''

import argparse
import collections
import io
import logging
import os
import sys
import zipfile

from PIL import Image

import numpy as np
from pywolf.audio import samples_upsample, wave_write, convert_imf_to_wave, convert_wave_to_ogg
import pywolf.game
from pywolf.graphics import write_targa_bgrx, build_color_image
import pywolf.persistence
from pywolf.utils import find_partition, load_as_module


IMF2WAV_PATH = os.path.join('..', 'tools', 'imf2wav')
OGGENC2_PATH = os.path.join('..', 'tools', 'oggenc2')


TEXTURE_SHADER_TEMPLATE = '''
{0!s}
{{
    qer_editorimage {1!s}
    noMipMaps
    {{
        map {1!s}
        rgbGen identityLighting
    }}
}}
'''

SPRITE_SHADER_TEMPLATE = '''
{0!s}
{{
    qer_editorimage {1!s}
    noMipMaps
    deformVertexes autoSprite2
    surfaceparm trans
    surfaceparm nonsolid
    cull none
    {{
        clampmap {1!s}
        alphaFunc GT0
        rgbGen identityLighting
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


def _force_unlink(*paths):
    for path in paths:
        try:
            os.unlink(path)
        except:
            pass


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
                          flip_directions=(NORTH, WEST), content_flags=None, surface_flags=None):
    if format_line is None:
        format_line = ('( {0[0]:.0f} {0[1]:.0f} {0[2]:.0f} ) '
                       '( {1[0]:.0f} {1[1]:.0f} {1[2]:.0f} ) '
                       '( {2[0]:.0f} {2[1]:.0f} {2[2]:.0f} ) '
                       '"{3!s}" 0 0 0 {4:f} {5:f} {6:d} {7:d} 0')

    if content_flags is None:
        content_flags = (0, 0, 0, 0, 0, 0)

    if surface_flags is None:
        surface_flags = (0, 0, 0, 0, 0, 0)

    lines = ['{']
    arrays = zip(range(len(face_vertices)), face_shaders, face_vertices, surface_flags, content_flags)
    for direction, shader_name, vertices, surface_flags, content_flags in arrays:
        scale_u = shader_scales[0]
        scale_v = shader_scales[1]
        if direction in flip_directions:
            scale_u = -scale_u
        line = format_line.format(vertices[0], vertices[1], vertices[2],
                                  shader_name, scale_u, scale_v,
                                  content_flags, surface_flags)  # TODO: make as arrays?
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

        self.tile_partition_cache = {}
        self.entity_partition_cache = {}

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
        shader_scales = [self.params.shader_scale, self.params.shader_scale]
        return describe_cuboid_brush(face_vertices, face_shaders, shader_scales)

    def describe_textured_sprite(self, tile_coords, face_shader, unit_offsets=(0, 0, 0)):
        center_x, center_y, center_z = self.center_units(tile_coords, unit_offsets, center_z=True)
        half = self.params.tile_units / 2
        extreme_a = ((center_x - half), (center_y - 1), (center_z - half - 1))
        extreme_b = ((center_x + half), (center_y + 0), (center_z + half))
        face_vertices = build_cuboid_vertices(extreme_a, extreme_b)
        face_shaders = [
            face_shader,
            'common/nodrawnonsolid',
            'common/nodrawnonsolid',
            'common/nodrawnonsolid',
            'common/nodrawnonsolid',
            'common/nodrawnonsolid',
        ]
        shader_scales = [self.params.shader_scale, self.params.shader_scale]
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
            facing_coords = ((x + displacement[0]), (y + displacement[1]))
            facing = tilemap.get(facing_coords)
            if facing is None:
                shader = 'common/caulk'
            else:
                if facing[1] == pushwall_entity:
                    facing_partition = 'floor'
                else:
                    facing_partition = find_partition(facing[0], partition_map, count_sign=1,
                                                      cache=self.tile_partition_cache)

                if facing_partition == 'wall':
                    shader = 'common/caulk'
                else:
                    if facing_partition == 'floor':
                        texture = tile[0] - partition_map['wall'][0]
                    elif facing_partition in ('door', 'door_elevator', 'door_silver', 'door_gold'):
                        texture = partition_map['door_hinge'][0] - partition_map['wall'][0]
                    else:
                        raise ValueError((tile_coords, facing_partition))
                    shader = '{}_wall/{}__{}'.format(params.short_name, cfg.TEXTURE_NAMES[texture], (direction & 1))
            face_shaders.append(shader)

        face_shaders += ['common/caulk'] * 2

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

    def describe_collectable(self, tile_coords):
        params = self.params
        cfg = self.cfg
        entity = self.tilemap[tile_coords][1]
        name = cfg.ENTITY_OBJECT_MAP[entity]
        lines = []

        if name in cfg.SOLID_OBJECT_NAMES:
            face_shaders = ['common/clip'] * 6
            lines.extend(self.describe_textured_cube(tile_coords, face_shaders, self.unit_offsets))

        face_shader = '{}_collectable/{}'.format(params.short_name, name)
        lines.extend(self.describe_textured_sprite(tile_coords, face_shader, self.unit_offsets))

        return lines

    def describe_door(self, tile_coords):
        params = self.params
        cfg = self.cfg
        tile = self.tilemap[tile_coords][0]
        _, texture_name, vertical = cfg.DOOR_MAP[tile]
        center_x, center_y, center_z = self.center_units(tile_coords, self.unit_offsets, center_z=True)
        half = self.params.tile_units / 2
        shader_scales = [self.params.shader_scale, self.params.shader_scale]

        trigger_begin = [
            '{',
            'classname trigger_multiple',
            'target "door_{:.0f}_{:.0f}_open"'.format(*tile_coords),
            'wait {}'.format(params.door_trigger_wait),
        ]
        trigger_end = ['}']

        face_shaders = ['common/trigger'] * 6
        trigger_brush = self.describe_textured_cube(tile_coords, face_shaders, self.unit_offsets)

        speaker_open_entity = [
            '{',
            'classname target_speaker',
            'origin "{:.0f} {:.0f} {:.0f}"'.format(center_x, center_y, center_z),
            'targetname "door_{:.0f}_{:.0f}_open"'.format(*tile_coords),
            'noise "sound/{}/{}"'.format(params.short_name, 'sampled/door__open'),  # FIXME: filename
            '}',
        ]

        delay_entity = [
            '{',
            'classname target_delay',
            'origin "{:.0f} {:.0f} {:.0f}"'.format(center_x, center_y, center_z),
            'targetname "door_{:.0f}_{:.0f}_open"'.format(*tile_coords),
            'target "door_{:.0f}_{:.0f}_close"'.format(*tile_coords),
            'wait {}'.format((params.door_trigger_wait + params.door_wait) / 2),
            '}',
        ]

        speaker_close_entity = [
            '{',
            'classname target_speaker',
            'origin "{:.0f} {:.0f} {:.0f}"'.format(center_x, center_y, center_z),
            'targetname "door_{:.0f}_{:.0f}_close"'.format(*tile_coords),
            'noise "sound/{}/{}"'.format(params.short_name, 'sampled/door__close'),  # FIXME: filename
            '}',
        ]

        # Door entity
        door_begin = [
            '{',
            'classname func_door',
            'targetname "door_{:.0f}_{:.0f}_open"'.format(*tile_coords),
            'angle {:.0f}'.format(270 if vertical else 0),
            'lip 2',
            'dmg 0',
            'health 0',
            'wait {}'.format(params.door_wait),
            'speed {}'.format(params.door_speed),
        ]
        door_end = ['}']

        # Door brush
        face_shader = '{}_wall/{}__{}'.format(params.short_name, texture_name, int(vertical))
        if vertical:
            extreme_a = ((center_x - 1), (center_y - half), (center_z - half))
            extreme_b = ((center_x + 1), (center_y + half), (center_z + half))
            face_shaders = [
                'common/caulk',
                face_shader,
                'common/caulk',
                face_shader,
                'common/caulk',
                'common/caulk',
            ]
        else:
            extreme_a = ((center_x - half), (center_y - 1), (center_z - half))
            extreme_b = ((center_x + half), (center_y + 1), (center_z + half))
            face_shaders = [
                face_shader,
                'common/caulk',
                face_shader,
                'common/caulk',
                'common/caulk',
                'common/caulk',
            ]
        face_vertices = build_cuboid_vertices(extreme_a, extreme_b)
        door_brush = describe_cuboid_brush(face_vertices, face_shaders, shader_scales, flip_directions=(EAST, WEST))

        # Underworld brush
        face_shaders = ['common/caulk'] * 6
        unit_offsets = list(self.unit_offsets)
        unit_offsets[2] += params.underworld_offset
        door_underworld_brush = self.describe_textured_cube(tile_coords, face_shaders, unit_offsets)

        return (trigger_begin + trigger_brush + trigger_end +
                speaker_open_entity + delay_entity + speaker_close_entity +
                door_begin + door_brush + door_underworld_brush + door_end)

    def describe_door_hint(self, tile_coords):
        cfg = self.cfg
        tile = self.tilemap[tile_coords][0]
        vertical = cfg.DOOR_MAP[tile][2]
        center_x, center_y, center_z = self.center_units(tile_coords, self.unit_offsets, center_z=True)
        half = self.params.tile_units / 2
        shader_scales = [self.params.shader_scale, self.params.shader_scale]

        face_shaders = ['common/skip'] * 6
        if vertical:
            extreme_a = ((center_x - 0), (center_y - half), (center_z - half))
            extreme_b = ((center_x + 1), (center_y + half), (center_z + half))
            face_shaders[WEST] = 'common/hint'
        else:
            extreme_a = ((center_x - half), (center_y - 0), (center_z - half))
            extreme_b = ((center_x + half), (center_y + 1), (center_z + half))
            face_shaders[NORTH] = 'common/hint'
        face_vertices = build_cuboid_vertices(extreme_a, extreme_b)
        hint_brush = describe_cuboid_brush(face_vertices, face_shaders, shader_scales)

        return hint_brush

    def describe_floor_ceiling_clipping(self, thickness=1):
        lines = []
        face_shaders = ['common/full_clip'] * 6
        shader_scales = (1, 1)
        dimensions = self.tilemap.dimensions
        tile_units = self.params.tile_units

        coords_a = self.center_units((-1, dimensions[1]), self.unit_offsets)
        coords_b = self.center_units((dimensions[0], -1), self.unit_offsets)

        extreme_a = ((coords_a[0] - 0), (coords_a[1] - 0), -thickness)
        extreme_b = ((coords_b[0] + 0), (coords_b[1] + 0), 0)
        face_vertices = build_cuboid_vertices(extreme_a, extreme_b)
        lines += describe_cuboid_brush(face_vertices, face_shaders, shader_scales)

        extreme_a = ((coords_a[0] - 0), (coords_a[1] - 0), tile_units)
        extreme_b = ((coords_b[0] + 0), (coords_b[1] + 0), (tile_units + thickness))
        face_vertices = build_cuboid_vertices(extreme_a, extreme_b)
        lines += describe_cuboid_brush(face_vertices, face_shaders, shader_scales)

        return lines

    def describe_underworld_hollow(self, offset_z=0, thickness=1):  # TODO: factorized code for hollows
        lines = []
        face_shaders = ['common/caulk'] * 6
        shader_scales = [self.params.shader_scale, self.params.shader_scale]
        dimensions = self.tilemap.dimensions
        tile_units = self.params.tile_units
        t = thickness

        coords_a = self.center_units((-1, dimensions[1]), self.unit_offsets)
        coords_b = self.center_units((dimensions[0], -1), self.unit_offsets)

        extreme_a = ((coords_a[0] - 0), (coords_a[1] - 0), (offset_z - 0 - tile_units))
        extreme_b = ((coords_b[0] + 0), (coords_b[1] + 0), (offset_z + t - tile_units))
        face_vertices = build_cuboid_vertices(extreme_a, extreme_b)
        lines += describe_cuboid_brush(face_vertices, face_shaders, shader_scales)

        extreme_a = ((coords_a[0] - 0), (coords_a[1] - 0), (offset_z - t + tile_units))
        extreme_b = ((coords_b[0] + 0), (coords_b[1] + 0), (offset_z + 0 + tile_units))
        face_vertices = build_cuboid_vertices(extreme_a, extreme_b)
        lines += describe_cuboid_brush(face_vertices, face_shaders, shader_scales)

        extreme_a = ((coords_a[0] - 0), (coords_a[1] - 0), (offset_z + t - tile_units))
        extreme_b = ((coords_a[0] + t), (coords_b[1] + 0), (offset_z - t + tile_units))
        face_vertices = build_cuboid_vertices(extreme_a, extreme_b)
        lines += describe_cuboid_brush(face_vertices, face_shaders, shader_scales)

        extreme_a = ((coords_b[0] - t), (coords_a[1] - 0), (offset_z + t - tile_units))
        extreme_b = ((coords_b[0] + 0), (coords_b[1] + 0), (offset_z - t + tile_units))
        face_vertices = build_cuboid_vertices(extreme_a, extreme_b)
        lines += describe_cuboid_brush(face_vertices, face_shaders, shader_scales)

        extreme_a = ((coords_a[0] + t), (coords_a[1] - 0), (offset_z + t - tile_units))
        extreme_b = ((coords_b[0] - t), (coords_a[1] + t), (offset_z - t + tile_units))
        face_vertices = build_cuboid_vertices(extreme_a, extreme_b)
        lines += describe_cuboid_brush(face_vertices, face_shaders, shader_scales)

        extreme_a = ((coords_a[0] + t), (coords_b[1] - t), (offset_z + t - tile_units))
        extreme_b = ((coords_b[0] - t), (coords_b[1] + 0), (offset_z - t + tile_units))
        face_vertices = build_cuboid_vertices(extreme_a, extreme_b)
        lines += describe_cuboid_brush(face_vertices, face_shaders, shader_scales)

        return lines

    def describe_worldspawn(self):
        params = self.params
        cfg = self.cfg
        dimensions = self.tilemap.dimensions
        tilemap = self.tilemap
        pushwall_entity = cfg.ENTITY_PARTITION_MAP['pushwall'][0]
        music_name = cfg.MUSIC_LABELS[cfg.TILEMAP_MUSIC_INDICES[self.tilemap_index]]

        lines = [
            '{',
            'classname worldspawn',
            'music "music/{}/{}"'.format(params.short_name, music_name),
            'ambient 100',
            '_color "1 1 1"',
            'message "{}"'.format(tilemap.name),
            'author "{}"'.format(params.author),
        ]
        if params.author2:
            lines.append('author2 "{}"'.format(params.author2))

        for tile_y in range(dimensions[1]):
            for tile_x in range(dimensions[0]):
                tile_coords = (tile_x, tile_y)
                tile, entity, *_ = tilemap[tile_coords]

                if tile:
                    partition = find_partition(tile, cfg.TILE_PARTITION_MAP, count_sign=1,
                                               cache=self.tile_partition_cache)
                    lines.append('// {} @ {!r} = tile 0x{:04X}'.format(partition, tile_coords, tile))

                    if (partition in ('floor', 'door', 'door_silver', 'door_gold', 'door_elevator') or
                        entity == pushwall_entity):
                        lines.extend(self.describe_area_brushes(tile_coords))
                    elif partition == 'wall':
                        lines.extend(self.describe_wall_brush(tile_coords))
                    else:
                        raise ValueError((tile_coords, partition))

                    if tile in cfg.DOOR_MAP:
                        lines.append('// {} @ {!r} = door 0x{:04X}, hint'.format(partition, tile_coords, tile))
                        lines += self.describe_door_hint(tile_coords)

                if entity:
                    partition = find_partition(entity, cfg.ENTITY_PARTITION_MAP, count_sign=-1,
                                               cache=self.entity_partition_cache)

                    if partition == 'enemy':
                        lines.append('// {} @ {!r} = entity 0x{:04X}'.format(partition, tile_coords, entity))
                        lines += self.describe_dead_enemy_sprite(tile_coords)

                    elif partition == 'object':
                        lines.append('// {} @ {!r} = entity 0x{:04X}'.format(partition, tile_coords, entity))
                        if cfg.ENTITY_OBJECT_MAP.get(entity) in cfg.STATIC_OBJECT_NAMES:
                            lines += self.describe_sprite(tile_coords)
                        elif cfg.ENTITY_OBJECT_MAP.get(entity) in cfg.COLLECTABLE_OBJECT_NAMES:
                            lines += self.describe_collectable(tile_coords)

        lines.append('// floor and ceiling clipping planes')
        lines += self.describe_floor_ceiling_clipping()

        lines.append('// underworld hollow')
        lines += self.describe_underworld_hollow(params.underworld_offset)

        lines.append('}  // worldspawn')
        return lines

    def compute_progression_field(self, player_start_tile_coords):
        cfg = self.cfg
        tilemap = self.tilemap
        dimensions = tilemap.dimensions

        wall_start = cfg.TILE_PARTITION_MAP['wall'][0]
        wall_endex = wall_start + cfg.TILE_PARTITION_MAP['wall'][1]
        pushwall_entity = cfg.ENTITY_PARTITION_MAP['pushwall'][0]

        field = {(x, y): 0 for y in range(dimensions[1]) for x in range(dimensions[0])}
        visited = {(x, y) : False for y in range(dimensions[1]) for x in range(dimensions[0])}
        border_tiles = collections.deque([player_start_tile_coords])

        while border_tiles:
            tile_coords = border_tiles.popleft()
            if not visited[tile_coords]:
                visited[tile_coords] = True
                field_value = field[tile_coords]
                x, y = tile_coords

                for direction, displacement in enumerate(DIR_TO_DISPL[:4]):
                    xd, yd, _ = displacement
                    facing_coords = (x + xd, y + yd)
                    facing_tile = tilemap.get(facing_coords)
                    if facing_tile is not None:
                        object_name = cfg.ENTITY_OBJECT_MAP.get(facing_tile[1])
                        if (not visited[facing_coords] and object_name not in cfg.SOLID_OBJECT_NAMES and
                            (not (wall_start <= facing_tile[0] < wall_endex) or facing_tile[1] == pushwall_entity)):
                            border_tiles.append(facing_coords)
                            field_value |= (1 << direction)

                field[tile_coords] = field_value

        return field

    def describe_player_start(self, tile_coords):
        tile = self.tilemap[tile_coords]
        index = tile[1] - self.cfg.ENTITY_PARTITION_MAP['start'][0]
        origin = self.center_units(tile_coords, self.unit_offsets)
        origin[2] += 32

        player_start = [
            '{',
            'classname info_player_start',
            'origin "{:.0f} {:.0f} {:.0f}"'.format(*origin),
            'angle {:.0f}'.format(DIR_TO_YAW[index]),
            '}',
        ]

        player_intermission = [
            '{',
            'classname info_player_intermission',
            'origin "{:.0f} {:.0f} {:.0f}"'.format(*origin),
            'angle {:.0f}'.format(DIR_TO_YAW[index]),
            '}',
        ]

        return player_start + player_intermission

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

        lines += [
            '{',
            'classname path_corner',
            'origin "{:.0f} {:.0f} {:.0f}"'.format(*origin),
            'angle {:.0f}'.format(TURN_TO_YAW[index]),
            'targetname "corner_{:.0f}_{:.0f}"'.format(*tile_coords),
            'target "corner_{:.0f}_{:.0f}"'.format(*target_coords),
            '}',
        ]

        return lines

    def describe_enemy(self, tile_coords, turn_tiles):
        cfg = self.cfg
        params = self.params
        tilemap = self.tilemap
        tile = tilemap.get(tile_coords)
        enemy = cfg.ENEMY_MAP.get(tile[1])
        if enemy:
            direction, level = enemy[1], enemy[3]
            if params.enemy_level_min <= level <= params.enemy_level_max and direction < 4:
                angle = DIR_TO_YAW[ENEMY_INDEX_TO_DIR[direction]]
                origin = self.center_units(tile_coords, self.unit_offsets, center_z=True)
                return [
                    '{',
                    'classname info_player_deathmatch',
                    'origin "{:.0f} {:.0f} {:.0f}"'.format(*origin),
                    'angle {:.0f}'.format(angle),
                    '}',
                ]
        return ()

    def describe_dead_enemy_sprite(self, tile_coords):
        cfg = self.cfg
        params = self.params
        tilemap = self.tilemap
        tile = tilemap.get(tile_coords)
        enemy = cfg.ENEMY_MAP.get(tile[1])

        if enemy:
            name = enemy[0] + '__dead'
            face_shader = '{}_enemy/{}'.format(params.short_name, name)
            return self.describe_textured_sprite(tile_coords, face_shader, self.unit_offsets)
        else:
            return ()

    def describe_object(self, tile_coords):
        cfg = self.cfg
        params = self.params
        tilemap = self.tilemap
        tile = tilemap.get(tile_coords)
        lines = []
        name = cfg.ENTITY_OBJECT_MAP.get(tile[1])
        center_x, center_y, center_z = self.center_units(tile_coords, self.unit_offsets, center_z=True)

        light = cfg.OBJECT_LIGHT_MAP.get(name)
        if light:
            normalized_height, amount, color = light
            origin = (center_x, center_y, (normalized_height * params.tile_units))
            lines += [
                '{',
                'classname light',
                'origin "{:.0f} {:.0f} {:.0f}"'.format(*origin),
                'light "{:d}"'.format(amount),
                'color "{:f} {:f} {:f}"'.format(*color),
                '}',
            ]

        return lines

    def describe_pushwall(self, tile_coords, progression_field):
        params = self.params
        cfg = self.cfg
        tile = self.tilemap[tile_coords]
        center_x, center_y, center_z = self.center_units(tile_coords, self.unit_offsets, center_z=True)

        field_value = progression_field[tile_coords]
        for direction in range(4):
            if field_value & (1 << direction):
                move_direction = direction
                xd, yd = DIR_TO_DISPL[move_direction][:2]
                break
        else:
            raise ValueError('Pushwall @ {!r} cannot be reached or move'.format(tile_coords))

        trigger_begin = [
            '{',
            'classname trigger_multiple',
            'target "pushwall_{:.0f}_{:.0f}_move"'.format(*tile_coords),
            'wait {}'.format(params.pushwall_trigger_wait),
        ]
        trigger_end = ['}']

        face_shaders = ['common/trigger'] * 6
        unit_offsets = list(self.unit_offsets)
        unit_offsets[0] -= xd
        unit_offsets[1] += yd
        trigger_brush = self.describe_textured_cube(tile_coords, face_shaders, unit_offsets)

        speaker_open_entity = [
            '{',
            'classname target_speaker',
            'origin "{:.0f} {:.0f} {:.0f}"'.format(center_x, center_y, center_z),
            'targetname "pushwall_{:.0f}_{:.0f}_move"'.format(*tile_coords),
            'noise "sound/{}/{}"'.format(params.short_name, 'sampled/pushwall__move'),  # FIXME: filename
            '}',
        ]

        # Door entity
        door_begin = [
            '{',
            'classname func_door',
            'targetname "pushwall_{:.0f}_{:.0f}_move"'.format(*tile_coords),
            'angle {:.0f}'.format(DIR_TO_YAW[move_direction]),
            'lip {}'.format(params.tile_units + 2),
            'dmg 0',
            'health 0',
            'wait {}'.format(params.pushwall_wait),
            'speed {}'.format(params.pushwall_speed),
            # TODO: crusher
        ]
        door_end = ['}']

        # Door brush
        face_shaders = []
        texture = tile[0] - cfg.TILE_PARTITION_MAP['wall'][0]
        for direction in range(4):
            shader = '{}_wall/{}__{}'.format(params.short_name, cfg.TEXTURE_NAMES[texture], (direction & 1))
            face_shaders.append(shader)
        face_shaders += ['common/caulk'] * 2
        door_brush = self.describe_textured_cube(tile_coords, face_shaders, self.unit_offsets)

        # Underworld brush
        stop_coords = list(tile_coords)
        steps = 0
        while progression_field[tuple(stop_coords)] & (1 << move_direction) and steps < 3:  # FIXME: magic 3
            stop_coords[0] += xd
            stop_coords[1] += yd
            steps += 1
        face_shaders = ['common/caulk'] * 6
        unit_offsets = list(self.unit_offsets)
        unit_offsets[2] += params.underworld_offset
        door_underworld_brush = self.describe_textured_cube(stop_coords, face_shaders, unit_offsets)

        return (trigger_begin + trigger_brush + trigger_end + speaker_open_entity +
                door_begin + door_brush + door_underworld_brush + door_end)

    def describe_entities(self):  # TODO
        cfg = self.cfg
        tilemap = self.tilemap
        dimensions = tilemap.dimensions
        lines = []
        turn_list = []
        enemy_list = []
        pushwall_list = []
        player_start_coords = None

        for tile_y in range(dimensions[1]):
            for tile_x in range(dimensions[0]):
                tile_coords = (tile_x, tile_y)
                tile, entity, *_ = tilemap[tile_coords]

                if entity:
                    partition = find_partition(entity, cfg.ENTITY_PARTITION_MAP, count_sign=-1,
                                               cache=self.entity_partition_cache)
                    description = '// {} @ {!r} = entity 0x{:04X}'.format(partition, tile_coords, entity)

                    if partition == 'start':
                        if player_start_coords is not None:
                            raise ValueError('There can be only one player start entity')
                        player_start_coords = tile_coords
                        lines.append(description)
                        lines += self.describe_player_start(tile_coords)

                    elif partition == 'turn':
                        turn_list.append([description, tile_coords])

                    elif partition == 'enemy':
                        enemy_list.append([description, tile_coords])

                    elif partition == 'pushwall':
                        pushwall_list.append([description, tile_coords])

                    elif partition == 'object':
                        lines.append(description)
                        lines += self.describe_object(tile_coords)

                if tile:
                    partition = find_partition(tile, cfg.TILE_PARTITION_MAP, count_sign=-1,
                                               cache=self.tile_partition_cache)
                    if tile in cfg.DOOR_MAP:
                        lines.append('// {} @ {!r} = door 0x{:04X}'.format(partition, tile_coords, tile))
                        lines += self.describe_door(tile_coords)

        progression_field = self.compute_progression_field(player_start_coords)

        for description, tile_coords in pushwall_list:
            lines.append(description)
            lines += self.describe_pushwall(tile_coords, progression_field)

        turn_list_entities = [turn[1] for turn in turn_list]
#         for description, tile_coords in turn_list:
#             lines.append(description)
#             lines += self.describe_turn(tile_coords, turn_list_entities)

        for description, tile_coords in enemy_list:
            lines.append(description)
            lines += self.describe_enemy(tile_coords, turn_list_entities)

        lines.append('// progression field')
        lines += ['// ' + ''.join('{:X}'.format(progression_field[x, y]) for x in range(dimensions[0]))
                  for y in range(dimensions[1])]

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
    group.add_argument('--cfg', required=True)
    group.add_argument('--short-name', default='wolf3d')
    group.add_argument('--author', default='(c) id Software')
    group.add_argument('--author2')
    group.add_argument('--wave-rate', default=22050, type=int)
    group.add_argument('--imf-rate', default=700, type=int)
    group.add_argument('--imf2wav-path', default=IMF2WAV_PATH)
    group.add_argument('--ogg-rate', default=44100, type=int)
    group.add_argument('--oggenc2-path', default=OGGENC2_PATH)
    group.add_argument('--tile-units', default=96, type=int)
    group.add_argument('--alpha-index', default=0xFF, type=int)
    group.add_argument('--fix-alpha-halo', action='store_true')
    group.add_argument('--texture-scale', default=4, type=int)
    group.add_argument('--shader-scale', default=0.375, type=float)
    group.add_argument('--door-wait', default=5, type=float)
    group.add_argument('--door-speed', default=100, type=float)
    group.add_argument('--door-trigger-wait', default=5, type=float)
    group.add_argument('--pushwall-wait', default=32767, type=float)
    group.add_argument('--pushwall-speed', default=90, type=float)
    group.add_argument('--pushwall-trigger-wait', default=32767, type=float)
    group.add_argument('--underworld-offset', default=-4096, type=int)
    group.add_argument('--enemy-level-min', default=0, type=int)
    group.add_argument('--enemy-level-max', default=3, type=int)

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
    scaled_size = [side * params.texture_scale for side in cfg.TEXTURE_DIMENSIONS]

    for i, texture in enumerate(texture_manager):
        name = cfg.TEXTURE_NAMES[i >> 1]
        path = 'textures/{}_wall/{}__{}.tga'.format(params.short_name, name, (i & 1))
        logger.info('Texture [%d/%d]: %r', (i + 1), count, path)
        image = texture.image.transpose(Image.FLIP_TOP_BOTTOM).resize(scaled_size).convert('RGB')
        pixels_bgr = bytes(x for pixel in image.getdata() for x in reversed(pixel))
        texture_stream = io.BytesIO()
        write_targa_bgrx(texture_stream, scaled_size, 24, pixels_bgr)
        zip_file.writestr(path, texture_stream.getbuffer())

    palette = cfg.GRAPHICS_PALETTE
    for i, color in enumerate(palette):
        path = 'textures/{}_palette/color_0x{:02x}.tga'.format(params.short_name, i)
        logger.info('Texture palette color [%d/%d]: %r, (0x%02X, 0x%02X, 0x%02X)',
                    (i + 1), len(palette), path, *color)
        image = build_color_image(cfg.TEXTURE_DIMENSIONS, color)
        image = image.transpose(Image.FLIP_TOP_BOTTOM).convert('RGB')
        pixels_bgr = bytes(x for pixel in image.getdata() for x in reversed(pixel))
        texture_stream = io.BytesIO()
        write_targa_bgrx(texture_stream, cfg.TEXTURE_DIMENSIONS, 24, pixels_bgr)
        zip_file.writestr(path, texture_stream.getbuffer())

    logger.info('Done')
    _sep()


def write_texture_shaders(params, cfg, shader_file, palette_shaders=True):
    for name in cfg.TEXTURE_NAMES:
        for j in range(2):
            shader_name = 'textures/{}_wall/{}__{}'.format(params.short_name, name, j)
            path = shader_name + '.tga'
            shader_file.write(TEXTURE_SHADER_TEMPLATE.format(shader_name, path))

    if palette_shaders:
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


def write_collectable_shaders(params, cfg, shader_file):
    for name in cfg.COLLECTABLE_OBJECT_NAMES:
        shader_name = 'textures/{}_collectable/{}'.format(params.short_name, name)
        path = 'sprites/{}/{}.tga'.format(params.short_name, name)
        shader_file.write(SPRITE_SHADER_TEMPLATE.format(shader_name, path))


def write_enemy_shaders(params, cfg, shader_file):
    ignored_names = cfg.STATIC_OBJECT_NAMES + cfg.COLLECTABLE_OBJECT_NAMES
    names = [name for name in cfg.SPRITE_NAMES if name not in ignored_names or name.endswith('__dead')]
    for name in names:
        shader_name = 'textures/{}_enemy/{}'.format(params.short_name, name)
        path = 'sprites/{}/{}.tga'.format(params.short_name, name)
        shader_file.write(SPRITE_SHADER_TEMPLATE.format(shader_name, path))


def export_shader(params, cfg, zip_file, script_name, shader_writer):
    shader_text_stream = io.StringIO()
    shader_writer(params, cfg, shader_text_stream)
    shader_text = shader_text_stream.getvalue()

    zip_file.writestr('scripts/{}'.format(script_name), shader_text.encode())

    folder = os.path.join(params.output_folder, 'scripts')
    os.makedirs(folder, exist_ok=True)
    with open(os.path.join(folder, script_name), 'wt') as shader_file:
        shader_file.write(shader_text)


def export_shaders(params, cfg, zip_file):
    logger = logging.getLogger()
    logger.info('Exporting shaders')

    script_writer_map = {
        '{}_wall.shader'.format(params.short_name): write_texture_shaders,
        '{}_static.shader'.format(params.short_name): write_static_shaders,
        '{}_collectable.shader'.format(params.short_name): write_collectable_shaders,
        '{}_enemy.shader'.format(params.short_name): write_enemy_shaders,
    }

    for script_name, shader_writer in script_writer_map.items():
        export_shader(params, cfg, zip_file, script_name, shader_writer)

    logger.info('Done')
    _sep()


def image_to_array(image, shape, dtype=np.uint8):
    return np.array(image.getdata(), dtype).reshape(shape)


def array_to_rgbx(arr, size, channels):
    assert 3 <= channels <= 4
    mode = 'RGBA' if channels == 4 else 'RGB'
    arr = arr.reshape(arr.shape[0] * arr.shape[1], arr.shape[2]).astype(np.uint8)
    if channels == 4 and len(arr[0]) == 3:  # FIXME: make generic, this is only for RGB->RGBA
        arr = np.c_[arr, 255 * np.ones((len(arr), 1), np.uint8)]
    return Image.frombuffer(mode, size, arr.tostring(), 'raw', mode, 0, 1)


def fix_sprite_halo(rgba_image, alpha_layer):
    alpha_layer = image_to_array(alpha_layer, rgba_image.size)
    mask = (alpha_layer != 0).astype(np.uint8)
    source = image_to_array(rgba_image, rgba_image.size + (4,))
    source *= mask[..., None].repeat(4, axis=2)

    accum = np.zeros_like(source, np.uint16)
    accum[ :-1,  :  ] += source[1:  ,  :  ]
    accum[1:  ,  :  ] += source[ :-1,  :  ]
    accum[ :  ,  :-1] += source[ :  , 1:  ]
    accum[ :  , 1:  ] += source[ :  ,  :-1]
    accum[ :-1,  :-1] += source[1:  , 1:  ]
    accum[ :-1, 1:  ] += source[1:  ,  :-1]
    accum[1:  ,  :-1] += source[ :-1, 1:  ]
    accum[1:  , 1:  ] += source[ :-1,  :-1]

    count = np.zeros_like(mask)
    count[ :-1,  :  ] += mask[1:  ,  :  ]
    count[1:  ,  :  ] += mask[ :-1,  :  ]
    count[ :  ,  :-1] += mask[ :  , 1:  ]
    count[ :  , 1:  ] += mask[ :  ,  :-1]
    count[ :-1,  :-1] += mask[1:  , 1:  ]
    count[ :-1, 1:  ] += mask[1:  ,  :-1]
    count[1:  ,  :-1] += mask[ :-1, 1:  ]
    count[1:  , 1:  ] += mask[ :-1,  :-1]

    count_div = np.maximum(np.ones_like(count), count)
    count_div = count_div[..., None].repeat(4, axis=2)
    accum = (accum // count_div).astype(np.uint8)
    accum[..., 3] = 0
    accum[mask != 0] = source[mask != 0]

    result = array_to_rgbx(accum, rgba_image.size, 4)
    return result


def export_sprites(params, cfg, zip_file, vswap_chunks_handler):
    logger = logging.getLogger()
    logger.info('Exporting sprites')

    start = vswap_chunks_handler.sprites_start
    count = vswap_chunks_handler.sounds_start - start
    sprite_manager = pywolf.graphics.SpriteManager(vswap_chunks_handler,
                                                   cfg.GRAPHICS_PALETTE_MAP[...],
                                                   cfg.SPRITE_DIMENSIONS,
                                                   start, count, params.alpha_index)
    scaled_size = [side * params.texture_scale for side in cfg.SPRITE_DIMENSIONS]

    for i, sprite in enumerate(sprite_manager):
        name = cfg.SPRITE_NAMES[i]
        path = 'sprites/{}/{}.tga'.format(params.short_name, name)
        logger.info('Sprite [%d/%d]: %r', (i + 1), count, path)
        image = sprite.image.convert('RGBA')
        if params.fix_alpha_halo:
            alpha_layer = image.split()[-1].transpose(Image.FLIP_TOP_BOTTOM).resize(scaled_size)
        image = image.transpose(Image.FLIP_TOP_BOTTOM).resize(scaled_size)
        if params.fix_alpha_halo:
            image = fix_sprite_halo(image, alpha_layer)
        pixels_bgra = bytes(x for pixel in image.getdata()
                            for x in [pixel[2], pixel[1], pixel[0], pixel[3]])
        sprite_stream = io.BytesIO()
        write_targa_bgrx(sprite_stream, scaled_size, 32, pixels_bgra)
        zip_file.writestr(path, sprite_stream.getbuffer())

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
        name = cfg.MUSIC_LABELS[i]
        path = 'music/{}/{}.ogg'.format(params.short_name, name)
        logger.info('Music [%d/%d]: %r', (i + 1), count, path)
        imf_chunk = audio_chunks_handler[chunk_index]
        wave_path = convert_imf_to_wave(imf_chunk, params.imf2wav_path,
                                        wave_rate=params.ogg_rate, imf_rate=params.imf_rate)
        try:
            ogg_path = convert_wave_to_ogg(wave_path, params.oggenc2_path)
            zip_file.write(ogg_path, path)
        finally:
            _force_unlink(wave_path, ogg_path)

    logger.info('Done')
    _sep()


def export_adlib_sounds(params, cfg, zip_file, audio_chunks_handler):
    logger = logging.getLogger()
    logger.info('Exporting AdLib sounds')

    start, count = cfg.AUDIO_PARTITIONS_MAP['adlib']
    adlib_manager = pywolf.audio.AdLibSoundManager(audio_chunks_handler, start, count)

    for i, sound in enumerate(adlib_manager):
        name = cfg.ADLIB_SOUND_NAMES[i]
        path = 'sound/{}/adlib/{}.ogg'.format(params.short_name, name)
        logger.info('AdLib sound [%d/%d]: %r', (i + 1), count, path)
        imf_chunk = sound.to_imf_chunk()
        wave_path = convert_imf_to_wave(imf_chunk, params.imf2wav_path,
                                        wave_rate=params.ogg_rate, imf_rate=params.imf_rate)
        try:
            ogg_path = convert_wave_to_ogg(wave_path, params.oggenc2_path)
            zip_file.write(ogg_path, path)
        finally:
            _force_unlink(wave_path, ogg_path)

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
    logger.info('Exporting tilemaps (Q3Map2 *.map)')

    start, count = (0, 60)  # FIXME: replace with map descriptors
    tilemap_manager = pywolf.game.TileMapManager(audio_chunks_handler, start, count)

    for i, tilemap in enumerate(tilemap_manager):
        folder = os.path.join(params.output_folder, 'maps', params.short_name)
        os.makedirs(folder, exist_ok=True)
        path = os.path.join(folder, (tilemap.name + '.map'))
        logger.info('TileMap [%d/%d]: %r', (i + 1), count, path)

        exporter = MapExporter(params, cfg, tilemap, i)
        description = '\n'.join(exporter.describe_tilemap())
        with open(path, 'wt') as map_file:
            map_file.write(description)

        path = 'maps/{}/{}.map'.format(params.short_name, tilemap.name)
        zip_file.writestr(path, description)

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
    with zipfile.ZipFile(pk3_path, 'w', zipfile.ZIP_DEFLATED) as pk3_file:
        _sep()
        export_tilemaps(params, cfg, pk3_file, tilemap_chunks_handler)
        export_shaders(params, cfg, pk3_file)
        export_textures(params, cfg, pk3_file, vswap_chunks_handler)
        export_sprites(params, cfg, pk3_file, vswap_chunks_handler)
        export_pictures(params, cfg, pk3_file, graphics_chunks_handler)
        export_tile8(params, cfg, pk3_file, graphics_chunks_handler)
        export_screens(params, cfg, pk3_file, graphics_chunks_handler)
        export_helparts(params, cfg, pk3_file, graphics_chunks_handler)
        export_endarts(params, cfg, pk3_file, graphics_chunks_handler)
        export_sampled_sounds(params, cfg, pk3_file, vswap_chunks_handler)
        export_adlib_sounds(params, cfg, pk3_file, audio_chunks_handler)
        export_buzzer_sounds(params, cfg, pk3_file, audio_chunks_handler)
        export_musics(params, cfg, pk3_file, audio_chunks_handler)

    logger.info('PK3 archived successfully')


if __name__ == '__main__':
    main(*sys.argv[1:])
