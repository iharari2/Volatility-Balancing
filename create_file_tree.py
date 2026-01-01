#!/usr/bin/env python3
"""Generate a complete file tree listing."""

import os


def generate_file_tree(root_dir="."):
    """Generate complete file tree listing."""
    items = []

    # Add root
    items.append(".")

    for root, dirs, files in os.walk(root_dir):
        # Sort for consistent output
        dirs.sort()
        files.sort()

        # Skip hidden and cache directories for cleaner output, but user can modify
        dirs[:] = [d for d in dirs if not d.startswith(".") or d in [".git"]]

        for d in dirs:
            rel_path = os.path.relpath(os.path.join(root, d), root_dir)
            items.append(rel_path.replace("\\", "/") + "/")

        for f in files:
            rel_path = os.path.relpath(os.path.join(root, f), root_dir)
            items.append(rel_path.replace("\\", "/"))

    return sorted(set(items))


if __name__ == "__main__":
    tree = generate_file_tree()
    output = "complete_file_tree.txt"
    with open(output, "w", encoding="utf-8") as f:
        f.write("\n".join(tree))
    print(f"Created {output} with {len(tree)} items")
