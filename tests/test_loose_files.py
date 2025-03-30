import os
import shutil
import tempfile
import unittest
from src.organizer import FolderOrganizer

class TestLooseFilesGrouping(unittest.TestCase):
    """Test cases for grouping loose files functionality"""
    
    def setUp(self):
        """Set up a temporary directory with loose files for testing"""
        self.test_dir = tempfile.mkdtemp()
        
        # Create some image files in the root directory
        for i in range(5):
            with open(os.path.join(self.test_dir, f"image_{i}.jpg"), "w") as f:
                f.write(f"Test image {i}")
        
        # Create some document files in the root directory
        for i in range(5):
            with open(os.path.join(self.test_dir, f"document_{i}.pdf"), "w") as f:
                f.write(f"Test document {i}")
        
        # Create some text files in the root directory
        for i in range(3):
            with open(os.path.join(self.test_dir, f"note_{i}.txt"), "w") as f:
                f.write(f"Test note {i}")
        
        # Create an Images folder with some existing images
        images_dir = os.path.join(self.test_dir, "Images")
        os.makedirs(images_dir)
        with open(os.path.join(images_dir, "existing_image.jpg"), "w") as f:
            f.write("Existing image")
        
        # Initialize the organizer
        self.organizer = FolderOrganizer(self.test_dir)
    
    def tearDown(self):
        """Clean up the temporary directory"""
        shutil.rmtree(self.test_dir)
    
    def test_find_loose_files_to_group(self):
        """Test that loose files are correctly identified and grouped"""
        # First scan the folder structure
        self.organizer.scan_folder_structure()
        
        # Get suggestions for grouping loose files
        suggestions = self.organizer._find_loose_files_to_group()
        
        # There should be at least 3 groups of files: JPGs, PDFs, and TXTs
        self.assertGreaterEqual(len(suggestions), 3)
        
        # Check if each type of file is in the suggestions
        jpg_suggestion = None
        pdf_suggestion = None
        txt_suggestion = None
        
        for suggestion in suggestions:
            # Check that all suggestions are of the right type
            self.assertEqual(suggestion['type'], 'group_loose_files')
            
            # Identify which file group this is
            file_types = set(file_info['extension'] for file_info in suggestion['files'])
            
            if '.jpg' in file_types:
                jpg_suggestion = suggestion
            elif '.pdf' in file_types:
                pdf_suggestion = suggestion
            elif '.txt' in file_types:
                txt_suggestion = suggestion
        
        # Verify JPG files detection
        self.assertIsNotNone(jpg_suggestion, "JPG files were not detected")
        self.assertEqual(len(jpg_suggestion['files']), 5, "Should have found 5 JPG files")
        self.assertFalse(jpg_suggestion['is_new_folder'], "Should use existing Images folder")
        self.assertEqual(os.path.basename(jpg_suggestion['target_folder']), "Images")
        
        # Verify PDF files detection
        self.assertIsNotNone(pdf_suggestion, "PDF files were not detected")
        self.assertEqual(len(pdf_suggestion['files']), 5, "Should have found 5 PDF files")
        self.assertTrue(pdf_suggestion['is_new_folder'], "Should create a new folder for PDFs")
        
        # Verify TXT files detection
        self.assertIsNotNone(txt_suggestion, "TXT files were not detected")
        self.assertEqual(len(txt_suggestion['files']), 3, "Should have found 3 TXT files")
    
    def test_apply_group_loose_files(self):
        """Test that applying the suggestion works correctly"""
        # First scan the folder structure
        self.organizer.scan_folder_structure()
        
        # Get suggestion for grouping JPG files
        suggestions = self.organizer._find_loose_files_to_group()
        jpg_suggestion = next((s for s in suggestions if any(f['extension'] == '.jpg' for f in s['files'])), None)
        
        self.assertIsNotNone(jpg_suggestion, "JPG files were not detected")
        
        # Apply the suggestion
        self.organizer.apply_changes([jpg_suggestion])
        
        # Check that JPG files are no longer in the root directory
        jpg_files_in_root = [f for f in os.listdir(self.test_dir) if f.endswith('.jpg')]
        self.assertEqual(len(jpg_files_in_root), 0, "JPG files should no longer be in root")
        
        # Check that JPG files are now in the Images directory
        jpg_files_in_images = [f for f in os.listdir(os.path.join(self.test_dir, "Images")) if f.endswith('.jpg')]
        self.assertEqual(len(jpg_files_in_images), 6, "Should be 6 JPG files in Images (5 moved + 1 existing)")
    
    def test_find_suitable_folder(self):
        """Test that the system correctly finds suitable folders for files"""
        # Scan folder structure
        self.organizer.scan_folder_structure()
        
        # Add some additional folders for testing
        os.makedirs(os.path.join(self.test_dir, "Documents"))
        os.makedirs(os.path.join(self.test_dir, "Text_Files"))
        
        # Re-scan to pick up new folders
        self.organizer.scan_folder_structure()
        
        # Test for JPG files
        jpg_files = [{'path': os.path.join(self.test_dir, f"image_{i}.jpg"), 
                     'extension': '.jpg'} for i in range(5)]
        suitable_folder = self.organizer._find_suitable_folder_for_files('.jpg', jpg_files)
        self.assertEqual(os.path.basename(suitable_folder), "Images")
        
        # Test for PDF files (should match Documents)
        pdf_files = [{'path': os.path.join(self.test_dir, f"document_{i}.pdf"), 
                     'extension': '.pdf'} for i in range(5)]
        suitable_folder = self.organizer._find_suitable_folder_for_files('.pdf', pdf_files)
        self.assertEqual(os.path.basename(suitable_folder), "Documents")
        
        # Test for TXT files (should match Text_Files)
        txt_files = [{'path': os.path.join(self.test_dir, f"note_{i}.txt"), 
                     'extension': '.txt'} for i in range(3)]
        suitable_folder = self.organizer._find_suitable_folder_for_files('.txt', txt_files)
        self.assertEqual(os.path.basename(suitable_folder), "Text_Files")

if __name__ == "__main__":
    unittest.main() 