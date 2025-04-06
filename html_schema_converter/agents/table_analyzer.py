"""Table Analyzer Agent for identifying the most relevant table."""

import re
import time
import psutil
import os
from typing import Dict, List, Any, Optional, Tuple

from html_schema_converter.llm.openai_client import OpenAIClient
from html_schema_converter.config import config
from html_schema_converter.utils.metrics import track_metrics

class TableAnalyzer:
    """Agent for analyzing and selecting the most relevant table."""
    
    def __init__(self):
        """Initialize the table analyzer with LLM client."""
        self.llm_client = OpenAIClient()
        self.model = config.get("llm.table_analysis_model", "gpt-3.5-turbo")
        self.temperature = config.get("llm.temperature", 0)
    
    @track_metrics
    def analyze_tables(self, tables_info: Dict[str, Any]) -> Dict[str, Any]:
        """
        Analyze tables using LLM to identify the most relevant one.
        
        Args:
            tables_info: Dictionary with table information from HTMLReader
            
        Returns:
            Dictionary with analysis results and metrics
        """
        if tables_info["status"] != "Success" or tables_info["tables_count"] == 0:
            return {"status": tables_info["status"], "recommendation": None}
        
        tables_description = self._prepare_tables_description(tables_info["tables"])
        prompt = self._create_analysis_prompt(tables_info["tables_count"], tables_description)
        
        # Call LLM for analysis
        raw_response = self.llm_client.generate(
            prompt=prompt,
            model=self.model,
            system_message="You are a data expert analyzing HTML tables to identify the most useful structured data.",
            max_tokens=500,
            temperature=self.temperature
        )
        
        # Parse the response
        main_table_rec, reasoning, table_type = self._parse_analysis_response(raw_response["content"])
        
        return {
            "status": "Success",
            "raw_analysis": raw_response["content"],
            "recommendation": {
                "table_index": main_table_rec,
                "reasoning": reasoning,
                "table_type": table_type
            },
            "tables_count": tables_info["tables_count"],
            "metrics": raw_response.get("metrics", {})
        }
    
    def _prepare_tables_description(self, tables: List[Dict[str, Any]]) -> List[str]:
        """
        Prepare descriptions of tables for the LLM prompt.
        
        Args:
            tables: List of table information dictionaries
            
        Returns:
            List of table descriptions
        """
        tables_description = []
        for i, table in enumerate(tables):
            table_desc = f"Table {i+1}:\n"
            table_desc += f"Caption/Context: {table.get('caption', 'None')}\n"
            table_desc += f"Columns ({table['column_count']}): {', '.join(table['headers'][:10])}{'...' if len(table['headers']) > 10 else ''}\n"
            table_desc += f"Rows: {table['row_count']}\n"
            if table['sample_data']:
                sample_row = table['sample_data'][0]
                table_desc += f"Sample data (first row): {sample_row}\n"
            tables_description.append(table_desc)
        return tables_description
    
    def _create_analysis_prompt(self, tables_count: int, tables_description: List[str]) -> str:
        """
        Create the prompt for LLM table analysis.
        
        Args:
            tables_count: Number of tables
            tables_description: List of table descriptions
            
        Returns:
            Analysis prompt string
        """
        prompt = f"""
You are analyzing HTML tables to find the one that contains the most structured data.
This page contains {tables_count} HTML tables.

Here are the details of each table:

{chr(10).join(tables_description)}

Based on this information, which table appears to be the main content table that likely contains
the most useful structured data?

Please identify the most likely main table by number and explain your reasoning in 2-3 sentences.

Provide your response in this format:
Main Table: [table number]
Reasoning: [your reasoning]
Table Type: [data/schema/list/other]
        """
        return prompt
    
    def _parse_analysis_response(self, response_text: str) -> Tuple[Optional[int], str, str]:
        """
        Parse the LLM response to extract main table recommendation.
        
        Args:
            response_text: Raw LLM response text
            
        Returns:
            Tuple of (table_index, reasoning, table_type)
        """
        main_table_rec = None
        reasoning = "No reasoning provided."
        table_type = "unknown"
        
        # Extract main table number
        main_table_match = re.search(r'Main Table:\s*(\d+)', response_text)
        if main_table_match:
            main_table_rec = int(main_table_match.group(1)) - 1  # Convert to 0-based index
        
        # Extract reasoning
        reasoning_match = re.search(r'Reasoning:(.*?)(?:Table Type:|$)', response_text, re.DOTALL)
        if reasoning_match:
            reasoning = reasoning_match.group(1).strip()
        
        # Extract table type
        type_match = re.search(r'Table Type:\s*(\w+)', response_text)
        if type_match:
            table_type = type_match.group(1).strip()
        
        return main_table_rec, reasoning, table_type
    
    def display_tables_and_get_selection(self, tables_info: Dict[str, Any], 
                                         analysis_result: Dict[str, Any]) -> Optional[int]:
        """
        Display table information and get user selection.
        
        Args:
            tables_info: Dictionary with table information
            analysis_result: Dictionary with analysis results
            
        Returns:
            Selected table index or None if invalid selection
        """
        if tables_info["status"] != "Success":
            print(tables_info["status"])
            return None
        
        print(f"Found {tables_info['tables_count']} tables in the HTML document.\n")
        
        # Display recommendation if available
        if analysis_result["status"] == "Success" and analysis_result.get("recommendation"):
            rec = analysis_result["recommendation"]
            if rec["table_index"] is not None:
                print("\nRecommendation:")
                print(f"  Recommended Table: Table {rec['table_index'] + 1}")
                print(f"  Reasoning: {rec['reasoning']}")
                print(f"  Table Type: {rec['table_type']}")
                print()
        
        # Display table information
        for i, table in enumerate(tables_info["tables"]):
            print(f"Table {i+1}:")
            print(f"  Caption/Context: {table.get('caption', 'None')}")
            print(f"  Columns: {table['column_count']}")
            print(f"  Headers: {', '.join(table['headers'][:5])}{'...' if len(table['headers']) > 5 else ''}")
            print(f"  Rows: {table['row_count']}")
            if table['sample_data']:
                first_row = table['sample_data'][0]
                print(f"  Sample Row: {first_row[:3]}{'...' if len(first_row) > 3 else ''}")
            print()
        
        # Automatic selection for single table
        if tables_info["tables_count"] == 1:
            print("Only one table found. Automatically selecting it.")
            return 0
        
        # Handle recommendation
        rec_idx = None
        if analysis_result["status"] == "Success" and analysis_result.get("recommendation"):
            rec_idx = analysis_result["recommendation"]["table_index"]
            if rec_idx is not None and 0 <= rec_idx < tables_info["tables_count"]:
                selection = input(f"Accept recommendation (Table {rec_idx + 1})? (y/n): ")
                if selection.lower() == 'y':
                    return rec_idx
        
        # Manual selection
        selected = input(f"Select a table (1-{tables_info['tables_count']}): ")
        try:
            selected_idx = int(selected) - 1
            if 0 <= selected_idx < tables_info["tables_count"]:
                return selected_idx
        except:
            pass
        
        print("Invalid selection.")
        return None