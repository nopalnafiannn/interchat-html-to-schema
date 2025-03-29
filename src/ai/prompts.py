"""
Prompts Module
------------
Templates for AI prompts used in the application
"""

# Updated prompt for analyzing raw HTML chunks directly with dataset inference
RAW_HTML_ANALYSIS_PROMPT = """
You are a dataset schema extraction expert. The following contains HTML code that may be about a specific dataset.

First, determine if this HTML contains:
A) Actual data tables with column headers and data rows
B) Only metadata/description about a dataset without the actual data table

Your task is to identify the primary data columns for this dataset.

If you find ACTUAL DATA TABLES (case A):
- Focus on extracting column names directly from the table headers
- Infer data types and descriptions from the sample data

If you find ONLY DATASET DESCRIPTION without tables (case B):
- Identify if this is a well-known dataset (Titanic, Iris, Netflix Stock, etc.)
- List ALL standard columns for this dataset using their EXACT COLUMN NAMES
- Do not omit any standard columns for well-known datasets

HTML content:
{chunk}

Please output:
1. Whether this HTML contains actual data tables or just dataset descriptions
2. The dataset type if identifiable (e.g., Titanic, Iris, Stock data)
3. A complete list of column names with their exact names as used in the dataset
4. The likely data type for each column
5. A brief description for each column
"""

IMPROVED_COMBINE_PROMPT = """
You are a data schema integration expert. Below are analyses of different chunks of HTML that may be about a dataset.

Your task is to consolidate these analyses into one comprehensive data schema. Your schema must ONLY include the primary data columns and EXCLUDE all metadata, UI elements, and auxiliary information.

Individual chunk analyses:
{results}

Please provide:
1. ONLY the core data columns that would appear in the main data table or visualization
2. For each column:
   - A clear, concise description
   - The data type
   - Any observed patterns, formats, or constraints

Core principles to follow:
- INCLUDE: numerical values, categories, dates, and measurements that are the focus of analysis
- EXCLUDE: user data, metadata, profile information, administrative fields, UI elements
- If a column seems peripheral or metadata-related, exclude it
- Focus on columns that would appear in a clean dataset ready for analysis

Example of core data columns for a stock dataset: Date, Open, High, Low, Close, Volume
Example of core data columns for a Pokemon dataset: id, name, type, hp, attack, defense, speed

Format your response as a clean, well-structured schema that includes ONLY the essential data columns.
"""

# Prompt for extracting dataset information from a description
DESCRIPTION_ANALYSIS_PROMPT = """
You are a helpful assistant skilled in understanding datasets. Please analyze the following description 
and extract structured information about the dataset it describes.

Description:
{description}

Please extract and provide:
1. The dataset title/name
2. A complete list of column names
3. Descriptions for each column
4. The likely data types for each column
5. Any additional metadata such as row count, data sources, etc.

Format your response as a structured list that clearly identifies all columns and their properties.
"""

# Prompt for improving schema extraction
SCHEMA_IMPROVEMENT_PROMPT = """
You are a data schema refinement expert. I have extracted a preliminary data schema from HTML content, 
but it may have issues or be incomplete.

Current schema information:
{schema}

Please improve this schema by:
1. Removing any duplicate columns
2. Standardizing column names (consistent capitalization, removing special characters)
3. Improving descriptions to be more precise and informative
4. Ensuring each column has an appropriate data type
5. Identifying any missing columns that are likely part of this dataset based on the existing columns
6. Adding relationships between columns if they are apparent
7. State how many column found
8. List all column found with number points

If this appears to be a well-known dataset (like Titanic, Iris, Housing, MNIST, etc.), ensure the schema matches the standard schema for that dataset.

Format your response as a clean, well-structured schema that completely replaces the current one.
"""

# New prompt for checking schema quality
SCHEMA_QUALITY_CHECK_PROMPT = """
You are a data schema quality assurance expert. Review the following data schema extracted from an HTML document:

{schema}

Please evaluate this schema for:
1. Completeness - Are there obvious missing columns?
2. Accuracy - Do the data types match the column descriptions?
3. Clarity - Are the descriptions clear and informative?
4. Standardization - Are the column names consistent in format?
5. Relationships - Are any important relationships between columns missing?

For each issue found, please provide:
- The specific problem
- Why it's a problem
- A suggested correction

If this appears to be a well-known dataset (like Titanic, Iris, Housing, MNIST, etc.), check if the schema matches the standard schema for that dataset.

If the schema appears to be high quality, please confirm this.
"""