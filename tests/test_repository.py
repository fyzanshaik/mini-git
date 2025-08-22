import unittest
import tempfile
import shutil
import os
import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import importlib.util

# Import Repository
spec = importlib.util.spec_from_file_location("repository", os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "repository.py"))
repo_module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(repo_module)
Repository = repo_module.Repository

# Import object classes
spec = importlib.util.spec_from_file_location("blob_object", os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "blob-object.py"))
blob_module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(blob_module)
Blob = blob_module.Blob


class TestRepository(unittest.TestCase):

    def setUp(self):
        self.test_dir = tempfile.mkdtemp()
        self.repo = Repository(self.test_dir)

    def tearDown(self):
        if os.path.exists(self.test_dir):
            shutil.rmtree(self.test_dir)

    def test_repository_creation(self):
        self.assertFalse(self.repo.exists())
        
        result = self.repo.create()
        
        self.assertTrue(result)
        self.assertTrue(self.repo.exists())
        self.assertTrue(os.path.exists(self.repo.minigit_path))
        self.assertTrue(os.path.exists(self.repo.objects_path))
        self.assertTrue(os.path.exists(self.repo.refs_path))
        self.assertTrue(os.path.exists(self.repo.heads_path))
        self.assertTrue(os.path.exists(self.repo.head_file))

    def test_repository_already_exists(self):
        self.repo.create()
        
        result = self.repo.create()
        
        self.assertFalse(result)

    def test_head_file_content(self):
        self.repo.create()
        
        with open(self.repo.head_file, 'r') as f:
            content = f.read().strip()
        
        self.assertEqual(content, "ref: refs/heads/main")

    def test_store_and_load_blob(self):
        self.repo.create()
        
        blob = Blob("Hello, Repository!")
        hash_value = self.repo.store_object(blob)
        
        self.assertEqual(len(hash_value), 40)
        self.assertTrue(self.repo.object_exists(hash_value))
        
        loaded_blob = self.repo.load_object(hash_value)
        
        self.assertEqual(loaded_blob.__class__.__name__, 'Blob')
        self.assertEqual(loaded_blob.data, blob.data)
        self.assertEqual(loaded_blob.hash, hash_value)

    def test_store_duplicate_object(self):
        self.repo.create()
        
        blob1 = Blob("Same content")
        blob2 = Blob("Same content")
        
        hash1 = self.repo.store_object(blob1)
        hash2 = self.repo.store_object(blob2)
        
        self.assertEqual(hash1, hash2)

    def test_load_nonexistent_object(self):
        self.repo.create()
        
        with self.assertRaises(FileNotFoundError):
            self.repo.load_object("a" * 40)

    def test_invalid_hash_length(self):
        self.repo.create()
        
        with self.assertRaises(ValueError):
            self.repo.load_object("invalid")

    def test_get_head_no_repository(self):
        head = self.repo.get_head()
        self.assertIsNone(head)

    def test_get_head_no_branch_file(self):
        self.repo.create()
        
        head = self.repo.get_head()
        self.assertIsNone(head)

    def test_update_and_get_branch(self):
        self.repo.create()
        
        commit_hash = "a" * 40
        self.repo.update_branch("main", commit_hash)
        
        head = self.repo.get_head()
        self.assertEqual(head, commit_hash)

    def test_get_current_branch(self):
        self.repo.create()
        
        branch = self.repo.get_current_branch()
        self.assertEqual(branch, "main")

    def test_list_objects_empty(self):
        self.repo.create()
        
        objects = self.repo.list_objects()
        self.assertEqual(len(objects), 0)

    def test_list_objects_with_content(self):
        self.repo.create()
        
        blob1 = Blob("Content 1")
        blob2 = Blob("Content 2")
        
        hash1 = self.repo.store_object(blob1)
        hash2 = self.repo.store_object(blob2)
        
        objects = self.repo.list_objects()
        
        self.assertEqual(len(objects), 2)
        self.assertIn(hash1, objects)
        self.assertIn(hash2, objects)

    def test_get_working_directory(self):
        working_dir = self.repo.get_working_directory()
        self.assertEqual(working_dir, os.path.abspath(self.test_dir))

    def test_get_minigit_path(self):
        minigit_path = self.repo.get_minigit_path()
        expected_path = os.path.join(self.test_dir, ".minigit")
        self.assertEqual(minigit_path, os.path.abspath(expected_path))

    def test_find_repository_current_dir(self):
        self.repo.create()
        
        found_repo = Repository.find_repository(self.test_dir)
        
        self.assertIsNotNone(found_repo)
        self.assertEqual(found_repo.repo_path, self.repo.repo_path)

    def test_find_repository_parent_dir(self):
        self.repo.create()
        
        subdir = os.path.join(self.test_dir, "subdir", "deep")
        os.makedirs(subdir, exist_ok=True)
        
        found_repo = Repository.find_repository(subdir)
        
        self.assertIsNotNone(found_repo)
        self.assertEqual(found_repo.repo_path, self.repo.repo_path)

    def test_find_repository_not_found(self):
        temp_dir = tempfile.mkdtemp()
        try:
            found_repo = Repository.find_repository(temp_dir)
            self.assertIsNone(found_repo)
        finally:
            shutil.rmtree(temp_dir)

    def test_resolve_hash_full_hash(self):
        self.repo.create()
        
        blob = Blob("test content")
        hash_value = self.repo.store_object(blob)
        
        resolved = self.repo.resolve_hash(hash_value)
        self.assertEqual(resolved, hash_value)

    def test_resolve_hash_short_hash(self):
        self.repo.create()
        
        blob = Blob("test content for short hash")
        hash_value = self.repo.store_object(blob)
        short_hash = hash_value[:6]
        
        resolved = self.repo.resolve_hash(short_hash)
        self.assertEqual(resolved, hash_value)

    def test_resolve_hash_too_short(self):
        self.repo.create()
        
        resolved = self.repo.resolve_hash("abc")
        self.assertIsNone(resolved)

    def test_resolve_hash_not_found(self):
        self.repo.create()
        
        resolved = self.repo.resolve_hash("1234")
        self.assertIsNone(resolved)

    def test_resolve_hash_nonexistent_full_hash(self):
        self.repo.create()
        
        fake_hash = "a" * 40
        resolved = self.repo.resolve_hash(fake_hash)
        self.assertIsNone(resolved)


if __name__ == '__main__':
    unittest.main()
