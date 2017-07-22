import array
from importlib import import_module
import importlib.util
import io
import os
import struct
import sys


def reverse_byte(value):
    # http://graphics.stanford.edu/~seander/bithacks.html#ReverseByteWith64BitsDiv
    return (value * 0x0202020202 & 0x010884422010) % 1023


HUFFMAN_NODE_COUNT = 256
HUFFMAN_HEAD_INDEX = HUFFMAN_NODE_COUNT - 2
HUFFMAN_REVERSED = tuple(map(reverse_byte, range(HUFFMAN_NODE_COUNT)))

HUFFMAN_CLONE_NODES = (tuple((HUFFMAN_REVERSED[i], HUFFMAN_REVERSED[i + 1])
                             for i in range(0, HUFFMAN_NODE_COUNT, 2)) +
                       tuple((HUFFMAN_NODE_COUNT + i, HUFFMAN_NODE_COUNT + i + 1)
                             for i in range(0, HUFFMAN_NODE_COUNT - 1, 2)))

HUFFMAN_MAX_DEPTH = 24
HUFFMAN_MAX_CODE = 0xFFFF
HUFFMAN_MAX_PROBABILITY = 0x7FFFFFFF


CARMACK_NEAR_TAG = 0xA7
CARMACK_FAR_TAG = 0xA8
CARMACK_MAX_SIZE = 1 << 17


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


def huffman_count(data):
    counts = [0] * HUFFMAN_NODE_COUNT
    for datum in data:
        counts[datum] += 1
    return counts


def huffman_trace(index, shift, mask, nodes, shifts, masks, counts):
    code0, code1 = nodes[index]
    shift += 1
    if shift < HUFFMAN_MAX_DEPTH:
        if code0 < HUFFMAN_NODE_COUNT:
            shifts[code0] = shift
            masks[code0] = mask
        else:
            huffman_trace(code0 - HUFFMAN_NODE_COUNT, shift, mask,
                          nodes, shifts, masks, counts)

        mask |= 1 << (shift - 1)
        if code1 < HUFFMAN_NODE_COUNT:
            shifts[code1] = shift
            masks[code1] = mask
        else:
            huffman_trace(code1 - HUFFMAN_NODE_COUNT, shift, mask,
                          nodes, shifts, masks, counts)


def huffman_build_nodes(counts, as_tuples=True):
    probs = list(counts)
    values = list(range(HUFFMAN_NODE_COUNT))
    nodes = [(0, 0)] * HUFFMAN_NODE_COUNT

    for index in range(HUFFMAN_NODE_COUNT):
        prob0 = min(probs)
        if prob0 < HUFFMAN_MAX_PROBABILITY:
            code0 = probs.index(prob0)
        else:
            code0 = HUFFMAN_MAX_CODE
        probs[code0] = HUFFMAN_MAX_PROBABILITY

        prob1 = min(probs)
        if prob1 < HUFFMAN_MAX_PROBABILITY:
            code1 = probs.index(prob1)
        else:
            code1 = HUFFMAN_MAX_CODE
        probs[code0] = prob0  # restore

        if code1 == HUFFMAN_MAX_CODE:
            value0 = values[code0]
            if value0 < HUFFMAN_NODE_COUNT:
                raise ValueError('Last code was not a node')
            elif value0 != HUFFMAN_NODE_COUNT + HUFFMAN_HEAD_INDEX:
                raise ValueError('Wrong head node')
            break
        else:
            value0 = values[code0]
        value1 = values[code1]

        nodes[index] = [value0, value1]
        values[code0] = HUFFMAN_NODE_COUNT + index
        probs[code0] += probs[code1]
        probs[code1] = HUFFMAN_MAX_PROBABILITY

    if as_tuples:
        nodes = tuple(tuple(node) for node in nodes)

    return nodes


def huffman_build_masks(counts, nodes):
    shifts = [0] * HUFFMAN_NODE_COUNT
    masks = [0] * HUFFMAN_NODE_COUNT
    huffman_trace(HUFFMAN_HEAD_INDEX, 0, 0, nodes, shifts, masks, counts)
    return shifts, masks


def huffman_compress(data, shifts, masks):
    output = bytearray(len(data) + 4)
    shift = 0
    tail = 0

    for datum in data:
        mask = masks[datum] << shift
        output[tail] |= mask & 0xFF
        mask >>= 8
        output[tail + 1] |= mask & 0xFF
        mask >>= 8
        output[tail + 2] |= mask & 0xFF
        mask >>= 8
        output[tail + 3] |= mask & 0xFF
        shift += shifts[datum]
        tail += shift >> 3
        shift &= 7

    del output[tail + (shift != 0):]
    return output


def huffman_expand(data, expanded_size, nodes):
    assert expanded_size > 0

    head = nodes[HUFFMAN_HEAD_INDEX]
    output = bytearray()
    append = output.append

    it = iter(data)
    try:
        datum = next(it)
        mask = 1 << 0
        node = head

        while True:
            value = node[1 if datum & mask else 0]
            if value < HUFFMAN_NODE_COUNT:
                append(value)
                node = head
                if len(output) >= expanded_size:
                    break
            else:
                node = nodes[value - HUFFMAN_NODE_COUNT]

            if mask == 1 << 7:
                datum = next(it)
                mask = 1 << 0
            else:
                mask <<= 1

    except StopIteration:
        output += bytes(expanded_size - len(output))

    return bytes(memoryview(output))


def carmack_compress(data):
    source = array.array('H', data)
    if sys.byteorder != 'little':
        source.byteswap()

    output = bytearray()
    append = output.append

    ahead = len(source)
    index = 0

    while True:
        word = source[index]
        count = 0
        match = 0

        for scan in range(index):
            if source[scan] == word:
                length = min(index - scan, ahead, 255)
                if length > 1:
                    for length in range(1, length):
                        if source[scan + length] != source[index + length]:
                            break
                else:
                    length = 1

                if count <= length:
                    count = length
                    match = scan

        if count > 1 and index - match <= 255:
            append(count)
            append(CARMACK_NEAR_TAG)
            append(index - match)

        elif count > 2:
            append(count)
            append(CARMACK_FAR_TAG)
            append(match & 0xFF)
            append(match >> 8)

        else:
            tag = word >> 8
            if tag == CARMACK_NEAR_TAG or tag == CARMACK_FAR_TAG:
                append(0)
                append(tag)
                append(word & 0xFF)
            else:
                append(word & 0xFF)
                append(tag)
            count = 1

        index += count
        ahead -= count

        if not ahead:
            break
        elif ahead < 0:
            raise ValueError('ahead < 0')

    return output


def carmack_expand(data, expanded_size):
    assert expanded_size > 0
    assert expanded_size % struct.calcsize('<H') == 0

    output = bytearray()
    extend = output.extend

    it = iter(data)
    ahead = expanded_size >> 1
    while ahead:
        count, tag = next(it), next(it)
        if tag == CARMACK_NEAR_TAG or tag == CARMACK_FAR_TAG:
            if count:
                if ahead < count:
                    break
                if tag == CARMACK_NEAR_TAG:
                    offset = len(output) - (next(it) << 1)
                else:
                    offset = (next(it) | (next(it) << 8)) << 1
                extend(output[offset:(offset + (count << 1))])
                ahead -= count
            else:
                extend([next(it), tag])
                ahead -= 1
        else:
            extend([count, tag])
            ahead -= 1

    output = bytes(memoryview(output))
    return output


def rlew_compress(data, tag):
    output = array.array('H')
    extend = output.extend

    it = iter(data)
    count = 0
    old = tag
    while True:
        try:
            datum = next(it)
        except StopIteration:
            extend([old] * count)
            break
        try:
            datum |= next(it) << 8
        except StopIteration:
            pass

        if datum == old:
            count += 1
        else:
            if count > 3 or old == tag:
                extend([tag, count, old])
            else:
                extend([old] * count)
            count = 1
            old = datum

    if sys.byteorder != 'little':
        output.byteswap()
    output = output.tobytes()
    return output


def rlew_expand(data, tag):
    output = array.array('H')
    append = output.append
    extend = output.extend

    it = iter(data)
    while True:
        try:
            datum = next(it) | (next(it) << 8)
        except StopIteration:
            break
        if datum == tag:
            count = next(it) | (next(it) << 8)
            value = next(it) | (next(it) << 8)
            extend(value for _ in range(count))
        else:
            append(datum)

    if sys.byteorder != 'little':
        output.byteswap()
    output = output.tobytes()
    return output


def stream_fit(stream, offset=None, size=None):
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


def stream_pack_array(stream, fmt, values, scalar=True):
    if scalar:
        for value in values:
            return stream_write(stream, struct.pack(fmt, value))
    else:
        for entry in values:
            return stream_write(stream, struct.pack(fmt, *entry))


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


class BinaryResource(object):

    @classmethod
    def from_stream(cls, stream, *args, **kwargs):
        raise NotImplementedError
        return cls()

    def to_stream(self, stream, *args, **kwargs):
        raise NotImplementedError

    @classmethod
    def from_bytes(cls, data, *args, **kwargs):
        return cls.from_stream(io.BytesIO(data), *args, **kwargs)

    def to_bytes(self, *args, **kwargs):
        stream = io.BytesIO()
        self.to_stream(stream, *args, **kwargs)
        return stream.getvalue()


class ResourceManager(object):

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
        item = self._build_resource(index, chunk)
        return item

    def _build_resource(self, index, chunk):
        return chunk


class ResourcePrecache(ResourceManager):

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


class ResourceCache(ResourceManager):

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

