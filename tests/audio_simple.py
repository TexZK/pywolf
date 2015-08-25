'''
@author: Andrea Zoppi
'''

import logging
import sys
import unittest

import pywolf.audio
import pywolf.configs.wl6
import pywolf.persistence


class Test(unittest.TestCase):

    def setUp(self):
        logger = logging.getLogger()
        stdout_handler = logging.StreamHandler(sys.stdout)
        stdout_handler.setLevel(logging.DEBUG)
        logger.addHandler(stdout_handler)
        logger.setLevel(logging.DEBUG)
        self._stdout_handler = stdout_handler

    def tearDown(self):
        logger = logging.getLogger()
        logger.removeHandler(self._stdout_handler)

    def testSampledSounds(self):
        logger = logging.getLogger()
        logger.info('testSampledSounds')

        vswap_chunks_handler = pywolf.persistence.VSwapChunksHandler()

        with open(r'../data/wl6/vswap.wl6', 'rb') as data_file:
            vswap_chunks_handler.load(data_file)

            start = vswap_chunks_handler.sounds_start
            count = len(vswap_chunks_handler.sounds_infos)
            sample_manager = pywolf.audio.SampledSoundManager(vswap_chunks_handler,
                                                              pywolf.configs.wl6.SAMPLED_SOUNDS_FREQUENCY,
                                                              start=start, count=count)

            for i, sound in enumerate(sample_manager):
                sound.wave_write(r'./outputs/sample_{}.wav'.format(i))

    # TODO: testMusics()

    # TODO: testAdLibSounds()

    def testBuzzerSounds(self):
        logger = logging.getLogger()
        logger.info('testBuzzerSounds')

        audio_chunks_handler = pywolf.persistence.AudioChunksHandler()

        with open('../data/wl6/audiohed.wl6', 'rb') as (header_file
        ),   open('../data/wl6/audiot.wl6', 'rb') as data_file:
            audio_chunks_handler.load(data_file, header_file)

            start, count = pywolf.configs.wl6.SOUNDS_PARTITIONS_MAP['buzzer']
            buzzer_manager = pywolf.audio.BuzzerSoundManager(audio_chunks_handler, start=start, count=count)

            for i, sound in enumerate(buzzer_manager):
                sound.wave_write(r'./outputs/buzzer_{}.wav'.format(i))


if __name__ == "__main__":
    #import sys;sys.argv = ['', 'Test.testName']
    unittest.main()


