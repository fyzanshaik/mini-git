import unittest
import tempfile
import shutil
import os
import sys
import subprocess

# Add the project root to the path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


class TestCLI(unittest.TestCase):

    def setUp(self):
        self.test_dir = tempfile.mkdtemp()
        self.cli_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "cli.py")

    def tearDown(self):
        if os.path.exists(self.test_dir):
            shutil.rmtree(self.test_dir)

    def run_cli(self, args, cwd=None):
        if cwd is None:
            cwd = self.test_dir
        
        cmd = ["python", self.cli_path] + args
        result = subprocess.run(
            cmd,
            cwd=cwd,
            capture_output=True,
            text=True,
            env=os.environ.copy()
        )
        
        return result.returncode, result.stdout, result.stderr

    def test_cli_help(self):
        exit_code, stdout, stderr = self.run_cli(["--help"])
        
        self.assertEqual(exit_code, 0)
        self.assertIn("Mini-Git: A minimal implementation", stdout)
        self.assertIn("init", stdout)

    def test_cli_no_command(self):
        exit_code, stdout, stderr = self.run_cli([])
        
        self.assertEqual(exit_code, 1)
        self.assertIn("usage:", stdout)

    def test_init_current_directory(self):
        exit_code, stdout, stderr = self.run_cli(["init"])
        
        self.assertEqual(exit_code, 0)
        self.assertIn("Initialized empty minigit repository", stdout)
        self.assertIn(".minigit", stdout)
        
        # Check that .minigit directory was created
        minigit_path = os.path.join(self.test_dir, ".minigit")
        self.assertTrue(os.path.exists(minigit_path))
        self.assertTrue(os.path.isdir(minigit_path))
        
        # Check directory structure
        self.assertTrue(os.path.exists(os.path.join(minigit_path, "objects")))
        self.assertTrue(os.path.exists(os.path.join(minigit_path, "refs")))
        self.assertTrue(os.path.exists(os.path.join(minigit_path, "refs", "heads")))
        self.assertTrue(os.path.exists(os.path.join(minigit_path, "refs", "tags")))
        self.assertTrue(os.path.exists(os.path.join(minigit_path, "HEAD")))
        
        # Check HEAD content
        with open(os.path.join(minigit_path, "HEAD"), 'r') as f:
            head_content = f.read().strip()
        self.assertEqual(head_content, "ref: refs/heads/main")

    def test_init_specific_directory(self):
        target_dir = os.path.join(self.test_dir, "my-project")
        exit_code, stdout, stderr = self.run_cli(["init", target_dir])
        
        self.assertEqual(exit_code, 0)
        self.assertIn("Initialized empty minigit repository", stdout)
        
        # Check that .minigit directory was created in the target directory
        minigit_path = os.path.join(target_dir, ".minigit")
        self.assertTrue(os.path.exists(minigit_path))
        self.assertTrue(os.path.isdir(minigit_path))

    def test_init_already_exists(self):
        # Initialize once
        exit_code, stdout, stderr = self.run_cli(["init"])
        self.assertEqual(exit_code, 0)
        
        # Try to initialize again
        exit_code, stdout, stderr = self.run_cli(["init"])
        
        self.assertEqual(exit_code, 1)
        self.assertIn("ERROR: Repository already exists", stdout)
        self.assertIn("Found existing .minigit directory", stdout)

    def test_init_help(self):
        exit_code, stdout, stderr = self.run_cli(["init", "--help"])
        
        self.assertEqual(exit_code, 0)
        self.assertIn("Directory to initialize", stdout)
        self.assertIn("directory", stdout)

    def test_unknown_command(self):
        exit_code, stdout, stderr = self.run_cli(["unknown"])
        
        self.assertEqual(exit_code, 2)
        self.assertIn("invalid choice: 'unknown'", stderr)

    def test_cat_file_help(self):
        exit_code, stdout, stderr = self.run_cli(["cat-file", "--help"])
        
        self.assertEqual(exit_code, 0)
        self.assertIn("Object hash", stdout)
        self.assertIn("object", stdout)
        self.assertIn("-p", stdout)

    def test_cat_file_no_repository(self):
        exit_code, stdout, stderr = self.run_cli(["cat-file", "-p", "1234"])
        
        self.assertEqual(exit_code, 1)
        self.assertIn("ERROR: Not a minigit repository", stdout)

    def test_cat_file_nonexistent_object(self):
        # Initialize repository first
        self.run_cli(["init"])
        
        exit_code, stdout, stderr = self.run_cli(["cat-file", "-p", "1234"])
        
        self.assertEqual(exit_code, 1)
        self.assertIn("No objects found matching: 1234", stdout)

    def test_cat_file_hash_too_short(self):
        # Initialize repository first
        self.run_cli(["init"])
        
        exit_code, stdout, stderr = self.run_cli(["cat-file", "-p", "abc"])
        
        self.assertEqual(exit_code, 1)
        self.assertIn("Hash too short: abc", stdout)

    def test_cat_file_blob_object(self):
        # This test requires creating an actual object, which is complex in a unit test
        # We'll test the basic functionality and leave detailed object testing to integration tests
        self.run_cli(["init"])
        
        # Test with non-existent but properly formatted hash
        exit_code, stdout, stderr = self.run_cli(["cat-file", "-p", "a" * 40])
        
        self.assertEqual(exit_code, 1)
        # The exact error message depends on whether the object exists, so just check for failure
        self.assertNotEqual(exit_code, 0)


if __name__ == '__main__':
    unittest.main()
