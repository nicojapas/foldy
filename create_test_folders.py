#!/usr/bin/env python3
"""
Creates a test directory structure with various naming inconsistencies
for testing the FolderSense tool.
"""
import os
import argparse
import shutil
import time
import random

def create_test_structure(base_path):
    """
    Creates a test directory structure with various naming inconsistencies.
    """
    # Ensure the base directory exists
    os.makedirs(base_path, exist_ok=True)
    
    # Clean any existing content
    for item in os.listdir(base_path):
        item_path = os.path.join(base_path, item)
        if os.path.isdir(item_path):
            shutil.rmtree(item_path)
        else:
            os.remove(item_path)
    
    # Create folders with case inconsistencies
    os.makedirs(os.path.join(base_path, "projects"), exist_ok=True)
    os.makedirs(os.path.join(base_path, "Projects"), exist_ok=True)
    os.makedirs(os.path.join(base_path, "PROJECTS"), exist_ok=True)
    
    # Create folders with separator inconsistencies
    os.makedirs(os.path.join(base_path, "work_documents"), exist_ok=True)
    os.makedirs(os.path.join(base_path, "work-documents"), exist_ok=True)
    os.makedirs(os.path.join(base_path, "work documents"), exist_ok=True)
    
    # Create folders with number padding inconsistencies
    os.makedirs(os.path.join(base_path, "chapter1"), exist_ok=True)
    os.makedirs(os.path.join(base_path, "chapter2"), exist_ok=True)
    os.makedirs(os.path.join(base_path, "chapter01"), exist_ok=True)
    os.makedirs(os.path.join(base_path, "chapter02"), exist_ok=True)
    
    # Create similar folders that could be merged
    os.makedirs(os.path.join(base_path, "photos"), exist_ok=True)
    os.makedirs(os.path.join(base_path, "pictures"), exist_ok=True)
    os.makedirs(os.path.join(base_path, "images"), exist_ok=True)
    
    # Create folders that could be grouped
    os.makedirs(os.path.join(base_path, "finance_2021"), exist_ok=True)
    os.makedirs(os.path.join(base_path, "finance_2022"), exist_ok=True)
    os.makedirs(os.path.join(base_path, "finance_2023"), exist_ok=True)
    
    # Create a deeper structure with inconsistencies
    os.makedirs(os.path.join(base_path, "project_alpha", "docs"), exist_ok=True)
    os.makedirs(os.path.join(base_path, "project_alpha", "source"), exist_ok=True)
    os.makedirs(os.path.join(base_path, "project_beta", "documentation"), exist_ok=True)
    os.makedirs(os.path.join(base_path, "project_beta", "src"), exist_ok=True)
    os.makedirs(os.path.join(base_path, "project_gamma", "Docs"), exist_ok=True)
    os.makedirs(os.path.join(base_path, "project_gamma", "Source_code"), exist_ok=True)
    
    # Create empty files in some of the folders
    for root, dirs, files in os.walk(base_path):
        # Create 1-5 empty files in each directory
        num_files = random.randint(1, 5)
        for i in range(num_files):
            with open(os.path.join(root, f"file_{i}.txt"), "w") as f:
                f.write(f"This is a test file {i} in {os.path.basename(root)}")
    
    # Add some README files
    with open(os.path.join(base_path, "README.txt"), "w") as f:
        f.write("This is a test folder structure for the FolderSense tool.\n")
        f.write("Use this structure to test the tool's ability to detect and suggest improvements.\n")
    
    # Create loose files in the root directory for testing file grouping functionality
    # Create a bunch of image files
    for i in range(10):
        with open(os.path.join(base_path, f"photo_{i}.jpg"), "w") as f:
            f.write(f"This is a test image {i}")
    
    # Create some document files
    for i in range(8):
        with open(os.path.join(base_path, f"document_{i}.pdf"), "w") as f:
            f.write(f"This is a test document {i}")
    
    # Create some spreadsheet files
    for i in range(6):
        with open(os.path.join(base_path, f"spreadsheet_{i}.xlsx"), "w") as f:
            f.write(f"This is a test spreadsheet {i}")
    
    # Create some source code files
    for i in range(5):
        with open(os.path.join(base_path, f"code_{i}.py"), "w") as f:
            f.write(f"# This is a test Python file {i}\nprint('Hello, world!')")
    
    # Create some random files with mixed extensions
    mixed_extensions = ['.json', '.csv', '.log', '.xml', '.md', '.ini']
    for i in range(8):
        ext = random.choice(mixed_extensions)
        with open(os.path.join(base_path, f"mixed_file_{i}{ext}"), "w") as f:
            f.write(f"This is a mixed test file {i} with extension {ext}")
    
    print(f"Test folder structure created successfully at: {base_path}")
    print("You can now run FolderSense on this directory to test its functionality.")
    print("Example: python main.py " + base_path + " --dry-run")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Create a test folder structure for FolderSense")
    parser.add_argument("--path", default="./test_folders", help="Path where to create the test structure")
    
    args = parser.parse_args()
    create_test_structure(args.path) 