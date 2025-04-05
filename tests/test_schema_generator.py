"""Tests for the Schema Generator Agent."""

import unittest
from unittest.mock import patch, MagicMock
from html_schema_converter.agents.schema_generator import generate_datascheme_with_llm

class TestSchemaGenerator(unittest.TestCase):
    """Test cases for the Schema Generator Agent."""
    
    @patch('html_schema_converter.llm.openai_client.OpenAIClient')
    @patch('html_schema_converter.agents.schema_generator.extract_schema_from_table')
    def test_generate_datascheme_with_llm(self, mock_extract_schema, mock_openai_client):
        """Test generating data schema with LLM."""
        # Setup extract_schema mock
        mock_extract_schema.return_value = {
            "status": "Success",
            "original_headers": ["Name", "Age", "City"],
            "schema_data": [
                ["John", "30", "New York"],
                ["Alice", "25", "Los Angeles"]
            ]
        }
        
        # Setup OpenAI client mock
        mock_client = MagicMock()
        mock_client.generate_completion.return_value = (
            '{"schema": [{"column_name": "Name", "type": "string", "description": "Person\'s name"}, '
            '{"column_name": "Age", "type": "number", "description": "Person\'s age in years"}, '
            '{"column_name": "City", "type": "string", "description": "City of residence"}]}',
            {
                "Latency (s)": 0.8,
                "Memory Usage (MB)": 15,
                "Prompt Tokens": 200,
                "Completion Tokens": 100,
                "Total Tokens": 300
            }
        )
        mock_openai_client.return_value = mock_client
        
        # Test data
        table_info = {
            "headers": ["Name", "Age", "City"],
            "sample_data": [
                ["John", "30", "New York"],
                ["Alice", "25", "Los Angeles"]
            ]
        }
        
        # Call function
        result = generate_datascheme_with_llm(table_info, mock_client)
        
        # Verify results
        self.assertIn("schema_table", result)
        self.assertIn("metrics", result)
        self.assertEqual(result["metrics"]["Agent"], "Generate Data Schema LLM")
        mock_client.generate_completion.assert_called_once()
        
    @patch('html_schema_converter.agents.schema_generator.extract_schema_from_table')
    def test_generate_datascheme_with_no_data(self, mock_extract_schema):
        """Test generating data schema when no data is found."""
        # Setup mock
        mock_extract_schema.return_value = {
            "status": "No data found",
            "schema_data": []
        }
        
        # Test data
        table_info = {
            "headers": [],
            "sample_data": []
        }
        
        # Call function
        result = generate_datascheme_with_llm(table_info)
        
        # Verify results
        self.assertEqual(result["schema_table"], "Could not extract schema data")

if __name__ == "__main__":
    unittest.main()