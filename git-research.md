

# **Deconstructing Git: An Architectural Blueprint for Implementation**

## **Introduction**

This report will deconstruct the Git version control system into its constituent architectural components. We will posit that Git's elegance and power derive from two fundamental computer science concepts: a **content-addressable filesystem** and a **Directed Acyclic Graph (DAG)**.1 Unlike version control systems that track deltas or file-based changes, Git operates on cryptographic snapshots of the entire project state.3 Every time a project's state is saved, Git effectively takes a picture of what all the files look like at that moment and stores a reference to that snapshot. To maintain efficiency, if files have not changed between snapshots, Git does not store the file again but instead stores a link to the previous identical file it has already stored.3 Our objective is to provide a sufficiently detailed architectural blueprint to enable the reader to implement a functional subset of Git, covering the

init, add, commit, and history traversal operations. We will focus exclusively on the foundational "loose" object format, as this is the basis for all repository interactions before storage optimization occurs.5

## **Section 1: The Bedrock of Git: A Content-Addressable Filesystem**

This section establishes the core paradigm of Git's storage model. At its lowest level, Git is not a version control system but a simple key-value data store where the key is derived directly from the value's content.6 This design choice is the source of Git's data integrity, efficiency, and distributed nature. By treating data this way, Git builds a robust foundation upon which all of its versioning features are layered.

### **1.1 The Object Database: A Key-Value Store in.git/objects**

The heart of a Git repository is the .git directory, and within it, the .git/objects directory serves as the object database.6 This database is where Git stores every piece of data essential for tracking a project's history. This includes the content of every version of every file, the structure of every directory, and the metadata associated with every commit.

The fundamental principle governing this database is **content-addressing**. When any piece of content is to be stored in Git, it is first processed through the Secure Hash Algorithm 1 (SHA-1) to generate a unique 40-character hexadecimal key.1 This SHA-1 hash is not arbitrary; it is a checksum computed from the content itself, plus a small, prepended header that identifies the type of data being stored.6 This means that any two pieces of content that are byte-for-byte identical will always produce the exact same SHA-1 hash, and therefore point to the same object in the database. This property is the basis for Git's powerful data deduplication; a file's content is stored only once, no matter how many times it appears across different commits or branches in the repository's history.2

To manage storage on the filesystem efficiently and avoid performance degradation that can occur when a single directory contains tens of thousands of files, Git employs a simple sharding strategy for its object database. The 40-character SHA-1 hash is partitioned: the first two characters are used as the name of a subdirectory within .git/objects, and the remaining 38 characters serve as the filename for the object itself within that subdirectory.2 For instance, an object with the hash

d670460b4b4aece5915caf5c68d12f560a9fe3e4 would be stored as a file at the path .git/objects/d6/70460b4b4aece5915caf5c68d12f560a9fe3e4.

This hashing mechanism is also the cornerstone of Git's data integrity. The SHA-1 hash acts as a robust checksum for the data it identifies. Whenever Git reads an object from the database, it can re-compute the hash of the retrieved content and verify that it matches the object's name. If even a single bit of the data has been altered due to disk corruption or any other reason, the computed hash will be completely different, and Git will immediately detect the corruption.1 This guarantees that the state of your project retrieved from the repository is exactly the state that was originally stored.

Finally, to conserve disk space, all objects are compressed using the zlib library before being written to the filesystem.2 When an object is read, it is first decompressed before its contents are used. This entire process—header prepending, hashing, compression, and sharded storage—forms the lifecycle of every object within the Git database.

### **1.2 The Anatomy of Git Objects**

Every object stored on disk follows a consistent structure before compression. It consists of a header that specifies the object's type and its content length in bytes, followed by a null byte (\\0) separator, and finally the object's payload or content.6 This consistent format allows Git's internal commands to handle different object types uniformly. There are three primary object types that form the building blocks of a Git repository: blobs, trees, and commits.

#### **1.2.1 Blobs: The Essence of Content**

A blob, which stands for Binary Large Object, is the simplest type of object in Git. Its sole purpose is to store the raw, uninterpreted content of a file.1 A blob is pure data; it contains no metadata about the file it represents, such as its name, path, or permissions. It is simply a byte-for-byte snapshot of a file's contents at a particular moment.

The structure of the data that is hashed to create a blob's SHA-1 identifier is straightforward. It begins with the ASCII string blob, followed by a space, the decimal representation of the content's length in bytes, a null byte separator, and then the actual content of the file.2 For example, a file containing the text "hello world" (11 bytes, plus a newline character making it 12\) would be prepared for hashing as the byte stream corresponding to

blob 12\\0hello world\\n.

The content-addressable nature of blobs means they are inherently immutable. If a file's content is changed in any way, a new blob with a completely new SHA-1 hash will be created to store the new version. The old blob remains untouched in the object database. Conversely, if two different files in the repository happen to have the exact same content, or if a file remains unchanged across multiple commits, they will all point to the same single blob object.2 This efficient reuse of blobs is a fundamental aspect of Git's storage model, preventing redundant data storage and keeping repository sizes manageable.

#### **1.2.2 Trees: The Skeleton of the Filesystem**

While blobs store file content, they do not store filenames or directory structures. This is the role of the tree object. A tree object represents a snapshot of a single directory's contents.1 It is analogous to a folder in a conventional filesystem, containing a list of entries that map filenames to their corresponding content (blobs) or subdirectories (other tree objects).

The uncompressed content of a tree object is a binary format consisting of a sequence of entries, sorted alphabetically by name. Each entry in the tree object is structured as follows: \<mode\> \<name\>\\0\<20-byte\_sha1\_hash\>.

* **Mode**: An ASCII string representing the file's permissions and type. Common modes include 100644 for a regular non-executable file, 100755 for an executable file, 120000 for a symbolic link, and 040000 for a directory, which indicates that the associated hash points to another tree object.2  
* **Name**: The filename or subdirectory name as a UTF-8 encoded string.  
* **Null Separator**: A single null byte (\\0) separates the name from the hash.  
* **SHA-1 Hash**: The 20-byte raw binary representation of the SHA-1 hash of the blob or tree object being referenced. This is not the 40-character hexadecimal string, but its binary equivalent.

Because a tree object can contain references to other tree objects, a single "root" tree can represent the entire hierarchical structure of a project. Each subdirectory is represented by its own tree object, which is in turn referenced by its parent directory's tree object, forming a recursive structure that mirrors the project's layout on the filesystem.18

#### **1.2.3 Commits: The Fabric of History**

The commit object is the data structure that brings blobs and trees together to form a cohesive, historical record. A commit object represents a single, specific snapshot of the entire project at a point in time. It does this by pointing to a single root tree object and enriching it with crucial metadata: who made the change, when it was made, why it was made, and how it connects to the project's history.1

The uncompressed content of a commit object is a plain-text set of key-value pairs, followed by the commit message. The structure is as follows:

* tree \<sha1\_of\_root\_tree\>: A line specifying the 40-character SHA-1 hash of the top-level tree object that represents the complete state of the project for this commit.  
* parent \<sha1\_of\_parent\_commit\>: One or more lines specifying the hash(es) of the immediate parent commit(s). An initial commit has no parent lines. A standard commit has exactly one parent. A merge commit, which combines two or more lines of development, will have two or more parent lines.4  
* author \<name\> \<email\> \<timestamp\> \<timezone\>: Information about the person who originally wrote the code. The timestamp is a standard Unix epoch time.  
* committer \<name\> \<email\> \<timestamp\> \<timezone\>: Information about the person who created the commit. This can differ from the author, for example, in cases where a patch is applied by a project maintainer or during a rebase operation.  
* An empty line separates the header from the commit message.  
* The user-provided commit message follows the empty line.

A clear example of this structure can be seen by inspecting a commit object with Git's internal tools, such as git cat-file \-p \<commit-hash\>, which will print this formatted metadata and message.6

The architectural decision to decouple content (blob), structure (tree), and history (commit) into distinct object types is a source of immense power and efficiency. A blob is entirely defined by its data and knows nothing of its filename or location. A tree object maps names to blobs and other trees but is unaware of the history that led to its creation. A commit object links a specific tree to a point in history but does not directly contain any file data. This separation allows for operations like renaming a file to be incredibly cheap. A rename does not alter the file's content, so its blob hash remains the same. Git only needs to create a new tree object that includes an entry with the new filename pointing to the *existing* blob. The parent tree(s) must then be updated to point to this new tree, but the vast majority of objects in the repository remain untouched.

Furthermore, this content-addressable model creates a powerful cryptographic chain of integrity that ripples through the entire repository. A change to a single byte in a single file will result in a new blob with a new SHA-1 hash.10 Because this blob's hash is different, the tree object that contains its entry must be updated, which in turn generates a new hash for that tree.20 This change propagates up through all parent tree objects until it reaches the root tree, which will also have a new hash. Finally, because the commit object's content includes the hash of the root tree, the commit itself will have a new and completely different SHA-1 hash.21 This means that a commit hash is a secure, unique fingerprint of the

*entire state* of the project at that moment. It is cryptographically impossible to alter any part of a project's history—be it file content, a filename, or commit metadata—without this change being immediately detectable, as it would break the chain of SHA-1 hashes that extends back to the very first commit.

| Object Type | Purpose | Content Structure (Pre-Hash) | Key Metadata |
| :---- | :---- | :---- | :---- |
| **Blob** | Stores raw file content, agnostic of filename. | blob \<content-length\>\\0\<actual-content\> | None (pure data) |
| **Tree** | Represents a directory snapshot, mapping names to blobs and sub-trees. | A sorted sequence of entries: \<mode\> \<name\>\\0\<20-byte\_sha1\_hash\> | File/directory mode, name, and the hash of the referenced object. |
| **Commit** | Links a tree to a point in history with metadata. | tree \<sha1\_of\_root\_tree\>\\nparent \<sha1\_of\_parent\_commit\>...\\nauthor...\\ncommitter...\\n\\n\<commit\_message\> | Root tree hash, parent commit hash(es), author/committer info, and message. |

## **Section 2: Managing State: The Three Trees of Git**

To understand how Git manages the transition of file modifications into permanent history, it is useful to think in terms of three conceptual "trees" or states that a project's files can occupy.3 These are the Working Directory, the Index (or Staging Area), and the Repository itself. The commands

git add and git commit are the mechanisms that move changes between these states.

### **2.1 Conceptual Data Flow: Working Directory, Index, and Repository**

The three primary states of a Git project form a clear workflow:

1. **Working Directory (or Working Tree):** This is the user-facing part of the repository. It consists of the actual files and directories checked out on the local filesystem that a developer can see, edit, and manipulate with standard tools and editors.3 This is the only state that is not in Git's compressed, object-database format.  
2. **Index (or Staging Area):** This is a crucial intermediate layer that acts as a buffer between the Working Directory and the Repository. The index is a single, binary file (typically located at .git/index) that contains a manifest of all files that will be included in the *next* commit.1 It essentially holds a proposed snapshot of the project.  
3. **Repository (Object Database):** This is the permanent, immutable record of the project's history. It is the collection of commit, tree, and blob objects stored within the .git/objects directory.3 Data in the repository is considered safely saved and part of the project's historical timeline.

The fundamental workflow involves modifying files in the working directory, selectively adding those changes to the index using git add, and then permanently recording the state of the index as a new commit in the repository using git commit.

### **2.2 The Index: A Technical Deep-Dive into.git/index**

The index is far more than a simple list of files; it is a highly optimized data structure designed to enable both Git's flexible workflow and its high performance. Its primary function is to decouple the working directory from the commit history, allowing a developer to carefully construct a commit by staging changes incrementally, rather than being forced to commit all current modifications at once.1

The .git/index file is a binary file with a specific, well-defined format.19 Understanding its structure reveals why Git can perform operations like

git status so quickly. The format consists of several key parts:

* **Header**: A 12-byte header that begins with the 4-byte signature DIRC (short for "directory cache"), followed by a 4-byte version number, and a 4-byte integer indicating the number of entries in the index.  
* **Entries**: A list of index entries, sorted alphabetically by path name. Each entry contains a wealth of metadata about a single file:  
  * Filesystem Timestamps (ctime and mtime): The last modification times of the file's metadata and content.  
  * Device and Inode Numbers: Identifiers from the filesystem that describe the file's location on disk.  
  * File Mode: The file's permissions (e.g., regular file, executable).  
  * User and Group IDs (UID and GID).  
  * File Size: The size of the file in bytes.  
  * Blob SHA-1: The 20-byte binary SHA-1 hash of the blob object representing the file's staged content.  
  * Flags: A set of flags that include information about the entry, such as the stage during a merge conflict.  
  * Path Name: The file's path, relative to the root of the working directory.  
* **Extensions and Checksum**: The index format can be extended with additional data for features like untracked file caches or merge conflict resolution. The entire file is concluded with a 20-byte SHA-1 checksum of all preceding content, ensuring the index file's integrity.

The presence of detailed filesystem metadata within the index is a critical performance optimization. When a command like git status is run, Git does not need to read and hash the content of every single file in a large project to check for modifications. Instead, it can first perform a much faster check by comparing the current mtime, file size, and other metadata of the file on disk with the values stored for that file in the index.19 Only if this metadata differs does Git proceed with the more computationally expensive task of reading the file's content and computing its SHA-1 hash to see if it has truly changed. This allows

git status to execute almost instantaneously, even in very large repositories.

### **2.3 Pointers to History: References and HEAD**

Remembering 40-character SHA-1 hashes to identify commits is impractical for human users.6 Git solves this problem by using human-readable names called "references" (or "refs") to point to specific commit objects. These references are the foundation of concepts like branches and tags.

A **branch** in Git is a remarkably simple construct. It is a plain text file located in the .git/refs/heads/ directory. The name of the file corresponds to the name of the branch (e.g., main), and the sole content of this file is the 40-character SHA-1 hash of the commit that the branch currently points to.1 When a new commit is made on a branch, Git's final action is to update this single file with the hash of the new commit. This implementation is the reason why creating, deleting, and updating branches in Git is an extremely lightweight and instantaneous operation, a stark contrast to older version control systems where branching often involved creating a full copy of the project's source code. This design choice is fundamental to modern, branch-heavy development workflows, as it encourages frequent branching and experimentation without performance penalties.

The **HEAD file** is a special pointer, located at .git/HEAD, that indicates the user's current position within the repository's history.1 It determines what commit is the parent of the next commit. The

HEAD file can be in one of two states:

* **Symbolic Reference**: In the most common state, HEAD acts as a symbolic reference, meaning it points to another reference rather than directly to a commit hash. Its content will be a single line of text, such as ref: refs/heads/main.31 This indicates that the repository is currently "on" the  
  main branch. When a new commit is created, Git sees that HEAD points to refs/heads/main and knows that it must update the main branch file with the new commit's hash.  
* **Detached HEAD**: It is also possible to check out a specific commit hash directly, rather than a branch. In this scenario, the .git/HEAD file will contain the 40-character SHA-1 hash of that commit. This is known as a "detached HEAD" state.31 Any new commits made while in this state will be parented to the checked-out commit, but they will not belong to any branch. If the user then switches to a different branch without first creating a new branch to point to these new commits, they may become "dangling" and eventually be garbage collected, as no reference points to them.

## **Section 3: A Step-by-Step Implementation Guide**

This section translates the architectural theory into a procedural guide for implementing the core Git commands: init, add, and commit. Each command will be broken down into the sequence of internal operations that must be performed on the filesystem and within the object database.

### **3.1 init: Constructing the Repository Skeleton**

The git init command is the first step in any new project. It transforms an ordinary directory into a fully functional Git repository by creating the necessary internal data structures.39

**Internal Process:**

1. **Create .git Directory**: The primary action is to create a new subdirectory named .git in the current working directory. This directory will house the entire repository database and metadata.39  
2. **Create Core Subdirectories**: Within the newly created .git directory, a specific folder structure must be established to organize the repository's data:  
   * .git/objects/: This directory is the object database. It should be created to store all blob, tree, and commit objects.9 For a basic implementation, it is also conventional to create empty subdirectories  
     info/ and pack/ inside objects/, although they will not be used in this simplified model.6  
   * .git/refs/: This directory will contain all references. Within refs/, two more subdirectories, heads/ and tags/, should be created. heads/ will store the branch pointers, and tags/ will store tag pointers.9  
3. **Create the HEAD File**: A file named HEAD must be created directly inside the .git directory. Its initial content should be a single line of text defining the default branch: ref: refs/heads/main.31 It is important to note that at this stage, the file  
   .git/refs/heads/main does not yet exist. It will only be created when the first commit is made.  
4. **Create Ancillary Files (Optional)**: A standard git init also creates several other files for configuration and description, such as .git/config, .git/description, and .git/info/exclude. While not strictly necessary for the core functionality of adding and committing, creating these empty files can make the repository structure more closely resemble a true Git repository.9

Upon completion of these steps, the directory is a valid, albeit empty, Git repository, ready to track files.

### **3.2 add: From Working File to Staged Object**

The git add command serves as the bridge between the working directory and the staging area. It takes the current content of a file, creates a blob object from it, and updates the index to reference this new blob, thereby marking the file as staged for the next commit.24

**Internal Process:** For each file path provided to the add command:

1. **Read File Content**: The first step is to read the entire content of the specified file from the working directory. This should be read as a raw byte stream to handle both text and binary files correctly.  
2. Create Blob Object: A new blob object must be created and stored in the object database. This involves several sub-steps:  
   a. Construct the blob's header. This is done by formatting the string blob {content\_length}\\0, where {content\_length} is the size of the file's content in bytes, and then encoding it into a byte string.6

   b. Concatenate this header byte string with the file's content byte stream.  
   c. Compute the SHA-1 hash of this combined byte stream. The result is the 40-character hexadecimal string that will serve as the blob's unique identifier.6

   d. Compress the combined data (header \+ content) using a zlib compression library.6

   e. Write the compressed data to the object database. The path is determined by the blob's hash: .git/objects/\<first\_2\_chars\>/\<last\_38\_chars\>. The subdirectory (\<first\_2\_chars\>) may need to be created if it does not already exist.2  
3. Update the Index: The final step is to record this change in the .git/index file.  
   a. The .git/index file must be read from disk and parsed into an in-memory data structure that represents the list of staged files. If the file does not exist, an empty structure should be initialized.  
   b. Search the in-memory list for an entry corresponding to the file path being added. If an entry exists, it should be updated with the new blob's SHA-1 hash and fresh filesystem metadata (mode, timestamps, etc.). If no entry exists, a new one should be created.27

   c. The list of index entries must be kept sorted alphabetically by path name.  
   d. The updated in-memory index structure must be serialized back into its binary format and written back to the .git/index file. This includes writing the 12-byte header, the sorted entries, and a final SHA-1 checksum of the preceding content.26

After these steps, the file's changes are officially staged, and git status would show the file as ready to be committed.

### **3.3 commit: Solidifying History**

The git commit command performs the final act of creating a permanent snapshot. It takes the state of the project as defined by the index, creates the necessary tree and commit objects, and updates the current branch to point to the new commit.43 A critical aspect of this process is that the

commit command does not interact with the working directory at all; its sole source of truth for the project's state is the .git/index file.1 This deliberate separation is what makes the staging area such a powerful tool for crafting precise, logical commits.

**Internal Process:**

1. Create Tree Objects from Index: The flat list of file paths and blob hashes in the index must be converted into a hierarchical structure of tree objects. This is the most algorithmically complex part of the commit process.  
   a. The process typically starts by parsing the sorted index entries and building an in-memory representation of the directory structure.  
   b. A recursive function then traverses this structure from the bottom up. For each directory at the deepest levels of the hierarchy, a tree object is constructed. Its content is formatted with the mode, name, and binary hash of each blob (file) and tree (subdirectory) it contains. This content is then hashed, compressed, and written to the object database.45

   c. The function then moves up to the parent directories. New tree objects are created for these directories, containing entries that point to the hashes of the blobs and sub-trees (the ones just created) within them. This process repeats until a single root tree object, representing the entire state of the project, has been created and written to the database. The SHA-1 hash of this root tree is saved for the next step. This entire operation is what the low-level git write-tree command accomplishes.46  
2. Identify Parent Commit: To link the new commit to the project's history, the parent commit must be identified.  
   a. Read the .git/HEAD file to determine the current branch (e.g., ref: refs/heads/main).31

   b. Read the content of the file at that reference path (e.g., .git/refs/heads/main). This file contains the 40-character SHA-1 hash of the current tip of the branch, which will be the parent of the new commit. If this file does not exist, it signifies that this is the initial commit, and it will have no parent.20  
3. Create Commit Object: With the root tree and parent commit identified, the new commit object can be created.  
   a. Gather the necessary metadata: the author and committer information (typically from Git configuration or environment variables 43), the current timestamp, and the commit message provided by the user.

   b. Construct the commit object's content as a formatted string, including the tree line, the parent line(s), the author and committer lines, and the commit message, separated by a blank line.6

   c. As with other objects, prepend the appropriate header (e.g., commit {size}\\0), hash the result to get the new commit's SHA-1, compress the data, and write the final commit object to the object database.  
4. Update Branch Reference: This is the final and most critical step. The current branch must be updated to point to the newly created commit.  
   a. The file corresponding to the current branch (e.g., .git/refs/heads/main) must be updated to contain the 40-character SHA-1 hash of the new commit object.31 This operation must be atomic to ensure repository integrity. If the system were to fail after the commit object is written but before this reference is updated, the new commit would become "dangling" and unreachable, but the repository would remain in a consistent state, with the branch still pointing to the previous valid commit. Low-level commands like  
   git update-ref are designed to handle this safely.49

Once the branch reference is updated, the commit is officially part of the project's history, and the process is complete.

## **Section 4: Navigating History: The Commit DAG**

Git does not store history as a simple linear list of changes. Instead, it uses a more powerful and flexible data structure: a Directed Acyclic Graph (DAG). Understanding this structure is key to comprehending how Git handles branching, merging, and history traversal.

### **4.1 The History as a Graph**

The commit history in Git is a graph where each commit is a node. The relationships between these nodes define the project's evolution.

* **Directed Edges**: The graph is "directed" because the connections (edges) between commits have a specific direction. Critically, each commit object contains pointers to its parent(s). This means the edges in the graph point backward in time, from a child commit to its parent(s).38 This child-to-parent linking is a non-negotiable design principle. It is fundamental to the cryptographic integrity of the repository. A commit's identity (its SHA-1 hash) is derived from its content, which includes the hashes of its parents. This creates an immutable, append-only ledger. If pointers went from parent to child, one could alter a commit's content without invalidating the hash of its parent, thereby breaking the chain of trust. Any operation that appears to "edit" history, such as a rebase, is in fact creating new commit objects with new parents and new hashes, effectively rewriting a new line of history rather than modifying the old one.  
* **Acyclic Nature**: The graph is "acyclic" because it is impossible to follow the chain of parent pointers from a commit and eventually arrive back at the same commit. A commit's hash depends on its parents' hashes, so a commit cannot exist before its parent, preventing the formation of cycles.51 This ensures that the history always moves backward in time in a well-defined manner.  
* **DAG vs. Tree**: The commit history is a DAG and not a strict tree because a node (commit) can have more than one parent. While most commits have a single parent, creating a linear chain, a merge commit is specifically defined as a commit with multiple parents. This allows the DAG to model the convergence of two or more independent lines of development (branches), a capability that a simple tree structure cannot support.51

### **4.2 A Traversal Algorithm**

All queries about a repository's history, from a simple log to complex blame or bisect operations, are fundamentally graph traversal problems on the commit DAG.50 To implement a basic

log command that displays the history of the current branch, a graph traversal algorithm can be employed.

**Starting Point**: The traversal must begin from a known commit. This is typically the commit pointed to by a reference, such as a branch name or the special HEAD pointer. For a log command, the first step is to resolve HEAD to find the starting commit's SHA-1 hash.

**The Walk (A Traversal Algorithm)**: A straightforward algorithm, such as a depth-first or breadth-first search, can be used to walk the history backward from the starting commit.

1. Initialize a data structure to act as a queue or stack for commits to visit (e.g., a list or deque) and add the starting commit's SHA-1 hash to it.  
2. Initialize a set to keep track of commit hashes that have already been visited. This is crucial to prevent processing the same commit multiple times and to handle the graph structure efficiently, especially in histories with complex merges.  
3. Begin a loop that continues as long as the queue is not empty.  
4. In each iteration, remove a commit hash from the queue.  
5. Check if this hash is already in the visited set. If it is, skip to the next iteration. If not, add it to the visited set.  
6. Read the corresponding commit object from the object database (at .git/objects/\<first\_2\>/\<last\_38\>). Decompress its content.  
7. Process the commit object. For a log command, this would involve parsing and printing its metadata (hash, author, date) and the commit message.  
8. Parse the parent lines from the commit object's content. For each parent SHA-1 hash found, add it to the end of the queue of commits to visit.  
9. Repeat the loop until the queue is empty, at which point all reachable ancestor commits will have been processed.

This algorithm effectively mimics the core logic of Git's low-level git rev-list command, which is the workhorse behind git log and other history-aware commands.54 By implementing this traversal, one can reconstruct and display the historical lineage of any branch or commit in the repository.

## **Conclusion**

This report has systematically deconstructed the internal architecture of Git, revealing that its sophisticated version control capabilities emerge from a small set of powerful, interlocking computer science concepts. At its foundation lies a content-addressable object store, which uses SHA-1 hashing and zlib compression to ensure data integrity and storage efficiency. This database is populated by three distinct object types—blobs, trees, and commits—which cleanly separate the concerns of file content, directory structure, and historical metadata.

The transition of changes from a developer's working directory to this permanent repository is managed by the crucial intermediate layer of the index, or staging area. This binary file not only enables the flexible workflow of crafting commits piece-by-piece but also serves as a critical performance optimization. The entire historical record is woven together into a Directed Acyclic Graph, where commits are linked cryptographically from child to parent, creating an immutable and verifiable ledger of the project's evolution. By understanding these first principles and the precise mechanics of the init, add, and commit commands—from creating the initial repository skeleton to the final, atomic update of a branch reference—one is equipped with the architectural blueprint necessary to implement a functional version of Git from the ground up.

#### **Works cited**

1. Understanding Git Internals: How Git Works Under the Hood | Cursa: Free Online Courses \+ Free Certificate, accessed on August 20, 2025, [https://cursa.app/en/article/understanding-git-internals-how-git-works-under-the-hood](https://cursa.app/en/article/understanding-git-internals-how-git-works-under-the-hood)  
2. A Deep Dive into Git Internals: Blobs, Trees, and Commits \- DEV ..., accessed on August 20, 2025, [https://dev.to/\_\_whyd\_rf/a-deep-dive-into-git-internals-blobs-trees-and-commits-1doc](https://dev.to/__whyd_rf/a-deep-dive-into-git-internals-blobs-trees-and-commits-1doc)  
3. 1.3 Getting Started \- What is Git?, accessed on August 20, 2025, [https://git-scm.com/book/en/v2/Getting-Started-What-is-Git%3F](https://git-scm.com/book/en/v2/Getting-Started-What-is-Git%3F)  
4. Branches in a Nutshell \- Git, accessed on August 20, 2025, [https://git-scm.com/book/en/v2/Git-Branching-Branches-in-a-Nutshell](https://git-scm.com/book/en/v2/Git-Branching-Branches-in-a-Nutshell)  
5. Packfiles \- Git, accessed on August 20, 2025, [https://git-scm.com/book/be/v2/Git-Internals-Packfiles](https://git-scm.com/book/be/v2/Git-Internals-Packfiles)  
6. Git Objects \- Git, accessed on August 20, 2025, [https://git-scm.com/book/en/v2/Git-Internals-Git-Objects](https://git-scm.com/book/en/v2/Git-Internals-Git-Objects)  
7. Git Guts: git as a content-addressable store \- Awasu, accessed on August 20, 2025, [https://awasu.com/weblog/git-guts/store/](https://awasu.com/weblog/git-guts/store/)  
8. 7.Git Internals. we explore the inner workings of Git… | by Praneeth Bilakanti | Medium, accessed on August 20, 2025, [https://praneethreddybilakanti.medium.com/7-git-internals-548f8707436a](https://praneethreddybilakanti.medium.com/7-git-internals-548f8707436a)  
9. How Git structures the repository content? \- SiteGround KB, accessed on August 20, 2025, [https://www.siteground.com/kb/git-structures-repository-content/](https://www.siteground.com/kb/git-structures-repository-content/)  
10. SHA-1: Definition, Examples, and Applications | Graph AI, accessed on August 20, 2025, [https://www.graphapp.ai/engineering-glossary/git/sha-1](https://www.graphapp.ai/engineering-glossary/git/sha-1)  
11. Hash Values (SHA-1) in Git: What You Need To Know \- Designveloper, accessed on August 20, 2025, [https://www.designveloper.com/blog/hash-values-sha-1-in-git/](https://www.designveloper.com/blog/hash-values-sha-1-in-git/)  
12. How Git Uses SHA-1 for Commit History \- DEV Community, accessed on August 20, 2025, [https://dev.to/cristiansifuentes/how-git-uses-sha-1-for-commit-history-3hc4](https://dev.to/cristiansifuentes/how-git-uses-sha-1-for-commit-history-3hc4)  
13. Git object types (blob, tree, commit, tag): Definition, Examples, and Applications | Graph AI, accessed on August 20, 2025, [https://www.graphapp.ai/engineering-glossary/git/git-object-types-blob-tree-commit-tag](https://www.graphapp.ai/engineering-glossary/git/git-object-types-blob-tree-commit-tag)  
14. Explain BLOB object and tree object in Git. \- Tutorialspoint, accessed on August 20, 2025, [https://www.tutorialspoint.com/explain-blob-object-and-tree-object-in-git](https://www.tutorialspoint.com/explain-blob-object-and-tree-object-in-git)  
15. Git Internals \- The BLOB \- YouTube, accessed on August 20, 2025, [https://www.youtube.com/watch?v=\_wj4MGuvcjc](https://www.youtube.com/watch?v=_wj4MGuvcjc)  
16. Understanding Git commit SHAs \- Graphite, accessed on August 20, 2025, [https://graphite.dev/guides/git-hash](https://graphite.dev/guides/git-hash)  
17. A Look Inside the .git Folder \- Humble Toolsmith, accessed on August 20, 2025, [https://humbletoolsmith.com/2022/01/30/a-look-inside-the-\_git-folder/](https://humbletoolsmith.com/2022/01/30/a-look-inside-the-_git-folder/)  
18. Git Book \- The Git Object Model, accessed on August 20, 2025, [https://shafiul.github.io/gitbook/1\_the\_git\_object\_model.html](https://shafiul.github.io/gitbook/1_the_git_object_model.html)  
19. DevOps \- Git Internals: Architecture and Index Files | Microsoft Learn, accessed on August 20, 2025, [https://learn.microsoft.com/en-us/archive/msdn-magazine/2017/august/devops-git-internals-architecture-and-index-files](https://learn.microsoft.com/en-us/archive/msdn-magazine/2017/august/devops-git-internals-architecture-and-index-files)  
20. Git Under the Hood, Part 1: Object Storage in Git | by Amir Ebrahimi ..., accessed on August 20, 2025, [https://medium.com/data-management-for-researchers/git-under-the-hood-part-1-object-storage-in-git-57c9adfb5e5f](https://medium.com/data-management-for-researchers/git-under-the-hood-part-1-object-storage-in-git-57c9adfb5e5f)  
21. The anatomy of a Git commit \- thoughtram Blog, accessed on August 20, 2025, [https://blog.thoughtram.io/git/2014/11/18/the-anatomy-of-a-git-commit.html](https://blog.thoughtram.io/git/2014/11/18/the-anatomy-of-a-git-commit.html)  
22. Git Gud: The Working Tree, Staging Area, and Local Repo | by Lucas Maurer | Medium, accessed on August 20, 2025, [https://medium.com/@lucasmaurer/git-gud-the-working-tree-staging-area-and-local-repo-a1f0f4822018](https://medium.com/@lucasmaurer/git-gud-the-working-tree-staging-area-and-local-repo-a1f0f4822018)  
23. About \- Staging Area \- Git, accessed on August 20, 2025, [https://git-scm.com/about/staging-area](https://git-scm.com/about/staging-area)  
24. Git Add | Atlassian Git Tutorial, accessed on August 20, 2025, [https://www.atlassian.com/git/tutorials/saving-changes](https://www.atlassian.com/git/tutorials/saving-changes)  
25. Using the Git staging area, accessed on August 20, 2025, [https://coderefinery.github.io/git-intro/branch/sphinx-book-theme/staging-area/](https://coderefinery.github.io/git-intro/branch/sphinx-book-theme/staging-area/)  
26. Git: Understanding the Index File \- Mincong Huang, accessed on August 20, 2025, [https://mincong.io/2018/04/28/git-index/](https://mincong.io/2018/04/28/git-index/)  
27. What does the git index contain EXACTLY? \- Stack Overflow, accessed on August 20, 2025, [https://stackoverflow.com/questions/4084921/what-does-the-git-index-contain-exactly](https://stackoverflow.com/questions/4084921/what-does-the-git-index-contain-exactly)  
28. Git Index Format: Definition, Examples, and Applications | Graph AI, accessed on August 20, 2025, [https://www.graphapp.ai/engineering-glossary/git/git-index-format](https://www.graphapp.ai/engineering-glossary/git/git-index-format)  
29. index-format Documentation \- Git, accessed on August 20, 2025, [https://git-scm.com/docs/index-format](https://git-scm.com/docs/index-format)  
30. gitformat-index \- Git index format \- Ubuntu Manpage, accessed on August 20, 2025, [https://manpages.ubuntu.com/manpages/oracular/man5/gitformat-index.5.html](https://manpages.ubuntu.com/manpages/oracular/man5/gitformat-index.5.html)  
31. Git References \- Git, accessed on August 20, 2025, [https://git-scm.com/book/ms/v2/Git-Internals-Git-References](https://git-scm.com/book/ms/v2/Git-Internals-Git-References)  
32. What are Git Refs: The Invisible Threads of Version Control | by Jahangir | Medium, accessed on August 20, 2025, [https://medium.com/@jahangir80842/what-are-git-refs-the-invisible-threads-of-version-control-3200d8f594c8](https://medium.com/@jahangir80842/what-are-git-refs-the-invisible-threads-of-version-control-3200d8f594c8)  
33. Git References \- Git, accessed on August 20, 2025, [https://git-scm.com/book/it/v2/Git-Internals-Git-References](https://git-scm.com/book/it/v2/Git-Internals-Git-References)  
34. Git branches are just references to commits | by Sergeon \- Medium, accessed on August 20, 2025, [https://medium.com/@Sergeon/git-branches-are-just-references-to-commits-b66923026df9](https://medium.com/@Sergeon/git-branches-are-just-references-to-commits-b66923026df9)  
35. What is "HEAD" in Git? | Learn Version Control with Git \- Git Tower, accessed on August 20, 2025, [https://www.git-tower.com/learn/git/glossary/head](https://www.git-tower.com/learn/git/glossary/head)  
36. Git \- Head \- GeeksforGeeks, accessed on August 20, 2025, [https://www.geeksforgeeks.org/git/git-head/](https://www.geeksforgeeks.org/git/git-head/)  
37. Git Internals Part 1- List of basic Concepts That Power your .git Directory \- Developer Nation, accessed on August 20, 2025, [https://www.developernation.net/blog/git-internals-list-of-basic-concepts-that-power-your-git-directory/](https://www.developernation.net/blog/git-internals-list-of-basic-concepts-that-power-your-git-directory/)  
38. Git is a Directed Acyclic Graph and What the Heck Does That Mean? | by Sharon Cichelli | Girl Writes Code | Medium, accessed on August 20, 2025, [https://medium.com/girl-writes-code/git-is-a-directed-acyclic-graph-and-what-the-heck-does-that-mean-b6c8dec65059](https://medium.com/girl-writes-code/git-is-a-directed-acyclic-graph-and-what-the-heck-does-that-mean-b6c8dec65059)  
39. git init | Atlassian Git Tutorial, accessed on August 20, 2025, [https://www.atlassian.com/git/tutorials/setting-up-a-repository/git-init](https://www.atlassian.com/git/tutorials/setting-up-a-repository/git-init)  
40. Git Init: A Walk Through How to Create a New Repo \- CloudBees, accessed on August 20, 2025, [https://www.cloudbees.com/blog/git-init-a-walk-through-how-to-create-a-new-repo](https://www.cloudbees.com/blog/git-init-a-walk-through-how-to-create-a-new-repo)  
41. How to initialize a new Git repository with the Git init command, accessed on August 20, 2025, [https://graphite.dev/guides/git-init](https://graphite.dev/guides/git-init)  
42. A hands-on intro to Git internals: creating a repo from scratch \- Swimm, accessed on August 20, 2025, [https://swimm.io/blog/a-hands-on-intro-to-git-internals-creating-a-repo-from-scratch](https://swimm.io/blog/a-hands-on-intro-to-git-internals-creating-a-repo-from-scratch)  
43. git-commit Documentation \- Git, accessed on August 20, 2025, [https://git-scm.com/docs/git-commit](https://git-scm.com/docs/git-commit)  
44. basic question about working/staging areas; blobs, trees, and commtis : r/git \- Reddit, accessed on August 20, 2025, [https://www.reddit.com/r/git/comments/1eh97fa/basic\_question\_about\_workingstaging\_areas\_blobs/](https://www.reddit.com/r/git/comments/1eh97fa/basic_question_about_workingstaging_areas_blobs/)  
45. Git Internal \- The Tree Explained \- YouTube, accessed on August 20, 2025, [https://www.youtube.com/watch?v=bMKW-VVWEZQ](https://www.youtube.com/watch?v=bMKW-VVWEZQ)  
46. Git Internals \- Tree Objects · Decentralized Data Workshops \- GitHub Pages, accessed on August 20, 2025, [https://codeforphilly.github.io/decentralized-data/tutorials/git-data-model/lessons/tree-objects/](https://codeforphilly.github.io/decentralized-data/tutorials/git-data-model/lessons/tree-objects/)  
47. git-commit-tree Documentation \- Git, accessed on August 20, 2025, [https://git-scm.com/docs/git-commit-tree](https://git-scm.com/docs/git-commit-tree)  
48. Git Object Model | Online Video Tutorial by thoughtbot, accessed on August 20, 2025, [https://thoughtbot.com/upcase/videos/git-object-model](https://thoughtbot.com/upcase/videos/git-object-model)  
49. git-update-ref Documentation \- Git, accessed on August 20, 2025, [https://git-scm.com/docs/git-update-ref](https://git-scm.com/docs/git-update-ref)  
50. DAG (Directed Acyclic Graph): Definition, Examples, and Applications, accessed on August 20, 2025, [https://www.graphapp.ai/engineering-glossary/git/dag-directed-acyclic-graph](https://www.graphapp.ai/engineering-glossary/git/dag-directed-acyclic-graph)  
51. Why the Git Graph is a Directed Acyclic Graph (DAG) | by Andreas Kagoshima \- Medium, accessed on August 20, 2025, [https://medium.com/@a.kago1988/why-the-git-graph-is-a-directed-acyclic-graph-dag-f9052b95f97f](https://medium.com/@a.kago1988/why-the-git-graph-is-a-directed-acyclic-graph-dag-f9052b95f97f)  
52. DAG vs. tree using Git? \- Stack Overflow, accessed on August 20, 2025, [https://stackoverflow.com/questions/26395521/dag-vs-tree-using-git](https://stackoverflow.com/questions/26395521/dag-vs-tree-using-git)  
53. Git's database internals II: commit history queries \- The GitHub Blog, accessed on August 20, 2025, [https://github.blog/open-source/git/gits-database-internals-ii-commit-history-queries/](https://github.blog/open-source/git/gits-database-internals-ii-commit-history-queries/)  
54. git-rev-parse Documentation \- Git, accessed on August 20, 2025, [https://git-scm.com/docs/git-rev-parse](https://git-scm.com/docs/git-rev-parse)  
55. git-log Documentation \- Git, accessed on August 20, 2025, [https://git-scm.com/docs/git-log](https://git-scm.com/docs/git-log)  
56. Traverse through HEAD to access all git commits \- Stack Overflow, accessed on August 20, 2025, [https://stackoverflow.com/questions/54929155/traverse-through-head-to-access-all-git-commits](https://stackoverflow.com/questions/54929155/traverse-through-head-to-access-all-git-commits)