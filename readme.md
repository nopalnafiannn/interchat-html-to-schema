# HTML to Data Schema Converter for InterChat

**[MILESTONE 3 ASSIGNMENT - AI PM COURSE, CARNEGIE MELLON UNIVERSITY]**

A specialized tool designed to automatically extract and generate structured data schemas from HTML tables for use with the InterChat visual analytics system.

## Overview

The HTML to Data Schema Converter eliminates a critical barrier to entry for InterChat users by automating the creation of data schemas. InterChat is a powerful generative visual analytics system that requires structured data schemas to function effectively, and this tool bridges the gap by converting HTML tables into these schemas.

This converter uses a multi-agent architecture powered by BeautifulSoup for HTML parsing and Large Language Models for intelligent schema generation, drastically reducing the time and technical knowledge required to prepare data for InterChat.

## Refined Workflow Architecture

In milestone 3, we have refined our approach with an enhanced workflow that better handles multiple input sources and processing paths:

![HTML to Data Schema Converter Workflow](images/images_workflow.jpg)

### Key Workflow Improvements

Our refined architecture now features:

1. **Dual Processing Branches**
   - HTML Processing Branch: Handles direct HTML inputs from files or URLs
   - Kaggle Processing Branch: Specialized pathway for working with Kaggle datasets

2. **Intelligent Table Selection**
   - LLM Agent now assists in identifying the most relevant table when multiple tables are present
   - User can verify and select the appropriate table for processing

3. **Enhanced Schema Generation**
   - Two-path schema generation based on available data:
     - Schema Generator 1: Processes tables with complete column and value data
     - Schema Generator 2: Works with limited data (column names only)

4. **Feedback Processing System**
   - Added user feedback integration (marked as "Not Developed Yet" in current iteration)
   - Framework for human-in-the-loop refinement

## Features

- **Multiple Input Sources**
  - Web URLs with HTML tables
  - Local HTML files
  - Kaggle datasets (CSV files)

- **Intelligent Table Analysis**
  - Automatic table detection with BeautifulSoup
  - LLM-assisted table selection for multi-table documents
  - Support for both standard HTML tables and div-based tables

- **Smart Schema Generation**
  - Data type inference from table contents
  - Meaningful column descriptions using LLM
  - Confidence scores for inferred types
  - Handling both complete data (headers + values) and partial data (headers only)

- **Output Options**
  - JSON format
  - YAML format
  - Text (pretty-printed JSON)
  - Preview before saving

- **User Experience**
  - Interactive step-by-step interface
  - Command-line interface for automation
  - Performance metrics reporting

## Installation

### Prerequisites

- Python 3.8 or higher
- OpenAI API key (for LLM functionality)
- Kaggle API credentials (optional, for Kaggle integration)

### Setup

```bash
# Clone the repository
git clone https://github.com/nopalnafiannn/interchat-html-to-schema.git
cd html-schema-converter

# Install the package
pip install -e .

# Install required dependencies
pip install -r requirements.txt
```

## Configuration

### API Keys

Set up your API keys using any of these methods:

1. **Environment Variables**
   ```bash
   # OpenAI API Key
   export OPENAI_API_KEY="your-openai-api-key"
   
   # Kaggle Credentials (optional)
   export KAGGLE_USERNAME="your-kaggle-username"
   export KAGGLE_SECRET_KEY="your-kaggle-api-key"
   ```

2. **.env File**
   Create a `.env` file in the project root:
   ```
   OPENAI_API_KEY=your-openai-api-key
   KAGGLE_USERNAME=your-kaggle-username
   KAGGLE_SECRET_KEY=your-kaggle-api-key
   ```

3. **Interactive Input**
   The interactive version can prompt for API keys if not found.

## Usage

### Interactive Mode (Recommended)

The interactive mode guides you through the process step by step:

```bash
python interactive_converter.py
```

The interactive interface will:
1. Guide you through input selection (URL, file, or Kaggle dataset)
2. Load and analyze tables
3. Help you select the most relevant table
4. Generate the schema
5. Allow you to choose output format and filename

### Command Line Interface

For automation or direct use:

```bash
# Process a URL
python -m html_schema_converter.main --url https://example.com/page-with-table.html

# Process a local HTML file
python -m html_schema_converter.main --file path/to/local/file.html

# Process a Kaggle dataset
python -m html_schema_converter.main --kaggle https://www.kaggle.com/datasets/username/dataset-name

# Specify output format (default is JSON)
python -m html_schema_converter.main --url https://example.com/page-with-table.html --format yaml

# Specify output file
python -m html_schema_converter.main --url https://example.com/page-with-table.html --output my_schema.json
```

## System Architecture

The system uses a multi-agent architecture with specialized components:

### Key Components

1. **HTML Reader Agent**
   - Uses BeautifulSoup to extract table structures
   - Identifies headers, sample data rows, and metadata
   - Handles both standard tables and div-based tables

2. **Table Analyzer Agent**
   - Evaluates multiple tables using LLM
   - Creates descriptive prompts about each table
   - Recommends the most suitable table for data analysis

3. **Schema Generator Agent**
   - Two pathways based on data completeness:
     - Schema Generator 1: Uses both column names AND sample data
     - Schema Generator 2: Uses ONLY column names with confidence scores
   - Generates structured schema with column types and descriptions

4. **Output Formatting**
   - Converts Schema objects to JSON/YAML/Text
   - Customizable output filenames
   - Performance metrics reporting

### Data Flow

1. User provides HTML source (URL, file, or Kaggle dataset)
2. HTML Reader extracts tables and metadata
3. Table Analyzer helps select the most relevant table (if multiple exist)
4. Schema Generator creates appropriate LLM prompts based on available data
5. LLM generates schema components (data types and descriptions)
6. Output is formatted, displayed, and saved

## Performance Metrics

The system tracks several key metrics for each run:

- **Processing Latency**: Time from input to schema generation
- **Memory Usage**: Memory consumed during processing
- **LLM Token Usage**: Prompt and completion tokens for each LLM call
- **Total Processing Cost**: Estimated API cost (based on token usage)

## Current Implementation Status

The current implementation includes:
- ✅ HTML Reader Agent
- ✅ Table Analyzer Agent
- ✅ Schema Generator (types 1 & 2)
- ✅ Interactive and CLI interfaces
- ✅ Kaggle integration
- ✅ Performance metrics
- ✅ Multiple output formats

**Note**: The human feedback loop for schema refinement (Schema Generator 3) described in the PRD is not yet implemented in the current version.

## Next Steps

Our development roadmap includes:

- 🔄 **Optimize token usage** - Refining prompts and implementing caching strategies to reduce API costs
- 🔄 **Working on testing automation** - Building comprehensive test suite for reliability across diverse inputs
- 🔄 **Integrate with UX team with current design system** - Ensuring visual consistency with InterChat's interface
- 🔄 **Working on last part of human feedback function** - Implementing the feedback processing system for iterative refinement

## Example Output

```json
{
  "schema": [
    {
      "column_name": "Date",
      "type": "date",
      "description": "Trading date for the stock"
    },
    {
      "column_name": "Open",
      "type": "number",
      "description": "Opening price of the stock for the day"
    },
    {
      "column_name": "High",
      "type": "number",
      "description": "Highest price of the stock during the day"
    }
    // Additional columns...
  ]
}
```

## Troubleshooting

### Common Issues

- **API Key Errors**: Ensure your OpenAI API key is correctly set in the environment or .env file
- **No Tables Found**: Verify the HTML source contains proper table elements
- **Schema Generation Fails**: Check the complexity of the table; very large tables may exceed token limits

### Requirements

For the Python packages required by this project, see `requirements.txt`:
```
requests>=2.28.0
beautifulsoup4>=4.11.0
pandas>=1.4.0
pyyaml>=6.0
openai>=1.0.0
psutil>=5.9.0
kaggle>=1.5.12
python-dotenv>=1.0.0
```

## Project Structure

```
html_schema_converter/            # Main package directory
├── main.py                       # Entry point
├── config.py                     # Configuration management
├── agents/                       # Agent modules
│   ├── html_reader.py            # HTML parsing agent
│   ├── table_analyzer.py         # Table analysis agent
│   └── schema_generator.py       # Schema generation agent
├── models/                       # Data models
│   └── schema.py                 # Schema data structures
├── utils/                        # Utility functions
│   ├── metrics.py                # Metrics collection
│   ├── kaggle.py                 # Kaggle integration
│   └── formatters.py             # Output formatting
└── llm/                          # LLM integration
    └── openai_client.py          # OpenAI client
```

## Team Member
- Naufal Nafian
- Praneetha Pratapa
- Akanksha Janna
- Ruofan Wu

## License

MIT License

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.
