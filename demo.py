#!/usr/bin/env python3
"""
Mini-Git Demonstration Script
============================

This script demonstrates all the key features of mini-git:
- Repository initialization
- File creation and staging
- Commits with multiple files
- Log viewing with object inspection
- Commit traversal (move up/down)
- Cat-file inspection of all objects

Features colorful output for better visualization.
"""

import os
import sys
import subprocess
import random
import string
import time
from pathlib import Path

# ANSI color codes for beautiful output
class Colors:
    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKCYAN = '\033[96m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'

def print_header(title):
    """Print a colorful header"""
    print(f"\n{Colors.HEADER}{'='*60}{Colors.ENDC}")
    print(f"{Colors.HEADER}{Colors.BOLD}{title.center(60)}{Colors.ENDC}")
    print(f"{Colors.HEADER}{'='*60}{Colors.ENDC}\n")

def print_step(step_num, description):
    """Print a step with numbering"""
    print(f"{Colors.OKBLUE}{Colors.BOLD}Step {step_num}: {description}{Colors.ENDC}")
    print(f"{Colors.OKBLUE}{'-' * (len(description) + 10)}{Colors.ENDC}")
    time.sleep(0.5)  # Quick pause for video recording

def print_success(message):
    """Print success message"""
    print(f"{Colors.OKGREEN}✅ {message}{Colors.ENDC}")
    time.sleep(0.5)  # Quick success pause for video

def print_info(message):
    """Print info message"""
    print(f"{Colors.OKCYAN}ℹ️  {message}{Colors.ENDC}")

def print_warning(message):
    """Print warning message"""
    print(f"{Colors.WARNING}⚠️  {message}{Colors.ENDC}")

def run_command(cmd, description=""):
    """Run a command and display output with colors"""
    if description:
        print(f"{Colors.OKCYAN}Running: {description}{Colors.ENDC}")
        time.sleep(0.3)  # Quick description pause for video
    
    print(f"{Colors.WARNING}$ {cmd}{Colors.ENDC}")
    time.sleep(0.5)  # Quick command preview for video
    
    result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
    
    if result.stdout:
        # Color the output based on content
        lines = result.stdout.strip().split('\n')
        for line in lines:
            if '[CLI]' in line and '✅' in line:
                print(f"{Colors.OKGREEN}{line}{Colors.ENDC}")
            elif '[Repository]' in line and ('Created' in line or 'Stored' in line):
                print(f"{Colors.OKBLUE}{line}{Colors.ENDC}")
            elif 'hash' in line.lower() or 'commit' in line.lower():
                print(f"{Colors.OKCYAN}{line}{Colors.ENDC}")
            else:
                print(line)
    
    if result.stderr:
        print(f"{Colors.FAIL}Error: {result.stderr}{Colors.ENDC}")
    
    print()  # Add spacing
    time.sleep(1)  # Perfect 1 second pause for video recording
    return result

def generate_random_content(length=50):
    """Generate random content for files"""
    return ''.join(random.choices(string.ascii_letters + string.digits + ' \n', k=length))

def create_file_with_content(filename, content):
    """Create a file with given content"""
    with open(filename, 'w') as f:
        f.write(content)
    print(f"{Colors.OKGREEN}Created {filename} with {len(content)} characters{Colors.ENDC}")

def show_file_content(filename):
    """Show file content with colors"""
    if os.path.exists(filename):
        with open(filename, 'r') as f:
            content = f.read()
        print(f"{Colors.OKCYAN}📄 Content of {filename}:{Colors.ENDC}")
        print(f"{Colors.WARNING}{content[:100]}{'...' if len(content) > 100 else ''}{Colors.ENDC}")
        time.sleep(1)  # Perfect timing for video
    else:
        print(f"{Colors.FAIL}❌ File {filename} does not exist{Colors.ENDC}")
        time.sleep(0.5)

def main():
    print_header("🚀 MINI-GIT DEMONSTRATION")
    
    # Setup demo directory
    demo_dir = "/tmp/minigit-demo"
    if os.path.exists(demo_dir):
        subprocess.run(f"rm -rf {demo_dir}", shell=True)
    os.makedirs(demo_dir)
    os.chdir(demo_dir)
    
    print_info(f"Working in: {demo_dir}")
    
    # Step 1: Initialize repository
    print_step(1, "Initialize Mini-Git Repository")
    run_command("minigit init", "Initialize new mini-git repository")
    print_success("Repository initialized!")
    
    # Step 2-4: Create files and commits
    files_data = []
    commit_hashes = []
    
    for i in range(1, 4):
        print_step(i + 1, f"Create File {i} and Make Commit")
        
        # Generate file content
        filename = f"file{i}.txt"
        content = f"File {i} Content:\n" + generate_random_content(80 + i * 20)
        files_data.append((filename, content))
        
        # Create file
        create_file_with_content(filename, content)
        show_file_content(filename)
        
        # Add to staging
        run_command(f"minigit add {filename}", f"Stage {filename}")
        
        # Show status
        run_command("minigit status", "Check repository status")
        
        # Commit
        commit_msg = f"Add {filename} with random content"
        result = run_command(f'minigit commit -m "{commit_msg}"', f"Commit {filename}")
        
        # Extract commit hash from output
        for line in result.stdout.split('\n'):
            if '✅ Created commit' in line:
                hash_part = line.split('commit ')[1].split()[0]
                commit_hashes.append(hash_part)
                break
        
        print_success(f"Committed {filename}!")
        
        # Show current files
        print(f"{Colors.OKCYAN}📁 Current files in working directory:{Colors.ENDC}")
        run_command("ls -la", "List current files")
    
    # Step 5: Show complete log
    print_step(5, "View Complete Commit History")
    run_command("minigit log", "Show all commits")
    
    # Step 6: Inspect objects with cat-file
    print_step(6, "Inspect Git Objects with cat-file")
    
    for i, commit_hash in enumerate(commit_hashes, 1):
        print(f"\n{Colors.BOLD}🔍 Inspecting Commit {i} ({commit_hash}):{Colors.ENDC}")
        run_command(f"minigit cat-file -p {commit_hash}", f"Inspect commit {commit_hash}")
        
        # Get tree hash from commit and inspect it
        result = subprocess.run(f"minigit cat-file -p {commit_hash}", shell=True, capture_output=True, text=True)
        for line in result.stdout.split('\n'):
            if line.startswith('tree '):
                tree_hash = line.split()[1][:4]  # Get first 4 chars
                print(f"\n{Colors.BOLD}🌳 Inspecting Tree {tree_hash}:{Colors.ENDC}")
                run_command(f"minigit cat-file -p {tree_hash}", f"Inspect tree {tree_hash}")
                break
    
    # Step 7: Demonstrate commit traversal
    print_step(7, "Demonstrate Commit Traversal")
    
    print(f"{Colors.BOLD}📍 Current state (latest commit):{Colors.ENDC}")
    time.sleep(0.5)
    run_command("ls -la", "Show current files")
    for filename, _ in files_data:
        show_file_content(filename)
    
    # Move down to oldest commit
    print(f"\n{Colors.BOLD}⬇️  Moving down to older commits:{Colors.ENDC}")
    time.sleep(1)  # Video-friendly pause before traversal
    for i in range(len(commit_hashes) - 1):
        run_command("minigit move d", f"Move down to older commit")
        print(f"{Colors.OKCYAN}📁 Files after moving down:{Colors.ENDC}")
        time.sleep(0.5)
        run_command("ls -la", "List files")
        # Show content of remaining files
        for filename, _ in files_data:
            if os.path.exists(filename):
                show_file_content(filename)
    
    print(f"\n{Colors.BOLD}📍 Now at oldest commit:{Colors.ENDC}")
    time.sleep(1)
    run_command("ls -la", "Show files in oldest commit")
    
    # Move back up to latest commit
    print(f"\n{Colors.BOLD}⬆️  Moving up to newer commits:{Colors.ENDC}")
    time.sleep(1)  # Video-friendly pause
    for i in range(len(commit_hashes) - 1):
        run_command("minigit move u", f"Move up to newer commit")
        print(f"{Colors.OKCYAN}📁 Files after moving up:{Colors.ENDC}")
        time.sleep(0.5)
        run_command("ls -la", "List files")
        # Show content of files
        for filename, _ in files_data:
            if os.path.exists(filename):
                show_file_content(filename)
    
    print(f"\n{Colors.BOLD}📍 Back at latest commit:{Colors.ENDC}")
    run_command("ls -la", "Show all files restored")
    
    # Step 8: Final inspection
    print_step(8, "Final Status and Summary")
    run_command("minigit status", "Final repository status")
    run_command("minigit log", "Final commit history")
    
    # Summary
    print_header("🎉 DEMONSTRATION COMPLETE")
    print_success("Mini-Git demonstration completed successfully!")
    print_info(f"Repository created at: {demo_dir}")
    print_info(f"Total commits made: {len(commit_hashes)}")
    print_info(f"Files created: {', '.join([f[0] for f in files_data])}")
    print_info("All features demonstrated:")
    print("   ✅ Repository initialization (minigit init)")
    print("   ✅ File staging (minigit add)")
    print("   ✅ Committing changes (minigit commit)")
    print("   ✅ Viewing history (minigit log)")
    print("   ✅ Object inspection (minigit cat-file)")
    print("   ✅ Commit traversal (minigit move u/d)")
    print("   ✅ Repository status (minigit status)")
    
    print(f"\n{Colors.OKCYAN}💡 Try exploring the repository manually:{Colors.ENDC}")
    print(f"   cd {demo_dir}")
    print("   minigit status")
    print("   minigit log")
    print("   minigit move d  # Move to older commit")
    print("   minigit move u  # Move to newer commit")

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print(f"\n{Colors.WARNING}Demo interrupted by user{Colors.ENDC}")
    except Exception as e:
        print(f"\n{Colors.FAIL}Error during demonstration: {e}{Colors.ENDC}")
        sys.exit(1)
