"""
Core module for folder structure analysis and reorganization.
"""
import os
import json
import datetime
import shutil
import time
from pathlib import Path
import networkx as nx
from difflib import SequenceMatcher
from collections import defaultdict

class FolderOrganizer:
    """
    Main class for analyzing folder structures and suggesting improvements.
    Only processes folder names and metadata, not file contents.
    """
    def __init__(self, root_path, verbose=False):
        self.root_path = os.path.abspath(root_path)
        self.verbose = verbose
        self.folder_structure = {}
        self.log_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'logs')
        
        # Ensure the root path exists and is a directory
        if not os.path.exists(self.root_path):
            raise FileNotFoundError(f"The path {self.root_path} does not exist.")
        if not os.path.isdir(self.root_path):
            raise NotADirectoryError(f"The path {self.root_path} is not a directory.")
        
        # Ensure logs directory exists
        os.makedirs(self.log_path, exist_ok=True)

    def log(self, message):
        """Print verbose messages if enabled"""
        if self.verbose:
            print(message)

    def scan_folder_structure(self):
        """
        Scan the folder structure starting from the root path.
        Only collects folder names and metadata, not file contents.
        """
        self.log(f"Scanning folder structure at {self.root_path}...")
        self.folder_structure = self._scan_directory(self.root_path)
        return self.folder_structure
    
    def _scan_directory(self, directory):
        """Recursively scan a directory and its subdirectories"""
        structure = {
            'path': directory,
            'name': os.path.basename(directory),
            'metadata': {
                'created': self._get_creation_time(directory),
                'modified': self._get_modification_time(directory),
            },
            'subdirectories': [],
            'file_count': 0,
            'files': []  # Store file names (not content)
        }
        
        try:
            with os.scandir(directory) as entries:
                for entry in entries:
                    if entry.is_dir():
                        subdir_info = self._scan_directory(entry.path)
                        structure['subdirectories'].append(subdir_info)
                    else:
                        # Only store file names and metadata, not content
                        structure['file_count'] += 1
                        structure['files'].append({
                            'name': entry.name,
                            'path': entry.path,
                            'extension': os.path.splitext(entry.name)[1].lower() if '.' in entry.name else '',
                            'modified': os.path.getmtime(entry.path)
                        })
        except PermissionError:
            self.log(f"Permission denied: {directory}")
        
        return structure
    
    def _get_creation_time(self, path):
        """Get file creation time in a cross-platform way"""
        if os.name == 'nt':  # Windows
            return os.path.getctime(path)
        else:  # Unix-based systems
            stat = os.stat(path)
            try:
                return stat.st_birthtime  # macOS
            except AttributeError:
                return stat.st_mtime  # Linux doesn't store creation time
    
    def _get_modification_time(self, path):
        """Get file modification time"""
        return os.path.getmtime(path)
    
    def suggest_improvements(self):
        """
        Analyze folder structure and suggest improvements.
        Returns a list of suggested changes.
        """
        self.log("Analyzing folder structure and generating suggestions...")
        
        if not self.folder_structure:
            self.scan_folder_structure()
        
        suggestions = []
        
        # Find similar folder names using Levenshtein distance
        similar_folders = self._find_similar_folders(self.folder_structure)
        for group in similar_folders:
            if len(group) > 1:
                suggestions.append({
                    'type': 'merge_similar_folders',
                    'folders': group,
                    'suggested_name': self._suggest_common_name(group),
                    'reason': f"These folders have similar names and might be duplicates or related content."
                })
        
        # Find inconsistent naming patterns
        inconsistent_naming = self._find_inconsistent_naming(self.folder_structure)
        for pattern, folders in inconsistent_naming.items():
            if len(folders) > 1:
                suggestions.append({
                    'type': 'rename_for_consistency',
                    'pattern': pattern,
                    'folders': folders,
                    'suggested_names': self._suggest_consistent_names(folders, pattern),
                    'reason': f"These folders follow inconsistent naming patterns."
                })
        
        # Find hierarchy improvements
        hierarchy_improvements = self._suggest_hierarchy_improvements()
        suggestions.extend(hierarchy_improvements)
        
        # Find loose files that need grouping
        loose_file_suggestions = self._find_loose_files_to_group()
        suggestions.extend(loose_file_suggestions)
        
        return suggestions
    
    def _find_loose_files_to_group(self):
        """
        Find loose files in the root folder that could be grouped into subfolders.
        This can either suggest grouping into existing folders or creating new folders.
        """
        suggestions = []
        
        # Skip if no folder structure has been scanned
        if not self.folder_structure:
            return suggestions
        
        # Get files directly in the root folder
        root_files = self.folder_structure.get('files', [])
        
        # Skip if there aren't enough files to warrant grouping
        if len(root_files) < 5:  # Threshold can be adjusted
            return suggestions
        
        # Group by file extension
        extension_groups = defaultdict(list)
        for file_info in root_files:
            ext = file_info['extension']
            extension_groups[ext].append(file_info)
        
        # Only consider significant groups
        significant_groups = {ext: files for ext, files in extension_groups.items() 
                             if len(files) >= 3 and ext}  # Only groups with at least 3 files and a non-empty extension
        
        # Generate suggestions for each significant group
        for ext, files in significant_groups.items():
            # Determine if there's an existing appropriate folder
            target_folder = self._find_suitable_folder_for_files(ext, files)
            
            if target_folder:
                # Suggest moving to existing folder
                suggestions.append({
                    'type': 'group_loose_files',
                    'files': files,
                    'target_folder': target_folder,
                    'is_new_folder': False,
                    'reason': f"Found {len(files)} loose {ext} files that could be organized into an existing folder."
                })
            else:
                # Suggest creating a new folder
                folder_name = self._suggest_folder_name_for_extension(ext, files)
                suggestions.append({
                    'type': 'group_loose_files',
                    'files': files,
                    'target_folder': os.path.join(self.root_path, folder_name),
                    'is_new_folder': True,
                    'reason': f"Found {len(files)} loose {ext} files that could be grouped into a new folder."
                })
        
        # If we have many mixed files without extensions or with varied extensions, suggest misc folder
        misc_files = [f for f in root_files if f not in [file for group in significant_groups.values() for file in group]]
        if len(misc_files) >= 5:  # Threshold for misc files
            suggestions.append({
                'type': 'group_loose_files',
                'files': misc_files,
                'target_folder': os.path.join(self.root_path, "Miscellaneous_Files"),
                'is_new_folder': True,
                'reason': f"Found {len(misc_files)} loose files with mixed types that could be grouped together."
            })
        
        return suggestions
    
    def _find_suitable_folder_for_files(self, extension, files):
        """
        Find an appropriate existing folder for files of a given extension.
        Returns the folder path if found, None otherwise.
        """
        # Get all subdirectories from the root
        all_subdirs = self._extract_all_folder_paths(self.folder_structure)[1:]  # Skip root folder
        
        # Look for folders with similar names to the file type
        ext_without_dot = extension[1:] if extension.startswith('.') else extension
        possible_folder_names = [
            ext_without_dot,
            ext_without_dot.capitalize(),
            ext_without_dot.upper(),
            f"{ext_without_dot}_files",
            f"{ext_without_dot.capitalize()}_Files",
            f"{ext_without_dot.upper()}_FILES"
        ]
        
        # Common folder names for specific file types
        common_mappings = {
            '.jpg': ['Images', 'Photos', 'Pictures', 'JPGs'],
            '.jpeg': ['Images', 'Photos', 'Pictures', 'JPEGs'],
            '.png': ['Images', 'Photos', 'Pictures', 'PNGs'],
            '.gif': ['Images', 'Photos', 'Pictures', 'GIFs'],
            '.pdf': ['Documents', 'PDFs'],
            '.doc': ['Documents', 'Word_Docs'],
            '.docx': ['Documents', 'Word_Docs'],
            '.xls': ['Spreadsheets', 'Excel_Files'],
            '.xlsx': ['Spreadsheets', 'Excel_Files'],
            '.ppt': ['Presentations', 'PowerPoint'],
            '.pptx': ['Presentations', 'PowerPoint'],
            '.txt': ['Text_Files', 'Documents', 'Notes'],
            '.csv': ['Data', 'Spreadsheets', 'CSV_Files'],
            '.mp3': ['Music', 'Audio', 'MP3s'],
            '.mp4': ['Videos', 'MP4s'],
            '.mov': ['Videos', 'MOVs'],
            '.zip': ['Archives', 'Compressed', 'ZIPs'],
            '.rar': ['Archives', 'Compressed', 'RARs']
        }
        
        if extension in common_mappings:
            possible_folder_names.extend(common_mappings[extension])
        
        # Check if any of these folders exist
        for folder in all_subdirs:
            folder_name = os.path.basename(folder['path'])
            if folder_name in possible_folder_names:
                return folder['path']
        
        # If no match by name, check if any folder already contains similar files
        for folder in all_subdirs:
            folder_files = []
            self._get_all_files_in_folder(folder, folder_files)
            
            # Check if any files in this folder have the same extension
            folder_extensions = {f['extension'] for f in folder_files}
            if extension in folder_extensions:
                return folder['path']
        
        # No suitable folder found
        return None
    
    def _get_all_files_in_folder(self, folder, result_list):
        """Recursively get all files in a folder and its subfolders"""
        # Add files directly in this folder
        result_list.extend(folder.get('files', []))
        
        # Add files from subfolders
        for subdir in folder.get('subdirectories', []):
            self._get_all_files_in_folder(subdir, result_list)
    
    def _suggest_folder_name_for_extension(self, extension, files):
        """Suggest a folder name based on file extension and file names"""
        ext_without_dot = extension[1:] if extension.startswith('.') else extension
        
        # Common folder names for specific file types
        common_names = {
            '.jpg': 'Images',
            '.jpeg': 'Images',
            '.png': 'Images',
            '.gif': 'Images',
            '.pdf': 'Documents',
            '.doc': 'Documents',
            '.docx': 'Documents',
            '.xls': 'Spreadsheets',
            '.xlsx': 'Spreadsheets',
            '.ppt': 'Presentations',
            '.pptx': 'Presentations',
            '.txt': 'Text_Files',
            '.csv': 'Data',
            '.mp3': 'Music',
            '.mp4': 'Videos',
            '.mov': 'Videos',
            '.zip': 'Archives',
            '.rar': 'Archives'
        }
        
        if extension in common_names:
            return common_names[extension]
        
        # Default to extension name + "_Files"
        return f"{ext_without_dot.capitalize()}_Files"

    def _find_similar_folders(self, folder_info, similarity_threshold=0.8):
        """Find folders with similar names using Levenshtein distance"""
        all_folder_paths = self._extract_all_folder_paths(folder_info)
        
        # Group by similarity
        similar_groups = []
        processed = set()
        
        for i, folder1 in enumerate(all_folder_paths):
            if folder1['path'] in processed:
                continue
                
            current_group = [folder1]
            
            for j, folder2 in enumerate(all_folder_paths):
                if i == j or folder2['path'] in processed:
                    continue
                
                # Calculate similarity based on folder names only
                similarity = SequenceMatcher(None, 
                                           os.path.basename(folder1['path']), 
                                           os.path.basename(folder2['path'])).ratio()
                
                if similarity >= similarity_threshold:
                    current_group.append(folder2)
            
            if len(current_group) > 1:
                similar_groups.append(current_group)
                for folder in current_group:
                    processed.add(folder['path'])
        
        return similar_groups
    
    def _extract_all_folder_paths(self, folder_info):
        """Extract all folder paths from the structure"""
        folders = []
        folders.append({
            'path': folder_info['path'],
            'name': folder_info['name'],
            'metadata': folder_info['metadata']
        })
        
        for subdir in folder_info['subdirectories']:
            folders.extend(self._extract_all_folder_paths(subdir))
        
        return folders
    
    def _suggest_common_name(self, folder_group):
        """Suggest a common name for similar folders"""
        names = [os.path.basename(f['path']) for f in folder_group]
        
        # Find the common prefix
        prefix = os.path.commonprefix(names)
        if len(prefix) > 3:  # Only use prefix if it's substantial
            return prefix.rstrip('_- ') + '_combined'
        
        # Otherwise, use the shortest name
        shortest = min(names, key=len)
        return shortest
    
    def _find_inconsistent_naming(self, folder_info):
        """Find groups of folders with inconsistent naming patterns"""
        all_folders = self._extract_all_folder_paths(folder_info)
        patterns = defaultdict(list)
        
        # Detect common patterns
        for folder in all_folders:
            name = os.path.basename(folder['path'])
            
            # Detect capitalization patterns
            if name.islower():
                patterns['lowercase'].append(folder)
            elif name.isupper():
                patterns['uppercase'].append(folder)
            elif name[0].isupper() and name[1:].islower():
                patterns['capitalized'].append(folder)
            
            # Detect separator patterns
            if '_' in name:
                patterns['underscore_separated'].append(folder)
            elif '-' in name:
                patterns['hyphen_separated'].append(folder)
            elif ' ' in name:
                patterns['space_separated'].append(folder)
            
            # Detect numbered sequence patterns
            if any(c.isdigit() for c in name):
                if any(f"{i:02d}" in name for i in range(1, 100)):
                    patterns['numbered_sequence_padded'].append(folder)
                elif any(str(i) in name for i in range(1, 100)):
                    patterns['numbered_sequence'].append(folder)
        
        # Filter out patterns with less than 2 folders
        return {k: v for k, v in patterns.items() if len(v) > 1}
    
    def _suggest_consistent_names(self, folders, pattern):
        """Suggest consistent names based on detected pattern"""
        names = {}
        for folder in folders:
            original_name = os.path.basename(folder['path'])
            new_name = original_name
            
            if pattern == 'lowercase':
                new_name = original_name.lower()
            elif pattern == 'uppercase':
                new_name = original_name.upper()
            elif pattern == 'capitalized':
                new_name = original_name[0].upper() + original_name[1:].lower()
            elif pattern == 'underscore_separated':
                # Convert other separators to underscore
                new_name = original_name.replace('-', '_').replace(' ', '_')
            elif pattern == 'hyphen_separated':
                new_name = original_name.replace('_', '-').replace(' ', '-')
            elif pattern == 'space_separated':
                new_name = original_name.replace('_', ' ').replace('-', ' ')
            elif pattern == 'numbered_sequence_padded':
                # Find numbers and ensure they're zero-padded
                for i in range(1, 100):
                    if str(i) in new_name and f"{i:02d}" not in new_name:
                        new_name = new_name.replace(str(i), f"{i:02d}")
            
            if new_name != original_name:
                names[folder['path']] = new_name
        
        return names
    
    def _suggest_hierarchy_improvements(self):
        """
        Use graph analysis to suggest optimized folder hierarchy
        """
        suggestions = []
        
        # Build a graph of folder relationships
        G = nx.DiGraph()
        self._build_folder_graph(G, self.folder_structure)
        
        # Detect potential grouping opportunities (folders with similar content/structure)
        potential_groups = self._find_potential_groups(G)
        
        for group in potential_groups:
            if len(group) >= 3:  # Only suggest groupings for 3+ similar folders
                parent_path = os.path.dirname(group[0])
                suggested_name = self._suggest_group_name(group)
                
                suggestions.append({
                    'type': 'create_group',
                    'folders': group,
                    'parent': parent_path,
                    'suggested_name': suggested_name,
                    'reason': f"These {len(group)} folders appear to be related and could be grouped together."
                })
        
        # Detect folders that might better belong in a different parent
        relocations = self._find_relocation_opportunities(G)
        
        for folder, new_parent in relocations:
            suggestions.append({
                'type': 'relocate',
                'folder': folder,
                'suggested_parent': new_parent,
                'reason': f"This folder might be better organized under {os.path.basename(new_parent)}."
            })
        
        return suggestions
    
    def _build_folder_graph(self, graph, folder_info):
        """Build a directed graph representing the folder structure"""
        parent_path = folder_info['path']
        
        for subdir in folder_info['subdirectories']:
            child_path = subdir['path']
            graph.add_edge(parent_path, child_path)
            
            # Add node attributes
            graph.nodes[child_path]['name'] = subdir['name']
            graph.nodes[child_path]['file_count'] = subdir['file_count']
            
            # Process subdirectories recursively
            self._build_folder_graph(graph, subdir)
    
    def _find_potential_groups(self, graph):
        """Find folders that could potentially be grouped together"""
        # Group sibling folders by similarity
        sibling_groups = []
        
        # Get all parent nodes
        parents = [node for node in graph.nodes() if graph.out_degree(node) > 0]
        
        for parent in parents:
            children = list(graph.successors(parent))
            
            if len(children) < 3:
                continue
                
            # Group children by similar names
            similar_children = []
            processed = set()
            
            for i, child1 in enumerate(children):
                if child1 in processed:
                    continue
                    
                current_group = [child1]
                child1_name = os.path.basename(child1).lower()
                
                for child2 in children[i+1:]:
                    if child2 in processed:
                        continue
                        
                    child2_name = os.path.basename(child2).lower()
                    
                    # Check for common patterns in names
                    if (child1_name.startswith(child2_name[:3]) or 
                        child2_name.startswith(child1_name[:3]) or
                        SequenceMatcher(None, child1_name, child2_name).ratio() > 0.5):
                        current_group.append(child2)
                
                if len(current_group) >= 3:
                    similar_children.append(current_group)
                    processed.update(current_group)
            
            sibling_groups.extend(similar_children)
        
        return sibling_groups
    
    def _suggest_group_name(self, group):
        """Suggest a name for a new group folder based on common elements"""
        names = [os.path.basename(path) for path in group]
        prefix = os.path.commonprefix(names)
        
        if len(prefix) > 2:
            return prefix.rstrip('_- ') + "_group"
        else:
            # Extract keywords from folder names
            words = " ".join(names).lower()
            words = ''.join(c if c.isalnum() or c.isspace() else ' ' for c in words)
            word_list = words.split()
            
            # Count word frequencies
            word_count = defaultdict(int)
            for word in word_list:
                if len(word) > 2:  # Ignore short words
                    word_count[word] += 1
                    
            # Use most frequent meaningful word
            if word_count:
                common_word = max(word_count.items(), key=lambda x: x[1])[0]
                return f"{common_word}_group"
            else:
                return "grouped_folders"
    
    def _find_relocation_opportunities(self, graph):
        """Find folders that might be better placed elsewhere in the hierarchy"""
        relocations = []
        
        # For each folder, see if there's a better parent based on similarity
        for node in graph.nodes():
            if graph.in_degree(node) == 0:  # Skip root node
                continue
                
            current_parent = list(graph.predecessors(node))[0]
            node_name = os.path.basename(node).lower()
            
            # Find potential better parents
            best_match = None
            best_score = 0.3  # Minimum threshold
            
            for potential_parent in graph.nodes():
                if potential_parent == current_parent or potential_parent == node:
                    continue
                    
                parent_name = os.path.basename(potential_parent).lower()
                score = SequenceMatcher(None, node_name, parent_name).ratio()
                
                # Check if node name contains parent name or vice versa
                if node_name in parent_name or parent_name in node_name:
                    score += 0.2
                
                if score > best_score:
                    best_score = score
                    best_match = potential_parent
            
            if best_match:
                relocations.append((node, best_match))
        
        return relocations
    
    def apply_changes(self, approved_suggestions):
        """
        Apply the approved suggestions to the folder structure.
        Records changes to the log for potential undo.
        """
        timestamp = time.strftime("%Y%m%d_%H%M%S")
        log_file = os.path.join(self.log_path, f"changes_{timestamp}.json")
        change_log = {
            'timestamp': timestamp,
            'root_path': self.root_path,
            'changes': []
        }
        
        try:
            for suggestion in approved_suggestions:
                change_record = {'suggestion': suggestion, 'status': 'completed'}
                
                if suggestion['type'] == 'merge_similar_folders':
                    target_path = os.path.join(
                        os.path.dirname(suggestion['folders'][0]['path']),
                        suggestion['suggested_name']
                    )
                    
                    # Create target directory if it doesn't exist
                    os.makedirs(target_path, exist_ok=True)
                    
                    # Move contents of each folder to target folder
                    for folder in suggestion['folders']:
                        self._move_folder_contents(folder['path'], target_path)
                        if os.path.exists(folder['path']) and folder['path'] != target_path:
                            shutil.rmtree(folder['path'])
                    
                    change_record['result'] = {'new_folder': target_path}
                
                elif suggestion['type'] == 'rename_for_consistency':
                    changes = {}
                    for path, new_name in suggestion['suggested_names'].items():
                        parent_dir = os.path.dirname(path)
                        new_path = os.path.join(parent_dir, new_name)
                        
                        if os.path.exists(path) and not os.path.exists(new_path):
                            os.rename(path, new_path)
                            changes[path] = new_path
                    
                    change_record['result'] = {'renamed': changes}
                
                elif suggestion['type'] == 'create_group':
                    target_path = os.path.join(
                        suggestion['parent'],
                        suggestion['suggested_name']
                    )
                    
                    # Create target directory if it doesn't exist
                    os.makedirs(target_path, exist_ok=True)
                    
                    # Move each folder under the group
                    moved = []
                    for folder_path in suggestion['folders']:
                        folder_name = os.path.basename(folder_path)
                        new_path = os.path.join(target_path, folder_name)
                        
                        if os.path.exists(folder_path) and not os.path.exists(new_path):
                            shutil.move(folder_path, new_path)
                            moved.append({'from': folder_path, 'to': new_path})
                    
                    change_record['result'] = {'moved': moved}
                
                elif suggestion['type'] == 'relocate':
                    folder_path = suggestion['folder']
                    folder_name = os.path.basename(folder_path)
                    new_parent = suggestion['suggested_parent']
                    new_path = os.path.join(new_parent, folder_name)
                    
                    if os.path.exists(folder_path) and not os.path.exists(new_path):
                        shutil.move(folder_path, new_path)
                        change_record['result'] = {
                            'from': folder_path,
                            'to': new_path
                        }
                
                elif suggestion['type'] == 'group_loose_files':
                    target_folder = suggestion['target_folder']
                    is_new_folder = suggestion['is_new_folder']
                    files = suggestion['files']
                    
                    # Create target folder if it's new
                    if is_new_folder:
                        os.makedirs(target_folder, exist_ok=True)
                    
                    # Move files to target folder
                    moved_files = []
                    for file_info in files:
                        src_path = file_info['path']
                        filename = os.path.basename(src_path)
                        dst_path = os.path.join(target_folder, filename)
                        
                        # Handle file conflicts
                        if os.path.exists(dst_path):
                            # Append timestamp to avoid overwrite
                            base, ext = os.path.splitext(dst_path)
                            timestamp = time.strftime("_%Y%m%d_%H%M%S")
                            dst_path = f"{base}{timestamp}{ext}"
                        
                        # Perform the move
                        if os.path.exists(src_path):
                            shutil.move(src_path, dst_path)
                            moved_files.append({'from': src_path, 'to': dst_path})
                    
                    change_record['result'] = {
                        'target_folder': target_folder,
                        'is_new_folder': is_new_folder,
                        'moved_files': moved_files
                    }
                
                change_log['changes'].append(change_record)
            
            # Write change log to file
            with open(log_file, 'w') as f:
                json.dump(change_log, f, indent=2)
            
            # Rescan the folder structure to update the internal state
            self.scan_folder_structure()
            
            return True
        
        except Exception as e:
            self.log(f"Error applying changes: {e}")
            return False
    
    def _move_folder_contents(self, source, destination):
        """Move all contents from source to destination folder"""
        try:
            with os.scandir(source) as entries:
                for entry in entries:
                    src_path = entry.path
                    dst_path = os.path.join(destination, entry.name)
                    
                    if entry.is_dir():
                        if os.path.exists(dst_path):
                            # If destination exists, recursively merge
                            self._move_folder_contents(src_path, dst_path)
                        else:
                            # If destination doesn't exist, move the whole directory
                            shutil.move(src_path, dst_path)
                    else:
                        # Handle file conflicts
                        if os.path.exists(dst_path):
                            # Append timestamp to avoid overwrite
                            base, ext = os.path.splitext(dst_path)
                            timestamp = time.strftime("_%Y%m%d_%H%M%S")
                            dst_path = f"{base}{timestamp}{ext}"
                        
                        shutil.move(src_path, dst_path)
        
        except Exception as e:
            self.log(f"Error moving contents: {e}")
            raise
    
    def undo_last_change(self):
        """
        Undo the most recent change by using the logs.
        Returns True if successful, False otherwise.
        """
        try:
            # Find the most recent log file
            log_files = sorted([f for f in os.listdir(self.log_path) 
                            if f.startswith('changes_')])
            
            if not log_files:
                self.log("No change logs found to undo.")
                return False
            
            latest_log = os.path.join(self.log_path, log_files[-1])
            
            with open(latest_log, 'r') as f:
                change_log = json.load(f)
            
            # Process changes in reverse order
            for change in reversed(change_log['changes']):
                suggestion = change['suggestion']
                
                if suggestion['type'] == 'merge_similar_folders':
                    if 'result' in change and 'new_folder' in change['result']:
                        # Restore original folders and move contents back
                        new_folder = change['result']['new_folder']
                        
                        for folder in suggestion['folders']:
                            original_path = folder['path']
                            os.makedirs(original_path, exist_ok=True)
                            self._move_folder_contents(new_folder, original_path)
                        
                        # Remove the merged folder if empty
                        if os.path.exists(new_folder) and not os.listdir(new_folder):
                            os.rmdir(new_folder)
                
                elif suggestion['type'] == 'rename_for_consistency':
                    if 'result' in change and 'renamed' in change['result']:
                        # Rename back to original names
                        for original_path, new_path in change['result']['renamed'].items():
                            if os.path.exists(new_path):
                                os.rename(new_path, original_path)
                
                elif suggestion['type'] == 'create_group':
                    if 'result' in change and 'moved' in change['result']:
                        # Move folders back to original locations
                        for move in change['result']['moved']:
                            if os.path.exists(move['to']):
                                os.makedirs(os.path.dirname(move['from']), exist_ok=True)
                                shutil.move(move['to'], move['from'])
                        
                        # Remove the group folder if empty
                        group_path = os.path.join(
                            suggestion['parent'],
                            suggestion['suggested_name']
                        )
                        if os.path.exists(group_path) and not os.listdir(group_path):
                            os.rmdir(group_path)
                
                elif suggestion['type'] == 'relocate':
                    if 'result' in change:
                        orig_path = change['result']['from']
                        new_path = change['result']['to']
                        
                        if os.path.exists(new_path):
                            os.makedirs(os.path.dirname(orig_path), exist_ok=True)
                            shutil.move(new_path, orig_path)
                
                elif suggestion['type'] == 'group_loose_files':
                    if 'result' in change and 'moved_files' in change['result']:
                        # Move files back to original locations
                        for move in change['result']['moved_files']:
                            if os.path.exists(move['to']):
                                shutil.move(move['to'], move['from'])
                        
                        # Remove the target folder if it was newly created and is empty
                        if change['result']['is_new_folder']:
                            target_folder = change['result']['target_folder']
                            if os.path.exists(target_folder) and not os.listdir(target_folder):
                                os.rmdir(target_folder)
            
            # Remove the log file after successful undo
            os.remove(latest_log)
            
            # Rescan the folder structure to update the internal state
            self.scan_folder_structure()
            
            return True
            
        except Exception as e:
            self.log(f"Error undoing changes: {e}")
            return False

    def explode_folder_structure(self):
        """
        Move all files from all subfolders to the root directory and delete all empty folders.
        This effectively flattens the entire folder structure.
        
        Returns:
            bool: True if successful, False otherwise
        """
        timestamp = time.strftime("%Y%m%d_%H%M%S")
        log_file = os.path.join(self.log_path, f"explode_{timestamp}.json")
        change_log = {
            'timestamp': timestamp,
            'root_path': self.root_path,
            'type': 'explode',
            'moved_files': []
        }
        
        try:
            self.log(f"Exploding folder structure at {self.root_path}...")
            
            # First, ensure we have the latest folder structure
            if not self.folder_structure:
                self.scan_folder_structure()
            
            # Collect all files from all subdirectories
            all_files = []
            self._collect_all_files(self.folder_structure, all_files)
            
            # Move all files to the root directory
            for file_info in all_files:
                src_path = file_info['path']
                filename = os.path.basename(src_path)
                dst_path = os.path.join(self.root_path, filename)
                
                # Skip if the file is already in the root directory
                if os.path.dirname(src_path) == self.root_path:
                    continue
                
                # Handle file name conflicts
                if os.path.exists(dst_path):
                    base, ext = os.path.splitext(filename)
                    counter = 1
                    while os.path.exists(dst_path):
                        dst_path = os.path.join(self.root_path, f"{base}_{counter}{ext}")
                        counter += 1
                
                # Move the file
                shutil.move(src_path, dst_path)
                change_log['moved_files'].append({
                    'from': src_path,
                    'to': dst_path
                })
                self.log(f"Moved: {src_path} -> {dst_path}")
            
            # Delete all empty directories (work from deepest to shallowest)
            deleted_dirs = []
            for root, dirs, files in os.walk(self.root_path, topdown=False):
                # Skip the root directory itself
                if root == self.root_path:
                    continue
                
                # Check if the directory is empty (no files or subdirectories)
                if not files and not dirs:
                    self.log(f"Deleting empty directory: {root}")
                    os.rmdir(root)
                    deleted_dirs.append(root)
            
            change_log['deleted_dirs'] = deleted_dirs
            
            # Write change log to file
            with open(log_file, 'w') as f:
                json.dump(change_log, f, indent=2)
            
            # Rescan the folder structure to update the internal state
            self.scan_folder_structure()
            
            return True
            
        except Exception as e:
            self.log(f"Error exploding folder structure: {e}")
            return False
    
    def _collect_all_files(self, folder_info, result_list):
        """
        Recursively collect all files from a folder and its subfolders.
        
        Args:
            folder_info: Dictionary with folder information
            result_list: List to store file information
        """
        # Add files directly in this folder
        for file_info in folder_info.get('files', []):
            result_list.append(file_info)
        
        # Add files from subdirectories
        for subdir in folder_info.get('subdirectories', []):
            self._collect_all_files(subdir, result_list)

    def _load_extension_metadata(self):
        """
        Load extension metadata from JSON file.
        This helps categorize files based on extensions.
        """
        file_types = {
            # Documents
            'document': ['.doc', '.docx', '.odt', '.pdf', '.rtf', '.tex', '.txt', '.md', '.csv'],
            
            # Spreadsheets
            'spreadsheet': ['.xls', '.xlsx', '.ods', '.xlsm'],
            
            # Presentations
            'presentation': ['.ppt', '.pptx', '.odp', '.key'],
            
            # Images
            'image': ['.jpg', '.jpeg', '.png', '.gif', '.bmp', '.tiff', '.svg', '.webp', '.ico', '.heic', '.heif'],
            
            # Audio
            'audio': ['.mp3', '.wav', '.aac', '.ogg', '.flac', '.m4a', '.wma'],
            
            # Video
            'video': ['.mp4', '.avi', '.mkv', '.mov', '.wmv', '.flv', '.webm', '.m4v', '.mpg', '.mpeg'],
            
            # Archives
            'archive': ['.zip', '.rar', '.7z', '.tar', '.gz', '.bz2', '.xz', '.iso'],
            
            # Code
            'code': ['.py', '.java', '.js', '.html', '.css', '.php', '.c', '.cpp', '.h', '.cs', '.go', '.rb', '.pl', '.swift', '.tsx', '.jsx'],
            
            # Data
            'data': ['.json', '.xml', '.yaml', '.yml', '.sql', '.db', '.sqlite'],
            
            # Executable
            'executable': ['.exe', '.msi', '.app', '.bat', '.sh', '.cmd', '.ps1'],
            
            # Fonts
            'font': ['.ttf', '.otf', '.woff', '.woff2', '.eot'],
        }
        
        return file_types 