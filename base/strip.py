#!/usr/bin/env python3
"""
Script to recursively remove trailing newlines from files.
Treats files as binary and only removes trailing \n or \r\n bytes.
"""

import os
import sys
import argparse
from pathlib import Path


def remove_trailing_newlines(file_path):
    """
    Remove trailing newlines from a file (binary mode).
    
    Args:
        file_path (Path): Path to the file to process
        
    Returns:
        tuple: (was_modified, bytes_removed)
    """
    try:
        # Read file in binary mode
        with open(file_path, 'rb') as f:
            content = f.read()
        
        if not content:
            return False, 0
        
        original_length = len(content)
        
        # Remove trailing \r\n and \n bytes
        while content and content[-1:] in (b'\n', b'\r'):
            if content.endswith(b'\r\n'):
                content = content[:-2]
            elif content.endswith(b'\n'):
                content = content[:-1]
            elif content.endswith(b'\r'):
                content = content[:-1]
        
        bytes_removed = original_length - len(content)
        
        # Only write back if file was modified
        if bytes_removed > 0:
            with open(file_path, 'wb') as f:
                f.write(content)
            return True, bytes_removed
        
        return False, 0
        
    except (IOError, OSError) as e:
        print(f"Error processing {file_path}: {e}", file=sys.stderr)
        return False, 0


def should_process_file(file_path, extensions=None, exclude_patterns=None):
    """
    Determine if a file should be processed based on extension and patterns.
    
    Args:
        file_path (Path): Path to the file
        extensions (set): Set of extensions to include (None = all files)
        exclude_patterns (list): List of patterns to exclude
        
    Returns:
        bool: True if file should be processed
    """
    # Skip if specific extensions are specified and file doesn't match
    if extensions and file_path.suffix.lower() not in extensions:
        return False
    
    # Skip if file matches exclude patterns
    if exclude_patterns:
        file_str = str(file_path)
        for pattern in exclude_patterns:
            if pattern in file_str:
                return False
    
    # Skip binary files that are likely not text-based
    binary_extensions = {
        '.exe', '.dll', '.so', '.dylib', '.bin', '.obj', '.o',
        '.jpg', '.jpeg', '.png', '.gif', '.bmp', '.ico', '.svg',
        '.mp3', '.mp4', '.avi', '.mov', '.wav', '.flac',
        '.zip', '.tar', '.gz', '.rar', '.7z',
        '.pdf', '.doc', '.docx', '.xls', '.xlsx', '.ppt', '.pptx'
    }
    
    if file_path.suffix.lower() in binary_extensions:
        return False
    
    return True


def process_directory(directory, extensions=None, exclude_patterns=None, dry_run=False):
    """
    Recursively process all files in a directory.
    
    Args:
        directory (Path): Directory to process
        extensions (set): Set of file extensions to include
        exclude_patterns (list): List of patterns to exclude
        dry_run (bool): If True, don't modify files, just report what would be done
    """
    total_files = 0
    modified_files = 0
    total_bytes_removed = 0
    
    print(f"Processing directory: {directory}")
    if dry_run:
        print("DRY RUN MODE - No files will be modified")
    print()
    
    for root, dirs, files in os.walk(directory):
        # Skip hidden directories
        dirs[:] = [d for d in dirs if not d.startswith('.')]
        
        for file in files:
            file_path = Path(root) / file
            
            # Skip hidden files
            if file.startswith('.'):
                continue
            
            if not should_process_file(file_path, extensions, exclude_patterns):
                continue
            
            total_files += 1
            
            if dry_run:
                # In dry run, just check what would be removed
                try:
                    with open(file_path, 'rb') as f:
                        content = f.read()
                    
                    if content:
                        original_length = len(content)
                        temp_content = content
                        
                        while temp_content and temp_content[-1:] in (b'\n', b'\r'):
                            if temp_content.endswith(b'\r\n'):
                                temp_content = temp_content[:-2]
                            elif temp_content.endswith(b'\n'):
                                temp_content = temp_content[:-1]
                            elif temp_content.endswith(b'\r'):
                                temp_content = temp_content[:-1]
                        
                        bytes_would_remove = original_length - len(temp_content)
                        if bytes_would_remove > 0:
                            print(f"WOULD MODIFY: {file_path} ({bytes_would_remove} bytes)")
                            modified_files += 1
                            total_bytes_removed += bytes_would_remove
                            
                except (IOError, OSError) as e:
                    print(f"Error reading {file_path}: {e}", file=sys.stderr)
            else:
                # Actually process the file
                was_modified, bytes_removed = remove_trailing_newlines(file_path)
                
                if was_modified:
                    print(f"Modified: {file_path} ({bytes_removed} bytes removed)")
                    modified_files += 1
                    total_bytes_removed += bytes_removed
    
    print(f"\nSummary:")
    print(f"Files processed: {total_files}")
    print(f"Files modified: {modified_files}")
    print(f"Total bytes removed: {total_bytes_removed}")


def main():
    parser = argparse.ArgumentParser(
        description="Recursively remove trailing newlines from files",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s /path/to/directory
  %(prog)s . --extensions .txt .py .js
  %(prog)s /code --exclude node_modules __pycache__ .git
  %(prog)s . --dry-run
        """
    )
    
    parser.add_argument(
        'directory',
        nargs='?',
        default='.',
        help='Directory to process (default: current directory)'
    )
    
    parser.add_argument(
        '--extensions',
        nargs='+',
        help='File extensions to include (e.g., .txt .py .js)'
    )
    
    parser.add_argument(
        '--exclude',
        nargs='+',
        default=['.git', '__pycache__', 'node_modules', '.venv', 'venv'],
        help='Patterns to exclude from processing'
    )
    
    parser.add_argument(
        '--dry-run',
        action='store_true',
        help='Show what would be done without modifying files'
    )
    
    args = parser.parse_args()
    
    directory = Path(args.directory)
    
    if not directory.exists():
        print(f"Error: Directory '{directory}' does not exist", file=sys.stderr)
        sys.exit(1)
    
    if not directory.is_dir():
        print(f"Error: '{directory}' is not a directory", file=sys.stderr)
        sys.exit(1)
    
    # Convert extensions to lowercase set
    extensions = None
    if args.extensions:
        extensions = {ext.lower() if ext.startswith('.') else f'.{ext.lower()}' 
                     for ext in args.extensions}
    
    try:
        process_directory(directory, extensions, args.exclude, args.dry_run)
    except KeyboardInterrupt:
        print("\nOperation cancelled by user", file=sys.stderr)
        sys.exit(1)


if __name__ == '__main__':
    main()