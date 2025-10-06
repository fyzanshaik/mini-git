# mini-git
A simplistic git implementation in Python3!

## Motivation

Git is the most widely used version control system, and this is my shot at implementing at least the basic functionality. I built this with Python3 with OOP principles in mind, following simplistic git internals. 

Credit goes to [Boot Dev](https://www.boot.dev/) for their courses on **Python**, **OOP**, and **functional programming**.

## Quick Start

### Installation
```bash
./install.sh
source ~/.bashrc  # or restart terminal
```

### Quick Demo
```bash
# Run the comprehensive Python demo with colorful output
python3 demo.py

# Or try the quick bash demo
./quick-demo.sh
```

**NOTE**: Add this to your IDE's workspace settings to visualize the git folders:
```json
{
  "files.exclude": {
    "**/.git": false,
    "**/.minigit": false
  }
}
```

## Usage

### Available Commands

- `minigit init` - Initialize a new repository
- `minigit add <file>` - Stage files for commit
- `minigit commit -m "message"` - Create a commit with staged changes
- `minigit status` - Show working directory status and staged files
- `minigit log` - Display commit history
- `minigit cat-file -p <hash>` - Inspect git objects by hash
- `minigit move u` - Traverse up to parent commit
- `minigit move d` - Traverse down to child commit
- `minigit checkout <commit-hash>` - Jump to a specific commit

### Advanced Features

**Object Inspection**: Use `cat-file -p` to examine the internal structure of commits, trees, and blobs.

**Commit Navigation**: The `move u/d` commands let you traverse the commit history interactively without checking out each commit.

### Current Limitations

Branching, merging, and checkout to branches are not yet implemented and will be added in future versions.

## Documentation

- `blog.md` - Detailed code implementation walkthrough
- `git-research.md` - Deep dive into git internals (researched with Gemini 2.5 Pro)

## Contributing

Contributions are welcome! Feel free to open issues or submit pull requests.

