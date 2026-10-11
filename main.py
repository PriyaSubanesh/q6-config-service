import os
from pathlib import Path

import yaml
from dotenv import load_dotenv
from fastapi import FastAPI, Query
from fastapi.middleware.cors import CORSMiddleware

load_dotenv()

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

defaults = {
    "port": 8000,
    "workers": 1,
    "debug": False,
    "log_level": "info",
    "api_key": "default-secret-000",
}


def parse_yaml_config():
    path = Path("config.development.yaml")

    if not path.exists():
        return {}

    with path.open("r") as file:
        data = yaml.safe_load(file) or {}

    return data


def parse_env_file():
    env_config = {}

    mapping = {
        "APP_PORT": "port",
        "NUM_WORKERS": "workers",
        "APP_WORKERS": "workers",
        "APP_DEBUG": "debug",
        "APP_LOG_LEVEL": "log_level",
        "APP_API_KEY": "api_key",
    }

    for env_name, config_name in mapping.items():
        value = os.getenv(env_name)

        if value is not None:
            env_config[config_name] = value

    return env_config


def parse_os_env_vars():
    os_config = {}

    for env_name, value in os.environ.items():
        if not env_name.startswith("APP_"):
            continue

        config_name = env_name.removeprefix("APP_").lower()

        if config_name == "workers":
            os_config["workers"] = value
        else:
            os_config[config_name] = value

    return os_config


def coerce_value(key, value):
    if key in ("port", "workers"):
        return int(value)

    if key == "debug":
        return str(value).strip().lower() in ("true", "1", "yes", "on")

    return str(value)


def parse_cli_overrides(overrides):
    cli_config = {}

    for item in overrides:
        if "=" not in item:
            continue

        key, value = item.split("=", 1)
        cli_config[key.strip()] = value

    return cli_config


@app.get("/effective-config")
def effective_config(
    set: list[str] | None = Query(default=None),
):
    config = dict(defaults)

    config.update(parse_yaml_config())
    config.update(parse_env_file())
    config.update(parse_os_env_vars())
    config.update(parse_cli_overrides(set or []))

    return {
        "port": coerce_value("port", config["port"]),
        "workers": coerce_value("workers", config["workers"]),
        "debug": coerce_value("debug", config["debug"]),
        "log_level": coerce_value("log_level", config["log_level"]),
        "api_key": "****",
    }