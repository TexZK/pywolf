'''
@author: Andrea Zoppi
'''

import unittest
import sys
import logging

import pywolf.persistence
import pywolf.audio
import pywolf.configs.wl6


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

            sample_manager = pywolf.audio.SampledSoundManager(vswap_chunks_handler,
                                                              frequency=pywolf.configs.wl6.SOUNDS_FREQUENCY)  # FIXME: start=?
            sample = sample_manager[0]
        sample.wave_write(r'./outputs/sample_0.wav')


if __name__ == "__main__":
    #import sys;sys.argv = ['', 'Test.testName']
    unittest.main()


