import os

from sysdata.config.production_config import get_production_config


def send(msg: str):
    recipient = get_recipient()
    os.system(f"simplex-chat -e \"@{recipient} {msg}\"")


def send_as_file(name: str, content: str):
    recipient = get_recipient()
    with open(name, 'w') as file:
        file.write(content)
    os.system(f"simplex-chat -e \"/f @{recipient} {file_path}\"")


def get_recipient():
    production_config = get_production_config()
    recipient = production_config.get_element("simplex_recipient")
    return recipient
