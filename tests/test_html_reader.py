"""Tests for the HTML Reader agent."""

import unittest
from unittest.mock import patch, MagicMock
import requests
from bs4 import BeautifulSoup

from html_schema_converter.agents.html_reader import HTMLReader

class TestHTMLReader(unittest.TestCase):
    """Test case for the HTMLReader class."""
    
    def setUp(self):
        """Set up the test environment."""
        self.reader = HTMLReader()
    
    @patch('requests.get')
    def test_read_from_url_success(self, mock_get):
        """Test reading HTML from a URL successfully."""
        # Mock the response
        mock_response = MagicMock()
        mock_response.content = """
        <html>
            <body>
                <table>
                    <tr><th>Name</th><th>Age</th><th>City</th></tr>
                    <tr><td>John</td><td>30</td><td>New York</td></tr>
                    <tr><td>Jane</td><td>25</td><td>Chicago</td></tr>
                </table>
            </body>
        </html>
        """
        mock_get.return_value = mock_response
        mock_response.raise_for_status = MagicMock()
        
        # Call the method
        result = self.reader.read_from_url("https://example.com")
        
        # Verify the results
        self.assertEqual(result["status"], "Success")
        self.assertEqual(result["tables_count"], 1)
        self.assertEqual(len(result["tables"]), 1)
        self.assertEqual(result["tables"][0]["headers"], ["Name", "Age", "City"])
        self.assertEqual(len(result["tables"][0]["sample_data"]), 2)
        self.assertEqual(result["tables"][0]["sample_data"][0], ["John", "30", "New York"])
    
    @patch('requests.get')
    def test_read_from_url_no_tables(self, mock_get):
        """Test reading HTML with no tables."""
        # Mock the response
        mock_response = MagicMock()
        mock_response.content = """
        <html>
            <body>
                <h1>No tables here</h1>
                <p>Just text content</p>
            </body>
        </html>
        """
        mock_get.return_value = mock_response
        mock_response.raise_for_status = MagicMock()
        
        # Call the method
        result = self.reader.read_from_url("https://example.com")
        
        # Verify the results
        self.assertEqual(result["status"], "No tables found")
        self.assertEqual(result["tables_count"], 0)
    
    @patch('requests.get')
    def test_read_from_url_error(self, mock_get):
        """Test reading HTML with a network error."""
        # Mock a network error
        mock_get.side_effect = requests.exceptions.RequestException("Network error")
        
        # Call the method
        result = self.reader.read_from_url("https://example.com")
        
        # Verify the results
        self.assertIn("Error", result["status"])
        self.assertEqual(result["tables_count"], 0)
    
    def test_extract_headers(self):
        """Test extracting headers from a table."""
        # Create a sample table
        html = """
        <table>
            <tr><th>Name</th><th>Age</th><th>City</th></tr>
        </table>
        """
        soup = BeautifulSoup(html, 'html.parser')
        table = soup.find('table')
        
        # Extract headers
        headers = self.reader._extract_headers(table)
        
        # Verify the results
        self.assertEqual(headers, ["Name", "Age", "City"])
    
    def test_extract_sample_data(self):
        """Test extracting sample data from a table."""
        # Create a sample table
        html = """
        <table>
            <tr><th>Name</th><th>Age</th><th>City</th></tr>
            <tr><td>John</td><td>30</td><td>New York</td></tr>
            <tr><td>Jane</td><td>25</td><td>Chicago</td></tr>
            <tr><td>Bob</td><td>40</td><td>Boston</td></tr>
        </table>
        """
        soup = BeautifulSoup(html, 'html.parser')
        table = soup.find('table')
        headers = ["Name", "Age", "City"]
        
        # Extract sample data
        sample_data = self.reader._extract_sample_data(table, headers)
        
        # Verify the results
        self.assertEqual(len(sample_data), 3)
        self.assertEqual(sample_data[0], ["John", "30", "New York"])
        self.assertEqual(sample_data[1], ["Jane", "25", "Chicago"])
        self.assertEqual(sample_data[2], ["Bob", "40", "Boston"])

if __name__ == '__main__':
    unittest.main()