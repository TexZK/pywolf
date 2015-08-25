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


def wave_write(file, frequency, byte_samples):
    with wave.open(file, 'w') as wave_stream:
        wave_stream.setnchannels(1)
        wave_stream.setsampwidth(struct.calcsize('<B'))
        wave_stream.setframerate(frequency)
        wave_stream.setnframes(len(byte_samples))
        wave_stream.writeframesraw(byte_samples)


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


def buzzer_expand(divisors, sample_rate=44100, char_rate=140, buzzer_clock=1193180, round_period=True):
    generator = SquareWaveGenerator(sample_rate, high=0xFF, low=0x00, silence=0x80, round_period=round_period)
    char_length = sample_rate / char_rate
    offset = 0

    for divisor in divisors:
        generator.set_frequency(buzzer_clock / (divisor * 60) if divisor else 0)
        length = offset + char_length
        length_floor = round(length)
        yield from generator(length_floor)
        offset = length - length_floor


class BuzzerSound(object):

    def __init__(self, divisors):
        self.divisors = divisors

    def to_samples(self, rate=44100):
        yield from buzzer_expand(self.divisors, rate)

    def wave_write(self, file, rate=44100):
        samples = bytes(self.to_samples(rate))
        wave_write(file, rate, samples)


class BuzzerSoundManager(ResourceManager):

    def __init__(self, chunks_handler, start=None, count=None, cache=None):
        super().__init__(chunks_handler, start, count, cache)

    def _build_resource(self, index, chunk):
        divisors = chunk
        return BuzzerSound(divisors)


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

    # TODO: to_stream()


# TODO: AdLibSound


# TODO: AdLibSoundManager


class SampledSound(object):

    def __init__(self, rate, samples):
        self.rate = rate
        self.samples = samples

    def wave_write(self, file):
        rate = self.rate
        samples = self.samples
        wave_write(file, rate, samples)


class SampledSoundManager(ResourceManager):

    def __init__(self, chunks_handler, rate, start=None, count=None, cache=None):
        super().__init__(chunks_handler, start, count, cache)
        self.rate = rate

    def _build_resource(self, index, chunk):
        chunks_handler = self._chunks_handler
        rate = self.rate

        samples = bytes(samples_expand(chunks_handler, index))
        return SampledSound(rate, samples)
