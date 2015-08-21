'''
@author: Andrea Zoppi
'''

import array
import io
import logging
import struct
import sys

from .utils import (stream_bound, stream_read, stream_write,
                    stream_unpack, stream_unpack_array,
                    sequence_index, sequence_getitem)


HUFFMAN_NODES_COUNT = 255
HUFFMAN_HEAD_INDEX = HUFFMAN_NODES_COUNT - 1

CARMACK_NEAR_TAG = 0xA7
CARMACK_FAR_TAG = 0xA8


def huffman_expand(data, expanded_size, nodes):
    assert expanded_size > 0

    head = nodes[HUFFMAN_HEAD_INDEX]
    output = bytearray()
    append = output.append

    it = iter(data)
    try:
        datum = next(it)
        mask = (1 << 0)
        node = head
        while True:
            value = node[1 if datum & mask else 0]
            if value < 0x100:
                append(value)
                node = head
                if len(output) >= expanded_size:
                    break
            else:
                node = nodes[value - 0x100]

            if mask == (1 << 7):
                datum = next(it)
                mask = (1 << 0)
            else:
                mask <<= 1

    except StopIteration:
        output.extend(0 for _ in range(expanded_size - len(output)))

    return bytes(memoryview(output))


def carmack_expand(data, expanded_size):
    assert expanded_size > 0
    assert expanded_size % struct.calcsize('<H') == 0

    output = bytearray()
    expand = output.expand

    it = iter(data)
    length = expanded_size >> 1
    while length:
        count, tag = next(it), next(it)
        if tag == CARMACK_NEAR_TAG or tag == CARMACK_FAR_TAG:
            if count:
                if length < count:
                    break
                if tag == CARMACK_NEAR_TAG:
                    offset = len(output) - (next(it) << 1)
                else:
                    offset = (next(it) | (next(it) << 8)) << 1
                expand(output[offset:(offset + (count << 1))])
                length -= count
            else:
                expand([next(it), tag])
                length -= 1
        else:
            expand([count, tag])
            length -= 1

    return bytes(memoryview(output))


def rlew_compress(data, tag):
    output = array.array('H')
    expand = output.expand

    it = iter(data)
    count = 0
    old = tag
    while True:
        try:
            datum = next(it)
        except StopIteration:
            break
        try:
            datum |= next(it) << 8
        except StopIteration:
            pass

        if datum == old:
            count += 1
        else:
            if count > 3 or old == tag:
                expand([tag, count, old])
            else:
                expand(old for _ in range(count))
            count = 1
            old = datum

    if sys.byteorder != 'little':
        output.byteswap()
    return output.tobytes()


def rlew_expand(data, tag):
    output = array.array('H')
    append = output.append
    expand = output.expand

    it = iter(data)
    while True:
        try:
            datum = next(it) | (next(it) << 8)
        except StopIteration:
            break
        if datum == tag:
            count = next(it) | (next(it) << 8)
            value = next(it) | (next(it) << 8)
            expand(value for _ in range(count))
        else:
            append(datum)

    if sys.byteorder != 'little':
        output.byteswap()
    return output.tobytes()


def jascpal_read(stream):
    line = stream.readline().strip()
    assert line == 'JASC-PAL'
    line = stream.readline().strip()
    assert line == '0100'
    line = stream.readline().strip()
    count = int(line)
    assert count > 0
    palette = [None] * count
    for i in range(count):
        r, g, b = [int(x) for x in stream.readline().split()]
        assert 0x00 <= r <= 0xFF
        assert 0x00 <= g <= 0xFF
        assert 0x00 <= b <= 0xFF
        palette[i] = [r, g, b]
    return palette


def jascpal_write(stream, palette):
    assert palette
    stream_write(stream, 'JASC-PAL\n')
    stream_write(stream, '0100\n')
    stream_write(stream, '{:d}\n'.format(len(palette)))
    for r, g, b in palette:
        assert 0x00 <= r <= 0xFF
        assert 0x00 <= g <= 0xFF
        assert 0x00 <= b <= 0xFF
        stream_write(stream, '{:d} {:d} {:d}\n'.format(r, g, b))


class ChunksHandler(object):

    def __init__(self):
        self.clear()

    def clear(self):
        self._data_stream = None
        self._data_base = None
        self._data_size = None
        self._chunk_count = 0
        self._chunk_offsets = ()

    def _offsetof(self, index):
        return self._chunk_offsets[sequence_index(index, self._chunk_count)]

    def _sizeof(self, index):
        chunk_offsets = self._chunk_offsets
        index = sequence_index(index, self._chunk_count)
        return chunk_offsets[index + 1] - chunk_offsets[index]

    def _seek(self, index, offsets=None):
        data_stream = self._data_stream
        data_base = self._data_base

        if offsets is None:
            offset = self._offsetof(index)
        else:
            offset = offsets[sequence_index(index, len(offsets))]

        data_stream.seek(data_base + offset)

    def load(self, data_stream, data_base=0, data_size=None):
        logger = logging.getLogger()
        self.clear()

        data_base, data_size = stream_bound(data_stream, data_base, data_size)
        logger.info('%r.load(data_stream=%r, data_base=0x%X, data_size=0x%X)',
                    self, data_stream, data_base, data_size)

        self._data_stream = data_stream
        self._data_base = data_base
        self._data_size = data_size
        return self

    def extract_chunk(self, index):
        raise NotImplementedError

    def _log_extract_chunk(self, index):
        logger = logging.getLogger()
        logger.debug('%r.extract_chunk(index=%d), chunk_offset=0x%X, chunk_size=0x%X',
                     self, index, self._offsetof(index), self._sizeof(index))

    def __len__(self):
        return self._chunk_count

    def __getitem__(self, index):
        return sequence_getitem(index, len(self), self.extract_chunk)

    def __contains__(self, item):
        return item in self

    def __iter__(self):
        yield from (self[i] for i in range(len(self)))


class PrecachedChunksHandler(ChunksHandler):

    def clear(self):
        super().clear()
        self._chunks = ()

    def __getitem__(self, index):
        return self._chunks[index]

    def __iter__(self):
        yield from self._chunks

    def _precache_all_chunks(self):
        chunk_count = self._chunk_count
        chunks = [b''] * chunk_count
        for i in range(chunk_count):
            chunks[i] = self.extract_chunk(i)
        self._chunks = chunks


class SpriteHeader(object):

    def __init__(self, left, right, offsets):
        self.left = left
        self.right = right
        self.offsets = offsets

    @classmethod
    def from_stream(cls, chunk_stream):
        left, right = stream_unpack('<HH', chunk_stream)
        width = right - left + 1
        offsets = list(stream_unpack_array('<H', chunk_stream, width))
        return cls(left, right, offsets)


class VSwapChunksHandler(ChunksHandler):

    def clear(self):
        super().clear()
        self._pages_offset = None
        self._pages_size = None
        self.sprites_start = None
        self.sounds_start = None

    def _seek(self, index, offsets=None):
        data_stream = self._data_stream
        data_base = self._data_base
        if offsets is None:
            offset = self._offsetof(index)
        else:
            offset = offsets[sequence_index(index, len(offsets))]
        data_stream.seek(data_base + offset)

    def load(self, data_stream, data_base=None, data_size=None, dimensions=(64, 64), alpha_index=0xFF):
        super().load(data_stream, data_base, data_size)
        data_stream = self._data_stream
        data_base = self._data_base
        data_size = self._data_size
        assert data_size % struct.calcsize('<LH') == 0
        alpha_index = int(alpha_index)
        assert 0x00 <= alpha_index <= 0xFF

        chunk_count, sprites_start, sounds_start = stream_unpack('<HHH', data_stream)
        chunk_offsets = list(stream_unpack_array('<L', data_stream, chunk_count))
        chunk_offsets.append(data_size)

        pages_offset = chunk_offsets[0]
        pages_size = data_size - pages_offset
        assert data_size < (100 << 20)  # 100 MiB
        for i in reversed(range(chunk_count)):
            if not chunk_offsets[i]:
                chunk_offsets[i] = chunk_offsets[i + 1]
        assert all(pages_offset <= chunk_offsets[i] <= data_size for i in range(chunk_count))
        assert all(chunk_offsets[i] <= chunk_offsets[i + 1] for i in range(chunk_count)), chunk_offsets

        self._chunk_count = chunk_count
        self._chunk_offsets = chunk_offsets
        self._pages_offset = pages_offset
        self._pages_size = pages_size
        self._dimensions = dimensions
        self._alpha_index = alpha_index
        self.sprites_start = sprites_start
        self.sounds_start = sounds_start
        self.sounds_infos = self._read_sounds_infos()
        return self

    def extract_chunk(self, index):
        self._log_extract_chunk(index)
        data_stream = self._data_stream

        chunk_size = self._sizeof(index)
        if not chunk_size:
            return b''

        self._seek(index)
        chunk = stream_read(data_stream, chunk_size)
        return chunk

    def _read_sounds_infos(self):
        data_stream = self._data_stream
        chunk_count = self._chunk_count
        sounds_start = self.sounds_start

        assert self._sizeof(chunk_count - 1) % struct.calcsize('<HH') == 0
        count = self._sizeof(chunk_count - 1) // struct.calcsize('<HH')
        self._seek(chunk_count - 1)
        bounds = list(stream_unpack_array('<HH', data_stream, count, scalar=False))
        bounds.append([(chunk_count - sounds_start), bounds[-1][1]])
        infos = [None] * count

        for i in range(count):
            start, length = bounds[i]
            if start >= chunk_count - 1:
                return infos[:i]
            last = bounds[i + 1][0]

            if not last or last + sounds_start > chunk_count - 1:
                last = chunk_count - 1;
            else:
                last += sounds_start;

            actual_length = sum(self._sizeof(j) for j in range(sounds_start + start, last))
            if actual_length & 0xFFFF0000 and (actual_length & 0xFFFF) < length:  # FIXME: really needed?
                actual_length -= 0x10000;
            actual_length = (actual_length & 0xFFFF0000) | length;

            infos[i] = (start, actual_length)

        return infos


class PrecachedVSwapChunksHandler(VSwapChunksHandler, PrecachedChunksHandler):

    def load(self, data_stream, data_base=None, data_size=None):
        super().load(data_stream, data_base, data_size)
        self._precache_all_chunks()
        return self


class AdLibSoundHeader(object):

    def __init__(self,
                 length, priority,
                 modulator_char, carrier_char,
                 modulator_scale, carrier_scale,
                 modulator_attack, carrier_attack,
                 modulator_sustain, carrier_sustain,
                 modulator_wave, carrier_wave,
                 conn, voice, mode, block):
        self.length            = length
        self.priority          = priority
        self.modulator_char    = modulator_char
        self.carrier_char      = carrier_char
        self.modulator_scale   = modulator_scale
        self.carrier_scale     = carrier_scale
        self.modulator_attack  = modulator_attack
        self.carrier_attack    = carrier_attack
        self.modulator_sustain = modulator_sustain
        self.carrier_sustain   = carrier_sustain
        self.modulator_wave    = modulator_wave
        self.carrier_wave      = carrier_wave
        self.conn              = conn
        self.voice             = voice
        self.mode              = mode
        self.block             = block

    @classmethod
    def from_stream(cls, data_stream):
        args = list(stream_unpack('<LH13B', data_stream))
        stream_unpack('<3B', data_stream)  # unused
        args += stream_unpack('<B', data_stream)
        return cls(*args)


class AudioChunksHandler(ChunksHandler):

    def clear(self):
        super().clear()
        self._header_stream = None
        self._header_base = None
        self._header_size = None

    def load(self, header_stream, data_stream,
             header_base=None, header_size=None,
             data_base=None, data_size=None):

        super().load(data_stream, data_base, data_size)
        data_size = self._data_size
        header_base, header_size = stream_bound(header_stream, header_base, header_size)
        assert header_size % struct.calcsize('<L') == 0

        chunk_count = header_size // struct.calcsize('<L')
        chunk_offsets = list(stream_unpack_array('<L', header_stream, chunk_count))
        chunk_offsets.append(data_size)
        assert all(0 <= chunk_offsets[i] <= data_size for i in range(chunk_count))
        assert all(chunk_offsets[i] <= chunk_offsets[i + 1] for i in range(chunk_count))

        self._chunk_count = chunk_count
        self._chunk_offsets = chunk_offsets
        self._header_stream = header_stream
        self._header_base = header_base
        self._header_size = header_size
        return self

    def extract_chunk(self, index):
        self._log_extract_chunk(index)
        chunk_count = self._chunk_count
        chunk_offsets = self._chunk_offsets
        data_stream = self._data_stream
        data_size = self._data_size
        index = sequence_index(index, chunk_count)

        header = None
        chunk = b''
        chunk_size = chunk_offsets[index + 1] - chunk_offsets[index]
        if chunk_size:
            self._seek(index)
            header = AdLibSoundHeader.from_stream(data_stream)
            chunk = stream_read(data_stream, (data_size - data_stream.tell()))
        return (header, chunk)


class PrecachedAudioChunksHandler(AudioChunksHandler, PrecachedChunksHandler):

    def load(self, header_stream, data_stream,
             header_base=None, header_size=None,
             data_base=None, data_size=None):

        super().load(data_stream, header_stream,
                     data_base, data_size,
                     header_base, header_size)
        self._precache_all_chunks()
        return self


class FontHeader(object):

    CHARACTER_COUNT = 256

    def __init__(self, height, offsets, widths):
        assert 0 < height
        assert len(offsets) == 256
        assert len(widths) == 256

        self.height = height
        self.offsets = offsets
        self.widths = widths

    @classmethod
    def from_stream(cls, chunk_stream):
        height = stream_unpack('<H', chunk_stream)
        locations = stream_unpack_array('<H', chunk_stream, cls.CHARACTER_COUNT)
        widths = stream_unpack_array('<B', chunk_stream, cls.CHARACTER_COUNT)
        return cls(height, locations, widths)


class GraphicsChunksHandler(ChunksHandler):

    def clear(self):
        super().clear()
        self._header_stream = None
        self._header_base = None
        self._header_size = None
        self._huffman_stream = None
        self._huffman_offset = None
        self._huffman_size = None
        self._partition_map = {}
        self._pics_dimensions_index = None
        self._huffman_nodes = ()
        self.dimensions = ()

    def _seek(self, index, offsets=None):
        data_stream = self._data_stream
        data_base = self._data_base
        data_stream.seek(data_base + self._offsetof(index))

    def load(self, data_stream, header_stream, huffman_stream,
             partition_map, pics_dimensions_index=0,
             data_base=None, data_size=None,
             header_base=None, header_size=None,
             huffman_offset=None, huffman_size=None):

        super().load(data_stream, data_base, data_size)
        data_size = self._data_size
        pics_dimensions_index = int(pics_dimensions_index)
        assert pics_dimensions_index >= 0
        header_base, header_size = stream_bound(header_stream, header_base, header_size)
        huffman_offset, huffman_size = stream_bound(huffman_stream, huffman_offset, huffman_size)
        assert header_size % struct.calcsize('<BBB') == 0
        assert huffman_size >= struct.calcsize('<HH') * HUFFMAN_NODES_COUNT

        chunk_count = header_size // struct.calcsize('<BBB')
        chunk_offsets = [None] * chunk_count
        for i in range(chunk_count):
            byte0, byte1, byte2 = stream_unpack('<BBB', header_stream)
            offset = byte0 | (byte1 << 8) | (byte2 << 16)
            if offset < 0xFFFFFF:
                chunk_offsets[i] = offset
        chunk_offsets.append(data_size)
        for i in reversed(range(chunk_count)):
            if chunk_offsets[i] is None:
                chunk_offsets[i] = chunk_offsets[i + 1]
        assert all(0 <= chunk_offsets[i] <= data_size for i in range(chunk_count))
        assert all(chunk_offsets[i] <= chunk_offsets[i + 1] for i in range(chunk_count))

        huffman_nodes = list(stream_unpack_array('<HH', huffman_stream,
                                                  HUFFMAN_NODES_COUNT, scalar=False))
        self._chunk_count = chunk_count
        self._chunk_offsets = chunk_offsets
        self._header_stream = header_stream
        self._header_base = header_base
        self._header_size = header_size
        self._huffman_stream = huffman_stream
        self._huffman_offset = huffman_offset
        self._huffman_size = huffman_size
        self._partition_map = partition_map
        self._pics_dimensions_index = pics_dimensions_index
        self._huffman_nodes = huffman_nodes
        self.pics_dimensions = self._build_pics_dimensions()
        return self

    def extract_chunk(self, index):
        self._log_extract_chunk(index)
        chunk_count = self._chunk_count
        data_stream = self._data_stream
        huffman_nodes = self._huffman_nodes
        index = sequence_index(index, chunk_count)

        chunk = b''
        chunk_size = self._sizeof(index)
        if chunk_size:
            self._seek(index)
            compressed_size, expanded_size = self._read_sizes(index)
            chunk = stream_read(data_stream, compressed_size)
            chunk = huffman_expand(chunk, expanded_size, huffman_nodes)
        return chunk

    def _read_sizes(self, index):
        logger = logging.getLogger()
        data_stream = self._data_stream
        partition_map = self._partition_map

        BLOCK_SIZE = 8 * 8 * struct.calcsize('<B')
        MASKBLOCK_SIZE = 8 * 8 * struct.calcsize('<H')
        compressed_size = self._sizeof(index)
        key, *value = self.find_partition(partition_map, index)

        if key == 'tile8':  # tile 8s are all in one chunk!
            expanded_size = BLOCK_SIZE * partition_map[key][1]
        elif key == 'tile8m':
            expanded_size = MASKBLOCK_SIZE * partition_map[key][1]
        elif key == 'tile16':  # all other tiles are one/chunk
            expanded_size = BLOCK_SIZE * 4
        elif key == 'tile16m':
            expanded_size = MASKBLOCK_SIZE * 4
        elif key == 'tile32':
            expanded_size = BLOCK_SIZE * 16
        elif key == 'tile32m':
            expanded_size = MASKBLOCK_SIZE * 16
        else:  # everything else has an explicit size longword
            expanded_size = stream_unpack('<L', data_stream)[0]
            compressed_size -= struct.calcsize('<L')

        logger.debug('%r._read_sizes(index=%d), partition_map[%r]=%r, '
                     'compressed_size=0x%X, expanded_size=0x%X',
                     self, index, key, value, compressed_size, expanded_size)

        return compressed_size, expanded_size

    def _build_pics_dimensions(self):
        partition_map = self._partition_map
        pics_dimensions_index = self._pics_dimensions_index

        count = partition_map['pics'][1]
        chunk = self.extract_chunk(pics_dimensions_index)
        pics_dimensions = list(stream_unpack_array('<HH', io.BytesIO(chunk), count, scalar=False))
        return pics_dimensions

    @classmethod
    def find_partition(cls, partition_map, index):
        for key, value in partition_map.items():
            start, chunks_count = value
            if chunks_count and key.startswith('tile8'):
                chunks_count = 1
            if start <= index < start + chunks_count:
                return (key, start, chunks_count)
        raise KeyError(index)


class PrecachedGraphicsChunksHandler(GraphicsChunksHandler, PrecachedChunksHandler):

    def load(self, data_stream, header_stream, huffman_stream,
             partition_map, pics_dimensions_index=0,
             data_base=None, data_size=None,
             header_base=None, header_size=None,
             huffman_offset=None, huffman_size=None):

        super().load(data_stream, header_stream, huffman_stream,
                     partition_map, pics_dimensions_index,
                     data_base, data_size,
                     header_base, header_size,
                     huffman_offset, huffman_size)
        self._precache_all_chunks()
        return self


class MapHeader(object):

    def __init__(self, plane_offsets, plane_sizes, width, height, name):
        self.plane_offsets = plane_offsets
        self.plane_sizes = plane_sizes
        self.width = width
        self.height = height
        self.name = name

    @classmethod
    def from_stream(cls, data_stream, planes_count=3):
        planes_count = int(planes_count)
        assert planes_count > 0
        plane_offsets = tuple(stream_unpack_array('<L', data_stream, planes_count))
        plane_sizes = tuple(stream_unpack_array('<H', data_stream, planes_count))
        width, height = stream_unpack('<HH', data_stream)
        name = stream_unpack('<16s', data_stream)
        return cls(plane_offsets, plane_sizes, width, height, name)


class MapChunksHandler(ChunksHandler):  # TODO

    def clear(self):
        super().clear()
        self._header_stream = None
        self._header_base = None
        self._header_size = None
        self._carmacized = True
        self._rlew_tag = None
        self.planes_count = 0

    def _seek(self, index, offsets=None):
        data_stream = self._data_stream
        data_base = self._data_base
        if offsets is None:
            offset = self._offsetof(index)
        else:
            offset = offsets[sequence_index(index, len(offsets))]
        data_stream.seek(data_base + offset)

    def load(self, data_stream, header_stream,
             data_base=None, data_size=None,
             header_base=None, header_size=None,
             planes_count=3, carmacized=True):

        super().load(data_stream, data_base, data_size)
        data_size = self._data_size
        planes_count = int(planes_count)
        carmacized = bool(carmacized)
        assert planes_count > 0
        header_base, header_size = stream_bound(header_stream, header_base, header_size)
        assert header_size % struct.calcsize('<H') == 0

        rlew_tag = stream_unpack('<H', header_stream)[0]

        chunk_count = (header_size - struct.calcsize('<H')) // struct.calcsize('<L')
        chunk_offsets = [None] * chunk_count
        for i in range(chunk_count):
            offset = stream_unpack('<L', header_stream)[0]
            if 0 < offset < 0xFFFFFFFF:
                chunk_offsets[i] = offset
        chunk_offsets.append(header_size)
        for i in reversed(range(chunk_count)):
            if chunk_offsets[i] is None:
                chunk_offsets[i] = chunk_offsets[i + 1]
        assert all(0 < chunk_offsets[i] <= data_size for i in range(chunk_count))
        assert all(chunk_offsets[i] <= chunk_offsets[i + 1] for i in range(chunk_count))

        self._chunk_count = chunk_count
        self._chunk_offsets = chunk_offsets
        self._header_stream = header_stream
        self._header_base = header_base
        self._header_size = header_size
        self._carmacized = carmacized
        self._rlew_tag = rlew_tag
        self.planes_count = planes_count
        return self

    def extract_chunk(self, index):
        self._log_extract_chunk(index)
        chunk_count = self._chunk_count
        chunk_offsets = self._chunk_offsets
        data_stream = self._data_stream
        carmacized = self._carmacized
        rlew_tag = self._rlew_tag
        planes_count = self.planes_count
        index = sequence_index(index, chunk_count)

        header = None
        planes = [None] * planes_count
        chunk_size = chunk_offsets[index + 1] - chunk_offsets[index]
        if chunk_size:
            self._seek(index)
            header = MapHeader.from_stream(data_stream, planes_count)

            for i in range(planes_count):
                self._seek(i, header.plane_offsets)
                expanded_size = stream_unpack('<H', data_stream)
                compressed_size = header.plane_sizes[i] - struct.calcsize('<H')
                chunk = stream_read(data_stream, compressed_size)
                if carmacized:
                    chunk = carmack_expand(chunk, expanded_size)[struct.calcsize('<H'):]
                planes[i] = rlew_expand(chunk, rlew_tag)
        return (header, planes)


class PrecachedMapChunksHandler(MapChunksHandler, PrecachedChunksHandler):

    def load(self, data_stream, header_stream,
             header_base=None, header_size=None,
             data_base=None, data_size=None):

        super().load(data_stream, header_stream,
                     data_base, data_size,
                     header_base, header_size)
        self._precache_all_chunks()
        return self
