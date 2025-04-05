"""Tests for the HTML Reader Agent."""

import unittest
from html_schema_converter.agents.html_reader import html_reader_agent, extract_schema_from_table

class TestHTMLReader(unittest.TestCase):
    """Test cases for the HTML Reader Agent."""
    
    def test_html_reader_with_valid_url(self):
        """Test HTML reader with a valid URL containing tables."""
        # Test with a simple Wikipedia page that likely has tables
        result = html_reader_agent("https://en.wikipedia.org/wiki/List_of_programming_languages")
        self.assertEqual(result["status"], "Success")
        self.assertGreater(result["tables_count"], 0)
    
    def test_html_reader_with_invalid_url(self):
        """Test HTML reader with an invalid URL."""
        result = html_reader_agent("https://thisurldoesnotexist.example.com")
        self.assertNotEqual(result["status"], "Success")
        self.assertEqual(result["tables_count"], 0)
    
    def test_extract_schema_from_table(self):
        """Test extraction of schema from table information."""
        table_info = {
            "headers": ["Name", "Age", "City"],
            "sample_data": [
                ["John", "30", "New York"],
                ["Alice", "25", "Los Angeles"]
            ]
        }
        result = extract_schema_from_table(table_info)
        self.assertEqual(result["status"], "Success")
        self.assertEqual(result["original_headers"], ["Name", "Age", "City"])
        self.assertEqual(len(result["schema_data"]), 2)

if __name__ == "__main__":
    unittest.main()