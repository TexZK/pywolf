import array
import sys

from pywolf.utils import reverse_byte


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

    elif counts[code0] < HUFFMAN_NODE_COUNT or counts[code1] < HUFFMAN_NODE_COUNT:
        raise ValueError('Huffman mask too long')


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

    output = memoryview(output)
    output = bytes(output[:tail + (shift != 0)])
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

    output = bytes(output)
    return output


CARMACK_NEAR_TAG = 0xA7
CARMACK_FAR_TAG = 0xA8
CARMACK_MAX_SIZE = 1 << 17


def carmack_compress(data):
    assert len(data) > 0
    assert len(data) % 2 == 0

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

    output = bytes(output)
    return output


def carmack_expand(data, expanded_size):
    assert expanded_size > 0
    assert expanded_size % 2 == 0

    output = bytearray()
    append = output.append
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
                append(next(it))
                append(tag)
                ahead -= 1
        else:
            append(count)
            append(tag)
            ahead -= 1

    output = bytes(output)
    return output


def rle_compress(source, output, tag, max_count):
    append = output.append
    extend = output.extend

    count = 0
    old = tag
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

    extend(old for _ in range(count))


def rle_expand(source, output, tag):
    append = output.append
    extend = output.extend

    it = iter(source)
    try:
        while True:
            datum = next(it)
            if datum == tag:
                count = next(it)
                value = next(it)
                extend(value for _ in range(count))
            else:
                append(datum)

    except StopIteration:
        pass


def rlew_compress(data, tag):
    source = array.array('H', data)
    output = array.array('H')

    rle_compress(source, output, tag, 0xFFFF)

    if sys.byteorder != 'little':
        output.byteswap()
    output = output.tobytes()
    return output


def rlew_expand(data, tag):
    source = array.array('H', data)
    output = array.array('H')

    rle_expand(source, output, tag)

    if sys.byteorder != 'little':
        output.byteswap()
    output = output.tobytes()
    return output


def rleb_compress(data, tag):
    output = bytearray()

    rle_compress(data, output, tag, 0xFF)

    output = bytes(output)
    return output


def rleb_expand(data, tag):
    output = bytearray()

    rle_expand(data, output, tag)

    output = bytes(output)
    return output
