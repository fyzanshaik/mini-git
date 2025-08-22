import unittest
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import importlib.util
spec = importlib.util.spec_from_file_location("tree_object", os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "tree-object.py"))
tree_module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(tree_module)
Tree = tree_module.Tree


class TestTree(unittest.TestCase):

    def test_tree_creation(self):
        tree = Tree()
        self.assertEqual(tree.get_type(), "tree")
        self.assertEqual(len(tree.entries), 0)
        self.assertEqual(tree.data, b'')

    def test_add_single_entry(self):
        tree = Tree()
        hash_value = "b6fc4c620b67d95f953a5c1c1230aaab5db5a1b0"
        tree.add_entry("100644", "hello.txt", hash_value)
        
        self.assertEqual(len(tree.entries), 1)
        entry = tree.entries[0]
        self.assertEqual(entry['mode'], "100644")
        self.assertEqual(entry['name'], "hello.txt")
        self.assertEqual(entry['hash'], hash_value)

    def test_add_multiple_entries(self):
        tree = Tree()
        
        tree.add_entry("100644", "file1.txt", "a" * 40)
        tree.add_entry("100755", "script.sh", "b" * 40)
        tree.add_entry("040000", "subdir", "c" * 40)
        
        self.assertEqual(len(tree.entries), 3)
        
        # Check entries are sorted by name
        names = [entry['name'] for entry in tree.entries]
        self.assertEqual(names, sorted(names))

    def test_tree_data_building(self):
        tree = Tree()
        hash_value = "b6fc4c620b67d95f953a5c1c1230aaab5db5a1b0"
        tree.add_entry("100644", "hello.txt", hash_value)
        
        # Tree data should be built automatically
        self.assertGreater(len(tree.data), 0)
        
        # Should contain the mode, name, null byte, and 20-byte hash
        expected_size = len("100644 hello.txt") + 1 + 20  # mode+name + null + hash
        self.assertEqual(len(tree.data), expected_size)

    def test_from_entries_class_method(self):
        entries = [
            ("100644", "file1.txt", "a" * 40),
            ("100755", "script.sh", "b" * 40),
            ("040000", "subdir", "c" * 40)
        ]
        
        tree = Tree.from_entries(entries)
        
        self.assertEqual(len(tree.entries), 3)
        self.assertEqual(tree.entries[0]['name'], "file1.txt")
        self.assertEqual(tree.entries[1]['name'], "script.sh")
        self.assertEqual(tree.entries[2]['name'], "subdir")

    def test_parse_tree_data(self):
        # First create a tree with some entries
        tree1 = Tree()
        hash_value = "b6fc4c620b67d95f953a5c1c1230aaab5db5a1b0"
        tree1.add_entry("100644", "hello.txt", hash_value)
        tree1.add_entry("040000", "subdir", "a" * 40)
        
        # Get the tree data
        original_data = tree1.data
        
        # Create a new tree and parse the data
        tree2 = Tree()
        tree2.data = original_data
        entries = tree2.parse_tree_data(original_data)
        
        # Should have same entries
        self.assertEqual(len(entries), 2)
        
        # Check first entry
        entry1 = entries[0]
        self.assertEqual(entry1['mode'], "100644")
        self.assertEqual(entry1['name'], "hello.txt")
        self.assertEqual(entry1['hash'], hash_value)

    def test_get_entries(self):
        tree = Tree()
        hash_value = "b6fc4c620b67d95f953a5c1c1230aaab5db5a1b0"
        tree.add_entry("100644", "hello.txt", hash_value)
        
        entries = tree.get_entries()
        
        # Should return a copy, not the original
        self.assertIsNot(entries, tree.entries)
        self.assertEqual(len(entries), 1)
        self.assertEqual(entries[0]['name'], "hello.txt")

    def test_tree_hash_calculation(self):
        tree = Tree()
        hash_value = "b6fc4c620b67d95f953a5c1c1230aaab5db5a1b0"
        tree.add_entry("100644", "hello.txt", hash_value)
        
        calculated_hash = tree.calculate_hash()
        
        self.assertEqual(len(calculated_hash), 40)
        self.assertIsInstance(calculated_hash, str)


if __name__ == '__main__':
    unittest.main()
