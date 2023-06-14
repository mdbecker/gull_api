from fastapi import HTTPException
from gull_api.main import get_api, process_request, create_llm_request_model, convert_request_to_cli_command, load_cli_json
from pydantic import BaseModel
from subprocess import TimeoutExpired
from typing import Dict, Any
from unittest import mock
import gull_api.main as main  # Import the main module, helps with mocking
import json
import pytest


cli_json = {'LLaMA-7B': [{'default': 'models/7B/ggml-model.bin',
       'description': 'Specify the path to the LLaMA model file (e.g., '
		      'models/7B/ggml-model.bin).',
       'hidden': True,
       'long': '--model',
       'name': 'Model',
       'nargs': 1,
       'required': True,
       'short': '-m',
       'type': 'str'},
      {'default': False,
       'description': 'Run the program in instruction mode, which is '
		      'particularly useful when working with Alpaca '
		      'models.',
       'long': '--instruct',
       'name': 'Instruct mode',
       'short': '-ins',
       'type': 'bool'},
      {'default': 128,
       'description': 'Set the number of tokens to predict when '
		      'generating text. Adjusting this value can '
		      'influence the length of the generated text.',
       'long': '--n_predict',
       'max': 2048,
       'min': 1,
       'name': 'Maximum length',
       'nargs': 1,
       'short': '-n',
       'step': 10,
       'type': 'int'},
      {'description': 'Provide a prompt',
       'long': '--prompt',
       'name': 'Prompt',
       'nargs': 1,
       'required': True,
       'type': 'str'},
      {'description': 'Specify one or multiple reverse prompts to '
		      'pause text generation and switch to interactive '
		      'mode.',
       'long': '--reverse-prompt',
       'name': 'Stop sequences',
       'nargs': 1,
       'required': False,
       'short': '-r',
       'type': 'str'},
      {'default': 0.8,
       'description': 'Adjust the randomness of the generated text.',
       'long': '--temp',
       'max': 1,
       'min': 0,
       'name': 'Temperature',
       'nargs': 1,
       'type': 'float'},
      {'default': 0.9,
       'description': 'Limit the next token selection to a subset of '
		      'tokens with a cumulative probability above a '
		      'threshold P.',
       'long': '--top_p',
       'max': 1,
       'min': 0,
       'name': 'Top P',
       'nargs': 1,
       'type': 'float'}]} 

def test_get_api():

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

    api_json = get_api(cli_json)
    assert api_json == expected_api_json

@pytest.fixture
def llm_request(scope='session'):
    return create_llm_request_model(cli_json)


def test_create_llm_request_model_is_a_pydantic_model(llm_request):
    assert issubclass(llm_request, BaseModel)


def test_llm_request_model_has_model_field(llm_request):
    assert "Model" in llm_request.__fields__


def test_llm_request_model_model_field_description(llm_request):
    assert llm_request.__fields__["Model"].field_info.description == 'Specify the path to the LLaMA model file (e.g., models/7B/ggml-model.bin).'


def test_llm_request_model_model_field_default(llm_request):
    assert llm_request.__fields__["Model"].field_info.default == 'models/7B/ggml-model.bin'


def test_llm_request_model_model_field_type(llm_request):
    assert llm_request.__fields__["Model"].outer_type_ == str


def test_llm_request_model_instruct_mode_field_type(llm_request):
    assert llm_request.__fields__["Instruct mode"].outer_type_ == bool


def test_llm_request_model_max_length_field_type(llm_request):
    assert issubclass(llm_request.__fields__["Maximum length"].outer_type_, int)


def test_llm_request_model_prompt_field_type(llm_request):
    assert llm_request.__fields__["Prompt"].outer_type_ == str


def test_llm_request_model_stop_sequences_field_type(llm_request):
    assert llm_request.__fields__["Stop sequences"].outer_type_ == str


def test_llm_request_model_temperature_field_type(llm_request):
    assert issubclass(llm_request.__fields__["Temperature"].outer_type_, float)


def test_llm_request_model_top_p_field_type(llm_request):
    assert issubclass(llm_request.__fields__["Top P"].outer_type_, float)


def test_post_llm_validates_correctly(llm_request):
    sample_request_data = {
        "Model": "models/7B/ggml-model.bin",
        "Instruct mode": False,
        "Maximum length": 100,
        "Prompt": "Hello, world!",
        "Stop sequences": "stop",
        "Temperature": 0.6,
        "Top P": 0.8
    }
    validated_request = llm_request(**sample_request_data)

    assert isinstance(validated_request, llm_request)
    assert validated_request.dict() == sample_request_data

def test_post_llm_raises_exception_for_invalid_data(llm_request):
    invalid_request_data = {"nonexistent_field": "some value"}

    with pytest.raises(ValueError):
        validated_request = llm_request(**invalid_request_data)


@mock.patch('subprocess.run')
def test_process_request_valid_run(mock_run):
    # TODO: Update with realistic output
    class MockCompletedProcess:
        def __init__(self, stdout='', stderr='', returncode=0):
            self.stdout = stdout.encode('utf-8')
            self.stderr = stderr.encode('utf-8')
            self.returncode = returncode

    mock_run.return_value = MockCompletedProcess(stdout='{"response": "OK"}')

    sample_request = BaseModel()
    result = process_request(sample_request, cli_json)

    assert result == {"response": "OK"}

@mock.patch('subprocess.run')
def test_process_request_valid_run_with_errors(mock_run):
    # TODO: Update with realistic output
    class MockCompletedProcess:
        def __init__(self, stdout='', stderr='', returncode=0):
            self.stdout = stdout.encode('utf-8')
            self.stderr = stderr.encode('utf-8')
            self.returncode = returncode

    mock_run.return_value = MockCompletedProcess(stderr='Error occurred', returncode=1)

    sample_request = BaseModel()
    with pytest.raises(HTTPException) as exc_info:
        result = process_request(sample_request, cli_json)

    assert exc_info.value.status_code == 400
    assert exc_info.value.detail == 'Error occurred'

@mock.patch('subprocess.run')
def test_process_request_timeout(mock_run):
    mock_run.side_effect = TimeoutExpired(cmd='', timeout=60)

    sample_request = BaseModel()
    with pytest.raises(HTTPException) as exc_info:
        result = process_request(sample_request, cli_json)

    assert exc_info.value.status_code == 408
    assert exc_info.value.detail == 'Request timed out.'


def test_load_cli_json():
    # Set up the mock file data
    mock_file_data = {"key": "value"}
    mock_file_contents = json.dumps(mock_file_data)

    # Set up the mock file object
    m = mock.mock_open(read_data=mock_file_contents)

    # Mock the 'open' call
    with mock.patch('builtins.open', m):
        # Call the function you're testing
        result = load_cli_json()

    # Make sure the function behaved as expected
    m.assert_called_once_with("cli.json", "r")
    assert result == mock_file_data

def test_convert_request_to_cli_command_with_bool():
    cli_json = {
        "LLaMA-7B": [{
            "name": "test_param",
            "type": "bool",
            "flag": "--test",
            "description": "test parameter",
        }]
    }
    request = create_llm_request_model(cli_json)(test_param=True)
    assert convert_request_to_cli_command(request, cli_json) == ["./main", "--test"]

def test_convert_request_to_cli_command_with_non_bool():
    cli_json = {
        "LLaMA-7B": [{
            "name": "test_param",
            "type": "str",
            "flag": "--test",
            "description": "test parameter",
        }]
    }
    request = create_llm_request_model(cli_json)(test_param="value")
    assert convert_request_to_cli_command(request, cli_json) == ["./main", "--test", "value"]

# @pytest.mark.asyncio
# @pytest.mark.parametrize("invalid_request_data", [
#     {"Top P": 0.5},  # Missing required field "Prompt"
#     {"Prompt": "Once upon a time", "Top P": -0.5},  # Invalid value for "Top P"
#     {"Prompt": "Once upon a time", "Top P": 1.5},  # Invalid value for "Top P"
# ])
# async def test_post_llm_invalid_request(invalid_request_data):
#     # Replace this URL with the actual URL of your running API
#     api_url = "http://localhost:8000/llm"
# 
#     async with httpx.AsyncClient() as client:
#         response = await client.post(api_url, json=invalid_request_data)
# 
#     assert response.status_code == 422  # Unprocessable Entity


# Mocked cli.json data
mock_cli_json = {
    "LLaMA-7B": [
        {"name": "test_param", "type": "str", "flag": "--test", "description": "Test parameter"}
    ]
}

# Mocked request data
mock_request = {"test_param": "test_value"}

@mock.patch('gull_api.main.executor')
def test_post_llm(mock_executor):
    # Call the function with the mocked request data
    result = main.post_llm(request=mock_request, cli_json=mock_cli_json)
    
    # Assert create_llm_request_model was called with the correct arguments
    LLMRequest = main.create_llm_request_model(mock_cli_json)
    validated_request = LLMRequest(**mock_request)
    mock_executor.submit.assert_called_once_with(main.process_request, validated_request, mock_cli_json)
    
    # Assert the result is the Future returned by executor.submit
    assert result == mock_executor.submit.return_value
