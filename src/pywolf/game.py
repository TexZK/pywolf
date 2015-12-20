'''
@author: Andrea Zoppi
'''

import array
import io

from pywolf.utils import (stream_pack, stream_pack_array, stream_unpack, stream_unpack_array,
                          BinaryResource, ResourceManager)


VERTICAL   = 0
HORIZONTAL = 1


class TileMapHeader(BinaryResource):

    def __init__(self, plane_offsets, plane_sizes, dimensions, name):
        self.plane_offsets = plane_offsets
        self.plane_sizes = plane_sizes
        self.dimensions = dimensions
        self.name = name

    @classmethod
    def from_stream(cls, stream, planes_count=3):
        planes_count = int(planes_count)
        assert planes_count > 0
        plane_offsets = tuple(stream_unpack_array('<L', stream, planes_count))
        plane_sizes = tuple(stream_unpack_array('<H', stream, planes_count))
        dimensions = stream_unpack('<HH', stream)
        name = stream_unpack('<16s', stream)[0].decode('ascii')
        null_char_index = name.find('\0')
        if null_char_index >= 0:
            name = name[:null_char_index]
        name = name.rstrip(' \t\r\n\v\0')
        return cls(plane_offsets, plane_sizes, dimensions, name)

    def to_stream(self, stream):
        stream_pack_array(stream, '<L', self.plane_offsets)
        stream_pack_array(stream, '<H', self.plane_sizes)
        stream_pack(stream, '<HH', *self.dimensions)
        stream_pack(stream, '<16s', self.name.encode('ascii'))

    @classmethod
    def from_bytes(cls, data, planes_count=3):
        return cls.from_stream(io.BytesIO(data), planes_count)


class TileMap(object):

    def __init__(self, dimensions, planes, name):
        width, height = dimensions
        area = width * height
        assert all(len(plane) == area for plane in planes)

        self.dimensions = dimensions
        self.name = name
        self.planes = planes

    def __getitem__(self, key):
        planes = self.planes
        height = self.dimensions[1]
        assert 2 <= len(key) <= 3

        tile_x, tile_y, *args = key
        tile_offset = tile_y * height + tile_x
        if args:
            plane_index = args[0]
            return planes[plane_index][tile_offset]
        else:
            return [planes[i][tile_offset] for i in range(len(planes))]

    def __settitem__(self, key, value):
        planes = self.planes
        height = self.dimensions[1]
        assert 2 <= len(key) <= 3

        tile_x, tile_y, *args = key
        tile_offset = tile_y * height + tile_x
        if args:
            plane_index = args[0]
            planes[plane_index][tile_offset] = value
        else:
            assert len(value) == len(planes)
            for i in range(len(planes)):
                planes[i][tile_offset] = value[i]

    def get(self, key, default=None):
        width, height = self.dimensions
        tile_x, tile_y, *_ = key
        tile_offset = tile_y * height + tile_x
        if 0 <= tile_offset < (width * height):
            return self[key]
        else:
            return default

    def check_coords(self, tile_coords):
        return (0 <= tile_coords[0] < self.dimensions[0] and
                0 <= tile_coords[1] < self.dimensions[1])


class TileMapManager(ResourceManager):

    def __init__(self, chunks_handler, start=None, count=None):
        super().__init__(chunks_handler, start, count)

    def _build_resource(self, index, chunk):
        header, raw_planes = chunk
        planes = [array.array('H', raw_plane) for raw_plane in raw_planes]
        return TileMap(header.dimensions, planes, header.name)


class Game(object):  # TODO

    instance = None

    def __init__(self, rules, gamemap):
        self.rules = rules
        self.gamemap = gamemap
        self.entities = {}  # all
        self.players = {}

