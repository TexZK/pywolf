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

import importlib.util
import io
import os
import struct
from importlib import import_module
from typing import Any
from typing import Iterator
from typing import Sequence

from .base import stream_fit as _stream_fit


def load_as_module(module_name, path):
    if os.path.exists(path):
        spec = importlib.util.spec_from_file_location(module_name, path)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
    else:
        module = import_module(path)
    return module


def is_in_partition(index, *partitions):
    for partition in partitions:
        start, count = partition
        if start <= index < (start + count):
            return True
    return False


def find_partition(index, partition_map, count_sign=1, cache=None):
    found = None
    if cache is not None:
        found = cache.get(index)

    if found is None:
        if count_sign > 0:
            maximum = 0
            found = None
            for key, value in partition_map.items():
                start, count = value
                if start <= index < (start + count) and maximum < count:
                    maximum = count
                    found = key

        elif count_sign < 0:
            maximum = 0
            found = None
            for key, value in partition_map.items():
                start, count = value
                if start <= index < (start + count) and -count < maximum:
                    maximum = -count
                    found = key

        else:
            for key, value in partition_map.items():
                start, count = value
                if start <= index < (start + count):
                    found = key

    if found is None:
        raise ValueError(index)

    if cache is not None:
        cache[index] = found
    return found


stream_fit = _stream_fit  # alias


def stream_unpack(  # TODO remove
    fmt: str,
    stream: io.BufferedReader,
) -> Sequence[Any]:

    chunk = stream.read(struct.calcsize(fmt))
    return struct.unpack(fmt, chunk)


def stream_unpack_array(  # TODO remove
    fmt: str,
    stream: io.BufferedReader,
    count: int,
    scalar: bool = True
) -> Iterator[Any]:

    if scalar:
        yield from (stream_unpack(fmt, stream)[0] for _ in range(count))
    else:
        yield from (stream_unpack(fmt, stream) for _ in range(count))
