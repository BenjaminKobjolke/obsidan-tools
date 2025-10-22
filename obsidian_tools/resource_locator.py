"""Resource file location utilities."""

from pathlib import Path


class ResourceLocator:
    """Handles locating resource files in the filesystem."""

    @staticmethod
    def find_resource(resource_name: str, search_root: Path) -> list[Path]:
        """
        Find all instances of a resource file in the directory tree.

        Args:
            resource_name: Name of the resource file to find
            search_root: Root directory to search from

        Returns:
            List of Path objects pointing to all found instances of the resource
        """
        found_resources = []

        try:
            # Use rglob to recursively search for files matching the name
            for path in search_root.rglob(resource_name):
                if path.is_file():
                    found_resources.append(path)
        except (OSError, PermissionError) as e:
            print(f"Warning: Error searching for {resource_name}: {e}")

        return found_resources

    @staticmethod
    def find_all_resources(resource_names: list[str], search_root: Path) -> dict[str, list[Path]]:
        """
        Find all instances of multiple resource files in the directory tree.

        Args:
            resource_names: List of resource file names to find
            search_root: Root directory to search from

        Returns:
            Dictionary mapping resource name to list of paths where it was found
        """
        results = {}

        for resource_name in resource_names:
            results[resource_name] = ResourceLocator.find_resource(resource_name, search_root)

        return results
