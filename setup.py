from setuptools import setup, find_packages

setup(
    name="html_schema_converter",
    version="0.1.0",
    description="Convert HTML tables to structured data schemas for InterChat",
    author="Your Name",
    author_email="your.email@example.com",
    packages=find_packages(),
    install_requires=[
        "requests",
        "beautifulsoup4",
        "pandas",
        "pyyaml",
        "openai",
        "psutil",
        "kaggle",
    ],
    entry_points={
        "console_scripts": [
            "html-schema=html_schema_converter.main:cli_main",
        ],
    },
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
    ],
    python_requires=">=3.8",
)