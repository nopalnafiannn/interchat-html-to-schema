# html_schema_converter/setup.py
from setuptools import setup, find_packages

setup(
    name="html_schema_converter",
    version="0.1.0",
    packages=find_packages(),
    install_requires=[
        "requests>=2.25.0",
        "beautifulsoup4>=4.9.0",
        "pandas>=1.0.0",
        "openai>=1.0.0",
        "pyyaml>=5.4.0",
        "psutil>=5.8.0",
        "kaggle>=1.5.0",
    ],
    entry_points={
        "console_scripts": [
            "html-schema-converter=html_schema_converter.main:main",
        ],
    },
    author="Your Name",
    author_email="your.email@example.com",
    description="Convert HTML tables to InterChat data schemas",
    keywords="html, data, schema, interchat",
    url="https://github.com/yourusername/html_schema_converter",
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Intended Audience :: Developers",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
    ],
)