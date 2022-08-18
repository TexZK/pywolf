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
import struct
from typing import ByteString
from typing import MutableSequence
from typing import Self
from typing import Sequence
from typing import Tuple

from .archives import ResourceLibrary
from .base import Chunk
from .base import Codec
from .base import Coord
from .base import Coords
from .base import Index
from .base import Offset
from .utils import ResourceManager


PLANE_COUNT: int = 3


class TileMapHeader(Codec):

    def __init__(
        self,
        plane_count: int,
        plane_offsets: Sequence[Offset],
        plane_sizes: Sequence[Coord],
        size: Coords,
        name: str,
    ):
        if plane_count < 1:
            raise ValueError('invalid plane count')
        if len(plane_offsets) != plane_count:
            raise ValueError('inconsistent plane offsets count')
        if len(plane_sizes) != plane_count:
            raise ValueError('inconsistent plane sizes count')

        self.plane_offsets = plane_offsets
        self.plane_sizes = plane_sizes
        self.size = size
        self.name = name

    @classmethod
    def calcsize_stateless(cls, plane_count: int = PLANE_COUNT) -> Offset:
        if plane_count < 1:
            raise ValueError('invalid plane count')
        return (plane_count * 4) + (plane_count * 2) + (2 * 2) + 16

    def to_bytes(self) -> bytes:
        chunk = struct.pack(
            f'<{len(self.plane_offsets)}L{len(self.plane_sizes)}H2H16s',
            *self.plane_offsets,
            *self.plane_sizes,
            *self.size,
            self.name.encode('ascii').ljust(16, b'\0')
        )
        return chunk

    @classmethod
    def from_bytes(
        cls,
        buffer: ByteString,
        offset: Offset = 0,
        plane_count: int = PLANE_COUNT,
    ) -> Tuple[Self, Offset]:

        if plane_count < 1:
            raise ValueError('invalid plane count')

        offset = int(offset)
        plane_offsets = struct.unpack_from(f'<{plane_count}L', buffer, offset)
        offset += plane_count * 4

        plane_sizes = struct.unpack_from(f'<{plane_count}H', buffer, offset)
        offset += plane_count * 2

        width, height = struct.unpack_from(f'<2H', buffer, offset)
        offset += 2
        size = (width, height)

        name = struct.unpack_from(f'<16s', buffer, offset)[0].decode('ascii')
        null_char_index = name.find('\0')
        if null_char_index >= 0:
            name = name[:null_char_index]
        name = name.rstrip(' \t\r\n\v\0')

        instance = cls(plane_count, plane_offsets, plane_sizes, size, name)
        return instance, offset

    @classmethod
    def from_stream(
        cls,
        stream: io.BufferedReader,
        plane_count: int = PLANE_COUNT,
    ) -> Self:

        size = cls.calcsize_stateless(plane_count=plane_count)
        chunk = stream.read(size)
        instance = cls.from_bytes(chunk)
        return instance


class TileMap:

    def __init__(
        self,
        size: Coords,
        planes_flat: Sequence[MutableSequence[int]],
        name: str,
    ):
        width, height = size
        if width < 1 or height < 1:
            raise ValueError(f'invalid map size: {size}')
        area = width * height
        for plane_flat in planes_flat:
            if len(plane_flat) != area:
                raise ValueError('inconsistent plane size')

        self.size: Coords = size
        self.name: str = name
        self.planes: Sequence[MutableSequence[int]] = planes_flat

    def __getitem__(self, key):  # FIXME TODO
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

    def __setitem__(self, key, value):  # FIXME TODO
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

    def get(self, key, default=None):  # FIXME TODO
        width, height = self.size
        tile_x, tile_y, *_ = key
        tile_offset = tile_y * height + tile_x
        if 0 <= tile_offset < (width * height):
            return self[key]
        else:
            return default

    def check_coords(self, tile_coords: Coords) -> bool:
        return (0 <= tile_coords[0] < self.size[0] and
                0 <= tile_coords[1] < self.size[1])


class TileMapManager(ResourceManager):

    def __init__(self, chunks_handler, start=None, count=None):
        super().__init__(chunks_handler, start, count)

    def _load_resource(self, index, chunk):
        header, raw_planes = chunk
        planes = [array.array('H', raw_plane) for raw_plane in raw_planes]
        instance = TileMap(header.size, planes, header.name)
        return instance


class TileMapLibrary(ResourceLibrary[Index, TileMap]):

    def _get_resource(self, index: Index, chunk: Chunk) -> TileMap:
        del index
        header, raw_planes = chunk  # FIXME how to do this ???
        planes_flat = [array.array('H', raw_plane) for raw_plane in raw_planes]
        instance = TileMap(header.size, planes_flat, header.name)
        return instance


class Game(object):  # TODO

    instance = None

    def __init__(self, rules, gamemap):
        self.rules = rules
        self.gamemap = gamemap
        self.entities = {}  # all
        self.players = {}
