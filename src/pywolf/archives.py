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

import abc
import collections.abc
import io
from typing import Dict
from typing import Iterator
from typing import List
from typing import Mapping
from typing import Optional
from typing import Self
from typing import Sequence
from typing import Tuple
from typing import Union
from typing import cast as _cast

from .base import Cache
from .base import Chunk
from .base import ColorIndex
from .base import Coords
from .base import Index
from .base import KT
from .base import KTS
from .base import NoCache
from .base import Offset
from .game import TileMapHeader
from .base import VT
from .compression import HUFFMAN_NODE_COUNT
from .compression import carmack_expand
from .compression import huffman_expand
from .compression import rlew_expand
from .utils import stream_fit
from .utils import stream_unpack
from .utils import stream_unpack_array

# (partition_name, start_index, count)
GraphicsPartitionEntry = Tuple[str, Index, Index]

# {partition_name: (start_index, count)}
GraphicsPartitionMap = Mapping[str, Tuple[Index, Index]]

# (chunk_index, chunk_size)
SoundInfo = Tuple[Index, Offset]


class ArchiveReader(collections.abc.Mapping[Index, Chunk]):

    def __getitem__(
        self,
        key: Union[Index, slice],
    ) -> Union[Chunk, List[Chunk]]:

        if isinstance(key, slice):
            start = max(0, key.start)
            stop = min(key.stop, self._chunk_count)
            step = key.step
            return [self.get(index) for index in range(start, stop, step)]
        else:
            return self.get(key)

    def __init__(
        self,
        chunk_cache: Optional[Cache[Index, Chunk]],
    ):
        if chunk_cache is None:
            chunk_cache = NoCache()

        self._data_stream: Optional[io.BufferedReader] = None
        self._data_offset: Offset = 0
        self._data_size: Offset = 0
        self._chunk_count: Index = 0
        self._chunk_offsets: Dict[Index, Offset] = {}  # appended end offset
        self._chunk_cache: Cache[Index, Chunk] = chunk_cache

        chunk_cache.clear()

    def __iter__(self) -> Iterator[Chunk]:
        for index in range(self._chunk_count):
            yield self.get(index)

    def __len__(self) -> Index:
        return self._chunk_count

    @abc.abstractmethod
    def _read_chunk(self, index: Index) -> Chunk:
        ...

    def _seek_chunk(
        self,
        index: Index,
        offsets: Optional[Sequence[Offset]] = None,
    ) -> None:

        if offsets is None:
            chunk_offset = self.offsetof(index)
        else:
            index = index.__index__()
            if index < 0:
                raise ValueError('negative index')
            chunk_offset = offsets[index]

        self._data_stream.seek(self._data_offset + chunk_offset, io.SEEK_SET)

    def open(
        self,
        data_stream: Optional[io.BufferedReader] = None,
        data_offset: Optional[Offset] = None,
        data_size: Optional[Offset] = None,
    ) -> Self:

        if data_stream is None:
            raise ValueError('a data stream should be provided')
        data_offset, data_size = stream_fit(data_stream, data_offset, data_size)

        self._data_stream = data_stream
        self._data_offset = data_offset
        self._data_size = data_size
        return self

    def close(self) -> None:
        self._data_stream = None

    def clear(self) -> None:
        self._data_stream = None
        self._data_offset = 0
        self._data_size = 0
        self._chunk_count = 0
        self._chunk_offsets = []
        self._chunk_cache = []

    def get(self, index: Index) -> Chunk:
        index = index.__index__()
        if index < 0:
            raise ValueError('negative index')
        value = self._chunk_cache.get(index)
        if value is None:
            value = self._read_chunk(index)
            self._chunk_cache.set(index, value)
        return value

    def offsetof(self, index: Index) -> Offset:
        index = index.__index__()
        if index < 0:
            raise ValueError('negative index')
        return self._chunk_offsets[index]

    def sizeof(self, index: Index) -> Offset:
        index = index.__index__()
        if index < 0:
            raise ValueError('negative index')
        return self._chunk_offsets[index + 1] - self._chunk_offsets[index]


class AudioArchiveReader(ArchiveReader):

    def __init__(self, chunk_cache: Cache[Index, Chunk]):
        super().__init__(chunk_cache)

        self._header_stream: Optional[io.BufferedReader] = None
        self._header_offset: Offset = 0
        self._header_size: Offset = 0

    def _read_chunk(self, index: Index) -> bytes:
        chunk_size = self.sizeof(index)
        self._seek_chunk(index)
        chunk = self._data_stream.read(chunk_size)
        return chunk

    def clear(self) -> None:
        super().clear()
        self._header_stream = None
        self._header_offset = 0
        self._header_size = 0

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
    ) -> Self:

        if header_stream is None:
            raise ValueError('a header stream should be provided')
        super().open(data_stream, data_offset=data_offset, data_size=data_size)

        header_offset, header_size = stream_fit(header_stream, header_offset, header_size)
        if header_size % 4:
            raise ValueError(f'header size must be divisible by 4: {header_size}')

        data_size = self._data_size
        chunk_count = header_size // 4
        chunk_offsets = list(stream_unpack_array('<L', header_stream, chunk_count))
        chunk_offsets.append(data_size)

        for index in range(chunk_count):
            if not 0 <= chunk_offsets[index] <= data_size:
                raise ValueError(f'invalid offset value: index={index}')
            if not chunk_offsets[index] <= chunk_offsets[index + 1]:
                raise ValueError(f'invalid offset ordering: index={index}')

        self._chunk_count = chunk_count
        self._chunk_offsets = chunk_offsets
        self._header_stream = header_stream
        self._header_offset = header_offset
        self._header_size = header_size
        return self


class GraphicsArchiveReader(ArchiveReader):

    def __init__(self, chunk_cache: Cache[Index, Chunk]):
        super().__init__(chunk_cache)

        self._header_stream: Optional[io.BufferedReader] = None
        self._header_offset: Offset = 0
        self._header_size: Offset = 0
        self._huffman_stream: Optional[io.BufferedReader] = None
        self._huffman_offset: Offset = 0
        self._huffman_size: Offset = 0
        self._partition_map: Dict[str, Tuple[Index, Index]] = {}
        self._pics_size_index: Index = -1
        self._huffman_nodes: List[int] = []
        self._pics_size: List[Coords] = []

    def _read_pics_size(self) -> List[Coords]:
        count = self._partition_map['pics'][1]
        chunk = self._read_chunk(self._pics_size_index)
        chunk_stream = io.BufferedReader(chunk)
        pics_size: List[Coords] = list(stream_unpack_array('<HH', chunk_stream, count, scalar=False))
        return pics_size

    def _read_chunk(self, index: Index) -> bytes:
        chunk_size = self.sizeof(index)
        if chunk_size:
            self._seek_chunk(index)
            compressed_size, expanded_size = self._read_sizes(index)
            chunk = self._data_stream.read(compressed_size)
            chunk = huffman_expand(chunk, expanded_size, self._huffman_nodes)
            return chunk
        else:
            return b''

    def _read_sizes(self, index: Index):
        BLOCK_SIZE = (8 * 8) * 1
        MASKBLOCK_SIZE = (8 * 8) * 2
        compressed_size = self.sizeof(index)

        key = self.find_partition(self._partition_map, index)[0]

        if key == 'tile8':  # tile 8s are all in one chunk!
            expanded_size = BLOCK_SIZE * self._partition_map[key][1]
        elif key == 'tile8m':
            expanded_size = MASKBLOCK_SIZE * self._partition_map[key][1]
        elif key == 'tile16':  # all other tiles are one per chunk
            expanded_size = BLOCK_SIZE * 4
        elif key == 'tile16m':
            expanded_size = MASKBLOCK_SIZE * 4
        elif key == 'tile32':
            expanded_size = BLOCK_SIZE * 16
        elif key == 'tile32m':
            expanded_size = MASKBLOCK_SIZE * 16
        else:  # everything else has an explicit size longword
            expanded_size = stream_unpack('<L', self._data_stream)[0]
            compressed_size -= 4

        return compressed_size, expanded_size

    def _seek_chunk(
        self,
        index: Index,
        offsets: Optional[Sequence[Offset]] = None,
    ) -> None:

        del offsets
        super()._seek_chunk(index, offsets=None)

    def clear(self) -> None:
        super().clear()
        self._header_stream = None
        self._header_offset = 0
        self._header_size = 0
        self._huffman_stream = None
        self._huffman_offset = 0
        self._huffman_size = 0
        self._partition_map = {}
        self._pics_size_index = -1
        self._huffman_nodes = []
        self._pics_size = []

    def close(self) -> None:
        super().close()
        self._header_stream = None
        self._huffman_stream = None

    @classmethod
    def find_partition(
        cls,
        partition_map: GraphicsPartitionMap,
        index: Index,
    ) -> GraphicsPartitionEntry:
        for key, value in partition_map.items():
            start, chunks_count = value
            if chunks_count and key.startswith('tile8'):
                chunks_count = 1
            if start <= index < start + chunks_count:
                return key, start, chunks_count
        raise KeyError(f'chunk index without partition: {index}')

    def open(
        self,
        data_stream: Optional[io.BufferedReader] = None,
        data_offset: Optional[Offset] = None,
        data_size: Optional[Offset] = None,
        header_stream: Optional[io.BufferedReader] = None,
        header_offset: Optional[Offset] = None,
        header_size: Optional[Offset] = None,
        huffman_stream: Optional[io.BufferedReader] = None,
        huffman_offset: Optional[Offset] = None,
        huffman_size: Optional[Offset] = None,
        partition_map: Optional[GraphicsPartitionMap] = None,
        pics_size_index: Index = 0,
    ) -> Self:

        if header_stream is None:
            raise ValueError('a header stream should be provided')
        if huffman_stream is None:
            raise ValueError('a Huffman stream should be provided')
        super().open(data_stream, data_offset=data_offset, data_size=data_size)

        pics_size_index = pics_size_index.__index__()
        if pics_size_index < 0:
            raise ValueError('negative pics size index')

        header_offset, header_size = stream_fit(header_stream, header_offset, header_size)
        if header_size % 3:
            raise ValueError(f'header size must be divisible by 3: {header_size}')

        huffman_offset, huffman_size = stream_fit(huffman_stream, huffman_offset, huffman_size)
        if huffman_size < 4 * HUFFMAN_NODE_COUNT:
            raise ValueError(f'Huffman size: actual={huffman_size} < expected={4 * HUFFMAN_NODE_COUNT}')

        chunk_count = header_size // 3
        chunk_offsets: List[Optional[Offset]] = [None] * chunk_count

        for index in range(chunk_count):
            byte0, byte1, byte2 = stream_unpack('<BBB', header_stream)
            offset = byte0 | (byte1 << 8) | (byte2 << 16)
            if offset < 0xFFFFFF:
                chunk_offsets[index] = offset

        data_size = self._data_size
        chunk_offsets.append(data_size)

        for index in reversed(range(chunk_count)):
            if chunk_offsets[index] is None:
                chunk_offsets[index] = chunk_offsets[index + 1]
        chunk_offsets = _cast(List[Offset], chunk_offsets)

        for index in range(chunk_count):
            if not 0 <= chunk_offsets[index] <= data_size:
                raise ValueError(f'invalid offset value: index={index}')
            if not chunk_offsets[index] <= chunk_offsets[index + 1]:
                raise ValueError(f'invalid offset ordering: index={index}')

        huffman_nodes: List[int] = list(stream_unpack_array('<HH', huffman_stream, HUFFMAN_NODE_COUNT, scalar=False))

        self._chunk_count = chunk_count
        self._chunk_offsets = chunk_offsets
        self._header_stream = header_stream
        self._header_offset = header_offset
        self._header_size = header_size
        self._huffman_stream = huffman_stream
        self._huffman_offset = huffman_offset
        self._huffman_size = huffman_size
        self._partition_map = partition_map
        self._pics_size_index = pics_size_index
        self._huffman_nodes = huffman_nodes
        self._pics_size = self._read_pics_size()
        return self

    @property
    def pics_size(self) -> Sequence[Coords]:
        return self._pics_size


class MapArchiveReader(ArchiveReader):

    def __init__(self, chunk_cache: Cache[Index, Chunk]):
        super().__init__(chunk_cache)

        self._header_stream: Optional[io.BufferedReader] = None
        self._header_offset: Offset = 0
        self._header_size: Offset = 0
        self._planes_count: int = 0
        self._carmacized: bool = True
        self._rlew_tag: int = -1

    def _read_chunk(
        self,
        index: Index,
    ) -> Tuple[TileMapHeader, List[Sequence[int]]]:

        planes: List[Sequence[int]] = []
        chunk_size = self.sizeof(index)
        if not chunk_size:
            raise ValueError('null chunk')

        self._seek_chunk(index)
        data_stream = self._data_stream
        header = TileMapHeader.from_stream(data_stream, self.planes_count)
        carmacized = self._carmacized
        rlew_tag = self._rlew_tag

        for index in range(self.planes_count):
            self._seek_chunk(index, header.plane_offsets)
            expanded_size = stream_unpack('<H', data_stream)[0]
            compressed_size = header.plane_sizes[index] - 2
            chunk = data_stream.read(compressed_size)
            if carmacized:
                chunk = carmack_expand(chunk, expanded_size)[2:]
            plane = rlew_expand(chunk, rlew_tag)
            planes.append(plane)

        return header, planes

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
        planes_count: int = 3,
        carmacized: bool = True,
    ) -> Self:

        if header_stream is None:
            raise ValueError('a header stream should be provided')
        super().open(data_stream, data_offset=data_offset, data_size=data_size)

        planes_count = planes_count.__index__()
        if planes_count < 1:
            raise ValueError(f'invalid planes count: {planes_count}')

        header_base, header_size = stream_fit(header_stream, header_offset, header_size)
        rlew_tag = stream_unpack('<H', header_stream)[0]

        chunk_count_size = header_size - 2
        if chunk_count_size % 4:
            raise ValueError(f'header size - 2 must be divisible by 4: {chunk_count_size}')

        chunk_count = chunk_count_size // 4
        chunk_offsets: List[Optional[Offset]] = [None] * chunk_count

        for i in range(chunk_count):
            offset = stream_unpack('<L', header_stream)[0]
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
        self._planes_count = planes_count
        self._carmacized = carmacized
        self._rlew_tag = rlew_tag
        return self

    @property
    def planes_count(self) -> int:
        return self._planes_count


class VswapArchiveReader(ArchiveReader):

    def __init__(self, chunk_cache: Cache[Index, Chunk]):
        super().__init__(chunk_cache)

        self._pages_offset: Offset = 0
        self._pages_size: Offset = 0
        self._image_size: Coords = (64, 64)
        self._alpha_index: Optional[ColorIndex] = None
        self._sprites_start: Index = 0
        self._sounds_start: Index = 0
        self._sounds_infos: List[SoundInfo] = []

    def _read_chunk(self, index: Index) -> bytes:
        chunk_size = self.sizeof(index)
        if chunk_size:
            self._seek_chunk(index)
            chunk = self._data_stream.read(chunk_size)
            return chunk
        else:
            return b''

    def _read_sounds_infos(self) -> List[SoundInfo]:
        chunk_count = self._chunk_count
        last_chunk_size = self.sizeof(chunk_count - 1)
        if last_chunk_size % 4:
            raise ValueError(f'last chunk size must be divisible by 4: {last_chunk_size}')

        count = last_chunk_size // 4
        self._seek_chunk(chunk_count - 1)

        data_stream = self._data_stream
        bounds: List[Tuple[Index, Offset]] = list(
            stream_unpack_array('<HH', data_stream, count, scalar=False))

        sounds_start = self.sounds_start
        bounds.append(((chunk_count - sounds_start), bounds[-1][1]))
        infos: List[SoundInfo] = []

        for index in range(count):
            start, length = bounds[index]
            if start >= chunk_count - 1:
                return infos[:index]
            last = bounds[index + 1][0]

            if not last or last + sounds_start > chunk_count - 1:
                last = chunk_count - 1
            else:
                last += sounds_start

            actual_length = sum(self.sizeof(j) for j in range(sounds_start + start, last))
            if actual_length & 0xFFFF0000 and (actual_length & 0xFFFF) < length:  # TBV: really needed?
                actual_length -= 0x10000
            actual_length = (actual_length & 0xFFFF0000) | length

            infos.append((start, actual_length))

        return infos

    def clear(self) -> None:
        super().clear()
        self._pages_offset = 0
        self._pages_size = 0
        self._sprites_start = 0
        self._sounds_start = 0
        self._sounds_infos = []

    def open(
        self,
        data_stream: Optional[io.BufferedReader] = None,
        data_offset: Optional[Offset] = None,
        data_size: Optional[Offset] = None,
        image_size: Coords = (64, 64),
        alpha_index: Optional[ColorIndex] = None,
        data_size_guard: Optional[Offset] = None,
    ) -> Self:

        super().open(data_stream, data_offset=data_offset, data_size=data_size)

        data_size = self._data_size
        if data_size % 6:
            raise ValueError(f'data size must be divisible by 6: {data_size}')

        width, height = image_size
        if width < 1 or height < 1:
            raise ValueError(f'invalid image size: {image_size}')

        alpha_index = alpha_index.__index__()
        if not 0x00 <= alpha_index <= 0xFF:
            raise ValueError(f'alpha index out of range: {alpha_index}')

        data_stream = self._data_stream
        chunk_count, sprites_start, sounds_start = stream_unpack('<HHH', data_stream)
        chunk_offsets: List[Offset] = list(stream_unpack_array('<L', data_stream, chunk_count))
        chunk_offsets.append(data_size)

        pages_offset = chunk_offsets[0]
        pages_size = data_size - pages_offset

        if data_size_guard is not None:
            if data_size >= data_size_guard:
                raise ValueError(f'data size guard: actual={data_size} > guard={data_size_guard}')

        for index in reversed(range(chunk_count)):
            if not chunk_offsets[index]:
                chunk_offsets[index] = chunk_offsets[index + 1]

        for index in range(chunk_count):
            if not pages_offset <= chunk_offsets[index] <= data_size:
                raise ValueError(f'inconsistent offset paging: index={index}')
            if not chunk_offsets[index] <= chunk_offsets[index + 1]:
                raise ValueError(f'inconsistent offset ordering: index={index}')

        self._chunk_count = chunk_count
        self._chunk_offsets = chunk_offsets
        self._pages_offset = pages_offset
        self._pages_size = pages_size
        self._image_size = image_size
        self._alpha_index = alpha_index
        self._sprites_start = sprites_start
        self._sounds_start = sounds_start
        self._sounds_infos = self._read_sounds_infos()
        return self

    @property
    def sounds_start(self) -> Index:
        return self._sounds_start

    @property
    def sounds_infos(self) -> List[SoundInfo]:
        return self._sounds_infos

    @property
    def sprites_start(self) -> Index:
        return self._sprites_start

    def iterate_sampled_sound(self, sound_index: Index) -> Iterator[int]:
        start, length = self._sounds_infos[sound_index]
        chunk_index = self._sounds_start + start
        remaining = int(length)

        while remaining:
            chunk = self[chunk_index]
            size = len(chunk)
            if size <= remaining:
                yield from chunk
                remaining -= size
            else:
                yield from memoryview(chunk)[:remaining]
                break
            chunk_index += 1


class ResourceLibrary(collections.abc.Mapping[KT, VT]):

    def __getitem__(self, key: KTS) -> Union[VT, List[VT]]:
        if isinstance(key, slice):
            return [self.get(index) for index in range(key.start, key.stop, key.step)]
        else:
            return self.get(key.__index__())

    def __init__(
        self,
        archive: ArchiveReader,
        resource_cache: Optional[Cache[KT, VT]] = None,
        start: Optional[Index] = None,
        count: Optional[Index] = None,
    ):
        if start is None:
            start = 0
        if start < 0:
            raise ValueError('negative start index')
        if count is None:
            count = len(archive) - start
        if count < 0:
            raise ValueError('negative count')
        if count < start:
            raise ValueError('count < start')
        if resource_cache is None:
            resource_cache = NoCache()

        self._start: Index = start
        self._count: Index = count
        self._archive: ArchiveReader = archive
        self._resource_cache: Cache[KT, VT] = resource_cache

        resource_cache.clear()

    def __iter__(self) -> Iterator[VT]:
        for index in range(self._start, self._count - self._start):
            yield self.get(index)

    def __len__(self) -> Index:
        return self._count

    def _get_chunk(self, index: KT) -> Chunk:
        return self._archive[self._start + index]

    @abc.abstractmethod
    def _get_resource(self, index: KT, chunk: Chunk) -> VT:
        ...

    def get(self, index: Index) -> VT:
        value = self._resource_cache.get(index)
        if value is None:
            value = self._get_resource(index, self._get_chunk(index))
            self._resource_cache[index] = value
        return value
