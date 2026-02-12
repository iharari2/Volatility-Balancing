#!/usr/bin/env python3
"""Generate a complete file tree listing including all files and directories."""

import os
from pathlib import Path


def generate_complete_file_tree(root_dir="."):
    """Generate complete file tree listing with both files and directories."""
    items = []
    root_path = Path(root_dir).resolve()

    # Add root directory
    items.append(".")

    for root, dirs, filenames in os.walk(root_dir):
        # Sort directories and files for consistent output
        dirs.sort()
        filenames.sort()

        # Add directories
        for dirname in dirs:
            dirpath = os.path.join(root, dirname)
            rel_path = os.path.relpath(dirpath, root_dir)
            normalized = rel_path.replace("\\", "/")
            items.append(normalized + "/")

        # Add files
        for filename in filenames:
            filepath = os.path.join(root, filename)
            rel_path = os.path.relpath(filepath, root_dir)
            normalized = rel_path.replace("\\", "/")
            items.append(normalized)

    return sorted(set(items))  # Remove duplicates and sort


if __name__ == "__main__":
    items = generate_complete_file_tree()
    output_file = "complete_file_tree.txt"

    with open(output_file, "w", encoding="utf-8") as f:
        for item in items:
            f.write(item + "\n")

    print(f"Generated complete file tree with {len(items)} items")
    print(f"Output saved to: {output_file}")
