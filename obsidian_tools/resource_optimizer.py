"""Resource optimization and relocation."""

import re
from pathlib import Path

from .resource_analyzer import ResourceAnalyzer
from .markdown_parser import MarkdownParser


class ResourceOptimizer:
    """Handles moving resources to optimal locations."""

    def __init__(self, base_path: Path, execute: bool = False):
        """
        Initialize ResourceOptimizer.

        Args:
            base_path: Base directory containing markdown files and resources
            execute: If True, actually move files. If False, dry-run mode.
        """
        self.base_path = base_path
        self.execute = execute
        self.analyzer = ResourceAnalyzer(base_path)

    def optimize_resources(self) -> None:
        """
        Analyze and move resources to optimal locations.
        """
        print("=" * 60)
        print("RESOURCE OPTIMIZATION")
        print("=" * 60)
        print(f"Mode: {'EXECUTE' if self.execute else 'DRY-RUN (use --execute to actually move files)'}")
        print()

        # Phase 1: Build reference array
        print("Phase 1: Building resource reference array...")
        references = self.analyzer.build_reference_array()
        print(f"Found {len(references)} resource reference(s)")
        print()

        # Phase 2: Detect conflicts
        print("Phase 2: Detecting conflicts...")
        conflicts = self.analyzer.detect_conflicts(references)
        if conflicts:
            print(f"WARNING: Found {len(conflicts)} resource(s) with same name but different content:")
            for resource_name, refs in conflicts.items():
                print(f"  - {resource_name}:")
                for ref in refs:
                    print(f"    Referenced in: {ref.md_file_path}")
                    print(f"    Found at: {ref.resource_actual_path}")
                    print(f"    Hash: {ref.resource_hash[:8] if ref.resource_hash else 'N/A'}...")
            print("  These resources will NOT be moved to avoid conflicts.")
            print()

        # Phase 3: Group by resource and calculate optimal locations
        print("Phase 3: Calculating optimal locations...")
        grouped = self.analyzer.group_by_resource(references)

        # Filter out conflicts
        conflict_paths = set()
        for refs in conflicts.values():
            for ref in refs:
                if ref.resource_actual_path:
                    conflict_paths.add(ref.resource_actual_path)

        moves = []
        stats = {
            'moved': 0,
            'skipped_conflict': 0,
            'skipped_optimal': 0,
            'errors': 0
        }

        for resource_path, md_files in grouped.items():
            # Skip conflicts
            if resource_path in conflict_paths:
                stats['skipped_conflict'] += 1
                continue

            # Calculate optimal location
            ancestor = self.analyzer.find_lowest_common_ancestor(md_files)
            optimal_location = ancestor / "_resources" / resource_path.name

            # Check if already in optimal location
            if resource_path == optimal_location:
                print(f"SKIP (already optimal): {resource_path.name}")
                print(f"  Location: {resource_path.relative_to(self.base_path)}")
                stats['skipped_optimal'] += 1
                continue

            moves.append((resource_path, optimal_location, md_files))
            print(f"{'WILL MOVE' if not self.execute else 'MOVING'}: {resource_path.name}")
            print(f"  From: {resource_path.relative_to(self.base_path)}")
            print(f"  To: {optimal_location.relative_to(self.base_path)}")
            print(f"  Referenced by {len(md_files)} markdown file(s)")

        print()

        # Phase 4: Move resources
        if moves:
            print(f"Phase 4: {'Moving' if self.execute else 'Would move'} resources...")
            for resource_path, optimal_location, md_files in moves:
                success = self._move_resource(resource_path, optimal_location, md_files)
                if success:
                    stats['moved'] += 1
                else:
                    stats['errors'] += 1
            print()

        # Print summary
        self._print_summary(stats)

    def _move_resource(self, source: Path, target: Path, md_files: list[Path]) -> bool:
        """
        Move a resource and update all referencing markdown files.

        Args:
            source: Current path of the resource
            target: Target path for the resource
            md_files: List of markdown files that reference this resource

        Returns:
            True if successful, False otherwise
        """
        resource_name = source.name

        if self.execute:
            try:
                # Create target directory
                target.parent.mkdir(parents=True, exist_ok=True)

                # Move the resource
                source.rename(target)

                # Update all markdown files
                for md_file in md_files:
                    self._update_markdown_link(md_file, resource_name, target)

                return True

            except OSError as e:
                print(f"  ERROR: Failed to move {resource_name}: {e}")
                return False
        else:
            # Dry-run mode
            print(f"  WOULD UPDATE {len(md_files)} markdown file(s)")
            return True

    def _update_markdown_link(self, md_file: Path, resource_name: str, new_resource_path: Path) -> bool:
        """
        Update resource link in markdown file to reflect new location.

        Args:
            md_file: Path to the markdown file
            resource_name: Name of the resource
            new_resource_path: New absolute path to the resource

        Returns:
            True if successful, False otherwise
        """
        try:
            content = md_file.read_text(encoding='utf-8')

            # Calculate relative path from markdown file to resource
            md_dir = md_file.parent
            try:
                relative_path = new_resource_path.relative_to(md_dir)
            except ValueError:
                # If not in same tree, use the path relative to a common ancestor
                relative_path = Path("_resources") / resource_name

            # Convert to forward slashes for markdown
            relative_str = str(relative_path).replace('\\', '/')

            # Update the resource reference
            # Match patterns like ![[_resources/filename]] or ![[../../_resources/filename]]
            old_pattern = re.escape(resource_name)
            pattern = r'(!\[\[)(?:.*?/)?' + old_pattern + r'(\|[^\]]+\]|\]\])'
            replacement = r'\1' + relative_str + r'\2'

            new_content = re.sub(pattern, replacement, content)
            md_file.write_text(new_content, encoding='utf-8')

            return True

        except (OSError, UnicodeDecodeError) as e:
            print(f"  ERROR: Failed to update {md_file.name}: {e}")
            return False

    def _print_summary(self, stats: dict[str, int]) -> None:
        """Print summary statistics."""
        print("=" * 60)
        print("SUMMARY")
        print("=" * 60)
        print(f"  {'Moved' if self.execute else 'Would move'}: {stats['moved']}")
        print(f"  Skipped (already optimal): {stats['skipped_optimal']}")
        if stats['skipped_conflict'] > 0:
            print(f"  Skipped (conflict): {stats['skipped_conflict']}")
        if stats['errors'] > 0:
            print(f"  Errors: {stats['errors']}")
        print("=" * 60)
