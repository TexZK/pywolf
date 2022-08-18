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

import importlib.util
import io
import os
import struct
from importlib import import_module
from typing import Any
from typing import ByteString
from typing import Iterable
from typing import Iterator
from typing import Optional
from typing import Sequence
from typing import Tuple

from .base import Offset


def load_as_module(module_name, path):
    if os.path.exists(path):
        spec = importlib.util.spec_from_file_location(module_name, path)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
    else:
        module = import_module(path)
    return module


def is_in_partition(index, *partitions):
    for partition in partitions:
        start, count = partition
        if start <= index < (start + count):
            return True
    return False


def find_partition(index, partition_map, count_sign=1, cache=None):
    found = None
    if cache is not None:
        found = cache.get(index)

    if found is None:
        if count_sign > 0:
            maximum = 0
            found = None
            for key, value in partition_map.items():
                start, count = value
                if start <= index < (start + count) and maximum < count:
                    maximum = count
                    found = key

        elif count_sign < 0:
            maximum = 0
            found = None
            for key, value in partition_map.items():
                start, count = value
                if start <= index < (start + count) and -count < maximum:
                    maximum = -count
                    found = key

        else:
            for key, value in partition_map.items():
                start, count = value
                if start <= index < (start + count):
                    found = key

    if found is None:
        raise ValueError(index)

    if cache is not None:
        cache[index] = found
    return found


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


def stream_read(  # TODO remove
    stream: io.BufferedReader,
    size: Offset,
) -> bytes:

    chunk = stream.read(size)
    return chunk


def stream_write(  # TODO remove
    stream: io.BufferedReader,
    raw: ByteString,
) -> Offset:

    written = stream.write(raw)
    return written


def stream_pack(  # TODO remove
    stream: io.BufferedReader,
    fmt: str,
    *args: Any,
) -> Offset:

    return stream.write(struct.pack(fmt, *args))


def stream_pack_array(  # TODO remove
    stream: io.BufferedReader,
    fmt: str,
    values: Iterable[Any],
    scalar: bool = True,
) -> Offset:

    written = 0
    if scalar:
        for value in values:
            written += stream.write(struct.pack(fmt, value))
    else:
        for entry in values:
            written += stream.write(struct.pack(fmt, *entry))
    return written


def stream_unpack(  # TODO remove
    fmt: str,
    stream: io.BufferedReader,
) -> Sequence[Any]:

    chunk = stream.read(struct.calcsize(fmt))
    return struct.unpack(fmt, chunk)


def stream_unpack_array(  # TODO remove
    fmt: str,
    stream: io.BufferedReader,
    count: int,
    scalar: bool = True
) -> Iterator[Any]:

    if scalar:
        yield from (stream_unpack(fmt, stream)[0] for _ in range(count))
    else:
        yield from (stream_unpack(fmt, stream) for _ in range(count))


def sequence_index(index, length):  # TODO remove
    assert 0 < length

    if hasattr(index, '__index__'):
        index = index.__index__()
    else:
        index = int(index)

    if index < 0:
        index = length + index

    assert 0 <= index < length, (index, length)
    return index


def sequence_getitem(key, length, getter):  # TODO remove
    if isinstance(key, slice):
        start, stop, step = key.start, key.stop, key.step
        start = sequence_index(start, length)
        stop = sequence_index(stop, length)
        return [getter(i) for i in range(start, stop, step)]
    else:
        return getter(sequence_index(key, length))


class BinaryResource(object):  # TODO remove

    @classmethod
    def from_stream(cls, stream, *args, **kwargs):
        raise NotImplementedError
        return cls()

    def to_stream(self, stream, *args, **kwargs):
        raise NotImplementedError

    @classmethod
    def from_bytes(cls, data, *args, **kwargs):
        return cls.from_stream(io.BufferedReader(data), *args, **kwargs)

    def to_bytes(self, *args, **kwargs):
        stream = io.BufferedReader()
        self.to_stream(stream, *args, **kwargs)
        return stream.getvalue()


class ResourceManager(object):  # TODO remove

    def __init__(self, chunks_handler, start=None, count=None):
        if start is None:
            start = 0
        if count is None:
            count = len(chunks_handler) - start
        assert 0 <= count
        assert 0 <= start

        self._chunks_handler = chunks_handler
        self._start = start
        self._count = count

    def __len__(self):
        return self._count

    def __iter__(self):
        yield from (self[i] for i in range(len(self)))

    def __getitem__(self, key):
        return sequence_getitem(key, len(self), self._get)

    def _get(self, index):
        chunk = self._chunks_handler[self._start + index]
        item = self._load_resource(index, chunk)
        return item

    def _load_resource(self, index, chunk):
        return chunk


class ResourcePrecache(ResourceManager):  # TODO remove

    def __init__(self, wrapped=None, cache=None):
        self._wrapped = wrapped
        self._cache = [] if cache is None else cache

        if wrapped is not None:
            self.cache_all()
        else:
            self.clear()

    def __len__(self):
        return len(self._wrapped)

    def __iter__(self):
        yield from self._cache

    def __getitem__(self, key):
        return self._cache[key]

    def assign(self, wrapped):
        if self._wrapped is not None:
            raise ValueError('already wrapped')
        self._wrapped = wrapped

    def clear(self):
        self._cache.clear()

    def cache_all(self):
        self.clear()
        self._cache.extend(self._wrapped)


class ResourceCache(ResourceManager):  # TODO remove

    def __init__(self, wrapped=None, cache=None):
        self._wrapped = wrapped
        self._cache = {} if cache is None else cache
        self.clear()

    def __len__(self):
        return len(self._wrapped)

    def __iter__(self):
        yield from (self[index] for index in range(len(self)))

    def __getitem__(self, key):
        try:
            return self._cache[key]
        except KeyError:
            item = self._wrapped[key]
            self._cache[key] = item
            return item

    def assign(self, wrapped):
        if self._wrapped is not None:
            raise ValueError('already wrapped')
        self._wrapped = wrapped

    def clear(self):
        self._cache.clear()

    def cache_all(self):
        self.clear()
        self._cache.update(enumerate(self._wrapped))

    def force_unload(self, index):
        self._cache.remove(index)

    def force_load(self, index):
        self.force_unload(index)
        return self[index]

    def load_only(self, indices):
        self.clear()
        self._cache.update((index, self._wrapped[index]) for index in indices)

