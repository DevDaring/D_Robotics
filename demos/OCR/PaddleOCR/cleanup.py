#!/usr/bin/env python3
"""
cleanup.py - Delete old voice files, images, and temp files

Usage:
    python3 cleanup.py          # Delete all temp/output files
    python3 cleanup.py --all    # Also delete __pycache__ folders
    
For hackathon: Run this before demo to clear old files.
"""

import os
import shutil
import sys
from pathlib import Path

# Directories to clean
BASE_DIR = Path(__file__).parent
TEMP_DIR = BASE_DIR / "temp"
OUTPUT_DIR = BASE_DIR / "output"
DATA_DIR = BASE_DIR / "data"

# File patterns to delete
VOICE_PATTERNS = ["*.wav", "*.mp3", "*.ogg", "*.flac"]
IMAGE_PATTERNS = ["*.jpg", "*.jpeg", "*.png", "*.bmp", "snapshot_*.jpg", "prescription_*.jpg"]
TEMP_PATTERNS = ["*.tmp", "*.temp", "*.log"]


def delete_files_in_dir(directory: Path, patterns: list, dry_run: bool = False):
    """Delete files matching patterns in a directory."""
    deleted_count = 0
    deleted_size = 0
    
    if not directory.exists():
        return 0, 0
    
    for pattern in patterns:
        for file_path in directory.glob(pattern):
            if file_path.is_file():
                size = file_path.stat().st_size
                if dry_run:
                    print(f"  [DRY RUN] Would delete: {file_path} ({size} bytes)")
                else:
                    try:
                        file_path.unlink()
                        print(f"  ✅ Deleted: {file_path.name} ({size} bytes)")
                        deleted_count += 1
                        deleted_size += size
                    except Exception as e:
                        print(f"  ❌ Failed to delete {file_path}: {e}")
    
    return deleted_count, deleted_size


def delete_pycache(base_dir: Path):
    """Delete all __pycache__ folders."""
    deleted = 0
    for pycache in base_dir.rglob("__pycache__"):
        if pycache.is_dir():
            try:
                shutil.rmtree(pycache)
                print(f"  ✅ Deleted: {pycache}")
                deleted += 1
            except Exception as e:
                print(f"  ❌ Failed: {pycache}: {e}")
    return deleted


def format_size(size_bytes):
    """Format bytes to human readable."""
    if size_bytes < 1024:
        return f"{size_bytes} B"
    elif size_bytes < 1024 * 1024:
        return f"{size_bytes / 1024:.1f} KB"
    else:
        return f"{size_bytes / (1024 * 1024):.1f} MB"


def main():
    print("=" * 60)
    print("🧹 KELVIN CLEANUP - Delete temp/output files")
    print("=" * 60)
    
    # Check for flags
    delete_all = "--all" in sys.argv
    dry_run = "--dry-run" in sys.argv
    
    if dry_run:
        print("⚠️  DRY RUN MODE - No files will be deleted\n")
    
    total_files = 0
    total_size = 0
    
    # 1. Clean temp directory (voice files)
    print("\n📁 Cleaning TEMP directory (voice files)...")
    if TEMP_DIR.exists():
        count, size = delete_files_in_dir(TEMP_DIR, VOICE_PATTERNS + TEMP_PATTERNS, dry_run)
        total_files += count
        total_size += size
        if count == 0:
            print("  (empty)")
    else:
        print("  (directory doesn't exist)")
    
    # 2. Clean output directory (images)
    print("\n📁 Cleaning OUTPUT directory (images)...")
    if OUTPUT_DIR.exists():
        count, size = delete_files_in_dir(OUTPUT_DIR, IMAGE_PATTERNS + VOICE_PATTERNS, dry_run)
        total_files += count
        total_size += size
        if count == 0:
            print("  (empty)")
    else:
        print("  (directory doesn't exist)")
    
    # 3. Clean data directory
    print("\n📁 Cleaning DATA directory...")
    if DATA_DIR.exists():
        count, size = delete_files_in_dir(DATA_DIR, IMAGE_PATTERNS, dry_run)
        total_files += count
        total_size += size
        if count == 0:
            print("  (empty)")
    else:
        print("  (directory doesn't exist)")
    
    # 4. Clean root directory temp files
    print("\n📁 Cleaning ROOT directory (temp files)...")
    count, size = delete_files_in_dir(BASE_DIR, ["test.wav", "test.mp3", "*.tmp"], dry_run)
    total_files += count
    total_size += size
    if count == 0:
        print("  (no temp files)")
    
    # 5. Optional: Delete __pycache__
    if delete_all:
        print("\n📁 Cleaning __pycache__ folders...")
        pycache_count = delete_pycache(BASE_DIR)
        if pycache_count == 0:
            print("  (none found)")
    
    # Summary
    print("\n" + "=" * 60)
    if dry_run:
        print(f"🧹 DRY RUN: Would delete {total_files} files ({format_size(total_size)})")
    else:
        print(f"🧹 CLEANUP COMPLETE: Deleted {total_files} files ({format_size(total_size)})")
    print("=" * 60)
    
    # Ensure directories exist for next run
    if not dry_run:
        TEMP_DIR.mkdir(exist_ok=True)
        OUTPUT_DIR.mkdir(exist_ok=True)
        print("\n✅ Directories ready for next run")


if __name__ == "__main__":
    main()
