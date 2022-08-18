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
from typing import Iterator
from typing import Optional
from typing import Sequence
from typing import Tuple
from typing import TypeVar
from typing import Union

Index = int
Offset = int
Chunk = ByteString

GenericItem = TypeVar('GenericItem')
KT = TypeVar('KT')
KTS = Union[KT, slice]
VT = TypeVar('VT')
Char = str

Coord = int
Coords = Tuple[Coord, Coord]

ColorIndex = int
ColorRGB = Tuple[int, int, int]
PaletteFlat: Sequence[ColorIndex]
PaletteRGB = Sequence[ColorRGB]
PixelsFlat = Sequence[ColorIndex]


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
        raise NotImplementedError


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
