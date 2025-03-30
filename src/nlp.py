"""
NLP module for folder name analysis using local sentence transformers.
Privacy-focused: all processing happens locally with no external API calls.
"""
from collections import defaultdict
import re
from difflib import SequenceMatcher
from fuzzywuzzy import fuzz

try:
    # Optional dependencies for enhanced NLP processing
    import spacy
    import numpy as np
    from sentence_transformers import SentenceTransformer
    ENHANCED_NLP_AVAILABLE = True
except ImportError:
    ENHANCED_NLP_AVAILABLE = False

class FolderNameAnalyzer:
    """
    Analyzes folder names to find patterns, detect inconsistencies,
    and suggest improvements for better organization.
    """
    def __init__(self, use_enhanced_nlp=True):
        self.use_enhanced_nlp = use_enhanced_nlp and ENHANCED_NLP_AVAILABLE
        self.nlp_model = None
        self.sentence_transformer = None
        
        # Initialize NLP models if available and requested
        if self.use_enhanced_nlp:
            try:
                # Load small model for basic NLP tasks
                self.nlp_model = spacy.load("en_core_web_sm")
                # Load sentence transformer for semantic similarity
                self.sentence_transformer = SentenceTransformer('all-MiniLM-L6-v2')
            except Exception as e:
                print(f"Warning: Enhanced NLP initialization failed: {e}")
                self.use_enhanced_nlp = False
    
    def analyze_name_patterns(self, folder_names):
        """
        Analyze a list of folder names to detect patterns and inconsistencies.
        Returns a dictionary of pattern types and inconsistencies.
        """
        patterns = {
            'case': self._analyze_case_patterns(folder_names),
            'separators': self._analyze_separator_patterns(folder_names),
            'numbering': self._analyze_numbering_patterns(folder_names),
            'semantic_groups': self._find_semantic_groups(folder_names)
        }
        
        return patterns
    
    def _analyze_case_patterns(self, folder_names):
        """Analyze capitalization patterns in folder names"""
        case_patterns = {
            'lowercase': [],
            'uppercase': [],
            'capitalized': [],
            'camelcase': [],
            'mixed': []
        }
        
        for name in folder_names:
            if name.islower():
                case_patterns['lowercase'].append(name)
            elif name.isupper():
                case_patterns['uppercase'].append(name)
            elif name[0].isupper() and name[1:].islower():
                case_patterns['capitalized'].append(name)
            elif not name.isupper() and not name.islower() and '_' not in name and '-' not in name and ' ' not in name:
                # Check for camelCase (no separators but mixed case)
                if any(c.isupper() for c in name[1:]):
                    case_patterns['camelcase'].append(name)
                else:
                    case_patterns['mixed'].append(name)
            else:
                case_patterns['mixed'].append(name)
        
        # Remove empty pattern groups
        return {k: v for k, v in case_patterns.items() if v}
    
    def _analyze_separator_patterns(self, folder_names):
        """Analyze separator patterns in folder names"""
        separator_patterns = {
            'underscore': [],
            'hyphen': [],
            'space': [],
            'no_separator': [],
            'mixed': []
        }
        
        for name in folder_names:
            underscore_count = name.count('_')
            hyphen_count = name.count('-')
            space_count = name.count(' ')
            
            if underscore_count > 0 and hyphen_count == 0 and space_count == 0:
                separator_patterns['underscore'].append(name)
            elif hyphen_count > 0 and underscore_count == 0 and space_count == 0:
                separator_patterns['hyphen'].append(name)
            elif space_count > 0 and underscore_count == 0 and hyphen_count == 0:
                separator_patterns['space'].append(name)
            elif underscore_count == 0 and hyphen_count == 0 and space_count == 0:
                separator_patterns['no_separator'].append(name)
            else:
                separator_patterns['mixed'].append(name)
        
        # Remove empty pattern groups
        return {k: v for k, v in separator_patterns.items() if v}
    
    def _analyze_numbering_patterns(self, folder_names):
        """Analyze numbering patterns in folder names"""
        numbering_patterns = {
            'leading_number': [],
            'trailing_number': [],
            'padded_number': [],
            'no_number': [],
            'version_number': []
        }
        
        for name in folder_names:
            # Check for leading number (e.g. "01_folder")
            if re.match(r'^\d+[_\-\s]', name):
                # Check if it's zero-padded
                if re.match(r'^0\d+[_\-\s]', name):
                    numbering_patterns['padded_number'].append(name)
                else:
                    numbering_patterns['leading_number'].append(name)
            
            # Check for trailing number (e.g. "folder_01")
            elif re.match(r'.*[_\-\s]\d+$', name):
                # Check if it's zero-padded
                if re.match(r'.*[_\-\s]0\d+$', name):
                    numbering_patterns['padded_number'].append(name)
                else:
                    numbering_patterns['trailing_number'].append(name)
            
            # Check for version numbers (e.g. "v1.2" or "v1_2")
            elif re.search(r'v\d+[\._]\d+', name, re.IGNORECASE):
                numbering_patterns['version_number'].append(name)
            
            # No numbers in the name
            elif not any(c.isdigit() for c in name):
                numbering_patterns['no_number'].append(name)
            
            # Has numbers but doesn't fit specific patterns
            else:
                pass  # Don't categorize
        
        # Remove empty pattern groups
        return {k: v for k, v in numbering_patterns.items() if v}
    
    def _find_semantic_groups(self, folder_names):
        """
        Group folder names by semantic similarity.
        If enhanced NLP is not available, fall back to string similarity.
        """
        if not folder_names:
            return {}
        
        if self.use_enhanced_nlp and self.sentence_transformer:
            return self._find_semantic_groups_with_transformers(folder_names)
        else:
            return self._find_semantic_groups_with_string_similarity(folder_names)
    
    def _find_semantic_groups_with_transformers(self, folder_names):
        """Use sentence transformers to find semantically similar folder names"""
        # Clean folder names for better semantic processing
        cleaned_names = [self._clean_name_for_semantic(name) for name in folder_names]
        
        # Skip empty names
        valid_indices = [i for i, name in enumerate(cleaned_names) if name]
        valid_names = [cleaned_names[i] for i in valid_indices]
        
        if not valid_names:
            return {}
        
        # Compute embeddings for folder names
        embeddings = self.sentence_transformer.encode(valid_names)
        
        # Compute similarity matrix
        similarity_matrix = np.zeros((len(valid_names), len(valid_names)))
        for i in range(len(valid_names)):
            for j in range(i, len(valid_names)):
                # Compute cosine similarity
                similarity = np.dot(embeddings[i], embeddings[j]) / (
                    np.linalg.norm(embeddings[i]) * np.linalg.norm(embeddings[j])
                )
                similarity_matrix[i, j] = similarity
                similarity_matrix[j, i] = similarity
        
        # Group by similarity
        threshold = 0.7  # Similarity threshold
        groups = []
        processed = set()
        
        for i in range(len(valid_names)):
            if i in processed:
                continue
                
            group = [valid_indices[i]]
            processed.add(i)
            
            for j in range(len(valid_names)):
                if i != j and j not in processed and similarity_matrix[i, j] > threshold:
                    group.append(valid_indices[j])
                    processed.add(j)
            
            if len(group) > 1:
                groups.append([folder_names[idx] for idx in group])
        
        # Convert to dictionary with group names
        result = {}
        for i, group in enumerate(groups):
            # Try to extract a common theme
            if self.nlp_model:
                keywords = []
                for name in group:
                    doc = self.nlp_model(self._clean_name_for_semantic(name))
                    keywords.extend([token.text for token in doc if token.pos_ in ('NOUN', 'PROPN')])
                
                # Use most common keyword if available
                if keywords:
                    common_word = max(set(keywords), key=keywords.count)
                    group_name = f"semantic_group_{common_word}"
                else:
                    group_name = f"semantic_group_{i+1}"
            else:
                group_name = f"semantic_group_{i+1}"
                
            result[group_name] = group
        
        return result
    
    def _find_semantic_groups_with_string_similarity(self, folder_names):
        """Use string similarity to find similar folder names"""
        groups = []
        processed = set()
        
        for i, name1 in enumerate(folder_names):
            if name1 in processed:
                continue
                
            group = [name1]
            processed.add(name1)
            
            for name2 in folder_names[i+1:]:
                if name2 in processed:
                    continue
                
                # Check similarity using fuzzywuzzy's token_sort_ratio
                # This handles word reordering better than simple string comparison
                similarity = fuzz.token_sort_ratio(
                    self._clean_name_for_semantic(name1),
                    self._clean_name_for_semantic(name2)
                )
                
                if similarity > 70:  # 70% similarity threshold
                    group.append(name2)
                    processed.add(name2)
            
            if len(group) > 1:
                groups.append(group)
        
        # Convert to dictionary with group names
        result = {}
        for i, group in enumerate(groups):
            # Extract common prefix if it exists
            prefix = self._find_common_substring(group)
            if prefix and len(prefix) > 3:
                group_name = f"similarity_group_{prefix}"
            else:
                group_name = f"similarity_group_{i+1}"
                
            result[group_name] = group
        
        return result
    
    def _clean_name_for_semantic(self, name):
        """Clean a folder name for semantic processing"""
        # Replace separators with spaces
        name = name.replace('_', ' ').replace('-', ' ')
        
        # Remove common prefixes/suffixes that don't add semantic meaning
        name = re.sub(r'^(\d+[_\-\s]+)', '', name)
        name = re.sub(r'([_\-\s]+\d+)$', '', name)
        
        # Remove common words that don't add much semantic value
        stop_words = {'folder', 'dir', 'directory', 'temp', 'tmp', 'backup', 'old', 'new'}
        words = name.lower().split()
        words = [w for w in words if w not in stop_words]
        
        return ' '.join(words)
    
    def _find_common_substring(self, strings):
        """Find the longest common substring among a list of strings"""
        if not strings or len(strings) < 2:
            return ""
            
        shortest = min(strings, key=len)
        
        for length in range(len(shortest), 0, -1):
            for start in range(len(shortest) - length + 1):
                substr = shortest[start:start+length]
                if all(substr in s for s in strings):
                    return substr
        
        return ""
    
    def suggest_name_standardization(self, folder_names, preferred_patterns=None):
        """
        Suggest standardized folder names based on detected patterns and
        optionally specified preferred patterns.
        """
        if not folder_names:
            return {}
            
        # Set default preferences if none provided
        if not preferred_patterns:
            preferred_patterns = {
                'case': self._detect_dominant_case_pattern(folder_names),
                'separator': self._detect_dominant_separator_pattern(folder_names),
                'numbering': self._detect_dominant_numbering_pattern(folder_names)
            }
        
        # Generate standardized names
        standardized_names = {}
        for name in folder_names:
            new_name = self._standardize_name(name, preferred_patterns)
            if new_name != name:
                standardized_names[name] = new_name
                
        return standardized_names
    
    def _detect_dominant_case_pattern(self, folder_names):
        """Detect the most common case pattern in the folder names"""
        patterns = self._analyze_case_patterns(folder_names)
        
        # Find the most common pattern
        dominant_pattern = None
        max_count = 0
        
        for pattern, names in patterns.items():
            if len(names) > max_count:
                max_count = len(names)
                dominant_pattern = pattern
        
        # Default to lowercase if no clear pattern
        return dominant_pattern or 'lowercase'
    
    def _detect_dominant_separator_pattern(self, folder_names):
        """Detect the most common separator pattern in the folder names"""
        patterns = self._analyze_separator_patterns(folder_names)
        
        # Find the most common pattern
        dominant_pattern = None
        max_count = 0
        
        for pattern, names in patterns.items():
            if len(names) > max_count:
                max_count = len(names)
                dominant_pattern = pattern
        
        # Default to underscore if no clear pattern
        return dominant_pattern or 'underscore'
    
    def _detect_dominant_numbering_pattern(self, folder_names):
        """Detect the most common numbering pattern in the folder names"""
        patterns = self._analyze_numbering_patterns(folder_names)
        
        # Find the most common pattern
        dominant_pattern = None
        max_count = 0
        
        for pattern, names in patterns.items():
            if len(names) > max_count and pattern != 'no_number':
                max_count = len(names)
                dominant_pattern = pattern
        
        # Default to no specific numbering pattern
        return dominant_pattern or None
    
    def _standardize_name(self, name, patterns):
        """Standardize a folder name according to specified patterns"""
        # Parse components from the original name
        name_components = self._parse_name_components(name)
        
        # Reconstruct with standardized components
        new_name = self._reconstruct_name(name_components, patterns)
        
        return new_name
    
    def _parse_name_components(self, name):
        """Parse a folder name into components (prefix number, main text, suffix number)"""
        components = {
            'prefix_number': None,
            'main_text': name,
            'suffix_number': None
        }
        
        # Extract leading number
        prefix_match = re.match(r'^(\d+)([_\-\s])(.*)', name)
        if prefix_match:
            components['prefix_number'] = prefix_match.group(1)
            components['prefix_separator'] = prefix_match.group(2)
            components['main_text'] = prefix_match.group(3)
        
        # Extract trailing number
        suffix_match = re.match(r'(.*)([_\-\s])(\d+)$', components['main_text'])
        if suffix_match:
            components['main_text'] = suffix_match.group(1)
            components['suffix_separator'] = suffix_match.group(2)
            components['suffix_number'] = suffix_match.group(3)
        
        # Split main text by separators
        words = re.split(r'[_\-\s]', components['main_text'])
        components['words'] = [w for w in words if w]
        
        return components
    
    def _reconstruct_name(self, components, patterns):
        """Reconstruct a folder name with standardized formatting"""
        # Apply case pattern to words
        if patterns['case'] == 'lowercase':
            words = [w.lower() for w in components['words']]
        elif patterns['case'] == 'uppercase':
            words = [w.upper() for w in components['words']]
        elif patterns['case'] == 'capitalized':
            words = [w[0].upper() + w[1:].lower() if w else '' for w in components['words']]
        elif patterns['case'] == 'camelcase':
            words = [components['words'][0].lower()] + [w[0].upper() + w[1:].lower() if w else '' for w in components['words'][1:]]
            return ''.join(words)
        else:
            words = components['words']
        
        # Apply separator pattern
        if patterns['separator'] == 'underscore':
            separator = '_'
        elif patterns['separator'] == 'hyphen':
            separator = '-'
        elif patterns['separator'] == 'space':
            separator = ' '
        else:
            separator = '_'  # Default
        
        # Build main text
        main_text = separator.join(words)
        
        # Apply numbering pattern
        result = main_text
        
        if components['prefix_number'] is not None and patterns['numbering'] == 'padded_number':
            # Ensure number is zero-padded to at least 2 digits
            num = int(components['prefix_number'])
            result = f"{num:02d}{separator}{main_text}"
        elif components['prefix_number'] is not None:
            result = f"{components['prefix_number']}{separator}{main_text}"
            
        if components['suffix_number'] is not None and patterns['numbering'] == 'padded_number':
            # Ensure number is zero-padded to at least 2 digits
            num = int(components['suffix_number'])
            result = f"{main_text}{separator}{num:02d}"
        elif components['suffix_number'] is not None:
            result = f"{main_text}{separator}{components['suffix_number']}"
            
        return result
    
    def detect_redundant_folders(self, folder_paths, folder_contents):
        """
        Detect potentially redundant folders based on name and content similarity.
        
        Args:
            folder_paths: List of folder paths
            folder_contents: Dictionary mapping folder paths to their content summary
                            (e.g. {path: {'file_count': 10, 'subdirs': ['a', 'b']}})
        
        Returns:
            Dictionary mapping groups of potentially redundant folders
        """
        redundant_groups = []
        processed = set()
        
        for i, path1 in enumerate(folder_paths):
            if path1 in processed:
                continue
                
            name1 = path1.split('/')[-1] if '/' in path1 else path1.split('\\')[-1]
            content1 = folder_contents.get(path1, {})
            
            group = [path1]
            processed.add(path1)
            
            for path2 in folder_paths[i+1:]:
                if path2 in processed:
                    continue
                    
                name2 = path2.split('/')[-1] if '/' in path2 else path2.split('\\')[-1]
                content2 = folder_contents.get(path2, {})
                
                # Check name similarity
                name_similarity = fuzz.ratio(name1.lower(), name2.lower())
                
                # Check content similarity if available
                content_similarity = 0
                if content1 and content2:
                    # Simple heuristic: compare file counts and subdirectory names
                    if 'file_count' in content1 and 'file_count' in content2:
                        if content1['file_count'] > 0 and content2['file_count'] > 0:
                            # Calculate similarity ratio between file counts
                            min_count = min(content1['file_count'], content2['file_count'])
                            max_count = max(content1['file_count'], content2['file_count'])
                            if max_count > 0:
                                count_ratio = min_count / max_count
                                content_similarity += count_ratio * 50  # Weight: 50%
                    
                    # Compare subdirectory names if available
                    if 'subdirs' in content1 and 'subdirs' in content2:
                        subdirs1 = set(content1['subdirs'])
                        subdirs2 = set(content2['subdirs'])
                        
                        if subdirs1 and subdirs2:
                            # Calculate Jaccard similarity of subdirectory sets
                            intersection = len(subdirs1.intersection(subdirs2))
                            union = len(subdirs1.union(subdirs2))
                            if union > 0:
                                jaccard = intersection / union
                                content_similarity += jaccard * 50  # Weight: 50%
                
                # Combine name and content similarity
                total_similarity = name_similarity * 0.7 + content_similarity * 0.3
                
                if total_similarity > 70:  # 70% total similarity threshold
                    group.append(path2)
                    processed.add(path2)
            
            if len(group) > 1:
                redundant_groups.append(group)
        
        # Convert to dictionary with group names
        result = {}
        for i, group in enumerate(redundant_groups):
            result[f"redundant_group_{i+1}"] = group
        
        return result 