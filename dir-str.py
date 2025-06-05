#!/usr/bin/env python3
"""
Script to display directory structure for debugging FastAPI import issues
"""
import os
from pathlib import Path

def print_tree(directory, prefix="", max_depth=4, current_depth=0):
    """Print directory tree structure"""
    if current_depth > max_depth:
        return
    
    directory = Path(directory)
    if not directory.exists():
        print(f"Directory {directory} does not exist")
        return
    
    # Get all items in directory
    items = []
    try:
        items = list(directory.iterdir())
    except PermissionError:
        print(f"{prefix}[Permission Denied]")
        return
    
    # Sort items - directories first, then files
    items.sort(key=lambda x: (x.is_file(), x.name.lower()))
    
    # Filter out common unimportant directories/files
    skip_dirs = {'.git', '__pycache__', '.pytest_cache', 'node_modules', '.venv', 'venv', '.env'}
    skip_files = {'.gitignore', '.DS_Store', '*.pyc', '*.pyo'}
    
    filtered_items = []
    for item in items:
        if item.name in skip_dirs:
            continue
        if any(item.name.endswith(ext.replace('*', '')) for ext in skip_files if '*' in ext):
            continue
        if item.name in skip_files:
            continue
        filtered_items.append(item)
    
    for i, item in enumerate(filtered_items):
        is_last = i == len(filtered_items) - 1
        current_prefix = "└── " if is_last else "├── "
        print(f"{prefix}{current_prefix}{item.name}")
        
        if item.is_dir() and current_depth < max_depth:
            extension = "    " if is_last else "│   "
            print_tree(item, prefix + extension, max_depth, current_depth + 1)

def main():
    # Try to find the backend directory
    current_dir = Path.cwd()
    
    # Common locations to check
    possible_paths = [
        current_dir,
        current_dir / "backend",
        current_dir / "whokan" / "backend",
        current_dir.parent / "backend",
    ]
    
    backend_dir = None
    for path in possible_paths:
        if (path / "app").exists():
            backend_dir = path
            break
    
    if not backend_dir:
        print("Could not find backend directory with 'app' folder.")
        print("Current directory contents:")
        print_tree(current_dir, max_depth=2)
        return
    
    print(f"Backend directory structure ({backend_dir}):")
    print("=" * 50)
    print_tree(backend_dir)
    
    # Also show key files content if they exist
    key_files = [
        backend_dir / "app" / "db" / "session.py",
        backend_dir / "app" / "deps.py", 
        backend_dir / "app" / "database.py",
        backend_dir / "app" / "db" / "database.py",
    ]
    
    print("\n" + "=" * 50)
    print("Key files found:")
    for file_path in key_files:
        if file_path.exists():
            print(f"✓ {file_path.relative_to(backend_dir)}")
        else:
            print(f"✗ {file_path.relative_to(backend_dir)}")

if __name__ == "__main__":
    main()