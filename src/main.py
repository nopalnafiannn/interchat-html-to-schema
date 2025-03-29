#!/usr/bin/env python3
"""
HTML Dataset Analyzer - Main entry point
---------------------------------------
Extracts dataset information from HTML files using AI
"""

import argparse
import json
from pathlib import Path

from src.analyzer.token_splitter import split_text_by_tokens
from src.analyzer.schema_extractor import analyze_chunks, combine_results
from src.utils.file_utils import read_file, save_json
from src.utils.logging_utils import setup_logger

# Set up logger
logger = setup_logger()

def analyze_html_file(file_path, output_path=None, max_chunk_tokens=7000, model="gpt-3.5-turbo"):
    """
    Main function to analyze an HTML file and extract dataset information.
    
    Args:
        file_path: Path to the HTML file
        output_path: Optional path to save the results (JSON format)
        max_chunk_tokens: Maximum tokens per chunk
        model: OpenAI model to use for analysis
    
    Returns:
        Dictionary with analysis results or None if error
    """
    logger.info(f"Analyzing file: {file_path}")
    
    # Read the HTML file
    html_content = read_file(file_path)
    if not html_content:
        logger.error(f"Failed to read file: {file_path}")
        return None
    
    # Split HTML directly into chunks without BeautifulSoup cleaning
    chunks, total_tokens = split_text_by_tokens(html_content, max_tokens=max_chunk_tokens)
    logger.info(f"Number of chunks created: {len(chunks)}")
    logger.info(f"Total token count: {total_tokens}")

    # Process each chunk
    chunk_results = analyze_chunks(chunks, model=model)
    
    # Combine results
    final_schema_summary = combine_results(chunk_results, model=model)
    logger.info("--- Final Combined Data Schema Summary ---")
    logger.info(final_schema_summary)
    
    # Check if no dataset was found
    if final_schema_summary.startswith("ERROR:"):
        logger.error(final_schema_summary)
        if output_path:
            error_results = {
                "file_analyzed": str(file_path),
                "error": final_schema_summary,
                "success": False
            }
            save_json(error_results, output_path)
            logger.info(f"Error results saved to {output_path}")
        
        return {
            "error": final_schema_summary,
            "success": False
        }
    
    # Save results if output path is provided
    if output_path:
        results = {
            "file_analyzed": str(file_path),
            "token_count": total_tokens,
            "chunk_count": len(chunks),
            "individual_analyses": chunk_results,
            "final_summary": final_schema_summary,
            "success": True
        }
        
        success = save_json(results, output_path)
        if success:
            logger.info(f"Results saved to {output_path}")
    
    return {
        "final_summary": final_schema_summary,
        "individual_analyses": chunk_results,
        "success": True
    }

def main():
    """Command line interface for HTML dataset analyzer"""
    parser = argparse.ArgumentParser(description='Extract dataset information from HTML files')
    parser.add_argument('--file', '-f', type=str, help='Path to HTML file')
    parser.add_argument('--output', '-o', type=str, help='Path to save output JSON')
    parser.add_argument('--max-tokens', '-t', type=int, default=7000, help='Maximum tokens per chunk')
    parser.add_argument('--model', '-m', type=str, default="gpt-3.5-turbo", 
                        help='OpenAI model to use (default: gpt-3.5-turbo)')
    
    args = parser.parse_args()
    
    # If no file path is provided, prompt the user
    file_path = args.file
    if not file_path:
        file_path = input("Enter the path to the HTML file: ")
    
    # Generate a default output path if not provided
    output_path = args.output
    if not output_path:
        file_name = Path(file_path).stem
        output_path = f"{file_name}_analysis.json"
    
    # Run the analysis
    result = analyze_html_file(
        file_path=file_path, 
        output_path=output_path,
        max_chunk_tokens=args.max_tokens,
        model=args.model
    )
    
    # Display appropriate message based on result
    if result and "error" in result:
        print("\n" + "="*80)
        print(result["error"])
        print("="*80 + "\n")
    elif result and result.get("success", False):
        print("\n" + "="*80)
        print("Analysis completed successfully.")
        print(f"Results saved to: {output_path}")
        print("="*80 + "\n")
    else:
        print("\n" + "="*80)
        print("Analysis failed. Check logs for details.")
        print("="*80 + "\n")

if __name__ == "__main__":
    main()