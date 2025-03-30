import unittest
from src.nlp import FolderNameAnalyzer

class TestFolderNameAnalyzer(unittest.TestCase):
    """Test cases for the FolderNameAnalyzer class"""
    
    def setUp(self):
        """Set up the analyzer for testing"""
        # Use basic mode (no enhanced NLP) for consistent testing
        self.analyzer = FolderNameAnalyzer(use_enhanced_nlp=False)
    
    def test_analyze_case_patterns(self):
        """Test detection of case patterns in folder names"""
        folder_names = [
            "lowercase",
            "UPPERCASE",
            "Capitalized",
            "camelCase",
            "Mixed_Case"
        ]
        
        patterns = self.analyzer._analyze_case_patterns(folder_names)
        
        # Check that each case pattern was detected
        self.assertIn("lowercase", patterns.get("lowercase", []))
        self.assertIn("UPPERCASE", patterns.get("uppercase", []))
        self.assertIn("Capitalized", patterns.get("capitalized", []))
        self.assertIn("camelCase", patterns.get("camelcase", []))
        self.assertIn("Mixed_Case", patterns.get("mixed", []))
    
    def test_analyze_separator_patterns(self):
        """Test detection of separator patterns in folder names"""
        folder_names = [
            "with_underscore",
            "with-hyphen",
            "with space",
            "noseparator",
            "mixed_separator-with space"
        ]
        
        patterns = self.analyzer._analyze_separator_patterns(folder_names)
        
        # Check that each separator pattern was detected
        self.assertIn("with_underscore", patterns.get("underscore", []))
        self.assertIn("with-hyphen", patterns.get("hyphen", []))
        self.assertIn("with space", patterns.get("space", []))
        self.assertIn("noseparator", patterns.get("no_separator", []))
        self.assertIn("mixed_separator-with space", patterns.get("mixed", []))
    
    def test_analyze_numbering_patterns(self):
        """Test detection of numbering patterns in folder names"""
        folder_names = [
            "01_leading_number",
            "trailing_number_2",
            "padded_number_02",
            "no_number_at_all",
            "version_v1.2"
        ]
        
        patterns = self.analyzer._analyze_numbering_patterns(folder_names)
        
        # Check that each numbering pattern was detected
        self.assertIn("01_leading_number", patterns.get("padded_number", []))
        self.assertIn("trailing_number_2", patterns.get("trailing_number", []))
        self.assertIn("padded_number_02", patterns.get("padded_number", []))
        self.assertIn("no_number_at_all", patterns.get("no_number", []))
        self.assertIn("version_v1.2", patterns.get("version_number", []))
    
    def test_suggest_name_standardization(self):
        """Test suggestion of standardized names"""
        folder_names = [
            "inconsistent_name",
            "INCONSISTENT_NAME",
            "Inconsistent-Name",
            "inconsistent name",
            "01_inconsistent_name"
        ]
        
        # Specify preferred patterns for consistent results
        preferred_patterns = {
            'case': 'lowercase',
            'separator': 'underscore',
            'numbering': 'padded_number'
        }
        
        suggestions = self.analyzer.suggest_name_standardization(folder_names, preferred_patterns)
        
        # Check that the suggestions follow the preferred patterns
        for original, suggested in suggestions.items():
            # Should be lowercase
            self.assertEqual(suggested, suggested.lower())
            
            # Should use underscore separator
            self.assertNotIn('-', suggested)
            self.assertNotIn(' ', suggested)
            
            # Numbers should be padded if present
            if original.startswith("01_"):
                self.assertTrue(suggested.startswith("01_"))
    
    def test_find_semantic_groups_with_string_similarity(self):
        """Test grouping of semantically similar folder names using string similarity"""
        folder_names = [
            "photos_2022",
            "pictures_2022",
            "images_2022",
            "documents_2022",
            "docs_2022"
        ]
        
        groups = self.analyzer._find_semantic_groups_with_string_similarity(folder_names)
        
        # Should have at least 2 groups
        self.assertGreaterEqual(len(groups), 2)
        
        # Check if similar names are grouped together
        for group_name, group in groups.items():
            # Photos/pictures/images should be in the same group
            if "photos_2022" in group:
                self.assertIn("pictures_2022", group)
                self.assertIn("images_2022", group)
            
            # Documents/docs should be in the same group
            elif "documents_2022" in group:
                self.assertIn("docs_2022", group)

if __name__ == "__main__":
    unittest.main() 