import unittest
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from minigit import MinigitObject


class TestObject(MinigitObject):
    def get_type(self):
        return "test"


class TestMinigitObject(unittest.TestCase):

    def setUp(self):
        self.test_data = b"Hello, Mini-Git!"
        self.obj = TestObject(self.test_data)

    def test_object_creation(self):
        self.assertEqual(self.obj.data, self.test_data)
        self.assertEqual(self.obj.get_type(), "test")
        self.assertIsNone(self.obj.hash)

    def test_header_creation(self):
        header = self.obj.create_header()
        expected_header = b"test 16\x00"
        self.assertEqual(header, expected_header)

    def test_hash_calculation(self):
        hash_value = self.obj.calculate_hash()
        self.assertEqual(len(hash_value), 40)
        self.assertEqual(hash_value, "7ab07d1e300bdb11548ea510ff4183ae6b95d187")
        self.assertEqual(self.obj.hash, hash_value)

    def test_compression_decompression(self):
        compressed = self.obj.compress_data()
        self.assertIsInstance(compressed, bytes)
        self.assertGreater(len(compressed), 0)
        
        decompressed = MinigitObject.decompress_data(compressed)
        self.assertIsInstance(decompressed, bytes)

    def test_parse_object_data(self):
        compressed = self.obj.compress_data()
        decompressed = MinigitObject.decompress_data(compressed)
        obj_type, size, content = MinigitObject.parse_object_data(decompressed)
        
        self.assertEqual(obj_type, "test")
        self.assertEqual(size, 16)
        self.assertEqual(content, self.test_data)

    def test_storage_path_components(self):
        dir_name, filename = self.obj.get_storage_path_components()
        
        self.assertEqual(len(dir_name), 2)
        self.assertEqual(len(filename), 38)
        self.assertEqual(dir_name + filename, self.obj.hash)

    def test_round_trip_integrity(self):
        compressed = self.obj.compress_data()
        decompressed = MinigitObject.decompress_data(compressed)
        obj_type, size, content = MinigitObject.parse_object_data(decompressed)
        
        self.assertEqual(content, self.test_data)
        self.assertEqual(obj_type, "test")
        self.assertEqual(size, len(self.test_data))


if __name__ == '__main__':
    unittest.main()
