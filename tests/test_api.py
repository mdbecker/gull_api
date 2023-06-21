from fastapi import HTTPException
from gull_api.main import get_api, create_llm_request_model, convert_request_to_cli_command, load_cli_json
from pydantic import BaseModel
from typing import Dict, Any
from unittest import mock
import gull_api.main as main  # Import the main module, helps with mocking
import json
import pytest
import subprocess
from asyncio import TimeoutError

cli_json = {'LLaMA-7B': [{'default': 'models/7B/ggml-model.bin',
       'description': 'Specify the path to the LLaMA model file (e.g., '
		      'models/7B/ggml-model.bin).',
       'hidden': True,
       'name': 'Model',
       'nargs': 1,
       'required': True,
       'flag': '-m',
       'type': 'str'},
      {'default': False,
       'description': 'Run the program in instruction mode, which is '
		      'particularly useful when working with Alpaca '
		      'models.',
       'name': 'Instruct mode',
       'flag': '-ins',
       'type': 'bool'},
      {'default': 128,
       'description': 'Set the number of tokens to predict when '
		      'generating text. Adjusting this value can '
		      'influence the length of the generated text.',
       'max': 2048,
       'min': 1,
       'name': 'Maximum length',
       'nargs': 1,
       'flag': '-n',
       'step': 10,
       'type': 'int'},
      {'description': 'Provide a prompt',
       'flag': '--prompt',
       'name': 'Prompt',
       'nargs': 1,
       'required': True,
       'type': 'str'},
      {'description': 'Specify one or multiple reverse prompts to '
		      'pause text generation and switch to interactive '
		      'mode.',
       'name': 'Stop sequences',
       'nargs': 1,
       'required': False,
       'flag': '-r',
       'type': 'str'},
      {'default': 0.8,
       'description': 'Adjust the randomness of the generated text.',
       'flag': '--temp',
       'max': 1,
       'min': 0,
       'name': 'Temperature',
       'nargs': 1,
       'type': 'float'},
      {'default': 0.9,
       'description': 'Limit the next token selection to a subset of '
		      'tokens with a cumulative probability above a '
		      'threshold P.',
       'flag': '--top_p',
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

def test_convert_request_to_cli_command_with_executable():
    cli_json = {
        "LLaMA-7B": [
            {
                "name": "Executable",
                "default": "./custom_main",
            },
            {
                "name": "test_param",
                "type": "str",
                "flag": "--test",
                "description": "test parameter",
            }
        ]
    }
    request = create_llm_request_model(cli_json)(test_param="value")
    assert convert_request_to_cli_command(request, cli_json) == ["./custom_main", "--test", "value"]

# Mocked cli.json data
mock_cli_json = {
    "LLaMA-7B": [
        {"name": "test_param", "type": "str", "flag": "--test", "description": "Test parameter"}
    ]
}

# Mocked request data
mock_request = {"test_param": "test_value"}


def test_get_api_with_executable():
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

    cli_json_with_executable = cli_json.copy()
    cli_json_with_executable['LLaMA-7B'] = [
            {
                "default": "./echo_args.sh",
                "hidden": True,
                "name": "Executable",
            },
        ] + cli_json_with_executable['LLaMA-7B']
    api_json = get_api(cli_json_with_executable)
    assert api_json == expected_api_json


sample_llm_request = {
    "Instruct mode": False,
    "Maximum length": 256,
    "Prompt": "Hello, world",
    "Stop sequences": "Goodbye, world",
    "Temperature": 0.7,
    "Top P": 0.95
}

@pytest.mark.asyncio
@mock.patch('asyncio.create_subprocess_exec')
async def test_post_llm_valid_run(mock_create_subprocess_exec):
    class MockProcess:
        def __init__(self, stdout='', stderr='', returncode=0):
            self.stdout = stdout.encode('utf-8')
            self.stderr = stderr.encode('utf-8')
            self.returncode = returncode

        async def communicate(self):
            return self.stdout, self.stderr

    expected = "Hello! How can I assist you today?"
    mock_create_subprocess_exec.return_value = MockProcess(stdout=expected)

    result = await main.post_llm(sample_llm_request, cli_json)
    assert result == {"response": expected}


@pytest.mark.asyncio
@mock.patch('asyncio.create_subprocess_exec')
async def test_post_llm_run_with_errors(mock_create_subprocess_exec):
    class MockProcess:
        def __init__(self, stdout='', stderr='', returncode=0):
            self.stdout = stdout.encode('utf-8')
            self.stderr = stderr.encode('utf-8')
            self.returncode = returncode

        async def communicate(self):
            return self.stdout, self.stderr

    mock_create_subprocess_exec.return_value = MockProcess(stderr='Error occurred', returncode=1)

    with pytest.raises(HTTPException) as exc_info:
        await main.post_llm(sample_llm_request, cli_json)

    assert exc_info.value.status_code == 400
    assert exc_info.value.detail == 'Error occurred'

@pytest.mark.asyncio
@mock.patch('asyncio.create_subprocess_exec')
async def test_post_llm_timeout(mock_create_subprocess_exec):
    # Set up the mock process to raise an exception when communicate is called
    class TimeoutMockProcess:
        async def communicate(self):
            raise TimeoutError

    mock_create_subprocess_exec.return_value = TimeoutMockProcess()

    with pytest.raises(HTTPException) as exc_info:
        await main.post_llm(sample_llm_request, cli_json)

    assert exc_info.value.status_code == 408
    assert exc_info.value.detail == 'Request timed out.'

# Mocked request data
mock_request = {"test_param": "test_value"}

@pytest.mark.asyncio
@mock.patch('gull_api.main.create_llm_request_model')
@mock.patch('gull_api.main.convert_request_to_cli_command')
@mock.patch('asyncio.create_subprocess_exec', new_callable=mock.AsyncMock)
async def test_post_llm(mock_create_subprocess_exec, mock_convert_request_to_cli_command, mock_create_llm_request_model):
    # Mock the process communicate function
    process_mock = mock.AsyncMock()
    process_mock.communicate = mock.AsyncMock(return_value=(b'OK', b''))
    process_mock.returncode = 0
    mock_create_subprocess_exec.return_value = process_mock

    # Call the function with the mocked request data
    result = await main.post_llm(request=mock_request, cli_json=mock_cli_json)

    # Assert create_llm_request_model was called with the correct arguments
    mock_create_llm_request_model.assert_called_once_with(mock_cli_json)
    validated_request = mock_create_llm_request_model.return_value(**mock_request)
    
    # Assert convert_request_to_cli_command was called with the correct arguments
    mock_convert_request_to_cli_command.assert_called_once_with(validated_request, mock_cli_json)

    # Assert subprocess command was called correctly
    mock_create_subprocess_exec.assert_called_once_with(
        *mock_convert_request_to_cli_command.return_value, stdout=subprocess.PIPE, stderr=subprocess.PIPE
    )

    # Assert the result is correct
    assert result == {"response": 'OK'}