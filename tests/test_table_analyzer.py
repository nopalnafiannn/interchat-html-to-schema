"""Tests for the Table Analyzer Agent."""

import unittest
from unittest.mock import patch, MagicMock
from html_schema_converter.agents.table_analyzer import analyze_tables_with_llm

class TestTableAnalyzer(unittest.TestCase):
    """Test cases for the Table Analyzer Agent."""
    
    @patch('html_schema_converter.llm.openai_client.OpenAIClient')
    def test_analyze_tables_with_llm(self, mock_openai_client):
        """Test analyzing tables with LLM."""
        # Setup mock
        mock_client = MagicMock()
        mock_client.generate_completion.return_value = (
            "Main Table: 1\nReasoning: This table has the most columns and data.\nTable Type: data",
            {
                "Latency (s)": 0.5,
                "Memory Usage (MB)": 10,
                "Prompt Tokens": 100,
                "Completion Tokens": 50,
                "Total Tokens": 150
            }
        )
        mock_openai_client.return_value = mock_client
        
        # Test data
        tables_info = {
            "status": "Success",
            "tables_count": 2,
            "tables": [
                {
                    "table_id": 0,
                    "caption": "Table 1",
                    "column_count": 3,
                    "row_count": 5,
                    "headers": ["Col1", "Col2", "Col3"],
                    "sample_data": [["1", "2", "3"]]
                },
                {
                    "table_id": 1,
                    "caption": "Table 2",
                    "column_count": 2,
                    "row_count": 3,
                    "headers": ["ColA", "ColB"],
                    "sample_data": [["A", "B"]]
                }
            ]
        }
        
        # Call function
        result = analyze_tables_with_llm(tables_info, mock_client)
        
        # Verify results
        self.assertEqual(result["status"], "Success")
        self.assertEqual(result["raw_analysis"], "Main Table: 1\nReasoning: This table has the most columns and data.\nTable Type: data")
        self.assertEqual(result["tables_count"], 2)
        self.assertIn("metrics", result)
        self.assertEqual(result["metrics"]["Agent"], "Analyze Tables LLM")
        mock_client.generate_completion.assert_called_once()

    def test_analyze_tables_with_no_tables(self):
        """Test analyzing tables when no tables are found."""
        tables_info = {
            "status": "No tables found",
            "tables_count": 0
        }
        result = analyze_tables_with_llm(tables_info)
        self.assertEqual(result["status"], "No tables found")
        self.assertIsNone(result["recommendation"])

if __name__ == "__main__":
    unittest.main()