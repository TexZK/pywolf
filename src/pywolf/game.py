# Copyright (c) 2015-2022, Andrea Zoppi
# All rights reserved.
#
# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions are met:
#
# 1. Redistributions of source code must retain the above copyright notice,
#    this list of conditions and the following disclaimer.
#
# 2. Redistributions in binary form must reproduce the above copyright
#    notice, this list of conditions and the following disclaimer in the
#    documentation and/or other materials provided with the distribution.
#
# THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS"
# AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE
# IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE
# ARE DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT HOLDER OR CONTRIBUTORS BE
# LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR
# CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF
# SUBSTITUTE GOODS OR SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS
# INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN
# CONTRACT, STRICT LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE)
# ARISING IN ANY WAY OUT OF THE USE OF THIS SOFTWARE, EVEN IF ADVISED OF THE
# POSSIBILITY OF SUCH DAMAGE.

import array
import io

from pywolf.utils import (
    stream_pack, stream_pack_array, stream_unpack, stream_unpack_array,
    BinaryResource, ResourceManager
)


VERTICAL = 0
HORIZONTAL = 1


class TileMapHeader(BinaryResource):

    def __init__(self, plane_offsets, plane_sizes, size, name):
        self.plane_offsets = plane_offsets
        self.plane_sizes = plane_sizes
        self.size = size
        self.name = name

    @classmethod
    def from_stream(cls, stream, planes_count=3):
        planes_count = int(planes_count)
        assert planes_count > 0
        plane_offsets = tuple(stream_unpack_array('<L', stream, planes_count))
        plane_sizes = tuple(stream_unpack_array('<H', stream, planes_count))
        size = stream_unpack('<HH', stream)
        name = stream_unpack('<16s', stream)[0].decode('ascii')
        null_char_index = name.find('\0')
        if null_char_index >= 0:
            name = name[:null_char_index]
        name = name.rstrip(' \t\r\n\v\0')
        return cls(plane_offsets, plane_sizes, size, name)

    def to_stream(self, stream):
        stream_pack_array(stream, '<L', self.plane_offsets)
        stream_pack_array(stream, '<H', self.plane_sizes)
        stream_pack(stream, '<HH', *self.size)
        stream_pack(stream, '<16s', self.name.encode('ascii'))

    @classmethod
    def from_bytes(cls, data, planes_count=3):
        return cls.from_stream(io.BytesIO(data), planes_count)


class TileMap(object):

    def __init__(self, size, planes, name):
        width, height = size
        area = width * height
        assert all(len(plane) == area for plane in planes)

        self.size = size
        self.name = name
        self.planes = planes

    def __getitem__(self, key):
        planes = self.planes
        height = self.size[1]
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
        height = self.size[1]
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
        width, height = self.size
        tile_x, tile_y, *_ = key
        tile_offset = tile_y * height + tile_x
        if 0 <= tile_offset < (width * height):
            return self[key]
        else:
            return default

    def check_coords(self, tile_coords):
        return (0 <= tile_coords[0] < self.size[0] and
                0 <= tile_coords[1] < self.size[1])


class TileMapManager(ResourceManager):

    def __init__(self, chunks_handler, start=None, count=None):
        super().__init__(chunks_handler, start, count)

    def _load_resource(self, index, chunk):
        header, raw_planes = chunk
        planes = [array.array('H', raw_plane) for raw_plane in raw_planes]
        return TileMap(header.size, planes, header.name)


class Game(object):  # TODO

    instance = None

    def __init__(self, rules, gamemap):
        self.rules = rules
        self.gamemap = gamemap
        self.entities = {}  # all
        self.players = {}

