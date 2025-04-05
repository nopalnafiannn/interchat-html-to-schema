"""Table Analyzer Agent for determining the most relevant table in HTML content."""

from ..llm.openai_client import OpenAIClient

def analyze_tables_with_llm(tables_info, llm_client=None):
    """
    Uses LLM to analyze which table is likely the main table.
    
    Args:
        tables_info (dict): Tables information
        llm_client (OpenAIClient, optional): LLM client. Creates a new one if None.
        
    Returns:
        dict: Analysis results and metrics
    """
    if tables_info["status"] != "Success" or tables_info["tables_count"] == 0:
        return {"status": tables_info["status"], "recommendation": None}

    # Create LLM client if not provided
    if llm_client is None:
        llm_client = OpenAIClient()

    # Prepare table descriptions
    tables_description = []
    for i, table in enumerate(tables_info["tables"]):
        table_desc = f"Table {i+1}:\n"
        table_desc += f"Caption/Context: {table.get('caption', 'None')}\n"
        table_desc += f"Columns ({table['column_count']}): {', '.join(table['headers'][:10])}{'...' if len(table['headers']) > 10 else ''}\n"
        table_desc += f"Rows: {table['row_count']}\n"
        if table['sample_data']:
            sample_row = table['sample_data'][0]
            table_desc += f"Sample data (first row): {sample_row}\n"
        tables_description.append(table_desc)

    # Create the prompt
    prompt = f"""
You are analyzing HTML tables to find the one that contains the most structured data.
This page contains {tables_info['tables_count']} HTML tables.

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
    
    # Get LLM response
    system_prompt = "You are a data expert analyzing HTML tables to identify the most useful structured data."
    result, metrics = llm_client.generate_completion(system_prompt, prompt)
    
    return {
        "status": "Success",
        "raw_analysis": result,
        "tables_count": tables_info["tables_count"],
        "metrics": {
            "Agent": "Analyze Tables LLM",
            **metrics
        }
    }