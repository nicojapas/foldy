#!/usr/bin/env python3
"""
FolderSense - AI-Powered Folder Organizer

A privacy-conscious tool that analyzes folder structures and suggests improvements
without reading file contents.
"""
import argparse
import sys
from src.organizer import FolderOrganizer
from src.ui import CommandLineInterface

def main():
    parser = argparse.ArgumentParser(description="FolderSense - AI-Powered Folder Organizer")
    parser.add_argument("path", help="Path to the folder to analyze")
    parser.add_argument("--dry-run", action="store_true", help="Preview changes without applying them")
    parser.add_argument("--verbose", action="store_true", help="Enable detailed output")
    parser.add_argument("--undo", action="store_true", help="Undo the last applied changes")
    parser.add_argument("--explode", action="store_true", help="Move all files to the root folder and delete empty subfolders")
    
    args = parser.parse_args()
    
    try:
        organizer = FolderOrganizer(args.path, verbose=args.verbose)
        ui = CommandLineInterface(organizer)
        
        if args.undo:
            # Handle undo operation
            print("Attempting to undo the last operation...")
            success = organizer.undo_last_change()
            
            if success:
                ui.display_undo_success()
            else:
                ui.display_undo_failure()
            
            return 0
        
        if args.explode:
            # Handle explode operation
            print("Exploding folder structure...")
            print(f"This will move ALL files to {args.path} and delete ALL empty folders.")
            confirm = input("Are you sure you want to continue? (y/n): ").lower().strip()
            
            if confirm == 'y':
                with ui.spinner("Exploding folder structure"):
                    success = organizer.explode_folder_structure()
                
                if success:
                    print("\nFolder structure exploded successfully!")
                    print("All files have been moved to the root directory.")
                    print("All empty folders have been deleted.")
                else:
                    print("\nFailed to explode folder structure. Please check logs for details.")
            else:
                print("Operation cancelled.")
            
            return 0
        
        # Scan folder structure
        with ui.spinner("Scanning folder structure"):
            organizer.scan_folder_structure()
        
        # Analyze and generate suggestions
        with ui.spinner("Analyzing and generating suggestions"):
            suggestions = organizer.suggest_improvements()
        
        # Show suggestions and ask for confirmation
        approved_suggestions = ui.display_suggestions(suggestions)
        
        if approved_suggestions:
            if not args.dry_run:
                print("\nApplying changes...")
                before_structure = organizer.folder_structure.copy()
                
                success = organizer.apply_changes(approved_suggestions)
                
                if success:
                    # Get the updated folder structure
                    after_structure = organizer.folder_structure
                    
                    print("\nChanges applied successfully!")
                    
                    # Display before/after comparison if not too large
                    if sum(1 for _ in str(before_structure).split('\n')) < 100:  # Limit to avoid huge output
                        ui.display_before_after(before_structure, after_structure)
                else:
                    print("\nFailed to apply changes. Please check logs for details.")
            else:
                print("\nDry run completed. No changes were made.")
        else:
            print("\nNo changes were approved.")
    
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        return 1
    
    return 0

if __name__ == "__main__":
    sys.exit(main()) 