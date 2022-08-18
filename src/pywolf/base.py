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
from typing import ByteString
from typing import Dict
from typing import Iterator
from typing import List
from typing import Optional
from typing import Sequence
from typing import Tuple
from typing import TypeVar
from typing import Union


KT = TypeVar('KT')
KTS = Union[KT, slice]
VT = TypeVar('VT')

Index = int
Offset = int

Chunk = ByteString
Char = str

Coord = int
Coords = Tuple[Coord, Coord]


# ============================================================================

# Defined here to avoid circular references
def stream_fit(
    stream: io.BufferedReader,
    offset: Optional[Offset] = None,
    size: Optional[Offset] = None,
) -> Tuple[Offset, Offset]:

    if offset is None:
        offset = stream.tell()
    else:
        offset = offset.__index__()
        if offset < 0:
            raise ValueError('negative offset')

    if size is None:
        stream.seek(0, io.SEEK_END)
        size = stream.tell() - offset
    else:
        size = size.__index__()
        if size < 0:
            raise ValueError('negative size')

    stream.seek(offset, io.SEEK_SET)
    return offset, size


# ============================================================================

class Cache(collections.abc.MutableMapping[KT, VT]):

    @abc.abstractmethod
    def get(self, key: KT, default: Optional[VT] = None) -> Optional[VT]:
        ...

    @abc.abstractmethod
    def set(self, key: KT, value: VT):
        ...


class NoCache(Cache[KT, VT]):

    def __contains__(self, key: KT) -> bool:
        del key
        return False

    def __delitem__(self, key: KTS) -> None:
        del key
        raise KeyError

    def __getitem__(self, key: KTS) -> None:
        del key
        raise KeyError

    def __iter__(self) -> Iterator[VT]:
        yield from ()

    def __len__(self) -> int:
        return 0

    def __setitem__(self, key: KT, value: VT) -> None:
        del key, value

    def clear(self) -> None:
        pass

    def get(self, key: KT, default: Optional[VT] = None) -> Optional[VT]:
        return default

    def set(self, key: KT, value: VT):
        pass


class PersistentCache(Cache[KT, VT], dict):

    def get(self, key: KT, default: Optional[VT] = None) -> Optional[VT]:
        instance = self.get(key, default)
        return instance

    def set(self, key: KT, value: VT):
        self[key] = value


class Codec(abc.ABC):

    @classmethod
    @abc.abstractmethod
    def calcsize_stateless(cls) -> Offset:
        ...

    @abc.abstractmethod
    def to_bytes(self) -> bytes:
        ...

    def into_bytearray(self, buffer: bytearray, offset: Offset = 0) -> Offset:
        chunk = self.to_bytes()
        size = len(chunk)
        stop = offset + size
        buffer[offset:stop] = chunk
        return stop

    @classmethod
    @abc.abstractmethod
    def from_bytes(cls, buffer: ByteString, offset: Offset = 0) -> Tuple['Codec', Offset]:
        ...

    def into_stream(self, stream: io.BytesIO) -> None:
        chunk = self.to_bytes()
        stream.write(chunk)

    @classmethod
    def from_stream(cls, stream: io.BytesIO) -> 'Codec':
        size = cls.calcsize_stateless()
        chunk = stream.read(size)
        instance, _ = cls.from_bytes(chunk)
        return instance


# ============================================================================

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
        chunk_cache: Optional[Cache[Index, Chunk]] = None,
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
    ) -> None:

        if data_stream is None:
            raise ValueError('a data stream should be provided')
        data_offset, data_size = stream_fit(data_stream, data_offset, data_size)

        self._data_stream = data_stream
        self._data_offset = data_offset
        self._data_size = data_size

    def close(self) -> None:
        self._data_stream = None

    def clear(self) -> None:
        self._data_stream = None
        self._data_offset = 0
        self._data_size = 0
        self._chunk_count = 0
        self._chunk_offsets = []
        self._chunk_cache.clear()

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


# ============================================================================

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
