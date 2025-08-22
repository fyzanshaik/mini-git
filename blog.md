# Mini Git

A git implemention in python3 with OOPS in mind. 

Git under the hood is a key-value store at its lowest level, where key is obtained from the hash value of a files content. 

## Objects in git
.git/objects acts as objects database where it stores for any specific file 

- every version of its content
- structure of every directory
- metadata associated with every commit


Fundamental principle governing this database is **content addressing**



Any file -> SHA1 ALGORITHM -> 40 character hexadecimal key it's a **checksum** generated from the content itself. 

checksum + prepended header (type of content being stored)

**A FILE IS ALWAYS STORED ONCE**

example hash of one file 

d670460b4b4aece5915caf5c68d12f560a9fe3e4

first two characters are stored as name of sub dir and the remaining as file name

.git/objects/d6/70460b4b4aece5915caf5c68d12f560a9fe3e4

All objects are compressed using zlib library before being written to the file system. 

When reading: 

decompressing the object and reading it then

### Lifecycle of any object: 
prepending header -> hashing -> compression -> shared storage

## Objects
3 types:

- blob -> files
- trees -> Directory structure
- Commit -> Historical snapshot
At every staging, all files are created into their blob objects, if an existing hash exist then it's not changed rather kept, but if there are any changes the sha1 algorithm produces a completely different hash and hence we store it as an object. 

Going through an example: 

#### Initialization of git repository
```
git init
```
![image.png](https://eraser.imgix.net/workspaces/S92vk2HtOE9aDYPBrJaU/qhwxEkPbxjZQcHM2usqDwaYSpsB2/TrSIMyfJH6lk7i_eoi8vw.png?ixlib=js-3.7.0 "image.png")

Creates the initial git structure which stores our required information.

Imp folders -> objects,refs , HEAD file for storing reference of the branch

#### Adding to staging area
```
echo  "Hello" > file1.txt && git add file1.txt
```
Create a new file and push to staging area, now this will create an object of the file : 



![image.png](https://eraser.imgix.net/workspaces/S92vk2HtOE9aDYPBrJaU/qhwxEkPbxjZQcHM2usqDwaYSpsB2/YGGVKRZukUw8QQPIIPBct.png?ixlib=js-3.7.0 "image.png")

This is produced by:

- Appending header which is of the format "blob <sizeInChar>\0<contentofFile> "
```
content = b"Hello"
header = f"blob {len(content)}\0".encode()
full_data = header + content  # "blob 5\0Hello"
sha = hashlib.sha1(full_data).hexdigest()  # Assume "a1b2..."
```
The files content is compressed using **zlib** and stored with filename as [2:] characters of **hash value **



With this we have one file in staging area we can store this information in an **index** file to reference/check later.

#### Committing
This has 2 stages where first it creates a **tree** commit which stores information regarding the files of all staged blobs. 

```
git commit -m "<message>"
```
Tree commit:

```
100644 blob e965047ad7c57865823c7d992b1d046ea66edf78 file1.txt
```
<file permission> <object type> <sha1 hash value> <actual filename>

It does this with all files that are available in the index.

This stores the structure of the entire commit we have **staged**

Now second part:

Creating commit object, which stores the tree structure with metadata information

```
tree 3ec21ace7721180c1ac1afe4d536f44023befa4c
author fyzanshaik <fyzan.shaik@gmail.com> 1755848074 +0530
committer fyzanshaik <fyzan.shaik@gmail.com> 1755848074 +0530

first commit
```
 The tree commit reference

author 

committer 

message



This entire process encapsulates the git working. 

Upon reading we decompress the content and over write where its needed. 


