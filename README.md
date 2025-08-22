# mini-git
A simplistic git implementation in Python3!

why?
Git is most widely used version control system and this is my shot at implementing at least the basic functionality. 

Built this with python3 with OOPS in mind, and simplistic git principles

## Installation
```bash
./install.sh
source ~/.bashrc  # or restart terminal
```

Branching - merge,checkout and plenty of stuff isn't done and needs more time and work!Will do it in future implementations

Commands implemented: 
- [x] init - initialize repository
- [x] add - stage files  
- [x] commit - create commits
- [x] status - show working directory status
- [x] log - show commit history
- [x] cat-file -p - inspect objects
- [x] move u/d - traverse commits up/down
- [x] checkout - jump to specific commit

Usage: `minigit <command>`. Run `./install.sh` to use globally.

## Documentation
- `blog.md` - code implementation details
- `git-research.md` - full understanding of git internals (researched with Gemini 2.5 Pro)


