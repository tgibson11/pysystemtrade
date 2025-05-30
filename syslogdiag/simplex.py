import os

from sysdata.config.production_config import get_production_config


def send(msg: str):
    recipient = get_recipient()
    os.system(f"simplex-chat -e \"@{recipient} {msg}\"")


def send_file(file_path: str):
    recipient = get_recipient()
    os.system(f"simplex-chat -e \"/f @{recipient} {file_path}\" -t 6")


def get_recipient():
    production_config = get_production_config()
    recipient = production_config.get_element("simplex_recipient")
    return recipient
