#!/bin/bash

# Mini-Git Quick Demo Script
# ==========================
# A simple bash script to demonstrate mini-git features with colors

# Color definitions
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[0;33m'
BLUE='\033[0;34m'
PURPLE='\033[0;35m'
CYAN='\033[0;36m'
BOLD='\033[1m'
NC='\033[0m' # No Color

# Helper functions
print_header() {
    echo -e "\n${PURPLE}${BOLD}============================================================${NC}"
    echo -e "${PURPLE}${BOLD}$(printf '%*s' $(((60+${#1})/2)) "$1")${NC}"
    echo -e "${PURPLE}${BOLD}============================================================${NC}\n"
}

print_step() {
    echo -e "\n${BLUE}${BOLD}Step $1: $2${NC}"
    echo -e "${BLUE}$(printf '%*s' $((${#2}+10)) '' | tr ' ' '-')${NC}"
    sleep 0.5
}

print_success() {
    echo -e "${GREEN}✅ $1${NC}"
}

print_info() {
    echo -e "${CYAN}ℹ️  $1${NC}"
}

run_cmd() {
    echo -e "${YELLOW}$ $1${NC}"
    sleep 0.5
    eval $1
    echo
    sleep 1
}

# Main demonstration
main() {
    print_header "🚀 MINI-GIT QUICK DEMONSTRATION"
    
    # Setup
    DEMO_DIR="/tmp/minigit-quick-demo"
    rm -rf $DEMO_DIR 2>/dev/null
    mkdir -p $DEMO_DIR
    cd $DEMO_DIR
    
    print_info "Working in: $DEMO_DIR"
    
    # Step 1: Initialize
    print_step 1 "Initialize Repository"
    run_cmd "minigit init"
    print_success "Repository initialized!"
    
    # Step 2: Create first file and commit
    print_step 2 "Create and Commit First File"
    echo "Hello from file1!" > file1.txt
    echo "This is some content in file1" >> file1.txt
    echo "Line 3 of file1" >> file1.txt
    
    print_info "Created file1.txt with content:"
    echo -e "${CYAN}$(cat file1.txt)${NC}"
    
    run_cmd "minigit add file1.txt"
    run_cmd "minigit commit -m 'Add file1 with hello content'"
    print_success "First commit created!"
    
    # Step 3: Create second file and commit
    print_step 3 "Create and Commit Second File"
    echo "World from file2!" > file2.txt
    echo "This is different content in file2" >> file2.txt
    echo "File2 has different data" >> file2.txt
    
    print_info "Created file2.txt with content:"
    echo -e "${CYAN}$(cat file2.txt)${NC}"
    
    run_cmd "minigit add file2.txt"
    run_cmd "minigit commit -m 'Add file2 with world content'"
    print_success "Second commit created!"
    
    # Step 4: Create third file and commit
    print_step 4 "Create and Commit Third File"
    echo "Final file3!" > file3.txt
    echo "This is the last file content" >> file3.txt
    echo "File3 completes our demo" >> file3.txt
    
    print_info "Created file3.txt with content:"
    echo -e "${CYAN}$(cat file3.txt)${NC}"
    
    run_cmd "minigit add file3.txt"
    run_cmd "minigit commit -m 'Add file3 to complete demo'"
    print_success "Third commit created!"
    
    # Step 5: Show current state
    print_step 5 "Current Repository State"
    print_info "All files in latest commit:"
    run_cmd "ls -la"
    
    # Step 6: View commit history
    print_step 6 "View Commit History"
    run_cmd "minigit log"
    
    # Step 7: Inspect objects (get commit hash from log)
    print_step 7 "Inspect Git Objects"
    print_info "Let's inspect the latest commit and its tree:"
    
    # Get the latest commit hash (first 4 chars)
    LATEST_COMMIT=$(minigit log | grep "commit" | head -1 | awk '{print $2}')
    if [ ! -z "$LATEST_COMMIT" ]; then
        echo -e "${YELLOW}Inspecting commit: $LATEST_COMMIT${NC}"
        run_cmd "minigit cat-file -p $LATEST_COMMIT"
        
        # Get tree hash from commit
        TREE_HASH=$(minigit cat-file -p $LATEST_COMMIT | grep "tree" | awk '{print $2}' | cut -c1-4)
        if [ ! -z "$TREE_HASH" ]; then
            echo -e "${YELLOW}Inspecting tree: $TREE_HASH${NC}"
            run_cmd "minigit cat-file -p $TREE_HASH"
        fi
    fi
    
    # Step 8: Demonstrate traversal
    print_step 8 "Commit Traversal Demo"
    
    print_info "Current files (latest commit):"
    run_cmd "ls"
    
    print_info "Moving down to older commits..."
    sleep 1
    run_cmd "minigit move d"
    print_info "Files after first move down:"
    run_cmd "ls"
    
    run_cmd "minigit move d"
    print_info "Files after second move down (oldest commit):"
    run_cmd "ls"
    
    print_info "Moving back up to newer commits..."
    sleep 1
    run_cmd "minigit move u"
    print_info "Files after first move up:"
    run_cmd "ls"
    
    run_cmd "minigit move u"
    print_info "Files after second move up (back to latest):"
    run_cmd "ls"
    
    # Step 9: Final status
    print_step 9 "Final Status"
    run_cmd "minigit status"
    
    # Summary
    print_header "🎉 DEMONSTRATION COMPLETE"
    print_success "Mini-Git demonstration completed successfully!"
    print_info "Repository location: $DEMO_DIR"
    print_info "You can explore it manually with:"
    echo -e "${YELLOW}  cd $DEMO_DIR${NC}"
    echo -e "${YELLOW}  minigit status${NC}"
    echo -e "${YELLOW}  minigit log${NC}"
    echo -e "${YELLOW}  minigit move d  # Move to older commit${NC}"
    echo -e "${YELLOW}  minigit move u  # Move to newer commit${NC}"
}

# Run the demonstration
main
