import io

from pywolf.compression import HUFFMAN_NODE_COUNT, huffman_expand, carmack_expand, rlew_expand
from pywolf.game import TileMapHeader
from pywolf.utils import stream_fit, stream_read, stream_unpack, stream_unpack_array, sequence_index, sequence_getitem


class ChunksHandler(object):

    def __init__(self):
        self.clear()

    def clear(self):
        self._data_stream = None
        self._data_base = None
        self._data_size = None
        self._chunk_count = 0
        self._chunk_offsets = ()

    def offsetof(self, index):
        return self._chunk_offsets[sequence_index(index, len(self))]

    def sizeof(self, index):
        chunk_offsets = self._chunk_offsets
        index = sequence_index(index, len(self))
        return chunk_offsets[index + 1] - chunk_offsets[index]

    def _seek(self, index, offsets=None):
        data_stream = self._data_stream
        data_base = self._data_base

        if offsets is None:
            offset = self.offsetof(index)
        else:
            offset = offsets[sequence_index(index, len(offsets))]

        data_stream.seek(data_base + offset)

    def load(self, data_stream, data_base=None, data_size=None):
        self.clear()
        data_base, data_size = stream_fit(data_stream, data_base, data_size)
        self._data_stream = data_stream
        self._data_base = data_base
        self._data_size = data_size

    def extract_chunk(self, index):
        raise NotImplementedError

    def __len__(self):
        return self._chunk_count

    def __getitem__(self, key):
        return sequence_getitem(key, len(self), self.extract_chunk)

    def __contains__(self, item):
        return item in self

    def __iter__(self):
        yield from (self[index] for index in range(len(self)))


class PrecachedChunksHandler(ChunksHandler):

    def __init__(self, wrapped=None, cache=None):
        self._wrapped = wrapped
        self._cache = [] if cache is None else cache

        if wrapped is not None:
            self.cache_all()
        else:
            self.clear()

    def clear(self):
        self._cache.clear()

    def offsetof(self, index):
        return self._wrapped.offsetof(index)

    def sizeof(self, index):
        return self._wrapped.sizeof(index)

    def _seek(self, index, offsets=None):
        pass

    def load(self, *args, **kwargs):
        self._wrapped.load(*args, **kwargs)

    def extract_chunk(self, index):
        return self._cache[index]

    def __len__(self):
        return len(self._wrapped)

    def __getitem__(self, key):
        return self._cache[key]

    def __contains__(self, item):
        return item in self._cache

    def __iter__(self):
        yield from self._cache

    def assign(self, wrapped):
        if self._wrapped is not None and self._wrapped is not wrapped:
            raise ValueError('already wrapped')
        self._wrapped = wrapped

    def cache_all(self):
        self.clear()
        self._cache.extend(self._wrapped)


class VSwapChunksHandler(ChunksHandler):

    def clear(self):
        super().clear()
        self._pages_offset = None
        self._pages_size = None
        self.sprites_start = None
        self.sounds_start = None

    def load(self, data_stream, data_base=None, data_size=None, image_size=(64, 64), alpha_index=0xFF,
             data_size_guard=None):
        super().load(data_stream, data_base, data_size)
        data_stream = self._data_stream
        data_base = self._data_base
        data_size = self._data_size
        assert data_size % 6 == 0
        alpha_index = int(alpha_index)
        assert 0x00 <= alpha_index <= 0xFF

        chunk_count, sprites_start, sounds_start = stream_unpack('<HHH', data_stream)
        chunk_offsets = list(stream_unpack_array('<L', data_stream, chunk_count))
        chunk_offsets.append(data_size)

        pages_offset = chunk_offsets[0]
        pages_size = data_size - pages_offset
        assert data_size_guard is None or data_size < data_size_guard
        for i in reversed(range(chunk_count)):
            if not chunk_offsets[i]:
                chunk_offsets[i] = chunk_offsets[i + 1]
        assert all(pages_offset <= chunk_offsets[i] <= data_size for i in range(chunk_count))
        assert all(chunk_offsets[i] <= chunk_offsets[i + 1] for i in range(chunk_count))

        self._chunk_count = chunk_count
        self._chunk_offsets = chunk_offsets
        self._pages_offset = pages_offset
        self._pages_size = pages_size
        self._image_size = image_size
        self._alpha_index = alpha_index
        self.sprites_start = sprites_start
        self.sounds_start = sounds_start
        self.sounds_infos = self._read_sounds_infos()
        return self

    def extract_chunk(self, index):
        data_stream = self._data_stream

        chunk_size = self.sizeof(index)
        if not chunk_size:
            return b''

        self._seek(index)
        chunk = stream_read(data_stream, chunk_size)
        return chunk

    def _read_sounds_infos(self):
        data_stream = self._data_stream
        chunk_count = self._chunk_count
        sounds_start = self.sounds_start

        assert self.sizeof(chunk_count - 1) % 4 == 0
        count = self.sizeof(chunk_count - 1) // 4
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
                last = chunk_count - 1
            else:
                last += sounds_start

            actual_length = sum(self.sizeof(j) for j in range(sounds_start + start, last))
            if actual_length & 0xFFFF0000 and (actual_length & 0xFFFF) < length:  # TBV: really needed?
                actual_length -= 0x10000
            actual_length = (actual_length & 0xFFFF0000) | length

            infos[i] = (start, actual_length)

        return infos


class AudioChunksHandler(ChunksHandler):

    def clear(self):
        super().clear()
        self._header_stream = None
        self._header_base = None
        self._header_size = None

    def load(self, data_stream, header_stream,
             data_base=None, data_size=None,
             header_base=None, header_size=None):

        super().load(data_stream, data_base, data_size)
        data_size = self._data_size
        header_base, header_size = stream_fit(header_stream, header_base, header_size)
        assert header_size % 4 == 0

        chunk_count = header_size // 4
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
        data_stream = self._data_stream

        chunk_size = self.sizeof(index)
        self._seek(index)
        chunk = stream_read(data_stream, chunk_size)
        return chunk


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
        self._pics_size_index = None
        self._huffman_nodes = ()
        self.pics_size = ()

    def _seek(self, index, offsets=None):
        data_stream = self._data_stream
        data_base = self._data_base
        data_stream.seek(data_base + self.offsetof(index))

    def load(self, data_stream, header_stream, huffman_stream,
             partition_map, pics_size_index=0,
             data_base=None, data_size=None,
             header_base=None, header_size=None,
             huffman_offset=None, huffman_size=None):

        super().load(data_stream, data_base, data_size)
        data_size = self._data_size
        pics_size_index = int(pics_size_index)
        assert pics_size_index >= 0
        header_base, header_size = stream_fit(header_stream, header_base, header_size)
        huffman_offset, huffman_size = stream_fit(huffman_stream, huffman_offset, huffman_size)
        assert header_size % 3 == 0
        assert huffman_size >= 4 * HUFFMAN_NODE_COUNT

        chunk_count = header_size // 3
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

        huffman_nodes = list(stream_unpack_array('<HH', huffman_stream, HUFFMAN_NODE_COUNT, scalar=False))
        self._chunk_count = chunk_count
        self._chunk_offsets = chunk_offsets
        self._header_stream = header_stream
        self._header_base = header_base
        self._header_size = header_size
        self._huffman_stream = huffman_stream
        self._huffman_offset = huffman_offset
        self._huffman_size = huffman_size
        self._partition_map = partition_map
        self._pics_size_index = pics_size_index
        self._huffman_nodes = huffman_nodes
        self.pics_size = self._build_pics_size()
        return self

    def extract_chunk(self, index):
        chunk_count = self._chunk_count
        data_stream = self._data_stream
        huffman_nodes = self._huffman_nodes
        index = sequence_index(index, chunk_count)

        chunk = b''
        chunk_size = self.sizeof(index)
        if chunk_size:
            self._seek(index)
            compressed_size, expanded_size = self._read_sizes(index)
            chunk = stream_read(data_stream, compressed_size)
            chunk = huffman_expand(chunk, expanded_size, huffman_nodes)
        return chunk

    def _read_sizes(self, index):
        data_stream = self._data_stream
        partition_map = self._partition_map

        BLOCK_SIZE = (8 * 8) * 1
        MASKBLOCK_SIZE = (8 * 8) * 2
        compressed_size = self.sizeof(index)
        key = self.find_partition(partition_map, index)[0]

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
            compressed_size -= 4

        return compressed_size, expanded_size

    def _build_pics_size(self):
        partition_map = self._partition_map
        pics_size_index = self._pics_size_index

        count = partition_map['pics'][1]
        chunk = self.extract_chunk(pics_size_index)
        pics_size = list(stream_unpack_array('<HH', io.BytesIO(chunk), count, scalar=False))
        return pics_size

    @classmethod
    def find_partition(cls, partition_map, index):
        for key, value in partition_map.items():
            start, chunks_count = value
            if chunks_count and key.startswith('tile8'):
                chunks_count = 1
            if start <= index < start + chunks_count:
                return (key, start, chunks_count)
        raise KeyError(index)


class MapChunksHandler(ChunksHandler):

    def clear(self):
        super().clear()
        self._header_stream = None
        self._header_base = None
        self._header_size = None
        self._carmacized = True
        self._rlew_tag = None
        self.planes_count = 0

    def load(self, data_stream, header_stream,
             data_base=None, data_size=None,
             header_base=None, header_size=None,
             planes_count=3, carmacized=True):

        super().load(data_stream, data_base, data_size)
        data_size = self._data_size
        planes_count = int(planes_count)
        carmacized = bool(carmacized)
        assert planes_count > 0
        header_base, header_size = stream_fit(header_stream, header_base, header_size)

        rlew_tag = stream_unpack('<H', header_stream)[0]

        assert (header_size - 2) % 4 == 0
        chunk_count = (header_size - 2) // 4
        chunk_offsets = [None] * chunk_count
        for i in range(chunk_count):
            offset = stream_unpack('<L', header_stream)[0]
            if 0 < offset < 0xFFFFFFFF:
                chunk_offsets[i] = offset
        chunk_offsets.append(data_size)
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
        data_stream = self._data_stream
        carmacized = self._carmacized
        rlew_tag = self._rlew_tag
        planes_count = self.planes_count

        header = None
        planes = [None] * planes_count
        chunk_size = self.sizeof(index)
        if chunk_size:
            self._seek(index)
            header = TileMapHeader.from_stream(data_stream, planes_count)

            for i in range(planes_count):
                self._seek(i, header.plane_offsets)
                expanded_size = stream_unpack('<H', data_stream)[0]
                compressed_size = header.plane_sizes[i] - 2
                chunk = stream_read(data_stream, compressed_size)
                if carmacized:
                    chunk = carmack_expand(chunk, expanded_size)[2:]
                planes[i] = rlew_expand(chunk, rlew_tag)
        return (header, planes)
