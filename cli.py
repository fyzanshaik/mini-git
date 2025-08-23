import sys
import os
import argparse
import importlib.util
#TODO: this is a bit of a hack, I should find a better way to do this but chalega
#Logs are very verbose and probably one log class would be better for all objects.

#this function is used to load the module from the file path, MODULE IS basically where the import command is
def load_module(module_name, file_path):
    spec = importlib.util.spec_from_file_location(module_name, file_path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module

#this is the directory of the script, so that the import command can be used here.
#basically an attempt to create some saner code, it would not be needed if it was a part of the repository.py file, but is needed here because of the import command.
script_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, script_dir)
repo_module = load_module("repository", os.path.join(script_dir, "repository.py"))
Repository = repo_module.Repository

#this is the command to initialize the repository, so the python code is a bit convoluted but it is needed to create the repository object.
def cmd_init(args):
    print("[CLI] Initializing minigit repository...")
    
    if args.directory:
        repo_path = args.directory
    else:
        repo_path = os.getcwd()
    
    repo = Repository(repo_path)
    #if exists we do not recreate the .minigit dir 
    if repo.exists():
        print(f"[CLI] ERROR: Repository already exists in {repo_path}")
        print(f"[CLI] Found existing .minigit directory")
        return 1
    
    success = repo.create()
    
    if success:
        print(f"[CLI] ✅ Initialized empty minigit repository in {repo.get_minigit_path()}")
        print(f"[CLI] Created directory structure:")
        print(f"[CLI]   .minigit/")
        print(f"[CLI]   .minigit/objects/")
        print(f"[CLI]   .minigit/refs/")
        print(f"[CLI]   .minigit/refs/heads/")
        print(f"[CLI]   .minigit/refs/tags/")
        print(f"[CLI]   .minigit/HEAD -> ref: refs/heads/main")
        return 0
    else:
        print(f"[CLI] ERROR: Failed to create repository")
        return 1


def cmd_cat_file(args):
    print(f"[CLI] Reading object: {args.object}")
    
    repo = Repository.find_repository()
    if repo is None:
        print("[CLI] ERROR: Not a minigit repository")
        print("[CLI] Run 'minigit init' to initialize a repository")
        return 1
    
    full_hash = repo.resolve_hash(args.object)
    if full_hash is None:
        return 1
    
    try:
        obj = repo.load_object(full_hash)
        
        print(f"[CLI] Object type: {obj.get_type()}")
        print(f"[CLI] Object hash: {full_hash}")
        print(f"[CLI] Object size: {len(obj.data)} bytes")
        print()
        
        if obj.get_type() == "blob":
            try:
                content = obj.data.decode('utf-8')
                print(content, end='')
            except UnicodeDecodeError:
                print(f"[CLI] Binary content ({len(obj.data)} bytes)")
                print(f"[CLI] First 100 bytes: {obj.data[:100]}")
        
        elif obj.get_type() == "tree":
            obj.display_tree()
        
        elif obj.get_type() == "commit":
            obj.display_commit()
        
        else:
            print(f"[CLI] Unknown object type: {obj.get_type()}")
            print(f"[CLI] Raw content: {obj.data}")
        
        return 0
        
    except FileNotFoundError:
        print(f"[CLI] ERROR: Object {args.object} not found")
        return 1
    except Exception as e:
        print(f"[CLI] ERROR: Failed to read object {args.object}: {e}")
        return 1


def cmd_status(args):
    print("[CLI] Checking repository status...")
    
    repo = Repository.find_repository()
    if repo is None:
        print("[CLI] ERROR: Not a minigit repository")
        print("[CLI] Run 'minigit init' to initialize a repository")
        return 1
    
    current_branch = repo.get_current_branch()
    head_commit = repo.get_head_commit()
    
    print(f"[CLI] On branch {current_branch if current_branch else 'unknown'}")
    
    if head_commit is None:
        print("[CLI] No commits yet")
        print()
    else:
        print(f"[CLI] HEAD points to: {head_commit.hash[:8]}")
        print(f"[CLI] Last commit: {head_commit.message}")
        print()
    
    working_files = repo.get_working_files()
    
    if not working_files:
        print("[CLI] No files in working directory")
        return 0
    
    staged_files = []
    modified_files = []
    untracked_files = []
    unmodified_files = []
    
    for file_path in working_files:
        status = repo.get_file_status_detailed(file_path)
        
        if status == "staged":
            staged_files.append(file_path)
        elif status == "modified":
            modified_files.append(file_path)
        elif status == "modified_after_staging":
            staged_files.append(file_path)
            modified_files.append(file_path)
        elif status == "untracked":
            untracked_files.append(file_path)
        elif status == "unmodified":
            unmodified_files.append(file_path)
    
    if staged_files:
        print("[CLI] Changes to be committed:")
        for file_path in staged_files:
            print(f"[CLI]   staged: {file_path}")
        print()
    
    if modified_files:
        print("[CLI] Changes not staged for commit:")
        for file_path in modified_files:
            print(f"[CLI]   modified: {file_path}")
        print()
    
    if untracked_files:
        print("[CLI] Untracked files:")
        for file_path in untracked_files:
            print(f"[CLI]   {file_path}")
        print()
        print("[CLI] (use 'minigit add <file>' to track files)")
    
    if not staged_files and not modified_files and not untracked_files:
        if head_commit is None:
            print("[CLI] Nothing to commit (create files and use 'minigit add' to track)")
        else:
            print("[CLI] Nothing to commit, working tree clean")
    
    print(f"[CLI] Total files: {len(working_files)} ({len(unmodified_files)} tracked, {len(staged_files)} staged, {len(untracked_files)} untracked, {len(modified_files)} modified)")
    
    return 0


def cmd_add(args):
    print(f"[CLI] Adding files to staging area...")
    
    repo = Repository.find_repository()
    if repo is None:
        print("[CLI] ERROR: Not a minigit repository")
        print("[CLI] Run 'minigit init' to initialize a repository")
        return 1
    
    if not args.files:
        print("[CLI] ERROR: No files specified")
        print("[CLI] Use 'minigit add <file>' to add files")
        return 1
    
    added_files = []
    failed_files = []
    
    for file_path in args.files:
        if os.path.isabs(file_path):
            try:
                rel_path = os.path.relpath(file_path, repo.repo_path)
                if rel_path.startswith('..'):
                    print(f"[CLI] ERROR: File {file_path} is outside repository")
                    failed_files.append(file_path)
                    continue
                file_path = rel_path
            except ValueError:
                print(f"[CLI] ERROR: Cannot resolve path {file_path}")
                failed_files.append(file_path)
                continue
        
        full_path = os.path.join(repo.repo_path, file_path)
        if not os.path.exists(full_path):
            print(f"[CLI] ERROR: File not found: {file_path}")
            failed_files.append(file_path)
            continue
        
        if os.path.isdir(full_path):
            print(f"[CLI] ERROR: Cannot add directory: {file_path}")
            print(f"[CLI] (Use 'minigit add' on individual files in the directory)")
            failed_files.append(file_path)
            continue
        
        hash_value = repo.add_to_index(file_path)
        if hash_value:
            added_files.append((file_path, hash_value))
            print(f"[CLI] ✅ Added: {file_path}")
        else:
            failed_files.append(file_path)
    
    if added_files:
        print(f"\n[CLI] Successfully added {len(added_files)} file(s):")
        for file_path, hash_value in added_files:
            print(f"[CLI]   {file_path} -> {hash_value[:8]}")
    
    if failed_files:
        print(f"\n[CLI] Failed to add {len(failed_files)} file(s):")
        for file_path in failed_files:
            print(f"[CLI]   {file_path}")
        
        if added_files:
            return 0
        else:
            return 1
    
    print(f"\n[CLI] Use 'minigit status' to see staged files")
    return 0


def cmd_commit(args):
    print(f"[CLI] Creating commit...")
    
    repo = Repository.find_repository()
    if repo is None:
        print("[CLI] ERROR: Not a minigit repository")
        print("[CLI] Run 'minigit init' to initialize a repository")
        return 1
    
    if not args.message:
        print("[CLI] ERROR: No commit message provided")
        print("[CLI] Use 'minigit commit -m \"<message>\"'")
        return 1
    
    staged_files = repo.get_staged_files()
    if not staged_files:
        print("[CLI] ERROR: No files staged for commit")
        print("[CLI] Use 'minigit add <file>' to stage files first")
        return 1
    
    print(f"[CLI] Committing {len(staged_files)} staged file(s):")
    for file_path, hash_value in staged_files.items():
        print(f"[CLI]   {file_path} ({hash_value[:8]})")
    
    author = f"{os.getenv('USER', 'Unknown')} <{os.getenv('USER', 'unknown')}@minigit.local>"
    commit_hash = repo.create_commit(args.message, author)
    
    if commit_hash:
        print(f"\n[CLI] ✅ Created commit {commit_hash[:8]}")
        print(f"[CLI] Message: {args.message}")
        print(f"[CLI] Author: {author}")
        return 0
    else:
        print("[CLI] ERROR: Failed to create commit")
        return 1


def cmd_log(args):
    print("[CLI] Showing commit history...")
    
    repo = Repository.find_repository()
    if repo is None:
        print("[CLI] ERROR: Not a minigit repository")
        print("[CLI] Run 'minigit init' to initialize a repository")
        return 1
    
    history = repo.get_commit_history(max_commits=args.max_count if hasattr(args, 'max_count') else None)
    
    if not history:
        print("[CLI] No commits found")
        return 0
    
    print(f"[CLI] Found {len(history)} commit(s)\n")
    
    for i, (commit_hash, commit) in enumerate(history):
        print(f"Commit: {commit_hash[:4]}")
        print(f"Tree:   {commit.tree_hash[:4]}")
        if commit.parent_hash:
            print(f"Parent: {commit.parent_hash[:4]}")
        print(f"Author: {commit.author}")
        print(f"Date:   {commit.timestamp}")
        print(f"Message: {commit.message}")
        
        try:
            tree = repo.load_object(commit.tree_hash)
            print(f"\nTree contents ({len(tree.entries)} files):")
            for entry in tree.entries:
                print(f"  {entry['mode']} {entry['hash'][:4]} {entry['name']}")
        except Exception as e:
            print(f"  Error loading tree: {e}")
        
        if i < len(history) - 1:
            print("\n" + "-" * 50 + "\n")
    
    return 0


def cmd_move(args):
    print(f"[CLI] Moving {args.direction}...")
    
    repo = Repository.find_repository()
    if repo is None:
        print("[CLI] ERROR: Not a minigit repository")
        print("[CLI] Run 'minigit init' to initialize a repository")
        return 1
    
    # Check for staged changes
    staged_files = repo.get_staged_files()
    if staged_files:
        print("[CLI] ERROR: You have staged changes")
        print("[CLI] Commit your changes before moving between commits")
        return 1
    
    current_hash, position = repo.get_current_commit_position()
    if current_hash is None:
        print("[CLI] ERROR: No commits found")
        return 1
    
    chain = repo.get_commit_chain()
    print(f"[CLI] Current position: {position + 1}/{len(chain)} (commit {current_hash[:8]})")
    
    if args.direction == 'u':
        success = repo.move_up()
    elif args.direction == 'd':
        success = repo.move_down()
    else:
        print("[CLI] ERROR: Direction must be 'u' (up/newer) or 'd' (down/older)")
        return 1
    
    if success:
        new_hash, new_position = repo.get_current_commit_position()
        print(f"[CLI] ✅ Moved to position {new_position + 1}/{len(chain)} (commit {new_hash[:8]})")
        return 0
    else:
        return 1


def cmd_checkout(args):
    print(f"[CLI] Checking out commit: {args.commit}")
    
    repo = Repository.find_repository()
    if repo is None:
        print("[CLI] ERROR: Not a minigit repository")
        print("[CLI] Run 'minigit init' to initialize a repository")
        return 1
    
    # Check for staged changes
    staged_files = repo.get_staged_files()
    if staged_files:
        print("[CLI] ERROR: You have staged changes")
        print("[CLI] Commit your changes before switching commits")
        return 1
    
    # Show current position
    current_hash, position = repo.get_current_commit_position()
    if current_hash:
        chain = repo.get_commit_chain()
        print(f"[CLI] Current: {position + 1}/{len(chain)} (commit {current_hash[:8]})")
    
    # Move to target commit
    success = repo.move_to_commit(args.commit)
    
    if success:
        new_hash, new_position = repo.get_current_commit_position()
        chain = repo.get_commit_chain()
        print(f"[CLI] ✅ Now at position {new_position + 1}/{len(chain)} (commit {new_hash[:8]})")
        return 0
    else:
        return 1


def main():
    parser = argparse.ArgumentParser(
        prog='minigit',
        description='Mini-Git: A minimal implementation of Git version control'
    )
    
    subparsers = parser.add_subparsers(dest='command', help='Available commands')
    
    init_parser = subparsers.add_parser('init', help='Initialize a new minigit repository')
    init_parser.add_argument(
        'directory', 
        nargs='?', 
        help='Directory to initialize (default: current directory)'
    )
    
    cat_file_parser = subparsers.add_parser('cat-file', help='Display object contents')
    cat_file_parser.add_argument(
        '-p', 
        action='store_true', 
        help='Pretty-print object contents'
    )
    cat_file_parser.add_argument(
        'object', 
        help='Object hash (full or abbreviated)'
    )
    
    status_parser = subparsers.add_parser('status', help='Show working directory status')
    
    add_parser = subparsers.add_parser('add', help='Add files to staging area')
    add_parser.add_argument(
        'files',
        nargs='+',
        help='Files to add to staging area'
    )
    
    commit_parser = subparsers.add_parser('commit', help='Create a new commit')
    commit_parser.add_argument(
        '-m', '--message',
        required=True,
        help='Commit message'
    )
    
    log_parser = subparsers.add_parser('log', help='Show commit history')
    log_parser.add_argument(
        '--max-count',
        type=int,
        help='Maximum number of commits to show'
    )
    
    move_parser = subparsers.add_parser('move', help='Move between commits')
    move_parser.add_argument(
        'direction',
        choices=['u', 'd'],
        help='Direction: u (up/newer) or d (down/older)'
    )
    
    checkout_parser = subparsers.add_parser('checkout', help='Jump to specific commit')
    checkout_parser.add_argument(
        'commit',
        help='Commit hash (4+ characters) to checkout'
    )
    
    if len(sys.argv) < 2:
        parser.print_help()
        return 1
    
    args = parser.parse_args()
    
    if args.command == 'init':
        return cmd_init(args)
    elif args.command == 'cat-file':
        return cmd_cat_file(args)
    elif args.command == 'status':
        return cmd_status(args)
    elif args.command == 'add':
        return cmd_add(args)
    elif args.command == 'commit':
        return cmd_commit(args)
    elif args.command == 'log':
        return cmd_log(args)
    elif args.command == 'move':
        return cmd_move(args)
    elif args.command == 'checkout':
        return cmd_checkout(args)
    else:
        print(f"[CLI] ERROR: Unknown command '{args.command}'")
        parser.print_help()
        return 1


if __name__ == '__main__':
    exit_code = main()
    sys.exit(exit_code)
