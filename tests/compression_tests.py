'''
@author: Andrea Zoppi
'''

import logging
import sys
import unittest

import pywolf.utils


def export(path, data):
    with open(path, 'wb') as file:
        file.write(data)


class Test(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        super(Test, cls).setUpClass()

        data = b''.join(bytes([i] * i) for i in range(256))
        revdata = bytes(reversed(data))
        data = data * 2 + revdata + data + revdata * 2 + data * 3 + revdata
        cls.data = data
        export('./outputs/data.bin', data)

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

    def testHuffman(self):
        logger = logging.getLogger()
        logger.info('testHuffman')

        data = self.data
        logger.debug('len(data): %d', len(data))
        export('./outputs/huffman_data.bin', data)

        counts = pywolf.utils.huffman_count(data)
        logger.debug('counts: %r', counts)
        nodes = pywolf.utils.huffman_build_nodes(counts)
        logger.debug('nodes: %r', nodes)
        shifts, masks = pywolf.utils.huffman_build_masks(counts, nodes)
        logger.debug('shifts: %r', shifts)
        logger.debug('masks: %r', masks)

        compressed = pywolf.utils.huffman_compress(data, shifts, masks)
        logger.debug('len(compressed): %d', len(compressed))
        logger.debug('ratio: %.2f%%', len(compressed) / len(data) * 100)
        export('./outputs/huffman_compressed.bin', compressed)

        expanded = pywolf.utils.huffman_expand(compressed, len(data), nodes)
        logger.debug('len(expanded): %d', len(expanded))
        export('./outputs/huffman_expanded.bin', expanded)

        self.assertEqual(expanded, data)

    def testRLEW(self):
        logger = logging.getLogger()
        logger.info('testRLEW')

        data = self.data
        logger.debug('len(data): %d', len(data))
        export('./outputs/rlew_data.bin', data)

        tag = 0xFEFE
        compressed = pywolf.utils.rlew_compress(data, tag)
        logger.debug('len(compressed): %d', len(compressed))
        logger.debug('ratio: %.2f%%', len(compressed) / len(data) * 100)
        export('./outputs/rlew_compressed.bin', compressed)

        expanded = pywolf.utils.rlew_expand(compressed, tag)
        logger.debug('len(expanded): %d', len(expanded))
        export('./outputs/rlew_expanded.bin', expanded)

        self.assertEqual(expanded, data)

    def testCarmack(self):
        logger = logging.getLogger()
        logger.info('testCarmack')

        data = self.data[:pywolf.utils.CARMACK_MAX_SIZE]
        logger.debug('len(data): %d', len(data))
        export('./outputs/carmack_data.bin', data)

        compressed = pywolf.utils.carmack_compress(data)
        logger.debug('len(compressed): %d', len(compressed))
        logger.debug('ratio: %.2f%%', len(compressed) / len(data) * 100)
        export('./outputs/carmack_compressed.bin', compressed)

        expanded = pywolf.utils.carmack_expand(compressed, len(data))
        logger.debug('len(expanded): %d', len(expanded))
        export('./outputs/carmack_expanded.bin', expanded)

        self.assertEqual(expanded, data)


if __name__ == "__main__":
    unittest.main()


