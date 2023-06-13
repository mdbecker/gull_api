# GULL-API

GULL-API is a web application backend that can be used to run Large Language Models (LLMs). The interface between the front-end and the back-end is a JSON REST API.

## Features

- Exposes a `/api` route that returns a JSON file describing the parameters of the LLM.
- Provides a `/llm` route that accepts POST requests with JSON payloads to run the LLM with the specified parameters.

## Installation

### Using Docker

1. Build the Docker image:

   ```
   docker build -t gull-api .
   ```

2. Run the Docker container:

   ```
   docker run -p 8000:8000 gull-api
   ```

The API will be available at `http://localhost:8000`.

### Local Installation

1. Clone the repository:

   ```
   git clone https://github.com/yourusername/gull-api.git
   ```

2. Change to the project directory:

   ```
   cd gull-api
   ```

3. Install the dependencies:

   ```
   pip install poetry
   poetry install
   ```

4. Run the application:

   ```
   uvicorn gull_api.main:app --host 0.0.0.0 --port 8000
   ```

The API will be available at `http://localhost:8000`.

## Usage

### `/api` Route

Send a GET request to the `/api` route to retrieve a JSON file describing the parameters of the LLM:

```
GET http://localhost:8000/api
```

### `/llm` Route

Send a POST request to the `/llm` route with a JSON payload containing the LLM parameters:

```
POST http://localhost:8000/llm
Content-Type: application/json

{
  "Prompt": "Once upon a time",
  "Top P": 0.5
}
```

## License

See LICENSE
