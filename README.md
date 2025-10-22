# Markdown File Organizer by Year

A Python script that automatically organizes markdown files into year-based subdirectories based on their creation date. Designed for Obsidian notes but works with any markdown files.

## Features

- **Automatic year extraction** from YAML frontmatter `Created at` field
- **Fallback to filename parsing** for files with `YYYYMMDD_` date prefix
- **Resource file handling** - Automatically moves associated media files (images, videos, zip files, etc.)
- **Intelligent conflict resolution** using SHA256 hashing
- **Dry-run mode** by default to preview changes before executing
- **Cross-platform** support (Windows, macOS, Linux)

## Requirements

- Python 3.10 or higher
- No external dependencies (uses only standard library)

## Installation

1. Clone or download this repository
2. Ensure Python 3.10+ is installed:
   ```bash
   python --version
   ```

## Usage

```bash
python sort_md_by_year.py --path <path_to_notes> [--resources <path_to_resources>] [--execute]
```

### Arguments

- `--path` (required): Directory containing markdown files to organize
- `--resources` (optional): Path to `_resources` directory containing media files
- `--execute` (optional): Actually move files (default is dry-run mode)

## Examples

### Preview what would be organized (dry-run)
```bash
python sort_md_by_year.py --path "C:\Users\YourName\Documents\Notes"
```

### Preview with resource files
```bash
python sort_md_by_year.py --path "C:\Users\YourName\Documents\Notes" --resources "C:\Users\YourName\Documents\Notes\_resources"
```

### Actually organize files
```bash
python sort_md_by_year.py --path "C:\Users\YourName\Documents\Notes" --resources "C:\Users\YourName\Documents\Notes\_resources" --execute
```

## How It Works

### Date Extraction Priority

1. **Primary**: Reads YAML frontmatter for `Created at` field
   ```yaml
   ---
   Created at: 2020-07-21 13:38:21
   Last updated at: 2020-07-21 13:38:21
   Author: Benjamin Kobjolke <b.kobjolke@xida.de>
   ---
   ```

2. **Fallback**: Extracts date from filename if it starts with `YYYYMMDD_`
   ```
   20250912_meeting_notes.md → Year: 2025
   ```

### File Organization

```
Before:
├── note1.md (Created: 2020)
├── note2.md (Created: 2021)
├── 20220315_report.md
└── _resources/
    ├── video.mp4
    └── document.zip

After:
├── 2020/
│   ├── note1.md
│   └── _resources/
│       └── video.mp4
├── 2021/
│   └── note2.md
└── 2022/
    ├── 20220315_report.md
    └── _resources/
        └── document.zip
```

### Resource File Handling

The script automatically detects and moves resource files referenced in your markdown:

- Embedded resources: `![[_resources/image.png]]`
- Linked resources: `[[_resources/file.zip|file.zip]]`

Resources are moved to `<year>/_resources/` alongside their markdown files.

## Edge Cases

### Conflict Resolution

**Markdown files**: If a file with the same name already exists in the target year directory, the file is skipped with a warning.

**Resource files**:
- If target resource exists with **identical content** (SHA256 hash match): File is skipped
- If target resource exists with **different content**: New file is renamed (e.g., `video_1.mp4`) and the markdown link is automatically updated

### Missing Resources

If a markdown file references a resource that doesn't exist, a warning is displayed but the markdown file is still moved.

### Files Without Dates

Files without YAML frontmatter or filename date patterns are skipped.

## Output Example

```
Found 1204 markdown file(s)
Resources directory: E:\Notes\_resources
Mode: EXECUTE
------------------------------------------------------------
MOVED: project_notes.md -> 2020/project_notes.md
  RESOURCE: video.mp4
  RESOURCE: diagram.png
MOVED: meeting_minutes.md -> 2021/meeting_minutes.md
  RESOURCE (identical): shared_logo.png
SKIP (no date): README.md
------------------------------------------------------------
Summary:
  Moved: 1202
  Skipped (no date): 2
  Skipped (exists): 0
  Resources moved: 1850
  Resources renamed: 5
  Resources missing: 3
```

## Supported File Types

All file types referenced in `_resources/` are supported:
- Images (`.png`, `.jpg`, `.gif`, etc.)
- Videos (`.mp4`, `.mov`, `.avi`, etc.)
- Documents (`.pdf`, `.docx`, etc.)
- Archives (`.zip`, `.tar.gz`, etc.)
- Any other file type

## License

This script is provided as-is for personal and commercial use.

## Contributing

Feel free to submit issues, fork the repository, and create pull requests for any improvements.
