FROM python:3.8-slim

WORKDIR /app

COPY requirements.txt .

RUN pip install --no-cache-dir -r requirements.txt

COPY . .

RUN pip install -e .

# Set environment variables placeholder - users should override these
ENV OPENAI_API_KEY="your-api-key"
ENV KAGGLE_USERNAME="your-kaggle-username" 
ENV KAGGLE_SECRET_KEY="your-kaggle-key"

# Expose the port if the application has a web interface
# EXPOSE 8000

# Command to run the application
ENTRYPOINT ["python", "-m", "html_schema_converter.main"]
CMD ["--help"]