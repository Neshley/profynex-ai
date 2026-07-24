#!/usr/bin/env python
"""Build script to create downloadable ZIP file.

Usage:
    python build.py

This will create profynex-ai.zip in the project root.
"""

import zipfile
import sys
from pathlib import Path
import shutil


def create_project_zip(output_path: Path = None) -> bool:
    """Create project ZIP file."""
    if output_path is None:
        output_path = Path.cwd() / "profynex-ai.zip"
    
    project_root = Path.cwd()
    
    # Files and directories to include
    include_items = [
        "src/",
        "docs/",
        "tests/",
        "config/",
        "README.md",
        "INSTALLATION.md",
        "requirements.txt",
        "package.json",
        "tsconfig.json",
        ".env.example",
        ".gitignore",
        "LICENSE",
        "CONTRIBUTING.md",
        "setup.py",
        "install.py",
        "build.py",
    ]
    
    # Directories to exclude
    exclude_dirs = {
        "venv",
        "node_modules",
        ".git",
        "__pycache__",
        ".pytest_cache",
        "build",
        "dist",
        ".egg-info",
        "user_data",
        "logs",
        "cache",
    }
    
    try:
        print(f"Creating {output_path}...")
        
        with zipfile.ZipFile(output_path, "w", zipfile.ZIP_DEFLATED) as zipf:
            for item in include_items:
                item_path = project_root / item
                
                if item_path.is_file():
                    arcname = f"profynex-ai/{item}"
                    zipf.write(item_path, arcname)
                    print(f"  ✓ Added {item}")
                
                elif item_path.is_dir():
                    for file_path in item_path.rglob("*"):
                        # Skip excluded directories
                        if any(part in exclude_dirs for part in file_path.parts):
                            continue
                        if file_path.is_file():
                            rel_path = file_path.relative_to(project_root)
                            arcname = f"profynex-ai/{rel_path}"
                            zipf.write(file_path, arcname)
        
        # Get file size
        size_mb = output_path.stat().st_size / (1024 * 1024)
        
        print(f"\n✓ Project archive created successfully!")
        print(f"  Location: {output_path}")
        print(f"  Size: {size_mb:.2f} MB")
        print(f"\nTo use the archive:")
        print(f"  1. Download: {output_path}")
        print(f"  2. Extract to your desired location")
        print(f"  3. Run: python install.py")
        
        return True
    except Exception as e:
        print(f"✗ Failed to create archive: {e}", file=sys.stderr)
        return False


if __name__ == "__main__":
    output_file = Path.cwd() / "profynex-ai.zip"
    
    # Remove existing archive if it exists
    if output_file.exists():
        print(f"Removing existing archive: {output_file}")
        output_file.unlink()
    
    success = create_project_zip(output_file)
    sys.exit(0 if success else 1)
