"""Resource file management and moving operations."""

from pathlib import Path
from typing import Literal

from .utils.file_hasher import FileHasher
from .markdown_parser import MarkdownParser


ResourceMoveStatus = Literal['moved', 'renamed', 'missing', 'identical', 'error']


class ResourceManager:
    """Handles moving and managing resource files associated with markdown files."""

    def __init__(self, execute: bool = False):
        """
        Initialize ResourceManager.

        Args:
            execute: If True, actually move files. If False, dry-run mode.
        """
        self.execute = execute
        self.file_hasher = FileHasher()

    @staticmethod
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

    def move_resource_file(
        self,
        source_resource: Path,
        target_resource: Path,
        md_file: Path,
        resource_name: str
    ) -> tuple[bool, str | None, ResourceMoveStatus]:
        """
        Move a resource file, handling conflicts intelligently.

        Args:
            source_resource: Source path of the resource file
            target_resource: Target path for the resource file
            md_file: Path to the markdown file (for updating links if needed)
            resource_name: Original resource filename (for updating links)

        Returns:
            Tuple of (success, new_filename, status) where:
            - success: True if operation completed without errors
            - new_filename: Set if file was renamed, None otherwise
            - status: 'moved', 'renamed', 'missing', 'identical', 'error'
        """
        if not source_resource.exists():
            print(f"  WARN: Resource not found: {source_resource.name}")
            return (True, None, 'missing')  # Continue anyway

        if target_resource.exists():
            # Compare file hashes
            if self.file_hasher.files_are_identical(source_resource, target_resource):
                # Same file, can skip
                print(f"  RESOURCE (identical): {source_resource.name}")
                return (True, None, 'identical')
            else:
                # Different files, need to rename
                unique_target = self.get_unique_filename(target_resource)
                new_filename = unique_target.name

                if self.execute:
                    try:
                        source_resource.rename(unique_target)
                        # Update the markdown file to reference the new name
                        MarkdownParser.update_resource_link(md_file, resource_name, new_filename)
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
            if self.execute:
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

    def move_resources_for_markdown(
        self,
        md_file: Path,
        resource_links: list[str],
        resources_path: Path,
        year_dir: Path
    ) -> dict[str, int]:
        """
        Move all resources associated with a markdown file.

        Args:
            md_file: Path to the markdown file
            resource_links: List of resource file references
            resources_path: Path to the source _resources directory
            year_dir: Target year directory

        Returns:
            Dictionary with statistics: moved, renamed, missing, errors
        """
        stats = {
            'moved': 0,
            'renamed': 0,
            'missing': 0,
            'errors': 0
        }

        if not resource_links:
            return stats

        year_resources_dir = year_dir / "_resources"

        for resource_link in resource_links:
            # Extract just the filename from the _resources/filename path
            resource_filename = Path(resource_link).name
            source_resource = resources_path / resource_filename
            target_resource = year_resources_dir / resource_filename

            success, new_filename, status = self.move_resource_file(
                source_resource, target_resource, md_file, resource_filename
            )

            if success:
                if status == 'moved':
                    stats['moved'] += 1
                elif status == 'renamed':
                    stats['renamed'] += 1
                elif status == 'missing':
                    stats['missing'] += 1
                # 'identical' doesn't increment any counter
            else:
                stats['errors'] += 1

        return stats
