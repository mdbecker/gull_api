from fastapi import FastAPI, Depends, HTTPException
from pydantic import BaseModel, Field, create_model
from typing import Dict, Any
import json
import subprocess
import asyncio
from gull_api.db import APIRequestLog, SessionManager
from gull_api import config

app = FastAPI()

def get_single_key(dictionary: Dict[str, Any]) -> str:
    return list(dictionary.keys())[0]

def load_cli_json():
    with open(config.CLI_JSON_PATH, "r") as f:
        return json.load(f)

def create_llm_request_model(cli_json: Dict[str, Any]) -> BaseModel:
    fields = {}
    for param in cli_json[get_single_key(cli_json)]:
        param_name = param["name"]
        field_kwargs = {"description": param["description"]}
        if "default" in param:
            field_kwargs["default"] = param["default"]
        else:
            if param.get('required', True) is False:
                field_kwargs["default"] = None
        if "min" in param and "max" in param:
            field_kwargs["gt"] = param["min"]
            field_kwargs["lt"] = param["max"]
        fields[param["name"]] = (param["type"], Field(**field_kwargs))
    return create_model("LLMRequest", **fields)

def convert_request_to_cli_command(request: BaseModel, cli_json: Dict[str, Any]) -> str:
    cli_args = []
    command = [config.EXECUTABLE]  # use executable from config
    for param in cli_json[get_single_key(cli_json)]:
        param_name = param["name"]
        if param_name in request.dict():
            value = request.dict()[param_name]
            flag = param["flag"]
            if param["type"] == "bool":
                if value:
                    cli_args.append(flag)
            else:
                cli_args.append(flag)
                cli_args.append(str(value))
    command += cli_args
    return command

def convert_cli_json_to_api_format(cli_json: Dict[str, Any]) -> Dict[str, Any]:
    key = get_single_key(cli_json)
    api_json = {key: []}
    for param in cli_json[key]:
        if not param.get("hidden", False):
            api_param = {
                "name": param["name"],
                "type": param["type"],
                "description": param["description"],
            }
            if "default" in param:
                api_param["default"] = param["default"]
            if "min" in param and "max" in param:
                api_param["min"] = param["min"]
                api_param["max"] = param["max"]
                if param["type"] == "int" or param["type"] == "float":
                    api_param["step"] = param.get("step", 1 if param["type"] == "int" else 0.01)  # respect "step" if provided in cli_json
            if param.get("required", False):
                api_param["required"] = param["required"]  # respect "required" if provided in cli_json
            api_json[key].append(api_param)
    return api_json

@app.get("/api")
def get_api(cli_json=Depends(load_cli_json)):
    api_json = convert_cli_json_to_api_format(cli_json)
    return api_json

async def create_log_object(request, stdout, stderr, returncode):
    return APIRequestLog(
        request=str(request),
        response=stdout if returncode == 0 else None,
        error_occurred=returncode != 0,
        error_details=stderr if returncode != 0 else None,
    )

# Helper function to create and log the API request
async def create_and_log(request, stdout="", stderr="", returncode=0):
    log = await create_log_object(request, stdout, stderr, returncode)
    with SessionManager(log) as session:
        pass
    return log

async def handle_error(request, status_code, detail, stderr="", returncode=1):
    """
    Generic error handling function to log and raise HTTPException.
    
    Args:
        request (Dict): The request data.
        status_code (int): HTTP status code to be returned.
        detail (str): Detailed error message.
        stderr (str, optional): Standard error stream. Defaults to "".
        returncode (int, optional): Return code of the process. Defaults to 1.
    """
    log = await create_and_log(request, stderr=stderr, returncode=returncode)
    raise HTTPException(status_code=status_code, detail=detail)

@app.post("/llm")
async def post_llm(request: Dict[str, Any], cli_json=Depends(load_cli_json)):
    LLMRequest = create_llm_request_model(cli_json)
    validated_request = LLMRequest(**request)
    command = convert_request_to_cli_command(validated_request, cli_json)
    
    return_code = None
    
    try:
        process = await asyncio.create_subprocess_exec(*command, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        stdout_bytes, stderr_bytes = await asyncio.wait_for(process.communicate(), timeout=60)
        stdout = stdout_bytes.decode("utf-8")
        stderr = stderr_bytes.decode("utf-8")
        return_code = process.returncode
    except asyncio.TimeoutError:
        await handle_error(request, status_code=504, detail="Server processing timed out.", returncode=return_code)
    except Exception as e:
        await handle_error(request, status_code=500, detail="Internal Server Error", stderr=str(e), returncode=return_code)
    else:
        if return_code != 0:
            await handle_error(request, status_code=422, detail=stderr, stderr=stderr, returncode=return_code)
    
    # Logging successful response
    await create_and_log(request, stdout=stdout, returncode=return_code)
    
    return {'response': stdout}