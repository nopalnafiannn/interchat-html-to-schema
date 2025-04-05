"""Example usage of the HTML to Data Schema Converter."""

from html_schema_converter.agents.html_reader import html_reader_agent
from html_schema_converter.agents.table_analyzer import analyze_tables_with_llm
from html_schema_converter.agents.schema_generator import generate_datascheme_with_llm
from html_schema_converter.utils.formatters import format_schema
from html_schema_converter.llm.openai_client import OpenAIClient

def run_example():
    """Run an example of the HTML to Data Schema Converter."""
    print("HTML to Data Schema Converter Example")
    print("====================================")
    
    # Initialize OpenAI client
    try:
        llm_client = OpenAIClient()
    except ValueError as e:
        print(f"Error: {e}")
        print("Please set your OpenAI API key as an environment variable: OPENAI_API_KEY")
        return
    
    # URL to process (example Wikipedia page with tables)
    url = "https://en.wikipedia.org/wiki/List_of_programming_languages"
    print(f"Extracting tables from {url}")
    
    # Extract tables
    tables_info = html_reader_agent(url)
    
    if tables_info["status"] != "Success":
        print(f"Error: {tables_info['status']}")
        return
    
    print(f"Found {tables_info['tables_count']} tables")
    
    # Analyze tables to find the main one
    print("Analyzing tables to find the main content table...")
    llm_analysis = analyze_tables_with_llm(tables_info, llm_client)
    
    # For demonstration, just use the first table
    print("For this example, we'll use the first table:")
    selected_table = tables_info["tables"][0]
    print(f"  Columns: {selected_table['column_count']}")
    print(f"  Headers: {', '.join(selected_table['headers'][:5])}...")
    
    # Generate schema
    print("\nGenerating schema...")
    schema = generate_datascheme_with_llm(selected_table, llm_client)
    
    # Format and display output
    json_output = format_schema(schema, "json")
    print("\nGenerated Schema (JSON):")
    print(json_output)
    
    # Save output
    output_file = "example_schema.json"
    with open(output_file, "w") as f:
        f.write(json_output)
    
    print(f"\nSchema saved to {output_file}")
    
    # Display metrics
    if "metrics" in schema:
        print("\nPerformance Metrics:")
        for key, value in schema["metrics"].items():
            print(f"  {key}: {value}")

if __name__ == "__main__":
    run_example()