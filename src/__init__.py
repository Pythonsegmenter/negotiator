"""Negotiator package."""

import os
from typing import Any, Dict

from dynaconf import Dynaconf

# Initialize settings with Dynaconf
settings = Dynaconf(
    envvar_prefix="NEGOTIATOR",
    settings_files=[
        "settings.toml",
        ".secrets.toml",
    ],
    environments=True,
    load_dotenv=True,
)

# Set OpenAI API key as an environment variable
if settings.get("openai_api_key"):
    os.environ["OPENAI_API_KEY"] = settings.openai_api_key 