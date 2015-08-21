'''
@author: Andrea Zoppi
'''

import struct
import wave

from .utils import ResourceManager


SAMPLE_RATE = 7042


def samples_expand(chunks_handler, index):
    sounds_start = chunks_handler.sounds_start
    sounds_infos = chunks_handler.sounds_infos
    start, length = sounds_infos[index]

    chunks = []
    chunk_index = sounds_start + start
    remaining = length
    while remaining:
        chunk = chunks_handler[chunk_index]
        if len(chunk) <= remaining:
            chunks.append(chunk)
            remaining -= len(chunk)
        else:
            chunks.append(chunk[:remaining])
            remaining = 0
        chunk_index += 1
    return b''.join(chunks)


class SampledSound(object):

    def __init__(self, frequency, samples):
        self.frequency = frequency
        self.samples = samples

    def wave_write(self, file):
        frequency = self.frequency
        samples = self.samples

        with wave.open(file, 'wb') as wave_file:
            wave_file.setnchannels(1)
            wave_file.setsampwidth(struct.calcsize('<B'))
            wave_file.setframerate(frequency)
            wave_file.setnframes(len(samples))
            wave_file.writeframesraw(samples)


class SampledSoundManager(ResourceManager):

    def __init__(self, chunks_handler, start=None, count=None, cache=None,
                 frequency=SAMPLE_RATE):
        super().__init__(chunks_handler, start, count, cache)
        self.frequency = frequency

    def _build_resource(self, index, chunk):
        chunks_handler = self._chunks_handler
        frequency = self.frequency

        samples = samples_expand(chunks_handler, index)
        return SampledSound(frequency, samples)
