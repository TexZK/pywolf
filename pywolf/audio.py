import io
import os
import struct
import subprocess
import tempfile
import wave

from .utils import (
    stream_read, stream_write,
    stream_pack, stream_unpack, stream_unpack_array,
    BinaryResource, ResourceManager
)


ADLIB_CARRIERS = (3, 4, 5, 11, 12, 13, 19, 20, 21)
ADLIB_MODULATORS = (0, 1, 2, 8, 9, 10, 16, 17, 18)

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


def samples_expand(chunks_handler, index):
    sounds_start = chunks_handler.sounds_start
    sounds_infos = chunks_handler.sounds_infos
    start, length = sounds_infos[index]

    chunk_index = sounds_start + start
    remaining = length
    while remaining:
        chunk = chunks_handler[chunk_index]
        if len(chunk) <= remaining:
            yield from chunk
            remaining -= len(chunk)
        else:
            yield from memoryview(chunk)[:remaining]
            remaining = 0
        chunk_index += 1


def samples_upsample(samples, factor):
    assert 1 < factor
    remainder = 0
    for sample in samples:
        times = factor + remainder
        times_floor = int(times)
        yield from (sample for _ in range(times_floor))
        remainder = times - times_floor


def wave_write(file, rate, samples, sample_format='<B'):
    with wave.open(file, 'w') as wave_stream:
        wave_stream.setnchannels(1)
        wave_stream.setsampwidth(struct.calcsize(sample_format))
        wave_stream.setframerate(rate)
        wave_stream.setnframes(len(samples))
        wave_stream.writeframesraw(samples)  # FIXME: pack into bytes() if necessary


class SquareWaveGenerator(object):

    def __init__(self, sample_rate, high=1, low=-1, silence=0, frequency=0, duty_cycle=0.5, round_period=True):
        assert 0 < sample_rate

        self.sample_rate = sample_rate
        self.low = low
        self.high = high
        self.silence = silence
        self.frequency = 0
        self.duty_cycle = duty_cycle
        self.round_period = round_period

        self.reset()

    def reset(self):
        self.period_length = 1
        self.phase_index = 0
        self.threshold_index = self.duty_cycle

        self.set_frequency(self.frequency)

    def set_frequency(self, frequency):
        if frequency != self.frequency:
            phase_index = self.phase_index

            if frequency:
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

    def set_duty_cycle(self, duty_cycle):
        assert 0 <= duty_cycle <= 1
        threshold_index = self.period_length * duty_cycle
        if self.round_period:
            threshold_index = round(threshold_index)

        self.duty_cycle = duty_cycle
        self.threshold_index = threshold_index

    def __call__(self, length=1):
        if self.frequency:
            high = self.high
            low = self.low
            period_length = self.period_length
            phase_index = self.phase_index
            threshold_index = self.threshold_index

            for _ in range(length):
                yield high if phase_index < threshold_index else low
                phase_index = (phase_index + 1) % period_length

            self.phase_index = phase_index
        else:
            silence = self.silence
            yield from (silence for _ in range(length))


def buzzer_expand(dividers, sample_rate=44100, char_rate=140, buzzer_clock=1193180, round_period=True):
    generator = SquareWaveGenerator(sample_rate, high=0xFF, low=0x00, silence=0x80, round_period=round_period)
    char_length = sample_rate / char_rate
    offset = 0

    for divider in dividers:
        generator.set_frequency(buzzer_clock / (divider * 60) if divider else 0)
        length = offset + char_length
        length_floor = round(length)
        yield from generator(length_floor)
        offset = length - length_floor


def convert_imf_to_wave(imf_chunk, imf2wav_path, wave_path=None, wave_rate=44100, imf_rate=700, chunk_path=None):
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


def convert_wave_to_ogg(wave_path, oggenc2_path, ogg_path=None):
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


class BuzzerSound(object):

    def __init__(self, dividers):
        self.dividers = dividers

    def __len__(self):
        return len(self.dividers)

    def __iter__(self):
        yield from self.dividers

    def __getitem__(self, key):
        return self.dividers[key]

    def to_samples(self, rate=44100):
        yield from buzzer_expand(self.dividers, rate)

    def wave_write(self, file, rate=44100):
        samples = bytes(self.to_samples(rate))
        wave_write(file, rate, samples)


class BuzzerSoundManager(ResourceManager):

    def __init__(self, chunks_handler, start=None, count=None):
        super().__init__(chunks_handler, start, count)

    def _build_resource(self, index, chunk):
        return BuzzerSound(chunk)


class AdLibSoundHeader(BinaryResource):

    SIZE = struct.calcsize('<LH13B3sB')

    def __init__(self,
                 length, priority,
                 modulator_char, carrier_char,
                 modulator_scale, carrier_scale,
                 modulator_attack, carrier_attack,
                 modulator_sustain, carrier_sustain,
                 modulator_wave, carrier_wave,
                 conn, voice, mode, block):
        self.length            = length
        self.priority          = priority
        self.modulator_char    = modulator_char
        self.carrier_char      = carrier_char
        self.modulator_scale   = modulator_scale
        self.carrier_scale     = carrier_scale
        self.modulator_attack  = modulator_attack
        self.carrier_attack    = carrier_attack
        self.modulator_sustain = modulator_sustain
        self.carrier_sustain   = carrier_sustain
        self.modulator_wave    = modulator_wave
        self.carrier_wave      = carrier_wave
        self.conn              = conn
        self.voice             = voice
        self.mode              = mode
        self.block             = block

    @classmethod
    def from_stream(cls, stream):
        args = list(stream_unpack('<LH13B', stream))
        stream_unpack('<3B', stream)  # unused
        args += stream_unpack('<B', stream)
        return cls(*args)

    def to_stream(self, stream):
        stream_write(stream, self.to_bytes())

    @classmethod
    def from_bytes(cls, data, offset=0):
        args = struct.unpack_from('<LH13B', data, offset)
        offset += struct.calcsize('<LH13B3s')
        args += stream_unpack('<B', data, offset)
        return cls(*args)

    def to_bytes(self):
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
                           b'',
                           self.block)

    def to_imf_chunk(self, length=None, which=0, old_muse_compatibility=False):
        modulator = ADLIB_MODULATORS[which]
        carrier = ADLIB_CARRIERS[which]

        setup_events = [
            [ADLIB_REG_DUMMY, 0x00, 0],
            [ADLIB_REG_EFFECTS, 0x00, 0],
            [ADLIB_REG_SPLIT, 0x00, 0],

            [(ADLIB_REG_FREQ_H  + modulator), 0x00, 0],
            [(ADLIB_REG_CHAR    + modulator), self.modulator_char, 0],
            [(ADLIB_REG_SCALE   + modulator), self.modulator_scale, 0],
            [(ADLIB_REG_ATTACK  + modulator), self.modulator_attack, 0],
            [(ADLIB_REG_SUSTAIN + modulator), self.modulator_sustain, 0],
            [(ADLIB_REG_WAVE    + modulator), self.modulator_wave, 0],

            [(ADLIB_REG_CHAR    + carrier), self.carrier_char, 0],
            [(ADLIB_REG_SCALE   + carrier), self.carrier_scale, 0],
            [(ADLIB_REG_ATTACK  + carrier), self.carrier_attack, 0],
            [(ADLIB_REG_SUSTAIN + carrier), self.carrier_sustain, 0],
            [(ADLIB_REG_WAVE    + carrier), self.carrier_wave, 0],

            [ADLIB_REG_FEEDBACK, (self.conn if old_muse_compatibility else 0x00), 0],
        ]

        if length is None:
            length = self.length
        length = (len(setup_events) + length) * struct.calcsize('<BBH')
        setup_events_data = [struct.pack('<BBH', *event) for event in setup_events]
        return b''.join([struct.pack('<H', length)] + setup_events_data)


class AdLibSound(BinaryResource):

    def __init__(self, header, events, metadata=b''):
        self.header = header
        self.events = events
        self.metadata = metadata  # TODO: fill from stream/chunk

    def __len__(self):
        return self.header.length

    def __iter__(self):
        yield from self.events

    def __getitem__(self, key):
        return self.events[key]

    def to_imf_chunk(self, delay_cycles=5, which=0, old_muse_compatibility=False):
        events = self.events
        header = self.header
        metadata = self.metadata

        if events:
            modulator = ADLIB_MODULATORS[which]
            freq_l_reg = ADLIB_REG_FREQ_L + modulator
            freq_h_reg = ADLIB_REG_FREQ_H + modulator
            block = ((header.block & 7) << 2) | 0x20
            key_on_data = struct.pack('<BBH', freq_h_reg, block, delay_cycles)
            key_off_data = struct.pack('<BBH', freq_h_reg, 0x00, delay_cycles)

            events_data = []
            for event in events:
                if event:
                    events_data.append(struct.pack('<BBH', freq_l_reg, event, 0))
                    events_data.append(key_on_data)
                else:
                    events_data.append(key_off_data)
            events_data.append(key_off_data)

            setup_data = header.to_imf_chunk(len(events_data), which, old_muse_compatibility)
            imf_chunk = b''.join([setup_data] + events_data + [metadata])
            return imf_chunk
        else:
            setup_data = header.to_imf_chunk(0, which, old_muse_compatibility)
            return bytes(setup_data)

    @classmethod
    def from_stream(cls, stream):
        header = AdLibSoundHeader.from_stream(stream)
        events = stream_read(stream, header.length)
        return cls(header, events)

    def to_stream(self, stream):
        self.header.to_stream(stream)
        stream_write(stream, self.events)

    @classmethod
    def from_bytes(cls, data):
        return cls.from_stream(io.BytesIO(data))

    def to_bytes(self):
        return b''.join([self.header.to_bytes(), self.events])


class AdLibSoundManager(ResourceManager):

    def __init__(self, chunks_handler, start=None, count=None, old_muse_compatibility=False):
        super().__init__(chunks_handler, start, count)
        self.old_muse_compatibility = old_muse_compatibility

    def _build_resource(self, index, chunk):
        return AdLibSound.from_bytes(chunk)


class Music(BinaryResource):

    def __init__(self, events):
        self.events = events

    def __len__(self):
        return len(self.events)

    def __iter__(self):
        yield from self.events

    def __getitem__(self, key):
        return self.events[key]

    def to_imf_chunk(self):
        length = len(self.events) * struct.calcsize('<BBH')
        events_data = [struct.pack('<BBH', *event) for event in self.events]
        return b''.join([struct.pack('<H', length)] + events_data)

    @classmethod
    def from_stream(cls, stream):
        length = stream_unpack('<H', stream)[0]
        assert length % struct.calcsize('<BBH') == 0
        length //= struct.calcsize('<BBH')
        events = list(stream_unpack_array('<BBH', stream, length, scalar=False))
        return cls(events)

    def to_stream(self, stream):
        stream_pack(stream, '<H', len(self.events))
        for event in self.events:
            stream_pack(stream, '<BBH', event)

    @classmethod
    def from_bytes(cls, data):
        return cls.from_stream(io.BytesIO(data))

    def to_bytes(self):
        return self.to_imf_chunk()


class MusicManager(ResourceManager):

    def __init__(self, chunks_handler, start=None, count=None):
        super().__init__(chunks_handler, start, count)

    def _build_resource(self, index, chunk):
        return Music.from_bytes(chunk)


class SampledSound(object):

    def __init__(self, rate, samples):
        self.rate = rate
        self.samples = samples

    def wave_write(self, file):
        rate = self.rate
        samples = self.samples
        wave_write(file, rate, samples)


class SampledSoundManager(ResourceManager):

    def __init__(self, chunks_handler, rate, start=None, count=None):
        super().__init__(chunks_handler, start, count)
        self.rate = rate

    def _build_resource(self, index, chunk):
        samples = bytes(samples_expand(self._chunks_handler, index))
        return SampledSound(self.rate, samples)
