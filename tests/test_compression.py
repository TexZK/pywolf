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

import os
import struct

import pytest
from pathlib import Path
from typing import List
from typing import Tuple
from typing import Union
from typing import cast as _cast

from pywolf.compression import HUFFMAN_NODE_COUNT
from pywolf.compression import carmack_compress
from pywolf.compression import carmack_expand
from pywolf.compression import huffman_build_masks
from pywolf.compression import huffman_build_nodes
from pywolf.compression import huffman_compress
from pywolf.compression import huffman_count
from pywolf.compression import huffman_expand
from pywolf.compression import rleb_compress
from pywolf.compression import rleb_expand
from pywolf.compression import rlew_compress
from pywolf.compression import rlew_expand


RLEB_TAG = 0xFE
RLEW_TAG = 0xFEFE


# ============================================================================

@pytest.fixture
def temppath(tmpdir):
    return Path(str(tmpdir))


@pytest.fixture(scope='module')
def datadir(request):
    dir_path, _ = os.path.splitext(request.module.__file__)
    assert os.path.isdir(str(dir_path))
    return dir_path


@pytest.fixture
def datapath(datadir):
    return Path(str(datadir))


# ----------------------------------------------------------------------------

def read_bytes(
    path: Union[str, Path],
) -> bytes:

    path = str(path)
    with open(path, 'rb') as stream:
        data = stream.read()
    return data


def write_bytes(
    path: Union[str, Path],
    data: Union[bytes, bytearray, memoryview],
) -> None:

    path = str(path)
    with open(path, 'wb') as stream:
        stream.write(data)

# ----------------------------------------------------------------------------


def read_huffman_nodes(
    path: Union[str, Path],
) -> List[Tuple[int, int]]:

    path = str(path)
    nodes = []
    with open(path, 'rb') as stream:
        for _ in range(HUFFMAN_NODE_COUNT):
            node = struct.unpack('<HH', stream.read(4))
            node = _cast(Tuple[int, int], node)
            nodes.append(node)
    return nodes


def write_huffman_nodes(
    path: Union[str, Path],
    nodes: List[Tuple[int, int]],
) -> None:

    path = str(path)
    with open(path, 'wb') as stream:
        for code0, code1 in nodes:
            chunk = struct.pack('<HH', code0, code1)
            stream.write(chunk)


# ============================================================================

def test_huffman_count__null():
    data = bytes()
    counts = huffman_count(data)
    assert len(counts) == 256
    assert all(c == 0 for c in counts)


def test_huffman_count__once():
    data = bytes(123)
    counts = huffman_count(data)
    assert len(counts) == 256
    assert counts[0] == 123
    assert all(c == 0 for c in counts[1:])


def test_huffman_count__256():
    data = bytes(range(256))
    counts = huffman_count(data)
    assert len(counts) == 256
    assert all(c == 1 for c in counts)


# ----------------------------------------------------------------------------

def test_huffman_trace():
    pass  # TODO


# ----------------------------------------------------------------------------

def test_huffman_build_nodes():
    pass  # TODO


# ----------------------------------------------------------------------------

def test_huffman_build_masks():
    pass  # TODO


# ----------------------------------------------------------------------------

def test_huffman_compress__empty(temppath: Path, datapath: Path):
    dat_nodes_path = datapath/'bytes.huffman_nodes.bin'
    out_bytes_path = temppath/'empty.huffman_compress.bin'
    ref_bytes_path = datapath/'empty.huffman_compress.bin'
    dat_bytes = bytes()
    counts = huffman_count(dat_bytes)
    nodes = read_huffman_nodes(dat_nodes_path)
    shifts, masks = huffman_build_masks(counts, nodes)
    out_bytes = huffman_compress(dat_bytes, shifts, masks)
    write_bytes(out_bytes_path, out_bytes)
    ref_bytes = read_bytes(ref_bytes_path)
    assert out_bytes == ref_bytes


def test_huffman_compress__bytes(temppath: Path, datapath: Path):
    dat_bytes_path = datapath/'bytes.bin'
    out_bytes_path = temppath/'bytes.huffman_compress.bin'
    ref_bytes_path = datapath/'bytes.huffman_compress.bin'
    dat_bytes = read_bytes(dat_bytes_path)
    counts = huffman_count(dat_bytes)
    nodes = huffman_build_nodes(counts)
    shifts, masks = huffman_build_masks(counts, nodes)
    out_bytes = huffman_compress(dat_bytes, shifts, masks)
    write_bytes(out_bytes_path, out_bytes)
    ref_bytes = read_bytes(ref_bytes_path)
    assert out_bytes == ref_bytes


def test_huffman_compress__ladder(temppath: Path, datapath: Path):
    dat_bytes_path = datapath/'ladder.bin'
    out_bytes_path = temppath/'ladder.huffman_compress.bin'
    ref_bytes_path = datapath/'ladder.huffman_compress.bin'
    dat_bytes = read_bytes(dat_bytes_path)
    counts = huffman_count(dat_bytes)
    nodes = huffman_build_nodes(counts)
    shifts, masks = huffman_build_masks(counts, nodes)
    out_bytes = huffman_compress(dat_bytes, shifts, masks)
    write_bytes(out_bytes_path, out_bytes)
    ref_bytes = read_bytes(ref_bytes_path)
    assert out_bytes == ref_bytes


# ----------------------------------------------------------------------------

def test_huffman_expand__empty(temppath: Path, datapath: Path):
    dat_nodes_path = datapath/'bytes.huffman_nodes.bin'
    dat_bytes_path = datapath/'empty.huffman_compress.bin'
    out_bytes_path = temppath/'empty.huffman_expand.bin'
    dat_bytes = read_bytes(dat_bytes_path)
    dat_nodes = read_huffman_nodes(dat_nodes_path)
    out_bytes = huffman_expand(dat_bytes, 0, dat_nodes)
    write_bytes(out_bytes_path, out_bytes)
    ref_bytes = bytes()
    assert out_bytes == ref_bytes


def test_huffman_expand__bytes(temppath: Path, datapath: Path):
    dat_nodes_path = datapath/'bytes.huffman_nodes.bin'
    dat_bytes_path = datapath/'bytes.huffman_compress.bin'
    out_bytes_path = temppath/'bytes.huffman_expand.bin'
    ref_bytes_path = datapath/'bytes.bin'
    dat_bytes = read_bytes(dat_bytes_path)
    dat_nodes = read_huffman_nodes(dat_nodes_path)
    out_bytes = huffman_expand(dat_bytes, HUFFMAN_NODE_COUNT, dat_nodes)
    write_bytes(out_bytes_path, out_bytes)
    ref_bytes = read_bytes(ref_bytes_path)
    assert out_bytes == ref_bytes


def test_huffman_expand__ladder(temppath: Path, datapath: Path):
    dat_nodes_path = datapath/'ladder.huffman_nodes.bin'
    dat_bytes_path = datapath/'ladder.huffman_compress.bin'
    out_bytes_path = temppath/'ladder.huffman_expand.bin'
    ref_bytes_path = datapath/'ladder.bin'
    dat_bytes = read_bytes(dat_bytes_path)
    dat_nodes = read_huffman_nodes(dat_nodes_path)
    ref_bytes = read_bytes(ref_bytes_path)
    out_bytes = huffman_expand(dat_bytes, len(ref_bytes), dat_nodes)
    write_bytes(out_bytes_path, out_bytes)
    assert out_bytes == ref_bytes


# ============================================================================

def test_carmack_compress__wrong():
    with pytest.raises(ValueError, match='not enough'):
        carmack_compress(b'1')

    with pytest.raises(ValueError, match='divisible by 2'):
        carmack_compress(b'123')


def test_carmack_compress__zeros(temppath: Path, datapath: Path):
    dat_bytes_path = datapath/'zeros.bin'
    out_bytes_path = temppath/'zeros.carmack_compress.bin'
    ref_bytes_path = datapath/'zeros.carmack_compress.bin'
    dat_bytes = read_bytes(dat_bytes_path)
    out_bytes = carmack_compress(dat_bytes)
    write_bytes(out_bytes_path, out_bytes)
    ref_bytes = read_bytes(ref_bytes_path)
    assert out_bytes == ref_bytes


def test_carmack_compress__bytes(temppath: Path, datapath: Path):
    dat_bytes_path = datapath/'bytes.bin'
    out_bytes_path = temppath/'bytes.carmack_compress.bin'
    ref_bytes_path = datapath/'bytes.carmack_compress.bin'
    dat_bytes = read_bytes(dat_bytes_path)
    out_bytes = carmack_compress(dat_bytes)
    write_bytes(out_bytes_path, out_bytes)
    ref_bytes = read_bytes(ref_bytes_path)
    assert out_bytes == ref_bytes


def test_carmack_compress__ladder(temppath: Path, datapath: Path):
    dat_bytes_path = datapath/'ladder.bin'
    out_bytes_path = temppath/'ladder.carmack_compress.bin'
    ref_bytes_path = datapath/'ladder.carmack_compress.bin'
    dat_bytes = read_bytes(dat_bytes_path)
    out_bytes = carmack_compress(dat_bytes)
    write_bytes(out_bytes_path, out_bytes)
    ref_bytes = read_bytes(ref_bytes_path)
    assert out_bytes == ref_bytes


# ----------------------------------------------------------------------------


def test_carmack_expand__zeros(temppath: Path, datapath: Path):
    dat_bytes_path = datapath/'zeros.carmack_compress.bin'
    out_bytes_path = temppath/'zeros.carmack_expand.bin'
    ref_bytes_path = datapath/'zeros.bin'
    dat_bytes = read_bytes(dat_bytes_path)
    ref_bytes = read_bytes(ref_bytes_path)
    out_bytes = carmack_expand(dat_bytes, len(ref_bytes))
    write_bytes(out_bytes_path, out_bytes)
    assert out_bytes == ref_bytes


def test_carmack_expand__bytes(temppath: Path, datapath: Path):
    dat_bytes_path = datapath/'bytes.carmack_compress.bin'
    out_bytes_path = temppath/'bytes.carmack_expand.bin'
    ref_bytes_path = datapath/'bytes.bin'
    dat_bytes = read_bytes(dat_bytes_path)
    ref_bytes = read_bytes(ref_bytes_path)
    out_bytes = carmack_expand(dat_bytes, len(ref_bytes))
    write_bytes(out_bytes_path, out_bytes)
    assert out_bytes == ref_bytes


def test_carmack_expand__ladder(temppath: Path, datapath: Path):
    dat_bytes_path = datapath/'ladder.carmack_compress.bin'
    out_bytes_path = temppath/'ladder.carmack_expand.bin'
    ref_bytes_path = datapath/'ladder.bin'
    dat_bytes = read_bytes(dat_bytes_path)
    ref_bytes = read_bytes(ref_bytes_path)
    out_bytes = carmack_expand(dat_bytes, len(ref_bytes))
    write_bytes(out_bytes_path, out_bytes)
    assert out_bytes == ref_bytes


# ============================================================================

def test_rleb_compress__empty(temppath: Path, datapath: Path):
    dat_bytes_path = datapath/'empty.bin'
    out_bytes_path = temppath/'empty.rleb_compress.bin'
    ref_bytes_path = datapath/'empty.rleb_compress.bin'
    dat_bytes = read_bytes(dat_bytes_path)
    out_bytes = rleb_compress(dat_bytes, RLEB_TAG)
    write_bytes(out_bytes_path, out_bytes)
    ref_bytes = read_bytes(ref_bytes_path)
    assert out_bytes == ref_bytes


def test_rleb_compress__zeros(temppath: Path, datapath: Path):
    dat_bytes_path = datapath/'zeros.bin'
    out_bytes_path = temppath/'zeros.rleb_compress.bin'
    ref_bytes_path = datapath/'zeros.rleb_compress.bin'
    dat_bytes = read_bytes(dat_bytes_path)
    out_bytes = rleb_compress(dat_bytes, RLEB_TAG)
    write_bytes(out_bytes_path, out_bytes)
    ref_bytes = read_bytes(ref_bytes_path)
    assert out_bytes == ref_bytes


def test_rleb_compress__bytes(temppath: Path, datapath: Path):
    dat_bytes_path = datapath/'bytes.bin'
    out_bytes_path = temppath/'bytes.rleb_compress.bin'
    ref_bytes_path = datapath/'bytes.rleb_compress.bin'
    dat_bytes = read_bytes(dat_bytes_path)
    out_bytes = rleb_compress(dat_bytes, RLEB_TAG)
    write_bytes(out_bytes_path, out_bytes)
    ref_bytes = read_bytes(ref_bytes_path)
    assert out_bytes == ref_bytes


def test_rleb_compress__ladder(temppath: Path, datapath: Path):
    dat_bytes_path = datapath/'ladder.bin'
    out_bytes_path = temppath/'ladder.rleb_compress.bin'
    ref_bytes_path = datapath/'ladder.rleb_compress.bin'
    dat_bytes = read_bytes(dat_bytes_path)
    out_bytes = rleb_compress(dat_bytes, RLEB_TAG)
    write_bytes(out_bytes_path, out_bytes)
    ref_bytes = read_bytes(ref_bytes_path)
    assert out_bytes == ref_bytes


# ----------------------------------------------------------------------------

def test_rleb_expand__empty(temppath: Path, datapath: Path):
    dat_bytes_path = datapath/'empty.rleb_compress.bin'
    out_bytes_path = temppath/'empty.rleb_expand.bin'
    ref_bytes_path = datapath/'empty.bin'
    dat_bytes = read_bytes(dat_bytes_path)
    out_bytes = rleb_expand(dat_bytes, RLEB_TAG)
    write_bytes(out_bytes_path, out_bytes)
    ref_bytes = read_bytes(ref_bytes_path)
    assert out_bytes == ref_bytes


def test_rleb_expand__zeros(temppath: Path, datapath: Path):
    dat_bytes_path = datapath/'zeros.rleb_compress.bin'
    out_bytes_path = temppath/'zeros.rleb_expand.bin'
    ref_bytes_path = datapath/'zeros.bin'
    dat_bytes = read_bytes(dat_bytes_path)
    out_bytes = rleb_expand(dat_bytes, RLEB_TAG)
    write_bytes(out_bytes_path, out_bytes)
    ref_bytes = read_bytes(ref_bytes_path)
    assert out_bytes == ref_bytes


def test_rleb_expand__bytes(temppath: Path, datapath: Path):
    dat_bytes_path = datapath/'bytes.rleb_compress.bin'
    out_bytes_path = temppath/'bytes.rleb_expand.bin'
    ref_bytes_path = datapath/'bytes.bin'
    dat_bytes = read_bytes(dat_bytes_path)
    out_bytes = rleb_expand(dat_bytes, RLEB_TAG)
    write_bytes(out_bytes_path, out_bytes)
    ref_bytes = read_bytes(ref_bytes_path)
    assert out_bytes == ref_bytes


def test_rleb_expand__ladder(temppath: Path, datapath: Path):
    dat_bytes_path = datapath/'ladder.rleb_compress.bin'
    out_bytes_path = temppath/'ladder.rleb_expand.bin'
    ref_bytes_path = datapath/'ladder.bin'
    dat_bytes = read_bytes(dat_bytes_path)
    out_bytes = rleb_expand(dat_bytes, RLEB_TAG)
    write_bytes(out_bytes_path, out_bytes)
    ref_bytes = read_bytes(ref_bytes_path)
    assert out_bytes == ref_bytes


# ============================================================================

def test_rlew_compress__empty(temppath: Path, datapath: Path):
    dat_bytes_path = datapath/'empty.bin'
    out_bytes_path = temppath/'empty.rlew_compress.bin'
    ref_bytes_path = datapath/'empty.rlew_compress.bin'
    dat_bytes = read_bytes(dat_bytes_path)
    out_bytes = rlew_compress(dat_bytes, RLEW_TAG)
    write_bytes(out_bytes_path, out_bytes)
    ref_bytes = read_bytes(ref_bytes_path)
    assert out_bytes == ref_bytes


def test_rlew_compress__zeros(temppath: Path, datapath: Path):
    dat_bytes_path = datapath/'zeros.bin'
    out_bytes_path = temppath/'zeros.rlew_compress.bin'
    ref_bytes_path = datapath/'zeros.rlew_compress.bin'
    dat_bytes = read_bytes(dat_bytes_path)
    out_bytes = rlew_compress(dat_bytes, RLEW_TAG)
    write_bytes(out_bytes_path, out_bytes)
    ref_bytes = read_bytes(ref_bytes_path)
    assert out_bytes == ref_bytes


def test_rlew_compress__bytes(temppath: Path, datapath: Path):
    dat_bytes_path = datapath/'bytes.bin'
    out_bytes_path = temppath/'bytes.rlew_compress.bin'
    ref_bytes_path = datapath/'bytes.rlew_compress.bin'
    dat_bytes = read_bytes(dat_bytes_path)
    out_bytes = rlew_compress(dat_bytes, RLEW_TAG)
    write_bytes(out_bytes_path, out_bytes)
    ref_bytes = read_bytes(ref_bytes_path)
    assert out_bytes == ref_bytes


def test_rlew_compress__ladder(temppath: Path, datapath: Path):
    dat_bytes_path = datapath/'ladder.bin'
    out_bytes_path = temppath/'ladder.rlew_compress.bin'
    ref_bytes_path = datapath/'ladder.rlew_compress.bin'
    dat_bytes = read_bytes(dat_bytes_path)
    out_bytes = rlew_compress(dat_bytes, RLEW_TAG)
    write_bytes(out_bytes_path, out_bytes)
    ref_bytes = read_bytes(ref_bytes_path)
    assert out_bytes == ref_bytes


# ----------------------------------------------------------------------------

def test_rlew_expand__empty(temppath: Path, datapath: Path):
    dat_bytes_path = datapath/'empty.rlew_compress.bin'
    out_bytes_path = temppath/'empty.rlew_expand.bin'
    ref_bytes_path = datapath/'empty.bin'
    dat_bytes = read_bytes(dat_bytes_path)
    out_bytes = rlew_expand(dat_bytes, RLEW_TAG)
    write_bytes(out_bytes_path, out_bytes)
    ref_bytes = read_bytes(ref_bytes_path)
    assert out_bytes == ref_bytes


def test_rlew_expand__zeros(temppath: Path, datapath: Path):
    dat_bytes_path = datapath/'zeros.rlew_compress.bin'
    out_bytes_path = temppath/'zeros.rlew_expand.bin'
    ref_bytes_path = datapath/'zeros.bin'
    dat_bytes = read_bytes(dat_bytes_path)
    out_bytes = rlew_expand(dat_bytes, RLEW_TAG)
    write_bytes(out_bytes_path, out_bytes)
    ref_bytes = read_bytes(ref_bytes_path)
    assert out_bytes == ref_bytes


def test_rlew_expand__bytes(temppath: Path, datapath: Path):
    dat_bytes_path = datapath/'bytes.rlew_compress.bin'
    out_bytes_path = temppath/'bytes.rlew_expand.bin'
    ref_bytes_path = datapath/'bytes.bin'
    dat_bytes = read_bytes(dat_bytes_path)
    out_bytes = rlew_expand(dat_bytes, RLEW_TAG)
    write_bytes(out_bytes_path, out_bytes)
    ref_bytes = read_bytes(ref_bytes_path)
    assert out_bytes == ref_bytes


def test_rlew_expand__ladder(temppath: Path, datapath: Path):
    dat_bytes_path = datapath/'ladder.rlew_compress.bin'
    out_bytes_path = temppath/'ladder.rlew_expand.bin'
    ref_bytes_path = datapath/'ladder.bin'
    dat_bytes = read_bytes(dat_bytes_path)
    out_bytes = rlew_expand(dat_bytes, RLEW_TAG)
    write_bytes(out_bytes_path, out_bytes)
    ref_bytes = read_bytes(ref_bytes_path)
    assert out_bytes == ref_bytes
