import unittest
import tempfile
import os
import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import importlib.util
spec = importlib.util.spec_from_file_location("blob_object", os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "blob-object.py"))
blob_module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(blob_module)
Blob = blob_module.Blob


class TestBlob(unittest.TestCase):

    def test_blob_creation_from_bytes(self):
        data = b"Hello, World!"
        blob = Blob(data)
        
        self.assertEqual(blob.data, data)
        self.assertEqual(blob.get_type(), "blob")

    def test_blob_creation_from_string(self):
        text = "Hello, World!"
        blob = Blob(text)
        
        self.assertEqual(blob.data, text.encode('utf-8'))
        self.assertEqual(blob.get_type(), "blob")

    def test_blob_hash_calculation(self):
        blob = Blob("hello")
        hash_value = blob.calculate_hash()
        
        self.assertEqual(len(hash_value), 40)
        self.assertEqual(hash_value, "b6fc4c620b67d95f953a5c1c1230aaab5db5a1b0")

    def test_blob_from_file(self):
        with tempfile.NamedTemporaryFile(mode='w', delete=False) as f:
            test_content = "This is a test file content"
            f.write(test_content)
            f.flush()
            
            blob = Blob.from_file(f.name)
            
            self.assertEqual(blob.data, test_content.encode('utf-8'))
            self.assertEqual(blob.get_type(), "blob")
            
            os.unlink(f.name)

    def test_blob_save_to_file(self):
        original_data = b"Test content for saving"
        blob = Blob(original_data)
        
        with tempfile.NamedTemporaryFile(delete=False) as f:
            blob.save_to_file(f.name)
            
            with open(f.name, 'rb') as read_file:
                saved_content = read_file.read()
            
            self.assertEqual(saved_content, original_data)
            os.unlink(f.name)

    def test_blob_round_trip_file_operations(self):
        original_content = "Round trip test content\nWith multiple lines\n"
        
        with tempfile.NamedTemporaryFile(mode='w', delete=False) as f:
            f.write(original_content)
            f.flush()
            
            blob = Blob.from_file(f.name)
            os.unlink(f.name)
        
        with tempfile.NamedTemporaryFile(delete=False) as f:
            blob.save_to_file(f.name)
            
            with open(f.name, 'r') as read_file:
                final_content = read_file.read()
            
            self.assertEqual(final_content, original_content)
            os.unlink(f.name)


if __name__ == '__main__':
    unittest.main()
