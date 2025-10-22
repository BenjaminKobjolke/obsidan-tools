"""Markdown file parsing and date extraction."""

import re
from pathlib import Path
from datetime import datetime


class MarkdownParser:
    """Handles parsing markdown files and extracting metadata."""

    @staticmethod
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

    @staticmethod
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
            return MarkdownParser.extract_year_from_filename(file_path)

        except (OSError, UnicodeDecodeError) as e:
            print(f"Error reading {file_path}: {e}")
            return None

    @staticmethod
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

    @staticmethod
    def update_resource_link(md_file: Path, old_name: str, new_name: str) -> bool:
        """
        Update a resource link in the markdown file.

        Args:
            md_file: Path to the markdown file
            old_name: Original resource filename
            new_name: New resource filename

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
            md_file.write_text(new_content, encoding='utf-8')

            return True

        except (OSError, UnicodeDecodeError) as e:
            print(f"Error updating {md_file}: {e}")
            return False
