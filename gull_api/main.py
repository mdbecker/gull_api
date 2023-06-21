from concurrent.futures import ThreadPoolExecutor
from fastapi import FastAPI, Depends, HTTPException
from pydantic import BaseModel, Field, create_model
from typing import Dict, Any
import json
import subprocess
import asyncio

app = FastAPI()
executor = ThreadPoolExecutor(max_workers=5)  # Adjust the number of simultaneous requests

def get_single_key(dictionary: Dict[str, Any]) -> str:
    return list(dictionary.keys())[0]

def load_cli_json():
    with open("cli.json", "r") as f:
        return json.load(f)

def create_llm_request_model(cli_json: Dict[str, Any]) -> BaseModel:
    fields = {}
    for param in cli_json[get_single_key(cli_json)]:
        param_name = param["name"]
        if param_name == "Executable":  # skip Executable since it's not used by the api
            continue
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
    command = ["./main"]  # default executable
    for param in cli_json[get_single_key(cli_json)]:
        param_name = param["name"]
        if param_name == "Executable":  # if parameter is the executable
            command = [param.get("default", "./main")]  # use default value or fallback to "./main"
            continue
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

@app.post("/llm")
async def post_llm(request: Dict[str, Any], cli_json=Depends(load_cli_json)):
    LLMRequest = create_llm_request_model(cli_json)
    validated_request = LLMRequest(**request)
    command = convert_request_to_cli_command(validated_request, cli_json)

    try:
        process = await asyncio.create_subprocess_exec(
            *command, stdout=subprocess.PIPE, stderr=subprocess.PIPE
        )

        stdout, stderr = await asyncio.wait_for(process.communicate(), timeout=60)
    except asyncio.TimeoutError:
        raise HTTPException(status_code=408, detail="Request timed out.")

    if process.returncode != 0:
        raise HTTPException(status_code=400, detail=stderr.decode("utf-8"))

    return {'response': stdout.decode("utf-8")}