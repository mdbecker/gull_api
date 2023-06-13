import json
from fastapi.testclient import TestClient
import pytest
import httpx
from main import app, load_cli_json, create_llm_request_model

client = TestClient(app)

def test_get_api():
    response = client.get("/api")
    assert response.status_code == 200

    cli_json = load_cli_json()
    expected_api_json = {
        "LLaMA-7B": [
            {
                "name": "Instruct mode",
                "type": "bool",
                "default": False,
                "description": "Run the program in instruction mode, which is particularly useful when working with Alpaca models."
            },
            {
                "name": "Maximum length",
                "type": "int",
                "default": 128,
                "description": "Set the number of tokens to predict when generating text. Adjusting this value can influence the length of the generated text.",
                "min": 1,
                "max": 2048,
                "step": 10
            },
            {
                "name": "Prompt",
                "type": "str",
                "required": True,
                "description": "Provide a prompt"
            },
            {
                "name": "Stop sequences",
                "type": "str",
                "description": "Specify one or multiple reverse prompts to pause text generation and switch to interactive mode."
            },
            {
                "name": "Temperature",
                "type": "float",
                "default": 0.8,
                "description": "Adjust the randomness of the generated text.",
                "min": 0,
                "max": 1,
                "step": 0.01
            },
            {
                "name": "Frequency penalty",
                "type": "float",
                "default": 1.1,
                "description": "Control the repetition of token sequences in the generated text.",
                "min": 0,
                "max": 2,
                "step": 0.01
            },
            {
                "name": "Top P",
                "type": "float",
                "default": 0.9,
                "description": "Limit the next token selection to a subset of tokens with a cumulative probability above a threshold P.",
                "min": 0,
                "max": 1,
                "step": 0.01
            }
        ]
    }

    assert response.json() == expected_api_json

def test_post_llm():
    request_data = {
        "Prompt": "Once upon a time",
        "Top P": 0.5
    }

    # Replace this URL with the actual URL of your running API
    api_url = "http://localhost:8000/llm"

    async with httpx.AsyncClient() as client:
        response = await client.post(api_url, json=request_data)

    assert response.status_code == 200
    # Add more assertions based on the expected response content

@pytest.mark.parametrize("invalid_request_data", [
    {"Top P": 0.5},  # Missing required field "Prompt"
    {"Prompt": "Once upon a time", "Top P": -0.5},  # Invalid value for "Top P"
    {"Prompt": "Once upon a time", "Top P": 1.5},  # Invalid value for "Top P"
])
def test_post_llm_invalid_request(invalid_request_data):
    # Replace this URL with the actual URL of your running API
    api_url = "http://localhost:8000/llm"

    async with httpx.AsyncClient() as client:
        response = await client.post(api_url, json=invalid_request_data)

    assert response.status_code == 422  # Unprocessable Entity
