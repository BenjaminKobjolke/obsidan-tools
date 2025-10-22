#!/usr/bin/env python3
"""Command-line interface for obsidian-sorter."""

import argparse
from pathlib import Path

from .file_sorter import FileSorter


def main():
    """Main entry point for the CLI."""
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

    sorter = FileSorter(execute=args.execute)
    sorter.sort_files(args.path, args.resources)


if __name__ == '__main__':
    main()
