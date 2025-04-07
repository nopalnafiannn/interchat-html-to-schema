## The interchat HTML project for course AI for PM

This project automates the generation of InterChat-compatible data schemas from HTML tables and URLs using a multi-agent system built on the OpenAI Agent SDK.  It extracts table structures with BeautifulSoup and employs LLM-driven prompt chaining to generate column names, types, and descriptions. The system supports iterative feedback, outputs JSON/YAML formats, and dramatically reduces schema preparation time.

InterChat is a powerful generative visual analytics system that requires structured data schemas to function effectively, and this tool bridges the gap by converting HTML tables into these schemas.

## Features

- Extract tables from HTML files or web pages
- Process datasets from Kaggle
- Generate high-quality data schemas with accurate data types and descriptions
- Support for both table formats:
  - Tables with both column names and sample data
  - Tables with column names only
- Output schemas in multiple formats (JSON, YAML, text)
- Interactive user feedback for schema refinement
- Performance metrics tracking

# Workflow

**1. HTML Table Extraction & Cleaning (Python-based)**
Input: User uploads an HTML file or provides a URL.
The system - Parses all table elements, Cleans data (remove null/NaN, standardize formats), Validate if the HTML contains any usable tables and Present a UI for table selection if multiple are found. 

**Tools:** Table parsing/cleaning	Python (BeautifulSoup, pandas)

**2. Metadata Generation (LLM Agent)**
Once a table is selected and cleaned, it’s passed to a Metadata Generation Agent using the OpenAI Agent SDK.
This agent analyzes the data to generate: Cleaned/formatted column names, Data types (e.g., string, integer, float, date) and Semantic column descriptions

Notes any low-confidence areas or potential discrepancies

**Tools:** Metadata generation	OpenAI LLM Agent

**3. Feedback & Refinement (LLM Agent)**
A second Refinement Agent (LLM) takes user input to iteratively improve the schema:
Users can suggest edits in plain language (“make date a string”, “add unit to salary”)
The agent applies changes and regenerates the schema metadata

**Tools:** MHuman feedback/refinement	OpenAI LLM Agent

**4. Schema Assembly (Python-based)**
Final metadata is passed to a Python module that Formats it into InterChat-compatible JSON and YAML schemas and Validates structure against InterChat's required schema

**Tools:** Schema assembly	Python (json, yaml)

**5. Output & Metrics Logging (Python-based)**
Output: JSON and YAML schema files available for download or upload to InterChat

**Metrics Logged:** Latency, Token usage (for each LLM agent call), Estimated API cost per run



## How to install this project. 

```bash
# Clone the repository
git clone https://github.com/nopalnafiannn/interchat-html-to-schema
cd html-schema-converter

# Install the package
pip install -e .
```

## Configuration

API keys and configurations can be set in the following ways:
1. Environment variables
2. Google Colab secrets (if using Colab)
3. Configuration file (`config.yaml`)

Required API keys:
- OpenAI API key (`OPENAI_API_KEY`)
- Kaggle credentials (`KAGGLE_USERNAME`, `KAGGLE_SECRET_KEY`) - only if using Kaggle integration

## Usage

### Command Line

```bash
# Convert HTML from a URL
html-schema --url https://example.com/page-with-table.html

# Convert a local HTML file
html-schema --file path/to/local/file.html

# Process a Kaggle dataset
html-schema --kaggle https://www.kaggle.com/datasets/username/dataset-name
```

### Python API

```python
from html_schema_converter import SchemaConverter

# Initialize the converter
converter = SchemaConverter()

# Generate schema from a URL
schema = converter.from_url("https://example.com/page-with-table.html")

# Save the schema
converter.save_schema(schema, "my_schema.json", format="json")
```

## Development

```bash
# Install development dependencies
pip install -e ".[dev]"

# Run tests
pytest

# Check code style
flake8
```

## License

MIT License


# How to tweak this project for your own use.
# Found a bug?
# Known issues (work in progress)

# Like this project?
Contact for more info - linkedin etc










