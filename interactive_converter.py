#!/usr/bin/env python
import sys
import os
from dotenv import load_dotenv
from html_schema_converter.main import SchemaConverter
from html_schema_converter.config import config
from html_schema_converter.agents.schema_refiner import refine_schema
from html_schema_converter.utils.formatters import SchemaFormatter

def load_api_key():
    """Load OpenAI API key from .env or prompt user."""
    # Try to load from .env file
    load_dotenv()
    
    api_key = os.environ.get("OPENAI_API_KEY")
    
    # If still not found, ask user
    if not api_key:
        print("\nOpenAI API key not found in environment or .env file.")
        api_key = input("Please enter your OpenAI API key: ").strip()
        if api_key:
            os.environ["OPENAI_API_KEY"] = api_key
        else:
            print("No API key provided. Exiting.")
            sys.exit(1)
    
    return api_key

def get_human_feedback(schema_text, output_format):
    """
    Request human feedback on the generated schema.
    
    Args:
        schema_text: The generated schema text to review
        output_format: The format of the schema (json, yaml, text)
    
    Returns:
        String with human feedback or None if satisfied
    """
    print("\n" + "=" * 50)
    print("Generated Schema Review")
    print("=" * 50)
    print(f"\n{schema_text}\n")
    
    print("Is this schema correct and suitable for your needs?")
    satisfaction = input("Enter 'y' if satisfied, or 'n' to provide feedback: ").strip().lower()
    
    if satisfaction == 'y':
        return None
    
    print("\nPlease provide your feedback on how to improve the schema.")
    print("Examples: 'Column X should be numeric instead of string', 'Add description for column Y', etc.")
    feedback = input("\nYour feedback: ").strip()
    
    return feedback

def feedback_loop(converter, original_schema, output_format):
    """
    Implement a feedback loop for refining the schema.
    
    Args:
        converter: SchemaConverter instance
        original_schema: Original Schema object
        output_format: Output format (json, yaml, text)
    
    Returns:
        Final refined schema
    """
    formatter = SchemaFormatter()
    current_schema = original_schema
    iteration = 1
    
    while True:
        # Format the current schema to show the user
        schema_text = formatter.format_schema(current_schema, output_format)
        
        # Get human feedback
        feedback = get_human_feedback(schema_text, output_format)
        
        # If user is satisfied, break the loop
        if not feedback:
            print("\nGreat! You are satisfied with the schema.")
            break
        
        print(f"\nRefining schema based on feedback (Iteration {iteration})...")
        
        # Convert schema to string format for refining
        schema_str = formatter.format_schema(current_schema, "json" if output_format == "text" else output_format)
        
        # Refine the schema using the schema_refiner
        refined_schema_str = refine_schema(schema_str, feedback)
        
        # Parse the refined schema back into a Schema object
        refined_schema = formatter.parse_schema_from_string(refined_schema_str, output_format)
        
        # Preserve the original metadata
        refined_schema.metadata = current_schema.metadata
        
        # Update current schema for next iteration
        current_schema = refined_schema
        iteration += 1
    
    return current_schema

def interactive_main():
    """Interactive version of the CLI that prompts for input."""
    print("=" * 50)
    print("HTML to Data Schema Converter for InterChat")
    print("=" * 50)
    
    # Load API key
    api_key = load_api_key()
    print("API key loaded successfully!")
    
    # Create a menu
    print("\nSelect an input type:")
    print("1. URL (web page)")
    print("2. Local HTML file")
    print("3. Kaggle dataset")
    
    choice = input("\nEnter your choice (1-3): ").strip()
    
    converter = SchemaConverter()
    
    try:
        if choice == "1":
            url = input("\nEnter the URL of the web page with tables: ").strip()
            print(f"\nProcessing URL: {url}")
            schema = converter.from_url(url)
        elif choice == "2":
            file_path = input("\nEnter the path to your HTML file: ").strip()
            print(f"\nProcessing file: {file_path}")
            schema = converter.from_file(file_path)
        elif choice == "3":
            kaggle_url = input("\nEnter the Kaggle dataset URL: ").strip()
            print(f"\nProcessing Kaggle dataset: {kaggle_url}")
            schema = converter.from_kaggle(kaggle_url)
        else:
            print("Invalid choice. Please enter 1, 2, or 3.")
            return 1
        
        # Ask for output format
        print("\nSelect output format:")
        print("1. JSON (default)")
        print("2. YAML")
        print("3. Text (pretty-printed JSON)")
        
        format_choice = input("\nEnter your choice (1-3, default=1): ").strip()
        
        if format_choice == "2":
            output_format = "yaml"
            output_file = "generated_schema.yaml"
        elif format_choice == "3":
            output_format = "text"
            output_file = "generated_schema.txt"
        else:
            output_format = "json"
            output_file = "generated_schema.json"
        
        # Run the feedback loop to refine the schema
        refined_schema = feedback_loop(converter, schema, output_format)
        
        # Ask if they want to change the output filename
        custom_filename = input(f"\nDefault output file: {output_file}\nPress Enter to use this or type a new filename: ").strip()
        
        if custom_filename:
            output_file = custom_filename
        
        # Save the refined schema
        converter.save_schema(refined_schema, output_file, output_format)
        converter.print_metrics_report()
        
        print(f"\nComplete! Refined schema saved to {output_file}")
        
    except Exception as e:
        print(f"\nError: {str(e)}")
        return 1
    
    return 0

if __name__ == "__main__":
    sys.exit(interactive_main())