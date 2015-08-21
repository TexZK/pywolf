'''
@author: Andrea Zoppi
'''

import io
import struct


def stream_bound(stream, offset=None, size=None):
    if offset is None:
        offset = stream.tell()
    else:
        offset = int(offset)

    if size is None:
        stream.seek(0, io.SEEK_END)
        size = stream.tell() - offset
        stream.seek(offset, io.SEEK_SET)
    else:
        size = int(size)

    return offset, size


def stream_read(stream, size):
    chunks = []
    remaining = size
    while remaining:
        chunk = stream.read(remaining)
        if chunk:
            chunks.append(chunk)
            remaining -= len(chunk)
        else:
            fmt = 'EOF at stream {!s} offset 0x{:X}'.format
            raise IOError(fmt(stream, stream.tell()))
    return b''.join(chunks)


def stream_write(stream, raw):
    written = 0
    if isinstance(raw, str):
        raw_view = raw
    else:
        raw_view = memoryview(raw)
    while written < len(raw):
        written += stream.write(raw_view[written:])
    return written


def stream_pack(stream, fmt, *args):
    return stream_write(stream, struct.pack(fmt, *args))


def stream_unpack(fmt, stream):
    chunk = stream_read(stream, struct.calcsize(fmt))
    return struct.unpack(fmt, chunk)


def stream_unpack_array(fmt, stream, count, scalar=True):
    if scalar:
        yield from (stream_unpack(fmt, stream)[0] for _ in range(count))
    else:
        yield from (stream_unpack(fmt, stream) for _ in range(count))


def sequence_index(index, length):
    assert 0 < length

    if hasattr(index, '__index__'):
        index = index.__index__()
    else:
        index = int(index)

    if index < 0:
        index = length + index

    assert 0 <= index < length, (index, length)
    return index


def sequence_getitem(key, length, getter):
    if isinstance(key, slice):
        start, stop, step = key.start, key.stop, key.step
        start = sequence_index(start, length)
        stop = sequence_index(stop, length)
        return [getter(i) for i in range(start, stop, step)]
    else:
        return getter(sequence_index(key, length))


class ResourceManager(object):

    def __init__(self, chunks_handler, start=None, count=None, cache=None):
        if start is None:
            start = 0
        if count is None:
            count = len(chunks_handler) - start
        assert 0 <= count
        assert not count or 0 <= start < count

        self._chunks_handler = chunks_handler
        self._start = start
        self._count = count
        self._cache = {} if cache is None else cache

    def __len__(self):
        return self._count

    def __iter__(self):
        yield from (self[i] for i in range(len(self)))

    def __getitem__(self, key):
        return sequence_getitem(key, len(self), self._get)

    def _get(self, index):
        chunks_handler = self._chunks_handler
        start = self._start
        cache = self._cache

        try:
            item = cache[index]
        except KeyError:
            chunk = chunks_handler[start + index]
            item = self._build_resource(index, chunk)
            cache[index] = item
        return item

    def _build_resource(self, index, chunk):
        raise NotImplementedError

    def clear(self):
        self._cache.clear()
