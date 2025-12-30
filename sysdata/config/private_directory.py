import os
from pathlib import Path

DEFAULT_PRIVATE_DIR = "private"
PRIVATE_CONFIG_DIR_ENV_VAR = "PYSYS_PRIVATE_CONFIG_DIR"


def get_full_path_for_private_config(filename: str):
    ## FIXME: should use os path join instead of '/'?

    if os.getenv(PRIVATE_CONFIG_DIR_ENV_VAR):
        private_config_path = f"{os.environ[PRIVATE_CONFIG_DIR_ENV_VAR]}/{filename}"
    else:
        private_config_path = f"{DEFAULT_PRIVATE_DIR}/{filename}"

    return private_config_path


def get_private_config_dir():
    if os.getenv(PRIVATE_CONFIG_DIR_ENV_VAR):
        private_config_dir = Path(os.environ[PRIVATE_CONFIG_DIR_ENV_VAR])
    else:
        private_config_dir = Path(DEFAULT_PRIVATE_DIR)

    return str(private_config_dir)
