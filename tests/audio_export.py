import logging
import os
import sys
import unittest

import pywolf.audio
import pywolf.persistence

import pywolf.configs.wl6


IMF2WAV_PATH = '../tools/imf2wav.exe'


def _sep():
    logger = logging.getLogger()
    logger.info('-' * 80)


class Test(unittest.TestCase):

    AUDIOHED_PATH = r'../data/wl6/audiohed.wl6'
    AUDIOT_PATH = r'../data/wl6/audiot.wl6'

    VSWAP_PATH = r'../data/wl6/vswap.wl6'

    OUTPUT_FOLDER = r'./outputs/audio_tests'
    OUTPUT_IMF_EXT = r'wlf'  # 700 tick/s

    @classmethod
    def setUpClass(cls):
        super(Test, cls).setUpClass()
        os.makedirs(cls.OUTPUT_FOLDER, exist_ok=True)

    @classmethod
    def tearDownClass(cls):
        super(Test, cls).tearDownClass()

    def setUp(self):
        logger = logging.getLogger()
        stdout_handler = logging.StreamHandler(sys.stdout)
        stdout_handler.setLevel(logging.DEBUG)
        logger.addHandler(stdout_handler)
        logger.setLevel(logging.DEBUG)
        logger.info('-' * 80)
        self._stdout_handler = stdout_handler

    def tearDown(self):
        logger = logging.getLogger()
        logger.removeHandler(self._stdout_handler)

    def testSampledSounds(self):
        logger = logging.getLogger()
        logger.info('testSampledSounds')

        vswap_chunks_handler = pywolf.persistence.VSwapChunksHandler()

        with open(self.VSWAP_PATH, 'rb') as data_file:
            vswap_chunks_handler.load(data_file)

            start = vswap_chunks_handler.sounds_start
            count = len(vswap_chunks_handler.sounds_infos)
            sample_manager = pywolf.audio.SampledSoundManager(vswap_chunks_handler,
                                                              pywolf.configs.wl6.SAMPLED_SOUND_FREQUENCY,
                                                              start=start, count=count)

            for i, sound in enumerate(sample_manager):
                path = r'{}/sample_{}.wav'.format(self.OUTPUT_FOLDER, i)
                logger.info('Sampled sound [%d/%d]: %r', (i + 1), count, path)
                sound.wave_write(path)

    def testMusics(self):
        logger = logging.getLogger()
        logger.info('testMusics')

        audio_chunks_handler = pywolf.persistence.AudioChunksHandler()

        with open(self.AUDIOHED_PATH, 'rb') as (header_file
        ), open(self.AUDIOT_PATH, 'rb') as data_file:
            audio_chunks_handler.load(data_file, header_file)

            start, count = pywolf.configs.wl6.AUDIO_PARTITIONS_MAP['music']
            music_manager = pywolf.audio.MusicManager(audio_chunks_handler, start, count)

            for i, sound in enumerate(music_manager):
                path = '{}/music_{}.wav'.format(self.OUTPUT_FOLDER, i)
                chunk_path = '{}/music_{}.{}'.format(self.OUTPUT_FOLDER, i, self.OUTPUT_IMF_EXT)
                logger.info('Music [%d/%d]: %r', (i + 1), count, path)
                imf_chunk = sound.to_imf_chunk()
                pywolf.audio.convert_imf_to_wave(imf_chunk, IMF2WAV_PATH, wave_path=path, chunk_path=chunk_path)

    def testAdLibSounds(self):
        logger = logging.getLogger()
        logger.info('testAdLibSounds')

        audio_chunks_handler = pywolf.persistence.AudioChunksHandler()

        with open(self.AUDIOHED_PATH, 'rb') as (header_file
        ), open(self.AUDIOT_PATH, 'rb') as data_file:
            audio_chunks_handler.load(data_file, header_file)

            start, count = pywolf.configs.wl6.AUDIO_PARTITIONS_MAP['adlib']
            adlib_manager = pywolf.audio.AdLibSoundManager(audio_chunks_handler, start, count)

            for i, sound in enumerate(adlib_manager):
                path = '{}/adlib_{}.wav'.format(self.OUTPUT_FOLDER, i)
                chunk_path = '{}/adlib_{}.{}'.format(self.OUTPUT_FOLDER, i, self.OUTPUT_IMF_EXT)
                imf_path = '{}/adlib_{}.{}'.format(self.OUTPUT_FOLDER, i, self.OUTPUT_IMF_EXT)
                logger.info('AdLib sound [%d/%d]: %r', (i + 1), count, path)
                imf_chunk = sound.to_imf_chunk()
                pywolf.audio.convert_imf_to_wave(imf_chunk, IMF2WAV_PATH, wave_path=path, chunk_path=chunk_path)


    def testBuzzerSounds(self):
        logger = logging.getLogger()
        logger.info('testBuzzerSounds')

        audio_chunks_handler = pywolf.persistence.AudioChunksHandler()

        with open(self.AUDIOHED_PATH, 'rb') as (header_file
        ), open(self.AUDIOT_PATH, 'rb') as data_file:
            audio_chunks_handler.load(data_file, header_file)

            start, count = pywolf.configs.wl6.AUDIO_PARTITIONS_MAP['buzzer']
            buzzer_manager = pywolf.audio.BuzzerSoundManager(audio_chunks_handler, start=start, count=count)

            for i, sound in enumerate(buzzer_manager):
                path = r'{}/buzzer_{}.wav'.format(self.OUTPUT_FOLDER, i)
                logger.info('Buzzer sound [%d/%d]: %r', (i + 1), count, path)
                sound.wave_write(path)


if __name__ == "__main__":
    unittest.main()


