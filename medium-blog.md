# How I Built Git From Scratch (And You Can Too!)

Yes, I did in fact build git from scratch using Python3!

[Demo GIF/Video space - showing minigit commands in action]

**Mini-Git** is a minimalistic git implementation that performs the core operations:
- `init` - initialize repository
- `add` - stage files  
- `commit` - create commits
- `status` - show working directory status
- `log` - show commit history
- `cat-file` - inspect objects by decompressing
- `move u/d` - navigate through commit history
- `checkout` - jump to specific commits

---

## Why I Built This

As a new engineering student, I was tired of building CRUD apps that any AI could implement in minutes. I wanted something challenging that would teach me computer science fundamentals from first principles.

After completing Python3, functional programming, and OOP courses at Boot.dev, I needed a personal project. Instead of building another web app, I chose to reverse-engineer Git - one of the most fundamental tools every developer uses.

## What is Git, Really?

If you're not familiar with Git, it's a Version Control System that's been the backbone of software development since 2005. Think of it like save points in a video game - you can save snapshots of your code and jump back to any previous state.

But here's the secret most developers don't know: **Git is just a fancy key-value store**.

## The Core Insight: Objects All The Way Down

Git uses this one fundamental principle of storing everything as **objects**. At its core, this is a __key-value__ store where the key is obtained by hashing the contents of any file. 

Let's understand hashing quickly: 
Algorithms such as SHA1 (which git uses) take any data and create a hashed value of it which is a 40-character string. What makes this useful is that data when hashed produces the same result all the time! Which means as long as the content doesn't change even by a single character, we can trust the hash value to always be reproducible. 

Hence this fundamental principle which governs the object database is **content addressing**.

### Understanding Objects:

Git stores everything as "objects" - not programming objects, but data objects on your filesystem. The magic formula is:

```python
# Any content → Header → Hash → Storage location
content = b"Hello World"
header = f"blob {len(content)}\0".encode()
full_data = header + content  # "blob 11\0Hello World"
hash_key = hashlib.sha1(full_data).hexdigest()

# Result: "557db03de997c86a4a028e1ebd3a1ceb225be238"
# Stored at: .git/objects/55/7db03de997c86a4a028e1ebd3a1ceb225be238
```

**This is everything.** Same content = same hash = same storage location. Git never stores duplicate data.

At every file which is added for staging, every commit that you do, git creates 3 objects all the time: 
**blob**: Any file at its current state
**trees**: Directory structure which consists information on all blobs and their structure at that snapshot
**commit**: Historical snapshots of the current tree

You can verify this on your own by creating an empty repo, initializing git and make a few commits. Check the .git/objects folder: 
This is how .git folder looks like for mini-git itself (Yes I used git for my own mini-git), and this is exactly how mini-git stores objects too!(eg: .mini-git/objects)

[example .git folder](image-git.png ".git/objects")

Every time you **add** a file to staging area, git takes its data, prepends a header in the format `<type> <size>\0 <data>`, hashes this information and using the hash it takes the first **2** characters as a subdirectory for that object and the rest 38 characters as file name. 

Now before it saves the file, it **compresses** the file to save space (You can confirm this by opening any of the files, you'll find garbage values that aren't readable).

## The Three Object Types (Your Building Blocks)

I spent days just trying to figure out the theory of this and as soon as I understood each and every object's role it clicked me quick and I started implementing this. The code is pretty simple, it might look verbose due to my *skill issue ahem* but hey it works well.

Git uses just three object types to store your entire project history:

### 1. Blob Objects (Files)
```python
class Blob(MinigitObject):
    def __init__(self, data):
        if isinstance(data, str):
            data = data.encode('utf-8')  # Convert strings to bytes
        super().__init__(data)
    
    def get_type(self):
        return "blob"
    
    @classmethod
    def from_file(cls, file_path):
        with open(file_path, 'rb') as f:
            content = f.read()
        return cls(content)
    
    def save_to_file(self, file_path):
        with open(file_path, 'wb') as f:
            f.write(self.data)
```

Blobs are the simplest objects. They just store raw file content with absolutely no metadata. No filename, no permissions, no timestamps. Just pure, unadulterated data. Think of them as the actual soul of your files, stripped of everything else.

### 2. Tree Objects (Directories)  
```python
class Tree(MinigitObject):
    def __init__(self):
        super().__init__()
        self.entries = []
    
    def get_type(self):
        return "tree"
    
    def add_entry(self, mode, name, hash_value):
        entry = {
            'mode': mode,     # "100644" for files, "040000" for directories
            'name': name,     # filename or directory name
            'hash': hash_value # points to blob or another tree
        }
        self.entries.append(entry)
        self._build_tree_data()  # Convert to binary format
    
    def _build_tree_data(self):
        # Sort entries and convert to Git's binary tree format
        sorted_entries = sorted(self.entries, key=lambda x: x['name'])
        tree_data = b''
        for entry in sorted_entries:
            # Build: "mode name\0hash_binary"
            entry_line = f"{entry['mode']} {entry['name']}".encode()
            entry_line += b'\0' + bytes.fromhex(entry['hash'])
            tree_data += entry_line
        self.data = tree_data
```

Trees are like your project's table of contents. They map filenames to their actual content (blobs) and can point to other trees for subdirectories. Basically, they're the ones keeping track of "what's where" in your project.

### 3. Commit Objects (History)
```python
class Commit(MinigitObject):
    def __init__(self, tree_hash, parent_hash=None, author=None, message=""):
        super().__init__()
        self.tree_hash = tree_hash
        self.parent_hash = parent_hash
        self.author = author or "Unknown <unknown@example.com>"
        self.message = message
        self.timestamp = int(time.time())
        self._build_commit_data()
    
    def get_type(self):
        return "commit"
    
    def _build_commit_data(self):
        commit_lines = []
        commit_lines.append(f"tree {self.tree_hash}")
        if self.parent_hash:
            commit_lines.append(f"parent {self.parent_hash}")
        commit_lines.append(f"author {self.author} {self.timestamp} +0000")
        commit_lines.append(f"committer {self.author} {self.timestamp} +0000")
        commit_lines.append("")  # Empty line before message
        commit_lines.append(self.message)
        
        self.data = "\n".join(commit_lines).encode('utf-8')
```

Commits are the storytellers. They point to a tree (your project snapshot) and link to their parent commit, creating a chain of history. They're basically saying "here's what the project looked like at this moment, and here's what happened before me".

## Experiment Time!

**NOTE**: Before you experiment this add this to your IDE's workspace setting 
```json
{
    "files.exclude": {
        "**/.git": false,
        "**/.minigit": false
    }
}
```

By default IDE's hide these folders for simplicity, you can always remove it and get back to default!

The best way you can see what each of these objects store is by using the **git cat-file -p** command and specify just the starting 4 characters of any hash. 

The cat-file decompresses the compressed files and prints on the terminal in their original form. 

Let's take a small example: 
1. Initialize the repo by `git init` → it creates the .git folder
2. Create a new file with some data and stage it by `echo "123" > 1.txt && git add 1.txt` → it creates an obj 

[Blob Object](first-obj.png "Shows new obj in .git/objects folder")

3. Now commit by `git commit -m "first commit"` → it creates 2 new objects 

[Tree and Commit Object](commit-obj.png)

4. Do a `git log` and you can see a message appear which consists of 
   - commit <hash>
   - Author 
   - Date
   - With metadata of your branch information too

If you look at the initial 2 characters of the hash you can find it inside .git/objects that is your commit obj!

Let's quickly do a cat-file -p for each hash we see, start with the commit hash: `git cat-file -p f380`
```
tree 69cd72f31a128f0336ef3e01ccbe0c50ea60e6b6
author fyzanshaik <fyzan.shaik@gmail.com> 1755943449 +0530
committer fyzanshaik <fyzan.shaik@gmail.com> 1755943449 +0530

1
```
Isn't this exactly what we see when we do git log? But this is just for one commit, now lets do this for the tree commit: 
`git cat-file -p 69cd` 
```
100644 blob 190a18037c64c43e6b11489df4bf0b9eb6d2c9bf    1.txt
```
This is our tree commit, we will come to this later but this stores all "indexed" files or staged files for the current commit. 

and finally lets do it again for our blob hash: 
`git cat-file -p 190a`
```
hello world!
```

This prints the data I stored but for you it could be different, you will have completely different hash too.

Now if we take a step back doesn't all of this seem more easier? It's so simple but at the same time amazing how such a small principle can help us build our own VCS!  

## The Three States: Where Your Files Live

Git operates on three different "states" of your files:

```
Working Directory  →   Staging Area   →   Repository
    (files)           (.git/index)       (.git/objects)
```

1. **Working Directory**: Files you can see and edit
2. **Staging Area**: Files marked for the next commit
3. **Repository**: Permanent object storage

## How Git Commands Actually Work

Once you understand objects, Git commands become obvious:

**`git add file.txt`** → Create blob object + add to staging area
**`git commit`** → Create tree from staging + create commit object + update branch  
**`git checkout abc123`** → Load commit → load tree → restore files to working directory

## Building Your Own: The Architecture

Now here's where the fun begins! I used an OOP architecture for my own ease of writing code, but honestly, this could be done much better with functional programming. But hey, objects made sense when dealing with... well, objects!

### The Base Class: MinigitObject

Every object in my implementation inherits from this base class:

```python
class MinigitObject(ABC):
    def __init__(self, data=None):
        self.data = data if data is not None else b''
        self.hash = None

    @abstractmethod
    def get_type(self):
        pass

    def create_header(self):
        obj_type = self.get_type()
        size = len(self.data)
        return f"{obj_type} {size}\0".encode('utf-8')

    def calculate_hash(self):
        full_data = self.create_header() + self.data
        self.hash = hashlib.sha1(full_data).hexdigest()
        return self.hash

    def compress_data(self):
        full_data = self.create_header() + self.data
        return zlib.compress(full_data)
```

This handles all the common object operations: header creation, hashing, and compression.

### The Concrete Classes

Each object type just needs to implement `get_type()` and handle its specific data format:

**Blob Class**: Super simple, just stores raw data
**Tree Class**: Manages entries and builds binary tree format
**Commit Class**: Handles commit metadata and parent linking

### The Repository Class: The Orchestra Conductor

This is where everything comes together:

```python
class Repository:
    def __init__(self, repo_path="."):
        self.repo_path = os.path.abspath(repo_path)
        self.minigit_path = os.path.join(self.repo_path, ".minigit")
        self.objects_path = os.path.join(self.minigit_path, "objects")
        # ... other paths

    def store_object(self, obj):
        hash_value = obj.calculate_hash()
        dir_name, filename = hash_value[:2], hash_value[2:]
        # ... compression and storage logic

    def load_object(self, hash_value):
        # ... decompression and object reconstruction logic
```

The Repository class handles:
Object storage and retrieval, index management (staging area), branch and HEAD management, and working directory operations. Basically, it's the boss that tells everyone else what to do.

## The Core Functions You Need

Want to implement this yourself? Start with these two functions:

### Object Storage
```python
def store_object(obj_type, content):
    # Build the object data
    header = f"{obj_type} {len(content)}\0".encode()
    full_data = header + content
    hash_value = hashlib.sha1(full_data).hexdigest()
    
    # Create storage path
    dir_name, filename = hash_value[:2], hash_value[2:]
    object_path = f".git/objects/{dir_name}/{filename}"
    
    # Compress and save
    os.makedirs(os.path.dirname(object_path), exist_ok=True)
    with open(object_path, 'wb') as f:
        f.write(zlib.compress(full_data))
    
    return hash_value
```

### Object Loading
```python
def load_object(hash_value):
    # Find the object file
    path = f".git/objects/{hash_value[:2]}/{hash_value[2:]}"
    
    # Read and decompress
    with open(path, 'rb') as f:
        compressed_data = f.read()
    data = zlib.decompress(compressed_data)
    
    # Parse header and content
    null_index = data.find(b'\0')
    header = data[:null_index].decode()
    content = data[null_index + 1:]
    
    obj_type = header.split()[0]  # "blob", "tree", or "commit"
    return obj_type, content
```

## Building Features: It's All About Reading Objects

Once you have the object system working, every Git feature becomes just reading from objects and updating files:

**DAG traversal**: Follow parent pointers in commit objects
**Logs**: Walk the commit chain and display metadata  
**Status**: Compare working directory with HEAD tree
**Checkout**: Load commit → load tree → restore files
**Diff**: Compare two tree objects

The beauty is that all these "complex" features are just different ways of reading the same three object types. It's like having Lego blocks - once you understand the basic pieces, you can build anything!

## My Implementation Highlights

What made this project special wasn't just recreating Git, it was adding my own features:

**Intuitive Navigation**: `minigit move u` and `minigit move d` for moving through commit history
**Comprehensive Status**: Detailed file status tracking (staged, modified, untracked)  
**Object Inspection**: `cat-file` command to peek inside any object
**Simple Index**: Text-based staging area instead of Git's complex binary format

## The "Aha!" Moment

The breakthrough came when I realized Git's elegance: **everything is just content-addressed storage with a simple object model on top**. 

Once the object storage worked, adding commands became straightforward:
Commands manipulate objects, objects reference other objects via hashes, and hashes ensure integrity and prevent duplicates. It's like a perfectly organized filing system!

## Want to Build Your Own?

Here's your roadmap:

1. **Start with the fundamentals**: Understand hashing and content addressing
2. **Build object storage**: Implement the store/load functions above  
3. **Create the three object types**: Start simple with just basic functionality
4. **Add the Repository class**: This orchestrates everything
5. **Implement basic commands**: `init`, `add`, `commit`
6. **Build features**: Each one is just reading objects and manipulating files

Remember: every "complex" Git feature is just a different way of reading these three object types and updating your working directory. Once you get that, you can build anything!

## Final Thoughts

Building Git from scratch taught me that the most powerful tools often have beautifully simple foundations. Git feels complex because we see all the fancy features, but underneath it's just three object types playing together.

The code might look verbose (*skill issue* on my part), but it works well and more importantly, it taught me how one of the most important tools in software development actually works.

Sometimes the best way to truly understand something is to build it yourself. Even if your version is simpler or different, the journey teaches you things no tutorial ever could.

I thought this was impossible to do for my skills, but it wasn't I did attempt this with C ( lmao) and shot myself a lot of times but I now understand the architecture completely and could probably implement it again in C. 
Best thing I did was I used Gemini 2.5 Pro(Deep research)to help me gather theory for understanding git and had a 10 page doc going through and figuring out.

I used AI for collection information, using it as my debugging duck and writing tests at the end. Other than that no code snippets were used(maybe syntax help). 
Funny enough when I asked AI to implement this it rewrote my whole code (stupid AI always acting smarter).

https://github.com/fyzanshaik/mini-git github repository.

If you have made it till here, check out my github and linkedin! I am a final year grad student looking for more challenges!