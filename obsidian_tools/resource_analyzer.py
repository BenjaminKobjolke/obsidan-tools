"""Resource usage analysis and conflict detection."""

from dataclasses import dataclass
from pathlib import Path
from collections import defaultdict

from .markdown_parser import MarkdownParser
from .resource_locator import ResourceLocator
from .utils.file_hasher import FileHasher


@dataclass
class ResourceReference:
    """Represents a reference to a resource file from a markdown file."""
    md_file_path: Path
    resource_name: str
    resource_actual_path: Path | None
    resource_hash: str | None


class ResourceAnalyzer:
    """Analyzes resource usage across markdown files."""

    def __init__(self, base_path: Path):
        """
        Initialize ResourceAnalyzer.

        Args:
            base_path: Base directory containing markdown files and resources
        """
        self.base_path = base_path
        self.parser = MarkdownParser()
        self.locator = ResourceLocator()
        self.hasher = FileHasher()

    def build_reference_array(self) -> list[ResourceReference]:
        """
        Build array of all resource references from all markdown files.

        Returns:
            List of ResourceReference objects
        """
        references = []

        # Find all markdown files recursively
        md_files = list(self.base_path.rglob('*.md'))
        print(f"Scanning {len(md_files)} markdown file(s) for resource references...")

        for md_file in md_files:
            # Extract resource links from markdown
            resource_links = self.parser.extract_resource_links(md_file)

            for resource_link in resource_links:
                # Extract just the filename from the _resources/filename path
                resource_name = Path(resource_link).name

                # Find the resource in the filesystem
                found_paths = self.locator.find_resource(resource_name, self.base_path)

                if not found_paths:
                    # Resource not found
                    references.append(ResourceReference(
                        md_file_path=md_file,
                        resource_name=resource_name,
                        resource_actual_path=None,
                        resource_hash=None
                    ))
                    print(f"  WARN: Resource not found: {resource_name} (referenced in {md_file.name})")
                elif len(found_paths) == 1:
                    # Single instance found
                    resource_path = found_paths[0]
                    resource_hash = self.hasher.compute_hash(resource_path)
                    references.append(ResourceReference(
                        md_file_path=md_file,
                        resource_name=resource_name,
                        resource_actual_path=resource_path,
                        resource_hash=resource_hash
                    ))
                else:
                    # Multiple instances found - compute hashes to see if they're identical
                    hashes = [self.hasher.compute_hash(p) for p in found_paths]
                    unique_hashes = set(h for h in hashes if h is not None)

                    if len(unique_hashes) == 1:
                        # All instances are identical, use the first one
                        resource_path = found_paths[0]
                        references.append(ResourceReference(
                            md_file_path=md_file,
                            resource_name=resource_name,
                            resource_actual_path=resource_path,
                            resource_hash=hashes[0]
                        ))
                    else:
                        # Different files with same name - warning
                        print(f"  WARN: Multiple different files found for {resource_name}:")
                        for path, hash_val in zip(found_paths, hashes):
                            print(f"    - {path} (hash: {hash_val[:8] if hash_val else 'N/A'}...)")
                        # Still add reference but mark as conflict
                        references.append(ResourceReference(
                            md_file_path=md_file,
                            resource_name=resource_name,
                            resource_actual_path=found_paths[0],  # Use first found
                            resource_hash='CONFLICT'
                        ))

        return references

    def detect_conflicts(self, references: list[ResourceReference]) -> dict[str, list[ResourceReference]]:
        """
        Detect resources with same filename but different hashes.

        Args:
            references: List of ResourceReference objects

        Returns:
            Dictionary mapping resource name to list of conflicting references
        """
        conflicts = defaultdict(list)

        # Group by resource name
        by_name = defaultdict(list)
        for ref in references:
            if ref.resource_hash and ref.resource_hash != 'CONFLICT':
                by_name[ref.resource_name].append(ref)

        # Check for different hashes
        for resource_name, refs in by_name.items():
            unique_hashes = set(ref.resource_hash for ref in refs if ref.resource_hash)
            if len(unique_hashes) > 1:
                conflicts[resource_name] = refs

        return dict(conflicts)

    def group_by_resource(self, references: list[ResourceReference]) -> dict[Path, list[Path]]:
        """
        Group references by unique resource file (path + hash).

        Args:
            references: List of ResourceReference objects

        Returns:
            Dictionary mapping resource path to list of markdown files that reference it
        """
        grouped = defaultdict(list)

        for ref in references:
            # Skip missing resources and conflicts
            if ref.resource_actual_path is None or ref.resource_hash == 'CONFLICT':
                continue

            grouped[ref.resource_actual_path].append(ref.md_file_path)

        return dict(grouped)

    def find_lowest_common_ancestor(self, paths: list[Path]) -> Path:
        """
        Find the lowest common ancestor directory for a list of paths.

        Args:
            paths: List of Path objects

        Returns:
            Path to the lowest common ancestor directory
        """
        if not paths:
            return self.base_path

        if len(paths) == 1:
            return paths[0].parent

        # Get all parent directories for each path
        all_parents = []
        for path in paths:
            parents = list(path.parents)
            all_parents.append(parents)

        # Find common ancestors
        common_ancestors = set(all_parents[0])
        for parents in all_parents[1:]:
            common_ancestors &= set(parents)

        if not common_ancestors:
            return self.base_path

        # Find the deepest (longest path) common ancestor
        deepest = max(common_ancestors, key=lambda p: len(p.parts))
        return deepest
