from concurrent.futures import ThreadPoolExecutor
from fastapi import FastAPI, Depends, HTTPException
from pydantic import BaseModel, Field, create_model
from typing import Dict, Any
import json
import subprocess

app = FastAPI()
executor = ThreadPoolExecutor(max_workers=5)  # Adjust the number of simultaneous requests

def load_cli_json():
    with open("cli.json", "r") as f:
        return json.load(f)

def create_llm_request_model(cli_json: Dict[str, Any]) -> BaseModel:
    fields = {}
    for param in cli_json["LLaMA-7B"]:
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
    for param in cli_json["LLaMA-7B"]:
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
    command = ["./main"] + cli_args
    return command

def process_request(request: BaseModel, cli_json: Dict[str, Any]) -> Dict[str, Any]:
    command = convert_request_to_cli_command(request, cli_json)
    try:
        result = subprocess.run(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=60)  # Set the desired timeout value
    except subprocess.TimeoutExpired:
        raise HTTPException(status_code=408, detail="Request timed out.")
    
    if result.returncode != 0:
        raise HTTPException(status_code=400, detail=result.stderr.decode("utf-8"))
    return json.loads(result.stdout)

def convert_cli_json_to_api_format(cli_json: Dict[str, Any]) -> Dict[str, Any]:
    api_json = {"LLaMA-7B": []}
    for param in cli_json["LLaMA-7B"]:
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
            api_json["LLaMA-7B"].append(api_param)
    return api_json

@app.get("/api")
def get_api(cli_json=Depends(load_cli_json)):
    api_json = convert_cli_json_to_api_format(cli_json)
    return api_json

@app.post("/llm")
def post_llm(request: Dict[str, Any], cli_json=Depends(load_cli_json)):
    LLMRequest = create_llm_request_model(cli_json)
    validated_request = LLMRequest(**request)
    return executor.submit(process_request, validated_request, cli_json)
