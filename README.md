# interchat-html-to-schema

# HTML Dataset Analyzer

A tool that analyzes HTML files to extract dataset information using AI.

## Features

- Extract dataset column information from HTML files
- Process HTML content with or without tables
- Use AI to infer data schema from context
- Handle large files by chunking based on token limits
- Export results in JSON format

## Installation

1. Clone the repository:
   ```bash
   git clone https://github.com/yourusername/html-dataset-analyzer.git
   cd html-dataset-analyzer
   ```

2. Create a virtual environment (optional but recommended):
   ```bash
   python -m venv venv
   
   # On Windows
   venv\Scripts\activate
   
   # On macOS/Linux
   source venv/bin/activate
   ```

3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

4. Create a `.env` file in the project root with your OpenAI API key:
   ```
   OPENAI_API_KEY=your-api-key-here
   ```

## Usage

### Command Line Interface

```bash
# Basic usage
python -m src.main --file path/to/your/file.html

# Specify output file
python -m src.main --file path/to/your/file.html --output results.json

# Use raw HTML (default) or cleaned text
python -m src.main --file path/to/your/file.html --raw  # Use raw HTML
python -m src.main --file path/to/your/file.html  # Uses raw HTML by default

# Set maximum tokens per chunk
python -m src.main --file path/to/your/file.html --max-tokens 5000
```

### Python API

```python
from src.main import analyze_html_file

# Analyze a file
results = analyze_html_file(
    file_path="path/to/your/file.html",
    output_path="results.json",
    use_raw_html=True,
    max_chunk_tokens=7000
)

# Access results
print(results["final_summary"])
```

## Project Structure

```
html-dataset-analyzer/              # Root directory
├── .env                           # Environment variables (API keys, etc.)
├── README.md                      # Project documentation
├── requirements.txt               # Project dependencies
├── setup.py                       # Package setup information
├── .gitignore                     # Git ignore file
├── src/                           # Source code directory
│   ├── __init__.py                # Makes src a package
│   ├── main.py                    # Entry point for the application
│   ├── analyzer/                  # Core analyzer functionality
│   │   ├── __init__.py
│   │   ├── html_processor.py      # HTML cleaning and processing
│   │   ├── token_splitter.py      # Tokenization and chunking
│   │   └── schema_extractor.py    # Schema extraction logic
│   ├── ai/                        # AI-related functionality
│   │   ├── __init__.py
│   │   ├── client.py              # OpenAI client setup
│   │   └── prompts.py             # Prompt templates
│   └── utils/                     # Utility functions
│       ├── __init__.py
│       ├── file_utils.py          # File handling utilities
│       └── logging_utils.py       # Logging functionality
└── tests/                         # Tests directory
    ├── __init__.py
    └── ...
```

## Development

### Setting Up for Development

1. Install development dependencies:
   ```bash
   pip install -r requirements.txt
   ```

2. Run tests:
   ```bash
   pytest
   ```

3. Format code:
   ```bash
   black src/
   ```

### Adding New Features

1. Create new modules in the appropriate directory
2. Update the main entry point if needed
3. Add tests for new functionality
4. Update documentation

## License

MIT

## Acknowledgements

- [OpenAI](https://openai.com/) for providing the AI models
- [Beautiful Soup](https://www.crummy.com/software/BeautifulSoup/) for HTML parsing
- [tiktoken](https://github.com/openai/tiktoken) for token counting