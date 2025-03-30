"""
User interface module for the folder organizer.
Provides a command-line interface for displaying suggestions
and getting user confirmation.
"""
import os
import sys
from tabulate import tabulate
from colorama import init, Fore, Style
from collections import defaultdict

# Initialize colorama for cross-platform colored terminal output
init()

class CommandLineInterface:
    """
    Command-line interface for the FolderSense organizer.
    Displays suggestions and gets user confirmation.
    """
    def __init__(self, organizer):
        self.organizer = organizer
    
    def display_suggestions(self, suggestions):
        """
        Display the suggested folder changes and ask for confirmation.
        
        Args:
            suggestions: List of suggestion dictionaries from the organizer
        
        Returns:
            Boolean indicating whether the user approved the suggestions
        """
        if not suggestions:
            print(f"{Fore.YELLOW}No organization suggestions found for this folder structure.{Style.RESET_ALL}")
            return False
        
        print(f"\n{Fore.CYAN}===== FolderSense: Suggested Improvements ====={Style.RESET_ALL}\n")
        print(f"Analyzing folder structure at: {Fore.GREEN}{self.organizer.root_path}{Style.RESET_ALL}\n")
        
        # Display each type of suggestion
        suggestion_by_type = self._group_suggestions_by_type(suggestions)
        approved_suggestions = []
        approve_all = False
        
        for suggestion_type, suggestion_group in suggestion_by_type.items():
            print(f"\n{Fore.CYAN}## {self._format_suggestion_type(suggestion_type)} ({len(suggestion_group)}){Style.RESET_ALL}")
            
            handler_name = f"_display_{suggestion_type}_suggestions"
            if hasattr(self, handler_name):
                handler = getattr(self, handler_name)
                for i, suggestion in enumerate(suggestion_group):
                    # Skip individual confirmation if approve_all is True
                    if approve_all:
                        approved_suggestions.append(suggestion)
                        continue
                    
                    print(f"\n{Fore.WHITE}Suggestion {i+1}/{len(suggestion_group)}:{Style.RESET_ALL}")
                    result = handler(suggestion)
                    
                    # Check if the user wants to approve all
                    if result == 'approve_all':
                        approve_all = True
                        approved_suggestions.append(suggestion)
                        # Add all remaining suggestions of this type
                        approved_suggestions.extend(suggestion_group[i+1:])
                        # Break out of the loop for this suggestion type
                        break
                    elif result is True or isinstance(result, dict):
                        # If it's a modified suggestion (due to rename), add that
                        if isinstance(result, dict):
                            approved_suggestions.append(result)
                        else:
                            approved_suggestions.append(suggestion)
            else:
                print(f"{Fore.YELLOW}No display handler for suggestion type: {suggestion_type}{Style.RESET_ALL}")
        
        # Summary and final confirmation
        if approved_suggestions:
            print(f"\n{Fore.CYAN}===== Summary of Approved Changes ====={Style.RESET_ALL}")
            print(f"You approved {Fore.GREEN}{len(approved_suggestions)}{Style.RESET_ALL} out of {len(suggestions)} suggestions.")
            
            confirm = input(f"\n{Fore.YELLOW}Apply all approved changes? (y/n): {Style.RESET_ALL}").lower().strip()
            if confirm == 'y':
                return approved_suggestions
        else:
            print(f"\n{Fore.YELLOW}No suggestions were approved.{Style.RESET_ALL}")
        
        return approved_suggestions if approved_suggestions and input(f"\n{Fore.YELLOW}Are you sure you want to proceed with these changes? (y/n): {Style.RESET_ALL}").lower().strip() == 'y' else []
    
    def _group_suggestions_by_type(self, suggestions):
        """Group suggestions by their type"""
        grouped = {}
        for suggestion in suggestions:
            suggestion_type = suggestion['type']
            if suggestion_type not in grouped:
                grouped[suggestion_type] = []
            grouped[suggestion_type].append(suggestion)
        return grouped
    
    def _format_suggestion_type(self, suggestion_type):
        """Format suggestion type as a readable string"""
        return suggestion_type.replace('_', ' ').title()
    
    def _display_merge_similar_folders_suggestions(self, suggestion):
        """Display suggestion to merge similar folders"""
        folders = suggestion['folders']
        folder_paths = [os.path.basename(f['path']) for f in folders]
        suggested_name = suggestion['suggested_name']
        reason = suggestion['reason']
        
        print(f"{Fore.YELLOW}Suggestion:{Style.RESET_ALL} Merge similar folders")
        print(f"{Fore.YELLOW}Reason:{Style.RESET_ALL} {reason}")
        print(f"\n{Fore.YELLOW}Folders to merge:{Style.RESET_ALL}")
        
        for i, folder in enumerate(folder_paths):
            print(f"  {i+1}. {folder}")
        
        print(f"\n{Fore.YELLOW}Suggested new folder name:{Style.RESET_ALL} {suggested_name}")
        
        result = self._get_user_approval()
        
        # Handle renaming if needed
        if isinstance(result, dict) and 'custom_name' in result:
            # Create a modified copy of the suggestion with the custom name
            modified_suggestion = suggestion.copy()
            modified_suggestion['suggested_name'] = result['custom_name']
            return modified_suggestion
        
        return result
    
    def _display_rename_for_consistency_suggestions(self, suggestion):
        """Display suggestion to rename folders for consistency"""
        pattern = suggestion['pattern']
        folders = suggestion['folders']
        suggested_names = suggestion['suggested_names']
        reason = suggestion['reason']
        
        print(f"{Fore.YELLOW}Suggestion:{Style.RESET_ALL} Rename folders for consistency")
        print(f"{Fore.YELLOW}Pattern type:{Style.RESET_ALL} {pattern}")
        print(f"{Fore.YELLOW}Reason:{Style.RESET_ALL} {reason}")
        
        # Display rename suggestions
        headers = ["Current Name", "Suggested Name"]
        rows = []
        
        for folder in folders:
            folder_path = folder['path']
            folder_name = os.path.basename(folder_path)
            new_name = suggested_names.get(folder_path, folder_name)
            
            if folder_name != new_name:
                rows.append([folder_name, new_name])
        
        if rows:
            print("\n" + tabulate(rows, headers=headers, tablefmt="pipe"))
        else:
            print(f"\n{Fore.YELLOW}No specific renaming suggestions for this pattern.{Style.RESET_ALL}")
            return False
        
        result = self._get_user_approval()
        
        # For rename_for_consistency, we don't support custom naming through the simple interface
        # as it would require handling multiple folders - we'll just return the result as is
        return result
    
    def _display_create_group_suggestions(self, suggestion):
        """Display suggestion to create a new group folder"""
        folders = suggestion['folders']
        suggested_name = suggestion['suggested_name']
        parent = os.path.basename(suggestion['parent'])
        reason = suggestion['reason']
        
        print(f"{Fore.YELLOW}Suggestion:{Style.RESET_ALL} Create a new group folder")
        print(f"{Fore.YELLOW}Reason:{Style.RESET_ALL} {reason}")
        print(f"{Fore.YELLOW}Parent folder:{Style.RESET_ALL} {parent}")
        print(f"{Fore.YELLOW}Suggested group name:{Style.RESET_ALL} {suggested_name}")
        
        print(f"\n{Fore.YELLOW}Folders to group:{Style.RESET_ALL}")
        for i, folder in enumerate(folders):
            print(f"  {i+1}. {os.path.basename(folder)}")
        
        result = self._get_user_approval()
        
        # Handle renaming if needed
        if isinstance(result, dict) and 'custom_name' in result:
            # Create a modified copy of the suggestion with the custom name
            modified_suggestion = suggestion.copy()
            modified_suggestion['suggested_name'] = result['custom_name']
            return modified_suggestion
        
        return result
    
    def _display_relocate_suggestions(self, suggestion):
        """Display suggestion to relocate a folder"""
        folder = os.path.basename(suggestion['folder'])
        suggested_parent = os.path.basename(suggestion['suggested_parent'])
        reason = suggestion['reason']
        
        print(f"{Fore.YELLOW}Suggestion:{Style.RESET_ALL} Relocate folder")
        print(f"{Fore.YELLOW}Reason:{Style.RESET_ALL} {reason}")
        print(f"{Fore.YELLOW}Folder to move:{Style.RESET_ALL} {folder}")
        print(f"{Fore.YELLOW}Suggested new parent:{Style.RESET_ALL} {suggested_parent}")
        
        # For relocate, we don't support custom naming as it's about relocating, not renaming
        return self._get_user_approval()
    
    def _display_group_loose_files_suggestions(self, suggestion):
        """Display suggestion to group loose files into a folder"""
        files = suggestion['files']
        target_folder = suggestion['target_folder']
        is_new_folder = suggestion['is_new_folder']
        reason = suggestion['reason']
        
        print(f"{Fore.YELLOW}Suggestion:{Style.RESET_ALL} Group loose files into a folder")
        print(f"{Fore.YELLOW}Reason:{Style.RESET_ALL} {reason}")
        
        if is_new_folder:
            print(f"{Fore.YELLOW}Action:{Style.RESET_ALL} Create a new folder: {Fore.GREEN}{os.path.basename(target_folder)}{Style.RESET_ALL}")
        else:
            print(f"{Fore.YELLOW}Action:{Style.RESET_ALL} Move files to existing folder: {Fore.GREEN}{os.path.basename(target_folder)}{Style.RESET_ALL}")
        
        # Group files by extension for cleaner display
        extensions = defaultdict(list)
        for file_info in files:
            ext = file_info['extension'] if file_info['extension'] else '(no extension)'
            extensions[ext].append(file_info['name'])
        
        print(f"\n{Fore.YELLOW}Files to move ({len(files)} total):{Style.RESET_ALL}")
        
        # If there are too many files, show a summary
        if len(files) > 10:
            for ext, file_list in extensions.items():
                print(f"  {Fore.CYAN}{ext}:{Style.RESET_ALL} {len(file_list)} files")
            
            # Show a few examples
            print(f"\n{Fore.YELLOW}Examples:{Style.RESET_ALL}")
            for i, file_info in enumerate(files[:5]):
                print(f"  {i+1}. {file_info['name']}")
            
            if len(files) > 5:
                print(f"  ... and {len(files) - 5} more files")
        else:
            # If there are only a few files, show them all
            for i, file_info in enumerate(files):
                print(f"  {i+1}. {file_info['name']}")
        
        result = self._get_user_approval()
        
        # Handle renaming if needed (only for new folders)
        if isinstance(result, dict) and 'custom_name' in result and is_new_folder:
            # Create a modified copy of the suggestion with the custom folder name
            modified_suggestion = suggestion.copy()
            parent_dir = os.path.dirname(target_folder)
            modified_suggestion['target_folder'] = os.path.join(parent_dir, result['custom_name'])
            return modified_suggestion
        
        return result
    
    def _get_user_approval(self):
        """Ask the user for approval of a suggestion"""
        choice = input(f"\n{Fore.GREEN}Approve this suggestion? (y/n/q to quit/a to approve all/r to rename): {Style.RESET_ALL}").lower().strip()
        
        if choice == 'q':
            print(f"\n{Fore.YELLOW}Operation cancelled by user.{Style.RESET_ALL}")
            sys.exit(0)
        elif choice == 'a':
            print(f"\n{Fore.GREEN}Approving all remaining suggestions.{Style.RESET_ALL}")
            return 'approve_all'
        elif choice == 'r':
            return self._handle_rename_option()
        
        return choice == 'y'
    
    def _handle_rename_option(self):
        """Handle the rename option by asking for a new name"""
        new_name = input(f"\n{Fore.YELLOW}Enter new name: {Style.RESET_ALL}").strip()
        
        if not new_name:
            print(f"{Fore.RED}Invalid name. Using the suggested name instead.{Style.RESET_ALL}")
            return True
        
        # Create a copy of the current suggestion with the modified name
        # This is a generic handler, specific suggestion types will need to
        # implement their own handling in their respective display methods
        return {'custom_name': new_name, 'use_custom_name': True}
    
    def display_before_after(self, before_structure, after_structure):
        """
        Display a before/after comparison of the folder structure.
        
        Args:
            before_structure: Dictionary representing the folder structure before changes
            after_structure: Dictionary representing the folder structure after changes
        """
        print(f"\n{Fore.CYAN}===== Before/After Comparison ====={Style.RESET_ALL}\n")
        
        before_tree = self._format_folder_tree(before_structure)
        after_tree = self._format_folder_tree(after_structure)
        
        # Split the console width for side-by-side display
        console_width = self._get_console_width()
        half_width = max(40, console_width // 2 - 4)
        
        # Format trees for display
        before_lines = before_tree.split('\n')
        after_lines = after_tree.split('\n')
        
        # Prepare headers
        before_header = f"{Fore.YELLOW}BEFORE{Style.RESET_ALL}".ljust(half_width)
        after_header = f"{Fore.YELLOW}AFTER{Style.RESET_ALL}".ljust(half_width)
        
        print(f"{before_header} | {after_header}")
        print(f"{'-' * half_width} | {'-' * half_width}")
        
        # Display trees side by side
        max_lines = max(len(before_lines), len(after_lines))
        for i in range(max_lines):
            before_line = before_lines[i] if i < len(before_lines) else ""
            after_line = after_lines[i] if i < len(after_lines) else ""
            
            # Truncate if needed
            before_line = before_line[:half_width].ljust(half_width)
            after_line = after_line[:half_width].ljust(half_width)
            
            print(f"{before_line} | {after_line}")
    
    def _format_folder_tree(self, folder_structure, indent=0, is_last=True):
        """Format folder structure as a tree string"""
        if not folder_structure:
            return ""
            
        result = []
        name = os.path.basename(folder_structure['path'])
        
        # Skip root node if it's the first call
        if indent > 0:
            # Determine prefix
            prefix = '└── ' if is_last else '├── '
            indent_str = '    ' * (indent - 1) + prefix
            result.append(f"{indent_str}{name}")
        else:
            result.append(name)
        
        # Process subdirectories
        subdirs = folder_structure.get('subdirectories', [])
        for i, subdir in enumerate(subdirs):
            is_last_child = (i == len(subdirs) - 1)
            subtree = self._format_folder_tree(subdir, indent + 1, is_last_child)
            result.append(subtree)
        
        return '\n'.join(result)
    
    def _get_console_width(self):
        """Get the width of the console"""
        try:
            return os.get_terminal_size().columns
        except (AttributeError, OSError):
            return 80  # Default fallback

    def display_undo_success(self):
        """Display a success message for undo operation"""
        print(f"\n{Fore.GREEN}Successfully undid the last operation.{Style.RESET_ALL}")
    
    def display_undo_failure(self):
        """Display a failure message for undo operation"""
        print(f"\n{Fore.RED}Failed to undo the last operation.{Style.RESET_ALL}")
        print("There may be no previous operations to undo, or an error occurred.")
    
    def spinner(self, message="Processing"):
        """
        Return a context manager for displaying a spinner during long operations.
        
        Usage:
            with ui.spinner("Scanning folders"):
                # Long operation here
        """
        import threading
        import itertools
        import time
        
        class Spinner:
            def __init__(self, message):
                self.message = message
                self.running = False
                self.spinner_thread = None
            
            def spin(self):
                spinner = itertools.cycle(['|', '/', '-', '\\'])
                while self.running:
                    sys.stdout.write(f"\r{self.message} {next(spinner)} ")
                    sys.stdout.flush()
                    time.sleep(0.1)
                sys.stdout.write(f"\r{self.message} Done!{' ' * 10}\n")
            
            def __enter__(self):
                self.running = True
                self.spinner_thread = threading.Thread(target=self.spin)
                self.spinner_thread.start()
                return self
            
            def __exit__(self, exc_type, exc_val, exc_tb):
                self.running = False
                if self.spinner_thread:
                    self.spinner_thread.join()
        
        return Spinner(message) 