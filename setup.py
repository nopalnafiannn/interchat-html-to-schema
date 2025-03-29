from setuptools import setup, find_packages

setup(
    name="html-dataset-analyzer",
    version="0.1.0",
    description="Extracts dataset information from HTML files using AI",
    author="Your Name",
    author_email="your.email@example.com",
    packages=find_packages(),
    install_requires=[
        "openai>=1.0.0",
        "tiktoken>=0.5.1",
        "python-dotenv>=1.0.0",
        "beautifulsoup4>=4.12.2",
        "argparse>=1.4.0",
    ],
    entry_points={
        'console_scripts': [
            'analyze-html=src.main:main',
        ],
    },
)