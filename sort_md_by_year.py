#!/usr/bin/env python3
"""
Sort markdown files into year-based subdirectories based on their YAML frontmatter.

This script reads markdown files, extracts the 'Created at' date from the YAML
frontmatter, and organizes them into subdirectories by year. It also handles
moving associated resource files referenced in the markdown.
"""

import argparse
import hashlib
import re
from pathlib import Path
from datetime import datetime


def extract_year_from_filename(file_path: Path) -> int | None:
    """
    Extract the year from filename if it starts with YYYYMMDD_ pattern.

    Args:
        file_path: Path to the markdown file

    Returns:
        Year as integer, or None if pattern not found or invalid
    """
    filename = file_path.name

    # Match YYYYMMDD_ pattern at the start of filename
    match = re.match(r'^(\d{4})(\d{2})(\d{2})_', filename)
    if not match:
        return None

    year = int(match.group(1))
    month = int(match.group(2))
    day = int(match.group(3))

    # Basic validation: year should be reasonable (1900-2100), month 1-12, day 1-31
    if 1900 <= year <= 2100 and 1 <= month <= 12 and 1 <= day <= 31:
        return year

    return None


def extract_year_from_frontmatter(file_path: Path) -> int | None:
    """
    Extract the year from the 'Created at' field in YAML frontmatter,
    with fallback to filename date pattern.

    Args:
        file_path: Path to the markdown file

    Returns:
        Year as integer, or None if not found or invalid
    """
    try:
        content = file_path.read_text(encoding='utf-8')

        # Match YAML frontmatter block (between --- delimiters)
        frontmatter_match = re.match(r'^---\s*\n(.*?)\n---', content, re.DOTALL)
        if frontmatter_match:
            frontmatter = frontmatter_match.group(1)

            # Extract 'Created at' field
            created_match = re.search(r'^Created at:\s*(\d{4})-\d{2}-\d{2}', frontmatter, re.MULTILINE)
            if created_match:
                year = int(created_match.group(1))
                return year

        # Fallback: try to extract year from filename
        return extract_year_from_filename(file_path)

    except (OSError, UnicodeDecodeError) as e:
        print(f"Error reading {file_path}: {e}")
        return None


def extract_resource_links(file_path: Path) -> list[str]:
    """
    Extract resource file references from markdown file.

    Args:
        file_path: Path to the markdown file

    Returns:
        List of resource file paths (e.g., ['_resources/video.mp4', '_resources/image.png'])
    """
    try:
        content = file_path.read_text(encoding='utf-8')

        # Match both ![[_resources/...]] (embedded) and [[_resources/...]] (linked) patterns
        # The !? makes the exclamation mark optional
        # This captures both the file path and any display text after |
        pattern = r'!?\[\[(_resources/[^\]|]+)'
        matches = re.findall(pattern, content)

        return matches

    except (OSError, UnicodeDecodeError) as e:
        print(f"Error reading {file_path}: {e}")
        return []


def compute_file_hash(file_path: Path) -> str | None:
    """
    Compute SHA256 hash of a file.

    Args:
        file_path: Path to the file

    Returns:
        Hex string of the hash, or None if file cannot be read
    """
    try:
        sha256_hash = hashlib.sha256()
        with open(file_path, "rb") as f:
            for byte_block in iter(lambda: f.read(4096), b""):
                sha256_hash.update(byte_block)
        return sha256_hash.hexdigest()
    except OSError as e:
        print(f"Error hashing {file_path}: {e}")
        return None


def get_unique_filename(target_path: Path) -> Path:
    """
    Generate a unique filename by adding a numeric suffix if needed.

    Args:
        target_path: Desired target path

    Returns:
        A unique path that doesn't exist yet
    """
    if not target_path.exists():
        return target_path

    stem = target_path.stem
    suffix = target_path.suffix
    parent = target_path.parent
    counter = 1

    while True:
        new_path = parent / f"{stem}_{counter}{suffix}"
        if not new_path.exists():
            return new_path
        counter += 1


def update_resource_link_in_markdown(md_file: Path, old_name: str, new_name: str, execute: bool) -> bool:
    """
    Update a resource link in the markdown file.

    Args:
        md_file: Path to the markdown file
        old_name: Original resource filename
        new_name: New resource filename
        execute: If True, actually modify the file

    Returns:
        True if successful, False otherwise
    """
    try:
        content = md_file.read_text(encoding='utf-8')

        # Replace the resource reference
        # Match the pattern ![[_resources/old_name...]] and replace just the filename
        old_pattern = re.escape(old_name)
        pattern = r'(!\[\[_resources/)' + old_pattern + r'(\|[^\]]+\]\]|\]\])'
        replacement = r'\1' + new_name + r'\2'

        new_content = re.sub(pattern, replacement, content)

        if execute:
            md_file.write_text(new_content, encoding='utf-8')

        return True

    except (OSError, UnicodeDecodeError) as e:
        print(f"Error updating {md_file}: {e}")
        return False


def move_resource_file(source_resource: Path, target_resource: Path, md_file: Path,
                       resource_name: str, execute: bool) -> tuple[bool, str | None, str]:
    """
    Move a resource file, handling conflicts intelligently.

    Args:
        source_resource: Source path of the resource file
        target_resource: Target path for the resource file
        md_file: Path to the markdown file (for updating links if needed)
        resource_name: Original resource filename (for updating links)
        execute: If True, actually move the file

    Returns:
        Tuple of (success, new_filename, status) where:
        - success: True if operation completed without errors
        - new_filename: Set if file was renamed, None otherwise
        - status: 'moved', 'renamed', 'missing', 'identical'
    """
    if not source_resource.exists():
        print(f"  WARN: Resource not found: {source_resource.name}")
        return (True, None, 'missing')  # Continue anyway

    if target_resource.exists():
        # Compare file hashes
        source_hash = compute_file_hash(source_resource)
        target_hash = compute_file_hash(target_resource)

        if source_hash and target_hash and source_hash == target_hash:
            # Same file, can overwrite (or skip since it's identical)
            print(f"  RESOURCE (identical): {source_resource.name}")
            return (True, None, 'identical')
        else:
            # Different files, need to rename
            unique_target = get_unique_filename(target_resource)
            new_filename = unique_target.name

            if execute:
                try:
                    source_resource.rename(unique_target)
                    # Update the markdown file to reference the new name
                    update_resource_link_in_markdown(md_file, resource_name, new_filename, execute=True)
                    print(f"  RESOURCE (renamed): {source_resource.name} -> {new_filename}")
                    return (True, new_filename, 'renamed')
                except OSError as e:
                    print(f"  ERROR moving resource {source_resource.name}: {e}")
                    return (False, None, 'error')
            else:
                print(f"  WOULD RENAME RESOURCE: {source_resource.name} -> {new_filename}")
                print(f"  WOULD UPDATE: {md_file.name} to reference {new_filename}")
                return (True, new_filename, 'renamed')
    else:
        # No conflict, just move
        if execute:
            try:
                target_resource.parent.mkdir(parents=True, exist_ok=True)
                source_resource.rename(target_resource)
                print(f"  RESOURCE: {source_resource.name}")
                return (True, None, 'moved')
            except OSError as e:
                print(f"  ERROR moving resource {source_resource.name}: {e}")
                return (False, None, 'error')
        else:
            print(f"  WOULD MOVE RESOURCE: {source_resource.name}")
            return (True, None, 'moved')


def sort_markdown_files(path: Path, resources_path: Path | None = None, execute: bool = False) -> None:
    """
    Sort markdown files into year-based subdirectories.

    Args:
        path: Directory containing markdown files
        resources_path: Path to _resources directory (optional)
        execute: If True, actually move files. If False, dry-run mode.
    """
    if not path.exists():
        print(f"Error: Path '{path}' does not exist")
        return

    if not path.is_dir():
        print(f"Error: Path '{path}' is not a directory")
        return

    if resources_path and not resources_path.exists():
        print(f"Warning: Resources path '{resources_path}' does not exist")
        resources_path = None

    # Find all .md files in the directory (non-recursive)
    md_files = list(path.glob('*.md'))

    if not md_files:
        print(f"No markdown files found in {path}")
        return

    print(f"Found {len(md_files)} markdown file(s)")
    if resources_path:
        print(f"Resources directory: {resources_path}")
    print(f"Mode: {'EXECUTE' if execute else 'DRY-RUN (use --execute to actually move files)'}")
    print("-" * 60)

    stats = {
        'moved': 0,
        'skipped_no_date': 0,
        'skipped_exists': 0,
        'resources_moved': 0,
        'resources_renamed': 0,
        'resources_missing': 0,
        'errors': 0
    }

    for md_file in md_files:
        year = extract_year_from_frontmatter(md_file)

        if year is None:
            print(f"SKIP (no date): {md_file.name}")
            stats['skipped_no_date'] += 1
            continue

        # Create year subdirectory path
        year_dir = path / str(year)
        target_path = year_dir / md_file.name

        # Check if target already exists
        if target_path.exists():
            print(f"SKIP (exists): {md_file.name} -> {year}/{md_file.name}")
            stats['skipped_exists'] += 1
            continue

        # Extract and process resource links if resources_path is provided
        resource_links = []
        if resources_path:
            resource_links = extract_resource_links(md_file)

        # Move or show what would be moved
        action_verb = "MOVED" if execute else "WOULD MOVE"
        print(f"{action_verb}: {md_file.name} -> {year}/{md_file.name}")

        if execute:
            try:
                year_dir.mkdir(exist_ok=True)
                md_file.rename(target_path)
                stats['moved'] += 1
            except OSError as e:
                print(f"ERROR moving {md_file.name}: {e}")
                stats['errors'] += 1
                continue
        else:
            stats['moved'] += 1

        # Handle resources
        if resources_path and resource_links:
            year_resources_dir = year_dir / "_resources"

            for resource_link in resource_links:
                # Extract just the filename from the _resources/filename path
                resource_filename = Path(resource_link).name
                source_resource = resources_path / resource_filename
                target_resource = year_resources_dir / resource_filename

                # For dry-run, use the original md_file path; for execute, use the new path
                md_file_for_update = target_path if execute else md_file

                success, new_filename, status = move_resource_file(
                    source_resource, target_resource, md_file_for_update,
                    resource_filename, execute
                )

                if success:
                    if status == 'moved':
                        stats['resources_moved'] += 1
                    elif status == 'renamed':
                        stats['resources_renamed'] += 1
                    elif status == 'missing':
                        stats['resources_missing'] += 1
                    # 'identical' doesn't increment any counter (file already exists and is the same)
                else:
                    stats['errors'] += 1

    # Print summary
    print("-" * 60)
    print(f"Summary:")
    print(f"  {'Moved' if execute else 'Would move'}: {stats['moved']}")
    print(f"  Skipped (no date): {stats['skipped_no_date']}")
    print(f"  Skipped (exists): {stats['skipped_exists']}")
    if resources_path:
        print(f"  Resources moved: {stats['resources_moved']}")
        print(f"  Resources renamed: {stats['resources_renamed']}")
        if stats['resources_missing'] > 0:
            print(f"  Resources missing: {stats['resources_missing']}")
    if stats['errors'] > 0:
        print(f"  Errors: {stats['errors']}")


def main():
    """Main entry point for the script."""
    parser = argparse.ArgumentParser(
        description='Sort markdown files into year-based subdirectories based on YAML frontmatter'
    )
    parser.add_argument(
        '--path',
        type=Path,
        required=True,
        help='Path to directory containing markdown files'
    )
    parser.add_argument(
        '--resources',
        type=Path,
        help='Path to _resources directory containing media files'
    )
    parser.add_argument(
        '--execute',
        action='store_true',
        help='Actually move files (default is dry-run mode)'
    )

    args = parser.parse_args()

    sort_markdown_files(args.path, args.resources, args.execute)


if __name__ == '__main__':
    main()
