"""Main file sorting orchestration."""

from pathlib import Path

from .markdown_parser import MarkdownParser
from .resource_manager import ResourceManager


class FileSorter:
    """Orchestrates the sorting of markdown files into year-based directories."""

    def __init__(self, execute: bool = False):
        """
        Initialize FileSorter.

        Args:
            execute: If True, actually move files. If False, dry-run mode.
        """
        self.execute = execute
        self.parser = MarkdownParser()
        self.resource_manager = ResourceManager(execute=execute)

    def sort_files(self, path: Path, resources_path: Path | None = None) -> None:
        """
        Sort markdown files into year-based subdirectories.

        Args:
            path: Directory containing markdown files
            resources_path: Path to _resources directory (optional)
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

        self._print_header(len(md_files), resources_path)

        stats = self._initialize_stats()

        for md_file in md_files:
            self._process_file(md_file, path, resources_path, stats)

        self._print_summary(stats, resources_path)

    def _print_header(self, file_count: int, resources_path: Path | None) -> None:
        """Print header information."""
        print(f"Found {file_count} markdown file(s)")
        if resources_path:
            print(f"Resources directory: {resources_path}")
        print(f"Mode: {'EXECUTE' if self.execute else 'DRY-RUN (use --execute to actually move files)'}")
        print("-" * 60)

    def _initialize_stats(self) -> dict[str, int]:
        """Initialize statistics dictionary."""
        return {
            'moved': 0,
            'skipped_no_date': 0,
            'skipped_exists': 0,
            'resources_moved': 0,
            'resources_renamed': 0,
            'resources_missing': 0,
            'errors': 0
        }

    def _process_file(
        self,
        md_file: Path,
        base_path: Path,
        resources_path: Path | None,
        stats: dict[str, int]
    ) -> None:
        """
        Process a single markdown file.

        Args:
            md_file: Path to the markdown file
            base_path: Base directory containing markdown files
            resources_path: Path to _resources directory (optional)
            stats: Statistics dictionary to update
        """
        year = self.parser.extract_year_from_frontmatter(md_file)

        if year is None:
            print(f"SKIP (no date): {md_file.name}")
            stats['skipped_no_date'] += 1
            return

        # Create year subdirectory path
        year_dir = base_path / str(year)
        target_path = year_dir / md_file.name

        # Check if target already exists
        if target_path.exists():
            print(f"SKIP (exists): {md_file.name} -> {year}/{md_file.name}")
            stats['skipped_exists'] += 1
            return

        # Extract resource links
        resource_links = []
        if resources_path:
            resource_links = self.parser.extract_resource_links(md_file)

        # Move markdown file
        if not self._move_markdown_file(md_file, year_dir, target_path, year, stats):
            return

        # Handle resources
        if resources_path and resource_links:
            # For dry-run, use the original md_file path; for execute, use the new path
            md_file_for_update = target_path if self.execute else md_file

            resource_stats = self.resource_manager.move_resources_for_markdown(
                md_file_for_update, resource_links, resources_path, year_dir
            )

            stats['resources_moved'] += resource_stats['moved']
            stats['resources_renamed'] += resource_stats['renamed']
            stats['resources_missing'] += resource_stats['missing']
            stats['errors'] += resource_stats['errors']

    def _move_markdown_file(
        self,
        md_file: Path,
        year_dir: Path,
        target_path: Path,
        year: int,
        stats: dict[str, int]
    ) -> bool:
        """
        Move markdown file to year directory.

        Args:
            md_file: Path to the markdown file
            year_dir: Year directory path
            target_path: Target file path
            year: Year number
            stats: Statistics dictionary to update

        Returns:
            True if successful or dry-run, False if error
        """
        action_verb = "MOVED" if self.execute else "WOULD MOVE"
        print(f"{action_verb}: {md_file.name} -> {year}/{md_file.name}")

        if self.execute:
            try:
                year_dir.mkdir(exist_ok=True)
                md_file.rename(target_path)
                stats['moved'] += 1
                return True
            except OSError as e:
                print(f"ERROR moving {md_file.name}: {e}")
                stats['errors'] += 1
                return False
        else:
            stats['moved'] += 1
            return True

    def _print_summary(self, stats: dict[str, int], resources_path: Path | None) -> None:
        """Print summary statistics."""
        print("-" * 60)
        print("Summary:")
        print(f"  {'Moved' if self.execute else 'Would move'}: {stats['moved']}")
        print(f"  Skipped (no date): {stats['skipped_no_date']}")
        print(f"  Skipped (exists): {stats['skipped_exists']}")

        if resources_path:
            print(f"  Resources moved: {stats['resources_moved']}")
            print(f"  Resources renamed: {stats['resources_renamed']}")
            if stats['resources_missing'] > 0:
                print(f"  Resources missing: {stats['resources_missing']}")

        if stats['errors'] > 0:
            print(f"  Errors: {stats['errors']}")
