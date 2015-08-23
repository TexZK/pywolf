'''
@author: Andrea Zoppi
'''

import struct
import wave

from .utils import ResourceManager, stream_unpack


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


def wave_write(file, frequency, samples):
    with wave.open(file, 'w') as wave_stream:
        wave_stream.setnchannels(1)
        wave_stream.setsampwidth(struct.calcsize('<B'))
        wave_stream.setframerate(frequency)
        wave_stream.setnframes(len(samples))
        wave_stream.writeframesraw(samples)


class AdLibSoundHeader(object):

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
    def from_stream(cls, data_stream):
        args = list(stream_unpack('<LH13B', data_stream))
        stream_unpack('<3B', data_stream)  # unused
        args += stream_unpack('<B', data_stream)
        return cls(*args)


class SampledSound(object):

    def __init__(self, frequency, samples):
        self.frequency = frequency
        self.samples = samples

    def wave_write(self, file):
        frequency = self.frequency
        samples = self.samples
        wave_write(file, frequency, samples)


class SampledSoundManager(ResourceManager):

    def __init__(self, chunks_handler, frequency, start=None, count=None, cache=None):
        super().__init__(chunks_handler, start, count, cache)
        self.frequency = frequency

    def _build_resource(self, index, chunk):
        chunks_handler = self._chunks_handler
        frequency = self.frequency

        samples = bytes(samples_expand(chunks_handler, index))
        return SampledSound(frequency, samples)
