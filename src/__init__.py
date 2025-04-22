import os

from dynaconf import Dynaconf

from src.log_manager.logging_config import logger

logger.info("Initializing settings")

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
