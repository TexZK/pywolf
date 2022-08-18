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
from typing import List
from typing import MutableSequence
from typing import Optional
from typing import Sequence
from typing import Tuple
from typing import cast as _cast

from .base import ArchiveReader
from .base import Cache
from .base import Chunk
from .base import Codec
from .base import Coord
from .base import Coords
from .base import Index
from .base import Offset
from .base import ResourceLibrary
from .compression import carmack_expand
from .compression import rlew_expand
from .utils import stream_fit


# ============================================================================

PLANE_COUNT: int = 3


# ============================================================================

class MapHeader(Codec):

    def __init__(
        self,
        plane_count: int,
        plane_offsets: Sequence[Offset],
        plane_sizes: Sequence[Coord],
        size: Coords,
        name: str,
    ):
        if plane_count < 0:
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
    ) -> Tuple['MapHeader', Offset]:

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
    ) -> 'MapHeader':

        size = cls.calcsize_stateless(plane_count=plane_count)
        chunk = stream.read(size)
        instance, _ = cls.from_bytes(chunk)
        return instance


class Map:

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


# ============================================================================

class MapArchiveReader(ArchiveReader):

    def __init__(
        self,
        chunk_cache: Optional[Cache[Index, Chunk]] = None,
    ):
        super().__init__(chunk_cache=chunk_cache)

        self._header_stream: Optional[io.BufferedReader] = None
        self._header_offset: Offset = 0
        self._header_size: Offset = 0
        self._planes_count: int = 0
        self._carmacized: bool = True
        self._rlew_tag: int = -1

    def _read_chunk(self, index: Index) -> Chunk:
        chunks = []
        chunk_size = self.sizeof(index)
        if chunk_size:
            self._seek_chunk(index)
            data_stream = self._data_stream
            header = MapHeader.from_stream(data_stream, self.plane_count)
            chunks.append(header.to_bytes())
            carmacized = self._carmacized
            rlew_tag = self._rlew_tag

            for index in range(self.plane_count):
                self._seek_chunk(index, header.plane_offsets)
                chunk = data_stream.read(2)
                chunks.append(chunk)
                expanded_size, = struct.unpack('<H', chunk)
                compressed_size = header.plane_sizes[index] - 2
                chunk = data_stream.read(compressed_size)
                if carmacized:
                    chunk = carmack_expand(chunk, expanded_size)[2:]
                plane = rlew_expand(chunk, rlew_tag)
                chunks.append(plane)
        else:
            header = MapHeader(0, [], [], (0, 0), '')
            chunks.append(header.to_bytes())
        chunk = b''.join(chunks)
        return chunk

    def clear(self) -> None:
        super().clear()
        self._header_stream = None
        self._header_offset = 0
        self._header_size = 0
        self._planes_count = 0
        self._carmacized = True
        self._rlew_tag = -1

    def close(self) -> None:
        super().close()
        self._header_stream = None

    def open(
        self,
        data_stream: Optional[io.BufferedReader] = None,
        data_offset: Optional[Offset] = None,
        data_size: Optional[Offset] = None,
        header_stream: Optional[io.BufferedReader] = None,
        header_offset: Optional[Offset] = None,
        header_size: Optional[Offset] = None,
        plane_count: int = 3,
        carmacized: bool = True,
    ) -> None:

        if header_stream is None:
            raise ValueError('a header stream should be provided')
        super().open(data_stream, data_offset=data_offset, data_size=data_size)

        plane_count = plane_count.__index__()
        if plane_count < 1:
            raise ValueError(f'invalid planes count: {plane_count}')

        header_base, header_size = stream_fit(header_stream, header_offset, header_size)
        rlew_tag, = struct.unpack('<H', header_stream.read(2))

        chunk_count_size = header_size - 2
        if chunk_count_size % 4:
            raise ValueError(f'header size - 2 must be divisible by 4: {chunk_count_size}')

        chunk_count = chunk_count_size // 4
        chunk_offsets: List[Optional[Offset]] = [None] * chunk_count

        for i in range(chunk_count):
            offset, = struct.unpack('<L', header_stream.read(4))
            if 0 < offset < 0xFFFFFFFF:
                chunk_offsets[i] = offset

        data_size = self._data_size
        chunk_offsets.append(data_size)

        for i in reversed(range(chunk_count)):
            if chunk_offsets[i] is None:
                chunk_offsets[i] = chunk_offsets[i + 1]
        chunk_offsets = _cast(List[Offset], chunk_offsets)

        for index in range(chunk_count):
            if not 0 <= chunk_offsets[index] <= data_size:
                raise ValueError(f'invalid offset value: index={index}')
            if not chunk_offsets[index] <= chunk_offsets[index + 1]:
                raise ValueError(f'invalid offset ordering: index={index}')

        self._chunk_count = chunk_count
        self._chunk_offsets = chunk_offsets
        self._header_stream = header_stream
        self._header_offset = header_base
        self._header_size = header_size
        self._planes_count = plane_count
        self._carmacized = carmacized
        self._rlew_tag = rlew_tag

    @property
    def plane_count(self) -> int:
        return self._planes_count


# ============================================================================

class MapLibrary(ResourceLibrary[Index, Map]):

    def __init__(
        self,
        map_archive: MapArchiveReader,
        resource_cache: Optional[Cache[Index, Map]] = None,
        start: Optional[Index] = None,
        count: Optional[Index] = None,
    ):
        super().__init__(
            map_archive,
            resource_cache=resource_cache,
            start=start,
            count=count,
        )

    def _get_resource(self, index: Index, chunk: Chunk) -> Map:
        header, offset = MapHeader.from_bytes(chunk)
        archive = _cast(MapArchiveReader, self._archive)
        planes_flat = []

        for plane_index in range(archive.plane_count):
            expanded_size, = struct.unpack_from('<H', chunk, offset)
            offset += 2

            plane_chunk = chunk[offset:(offset + expanded_size)]
            offset += expanded_size

            plane_flat = array.array('H', plane_chunk)
            planes_flat.append(plane_flat)

        instance = Map(header.size, planes_flat, header.name)
        return instance


# ============================================================================

class Game(object):  # TODO

    instance = None

    def __init__(self, rules, gamemap):
        self.rules = rules
        self.gamemap = gamemap
        self.entities = {}  # all
        self.players = {}
