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

import io
import struct
from typing import Any
from typing import ByteString
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

from PIL import Image
from PIL import ImageDraw
from PIL import ImageFont

from .archives import GraphicsArchiveReader
from .archives import ResourceLibrary
from .archives import VswapArchiveReader
from .base import Cache
from .base import Char
from .base import Chunk
from .base import Codec
from .base import ColorIndex
from .base import ColorRGB
from .base import Coord
from .base import Coords
from .base import Index
from .base import Offset
from .base import PaletteFlat
from .base import PaletteRGB
from .base import PixelsFlat
# from .utils import stream_pack
# from .utils import stream_unpack
# from .utils import stream_unpack_array
from .utils import ResourceManager


TextArt = str


ALPHA: ColorIndex = 0xFF

CP437_INDEX_TO_CHAR: List[Char] = list(bytes(range(256)).decode('cp437'))
CP437_CHAR_TO_INDEX: Mapping[Char, int] = {c: i for i, c in enumerate(CP437_INDEX_TO_CHAR)}

ANSI_SCREEN_SIZE: Coords = (80, 25)


def text_measure(
    text: str,
    widths: Sequence[Coord],
    char_to_index: Mapping[Char, int] = CP437_CHAR_TO_INDEX,
) -> Coord:

    return sum(widths[char_to_index[c]] for c in text)


def text_wrap(
    text: str,
    max_width: Coord,
    widths: Sequence[Coord],
    char_to_index: Mapping[Char, int] = CP437_CHAR_TO_INDEX,
) -> List[str]:

    lines: List[str] = []
    start = 0
    endex = 0
    width = 0

    for c in text:
        delta = widths[char_to_index[c]]
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


def pixels_transpose(
    pixels: Sequence[ColorIndex],
    size: Coords,
) -> Iterator[ColorIndex]:

    width, height = size

    for y in range(height):
        for x in range(width):
            yield pixels[x * width + y]


def pixels_linearize(
    pixels: Sequence[ColorIndex],
    size: Coords,
) -> Iterator[ColorIndex]:

    width, height = size
    if width % 4:
        raise ValueError(f'width must be divisible by 4: {width}')
    width_4 = width >> 2
    area_4 = width_4 * height

    for y in range(height):
        for x in range(width):
            yield pixels[(y * width_4 + (x >> 2)) + ((x & 3) * area_4)]


def sprite_expand(
    chunk: ByteString,
    size: Coords,
    alpha: ColorIndex = ALPHA,
) -> bytearray:

    width, height = size
    if width < 1:
        raise ValueError(f'invalid width: {width}')
    if height < 1:
        raise ValueError(f'invalid height: {height}')

    header, _ = SpriteHeader.from_bytes(chunk)
    expanded = bytearray().ljust((width * height), bytes([alpha]))
    unpack_from = struct.unpack_from
    x = header.left

    for offset in header.offsets:
        while True:
            y_endex, = unpack_from('<H', chunk, offset)
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

    return expanded


def rgbpalette_flatten(palette_colors: PaletteRGB) -> PaletteFlat:
    flat_palette: PaletteFlat = []
    append = flat_palette.append

    for color in palette_colors:
        r, g, b = color
        append(r)
        append(g)
        append(b)

    return flat_palette


def rgbpalette_split(flat_palette: PaletteFlat) -> PaletteRGB:
    if len(flat_palette) % 3:
        raise ValueError(f'flat palette length must be divisible by 3: {len(flat_palette)}')
    palette_colors: List[ColorRGB] = []

    for i in range(0, len(flat_palette), 3):
        r = flat_palette[i]
        g = flat_palette[i + 1]
        b = flat_palette[i + 2]
        rgb = (r, g, b)
        palette_colors.append(rgb)

    return palette_colors


def make_8bit_image(
    size: Coords,
    pixels: Sequence[ColorIndex],
    palette_flat: PaletteFlat,
    alpha: Optional[ColorIndex] = None,
) -> Image:

    image = Image.frombuffer('P', size, pixels, 'raw', 'P', 0, 1)
    image.putpalette(palette_flat)
    if alpha is not None:
        image.info['transparency'] = alpha
    return image


def jascpal_read(stream: io.TextIOBase) -> PaletteRGB:
    line = stream.readline().strip()
    if line != 'JASC-PAL':
        raise ValueError('expected "JASC-PAL"')

    line = stream.readline().strip()
    if line != '0100':
        raise ValueError('expected "0100"')

    line = stream.readline().strip()
    count = int(line)
    if count <= 0:
        raise ValueError(f'count not positive: {count}')

    palette: List[ColorRGB] = []
    for i in range(count):
        r, g, b = stream.readline().split()
        r = int(r)
        g = int(g)
        b = int(b)
        rgb = (r, g, b)
        if not ((0x00 <= r <= 0xFF) and (0x00 <= g <= 0xFF) and (0x00 <= b <= 0xFF)):
            raise ValueError(f'invalid RGB color: {rgb}')
        palette.append(rgb)
    return palette


def jascpal_write(stream: io.TextIOBase, palette: PaletteRGB) -> None:
    stream.write('JASC-PAL\n')
    stream.write('0100\n')
    stream.write('{:d}\n'.format(len(palette)))
    for rgb in palette:
        r, g, b = rgb
        if not ((0x00 <= r <= 0xFF) and (0x00 <= g <= 0xFF) and (0x00 <= b <= 0xFF)):
            raise ValueError(f'invalid RGB color: {rgb}')
        stream.write(f'{r:d} {g:d} {b:d}\n')


def write_targa_bgrx(
    stream: io.BufferedReader,
    size: Coords,
    depth_bits: int,
    pixels_bgrx: Sequence[ColorIndex],
) -> None:

    width, height = size
    if width < 0 or height < 0:
        raise ValueError(f'invalid size: {size}')
    if depth_bits != 24 or depth_bits != 32:
        raise ValueError(f'depth bits must be either 24 or 32: {depth_bits}')
    pixel_data_expected = width * height * (depth_bits // 8)
    if len(pixels_bgrx) < pixel_data_expected:
        raise ValueError(f'not enough pixel data: '
                         f'actual={len(pixels_bgrx)} < expected={pixel_data_expected}')

    header_chunk = struct.pack(
        '<BBBHHBHHHHBB',
        0,  # id_length
        0,  # colormap_type
        2,  # image_type: BGR(A)
        0,  # colormap_index
        0,  # colormap_length
        0,  # colormap_size
        0,  # x_origin
        0,  # y_origin
        width,  # width
        height,  # height
        depth_bits,  # pixel_size: 24 (BGR) | 32 (BGRA)
        0x00,  # attributes
    )
    stream.write(header_chunk)
    stream.write(pixels_bgrx)


def build_color_image(size: Coords, rgb: ColorRGB) -> Image:
    return Image.new('RGB', size, rgb)


WINFNT_HEADER_FMT: Mapping[str, str] = {
    'dfVersion':         '<H',
    'dfSize':            '<L',
    'dfCopyright':       '<60s',
    'dfType':            '<H',
    'dfPoints':          '<H',
    'dfVertRes':         '<H',
    'dfHorizRes':        '<H',
    'dfAscent':          '<H',
    'dfInternalLeading': '<H',
    'dfExternalLeading': '<H',
    'dfdfItalic':        '<B',
    'dfUnderline':       '<B',
    'dfStrikeOut':       '<B',
    'dfWeight':          '<H',
    'dfCharSet':         '<B',
    'dfPixWidth':        '<H',
    'dfPixHeight':       '<H',
    'dfPitchAndFamily':  '<B',
    'dfAvgWidth':        '<H',
    'dfMaxWidth':        '<H',
    'dfFirstChar':       '<B',
    'dfLastChar':        '<B',
    'dfDefaultChar':     '<B',
    'dfBreakChar':       '<B',
    'dfWidthBytes':      '<H',
    'dfDevice':          '<L',
    'dfFace':            '<L',
    'dfBitsPointer':     '<L',
    'dfBitsOffset':      '<L',
    'dfReserved':        '<B',
}

BYTE_MASK_EXPANDED: List[bytes] = [
    bytes([1 if m & (1 << (7 - b)) else 0
           for b in range(8)])
    for m in range(256)
]

BYTE_MASK_TO_BYTES: List[bytes] = [
    bytes([0xFF if m & (1 << (7 - b)) else 0x00
           for b in range(8)])
    for m in range(256)
]


def winfnt_read(stream: io.BufferedReader) -> Tuple[Dict[str, Any], List[Image]]:
    start = stream.tell()
    fields = {name: struct.unpack(fmt, stream.read(struct.calcsize(fmt)))[0]
              for name, fmt in WINFNT_HEADER_FMT.items()}
    fields['dfCopyright'] = fields['dfCopyright'].rstrip(b'\0')
    count = fields['dfLastChar'] - fields['dfFirstChar'] + 2
    fields['dfCharTable'] = [struct.unpack('<HH', stream.read(4)) for _ in range(count)]
    height = fields['dfPixHeight']

    palette_flat: PaletteFlat = [
        0x00, 0x00, 0x00,
        0xFF, 0xFF, 0xFF,
    ]
    images: List[Image] = []

    for width, offset in fields['dfCharTable']:
        stream.seek(start + offset)
        lines = [[] for _ in range(height)]
        padded_width = (width + 7) & 0xFFF8

        for _ in range(padded_width >> 3):
            for y in range(height):
                mask = stream.read(1)
                lines[y].append(mask)

        bitmap_flat = b''.join(b''.join(line) for line in lines)
        pixels_flat = b''.join(BYTE_MASK_EXPANDED[mask] for mask in bitmap_flat)
        size = (padded_width, height)
        image = make_8bit_image(size, pixels_flat, palette_flat)
        image = image.crop((0, 0, width, height))
        images.append(image)

    return fields, images


ANSI_PALETTE_FLAT: PaletteFlat = [
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
]


def render_ansi_line(
    image: Image,
    font_impl: ImageFont,
    cursor: Coords,
    text: str,
    attrs: Sequence[int],
    special: Optional[str] = None,
    font_size: Optional[Coords] = None,
) -> None:

    if len(text) != len(attrs):
        raise ValueError('text and attrs must have the same length')
    if font_size is None:
        font_size = font_impl.getsize('\u2588')  # full block
    font_width, font_height = font_size
    image_width, image_height = image.size
    text_width = image_width // font_width
    text_height = image_height // font_height
    cursor_x, cursor_y = cursor
    left = cursor_x * font_width
    top = cursor_y * font_height
    bg_mask = 0x0F if special == 'fullcolor' else 0x07
    context = ImageDraw.Draw(image)

    for char, attr in zip(text, attrs):
        if left > -font_width and top > -font_height:
            bg = (attr >> 4) & bg_mask
            box = (left, top, (left + font_width - 1), (top + font_height - 1))
            context.rectangle(box, fill=bg)
            fg = bg if special == 'hide' and attr & 0x80 else attr & 0x0F
            context.text((left, top), char, font=font_impl, fill=fg)

        left += font_width
        cursor_x += 1
        if cursor_x >= text_width:
            cursor_x = 0
            cursor_y += 1
            left = 0
            top += font_height
        if cursor_y >= text_height:
            break


def create_ansi_image(
    text_size: Coords,
    font_size: Coords,
    color: ColorIndex = 0,
    palette_flat: Optional[PaletteFlat] = None,
) -> Image:

    text_width, text_height = text_size
    if text_width < 1 or text_height < 1:
        raise ValueError(f'invalid text size: {text_size}')
    font_width, font_height = font_size
    if font_width < 1 or font_height < 1:
        raise ValueError(f'invalid font size: {font_size}')
    if palette_flat is None:
        palette_flat = ANSI_PALETTE_FLAT

    size = ((text_width * font_width), (text_height * font_height))
    image = Image.new('P', size, color=color)
    image.putpalette(palette_flat)
    return image


class Picture:

    def __init__(
        self,
        size: Coords,
        pixels_flat: PixelsFlat,
        palette_flat: PaletteFlat,
        alpha: Optional[ColorIndex] = None,
    ):
        image = make_8bit_image(size, pixels_flat, palette_flat, alpha=alpha)
        self.image: Image = image
        self.size: Coords = size


class PictureManager(ResourceManager):

    def __init__(self, chunks_handler, palette_map, start=None, count=None):
        super().__init__(chunks_handler, start, count)
        self._palette_map = palette_map

    def _load_resource(self, index, chunk):
        chunks_handler = self._chunks_handler
        palette_map = self._palette_map
        start = self._start

        size = chunks_handler._pics_size[index]
        pixels = bytes(pixels_linearize(chunk, size))
        palette = palette_map.get((start + index), palette_map[...])
        return Picture(size, pixels, palette)


class PictureLibrary(ResourceLibrary[Index, Picture]):

    def __init__(
        self,
        graphics_archive: GraphicsArchiveReader,
        palette_map: Mapping[Optional[Index], PaletteFlat],
        resource_cache: Optional[Cache[Index, Picture]] = None,
        start: Optional[Index] = None,
        count: Optional[Index] = None,
    ):
        super().__init__(
            graphics_archive,
            resource_cache=resource_cache,
            start=start,
            count=count,
        )
        self._palette_map: Mapping[Optional[Index], PaletteFlat] = palette_map

    def _get_resource(self, index: Index, chunk: Chunk) -> Picture:
        graphics_archive = _cast(GraphicsArchiveReader, self._archive)
        size = graphics_archive.pics_size[index]
        pixels = bytes(pixels_linearize(chunk, size))
        palette_map = self._palette_map
        palette = palette_map.get(self._start + index, palette_map[None])
        instance = Picture(size, pixels, palette)
        return instance


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
        pixels_flat = bytes(pixels_linearize(chunk, size))
        palette_flat = palette_map.get(start, palette_map[...])
        return Picture(size, pixels_flat, palette_flat)


class Tile8Library(ResourceLibrary[Index, Picture]):

    def __init__(
        self,
        graphics_archive: GraphicsArchiveReader,
        palette_map: Mapping[Optional[Index], PaletteFlat],
        resource_cache: Optional[Cache[Index, Picture]] = None,
        start: Optional[Index] = None,
        count: Optional[Index] = None,
    ):
        super().__init__(
            graphics_archive,
            resource_cache=resource_cache,
            start=start,
            count=count,
        )
        self._palette_map: Mapping[Optional[Index], PaletteFlat] = palette_map

    def _get_resource(self, index: Index, chunk: Chunk) -> Picture:
        size = (8, 8)
        area = 8 * 8
        offset = index * area
        chunk = chunk[offset:(offset + area)]
        pixels_flat = bytes(pixels_linearize(chunk, size))
        palette_map = self._palette_map
        palette_flat = palette_map.get(self._start, palette_map[None])
        instance = Picture(size, pixels_flat, palette_flat)
        return instance


class Texture:

    def __init__(
        self,
        size: Coords,
        pixels_flat: PixelsFlat,
        palette_flat: PaletteFlat,
        alpha: Optional[ColorIndex] = None,
    ):
        image = make_8bit_image(size, pixels_flat, palette_flat, alpha=alpha)
        self.image: Image = image
        self.size: Coords = size


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


class TextureLibrary(ResourceLibrary[Index, Texture]):

    def __init__(
        self,
        vswap_archive: VswapArchiveReader,
        palette_flat: PaletteFlat,
        size: Coords,
        resource_cache: Optional[Cache[Index, Texture]] = None,
        start: Optional[Index] = None,
        count: Optional[Index] = None,
    ):
        super().__init__(
            vswap_archive,
            resource_cache=resource_cache,
            start=start,
            count=count,
        )
        self._palette_flat: PaletteFlat = palette_flat
        self._size: Coords = size

    def _get_resource(self, index: Index, chunk: Chunk) -> Texture:
        size = self._size
        pixels_flat = bytes(pixels_transpose(chunk, size))
        instance = Texture(size, pixels_flat, self._palette_flat)
        return instance


class SpriteHeader(Codec):

    def __init__(
        self,
        left: Coord,
        right: Coord,
        offsets: Sequence[Coord],
    ):
        if left < 0:
            raise ValueError('negative left')
        if right < 0:
            raise ValueError('negative right')
        width = right - left + 1
        if len(offsets) != width:
            raise ValueError(f'wrong offsets count: actual={len(offsets)} != expected={width}')

        self.left: Coord = left
        self.right: Coord = right
        self.offsets: Sequence[Coord] = offsets

    @classmethod
    def calcsize_stateless(cls) -> Offset:
        raise NotImplementedError('unavailable')

    def to_bytes(self) -> bytes:
        chunk = struct.pack(f'<HH{len(self.offsets)}H',
                            self.left, self.right, *self.offsets)
        return chunk

    @classmethod
    def from_bytes(cls, buffer: ByteString, offset: Offset = 0) -> Tuple[Self, Offset]:
        offset = int(offset)
        left, right = struct.unpack_from('<HH', buffer, offset)
        offset += 2

        width = right - left + 1
        offsets = list(struct.unpack_from(f'<{width}H', buffer, offset))
        offset += width * 2

        instance = cls(left, right, offsets)
        return instance, offset

    @classmethod
    def from_stream(cls, stream: io.BufferedReader) -> Self:
        buffer = stream.read(4)
        left, right = struct.unpack('<HH', buffer)
        width = right - left + 1
        buffer += stream.read(width * 2)
        instance = cls.from_bytes(buffer)
        return instance


class Sprite:

    def __init__(
        self,
        size: Coords,
        pixels: PixelsFlat,
        palette: PaletteFlat,
        alpha: ColorIndex = ALPHA,
    ):
        image = make_8bit_image(size, pixels, palette, alpha=alpha)
        self.image: Image = image
        self.size: Coords = size
        self.alpha: ColorIndex = alpha


class SpriteManager(ResourceManager):

    def __init__(self, chunks_handler, palette, size,
                 start=None, count=None, alpha=ALPHA):
        super().__init__(chunks_handler, start, count)
        self._palette = palette
        self._size = size
        self._alpha = alpha

    def _load_resource(self, index, chunk):
        palette = self._palette
        size = self._size
        alpha = self._alpha

        pixels = sprite_expand(chunk, size, alpha)
        pixels = bytes(pixels_transpose(pixels, size))
        return Sprite(size, pixels, palette, alpha)


class SpriteLibrary(ResourceLibrary[Index, Sprite]):

    def __init__(
        self,
        vswap_archive: VswapArchiveReader,
        palette_flat: PaletteFlat,
        size: Coords,
        resource_cache: Optional[Cache[Index, Sprite]] = None,
        start: Optional[Index] = None,
        count: Optional[Index] = None,
        alpha: ColorIndex = ALPHA,
    ):
        super().__init__(
            vswap_archive,
            resource_cache=resource_cache,
            start=start,
            count=count,
        )
        self._palette_flat: PaletteFlat = palette_flat
        self._size: Coords = size
        self._alpha: ColorIndex = alpha

    def _get_resource(self, index: Index, chunk: Chunk) -> Sprite:
        del index
        size = self._size
        alpha = self._alpha
        pixels_flat = sprite_expand(chunk, size, alpha)
        pixels_flat = bytes(pixels_transpose(pixels_flat, size))
        instance = Sprite(size, pixels_flat, self._palette_flat, alpha)
        return instance


class FontHeader(Codec):
    CHARACTER_COUNT: int = 256

    def __init__(
        self,
        height: Coord,
        offsets: Sequence[Coord],
        widths: Sequence[Coord],
    ):
        if height < 1:
            raise ValueError(f'invalid height: {height}')
        if len(offsets) != self.CHARACTER_COUNT:
            raise ValueError('wrong offsets count')
        if len(widths) != self.CHARACTER_COUNT:
            raise ValueError('wrong widths count')

        self.height: Coord = height
        self.offsets: Sequence[Coord] = offsets
        self.widths: Sequence[Coord] = widths

    @classmethod
    def calcsize_stateless(cls) -> Offset:
        return 2 + ((2 * 2) * cls.CHARACTER_COUNT)

    def to_bytes(self) -> bytes:
        chunk = struct.pack(f'<H{len(self.offsets)}H{len(self.widths)}B',
                            self.height, *self.offsets, *self.widths)
        return chunk

    @classmethod
    def from_bytes(cls, buffer: ByteString, offset: Offset = 0) -> Tuple[Self, Offset]:
        offset = int(offset)
        height, = struct.unpack_from('<H', buffer, offset)
        offset += 2

        offsets = list(struct.unpack_from(f'<{cls.CHARACTER_COUNT}H', buffer, offset))
        offset += cls.CHARACTER_COUNT * 2

        widths = list(struct.unpack_from(f'={cls.CHARACTER_COUNT}B', buffer, offset))
        offset += cls.CHARACTER_COUNT

        instance = cls(height, offsets, widths)
        return instance, offset


class Font:

    def __init__(
        self,
        height: Coord,
        widths: List[Coord],
        glyphs_pixels_flat: Sequence[PixelsFlat],
        palette: PaletteFlat,
    ):
        count = len(glyphs_pixels_flat)
        images: Optional[List[Image]] = [None] * count

        for glyph_index in range(count):
            width = widths[glyph_index]
            if width < 0:
                raise ValueError('negative width')

            if width:
                size = (width, height)
                pixels_flat = glyphs_pixels_flat[glyph_index]
                image = make_8bit_image(size, pixels_flat, palette)
                images[glyph_index] = image

        self.height: Coord = height
        self.widths: List[Coord] = widths
        self.images: List[Optional[Image]] = images

    def __len__(self) -> int:
        return len(self.widths)

    def __getitem__(self, key: Union[Index, Char]) -> Image:
        if isinstance(key, str):
            key = ord(key)
        return self.images[key]

    def __call__(self, text_bytes: ByteString) -> Iterator[Image]:
        images = self.images
        for glyph_index in text_bytes:
            yield from images[glyph_index]


class FontManager(ResourceManager):

    def __init__(self, chunks_handler, palette, start=None, count=None, alpha=0xFF):
        super().__init__(chunks_handler, start, count)
        self._palette = palette
        self._alpha = alpha

    def _load_resource(self, index, chunk):
        palette = self._palette
        alpha = self._alpha

        header = FontHeader.from_bytes(chunk)
        glyph_count = header.CHARACTER_COUNT
        height = header.height
        glyphs_pixels = [None] * glyph_count

        for glyph_index in range(glyph_count):
            offset = header.offsets[glyph_index]
            width = header.widths[glyph_index]
            glyphs_pixels[glyph_index] = chunk[offset:(offset + (width * height))]

        return Font(height, header.widths, glyphs_pixels, palette, alpha=alpha)


class FontLibrary(ResourceLibrary[Index, Font]):

    def __init__(
        self,
        graphics_archive: GraphicsArchiveReader,
        palette_flat: PaletteFlat,
        resource_cache: Optional[Cache[Index, Font]] = None,
        start: Optional[Index] = None,
        count: Optional[Index] = None,
    ):
        super().__init__(
            graphics_archive,
            resource_cache=resource_cache,
            start=start,
            count=count,
        )
        self._palette_flat: PaletteFlat = palette_flat

    def _get_resource(self, index: Index, chunk: Chunk) -> Font:
        del index
        header, _ = FontHeader.from_bytes(chunk)
        glyph_count = header.CHARACTER_COUNT
        height = header.height
        glyphs_pixels_flat: List[PixelsFlat] = []

        for glyph_index in range(glyph_count):
            offset = header.offsets[glyph_index]
            width = header.widths[glyph_index]
            pixels_flat = chunk[offset:(offset + (width * height))]
            glyphs_pixels_flat.append(pixels_flat)

        instance = Font(height, header.widths, glyphs_pixels_flat, self._palette_flat)
        return instance


class AnsiScreen:

    def __init__(
        self,
        data: ByteString,
        font_impl: ImageFont,
        text_size: Coords,
        font_size: Optional[Coords] = None,
    ):
        if len(data) % 2:
            raise ValueError('data should be made of character+attributes pairs')
        if font_size is None:
            font_size = font_impl.getsize('\u2588')  # full block
        chars = bytes(data[i] for i in range(9 + 0, len(data), 2))
        attrs = bytes(data[i] for i in range(9 + 1, len(data), 2))

        frame0 = create_ansi_image(text_size, font_size)
        text = chars.decode('cp437')
        render_ansi_line(frame0, font_impl, (0, 0), text, attrs, font_size=font_size)

        frame1 = frame0
        if any(attr & 0x80 for attr in attrs):
            frame1 = create_ansi_image(text_size, font_size)
            text = chars.decode('cp437')
            render_ansi_line(frame1, font_impl, (0, 0), text, attrs,
                             font_size=font_size, special='hide')

        self.chars = bytes(data[i] for i in range(9 + 0, len(data), 2))
        self.attrs = bytes(data[i] for i in range(9 + 1, len(data), 2))
        self.frame0: Image = frame0
        self.frame1: Image = frame1
        self.text_size: Coords = text_size
        self.font_size: Coords = font_size


class DOSScreenManager(ResourceManager):

    def __init__(self, chunks_handler, font, start=None, count=None, size=(80, 25), font_size=None):
        super().__init__(chunks_handler, start, count)
        self._font = font
        self._size = size
        self._font_size = font_size

    def _load_resource(self, index, chunk):
        return AnsiScreen(chunk, self._font, self._size, self._font_size)


class AnsiScreenLibrary(ResourceLibrary[Index, AnsiScreen]):

    def __init__(
        self,
        graphics_archive: GraphicsArchiveReader,
        font_impl: ImageFont,
        resource_cache: Optional[Cache[Index, AnsiScreen]] = None,
        start: Optional[Index] = None,
        count: Optional[Index] = None,
        text_size: Coords = ANSI_SCREEN_SIZE,
        font_size: Optional[Coords] = None,
    ):
        super().__init__(
            graphics_archive,
            resource_cache=resource_cache,
            start=start,
            count=count,
        )
        self._font_impl: ImageFont = font_impl
        self._text_size: Coords = text_size
        self._font_size: Optional[Coords] = font_size

    def _get_resource(self, index: Index, chunk: Chunk) -> AnsiScreen:
        instance = AnsiScreen(chunk, self._font_impl, self._text_size, self._font_size)
        return instance


class TextArtManager(ResourceManager):

    def _load_resource(self, index, chunk):
        return chunk.decode('ascii')


class TextArtLibrary(ResourceLibrary[Index, TextArt]):

    def __init__(
        self,
        graphics_archive: GraphicsArchiveReader,
        resource_cache: Optional[Cache[Index, TextArt]] = None,
        start: Optional[Index] = None,
        count: Optional[Index] = None,
    ):
        super().__init__(
            graphics_archive,
            resource_cache=resource_cache,
            start=start,
            count=count,
        )

    def _get_resource(self, index: Index, chunk: Chunk) -> TextArt:
        instance = bytes(chunk).decode('ascii', errors='ignore')
        return instance
