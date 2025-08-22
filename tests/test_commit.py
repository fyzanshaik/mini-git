import unittest
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import importlib.util
spec = importlib.util.spec_from_file_location("commit_object", os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "commit-object.py"))
commit_module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(commit_module)
Commit = commit_module.Commit


class TestCommit(unittest.TestCase):

    def test_commit_creation(self):
        tree_hash = "a" * 40
        commit = Commit(tree_hash=tree_hash, message="Initial commit")
        
        self.assertEqual(commit.get_type(), "commit")
        self.assertEqual(commit.tree_hash, tree_hash)
        self.assertIsNone(commit.parent_hash)
        self.assertEqual(commit.message, "Initial commit")
        self.assertTrue(commit.is_initial_commit())

    def test_commit_with_parent(self):
        tree_hash = "a" * 40
        parent_hash = "b" * 40
        commit = Commit(
            tree_hash=tree_hash, 
            parent_hash=parent_hash, 
            message="Second commit"
        )
        
        self.assertEqual(commit.tree_hash, tree_hash)
        self.assertEqual(commit.parent_hash, parent_hash)
        self.assertEqual(commit.message, "Second commit")
        self.assertFalse(commit.is_initial_commit())

    def test_commit_data_format(self):
        tree_hash = "a" * 40
        commit = Commit(
            tree_hash=tree_hash, 
            author="John Doe <john@example.com>",
            message="Test commit"
        )
        
        # Check that commit data contains expected parts
        commit_text = commit.data.decode('utf-8')
        self.assertIn(f"tree {tree_hash}", commit_text)
        self.assertIn("author John Doe <john@example.com>", commit_text)
        self.assertIn("committer John Doe <john@example.com>", commit_text)
        self.assertIn("Test commit", commit_text)

    def test_commit_with_parent_data_format(self):
        tree_hash = "a" * 40
        parent_hash = "b" * 40
        commit = Commit(
            tree_hash=tree_hash,
            parent_hash=parent_hash,
            message="Child commit"
        )
        
        commit_text = commit.data.decode('utf-8')
        self.assertIn(f"tree {tree_hash}", commit_text)
        self.assertIn(f"parent {parent_hash}", commit_text)
        self.assertIn("Child commit", commit_text)

    def test_set_tree(self):
        commit = Commit(message="Test")
        new_tree = "c" * 40
        commit.set_tree(new_tree)
        
        self.assertEqual(commit.tree_hash, new_tree)
        commit_text = commit.data.decode('utf-8')
        self.assertIn(f"tree {new_tree}", commit_text)

    def test_set_parent(self):
        commit = Commit(tree_hash="a" * 40, message="Test")
        parent_hash = "d" * 40
        commit.set_parent(parent_hash)
        
        self.assertEqual(commit.parent_hash, parent_hash)
        self.assertFalse(commit.is_initial_commit())
        commit_text = commit.data.decode('utf-8')
        self.assertIn(f"parent {parent_hash}", commit_text)

    def test_set_message(self):
        commit = Commit(tree_hash="a" * 40, message="Old message")
        new_message = "New commit message"
        commit.set_message(new_message)
        
        self.assertEqual(commit.message, new_message)
        commit_text = commit.data.decode('utf-8')
        self.assertIn(new_message, commit_text)

    def test_set_author(self):
        commit = Commit(tree_hash="a" * 40, message="Test")
        new_author = "Jane Smith <jane@example.com>"
        commit.set_author(new_author)
        
        self.assertEqual(commit.author, new_author)
        commit_text = commit.data.decode('utf-8')
        self.assertIn(f"author {new_author}", commit_text)

    def test_parse_commit_data(self):
        # Create original commit
        original = Commit(
            tree_hash="a" * 40,
            parent_hash="b" * 40,
            author="Test Author <test@example.com>",
            message="Parse test commit"
        )
        
        # Parse the commit data
        parsed = Commit.parse_commit_data(original.data)
        
        self.assertEqual(parsed.tree_hash, original.tree_hash)
        self.assertEqual(parsed.parent_hash, original.parent_hash)
        self.assertEqual(parsed.message, original.message)

    def test_parse_initial_commit_data(self):
        # Create initial commit (no parent)
        original = Commit(
            tree_hash="a" * 40,
            author="Test Author <test@example.com>",
            message="Initial commit"
        )
        
        # Parse the commit data
        parsed = Commit.parse_commit_data(original.data)
        
        self.assertEqual(parsed.tree_hash, original.tree_hash)
        self.assertIsNone(parsed.parent_hash)
        self.assertTrue(parsed.is_initial_commit())
        self.assertEqual(parsed.message, original.message)

    def test_get_commit_info(self):
        tree_hash = "a" * 40
        parent_hash = "b" * 40
        commit = Commit(
            tree_hash=tree_hash,
            parent_hash=parent_hash,
            author="Test Author <test@example.com>",
            message="Info test"
        )
        
        info = commit.get_commit_info()
        
        self.assertEqual(info['tree'], tree_hash)
        self.assertEqual(info['parent'], parent_hash)
        self.assertEqual(info['author'], "Test Author <test@example.com>")
        self.assertEqual(info['message'], "Info test")
        self.assertFalse(info['is_initial'])

    def test_commit_hash_calculation(self):
        commit = Commit(
            tree_hash="a" * 40,
            message="Hash test"
        )
        
        calculated_hash = commit.calculate_hash()
        
        self.assertEqual(len(calculated_hash), 40)
        self.assertIsInstance(calculated_hash, str)


if __name__ == '__main__':
    unittest.main()
