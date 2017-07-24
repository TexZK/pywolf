'''
@author: Andrea Zoppi
'''

import logging
import os
import sys
import unittest

import pywolf.utils


def export(path, data):
    with open(path, 'wb') as file:
        file.write(data)


class Test(unittest.TestCase):

    OUTPUT_FOLDER = r'./outputs/compression_tests'

    @classmethod
    def setUpClass(cls):
        super(Test, cls).setUpClass()
        os.makedirs(cls.OUTPUT_FOLDER, exist_ok=True)

        data = b''.join(bytes([i] * i) for i in range(256))
        revdata = bytes(reversed(data))
        data = data * 2 + revdata + data + revdata * 2 + data * 3 + revdata
        cls.data = data
        export(r'{}/data.bin'.format(cls.OUTPUT_FOLDER), data)

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
        logger.info('len(data): %d', len(data))
        export(r'{}/huffman_data.bin'.format(self.OUTPUT_FOLDER), data)

        counts = pywolf.utils.huffman_count(data)
        logger.info('counts: %r', counts)
        nodes = pywolf.utils.huffman_build_nodes(counts)
        logger.info('nodes: %r', nodes)
        shifts, masks = pywolf.utils.huffman_build_masks(counts, nodes)
        logger.info('shifts: %r', shifts)
        logger.info('masks: %r', masks)

        compressed = pywolf.utils.huffman_compress(data, shifts, masks)
        logger.info('len(compressed): %d', len(compressed))
        logger.info('ratio: %.2f%%', len(compressed) / len(data) * 100)
        export(r'{}/huffman_compressed.bin'.format(self.OUTPUT_FOLDER), compressed)

        expanded = pywolf.utils.huffman_expand(compressed, len(data), nodes)
        logger.info('len(expanded): %d', len(expanded))
        export(r'{}/huffman_expanded.bin'.format(self.OUTPUT_FOLDER), expanded)

        self.assertEqual(expanded, data)

    def testRLEW(self):
        logger = logging.getLogger()
        logger.info('testRLEW')

        data = self.data
        logger.info('len(data): %d', len(data))
        export(r'{}/rlew_data.bin'.format(self.OUTPUT_FOLDER), data)

        tag = 0xFEFE
        compressed = pywolf.utils.rlew_compress(data, tag)
        logger.info('len(compressed): %d', len(compressed))
        logger.info('ratio: %.2f%%', len(compressed) / len(data) * 100)
        export(r'{}/rlew_compressed.bin'.format(self.OUTPUT_FOLDER), compressed)

        expanded = pywolf.utils.rlew_expand(compressed, tag)
        logger.info('len(expanded): %d', len(expanded))
        export(r'{}/rlew_expanded.bin'.format(self.OUTPUT_FOLDER), expanded)

        self.assertEqual(expanded, data)

    def testCarmack(self):
        logger = logging.getLogger()
        logger.info('testCarmack')

        data = self.data[:pywolf.utils.CARMACK_MAX_SIZE]
        logger.info('len(data): %d', len(data))
        export(r'{}/carmack_data.bin'.format(self.OUTPUT_FOLDER), data)

        compressed = pywolf.utils.carmack_compress(data)
        logger.info('len(compressed): %d', len(compressed))
        logger.info('ratio: %.2f%%', len(compressed) / len(data) * 100)
        export(r'{}/carmack_compressed.bin'.format(self.OUTPUT_FOLDER), compressed)

        expanded = pywolf.utils.carmack_expand(compressed, len(data))
        logger.info('len(expanded): %d', len(expanded))
        export(r'{}/carmack_expanded.bin'.format(self.OUTPUT_FOLDER), expanded)

        self.assertEqual(expanded, data)


if __name__ == "__main__":
    unittest.main()


