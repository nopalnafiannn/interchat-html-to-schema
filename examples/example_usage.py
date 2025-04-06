"""Example usage of the HTML to Data Schema Converter."""

from html_schema_converter import SchemaConverter

def example_url_conversion():
    """Example of converting HTML from a URL."""
    # URL with a data table (this is just an example URL)
    url = "https://en.wikipedia.org/wiki/List_of_countries_by_GDP_(nominal)"
    
    # Initialize the converter
    converter = SchemaConverter()
    
    print(f"Converting tables from URL: {url}")
    print("This will use LLM to analyze tables and generate schema.")
    print("Follow the interactive prompts to select a table...")
    
    # Generate schema from URL
    schema = converter.from_url(url)
    
    # Save in different formats
    converter.save_schema(schema, "example_schema.json", "json")
    converter.save_schema(schema, "example_schema.yaml", "yaml")
    
    # Print metrics
    converter.print_metrics_report()
    
    # Print schema details
    print(f"\nGenerated schema has {len(schema)} columns:")
    for col in schema.schema:
        print(f"  - {col.column_name} ({col.type}): {col.description}")

def example_kaggle_conversion():
    """Example of converting a CSV from a Kaggle dataset."""
    # Kaggle dataset URL (this is just an example URL)
    kaggle_url = "https://www.kaggle.com/datasets/kaggle/us-baby-names"
    
    # Initialize the converter
    converter = SchemaConverter()
    
    print(f"Converting Kaggle dataset: {kaggle_url}")
    print("This requires valid Kaggle credentials to be configured.")
    print("Follow the interactive prompts to select a CSV file...")
    
    # Generate schema from Kaggle dataset
    schema = converter.from_kaggle(kaggle_url)
    
    # Save schema
    converter.save_schema(schema, "kaggle_example_schema.json")
    
    # Print metrics
    converter.print_metrics_report()

def main():
    """Run the examples."""
    print("HTML to Data Schema Converter - Example Usage")
    print("=" * 50)
    
    # Uncomment the example you want to run
    example_url_conversion()
    # example_kaggle_conversion()

if __name__ == "__main__":
    main()