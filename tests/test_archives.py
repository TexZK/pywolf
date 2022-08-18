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
from typing import Mapping
from typing import Optional
from typing import Union

import pywolf.configs.wl6 as wl6
from pywolf.audio import AudioArchiveReader
from pywolf.game import MapArchiveReader
from pywolf.graphics import GraphicsArchiveReader
from pywolf.graphics import VswapArchiveReader

DEFAULT_CHECKSUM_OPTION: bool = True


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


@pytest.fixture(scope='module')
def checksum_option():
    value = os.environ.get('DO_CHECK_CHECKSUM', str(DEFAULT_CHECKSUM_OPTION))
    value = value.strip().lower()
    matches = ('true', '1', 't', 'y', 'yes')
    return value in matches


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


def read_md5_list(
    path: Path,
) -> Optional[Mapping[str, str]]:

    checksums = {}
    with open(str(path), 'rt') as stream:
        for line in stream:
            checksum, filename = line.split(':')
            filename = filename.strip()
            checksums[filename] = checksum
    return checksums


# ============================================================================

def test_audio_export(
    temppath: Path,
    datapath: Path,
    assetspath: Path,
    checksum_option: bool,
):
    data_path = assetspath/'AUDIOT.WL6'
    header_path = assetspath/'AUDIOHED.WL6'
    md5_list = read_md5_list(datapath/'audio.md5')

    with open(data_path, 'rb') as data_stream:
        with open(header_path, 'rb') as header_stream:
            archive = AudioArchiveReader()

            archive.open(
                data_stream=data_stream,
                header_stream=header_stream,
            )
            if checksum_option:
                assert len(archive) == len(md5_list)

            for index, chunk in enumerate(archive):
                filename = f'audio_{index:05d}.chunk'
                out_path = datapath/filename
                out_path.write_bytes(chunk)

                if checksum_option:
                    md5_value = hashlib.md5(chunk).hexdigest()
                    assert md5_value == md5_list[filename]

            archive.close()


# ----------------------------------------------------------------------------

def test_graphics_export(
    temppath: Path,
    datapath: Path,
    assetspath: Path,
    checksum_option: bool,
):
    data_path = assetspath/'VGAGRAPH.WL6'
    header_path = assetspath/'VGAHEAD.WL6'
    huffman_path = assetspath/'VGADICT.WL6'
    md5_list = read_md5_list(datapath/'graphics.md5')

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
                if checksum_option:
                    assert len(archive) == len(md5_list)

                for index, chunk in enumerate(archive):
                    filename = f'graphics_{index:05d}.chunk'
                    out_path = datapath/filename
                    out_path.write_bytes(chunk)

                    if checksum_option:
                        md5_value = hashlib.md5(chunk).hexdigest()
                        assert md5_value == md5_list[filename]

                archive.close()


# ----------------------------------------------------------------------------

def test_map_export(
    temppath: Path,
    datapath: Path,
    assetspath: Path,
    checksum_option: bool,
):
    data_path = assetspath/'GAMEMAPS.WL6'
    header_path = assetspath/'MAPHEAD.WL6'
    md5_list = read_md5_list(datapath/'map.md5')

    with open(data_path, 'rb') as data_stream:
        with open(header_path, 'rb') as header_stream:
            archive = MapArchiveReader()

            archive.open(
                data_stream=data_stream,
                header_stream=header_stream,
            )
            if checksum_option:
                assert len(archive) == len(md5_list)

            for index, chunk in enumerate(archive):
                filename = f'map_{index:05d}.chunk'
                out_path = datapath/filename
                out_path.write_bytes(chunk)

                if checksum_option:
                    md5_value = hashlib.md5(chunk).hexdigest()
                    assert md5_value == md5_list[filename]

            archive.close()


# ----------------------------------------------------------------------------

def test_vswap_export(
    temppath: Path,
    datapath: Path,
    assetspath: Path,
    checksum_option: bool,
):
    data_path = assetspath/'VSWAP.WL6'
    md5_list = read_md5_list(datapath/'vswap.md5')

    with open(data_path, 'rb') as data_stream:
        archive = VswapArchiveReader()

        archive.open(
            data_stream=data_stream,
        )
        if checksum_option:
            assert len(archive) == len(md5_list)

        for index, chunk in enumerate(archive):
            filename = f'vswap_{index:05d}.chunk'
            out_path = datapath/filename
            out_path.write_bytes(chunk)

            if checksum_option:
                md5_value = hashlib.md5(chunk).hexdigest()
                assert md5_value == md5_list[filename]

        archive.close()
