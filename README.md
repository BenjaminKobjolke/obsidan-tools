# Obsidian Sorter

A Python tool to organize Obsidian markdown files into year-based subdirectories based on their YAML frontmatter dates. It also handles moving associated resource files (images, videos, etc.) referenced in the markdown files.

## Features

- Sorts markdown files into year-based subdirectories (e.g., `2023/`, `2024/`)
- Extracts year from YAML frontmatter `Created at:` field
- Fallback to YYYYMMDD_ filename pattern if frontmatter is missing
- Moves associated resource files from `_resources/` directory
- Intelligent duplicate handling with file hash comparison
- Automatic renaming of conflicting files
- Updates markdown links when resources are renamed
- Dry-run mode by default to preview changes

## Requirements

- Python 3.10 or higher
- No external dependencies (uses only standard library)

## Installation

```bash
# Clone the repository
git clone https://github.com/BenjaminKobjolke/obsidian-tools.git
cd obsidian-tools

# Run the install script (creates venv and installs dependencies)
install.bat
```

## Project Structure

```
obsidian-tools/
├── obsidian_sorter/           # Main package
│   ├── __init__.py            # Package initialization
│   ├── cli.py                 # Command-line interface
│   ├── file_sorter.py         # Main sorting orchestration
│   ├── markdown_parser.py     # Markdown parsing and date extraction
│   ├── resource_manager.py    # Resource file management
│   └── utils/
│       ├── __init__.py
│       └── file_hasher.py     # File hashing utilities
├── sort_md_by_year.py         # Legacy script (for reference)
├── requirements.txt
└── README.md
```

## Usage

### Basic Usage

Dry-run mode (preview changes without moving files):
```bash
python -m obsidian_sorter.cli --path "C:\path\to\markdown\files"
```

Execute mode (actually move files):
```bash
python -m obsidian_sorter.cli --path "C:\path\to\markdown\files" --execute
```

### With Resources

Move markdown files and their associated resources:
```bash
python -m obsidian_sorter.cli --path "C:\path\to\markdown\files" --resources "C:\path\to\_resources" --execute
```

### Command-line Arguments

- `--path`: (Required) Path to directory containing markdown files
- `--resources`: (Optional) Path to `_resources` directory containing media files
- `--execute`: (Optional) Actually move files (default is dry-run mode)

## How It Works

### Date Extraction

The tool extracts the year from markdown files in the following order:

1. **YAML Frontmatter**: Looks for `Created at: YYYY-MM-DD` in the frontmatter
   ```yaml
   ---
   Created at: 2024-03-15
   ---
   ```

2. **Filename Pattern**: Falls back to YYYYMMDD_ pattern at the start of the filename
   ```
   20240315_my-note.md
   ```

### File Organization

Files are organized into year-based subdirectories:
```
before/
├── 20230115_note1.md
├── 20240315_note2.md
└── _resources/
    ├── image1.png
    └── video1.mp4

after/
├── 2023/
│   ├── 20230115_note1.md
│   └── _resources/
│       └── image1.png
└── 2024/
    ├── 20240315_note2.md
    └── _resources/
        └── video1.mp4
```

### Resource Handling

- Extracts resource links matching `![[_resources/filename]]` pattern
- Moves resources to year-specific `_resources/` subdirectories
- Compares file hashes to detect duplicates
- Renames conflicting files with numeric suffixes (e.g., `image_1.png`)
- Updates markdown links when resources are renamed

## Classes and Modules

### `FileSorter` (file_sorter.py)
Main orchestration class that coordinates the sorting process.

### `MarkdownParser` (markdown_parser.py)
Handles parsing markdown files:
- `extract_year_from_frontmatter()`: Extract year from YAML frontmatter
- `extract_year_from_filename()`: Extract year from filename pattern
- `extract_resource_links()`: Find resource file references
- `update_resource_link()`: Update markdown links

### `ResourceManager` (resource_manager.py)
Manages resource file operations:
- `move_resource_file()`: Move individual resource with conflict handling
- `move_resources_for_markdown()`: Move all resources for a markdown file
- `get_unique_filename()`: Generate unique filenames for conflicts

### `FileHasher` (utils/file_hasher.py)
File hashing utilities:
- `compute_hash()`: Calculate SHA256 hash of a file
- `files_are_identical()`: Compare two files by hash

## Example Output

```
Found 5 markdown file(s)
Resources directory: C:\path\to\_resources
Mode: DRY-RUN (use --execute to actually move files)
------------------------------------------------------------
WOULD MOVE: 20230115_note1.md -> 2023/20230115_note1.md
  WOULD MOVE RESOURCE: image1.png
WOULD MOVE: 20240315_note2.md -> 2024/20240315_note2.md
  WOULD MOVE RESOURCE: video1.mp4
SKIP (no date): readme.md
------------------------------------------------------------
Summary:
  Would move: 2
  Skipped (no date): 1
  Skipped (exists): 0
  Resources moved: 2
```

## License

This script is provided as-is for personal and commercial use.

## Contributing

Feel free to submit issues, fork the repository, and create pull requests for any improvements.
