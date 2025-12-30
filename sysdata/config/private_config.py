from syscore.fileutils import resolve_path_and_filename_for_package, does_filename_exist
from syscore.constants import arg_not_supplied
from sysdata.config.private_directory import get_private_config_dir

import yaml

PRIVATE_CONFIG_FILE = "private_config.yaml"


def get_private_config_as_dict() -> dict:
    dir = get_private_config_dir()
    try:
        private_file = resolve_path_and_filename_for_package(dir, PRIVATE_CONFIG_FILE)
        with open(private_file) as file_to_parse:
            private_dict = yaml.load(file_to_parse, Loader=yaml.FullLoader)
        return private_dict

    except (FileNotFoundError, ModuleNotFoundError):
        print(
            f"Private configuration '{dir}.{PRIVATE_CONFIG_FILE}' does not exist; no problem if running in sim mode"
        )
        return {}
