import os
from pathlib import Path
from typing import List
from pydantic import BaseModel
from bs4 import BeautifulSoup
from agents import Agent, Runner, function_tool
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# --- Data Models ---
class VariableSchema(BaseModel):
    name: str
    description: str
    data_type: str

class DatasetSchema(BaseModel):
    variables: List[VariableSchema]

# --- Core Functions ---
@function_tool
def parse_html_table(file_path: str) -> str:
    """Extracts first HTML table from local file"""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            soup = BeautifulSoup(f.read(), 'html.parser')
            table = soup.find('table')
            return str(table) if table else "No table found in HTML file"
    except Exception as e:
        return f"File error: {str(e)}"

def save_schema_json(schema: DatasetSchema, output_path: str):
    """Save schema to JSON file"""
    if not isinstance(schema, DatasetSchema):
        raise TypeError("Expected a DatasetSchema instance")

    with open(output_path, 'w') as f:
        f.write(schema.model_dump_json(indent=2))  # Updated to use model_dump_json
    print(f"\nSchema saved to {output_path}")

# --- AI Agents ---
schema_agent = Agent(
    name="Schema Extractor",
    model="gpt-4o-mini",
    instructions="""Analyze HTML table structure and return structured JSON data conforming to this format:
{
  "variables": [
    {
      "name": "string",
      "description": "string",
      "data_type": "string"
    }
  ]
}""",
    tools=[parse_html_table],
    output_type=DatasetSchema
)

validation_agent = Agent(
    name="Schema Validator",
    model="gpt-4o-mini",
    instructions="""Present schema and incorporate user feedback:
    1. Display current schema
    2. Process text corrections
    3. Return final validated schema""",
    handoffs=[schema_agent]
)

# --- Workflow ---
async def main_workflow():
    # Get input file path from user
    html_path = input("Enter path to HTML file: ").strip()

    if not Path(html_path).exists():
        print("Error: File not found")
        return

    # Extract and process table schema using GPT-4o Mini model
    raw_table = await Runner.run(schema_agent, input=html_path)

    # Debugging step: Check raw output from agent
    print(f"Raw table output: {raw_table}")

    # Ensure raw_table is valid before proceeding
    if isinstance(raw_table, str):
        print("Error: Agent returned raw text instead of structured data.")
        return

    schema = await Runner.run(
        schema_agent,
        input=f"HTML TABLE: {raw_table}"
    )

    # Handle cases where schema is returned as a string instead of a Pydantic model
    if isinstance(schema.final_output, str):
        try:
            # Attempt to parse the string into a Pydantic model
            schema.final_output = DatasetSchema.parse_raw(schema.final_output)
        except Exception as e:
            print(f"Error parsing schema: {e}")
            return

    # Human validation step
    print("\n=== Generated Schema ===")
    for var in schema.final_output.variables:
        print(f"- {var.name}: {var.description} ({var.data_type})")

    feedback = input("\nAccept schema? (Y/n/edit): ").strip()

    if feedback.lower() not in {'y', 'yes', ''}:
        try:
            schema = await Runner.run(
                validation_agent,
                input=f"SCHEMA: {schema.final_output.model_dump_json()}\nFEEDBACK: {feedback}"
            )
        except Exception as e:
            print(f"Error during validation step: {e}")
            return

    # Save output as JSON file
    output_path = Path(html_path).stem + "_schema.json"
    save_schema_json(schema.final_output, output_path)

if __name__ == "__main__":
    import asyncio
    asyncio.run(main_workflow())


