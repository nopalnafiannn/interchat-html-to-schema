#!/usr/bin/env python
import sys
import os
from dotenv import load_dotenv
from html_schema_converter.main import SchemaConverter
from html_schema_converter.config import config
from html_schema_converter.agents.schema_refiner import refine_schema
from html_schema_converter.utils.formatters import SchemaFormatter
from html_schema_converter.models.schema import Schema

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
    try:
        satisfaction = input("Enter 'y' if satisfied, or 'n' to provide feedback: ").strip().lower()
    except EOFError:
        # In non-interactive mode, assume satisfied
        print("Non-interactive environment detected. Assuming schema is satisfactory.")
        return None
    
    if satisfaction == 'y':
        return None
    
    print("\nPlease provide your feedback on how to improve the schema.")
    print("Examples: 'Column X should be numeric instead of string', 'Add description for column Y', etc.")
    
    try:
        feedback = input("\nYour feedback: ").strip()
        return feedback
    except EOFError:
        # In non-interactive mode, provide default feedback
        print("Non-interactive environment detected. No feedback provided.")
        return None

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
        
        try:
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
        except EOFError:
            # Handle non-interactive environment
            print("\nNon-interactive environment detected. Skipping feedback loop.")
            break
    
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
    
    try:
        choice = input("\nEnter your choice (1-3): ").strip()
    except EOFError:
        # Use a default choice for non-interactive environments
        choice = "1"
        print("Non-interactive environment detected. Using URL input as default.")
    
    converter = SchemaConverter()
    
    try:
        if choice == "1":
            try:
                url = input("\nEnter the URL of the web page with tables: ").strip()
            except EOFError:
                # For testing purposes, use a default URL
                url = "https://www.kaggle.com/datasets/rzgiza/pokdex-for-all-1025-pokemon-w-text-description"
                print(f"Using default URL for testing: {url}")
            
            print(f"\nProcessing URL: {url}")
            schema = converter.from_url(url)
        elif choice == "2":
            try:
                file_path = input("\nEnter the path to your HTML file: ").strip()
            except EOFError:
                # Default to a sample file if available
                file_path = "list_countries_wiki.html"
                print(f"Using default file: {file_path}")
            
            print(f"\nProcessing file: {file_path}")
            schema = converter.from_file(file_path)
        elif choice == "3":
            try:
                kaggle_url = input("\nEnter the Kaggle dataset URL: ").strip()
            except EOFError:
                # Default Kaggle URL for testing
                kaggle_url = "https://www.kaggle.com/datasets/rzgiza/pokdex-for-all-1025-pokemon-w-text-description"
                print(f"Using default Kaggle URL: {kaggle_url}")
            
            print(f"\nProcessing Kaggle dataset: {kaggle_url}")
            try:
                schema = converter.from_kaggle(kaggle_url)
            except EOFError:
                # Handle case where interactive input is not available
                print("Interactive input not available. Using alternative approach for Kaggle dataset.")
                from test_pokedex import non_interactive_kaggle_process
                schema = non_interactive_kaggle_process(kaggle_url)
                if not schema:
                    raise ValueError("Failed to process Kaggle dataset in non-interactive mode.")
        else:
            print("Invalid choice. Please enter 1, 2, or 3.")
            return 1
        
        # Ask for output format
        print("\nSelect output format:")
        print("1. JSON (default)")
        print("2. YAML")
        print("3. Text (pretty-printed JSON)")
        
        try:
            format_choice = input("Enter your choice (1-3): ").strip()
        except EOFError:
            # Default to JSON in non-interactive mode
            format_choice = "1"
            print("Using default JSON format in non-interactive mode.")
        
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
        
        try:
            # Ask if they want to change the output filename
            custom_filename = input(f"\nDefault output file: {output_file}\nPress Enter to use this or type a new filename: ").strip()
            
            if custom_filename:
                output_file = custom_filename
        except EOFError:
            # Use default in non-interactive mode
            print(f"Using default output file: {output_file}")
        
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