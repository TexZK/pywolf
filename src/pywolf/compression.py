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

import array
import sys
from typing import ByteString
from typing import List
from typing import MutableSequence
from typing import Sequence
from typing import Tuple


def _reverse_byte(value: int) -> int:
    # http://graphics.stanford.edu/~seander/bithacks.html#ReverseByteWith64BitsDiv
    return (value * 0x0202020202 & 0x010884422010) % 1023


HUFFMAN_NODE_COUNT: int = 256
HUFFMAN_HEAD_INDEX: int = HUFFMAN_NODE_COUNT - 2
HUFFMAN_REVERSED: List[int] = [_reverse_byte(i) for i in range(HUFFMAN_NODE_COUNT)]

HUFFMAN_CLONE_NODES = (
    [(HUFFMAN_REVERSED[i], HUFFMAN_REVERSED[i + 1])
     for i in range(0, HUFFMAN_NODE_COUNT, 2)]
    +
    [(HUFFMAN_NODE_COUNT + i, HUFFMAN_NODE_COUNT + i + 1)
     for i in range(0, HUFFMAN_NODE_COUNT - 1, 2)]
)

HUFFMAN_MAX_DEPTH: int = 24
HUFFMAN_MAX_CODE: int = 0xFFFF
HUFFMAN_MAX_PROBABILITY: int = 0x7FFFFFFF


def huffman_count(data: ByteString) -> List[int]:
    counts = [0] * HUFFMAN_NODE_COUNT
    for datum in data:
        counts[datum] += 1
    return counts


def huffman_trace(
    index: int,
    shift: int,
    mask: int,
    nodes: Sequence[Tuple[int, int]],
    shifts: MutableSequence[int],
    masks: MutableSequence[int],
    counts: Sequence[int]
) -> None:

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

    elif (counts[code0 - HUFFMAN_NODE_COUNT] < HUFFMAN_NODE_COUNT or
          counts[code1 - HUFFMAN_NODE_COUNT] < HUFFMAN_NODE_COUNT):
        raise ValueError('Huffman mask too long')


def huffman_build_nodes(counts: Sequence[int]) -> List[Tuple[int, int]]:
    probs: List[int] = list(counts)
    values = list(range(HUFFMAN_NODE_COUNT))
    nodes: List[Tuple[int, int]] = [(0, 0)] * HUFFMAN_NODE_COUNT

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

        nodes[index] = (value0, value1)
        values[code0] = HUFFMAN_NODE_COUNT + index
        probs[code0] += probs[code1]
        probs[code1] = HUFFMAN_MAX_PROBABILITY

    return nodes


def huffman_build_masks(
    counts: Sequence[int],
    nodes: Sequence[Tuple[int, int]],
) -> Tuple[List[int], List[int]]:

    shifts = [0] * HUFFMAN_NODE_COUNT
    masks = [0] * HUFFMAN_NODE_COUNT
    huffman_trace(HUFFMAN_HEAD_INDEX, 0, 0, nodes, shifts, masks, counts)
    return shifts, masks


def huffman_compress(
    data: ByteString,
    shifts: Sequence[int],
    masks: Sequence[int],
) -> bytes:

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

    output = memoryview(output)
    output = bytes(output[:tail + (shift != 0)])
    return output


def huffman_expand(
    data: ByteString,
    expanded_size: int,
    nodes: Sequence[Tuple[int, int]],
) -> bytearray:

    if expanded_size < 0:
        raise ValueError('negative expanded size')
    head = nodes[HUFFMAN_HEAD_INDEX]
    output = bytearray()
    append = output.append

    it = iter(data)
    try:
        datum = it.__next__()
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
                datum = it.__next__()
                mask = 1 << 0
            else:
                mask <<= 1

    except StopIteration:
        output += bytes(expanded_size - len(output))

    return output


CARMACK_NEAR_TAG: int = 0xA7
CARMACK_FAR_TAG: int = 0xA8
CARMACK_MAX_SIZE: int = 1 << 17


def carmack_compress(
    data: ByteString,
) -> bytearray:

    if len(data) < 2:
        raise ValueError('not enough data to compress')
    if len(data) % 2:
        raise ValueError('data size must be divisible by 2')

    source = array.array('H', data)
    if sys.byteorder != 'little':
        source.byteswap()

    output = bytearray()
    append = output.append
    ahead = len(source)
    index = 0

    while ahead > 0:
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

    if ahead < 0:
        raise ValueError('ahead < 0')

    return output


def carmack_expand(
    data: ByteString,
    expanded_size: int,
) -> bytearray:

    if expanded_size < 2:
        raise ValueError('not enough data to expand')
    if expanded_size % 2:
        raise ValueError('expanded size must be divisible by 2')

    output = bytearray()
    append = output.append
    extend = output.extend

    it = iter(data)
    ahead = expanded_size >> 1
    while ahead:
        count, tag = it.__next__(), it.__next__()
        if tag == CARMACK_NEAR_TAG or tag == CARMACK_FAR_TAG:
            if count:
                if ahead < count:
                    break
                if tag == CARMACK_NEAR_TAG:
                    offset = len(output) - (it.__next__() << 1)
                else:
                    offset = (it.__next__() | (it.__next__() << 8)) << 1
                extend(output[offset:(offset + (count << 1))])
                ahead -= count
            else:
                append(it.__next__())
                append(tag)
                ahead -= 1
        else:
            append(count)
            append(tag)
            ahead -= 1

    return output


def rle_compress(
    source: Sequence[int],
    output: MutableSequence[int],
    tag: int,
    max_count: int,
) -> None:

    append = output.append
    extend = output.extend
    count = 0
    old = None

    for datum in source:
        if datum == old and count < max_count:
            count += 1
        else:
            if count > 3 or old == tag:
                append(tag)
                append(count)
                append(old)
            else:
                extend(old for _ in range(count))
            count = 1
            old = datum

    if count > 3 or old == tag:
        append(tag)
        append(count)
        append(old)
    else:
        extend(old for _ in range(count))


def rle_expand(
    source: Sequence[int],
    output: MutableSequence[int],
    tag: int,
) -> None:

    append = output.append
    extend = output.extend
    it = iter(source)
    try:
        while True:
            datum = it.__next__()
            if datum == tag:
                count = it.__next__()
                value = it.__next__()
                extend(value for _ in range(count))
            else:
                append(datum)
    except StopIteration:
        pass


def rlew_compress(
    data: ByteString,
    tag: int,
) -> bytes:

    source = array.array('H', data)
    if sys.byteorder != 'little':
        source.byteswap()
    output = array.array('H')
    rle_compress(source, output, tag, 0xFFFF)
    if sys.byteorder != 'little':
        output.byteswap()
    output = output.tobytes()
    return output


def rlew_expand(
    data: ByteString,
    tag: int,
) -> bytes:

    source = array.array('H', data)
    if sys.byteorder != 'little':
        source.byteswap()
    output = array.array('H')
    if sys.byteorder != 'little':
        output.byteswap()
    rle_expand(source, output, tag)
    output = output.tobytes()
    return output


def rleb_compress(
    data: ByteString,
    tag: int,
) -> bytearray:

    output = bytearray()
    rle_compress(data, output, tag, 0xFF)
    return output


def rleb_expand(
    data: ByteString,
    tag: int,
) -> bytearray:

    output = bytearray()
    rle_expand(data, output, tag)
    return output
