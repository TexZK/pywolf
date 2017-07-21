import io
import struct

from PIL import Image

from .utils import (
    stream_write, stream_pack, stream_unpack, 
    stream_pack_array, stream_unpack_array,
    BinaryResource, ResourceManager
)


ALPHA_INDEX = 0xFF


def pixels_transpose(pixels, dimensions):
    width, height = dimensions
    yield from (pixels[x * width + y]
                for y in range(height)
                for x in range(width))


def pixels_linearize(pixels, dimensions):
    width, height = dimensions
    assert width % 4 == 0
    width_4 = width >> 2
    area_4 = width_4 * height
    yield from (pixels[(y * width_4 + (x >> 2)) + ((x & 3) * area_4)]
                for y in range(height)
                for x in range(width))


def sprite_expand(chunk, dimensions, alpha_index=0xFF):
    width, height = dimensions
    header = SpriteHeader.from_stream(io.BytesIO(chunk))
    expanded = bytearray([alpha_index]) * (width * height)

    unpack_from = struct.unpack_from
    word_size = struct.calcsize('<H')
    dword_size = struct.calcsize('<HH')

    x = header.left
    for offset in header.offsets:
        assert 0 <= offset < len(chunk)
        while True:
            y_endex = unpack_from('<H', chunk, offset)[0]
            offset += word_size
            if y_endex:
                y_base, y_start = unpack_from('<hH', chunk, offset)
                offset += dword_size
                y_endex >>= 1
                y_start >>= 1
                for y in range(y_start, y_endex):
                    expanded[x * width + y] = chunk[y_base + y]
            else:
                break
        x += 1
    return bytes(expanded)


def _rgbpalette_flatten(palette_colors):
    flat_palette = []
    for color in palette_colors:
        assert len(color) == 3
        flat_palette += color
    return flat_palette


def rgbpalette_split(flat_palette):
    assert len(flat_palette) % 3 == 0
    palette_colors = []
    for i in range(0, len(flat_palette), 3):
        palette_colors.append(list(flat_palette[i:(i + 3)]))
    return palette_colors


def make_8bit_image(dimensions, pixels, palette, alpha_index=None):
    image = Image.frombuffer('P', dimensions, pixels, 'raw', 'P', 0, 1)
    image.putpalette(palette)
    if alpha_index is not None:
        image.info['transparency'] = alpha_index
    return image


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


def write_targa_bgrx(stream, dimensions, depth_bits, pixels_bgrx):
    stream_pack(stream, '<BBBHHBHHHHBB',
                0, #  id_length
                0,  # colormap_type
                2,  # image_type: BGR(A)
                0,  # colormap_index
                0,  # colormap_length
                0,  # colormap_size
                0,  # x_origin
                0,  # y_origin
                dimensions[0], # width
                dimensions[1], # height
                depth_bits,  # pixel_size: 24 (BGR) | 32 (BGRA)
                0x00)  # attributes
    stream_write(stream, pixels_bgrx)


def build_color_image(dimensions, color):
    return Image.new('RGB', dimensions, color)


class Picture(object):

    def __init__(self, dimensions, pixels, palette, alpha_index=None):
        image = make_8bit_image(dimensions, pixels, palette, alpha_index)

        self.dimensions = dimensions
        self.image = image


class PictureManager(ResourceManager):

    def __init__(self, chunks_handler, palette_map, start=None, count=None):
        super().__init__(chunks_handler, start, count)
        self._palette_map = palette_map

    def _build_resource(self, index, chunk):
        chunks_handler = self._chunks_handler
        palette_map = self._palette_map
        start = self._start

        dimensions = chunks_handler.pics_dimensions[index]
        pixels = bytes(pixels_linearize(chunk, dimensions))
        palette = palette_map.get((start + index), palette_map[...])
        return Picture(dimensions, pixels, palette)


class Tile8Manager(ResourceManager):

    def __init__(self, chunks_handler, palette_map, start=None, count=None):
        super().__init__(chunks_handler, start, count)
        self._palette_map = palette_map

    def _get(self, index):
        chunk = self._chunks_handler[self._start]
        item = self._build_resource(index, chunk)
        return item

    def _build_resource(self, index, chunk):
        palette_map = self._palette_map
        start = self._start

        dimensions = (8, 8)
        area = dimensions[0] * dimensions[1]
        offset = index * area
        chunk = chunk[offset:(offset + area)]
        pixels = bytes(pixels_linearize(chunk, dimensions))
        palette = palette_map.get(start, palette_map[...])
        return Picture(dimensions, pixels, palette)


class Texture(object):

    def __init__(self, dimensions, pixels, palette, alpha_index=None):
        image = make_8bit_image(dimensions, pixels, palette, alpha_index)

        self.dimensions = dimensions
        self.image = image


class TextureManager(ResourceManager):

    def __init__(self, chunks_handler, palette, dimensions, 
                 start=None, count=None):
        super().__init__(chunks_handler, start, count)
        self._palette = palette
        self._dimensions = dimensions

    def _build_resource(self, index, chunk):
        palette = self._palette
        dimensions = self._dimensions

        pixels = bytes(pixels_transpose(chunk, dimensions))
        return Texture(dimensions, pixels, palette)


class SpriteHeader(BinaryResource):

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

    def to_stream(self, stream):
        stream_pack(stream, '<HH', self.left, self.right)
        stream_pack_array(stream, '<H', self.offsets)


class Sprite(object):

    def __init__(self, dimensions, pixels, palette, alpha_index=ALPHA_INDEX):
        image = make_8bit_image(dimensions, pixels, palette, alpha_index)

        self.dimensions = dimensions
        self.image = image
        self.alpha_index = alpha_index


class SpriteManager(ResourceManager):

    def __init__(self, chunks_handler, palette, dimensions, 
                 start=None, count=None, alpha_index=ALPHA_INDEX):
        super().__init__(chunks_handler, start, count)
        self._palette = palette
        self._dimensions = dimensions
        self._alpha_index = alpha_index

    def _build_resource(self, index, chunk):
        palette = self._palette
        dimensions = self._dimensions
        alpha_index = self._alpha_index

        pixels = sprite_expand(chunk, dimensions, alpha_index)
        pixels = bytes(pixels_transpose(pixels, dimensions))
        return Sprite(dimensions, pixels, palette, alpha_index)


class FontHeader(BinaryResource):

    CHARACTER_COUNT = 256

    def __init__(self, height, offsets, widths):
        assert 0 < height
        assert len(offsets) == type(self).CHARACTER_COUNT
        assert len(widths) == type(self).CHARACTER_COUNT

        self.height = height
        self.offsets = offsets
        self.widths = widths

    @classmethod
    def from_stream(cls, chunk_stream):
        height = stream_unpack('<H', chunk_stream)[0]
        offsets = list(stream_unpack_array('<H', chunk_stream, cls.CHARACTER_COUNT))
        widths = list(stream_unpack_array('<B', chunk_stream, cls.CHARACTER_COUNT))
        return cls(height, offsets, widths)

    def to_stream(self, chunk_stream):
        stream_pack(chunk_stream, '<H', self.height)
        stream_pack_array(chunk_stream, '<H', self.locations)
        stream_pack_array(chunk_stream, '<B', self.widths)


class Font(object):

    def __init__(self, height, widths, glyphs_pixels, palette, alpha_index=0xFF):
        count = len(glyphs_pixels)
        images = [None] * count
        for i in range(count):
            if widths[i]:
                images[i] = make_8bit_image((widths[i], height), glyphs_pixels[i], palette)

        self.height = height
        self.widths = widths
        self.images = images

    def __len__(self):
        return len(self.widths)

    def __getitem__(self, key):
        if isinstance(key, str):
            key = ord(key)
        return self.images[key]

    def __call__(self, text):
        get_image = self.images.__getitem__
        return (get_image(ord(c)) for c in text)

    def measure(self, line):
        get_width = self.widths.__getitem__
        return sum(get_width(ord(c)) for c in line)

    def wrap(self, text, max_width):
        widths = self.widths
        assert all(width <= max_width for width in widths)

        lines = []
        start, endex = 0, 0
        width = 0
        for c in text:
            delta = widths[ord(c)]
            if width + delta <= max_width and c not in '\n\v':
                width += delta
                endex += 1
            else:
                lines.append(text[start:endex])
                if c in '\n\v':
                    endex += 1
                    start = endex
                    width = 0
                else:
                    start = endex
                    width = delta
        return lines


class FontManager(ResourceManager):

    def __init__(self, chunks_handler, palette, start=None, count=None, alpha_index=0xFF):
        super().__init__(chunks_handler, start, count)
        self._palette = palette
        self._alpha_index = alpha_index

    def _build_resource(self, index, chunk):
        palette = self._palette
        alpha_index = self._alpha_index

        header = FontHeader.from_bytes(chunk)
        character_count = type(header).CHARACTER_COUNT
        height = header.height
        assert 0 < height
        glyphs_pixels = [None] * character_count

        for i in range(character_count):
            offset = header.offsets[i]
            width = header.widths[i]
            glyphs_pixels[i] = chunk[offset:(offset + (width * height))]

        return Font(height, header.widths, glyphs_pixels, palette, alpha_index)


class DOSScreen(object):

    def __init__(self, data):
        assert len(data) % struct.calcsize('<BB') == 0
        self.data = data

    def __len__(self):
        return len(self.data) // 2

    # TODO: convert to image


class DOSScreenManager(ResourceManager):

    def _build_resource(self, index, chunk):
        return DOSScreen(chunk)


class TextArtManager(ResourceManager):

    def _build_resource(self, index, chunk):
        return chunk.decode('ascii')
