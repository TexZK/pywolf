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
from typing import Sequence
from typing import Tuple
from typing import Union
from typing import cast as _cast

from PIL import Image
from PIL import ImageDraw
from PIL import ImageFont

from .base import ArchiveReader
from .base import Cache
from .base import Char
from .base import Chunk
from .base import Codec
from .base import Coord
from .base import Coords
from .base import Index
from .base import Offset
from .base import ResourceLibrary
from .compression import HUFFMAN_NODE_COUNT
from .compression import huffman_expand
from .utils import stream_fit
from .utils import stream_unpack
from .utils import stream_unpack_array


ColorIndex = int
ColorRGB = Tuple[int, int, int]
PaletteFlat = Sequence[ColorIndex]
PaletteRGB = Sequence[ColorRGB]
PixelsFlat = Sequence[ColorIndex]

TextArt = str

# (partition_name, start_index, count)
GraphicsPartitionEntry = Tuple[str, Index, Index]

# {partition_name: (start_index, count)}
GraphicsPartitionMap = Mapping[str, Tuple[Index, Index]]

# (chunk_index, chunk_size)
SoundInfo = Tuple[Index, Offset]


# ============================================================================


CP437_INDEX_TO_CHAR: List[Char] = list(bytes(range(256)).decode('cp437'))
CP437_CHAR_TO_INDEX: Mapping[Char, int] = {c: i for i, c in enumerate(CP437_INDEX_TO_CHAR)}

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


ANSI_SCREEN_SIZE: Coords = (80, 25)

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


ALPHA: ColorIndex = 0xFF


# ============================================================================

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
    flat_palette = []
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
) -> Image.Image:

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


def build_color_image(size: Coords, rgb: ColorRGB) -> Image.Image:
    return Image.new('RGB', size, rgb)


def winfnt_read(stream: io.BufferedReader) -> Tuple[Dict[str, Any], List[Image.Image]]:
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
    images: List[Image.Image] = []

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


# ============================================================================

def render_ansi_line(
    image: Image.Image,
    font_impl: ImageFont.ImageFont,
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
) -> Image.Image:

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


# ============================================================================

class AnsiScreen:

    def __init__(
        self,
        data: ByteString,
        font_impl: ImageFont.ImageFont,
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
        self.frame0: Image.Image = frame0
        self.frame1: Image.Image = frame1
        self.text_size: Coords = text_size
        self.font_size: Coords = font_size


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
    def from_bytes(cls, buffer: ByteString, offset: Offset = 0) -> Tuple['FontHeader', Offset]:
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
        images: Optional[List[Image.Image]] = [None] * count

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
        self.images: List[Optional[Image.Image]] = images

    def __len__(self) -> int:
        return len(self.widths)

    def __getitem__(self, key: Union[Index, Char]) -> Image.Image:
        if isinstance(key, str):
            key = ord(key)
        return self.images[key]

    def __call__(self, text_bytes: ByteString) -> Iterator[Image.Image]:
        images = self.images
        for glyph_index in text_bytes:
            yield from images[glyph_index]


class Picture:

    def __init__(
        self,
        size: Coords,
        pixels_flat: PixelsFlat,
        palette_flat: PaletteFlat,
        alpha: Optional[ColorIndex] = None,
    ):
        image = make_8bit_image(size, pixels_flat, palette_flat, alpha=alpha)
        self.image: Image.Image = image
        self.size: Coords = size


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
    def from_bytes(cls, buffer: ByteString, offset: Offset = 0) -> Tuple['SpriteHeader', Offset]:
        offset = int(offset)
        left, right = struct.unpack_from('<HH', buffer, offset)
        offset += 2

        width = right - left + 1
        offsets = list(struct.unpack_from(f'<{width}H', buffer, offset))
        offset += width * 2

        instance = cls(left, right, offsets)
        return instance, offset

    @classmethod
    def from_stream(cls, stream: io.BufferedReader) -> 'SpriteHeader':
        buffer = stream.read(4)
        left, right = struct.unpack('<HH', buffer)
        width = right - left + 1
        buffer += stream.read(width * 2)
        instance, _ = cls.from_bytes(buffer)
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
        self.image: Image.Image = image
        self.size: Coords = size
        self.alpha: ColorIndex = alpha


class Texture:

    def __init__(
        self,
        size: Coords,
        pixels_flat: PixelsFlat,
        palette_flat: PaletteFlat,
        alpha: Optional[ColorIndex] = None,
    ):
        image = make_8bit_image(size, pixels_flat, palette_flat, alpha=alpha)
        self.image: Image.Image = image
        self.size: Coords = size


# ============================================================================

class GraphicsArchiveReader(ArchiveReader):

    def __init__(
        self,
        chunk_cache: Optional[Cache[Index, Chunk]] = None,
    ):
        super().__init__(chunk_cache=chunk_cache)

        self._header_stream: Optional[io.BufferedReader] = None
        self._header_offset: Offset = 0
        self._header_size: Offset = 0
        self._huffman_stream: Optional[io.BufferedReader] = None
        self._huffman_offset: Offset = 0
        self._huffman_size: Offset = 0
        self._partition_map: Dict[str, Tuple[Index, Index]] = {}
        self._pics_size_index: Index = -1
        self._huffman_nodes: List[Tuple[int, int]] = []
        self._pics_size: List[Coords] = []

    def _read_pics_size(self) -> List[Coords]:
        count = self._partition_map['pics'][1]
        chunk = self._read_chunk(self._pics_size_index)
        chunk_stream = io.BytesIO(chunk)
        pics_size: List[Coords] = list(stream_unpack_array('<HH', chunk_stream, count, scalar=False))
        return pics_size

    def _read_chunk(self, index: Index) -> bytes:
        chunk_size = self.sizeof(index)
        if chunk_size:
            self._seek_chunk(index)
            compressed_size, expanded_size = self._read_sizes(index)
            chunk = self._data_stream.read(compressed_size)
            chunk = huffman_expand(chunk, expanded_size, self._huffman_nodes)
            return chunk
        else:
            return b''

    def _read_huffman_nodes(self) -> List[Tuple[int, int]]:
        huffman_stream = self._huffman_stream
        huffman_nodes: List[Tuple[int, int]] = []

        for node_index in range(HUFFMAN_NODE_COUNT):
            node = struct.unpack('<HH', huffman_stream.read(4))
            node = _cast(Tuple[int, int], node)
            huffman_nodes.append(node)

        return huffman_nodes

    def _read_sizes(self, index: Index):
        BLOCK_SIZE = (8 * 8) * 1
        MASKBLOCK_SIZE = (8 * 8) * 2
        compressed_size = self.sizeof(index)

        key = self.find_partition(self._partition_map, index)[0]

        if key == 'tile8':  # tile 8s are all in one chunk!
            expanded_size = BLOCK_SIZE * self._partition_map[key][1]
        elif key == 'tile8m':
            expanded_size = MASKBLOCK_SIZE * self._partition_map[key][1]
        elif key == 'tile16':  # all other tiles are one per chunk
            expanded_size = BLOCK_SIZE * 4
        elif key == 'tile16m':
            expanded_size = MASKBLOCK_SIZE * 4
        elif key == 'tile32':
            expanded_size = BLOCK_SIZE * 16
        elif key == 'tile32m':
            expanded_size = MASKBLOCK_SIZE * 16
        else:  # everything else has an explicit size longword
            expanded_size = stream_unpack('<L', self._data_stream)[0]
            compressed_size -= 4

        return compressed_size, expanded_size

    def _seek_chunk(
        self,
        index: Index,
        offsets: Optional[Sequence[Offset]] = None,
    ) -> None:

        del offsets
        super()._seek_chunk(index, offsets=None)

    def clear(self) -> None:
        super().clear()
        self._header_stream = None
        self._header_offset = 0
        self._header_size = 0
        self._huffman_stream = None
        self._huffman_offset = 0
        self._huffman_size = 0
        self._partition_map = {}
        self._pics_size_index = -1
        self._huffman_nodes = []
        self._pics_size = []

    def close(self) -> None:
        super().close()
        self._header_stream = None
        self._huffman_stream = None

    @classmethod
    def find_partition(
        cls,
        partition_map: GraphicsPartitionMap,
        index: Index,
    ) -> GraphicsPartitionEntry:
        for key, value in partition_map.items():
            start, chunks_count = value
            if chunks_count and key.startswith('tile8'):
                chunks_count = 1
            if start <= index < start + chunks_count:
                return key, start, chunks_count
        raise KeyError(f'chunk index without partition: {index}')

    def open(
        self,
        data_stream: Optional[io.BufferedReader] = None,
        data_offset: Optional[Offset] = None,
        data_size: Optional[Offset] = None,
        header_stream: Optional[io.BufferedReader] = None,
        header_offset: Optional[Offset] = None,
        header_size: Optional[Offset] = None,
        huffman_stream: Optional[io.BufferedReader] = None,
        huffman_offset: Optional[Offset] = None,
        huffman_size: Optional[Offset] = None,
        partition_map: Optional[GraphicsPartitionMap] = None,
        pics_size_index: Index = 0,
    ) -> None:

        if header_stream is None:
            raise ValueError('a header stream should be provided')
        if huffman_stream is None:
            raise ValueError('a Huffman stream should be provided')
        if partition_map is None:
            raise ValueError('a graphics partition map must be provided')
        super().open(data_stream, data_offset=data_offset, data_size=data_size)

        pics_size_index = pics_size_index.__index__()
        if pics_size_index < 0:
            raise ValueError('negative pics size index')

        header_offset, header_size = stream_fit(header_stream, header_offset, header_size)
        if header_size % 3:
            raise ValueError(f'header size must be divisible by 3: {header_size}')

        huffman_offset, huffman_size = stream_fit(huffman_stream, huffman_offset, huffman_size)
        if huffman_size < 4 * HUFFMAN_NODE_COUNT:
            raise ValueError(f'Huffman size: actual={huffman_size} < expected={4 * HUFFMAN_NODE_COUNT}')

        chunk_count = header_size // 3
        chunk_offsets: List[Optional[Offset]] = [None] * chunk_count

        for index in range(chunk_count):
            byte0, byte1, byte2 = stream_unpack('<BBB', header_stream)
            offset = byte0 | (byte1 << 8) | (byte2 << 16)
            if offset < 0xFFFFFF:
                chunk_offsets[index] = offset

        data_size = self._data_size
        chunk_offsets.append(data_size)

        for index in reversed(range(chunk_count)):
            if chunk_offsets[index] is None:
                chunk_offsets[index] = chunk_offsets[index + 1]
        chunk_offsets = _cast(List[Offset], chunk_offsets)

        for index in range(chunk_count):
            if not 0 <= chunk_offsets[index] <= data_size:
                raise ValueError(f'invalid offset value: index={index}')
            if not chunk_offsets[index] <= chunk_offsets[index + 1]:
                raise ValueError(f'invalid offset ordering: index={index}')

        self._chunk_count = chunk_count
        self._chunk_offsets = chunk_offsets
        self._header_stream = header_stream
        self._header_offset = header_offset
        self._header_size = header_size
        self._huffman_stream = huffman_stream
        self._huffman_offset = huffman_offset
        self._huffman_size = huffman_size
        self._partition_map = partition_map
        self._pics_size_index = pics_size_index
        self._huffman_nodes = self._read_huffman_nodes()
        self._pics_size = self._read_pics_size()

    @property
    def pics_size(self) -> Sequence[Coords]:
        return self._pics_size


class VswapArchiveReader(ArchiveReader):

    def __init__(
        self,
        chunk_cache: Optional[Cache[Index, Chunk]] = None,
    ):
        super().__init__(chunk_cache=chunk_cache)

        self._pages_offset: Offset = 0
        self._pages_size: Offset = 0
        self._image_size: Coords = (64, 64)
        self._alpha_index: Optional[ColorIndex] = None
        self._sprites_start: Index = 0
        self._sounds_start: Index = 0
        self._sounds_infos: List[SoundInfo] = []

    def _read_chunk(self, index: Index) -> bytes:
        chunk_size = self.sizeof(index)
        if chunk_size:
            self._seek_chunk(index)
            chunk = self._data_stream.read(chunk_size)
            return chunk
        else:
            return b''

    def _read_sounds_infos(self) -> List[SoundInfo]:
        chunk_count = self._chunk_count
        last_chunk_size = self.sizeof(chunk_count - 1)
        if last_chunk_size % 4:
            raise ValueError(f'last chunk size must be divisible by 4: {last_chunk_size}')

        count = last_chunk_size // 4
        self._seek_chunk(chunk_count - 1)

        data_stream = self._data_stream
        bounds: List[Tuple[Index, Offset]] = list(
            stream_unpack_array('<HH', data_stream, count, scalar=False))

        sounds_start = self.sounds_start
        bounds.append(((chunk_count - sounds_start), bounds[-1][1]))
        infos: List[SoundInfo] = []

        for index in range(count):
            start, length = bounds[index]
            if start >= chunk_count - 1:
                return infos[:index]
            last = bounds[index + 1][0]

            if not last or last + sounds_start > chunk_count - 1:
                last = chunk_count - 1
            else:
                last += sounds_start

            actual_length = sum(self.sizeof(j) for j in range(sounds_start + start, last))
            if actual_length & 0xFFFF0000 and (actual_length & 0xFFFF) < length:  # TBV: really needed?
                actual_length -= 0x10000
            actual_length = (actual_length & 0xFFFF0000) | length

            infos.append((start, actual_length))

        return infos

    def clear(self) -> None:
        super().clear()
        self._pages_offset = 0
        self._pages_size = 0
        self._sprites_start = 0
        self._sounds_start = 0
        self._sounds_infos = []

    def open(
        self,
        data_stream: Optional[io.BufferedReader] = None,
        data_offset: Optional[Offset] = None,
        data_size: Optional[Offset] = None,
        image_size: Coords = (64, 64),
        alpha_index: ColorIndex = ALPHA,
        data_size_guard: Optional[Offset] = None,
    ) -> None:

        super().open(data_stream, data_offset=data_offset, data_size=data_size)

        data_size = self._data_size
        if data_size % 6:
            raise ValueError(f'data size must be divisible by 6: {data_size}')

        width, height = image_size
        if width < 1 or height < 1:
            raise ValueError(f'invalid image size: {image_size}')

        alpha_index = alpha_index.__index__()
        if not 0x00 <= alpha_index <= 0xFF:
            raise ValueError(f'alpha index out of range: {alpha_index}')

        data_stream = self._data_stream
        chunk_count, sprites_start, sounds_start = stream_unpack('<HHH', data_stream)
        chunk_offsets: List[Offset] = list(stream_unpack_array('<L', data_stream, chunk_count))
        chunk_offsets.append(data_size)

        pages_offset = chunk_offsets[0]
        pages_size = data_size - pages_offset

        if data_size_guard is not None:
            if data_size >= data_size_guard:
                raise ValueError(f'data size guard: actual={data_size} > guard={data_size_guard}')

        for index in reversed(range(chunk_count)):
            if not chunk_offsets[index]:
                chunk_offsets[index] = chunk_offsets[index + 1]

        for index in range(chunk_count):
            if not pages_offset <= chunk_offsets[index] <= data_size:
                raise ValueError(f'inconsistent offset paging: index={index}')
            if not chunk_offsets[index] <= chunk_offsets[index + 1]:
                raise ValueError(f'inconsistent offset ordering: index={index}')

        self._chunk_count = chunk_count
        self._chunk_offsets = chunk_offsets
        self._pages_offset = pages_offset
        self._pages_size = pages_size
        self._image_size = image_size
        self._alpha_index = alpha_index
        self._sprites_start = sprites_start
        self._sounds_start = sounds_start
        self._sounds_infos = self._read_sounds_infos()

    @property
    def sounds_start(self) -> Index:
        return self._sounds_start

    @property
    def sounds_infos(self) -> List[SoundInfo]:
        return self._sounds_infos

    @property
    def sprites_start(self) -> Index:
        return self._sprites_start

    def iterate_sampled_sound(self, sound_index: Index) -> Iterator[int]:
        start, length = self._sounds_infos[sound_index]
        chunk_index = self._sounds_start + start
        remaining = int(length)

        while remaining:
            chunk = self[chunk_index]
            size = len(chunk)
            if size <= remaining:
                yield from chunk
                remaining -= size
            else:
                yield from memoryview(chunk)[:remaining]
                break
            chunk_index += 1


# ============================================================================

class AnsiScreenLibrary(ResourceLibrary[Index, AnsiScreen]):

    def __init__(
        self,
        graphics_archive: GraphicsArchiveReader,
        font_impl: ImageFont.ImageFont,
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
        self._font_impl: ImageFont.ImageFont = font_impl
        self._text_size: Coords = text_size
        self._font_size: Optional[Coords] = font_size

    def _get_resource(self, index: Index, chunk: Chunk) -> AnsiScreen:
        instance = AnsiScreen(chunk, self._font_impl, self._text_size, self._font_size)
        return instance


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
