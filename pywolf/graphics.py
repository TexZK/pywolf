import collections
import struct

from PIL import Image, ImageDraw, ImageFont
from pywolf.utils import (
    stream_write, stream_pack, stream_unpack,
    stream_pack_array, stream_unpack_array,
    BinaryResource, ResourceManager
)


ALPHA_INDEX = 0xFF

CP437_CHARS = (
    '\u0000', '\u263A', '\u263B', '\u2665', '\u2666', '\u2663', '\u2660', '\u2022',
    '\u25D8', '\u25CB', '\u25D9', '\u2642', '\u2640', '\u266A', '\u266B', '\u263C',
    '\u25BA', '\u25C4', '\u2195', '\u203C', '\u00B6', '\u00A7', '\u25AC', '\u21A8',
    '\u2191', '\u2193', '\u2192', '\u2190', '\u221F', '\u2194', '\u25B2', '\u25BC',
    '\u0020', '\u0021', '\u0022', '\u0023', '\u0024', '\u0025', '\u0026', '\u0027',
    '\u0028', '\u0029', '\u002A', '\u002B', '\u002C', '\u002D', '\u002E', '\u002F',
    '\u0030', '\u0031', '\u0032', '\u0033', '\u0034', '\u0035', '\u0036', '\u0037',
    '\u0038', '\u0039', '\u003A', '\u003B', '\u003C', '\u003D', '\u003E', '\u003F',
    '\u0040', '\u0041', '\u0042', '\u0043', '\u0044', '\u0045', '\u0046', '\u0047',
    '\u0048', '\u0049', '\u004A', '\u004B', '\u004C', '\u004D', '\u004E', '\u004F',
    '\u0050', '\u0051', '\u0052', '\u0053', '\u0054', '\u0055', '\u0056', '\u0057',
    '\u0058', '\u0059', '\u005A', '\u005B', '\u005C', '\u005D', '\u005E', '\u005F',
    '\u0060', '\u0061', '\u0062', '\u0063', '\u0064', '\u0065', '\u0066', '\u0067',
    '\u0068', '\u0069', '\u006A', '\u006B', '\u006C', '\u006D', '\u006E', '\u006F',
    '\u0070', '\u0071', '\u0072', '\u0073', '\u0074', '\u0075', '\u0076', '\u0077',
    '\u0078', '\u0079', '\u007A', '\u007B', '\u007C', '\u007D', '\u007E', '\u2302',
    '\u00C7', '\u00FC', '\u00E9', '\u00E2', '\u00E4', '\u00E0', '\u00E5', '\u00E7',
    '\u00EA', '\u00EB', '\u00E8', '\u00EF', '\u00EE', '\u00EC', '\u00C4', '\u00C5',
    '\u00C9', '\u00E6', '\u00C6', '\u00F4', '\u00F6', '\u00F2', '\u00FB', '\u00F9',
    '\u00FF', '\u00D6', '\u00DC', '\u00A2', '\u00A3', '\u00A5', '\u20A7', '\u0192',
    '\u00E1', '\u00ED', '\u00F3', '\u00FA', '\u00F1', '\u00D1', '\u00AA', '\u00BA',
    '\u00BF', '\u2310', '\u00AC', '\u00BD', '\u00BC', '\u00A1', '\u00AB', '\u00BB',
    '\u2591', '\u2592', '\u2593', '\u2502', '\u2524', '\u2561', '\u2562', '\u2556',
    '\u2555', '\u2563', '\u2551', '\u2557', '\u255D', '\u255C', '\u255B', '\u2510',
    '\u2514', '\u2534', '\u252C', '\u251C', '\u2500', '\u253C', '\u255E', '\u255F',
    '\u255A', '\u2554', '\u2569', '\u2566', '\u2560', '\u2550', '\u256C', '\u2567',
    '\u2568', '\u2564', '\u2565', '\u2559', '\u2558', '\u2552', '\u2553', '\u256B',
    '\u256A', '\u2518', '\u250C', '\u2588', '\u2584', '\u258C', '\u2590', '\u2580',
    '\u03B1', '\u00DF', '\u0393', '\u03C0', '\u03A3', '\u03C3', '\u00B5', '\u03C4',
    '\u03A6', '\u0398', '\u03A9', '\u03B4', '\u221E', '\u03C6', '\u03B5', '\u2229',
    '\u2261', '\u00B1', '\u2265', '\u2264', '\u2320', '\u2321', '\u00F7', '\u2248',
    '\u00B0', '\u2219', '\u00B7', '\u221A', '\u207F', '\u00B2', '\u25A0', '\u00A0',
)


def unicode_to_cp437(unicode_text):
    cp437_bytes = bytes(CP437_CHARS.index(c) for c in unicode_text)
    return cp437_bytes


def cp437_to_unicode(cp437_bytes):
    unicode_text = ''.join(CP437_CHARS[c] for c in cp437_bytes)
    return unicode_text


def text_measure(text, widths):
    width = sum(widths[c] for c in text)
    return width


def text_wrap(text, max_width, widths):
    lines = []
    start, endex = 0, 0
    width = 0
    for c in text:
        delta = widths[c]
        assert delta <= max_width
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


def pixels_transpose(pixels, size):
    width, height = size
    yield from (pixels[x * width + y]
                for y in range(height)
                for x in range(width))


def pixels_linearize(pixels, size):
    width, height = size
    assert width % 4 == 0
    width_4 = width >> 2
    area_4 = width_4 * height
    yield from (pixels[(y * width_4 + (x >> 2)) + ((x & 3) * area_4)]
                for y in range(height)
                for x in range(width))


def sprite_expand(chunk, size, alpha_index=0xFF):
    width, height = size
    header = SpriteHeader.from_bytes(chunk)
    expanded = bytearray([alpha_index]) * (width * height)

    unpack_from = struct.unpack_from

    x = header.left
    for offset in header.offsets:
        assert 0 <= offset < len(chunk)
        while True:
            y_endex = unpack_from('<H', chunk, offset)[0]
            offset += 2
            if y_endex:
                y_base, y_start = unpack_from('<hH', chunk, offset)
                offset += 4
                y_endex >>= 1
                y_start >>= 1
                for y in range(y_start, y_endex):
                    expanded[x * width + y] = chunk[y_base + y]
            else:
                break
        x += 1
    return bytes(expanded)


def rgbpalette_flatten(palette_colors):
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


def make_8bit_image(size, pixels, palette, alpha_index=None):
    image = Image.frombuffer('P', size, pixels, 'raw', 'P', 0, 1)
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


def write_targa_bgrx(stream, size, depth_bits, pixels_bgrx):
    stream_pack(stream, '<BBBHHBHHHHBB',
                0,  #  id_length
                0,  # colormap_type
                2,  # image_type: BGR(A)
                0,  # colormap_index
                0,  # colormap_length
                0,  # colormap_size
                0,  # x_origin
                0,  # y_origin
                size[0],  # width
                size[1],  # height
                depth_bits,  # pixel_size: 24 (BGR) | 32 (BGRA)
                0x00)  # attributes
    stream_write(stream, pixels_bgrx)


def build_color_image(size, color):
    return Image.new('RGB', size, color)


WINFNT_HEADER_FMT = (
    ('dfVersion', '<H'),
    ('dfSize', '<L'),
    ('dfCopyright', '<60s'),
    ('dfType', '<H'),
    ('dfPoints', '<H'),
    ('dfVertRes', '<H'),
    ('dfHorizRes', '<H'),
    ('dfAscent', '<H'),
    ('dfInternalLeading', '<H'),
    ('dfExternalLeading', '<H'),
    ('dfdfItalic', '<B'),
    ('dfUnderline', '<B'),
    ('dfStrikeOut', '<B'),
    ('dfWeight', '<H'),
    ('dfCharSet', '<B'),
    ('dfPixWidth', '<H'),
    ('dfPixHeight', '<H'),
    ('dfPitchAndFamily', '<B'),
    ('dfAvgWidth', '<H'),
    ('dfMaxWidth', '<H'),
    ('dfFirstChar', '<B'),
    ('dfLastChar', '<B'),
    ('dfDefaultChar', '<B'),
    ('dfBreakChar', '<B'),
    ('dfWidthBytes', '<H'),
    ('dfDevice', '<L'),
    ('dfFace', '<L'),
    ('dfBitsPointer', '<L'),
    ('dfBitsOffset', '<L'),
    ('dfReserved', '<B'),
)

BYTE_MASK_EXPANDED = tuple(bytes([1 if m & (1 << (7 - b)) else 0 for b in range(8)]) for m in range(256))
BYTE_MASK_TO_BYTES = tuple(bytes([0xFF if m & (1 << (7 - b)) else 0x00 for b in range(8)]) for m in range(256))


def winfnt_read(stream):
    start = stream.tell()
    fields = collections.OrderedDict((name, stream_unpack(fmt, stream)[0])
                                     for name, fmt in WINFNT_HEADER_FMT)
    fields['dfCopyright'] = fields['dfCopyright'].rstrip(b'\0')
    count = fields['dfLastChar'] - fields['dfFirstChar'] + 2
    fields['dfCharTable'] = [stream_unpack('<HH', stream) for _ in range(count)]
    height = fields['dfPixHeight']

    palette = (0x00, 0x00, 0x00, 0xFF, 0xFF, 0xFF)
    images = []

    for width, offset in fields['dfCharTable']:
        stream.seek(start + offset)
        lines = [[] for y in range(height)]
        padded_width = (width + 7) & 0xFFF8

        for _ in range(padded_width >> 3):
            for y in range(height):
                mask = stream.read(1)
                lines[y].append(mask)

        bitmap = b''.join(b''.join(line) for line in lines)
        pixels = b''.join(BYTE_MASK_EXPANDED[mask] for mask in bitmap)
        image = make_8bit_image((padded_width, height), pixels, palette)
        image = image.crop((0, 0, width, height))
        images.append(image)

    return fields, images


ANSI_PALETTE = (
    0x00, 0x00, 0x00,  # Black
    0x00, 0x00, 0xAA,  # Blue
    0x00, 0xAA, 0x00,  # Green
    0x00, 0xAA, 0xAA,  # Cyan
    0xAA, 0x00, 0x00,  # Red
    0xAA, 0x00, 0xAA,  # Magenta
    0xAA, 0x55, 0x00,  # Brown
    0xAA, 0xAA, 0xAA,  # Light Gray

    0x55, 0x55, 0x55,  # Dark Gray
    0x55, 0x55, 0xFF,  # Light Blue
    0x55, 0xFF, 0x55,  # Light Green
    0x55, 0xFF, 0xFF,  # Light Cyan
    0xFF, 0x55, 0x55,  # Light Red
    0xFF, 0x55, 0xFF,  # Light Magenta
    0xFF, 0xFF, 0x55,  # Yellow
    0xFF, 0xFF, 0xFF,  # White
)


def render_ansi_line(ansi_image, cursor, font, text, attrs, special=None, font_size=None):
    draw = ImageDraw.Draw(ansi_image)
    if font_size is None:
        font_width, font_height = (9, 16)  # TODO: retrieve from font
    else:
        font_width, font_height = font_size
    image_width, image_height = ansi_image.size
    text_width = image_width // font_width
    text_height = image_height // font_height
    cursor_x, cursor_y = cursor
    left = cursor[0] * font_width
    top = cursor[1] * font_height

    for char, attr in zip(text, attrs):
        bg = (attr >> 4) & (0x0F if special is 'fullcolor' else 0x07)

        box = (left, top, left + font_width - 1, top + font_height - 1)
        draw.rectangle(box, fill=bg)

        fg = bg if special is 'hide' and attr & 0x80 else attr & 0x0F
        draw.text((left, top), char, font=font, fill=fg)

        left += font_width
        cursor_x += 1
        if cursor_x >= text_width:
            cursor_x = 0
            cursor_y += 1
            left = 0
            top += font_height
        if cursor_y >= text_height:
            break


def create_ansi_image(text_size, font_size, color=0, palette=ANSI_PALETTE):
    size = (text_size[0] * font_size[0], text_size[1] * font_size[1])
    image = Image.new('P', size, color=color)
    image.putpalette(palette)
    return image


class Picture(object):

    def __init__(self, size, pixels, palette, alpha_index=None):
        image = make_8bit_image(size, pixels, palette, alpha_index)

        self.size = size
        self.image = image


class PictureManager(ResourceManager):

    def __init__(self, chunks_handler, palette_map, start=None, count=None):
        super().__init__(chunks_handler, start, count)
        self._palette_map = palette_map

    def _load_resource(self, index, chunk):
        chunks_handler = self._chunks_handler
        palette_map = self._palette_map
        start = self._start

        size = chunks_handler.pics_size[index]
        pixels = bytes(pixels_linearize(chunk, size))
        palette = palette_map.get((start + index), palette_map[...])
        return Picture(size, pixels, palette)


class Tile8Manager(ResourceManager):

    def __init__(self, chunks_handler, palette_map, start=None, count=None):
        super().__init__(chunks_handler, start, count)
        self._palette_map = palette_map

    def _get(self, index):
        chunk = self._chunks_handler[self._start]
        item = self._load_resource(index, chunk)
        return item

    def _load_resource(self, index, chunk):
        palette_map = self._palette_map
        start = self._start

        size = (8, 8)
        area = size[0] * size[1]
        offset = index * area
        chunk = chunk[offset:(offset + area)]
        pixels = bytes(pixels_linearize(chunk, size))
        palette = palette_map.get(start, palette_map[...])
        return Picture(size, pixels, palette)


class Texture(object):

    def __init__(self, size, pixels, palette, alpha_index=None):
        image = make_8bit_image(size, pixels, palette, alpha_index)

        self.size = size
        self.image = image


class TextureManager(ResourceManager):

    def __init__(self, chunks_handler, palette, size,
                 start=None, count=None):
        super().__init__(chunks_handler, start, count)
        self._palette = palette
        self._size = size

    def _load_resource(self, index, chunk):
        palette = self._palette
        size = self._size

        pixels = bytes(pixels_transpose(chunk, size))
        return Texture(size, pixels, palette)


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

    def __init__(self, size, pixels, palette, alpha_index=ALPHA_INDEX):
        image = make_8bit_image(size, pixels, palette, alpha_index)

        self.size = size
        self.image = image
        self.alpha_index = alpha_index


class SpriteManager(ResourceManager):

    def __init__(self, chunks_handler, palette, size,
                 start=None, count=None, alpha_index=ALPHA_INDEX):
        super().__init__(chunks_handler, start, count)
        self._palette = palette
        self._size = size
        self._alpha_index = alpha_index

    def _load_resource(self, index, chunk):
        palette = self._palette
        size = self._size
        alpha_index = self._alpha_index

        pixels = sprite_expand(chunk, size, alpha_index)
        pixels = bytes(pixels_transpose(pixels, size))
        return Sprite(size, pixels, palette, alpha_index)


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

    def __call__(self, text_bytes):
        get_image = self.images.__getitem__
        yield from (get_image(ord(c)) for c in text_bytes)

    def measure(self, text):
        return text_measure(text, self.widths)

    def wrap(self, text, max_width):
        return text_wrap(text, max_width, self.widths)


class FontManager(ResourceManager):

    def __init__(self, chunks_handler, palette, start=None, count=None, alpha_index=0xFF):
        super().__init__(chunks_handler, start, count)
        self._palette = palette
        self._alpha_index = alpha_index

    def _load_resource(self, index, chunk):
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

    def __init__(self, data, font, text_size, font_size=None):
        assert len(data) % 2 == 0
        self.chars = bytes(data[i] for i in range(9 + 0, len(data), 2))
        self.attrs = bytes(data[i] for i in range(9 + 1, len(data), 2))

        image0 = create_ansi_image(text_size, font_size)
        text = cp437_to_unicode(self.chars)
        render_ansi_line(image0, (0, 0), font, text, self.attrs, font_size=font_size)

        if any(attr & 0x80 for attr in self.attrs):
            image1 = create_ansi_image(text_size, font_size)
            text = cp437_to_unicode(self.chars)
            render_ansi_line(image1, (0, 0), font, text, self.attrs, font_size=font_size, special='hide')
            self.images = [image0, image1]
        else:
            self.images = [image0]

    def __len__(self):
        return len(self.chars)


class DOSScreenManager(ResourceManager):

    def __init__(self, chunks_handler, font, start=None, count=None, size=(80, 25), font_size=(9, 16)):
        super().__init__(chunks_handler, start, count)
        self._font = font
        self._size = size
        self._font_size = font_size

    def _load_resource(self, index, chunk):
        return DOSScreen(chunk, self._font, self._size, self._font_size)


class TextArtManager(ResourceManager):

    def _load_resource(self, index, chunk):
        return chunk.decode('ascii')
