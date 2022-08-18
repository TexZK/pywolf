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
import os
import struct
import subprocess
import tempfile
import wave
from typing import ByteString
from typing import Iterable
from typing import Iterator
from typing import List
from typing import Optional
from typing import Sequence
from typing import Tuple
from typing import cast as _cast

from .archives import AudioArchiveReader
from .archives import ResourceLibrary
from .archives import VswapArchiveReader
from .base import Cache
from .base import Chunk
from .base import Codec
from .base import Index
from .base import Offset
from .utils import ResourceManager


# (reg_index, reg_value, pre_delay)
AdLibEvent = Tuple[int, int, int]


ADLIB_CARRIERS   = ( 3,  4,  5, 11, 12, 13, 19, 20, 21)
ADLIB_MODULATORS = ( 0,  1,  2,  8,  9, 10, 16, 17, 18)

ADLIB_REG_DUMMY     = 0x00
ADLIB_REG_SPLIT     = 0x08
ADLIB_REG_CHAR      = 0x20
ADLIB_REG_SCALE     = 0x40
ADLIB_REG_ATTACK    = 0x60
ADLIB_REG_SUSTAIN   = 0x80
ADLIB_REG_FREQ_L    = 0xA0
ADLIB_REG_FREQ_H    = 0xB0
ADLIB_REG_FEEDBACK  = 0xC0
ADLIB_REG_EFFECTS   = 0xBD
ADLIB_REG_WAVE      = 0xE0


def samples_upsample_zoh(
    samples: Iterable[int],
    factor: float,
) -> Iterator[int]:

    if factor < 1:
        raise ValueError('shrinking scale factor')
    remainder = 0

    for sample in samples:
        times = factor + remainder
        times_floor = int(times)
        for _ in range(times_floor):
            yield sample
        remainder = times - times_floor


def wave_write(
    file_path: str,
    rate: int,
    samples: ByteString,
    sample_format: str = '<B',
) -> None:

    with wave.open(file_path, 'w') as wave_stream:
        wave_stream.setnchannels(1)
        wave_stream.setsampwidth(struct.calcsize(sample_format))
        wave_stream.setframerate(rate)
        wave_stream.setnframes(len(samples))
        wave_stream.writeframesraw(samples)  # FIXME: pack into bytes() if necessary


class SquareWaveGenerator:

    def __init__(
        self,
        sample_rate: int,
        high: int = 1,
        low: int = -1,
        silence: int = 0,
        frequency: float = 0,
        duty_cycle: float = 0.5,
        round_period: bool = True,
    ):
        if sample_rate <= 0:
            raise ValueError('invalid sample rate')
        if frequency <= 0:
            raise ValueError('invalid frequency')
        if not 0 <= duty_cycle <= 1:
            raise ValueError('invalid duty cycle')

        self.sample_rate: int = sample_rate
        self.low: int = low
        self.high: int = high
        self.silence: int = silence
        self.frequency: float = frequency
        self.duty_cycle: float = duty_cycle
        self.round_period: bool = round_period

        self.period_length = 1
        self.phase_index = 0
        self.threshold_index = self.duty_cycle

        self.reset()

    def reset(self) -> None:
        self.period_length = 1
        self.phase_index = 0
        self.threshold_index = self.duty_cycle

        self.set_frequency(self.frequency)

    def set_frequency(self, frequency: float) -> None:
        if frequency != self.frequency:
            phase_index = self.phase_index

            if frequency > 0:
                assert 0 < frequency < 2 * self.sample_rate
                period_length = self.sample_rate / frequency
                phase_index *= period_length / self.period_length
                if self.round_period:
                    period_length = round(period_length)
                    phase_index = int(phase_index)
                phase_index %= period_length
            else:
                period_length = 1
                phase_index = 0

            self.frequency = frequency
            self.phase_index = phase_index
            self.period_length = period_length

            self.set_duty_cycle(self.duty_cycle)

    def set_duty_cycle(self, duty_cycle: float) -> None:
        if not 0 <= duty_cycle <= 1:
            raise ValueError('invalid duty cycle')

        threshold_index = self.period_length * duty_cycle
        if self.round_period:
            threshold_index = round(threshold_index)

        self.duty_cycle = duty_cycle
        self.threshold_index = threshold_index

    def __call__(self, sample_count: int = 1) -> Iterator[int]:
        if self.frequency > 1:  # silence below 1 Hz
            high = self.high
            low = self.low
            period_length = self.period_length
            phase_index = self.phase_index
            threshold_index = self.threshold_index

            for _ in range(sample_count):
                yield high if phase_index < threshold_index else low
                phase_index = (phase_index + 1) % period_length

            self.phase_index = phase_index
        else:
            silence = self.silence
            for _ in range(sample_count):
                yield silence


def buzzer_expand(
    dividers: Sequence[int],
    sample_rate: int = 44100,
    command_rate: int = 140,
    buzzer_clock: int = 1193180,
    round_period: bool = True,
) -> Iterator[int]:

    generator = SquareWaveGenerator(sample_rate, high=0xFF, low=0x00, silence=0x80,
                                    round_period=round_period)
    delay = sample_rate / command_rate
    offset = 0
    divider_last = -1  # invalid

    for divider in dividers:
        if divider != divider_last:
            generator.set_frequency(buzzer_clock / (divider * 60) if divider else 0)
        divider_last = divider
        length = offset + delay
        length_floor = round(length)
        yield from generator(length_floor)
        offset = length - length_floor


def convert_imf_to_wave(
    imf_chunk,
    imf2wav_path: str,
    wave_path: Optional[str] = None,
    wave_rate: int = 44100,
    imf_rate: int = 700,
    chunk_path: Optional[str] = None,
) -> str:

    wave_is_temporary = wave_path is None
    chunk_is_temporary = chunk_path is None
    tempdir_path = tempfile.gettempdir()
    PIPE = subprocess.PIPE

    try:
        if chunk_is_temporary:
            with tempfile.NamedTemporaryFile('wb', delete=False) as chunk_file:
                chunk_file.write(imf_chunk)
                chunk_path = os.path.join(tempdir_path, chunk_file.name)
        else:
            with open(chunk_path, 'wb') as chunk_file:
                chunk_file.write(imf_chunk)

        if wave_is_temporary:
            with tempfile.NamedTemporaryFile('wb', delete=False) as wave_file:
                wave_path = os.path.join(tempdir_path, wave_file.name)
        else:
            wave_path = os.path.abspath(wave_path)

        imf2wav_path = os.path.abspath(imf2wav_path)
        args = [imf2wav_path, chunk_path, wave_path, str(imf_rate), str(wave_rate)]
        subprocess.Popen(args, shell=True, stdin=PIPE, stdout=PIPE, stderr=PIPE).communicate()

    except:
        if wave_is_temporary:
            try:
                os.unlink(wave_path)
            except:
                pass
        raise

    finally:
        if chunk_is_temporary:
            try:
                os.unlink(chunk_path)
            except:
                pass

    return wave_path


def convert_wave_to_ogg(
    wave_path: str,
    oggenc2_path: str,
    ogg_path: Optional[str] = None,
) -> str:

    ogg_is_temporary = ogg_path is None
    tempdir_path = tempfile.gettempdir()
    PIPE = subprocess.PIPE

    try:
        if ogg_is_temporary:
            with tempfile.NamedTemporaryFile('wb', delete=False) as ogg_file:
                ogg_path = os.path.join(tempdir_path, ogg_file.name)
        else:
            ogg_path = os.path.abspath(ogg_path)

        oggenc2_path = os.path.abspath(oggenc2_path)
        args = [oggenc2_path, wave_path, '-o', ogg_path]
        subprocess.Popen(args, shell=True, stdin=PIPE, stdout=PIPE, stderr=PIPE).communicate()

    except:
        if ogg_is_temporary:
            try:
                os.unlink(ogg_path)
            except:
                pass
        raise

    return ogg_path


class BuzzerSound:

    def __init__(
        self,
        dividers: Sequence[int],
    ):
        self.dividers: Sequence[int] = dividers

    def __len__(self) -> int:
        return len(self.dividers)

    def __iter__(self) -> Iterator[int]:
        yield from self.dividers

    def to_samples(self, rate: int = 44100) -> Iterator[int]:
        yield from buzzer_expand(self.dividers, rate)

    def wave_write(self, file_path: str, rate: int = 44100):
        samples = bytes(self.to_samples(rate))
        wave_write(file_path, rate, samples)


class BuzzerSoundManager(ResourceManager):

    def __init__(self, chunks_handler, start=None, count=None):
        super().__init__(chunks_handler, start, count)

    def _load_resource(self, index, chunk):
        instance = BuzzerSound(chunk)
        return instance


class BuzzerSoundLibrary(ResourceLibrary[Index, BuzzerSound]):

    def _get_resource(self, index: Index, chunk: Chunk) -> BuzzerSound:
        del index
        instance = BuzzerSound(chunk)
        return instance


class AdLibSoundHeader(Codec):

    def __init__(
        self,
        length : int,
        priority : int,
        modulator_char : int,
        carrier_char : int,
        modulator_scale : int,
        carrier_scale : int,
        modulator_attack : int,
        carrier_attack : int,
        modulator_sustain : int,
        carrier_sustain : int,
        modulator_wave : int,
        carrier_wave : int,
        conn : int,
        voice : int,
        mode : int,
        block : int,
        padding: bytes = b'\0\0\0',
    ):
        self.length            : int = length
        self.priority          : int = priority
        self.modulator_char    : int = modulator_char
        self.carrier_char      : int = carrier_char
        self.modulator_scale   : int = modulator_scale
        self.carrier_scale     : int = carrier_scale
        self.modulator_attack  : int = modulator_attack
        self.carrier_attack    : int = carrier_attack
        self.modulator_sustain : int = modulator_sustain
        self.carrier_sustain   : int = carrier_sustain
        self.modulator_wave    : int = modulator_wave
        self.carrier_wave      : int = carrier_wave
        self.conn              : int = conn
        self.voice             : int = voice
        self.mode              : int = mode
        self.block             : int = block
        self.padding: bytes = padding

    @classmethod
    def calcsize_stateless(cls) -> Offset:
        return struct.calcsize('<LH13B3sB')

    def to_bytes(self) -> bytes:
        return struct.pack('<LH13B3sB',
                           self.length,
                           self.priority,
                           self.modulator_char,
                           self.carrier_char,
                           self.modulator_scale,
                           self.carrier_scale,
                           self.modulator_attack,
                           self.carrier_attack,
                           self.modulator_sustain,
                           self.carrier_sustain,
                           self.modulator_wave,
                           self.carrier_wave,
                           self.conn,
                           self.voice,
                           self.mode,
                           self.padding,
                           self.block)

    @classmethod
    def from_bytes(cls, buffer: ByteString, offset: Offset = 0) -> Tuple['AdLibSoundHeader', Offset]:
        offset = int(offset)
        args = struct.unpack_from('<LH13B3sB', buffer, offset)
        offset += struct.calcsize('<LH13B3sB')
        return cls(*args), offset

    def to_imf_chunk(
        self,
        length: Optional[int] = None,
        channel: int = 0,
        old_muse_compatibility: bool = False,
    ) -> bytes:

        if length is None:
            length = self.length
        if length < 0:
            raise ValueError('negative length')
        if not 0 <= channel < 9:
            raise ValueError('invalid channel')

        modulator = ADLIB_MODULATORS[channel]
        carrier = ADLIB_CARRIERS[channel]
        setup_events = [
            [ADLIB_REG_DUMMY,   0x00, 0],
            [ADLIB_REG_EFFECTS, 0x00, 0],
            [ADLIB_REG_SPLIT,   0x00, 0],

            [(ADLIB_REG_FREQ_H  + modulator), 0x00,                   0],
            [(ADLIB_REG_CHAR    + modulator), self.modulator_char,    0],
            [(ADLIB_REG_SCALE   + modulator), self.modulator_scale,   0],
            [(ADLIB_REG_ATTACK  + modulator), self.modulator_attack,  0],
            [(ADLIB_REG_SUSTAIN + modulator), self.modulator_sustain, 0],
            [(ADLIB_REG_WAVE    + modulator), self.modulator_wave,    0],

            [(ADLIB_REG_CHAR    + carrier), self.carrier_char,    0],
            [(ADLIB_REG_SCALE   + carrier), self.carrier_scale,   0],
            [(ADLIB_REG_ATTACK  + carrier), self.carrier_attack,  0],
            [(ADLIB_REG_SUSTAIN + carrier), self.carrier_sustain, 0],
            [(ADLIB_REG_WAVE    + carrier), self.carrier_wave,    0],

            [ADLIB_REG_FEEDBACK, (self.conn if old_muse_compatibility else 0x00), 0],
        ]

        size = (len(setup_events) + length) * struct.calcsize('<BBH')
        setup_events_chunks = [struct.pack('<BBH', *event) for event in setup_events]
        return b''.join([struct.pack('<H', size)] + setup_events_chunks)


class AdLibSound(Codec):

    def __init__(
        self,
        header: AdLibSoundHeader,
        events: Sequence[AdLibEvent],
    ):
        self.header: AdLibSoundHeader = header
        self.events: Sequence[AdLibEvent] = events

    def __len__(self) -> int:
        return self.header.length

    def __iter__(self) -> Iterator[AdLibEvent]:
        yield from self.events

    @classmethod
    def calcsize_stateless(cls, events_count: int = 0) -> Offset:
        if events_count < 0:
            raise ValueError('negative events count')
        return AdLibSoundHeader.calcsize_stateless() + (events_count * 4)

    def to_bytes(self) -> bytes:
        chunks = [self.header.to_bytes()]
        chunks.extend(struct.pack('<BBH', *event) for event in self.events)
        chunk = b''.join(chunks)
        return chunk

    @classmethod
    def from_bytes(cls, buffer: ByteString, offset: Offset = 0) -> Tuple['AdLibSound', Offset]:
        offset = int(offset)
        header, offset = AdLibSoundHeader.from_bytes(buffer, offset)
        events: List[Tuple[int, int, int]] = []

        for _ in range(header.length):
            event = struct.unpack_from('<BBH', buffer, offset)
            offset += 4
            event = _cast(AdLibEvent, event)
            events.append(event)

        instance = cls(header, events)
        return instance, offset

    @classmethod
    def from_stream(cls, stream: io.BufferedReader) -> 'AdLibSound':
        size = cls.calcsize_stateless()
        chunk = stream.read(size)
        instance, _ = cls.from_bytes(chunk)
        return instance

    def to_imf_chunk(
        self,
        delay_cycles: int = 5,
        channel: int = 0,
        old_muse_compatibility: bool = False,
    ) -> bytes:

        events = self.events
        header = self.header
        events_chunks = []

        if events:
            modulator = ADLIB_MODULATORS[channel]
            freq_l_reg = ADLIB_REG_FREQ_L + modulator
            freq_h_reg = ADLIB_REG_FREQ_H + modulator
            block = ((header.block & 7) << 2) | 0x20
            key_on_data = struct.pack('<BBH', freq_h_reg, block, delay_cycles)
            key_off_data = struct.pack('<BBH', freq_h_reg, 0x00, delay_cycles)

            for event in events:
                if event:
                    events_chunks.append(struct.pack('<BBH', freq_l_reg, event, 0))
                    events_chunks.append(key_on_data)
                else:
                    events_chunks.append(key_off_data)
            events_chunks.append(key_off_data)

        chunks = [header.to_imf_chunk(len(events_chunks), channel, old_muse_compatibility)]
        chunks.extend(events_chunks)
        chunk = b''.join(chunks)
        return chunk


class AdLibSoundManager(ResourceManager):

    def __init__(self, chunks_handler, start=None, count=None, old_muse_compatibility=False):
        super().__init__(chunks_handler, start, count)
        self.old_muse_compatibility = old_muse_compatibility

    def _load_resource(self, index, chunk):
        instance, _ = AdLibSound.from_bytes(chunk)
        return instance


class AdLibSoundLibrary(ResourceLibrary[Index, AdLibSound]):

    def __init__(
        self,
        audio_archive: AudioArchiveReader,
        resource_cache: Optional[Cache[Index, AdLibSound]] = None,
        start: Optional[Index] = None,
        count: Optional[Index] = None,
    ):
        super().__init__(
            audio_archive,
            resource_cache=resource_cache,
            start=start,
            count=count,
        )

    def _get_resource(self, index: Index, chunk: Chunk) -> AdLibSound:
        del index
        instance, _ = AdLibSound.from_bytes(chunk)
        return instance


class Music(Codec):

    def __init__(
        self,
        events: Sequence[AdLibEvent],
    ):
        self.events: Sequence[AdLibEvent] = events

    def __len__(self) -> int:
        return len(self.events)

    def __iter__(self) -> Iterator[AdLibEvent]:
        yield from self.events

    @classmethod
    def calcsize_stateless(cls, events_count: int = 0) -> Offset:
        if events_count < 0:
            raise ValueError('negative events count')
        return events_count * 4

    def to_bytes(self) -> bytes:
        return self.to_imf_chunk()

    @classmethod
    def from_bytes(cls, buffer: ByteString, offset: Offset = 0) -> Tuple['Music', Offset]:
        offset = int(offset)
        length, = struct.unpack_from('<H', buffer, offset)
        offset += 2
        if length % 4:
            raise ValueError('length must be divisible by 4')
        length //= 4
        events: List[AdLibEvent] = []

        for _ in range(length):
            event = struct.unpack_from('<BBH', buffer, offset)
            offset += 4
            event = _cast(AdLibEvent, event)
            events.append(event)

        instance = cls(events)
        return instance, offset

    @classmethod
    def from_stream(cls, stream: io.BufferedReader) -> 'Music':
        buffer = stream.read(2)
        length, = struct.unpack('<H', buffer)
        buffer += stream.read(length * 4)
        instance, _ = cls.from_bytes(buffer)
        return instance

    def to_imf_chunk(self):
        length = len(self.events) * 4
        events_data = [struct.pack('<BBH', *event) for event in self.events]
        chunk = b''.join([struct.pack('<H', length)] + events_data)
        return chunk


class MusicManager(ResourceManager):

    def __init__(self, chunks_handler, start=None, count=None):
        super().__init__(chunks_handler, start, count)

    def _load_resource(self, index, chunk):
        return Music.from_bytes(chunk)


class MusicLibrary(ResourceLibrary[Index, Music]):

    def __init__(
        self,
        audio_archive: AudioArchiveReader,
        resource_cache: Optional[Cache[Index, Music]] = None,
        start: Optional[Index] = None,
        count: Optional[Index] = None,
    ):
        super().__init__(
            audio_archive,
            resource_cache=resource_cache,
            start=start,
            count=count,
        )

    def _get_resource(self, index: Index, chunk: Chunk) -> Music:
        del index
        instance, _ = Music.from_bytes(chunk)
        return instance


class SampledSound:

    def __init__(
        self,
        rate: int,
        samples: Sequence[int],
    ):
        self.rate: int = rate
        self.samples: Sequence[int] = samples

    def wave_write(self, file_path: str) -> None:
        wave_write(file_path, self.rate, bytes(self.samples))


class SampledSoundManager(ResourceManager):

    def __init__(self, chunks_handler, rate, start=None, count=None):
        super().__init__(chunks_handler, start, count)
        self.rate = rate

    def _load_resource(self, index, chunk):
        samples = bytes(samples_from_vswap(self._chunks_handler, index))
        return SampledSound(self.rate, samples)


class SampledSoundLibrary(ResourceLibrary[Index, SampledSound]):

    def __init__(
        self,
        vswap_archive: VswapArchiveReader,
        sample_rate: int,
        resource_cache: Optional[Cache[Index, SampledSound]] = None,
        start: Optional[Index] = None,
        count: Optional[Index] = None,
    ):
        if sample_rate < 1:
            raise ValueError('invalid sample rate')

        super().__init__(
            vswap_archive,
            resource_cache=resource_cache,
            start=start,
            count=count,
        )
        self._sample_rate: int = sample_rate

    def _get_resource(self, index: Index, chunk: Chunk) -> SampledSound:
        del chunk
        vswap_archive = _cast(VswapArchiveReader, self._archive)
        samples = bytes(vswap_archive.iterate_sampled_sound(index))
        instance = SampledSound(self._sample_rate, samples)
        return instance
