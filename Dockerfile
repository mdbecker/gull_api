# Use the minimal Python 3.10 base container
FROM python:3.10-slim

# Set the working directory
WORKDIR /app

# Copy the pyproject.toml file to the working directory
COPY pyproject.toml .

# Install the dependencies
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir poetry && \
    poetry config virtualenvs.create false && \
    poetry install --no-dev --no-interaction --no-ansi

# Copy the application code to the working directory
COPY gull_api/ ./gull_api

# Copy the mock LLM cli app to the working directory
COPY echo_args.sh ./

# Expose the port the app runs on
EXPOSE 8000

# Start the application
CMD ["uvicorn", "gull_api.main:app", "--host", "0.0.0.0", "--port", "8000"]
