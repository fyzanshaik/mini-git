from minigit import MinigitObject
import time

class Commit(MinigitObject):

    def __init__(self, tree_hash=None, parent_hash=None, author=None, committer=None, message=""):
        self.tree_hash = tree_hash
        self.parent_hash = parent_hash
        #if the author is not provided, we use a default value, I could change this to be changed in cli command
        self.author = author or "Unknown <unknown@example.com>"
        self.committer = committer or self.author
        self.message = message
        self.timestamp = int(time.time())
        self.timezone = "+0000"
        
        super().__init__()
        self._build_commit_data()
        print(f"[Commit] Created commit with tree {tree_hash}")

    def get_type(self):
        return "commit"

    def _build_commit_data(self):
        commit_lines = []
        
        if self.tree_hash:
            commit_lines.append(f"tree {self.tree_hash}")
        
        if self.parent_hash:
            commit_lines.append(f"parent {self.parent_hash}")
        
        commit_lines.append(f"author {self.author} {self.timestamp} {self.timezone}")
        commit_lines.append(f"committer {self.committer} {self.timestamp} {self.timezone}")
        commit_lines.append("")
        commit_lines.append(self.message)
        
        commit_content = "\n".join(commit_lines)
        self.data = commit_content.encode('utf-8')
        
        print(f"[Commit] Built commit data: {len(self.data)} bytes")

    def set_tree(self, tree_hash):
        self.tree_hash = tree_hash
        self._build_commit_data()
        print(f"[Commit] Set tree hash to {tree_hash}")

    def set_parent(self, parent_hash):
        self.parent_hash = parent_hash
        self._build_commit_data()
        print(f"[Commit] Set parent hash to {parent_hash}")

    def set_message(self, message):
        self.message = message
        self._build_commit_data()
        print(f"[Commit] Set message: {message}")

    def set_author(self, author):
        self.author = author
        self._build_commit_data()
        print(f"[Commit] Set author: {author}")

    @classmethod
    def parse_commit_data(cls, commit_data):
        if isinstance(commit_data, bytes):
            commit_data = commit_data.decode('utf-8')
        
        lines = commit_data.split('\n')
        print(lines)
        tree_hash = None
        parent_hash = None
        author = None
        committer = None
        message_lines = []
        
        in_message = False
        
        for line in lines:
            if in_message:
                message_lines.append(line)
            elif line.startswith('tree '):
                tree_hash = line[5:]
            elif line.startswith('parent '):
                parent_hash = line[7:]
            elif line.startswith('author '):
                author = line[7:]
            elif line.startswith('committer '):
                committer = line[10:]
            elif line == '':
                in_message = True
        
        message = '\n'.join(message_lines)
        
        commit = cls(tree_hash, parent_hash, author, committer, message)
        print(commit)
        
        print(f"[Commit] Parsed commit: tree={tree_hash}, parent={parent_hash}")
        return commit

    def display_commit(self):
        print(f"[Commit] Commit Information:")
        print(f"  Tree: {self.tree_hash}")
        if self.parent_hash:
            print(f"  Parent: {self.parent_hash}")
        else:
            print(f"  Parent: (none - initial commit)")
        print(f"  Author: {self.author}")
        print(f"  Committer: {self.committer}")
        print(f"  Timestamp: {self.timestamp}")
        print(f"  Message: {self.message}")

    def is_initial_commit(self):
        return self.parent_hash is None

    def get_commit_info(self):
        return {
            'tree': self.tree_hash,
            'parent': self.parent_hash,
            'author': self.author,
            'committer': self.committer,
            'timestamp': self.timestamp,
            'message': self.message,
            'is_initial': self.is_initial_commit()
        }
