#!/usr/bin/env python3
"""Generate a complete file tree listing."""

import os
from pathlib import Path


def should_ignore(path_str):
    """Check if path should be ignored."""
    ignore_patterns = [
        ".git",
        "node_modules",
        "__pycache__",
        ".pytest_cache",
        ".mypy_cache",
        ".venv",
        "venv",
        "env",
        ".env",
        "dist",
        "build",
        ".egg-info",
    ]
    return any(pattern in path_str for pattern in ignore_patterns)


def generate_file_tree(root_dir="."):
    """Generate file tree listing."""
    files = []
    root_path = Path(root_dir).resolve()

    for root, dirs, filenames in os.walk(root_dir):
        # Filter out ignored directories
        dirs[:] = [d for d in dirs if not should_ignore(os.path.join(root, d))]

        for filename in filenames:
            filepath = os.path.join(root, filename)
            if not should_ignore(filepath):
                # Get relative path
                rel_path = os.path.relpath(filepath, root_dir)
                # Normalize path separators
                normalized = rel_path.replace("\\", "/")
                files.append(normalized)

    return sorted(files)


if __name__ == "__main__":
    files = generate_file_tree()
    output_file = "file_tree.txt"

    with open(output_file, "w", encoding="utf-8") as f:
        for file_path in files:
            f.write(file_path + "\n")

    print(f"Generated file tree with {len(files)} files")
    print(f"Output saved to: {output_file}")
