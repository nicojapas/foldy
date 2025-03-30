import os
import shutil
import tempfile
import unittest
from src.organizer import FolderOrganizer

class TestFolderOrganizer(unittest.TestCase):
    """Test cases for the FolderOrganizer class"""
    
    def setUp(self):
        """Set up a temporary directory for testing"""
        self.test_dir = tempfile.mkdtemp()
        
        # Create a simple folder structure for testing
        os.makedirs(os.path.join(self.test_dir, "folder1"))
        os.makedirs(os.path.join(self.test_dir, "folder2"))
        os.makedirs(os.path.join(self.test_dir, "Folder1_Similar"))
        
        # Create nested folders
        os.makedirs(os.path.join(self.test_dir, "parent", "child1"))
        os.makedirs(os.path.join(self.test_dir, "parent", "child2"))
        
        # Create a file in one of the folders
        with open(os.path.join(self.test_dir, "folder1", "test.txt"), "w") as f:
            f.write("Test file")
        
        # Initialize the organizer
        self.organizer = FolderOrganizer(self.test_dir)
    
    def tearDown(self):
        """Clean up the temporary directory"""
        shutil.rmtree(self.test_dir)
    
    def test_scan_folder_structure(self):
        """Test that folder scanning works correctly"""
        structure = self.organizer.scan_folder_structure()
        
        # Check that the structure contains the correct information
        self.assertEqual(structure['path'], self.test_dir)
        self.assertEqual(len(structure['subdirectories']), 3)  # folder1, folder2, parent
        
        # Check folder names
        folder_names = [os.path.basename(subdir['path']) for subdir in structure['subdirectories']]
        self.assertIn("folder1", folder_names)
        self.assertIn("folder2", folder_names)
        self.assertIn("parent", folder_names)
        
        # Check file counts
        for subdir in structure['subdirectories']:
            if os.path.basename(subdir['path']) == "folder1":
                self.assertEqual(subdir['file_count'], 1)  # should have one file
            elif os.path.basename(subdir['path']) == "folder2":
                self.assertEqual(subdir['file_count'], 0)  # should be empty
    
    def test_find_similar_folders(self):
        """Test that similar folder detection works"""
        self.organizer.scan_folder_structure()
        similar_folders = self.organizer._find_similar_folders(self.organizer.folder_structure)
        
        # There should be at least one group of similar folders
        self.assertGreaterEqual(len(similar_folders), 1)
        
        # Check if folder1 and Folder1_Similar are grouped together
        for group in similar_folders:
            folder_names = [os.path.basename(f['path']) for f in group]
            if "folder1" in folder_names:
                self.assertIn("Folder1_Similar", folder_names)
                break
        else:
            self.fail("folder1 and Folder1_Similar were not detected as similar")

if __name__ == "__main__":
    unittest.main() 