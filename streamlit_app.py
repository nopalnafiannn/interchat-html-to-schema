#!/usr/bin/env python
"""
HTML to Schema Converter - Streamlit UI

This application provides a user-friendly interface for converting HTML tables to structured data schemas.
It allows users to input data from URLs, HTML file uploads, or Kaggle datasets, and guides them through
the conversion process step by step.
"""

import os
import io
import streamlit as st
import pandas as pd
from dotenv import load_dotenv

from html_schema_converter.main import SchemaConverter
from html_schema_converter.agents.schema_refiner import refine_schema
from html_schema_converter.utils.formatters import SchemaFormatter
from html_schema_converter.models.schema import Schema

# Load environment variables from .env file
load_dotenv()

# Set page configuration
st.set_page_config(
    page_title="InterChat HTML-to-Schema Converter",
    page_icon="🔄",
    layout="wide",
)

# Initialize session state variables if they don't exist
if "step" not in st.session_state:
    st.session_state.step = 1
if "input_type" not in st.session_state:
    st.session_state.input_type = None
if "url" not in st.session_state:
    st.session_state.url = ""
if "uploaded_file" not in st.session_state:
    st.session_state.uploaded_file = None
if "tables_info" not in st.session_state:
    st.session_state.tables_info = None
if "selected_table_index" not in st.session_state:
    st.session_state.selected_table_index = None
if "schema" not in st.session_state:
    st.session_state.schema = None
if "schema_accepted" not in st.session_state:
    st.session_state.schema_accepted = False
if "output_format" not in st.session_state:
    st.session_state.output_format = "json"
if "output_filename" not in st.session_state:
    st.session_state.output_filename = "schema"
if "csv_files" not in st.session_state:
    st.session_state.csv_files = None
if "selected_csv" not in st.session_state:
    st.session_state.selected_csv = None
if "converter" not in st.session_state:
    st.session_state.converter = SchemaConverter()
if "api_key_set" not in st.session_state:
    st.session_state.api_key_set = bool(os.environ.get("OPENAI_API_KEY"))


def reset_session():
    """Reset session state to initial values."""
    st.session_state.step = 1
    st.session_state.input_type = None
    st.session_state.url = ""
    st.session_state.uploaded_file = None
    st.session_state.tables_info = None
    st.session_state.selected_table_index = None
    st.session_state.schema = None
    st.session_state.schema_accepted = False
    st.session_state.output_format = "json"
    st.session_state.output_filename = "schema"
    st.session_state.csv_files = None
    st.session_state.selected_csv = None


def set_input_type(input_type):
    """Set the input type and move to the next step."""
    st.session_state.input_type = input_type
    st.session_state.step = 2


def process_url(url):
    """Process URL input and move to table selection or schema display."""
    with st.spinner("Analyzing URL and extracting tables..."):
        if "kaggle.com/datasets" in url:
            # Handle Kaggle URL
            result = st.session_state.converter.kaggle_integration.process_dataset(url)
            if result["status"] == "Success":
                st.session_state.csv_files = result["csv_files"]
                st.session_state.step = 2.5  # Step for CSV selection
            else:
                st.error(f"Error processing Kaggle dataset: {result['message']}")
        else:
            # Handle regular URL
            tables_info = st.session_state.converter.html_reader.read_from_url(url)
            if tables_info["status"] == "Success" and tables_info["tables_count"] > 0:
                st.session_state.tables_info = tables_info
                st.session_state.step = 3  # Table selection step
            else:
                st.error("No tables found in the HTML document or error occurred.")


def process_uploaded_file(uploaded_file):
    """Process uploaded HTML file and move to table selection."""
    with st.spinner("Analyzing uploaded file and extracting tables..."):
        # Save the uploaded file to a temporary file
        temp_file_path = f"/tmp/{uploaded_file.name}"
        with open(temp_file_path, "wb") as f:
            f.write(uploaded_file.getbuffer())
        
        # Extract tables from the temporary file
        tables_info = st.session_state.converter.html_reader.read_from_file(temp_file_path)
        
        # Clean up
        os.remove(temp_file_path)
        
        if tables_info["status"] == "Success" and tables_info["tables_count"] > 0:
            st.session_state.tables_info = tables_info
            st.session_state.step = 3  # Table selection step
        else:
            st.error("No tables found in the uploaded file or error occurred.")


def select_csv_file(csv_index):
    """Select a CSV file from Kaggle dataset and process it."""
    selected_csv = st.session_state.csv_files[csv_index]
    st.session_state.selected_csv = selected_csv
    
    with st.spinner("Generating schema from CSV file..."):
        schema_result = st.session_state.converter.kaggle_integration.generate_csv_schema(selected_csv)
        
        if "schema" in schema_result and schema_result["schema"] is not None:
            st.session_state.schema = schema_result["schema"]
            st.session_state.step = 4  # Schema review step
        else:
            st.error(f"Error generating schema: {schema_result.get('error', 'Unknown error')}")


def select_table(table_index):
    """Select a table and generate schema from it."""
    st.session_state.selected_table_index = table_index
    selected_table = st.session_state.tables_info["tables"][table_index]
    
    with st.spinner("Generating schema from selected table..."):
        schema_result = st.session_state.converter.schema_generator.generate_schema(selected_table)
        
        if "schema" in schema_result and schema_result["schema"] is not None:
            # Add metadata based on input type
            if st.session_state.input_type == "url":
                schema_result["schema"].metadata["source_url"] = st.session_state.url
            elif st.session_state.input_type == "file":
                schema_result["schema"].metadata["source_file"] = st.session_state.uploaded_file.name
            
            schema_result["schema"].metadata["table_index"] = table_index
            st.session_state.schema = schema_result["schema"]
            st.session_state.step = 4  # Schema review step
        else:
            st.error(f"Error generating schema: {schema_result.get('error', 'Unknown error')}")


def process_feedback(feedback):
    """Process user feedback and refine the schema."""
    with st.spinner("Refining schema based on feedback..."):
        # Format the current schema to JSON for the refiner
        formatter = SchemaFormatter()
        schema_json = formatter.format_schema(st.session_state.schema, "json")
        
        # Refine the schema using the feedback
        refined_schema_str = refine_schema(schema_json, feedback)
        
        try:
            # Parse the refined schema back into a Schema object
            refined_schema = formatter.parse_schema_from_string(refined_schema_str, "json")
            
            # Preserve the original metadata
            refined_schema.metadata = st.session_state.schema.metadata
            
            # Update the schema in session state
            st.session_state.schema = refined_schema
        except Exception as e:
            st.error(f"Error refining schema: {str(e)}")


def accept_schema():
    """Mark the schema as accepted and move to output format selection."""
    st.session_state.schema_accepted = True
    st.session_state.step = 5  # Output format selection step


def set_output_format(format_type):
    """Set the output format and move to filename selection."""
    st.session_state.output_format = format_type
    st.session_state.step = 6  # Filename selection step


def set_output_filename(filename):
    """Set the output filename and move to download step."""
    st.session_state.output_filename = filename
    st.session_state.step = 7  # Download step


def get_download_filename():
    """Get the full filename with appropriate extension based on output format."""
    filename = st.session_state.output_filename
    if st.session_state.output_format == "json" and not filename.endswith(".json"):
        return f"{filename}.json"
    elif st.session_state.output_format == "yaml" and not (filename.endswith(".yaml") or filename.endswith(".yml")):
        return f"{filename}.yaml"
    elif st.session_state.output_format == "txt" and not filename.endswith(".txt"):
        return f"{filename}.txt"
    return filename


def get_schema_content():
    """Get the schema content as a string in the selected format."""
    if not st.session_state.schema:
        return ""
    
    formatter = SchemaFormatter()
    return formatter.format_schema(st.session_state.schema, st.session_state.output_format)


# Application UI
def main():
    st.title("InterChat HTML-to-Schema Converter")
    
    # Check for API key
    if not st.session_state.api_key_set:
        st.warning("OpenAI API key not found. Please enter your API key.")
        api_key = st.text_input("OpenAI API Key", type="password")
        if st.button("Set API Key"):
            if api_key:
                os.environ["OPENAI_API_KEY"] = api_key
                st.session_state.api_key_set = True
                st.success("API key set successfully!")
                st.rerun()
            else:
                st.error("Please enter a valid API key.")
        return
    
    # Progress bar showing the current step
    progress_percentage = (st.session_state.step / 7) * 100
    st.progress(progress_percentage / 100)
    
    # Step 1: Select input type
    if st.session_state.step == 1:
        st.subheader("Step 1: Select Input Type")
        
        col1, col2, col3 = st.columns(3)
        with col1:
            if st.button("URL Input", use_container_width=True):
                set_input_type("url")
        with col2:
            if st.button("HTML File Upload", use_container_width=True):
                set_input_type("file")
        with col3:
            if st.button("Kaggle Dataset", use_container_width=True):
                set_input_type("kaggle")
    
    # Step 2: Provide input based on selected type
    elif st.session_state.step == 2:
        st.subheader(f"Step 2: Provide {st.session_state.input_type.capitalize()} Input")
        
        if st.session_state.input_type == "url":
            st.text_input("Enter URL", key="url_input", help="URL containing HTML tables or a Kaggle dataset URL")
            if st.button("Process URL"):
                if st.session_state.url_input:
                    st.session_state.url = st.session_state.url_input
                    process_url(st.session_state.url)
                else:
                    st.error("Please enter a URL.")
        
        elif st.session_state.input_type == "file":
            uploaded_file = st.file_uploader("Upload HTML file", type=["html", "htm"])
            if uploaded_file is not None:
                st.session_state.uploaded_file = uploaded_file
                if st.button("Process HTML File"):
                    process_uploaded_file(uploaded_file)
        
        elif st.session_state.input_type == "kaggle":
            st.text_input("Enter Kaggle Dataset URL", key="kaggle_url_input", 
                         help="Example: https://www.kaggle.com/datasets/username/dataset-name")
            if st.button("Process Kaggle Dataset"):
                if st.session_state.kaggle_url_input:
                    st.session_state.url = st.session_state.kaggle_url_input
                    process_url(st.session_state.url)
                else:
                    st.error("Please enter a Kaggle dataset URL.")
        
        # Back button
        if st.button("Back"):
            st.session_state.step = 1
    
    # Step 2.5: Select CSV file from Kaggle dataset
    elif st.session_state.step == 2.5:
        st.subheader("Step 2.5: Select CSV File")
        
        if st.session_state.csv_files:
            st.write("Available CSV files in the Kaggle dataset:")
            
            # Display CSV files as selectable options
            for i, csv_file in enumerate(st.session_state.csv_files):
                filename = os.path.basename(csv_file)
                if st.button(f"{i+1}. {filename}", key=f"csv_{i}"):
                    select_csv_file(i)
        else:
            st.error("No CSV files found in the dataset.")
            if st.button("Back"):
                st.session_state.step = 2
    
    # Step 3: Table selection
    elif st.session_state.step == 3:
        st.subheader("Step 3: Select Table")
        
        if st.session_state.tables_info:
            tables = st.session_state.tables_info["tables"]
            st.write(f"Found {len(tables)} tables in the document. Please select one:")
            
            # Analyze tables to find the most relevant one
            with st.spinner("Analyzing tables..."):
                analysis_result = st.session_state.converter.table_analyzer.analyze_tables(st.session_state.tables_info)
            
            # Display recommendation if available
            if analysis_result["status"] == "Success" and analysis_result.get("recommendation"):
                rec = analysis_result["recommendation"]
                if rec["table_index"] is not None:
                    st.info(f"Recommended: Table {rec['table_index']+1} - {rec['reasoning']}")
            
            # Display tables with previews
            for i, table in enumerate(tables):
                with st.expander(f"Table {i+1}: {table.get('caption', 'No caption')} ({table['column_count']} columns, {table['row_count']} rows)"):
                    # Create DataFrame for preview
                    headers = table['headers']
                    sample_data = table['sample_data']
                    
                    if sample_data:
                        # Adjust sample_data if it doesn't match headers length
                        adjusted_data = []
                        for row in sample_data:
                            if len(row) < len(headers):
                                adjusted_data.append(row + [''] * (len(headers) - len(row)))
                            elif len(row) > len(headers):
                                adjusted_data.append(row[:len(headers)])
                            else:
                                adjusted_data.append(row)
                        
                        df = pd.DataFrame(adjusted_data, columns=headers)
                        st.dataframe(df)
                    else:
                        st.write("No sample data available.")
                    
                    if st.button(f"Select Table {i+1}", key=f"table_{i}"):
                        select_table(i)
            
            # Back button
            if st.button("Back"):
                st.session_state.step = 2
        else:
            st.error("No table information available.")
            if st.button("Back to Start"):
                reset_session()
    
    # Step 4: Schema review
    elif st.session_state.step == 4:
        st.subheader("Step 4: Review Generated Schema")
        
        if st.session_state.schema:
            # Format and display the schema
            formatter = SchemaFormatter()
            schema_text = formatter.format_schema(st.session_state.schema, "json")
            
            # Display schema in a code block
            st.code(schema_text, language="json")
            
            # Also show a table view of the schema columns
            columns = st.session_state.schema.columns
            if columns:
                col_data = [
                    {
                        "Name": col.name,
                        "Type": col.type,
                        "Description": col.description,
                        "Nullable": "Yes" if col.nullable else "No"
                    }
                    for col in columns
                ]
                st.write("Schema columns:")
                st.table(pd.DataFrame(col_data))
            
            # Feedback options
            st.write("Is this schema correct and suitable for your needs?")
            col1, col2 = st.columns(2)
            with col1:
                if st.button("Yes, Accept Schema"):
                    accept_schema()
            
            with col2:
                if st.button("No, I Want to Provide Feedback"):
                    st.session_state.show_feedback = True
            
            # Display feedback form if requested
            if st.session_state.get("show_feedback", False):
                st.write("Please provide your feedback on how to improve the schema:")
                feedback = st.text_area(
                    "Your feedback", 
                    height=150,
                    help="Examples: 'Column X should be numeric instead of string', 'Add description for column Y', etc."
                )
                
                if st.button("Submit Feedback"):
                    if feedback:
                        process_feedback(feedback)
                        st.session_state.show_feedback = False
                        st.success("Schema refined based on your feedback!")
                        st.rerun()
                    else:
                        st.error("Please provide feedback before submitting.")
            
            # Back button
            if st.button("Back"):
                if st.session_state.input_type == "kaggle" and st.session_state.csv_files:
                    st.session_state.step = 2.5  # Back to CSV selection
                else:
                    st.session_state.step = 3  # Back to table selection
        else:
            st.error("No schema available to review.")
            if st.button("Back to Start"):
                reset_session()
    
    # Step 5: Output format selection
    elif st.session_state.step == 5:
        st.subheader("Step 5: Select Output Format")
        
        col1, col2, col3 = st.columns(3)
        with col1:
            if st.button("JSON", use_container_width=True):
                set_output_format("json")
        with col2:
            if st.button("YAML", use_container_width=True):
                set_output_format("yaml")
        with col3:
            if st.button("TXT", use_container_width=True):
                set_output_format("txt")
        
        # Back button
        if st.button("Back"):
            st.session_state.step = 4
            st.session_state.schema_accepted = False
    
    # Step 6: Filename selection
    elif st.session_state.step == 6:
        st.subheader("Step 6: Enter Output Filename")
        
        st.write(f"Selected format: {st.session_state.output_format.upper()}")
        
        filename = st.text_input(
            "Enter filename (without extension)",
            value="schema",
            help="The appropriate extension will be added automatically"
        )
        
        if st.button("Continue"):
            if filename:
                set_output_filename(filename)
            else:
                st.error("Please enter a filename.")
        
        # Back button
        if st.button("Back"):
            st.session_state.step = 5
    
    # Step 7: Download
    elif st.session_state.step == 7:
        st.subheader("Step 7: Download Schema")
        
        if st.session_state.schema:
            # Get schema content
            schema_content = get_schema_content()
            filename = get_download_filename()
            
            # Provide download button
            st.download_button(
                label=f"Download Schema as {st.session_state.output_format.upper()}",
                data=schema_content,
                file_name=filename,
                mime={
                    "json": "application/json",
                    "yaml": "application/x-yaml",
                    "txt": "text/plain"
                }.get(st.session_state.output_format, "text/plain")
            )
            
            # Display the final schema
            st.write("Final Schema:")
            st.code(schema_content, language="json" if st.session_state.output_format == "json" else "yaml")
            
            # Option to start over
            if st.button("Convert Another HTML Table"):
                reset_session()
        else:
            st.error("No schema available to download.")
            if st.button("Back to Start"):
                reset_session()
    
    # Footer
    st.markdown("---")
    st.markdown("InterChat HTML-to-Schema Converter | Made with ❤️ using Streamlit")


if __name__ == "__main__":
    main()