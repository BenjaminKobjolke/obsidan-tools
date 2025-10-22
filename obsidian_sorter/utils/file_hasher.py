"""File hashing utilities for comparing files."""

import hashlib
from pathlib import Path


class FileHasher:
    """Handles file hashing operations for duplicate detection."""

    @staticmethod
    def compute_hash(file_path: Path, algorithm: str = "sha256") -> str | None:
        """
        Compute hash of a file.

        Args:
            file_path: Path to the file
            algorithm: Hash algorithm to use (default: sha256)

        Returns:
            Hex string of the hash, or None if file cannot be read
        """
        try:
            hash_obj = hashlib.new(algorithm)
            with open(file_path, "rb") as f:
                for byte_block in iter(lambda: f.read(4096), b""):
                    hash_obj.update(byte_block)
            return hash_obj.hexdigest()
        except OSError as e:
            print(f"Error hashing {file_path}: {e}")
            return None

    @staticmethod
    def files_are_identical(file1: Path, file2: Path) -> bool:
        """
        Check if two files are identical by comparing their hashes.

        Args:
            file1: Path to first file
            file2: Path to second file

        Returns:
            True if files are identical, False otherwise
        """
        hash1 = FileHasher.compute_hash(file1)
        hash2 = FileHasher.compute_hash(file2)

        if hash1 is None or hash2 is None:
            return False

        return hash1 == hash2
