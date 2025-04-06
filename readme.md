# HTML to Data Schema Converter

A specialized tool that automatically extracts and generates structured data schemas from HTML tables for use with InterChat.

## Overview

The HTML to Data Schema Converter eliminates a critical barrier to entry for InterChat users by automating the creation of data schemas. InterChat is a powerful generative visual analytics system that requires structured data schemas to function effectively, and this tool bridges the gap by converting HTML tables into these schemas.

## Features

- Extract tables from HTML files or web pages
- Process datasets from Kaggle
- Use LLM to intelligently identify main tables in multi-table documents
- Generate high-quality data schemas with accurate data types and descriptions
- Support for both table formats:
  - Tables with both column names and sample data
  - Tables with column names only
- Output schemas in multiple formats (JSON, YAML, text)
- Interactive user feedback for schema refinement
- Performance metrics tracking

## Installation

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