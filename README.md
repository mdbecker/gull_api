# GULL-API

![Docker Publish](https://github.com/mdbecker/gull_api/actions/workflows/docker-publish.yml/badge.svg?event=release)
![Test](https://github.com/mdbecker/gull_api/actions/workflows/test.yml/badge.svg)


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

### Docker Test Mode

To build and run the Docker container in test mode, use the following commands:

```bash
docker build -t gull-api .
docker run -v $(pwd)/data:/app/data -v $(pwd)/example_cli.json:/app/cli.json -p 8000:8000 gull-api
```

In test mode, an included script echo_args.sh is used instead of a real LLM. This script echoes the arguments it receives, which can be helpful for local testing.


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

### Example Requests

```bash
curl -X POST "http://localhost:8000/llm" -H  "accept: application/json" -H  "Content-Type: application/json" -d "{\"Instruct mode\":false, \"Maximum length\":256, \"Prompt\":\"Hello, world\", \"Stop sequences\":\"Goodbye, world\", \"Temperature\":0.7, \"Top P\":0.95}"
curl -X GET "http://localhost:8000/api" -H "accept: application/json" | python -mjson.tool
```

### Example CLI JSON

An example CLI JSON file is provided in the repository as `example_cli.json`. This file provides an example of the expected structure for defining the command-line arguments for the LLM.

## License

See LICENSE
