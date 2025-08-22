from minigit import MinigitObject

class Tree(MinigitObject):

    def __init__(self):
        self.entries = []
        super().__init__()
        print(f"[Tree] Created tree with 0 entries")

    def get_type(self):
        return "tree"

    def add_entry(self, mode, name, hash_value):
        print(f"[Tree] Adding entry: {mode} {name} {hash_value}")
        entry = {
            'mode': mode,
            'name': name,
            'hash': hash_value
        }
        self.entries.append(entry)
        self._build_tree_data()

    def _build_tree_data(self):
        if not self.entries:
            self.data = b''
            return

        sorted_entries = sorted(self.entries, key=lambda x: x['name'])
        tree_data = b''
        
        for entry in sorted_entries:
            mode = entry['mode']
            name = entry['name']
            hash_value = entry['hash']
            
            hash_binary = bytes.fromhex(hash_value)
            
            entry_line = f"{mode} {name}".encode('utf-8')
            entry_line += b'\0'
            entry_line += hash_binary
            
            tree_data += entry_line

        self.data = tree_data
        print(f"[Tree] Built tree data with {len(sorted_entries)} entries, {len(self.data)} bytes")

    def get_entries(self):
        return self.entries.copy()

    @classmethod
    def from_entries(cls, entries_list):
        tree = cls()
        for mode, name, hash_value in entries_list:
            tree.add_entry(mode, name, hash_value)
        return tree

    def parse_tree_data(self, tree_data):
        self.entries = []
        pos = 0
        
        while pos < len(tree_data):
            null_pos = tree_data.find(b'\0', pos)
            if null_pos == -1:
                break
                
            mode_name = tree_data[pos:null_pos].decode('utf-8')
            mode, name = mode_name.split(' ', 1)
            
            hash_start = null_pos + 1
            hash_end = hash_start + 20
            if hash_end > len(tree_data):
                break
                
            hash_binary = tree_data[hash_start:hash_end]
            hash_hex = hash_binary.hex()
            
            entry = {
                'mode': mode,
                'name': name,
                'hash': hash_hex
            }
            self.entries.append(entry)
            
            pos = hash_end
            
        print(f"[Tree] Parsed {len(self.entries)} entries from tree data")
        return self.entries

    def display_tree(self):
        print(f"[Tree] Tree contents ({len(self.entries)} entries):")
        for entry in sorted(self.entries, key=lambda x: x['name']):
            mode = entry['mode']
            name = entry['name']
            hash_value = entry['hash']
            obj_type = "tree" if mode == "040000" else "blob"
            print(f"  {mode} {obj_type} {hash_value} {name}")
