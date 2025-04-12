# Docker Usage Instructions

This document explains how to use Docker with the InterChat HTML-to-Schema Converter project.

## Prerequisites

- Docker installed on your system
- Docker Compose installed on your system (optional, but recommended)
- OpenAI API key

## Using Docker

### Building the Docker Image

```bash
docker build -t html-to-schema .
```

### Running with Docker

Run the container with your OpenAI API key:

```bash
docker run -e OPENAI_API_KEY=your-openai-api-key -v $(pwd)/output:/app/output html-to-schema --url https://example.com/table.html --output /app/output/schema.json --format json
```

### Using the Interactive Mode

```bash
docker run -it -e OPENAI_API_KEY=your-openai-api-key -v $(pwd)/output:/app/output --entrypoint python html-to-schema interactive_converter.py
```

## Using Docker Compose

Create a `.env` file in the project root with your API keys:

```
OPENAI_API_KEY=your-openai-api-key
KAGGLE_USERNAME=your-kaggle-username
KAGGLE_SECRET_KEY=your-kaggle-key
```

### Running with Docker Compose

```bash
docker-compose run --rm html-to-schema --url https://example.com/table.html --output /app/output/schema.json --format json
```

### Using the Interactive Mode with Docker Compose

```bash
docker-compose run --rm --entrypoint python html-to-schema interactive_converter.py
```

## Volume Mounts

- The entire project directory is mounted at `/app` inside the container
- The `./output` directory is specifically mounted to `/app/output` for saving results

## Environment Variables

- `OPENAI_API_KEY`: Your OpenAI API key (required)
- `KAGGLE_USERNAME`: Your Kaggle username (optional, for Kaggle integration)
- `KAGGLE_SECRET_KEY`: Your Kaggle API key (optional, for Kaggle integration)