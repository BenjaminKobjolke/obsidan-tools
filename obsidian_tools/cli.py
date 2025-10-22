#!/usr/bin/env python3
"""Command-line interface for obsidian-tools."""

import argparse
import sys
from pathlib import Path

from .file_sorter import FileSorter
from .resource_optimizer import ResourceOptimizer


def handle_sort_by_year(args: argparse.Namespace) -> None:
    """
    Handle the sort-by-year mode.

    Args:
        args: Parsed command-line arguments
    """
    sorter = FileSorter(execute=args.execute)
    sorter.sort_files(args.path, args.resources)


def handle_sort_resources(args: argparse.Namespace) -> None:
    """
    Handle the sort-resources mode.

    Args:
        args: Parsed command-line arguments
    """
    optimizer = ResourceOptimizer(base_path=args.path, execute=args.execute)
    optimizer.optimize_resources()


def main():
    """Main entry point for the CLI."""
    parser = argparse.ArgumentParser(
        description='Obsidian Tools - A collection of tools for managing Obsidian markdown files',
        formatter_class=argparse.RawDescriptionHelpFormatter
    )

    parser.add_argument(
        '--mode',
        type=str,
        required=True,
        choices=['sort-by-year', 'sort-resources'],
        help='Operation mode to execute'
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

    # Dispatch to appropriate handler based on mode
    if args.mode == 'sort-by-year':
        handle_sort_by_year(args)
    elif args.mode == 'sort-resources':
        handle_sort_resources(args)
    else:
        print(f"Error: Unknown mode '{args.mode}'")
        sys.exit(1)


if __name__ == '__main__':
    main()
