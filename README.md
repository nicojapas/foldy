# FolderSense - AI-Powered Folder Organizer

**A privacy-conscious tool that analyzes folder structures and suggests improvements without reading file contents.**

FolderSense is a tool designed to help users organize their directories in a more logical and efficient manner. It analyzes folder structures and suggests improvements based on naming patterns, content types, and best practices for folder organization.

## Public Repository Status

This repository is now public and available for use, contributions, and feedback. It has been cleaned of any personal data and is ready for community use.

## Key Features

- **Folder Analysis**: Scan a folder and its subfolders to extract structure and naming patterns
- **AI-Based Suggestions**: Use NLP and fuzzy matching to detect inconsistencies, redundant folders, and reorganization opportunities
- **Preview & Confirmation**: Display suggested changes before applying them, allowing you to approve or modify them
- **Privacy First**: No uploading of data, no reading file contents—only folder names and metadata
- **Undo & Logging**: Keep a history of changes with an option to revert to the previous state
- **Loose Files Grouping**: Automatically detect and group loose files in the root directory into appropriate folders

## Privacy Focus

FolderSense is designed with privacy as a priority:
- Runs 100% locally on your machine
- Never reads file contents, only folder names and metadata
- No cloud processing or data upload
- No external API calls

## Installation

1. Clone this repository:
   ```
   git clone https://github.com/yourusername/foldersense.git
   cd foldersense
   ```

2. Install the required dependencies:
   ```
   pip install -r requirements.txt
   ```

3. (Optional) For enhanced NLP features, uncomment the optional dependencies in the requirements.txt file and run:
   ```
   pip install -r requirements.txt
   python -m spacy download en_core_web_sm
   ```

## Usage

### Basic Usage

```
python main.py /path/to/folder
```

### Options

- `--dry-run`: Preview changes without applying them
- `--verbose`: Enable detailed output
- `--undo`: Undo the last operation
- `--explode`: Move all files to the root folder and delete all empty folders

### Example

```
python main.py ~/Documents/Projects --dry-run
```

This will analyze the folder structure in your Projects directory and suggest improvements without making any changes.

### Interactive Commands

When reviewing suggestions, you can use the following commands:
- `y`: Approve the current suggestion
- `n`: Reject the current suggestion
- `q`: Quit the program
- `a`: Approve all remaining suggestions without further prompts
- `r`: Provide a custom name instead of using the suggested name

## How It Works

1. FolderSense scans the folder structure, collecting only folder names and metadata (creation/modification dates)
2. It analyzes the structure using various techniques:
   - String similarity for detecting similar folder names
   - Pattern detection for identifying inconsistent naming conventions
   - Graph analysis for optimizing folder hierarchy
   - File extension analysis for grouping loose files
   - (Optional) NLP for semantic grouping of related folders
3. It presents suggested changes for your approval
4. After confirmation, it applies the approved changes
5. All changes are logged for potential undo operations

## Suggestion Types

FolderSense can suggest several types of improvements:

1. **Merge Similar Folders**: Detect folders with very similar names that might be duplicates
2. **Rename for Consistency**: Identify inconsistent naming patterns and suggest standardization
3. **Create Group**: Suggest grouping related folders into a new parent folder
4. **Relocate**: Suggest moving a folder to a more appropriate location in the hierarchy
5. **Group Loose Files**: Detect files sitting directly in the root directory and group them into appropriate folders

### Loose Files Grouping

The loose files grouping feature works as follows:

- Detects when there are multiple files (5+) sitting directly in the root directory
- Groups files by their extensions (e.g., all .jpg files together)
- For each group:
  - Checks if there's an existing appropriate folder (like "Images" for .jpg files)
  - If a suitable folder exists, suggests moving the files there
  - If no suitable folder exists, suggests creating a new appropriately named folder
- Also handles files with mixed or no extensions by grouping them into a "Miscellaneous_Files" folder

## Undoing Changes

To undo the last operation:

```
python main.py /path/to/folder --undo
```

## Development

### Project Structure

- `main.py`: Entry point for the application
- `src/organizer.py`: Core logic for scanning folders and suggesting changes
- `src/nlp.py`: NLP-based naming convention analysis
- `src/ui.py`: Command-line interface
- `logs/`: Stores logs of changes for undo functionality

### Adding New Features

Contributions are welcome! To add a new suggestion type:

1. Implement the analysis in `organizer.py`
2. Add the suggestion handling in `ui.py`
3. Implement the change application in `organizer.py`

## License

MIT License - See the LICENSE file for details.

## Future Improvements

- GUI interface (PyQt or Electron)
- More advanced semantic analysis
- Customizable naming conventions
- Support for file renaming (while maintaining privacy)
- Smart detection of file types based on content signatures (not content reading) 