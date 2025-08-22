import os
import importlib.util
from minigit import MinigitObject

def load_module(module_name, file_path):
    spec = importlib.util.spec_from_file_location(module_name, file_path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module

script_dir = os.path.dirname(os.path.abspath(__file__))
blob_module = load_module("blob_object", os.path.join(script_dir, "blob-object.py"))
tree_module = load_module("tree_object", os.path.join(script_dir, "tree-object.py"))
commit_module = load_module("commit_object", os.path.join(script_dir, "commit-object.py"))

Blob = blob_module.Blob
Tree = tree_module.Tree
Commit = commit_module.Commit


class Repository:

    def __init__(self, repo_path="."):
        self.repo_path = os.path.abspath(repo_path)
        self.minigit_path = os.path.join(self.repo_path, ".minigit")
        self.objects_path = os.path.join(self.minigit_path, "objects")
        self.refs_path = os.path.join(self.minigit_path, "refs")
        self.heads_path = os.path.join(self.refs_path, "heads")
        self.head_file = os.path.join(self.minigit_path, "HEAD")
        self.index_file = os.path.join(self.minigit_path, "index")
        
        print(f"[Repository] Initialized repository at {self.repo_path}")

    def exists(self):
        return os.path.exists(self.minigit_path) and os.path.isdir(self.minigit_path)

    def create(self):
        if self.exists():
            print(f"[Repository] Repository already exists at {self.repo_path}")
            return False
        
        print(f"[Repository] Creating new repository at {self.repo_path}")
        
        os.makedirs(self.objects_path, exist_ok=True)
        os.makedirs(self.heads_path, exist_ok=True)
        os.makedirs(os.path.join(self.refs_path, "tags"), exist_ok=True)
        
        with open(self.head_file, 'w') as f:
            f.write("ref: refs/heads/main\n")
        
        print(f"[Repository] Created .minigit directory structure")
        return True

    def store_object(self, obj):
        if not isinstance(obj, MinigitObject):
            raise ValueError("Object must be a MinigitObject")
        
        hash_value = obj.calculate_hash()
        dir_name, filename = obj.get_storage_path_components()
        
        object_dir = os.path.join(self.objects_path, dir_name)
        os.makedirs(object_dir, exist_ok=True)
        
        object_file = os.path.join(object_dir, filename)
        
        if os.path.exists(object_file):
            print(f"[Repository] Object {hash_value} already exists")
            return hash_value
        
        compressed_data = obj.compress_data()
        
        with open(object_file, 'wb') as f:
            f.write(compressed_data)
        
        print(f"[Repository] Stored object {hash_value} ({len(compressed_data)} bytes)")
        return hash_value

    def load_object(self, hash_value):
        if len(hash_value) != 40:
            raise ValueError("Hash must be 40 characters")
        
        dir_name = hash_value[:2]
        filename = hash_value[2:]
        
        object_file = os.path.join(self.objects_path, dir_name, filename)
        
        if not os.path.exists(object_file):
            raise FileNotFoundError(f"Object {hash_value} not found")
        
        with open(object_file, 'rb') as f:
            compressed_data = f.read()
        
        decompressed_data = MinigitObject.decompress_data(compressed_data)
        obj_type, size, content = MinigitObject.parse_object_data(decompressed_data)
        
        print(f"[Repository] Loaded object {hash_value} (type: {obj_type}, size: {size})")
        
        if obj_type == "blob":
            blob = Blob(content)
            blob.hash = hash_value
            return blob
        elif obj_type == "tree":
            tree = Tree()
            tree.data = content
            tree.parse_tree_data(content)
            tree.hash = hash_value
            return tree
        elif obj_type == "commit":
            commit = Commit.parse_commit_data(content)
            commit.hash = hash_value
            return commit
        else:
            raise ValueError(f"Unknown object type: {obj_type}")

    def object_exists(self, hash_value):
        dir_name = hash_value[:2]
        filename = hash_value[2:]
        object_file = os.path.join(self.objects_path, dir_name, filename)
        return os.path.exists(object_file)

    def get_head(self):
        if not os.path.exists(self.head_file):
            return None
        
        with open(self.head_file, 'r') as f:
            head_content = f.read().strip()
        
        if head_content.startswith("ref: "):
            ref_path = head_content[5:]
            ref_file = os.path.join(self.minigit_path, ref_path)
            
            if not os.path.exists(ref_file):
                return None
            
            with open(ref_file, 'r') as f:
                commit_hash = f.read().strip()
            
            print(f"[Repository] HEAD points to {ref_path} -> {commit_hash}")
            return commit_hash
        else:
            print(f"[Repository] HEAD points directly to {head_content}")
            return head_content

    def update_branch(self, branch_name, commit_hash):
        branch_file = os.path.join(self.heads_path, branch_name)
        
        with open(branch_file, 'w') as f:
            f.write(commit_hash + '\n')
        
        print(f"[Repository] Updated branch {branch_name} to {commit_hash}")

    def get_current_branch(self):
        if not os.path.exists(self.head_file):
            return None
        
        with open(self.head_file, 'r') as f:
            head_content = f.read().strip()
        
        if head_content.startswith("ref: refs/heads/"):
            return head_content[16:]
        
        return None

    def list_objects(self):
        objects = []
        
        if not os.path.exists(self.objects_path):
            return objects
        
        for dir_name in os.listdir(self.objects_path):
            dir_path = os.path.join(self.objects_path, dir_name)
            
            if not os.path.isdir(dir_path) or len(dir_name) != 2:
                continue
            
            for filename in os.listdir(dir_path):
                if len(filename) == 38:
                    hash_value = dir_name + filename
                    objects.append(hash_value)
        
        print(f"[Repository] Found {len(objects)} objects")
        return objects

    def get_working_directory(self):
        return self.repo_path

    def get_minigit_path(self):
        return self.minigit_path

    def resolve_hash(self, short_hash):
        if len(short_hash) == 40:
            return short_hash if self.object_exists(short_hash) else None
        
        if len(short_hash) < 4:
            print(f"[Repository] Hash too short: {short_hash} (minimum 4 characters)")
            return None
        
        matching_hashes = []
        all_objects = self.list_objects()
        
        for obj_hash in all_objects:
            if obj_hash.startswith(short_hash):
                matching_hashes.append(obj_hash)
        
        if len(matching_hashes) == 0:
            print(f"[Repository] No objects found matching: {short_hash}")
            return None
        elif len(matching_hashes) == 1:
            print(f"[Repository] Resolved {short_hash} -> {matching_hashes[0]}")
            return matching_hashes[0]
        else:
            print(f"[Repository] Ambiguous hash {short_hash}, matches:")
            for match in matching_hashes[:5]:
                print(f"[Repository]   {match}")
            if len(matching_hashes) > 5:
                print(f"[Repository]   ... and {len(matching_hashes) - 5} more")
            return None

    def get_working_files(self):
        working_files = []
        minigit_dir = os.path.basename(self.minigit_path)
        
        for root, dirs, files in os.walk(self.repo_path):
            if minigit_dir in dirs:
                dirs.remove(minigit_dir)
            
            for file in files:
                file_path = os.path.join(root, file)
                rel_path = os.path.relpath(file_path, self.repo_path)
                working_files.append(rel_path)
        
        return working_files

    def get_head_commit(self):
        head_hash = self.get_head()
        if head_hash is None:
            return None
        
        try:
            return self.load_object(head_hash)
        except:
            return None

    def get_head_tree(self):
        head_commit = self.get_head_commit()
        if head_commit is None:
            return None
        
        try:
            return self.load_object(head_commit.tree_hash)
        except:
            return None

    def get_file_status(self, file_path):
        full_path = os.path.join(self.repo_path, file_path)
        
        if not os.path.exists(full_path):
            return "deleted"
        
        try:
            with open(full_path, 'rb') as f:
                content = f.read()
            
            # Use the already loaded Blob class from module imports
            blob = Blob(content)
            current_hash = blob.calculate_hash()
            
            head_tree = self.get_head_tree()
            if head_tree is None:
                return "untracked"
            
            for entry in head_tree.entries:
                if entry['name'] == file_path:
                    if entry['hash'] == current_hash:
                        return "unmodified"
                    else:
                        return "modified"
            
            return "untracked"
            
        except Exception:
            return "error"

    def read_index(self):
        if not os.path.exists(self.index_file):
            return {}
        
        try:
            index = {}
            with open(self.index_file, 'r') as f:
                for line in f:
                    line = line.strip()
                    if line and ' ' in line:
                        hash_value, file_path = line.split(' ', 1)
                        index[file_path] = hash_value
            print(f"[Repository] Read index with {len(index)} entries")
            return index
        except Exception as e:
            print(f"[Repository] Error reading index: {e}")
            return {}

    def write_index(self, index):
        try:
            with open(self.index_file, 'w') as f:
                for file_path, hash_value in sorted(index.items()):
                    f.write(f"{hash_value} {file_path}\n")
            print(f"[Repository] Wrote index with {len(index)} entries")
        except Exception as e:
            print(f"[Repository] Error writing index: {e}")

    def add_to_index(self, file_path):
        full_path = os.path.join(self.repo_path, file_path)
        
        if not os.path.exists(full_path):
            print(f"[Repository] File not found: {file_path}")
            return None
        
        if os.path.isdir(full_path):
            print(f"[Repository] Cannot add directory: {file_path}")
            return None
        
        try:
            blob = Blob.from_file(full_path)
            hash_value = self.store_object(blob)
            
            index = self.read_index()
            index[file_path] = hash_value
            self.write_index(index)
            
            print(f"[Repository] Added {file_path} to index (hash: {hash_value[:8]})")
            return hash_value
            
        except Exception as e:
            print(f"[Repository] Error adding {file_path}: {e}")
            return None

    def get_staged_files(self):
        return self.read_index()

    def is_staged(self, file_path):
        index = self.read_index()
        return file_path in index

    def get_file_status_detailed(self, file_path):
        full_path = os.path.join(self.repo_path, file_path)
        
        if not os.path.exists(full_path):
            if self.is_staged(file_path):
                return "deleted_staged"
            return "deleted"
        
        try:
            with open(full_path, 'rb') as f:
                content = f.read()
            
            blob = Blob(content)
            current_hash = blob.calculate_hash()
            
            index = self.read_index()
            staged_hash = index.get(file_path)
            
            head_tree = self.get_head_tree()
            committed_hash = None
            
            if head_tree:
                for entry in head_tree.entries:
                    if entry['name'] == file_path:
                        committed_hash = entry['hash']
                        break
            
            if staged_hash:
                if staged_hash == current_hash:
                    if committed_hash == current_hash:
                        return "unmodified"
                    else:
                        return "staged"
                else:
                    return "modified_after_staging"
            else:
                if committed_hash:
                    if committed_hash == current_hash:
                        return "unmodified"
                    else:
                        return "modified"
                else:
                    return "untracked"
                    
        except Exception:
            return "error"

    def create_commit(self, message, author=None):
        staged_files = self.get_staged_files()
        
        if not staged_files:
            print("[Repository] No files staged for commit")
            return None
        
        print(f"[Repository] Creating commit with {len(staged_files)} staged files")
        
        # Build complete tree: staged files + unchanged files from parent
        all_files = {}
        
        # First, get all files from parent commit (if exists)
        parent_hash = self.get_head()
        if parent_hash:
            try:
                parent_commit = self.load_object(parent_hash)
                if parent_commit.get_type() == "commit":
                    parent_tree = self.load_object(parent_commit.tree_hash)
                    # Add all files from parent tree
                    for entry in parent_tree.entries:
                        all_files[entry['name']] = entry['hash']
                    print(f"[Repository] Inherited {len(parent_tree.entries)} files from parent commit")
            except Exception as e:
                print(f"[Repository] Warning: Could not load parent commit: {e}")
        
        # override with staged files (new/modified files) so that I can see the changes, this works for some reason 
        all_files.update(staged_files)
        
        tree = Tree()
        for file_path, hash_value in all_files.items():
            tree.add_entry("100644", file_path, hash_value)
        
        tree_hash = self.store_object(tree)
        print(f"[Repository] Created tree {tree_hash[:8]} with {len(all_files)} total entries ({len(staged_files)} staged)")
        
        parent_hash = self.get_head()
        
        commit = Commit(
            tree_hash=tree_hash,
            parent_hash=parent_hash,
            author=author,
            message=message
        )
        
        commit_hash = self.store_object(commit)
        print(f"[Repository] Created commit {commit_hash[:8]}")
        
        current_branch = self.get_current_branch()
        if current_branch:
            self.update_branch(current_branch, commit_hash)
            print(f"[Repository] Updated branch {current_branch} -> {commit_hash[:8]}")
        else:
            self.update_head(commit_hash)
            print(f"[Repository] Updated HEAD -> {commit_hash[:8]}")
        
        self.write_index({})
        print("[Repository] Cleared staging area")
        
        return commit_hash

    def get_commit_history(self, start_hash=None, max_commits=None):
        if start_hash is None:
            start_hash = self.get_head()
        
        if start_hash is None:
            return []
        
        history = []
        current_hash = start_hash
        count = 0
        
        while current_hash and (max_commits is None or count < max_commits):
            try:
                commit = self.load_object(current_hash)
                if commit.get_type() != "commit":
                    break
                
                history.append((current_hash, commit))
                current_hash = commit.parent_hash
                count += 1
                
            except Exception as e:
                print(f"[Repository] Error loading commit {current_hash}: {e}")
                break
        
        return history

    def get_branch_head(self, branch_name):
        branch_file = os.path.join(self.heads_path, branch_name)
        if not os.path.exists(branch_file):
            return None
        
        with open(branch_file, 'r') as f:
            return f.read().strip()

    def get_commit_chain(self):
        """Get the full commit chain from main branch head backwards"""
        # Always use main branch to get the full commit chain
        # This ensures we see all commits even when HEAD is detached
        branch_head = self.get_branch_head("main")
        
        if not branch_head:
            return []
        
        history = []
        current_hash = branch_head
        
        while current_hash:
            try:
                commit = self.load_object(current_hash)
                if commit.get_type() != "commit":
                    break
                    
                history.append(current_hash)
                current_hash = commit.parent_hash
                
            except Exception as e:
                print(f"[Repository] Error loading commit {current_hash}: {e}")
                break
        
        return history

    def get_current_commit_position(self):
        """Get current commit and its position in the chain"""
        current_hash = self.get_head()
        if not current_hash:
            return None, -1
        
        chain = self.get_commit_chain()
        try:
            position = chain.index(current_hash)
            return current_hash, position
        except ValueError:
            return current_hash, 0
    #this is just for my own simplicity and i dont lose my fucking head
    def move_to_commit(self, target_hash):
        """Simple commit switching - overwrites working directory with commit state"""
        full_hash = self.resolve_hash(target_hash)
        if not full_hash:
            print(f"[Repository] Error: Could not resolve hash {target_hash}")
            return False

        try:
            # Load commit and tree
            commit = self.load_object(full_hash)
            if commit.get_type() != "commit":
                print(f"[Repository] Error: {target_hash} is not a commit")
                return False

            tree = self.load_object(commit.tree_hash)
            print(f"[Repository] Moving to commit {full_hash[:8]}: {commit.message}")
            
            # Simple approach: remove tracked files and restore from tree
            self._restore_commit_state(tree)
            
            # Update HEAD directly
            with open(self.head_file, 'w') as f:
                f.write(full_hash)
            print(f"[Repository] Updated HEAD to {full_hash[:8]}")
            
            # Clear staging
            self.write_index({})
            
            print(f"[Repository] ✅ Now at {full_hash[:8]}")
            return True
            
        except Exception as e:
            print(f"[Repository] Error moving to commit: {e}")
            return False

    def move_up(self):
        """Move to newer commit (child of current)"""
        current_hash, position = self.get_current_commit_position()
        if current_hash is None:
            print("[Repository] No commits found")
            return False
            
        if position == 0:
            print("[Repository] Already at the newest commit")
            return False
            
        chain = self.get_commit_chain()
        newer_hash = chain[position - 1]
        return self.move_to_commit(newer_hash)

    def move_down(self):
        """Move to older commit (parent of current)"""
        current_hash, position = self.get_current_commit_position()
        if current_hash is None:
            print("[Repository] No commits found")
            return False
            
        chain = self.get_commit_chain()
        if position >= len(chain) - 1:
            print("[Repository] Already at the oldest commit")
            return False
            
        older_hash = chain[position + 1]
        return self.move_to_commit(older_hash)

    def _restore_commit_state(self, tree):
        """Restore working directory to match tree state"""
        current_files = set()
        for root, dirs, files in os.walk(self.repo_path):
            # Skip .minigit
            if '.minigit' in dirs:
                dirs.remove('.minigit')
            dirs[:] = [d for d in dirs if not d.startswith('.')]
            
            for file in files:
                if not file.startswith('.') and not file.endswith('.pyc'):
                    rel_path = os.path.relpath(os.path.join(root, file), self.repo_path)
                    current_files.add(rel_path)
        
        tree_files = {entry['name'] for entry in tree.entries}
        
        for file_path in current_files - tree_files:
            full_path = os.path.join(self.repo_path, file_path)
            try:
                os.remove(full_path)
                print(f"[Repository] Removed: {file_path}")
            except Exception as e:
                print(f"[Repository] Warning: Could not remove {file_path}: {e}")
        
        for entry in tree.entries:
            file_path = entry['name']
            hash_value = entry['hash']
            
            try:
                blob = self.load_object(hash_value)
                full_path = os.path.join(self.repo_path, file_path)
                
                os.makedirs(os.path.dirname(full_path), exist_ok=True)
                
                with open(full_path, 'wb') as f:
                    f.write(blob.data)
                
                print(f"[Repository] Restored: {file_path}")
                
            except Exception as e:
                print(f"[Repository] Error restoring {file_path}: {e}")

    @classmethod
    def find_repository(cls, start_path="."):
        current_path = os.path.abspath(start_path)
        
        while True:
            repo = cls(current_path)
            if repo.exists():
                print(f"[Repository] Found repository at {current_path}")
                return repo
            
            parent_path = os.path.dirname(current_path)
            if parent_path == current_path:
                break
            current_path = parent_path
        
        print(f"[Repository] No repository found starting from {start_path}")
        return None
