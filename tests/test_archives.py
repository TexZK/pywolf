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
import hashlib
import os

import pytest
from pathlib import Path
from typing import Union

import pywolf.configs.wl6 as wl6
from pywolf.audio import AudioArchiveReader
from pywolf.game import MapArchiveReader
from pywolf.graphics import GraphicsArchiveReader
from pywolf.graphics import VswapArchiveReader


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


@pytest.fixture
def assetspath(datadir):
    return Path(str(datadir))/'..'/'assets'


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


# ============================================================================

def test_audio_export(temppath: Path, datapath: Path, assetspath: Path):
    data_path = assetspath/'AUDIOT.WL6'
    header_path = assetspath/'AUDIOHED.WL6'

    with open(data_path, 'rb') as data_stream:
        with open(header_path, 'rb') as header_stream:
            archive = AudioArchiveReader()

            archive.open(
                data_stream=data_stream,
                header_stream=header_stream,
            )

            for index, chunk in enumerate(archive):
                out_path = datapath/f'audio_{index:05d}.chunk'
                with open(str(out_path), 'wb') as out_stream:
                    out_stream.write(chunk)

            archive.close()


# ----------------------------------------------------------------------------

def test_graphics_export(temppath: Path, datapath: Path, assetspath: Path):
    data_path = assetspath/'VGAGRAPH.WL6'
    header_path = assetspath/'VGAHEAD.WL6'
    huffman_path = assetspath/'VGADICT.WL6'

    with open(data_path, 'rb') as data_stream:
        with open(header_path, 'rb') as header_stream:
            with open(huffman_path, 'rb') as huffman_stream:
                archive = GraphicsArchiveReader()

                archive.open(
                    data_stream=data_stream,
                    header_stream=header_stream,
                    huffman_stream=huffman_stream,
                    partition_map=wl6.GRAPHICS_PARTITIONS_MAP,
                )

                for index, chunk in enumerate(archive):
                    out_path = datapath/f'graphics_{index:05d}.chunk'
                    with open(str(out_path), 'wb') as out_stream:
                        out_stream.write(chunk)

                    md5_path = datapath/f'graphics_{index:05d}.md5'
                    with open(str(md5_path), 'rt') as md5_stream:
                        md5_expected = md5_stream.readline().strip()
                    md5_actual = hashlib.md5(chunk).hexdigest()
                    assert md5_actual == md5_expected

                archive.close()


# ----------------------------------------------------------------------------

def test_map_export(temppath: Path, datapath: Path, assetspath: Path):
    data_path = assetspath/'GAMEMAPS.WL6'
    header_path = assetspath/'MAPHEAD.WL6'

    with open(data_path, 'rb') as data_stream:
        with open(header_path, 'rb') as header_stream:
            archive = MapArchiveReader()

            archive.open(
                data_stream=data_stream,
                header_stream=header_stream,
            )

            for index, chunk in enumerate(archive):
                out_path = datapath/f'map_{index:05d}.chunk'
                with open(str(out_path), 'wb') as out_stream:
                    out_stream.write(chunk)

            archive.close()


# ----------------------------------------------------------------------------

def test_vswap_export(temppath: Path, datapath: Path, assetspath: Path):
    data_path = assetspath/'VSWAP.WL6'

    with open(data_path, 'rb') as data_stream:
        archive = VswapArchiveReader()

        archive.open(
            data_stream=data_stream,
        )

        for index, chunk in enumerate(archive):
            out_path = datapath/f'vswap_{index:05d}.chunk'
            with open(str(out_path), 'wb') as out_stream:
                out_stream.write(chunk)

        archive.close()
