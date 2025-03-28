import os
from enum import Enum

from sysdata.config.private_directory import PRIVATE_CONFIG_DIR_ENV_VAR


class Account:
    def __init__(self, config_subdir: str):
        self.config_subdir = config_subdir


class Accounts(Enum):
    LLC_ACCOUNT = Account("llc")
    PERSONAL_ACCOUNT = Account("personal")


def use_account(account: Account | None = None):
    if account is None:
        account = prompt_for_account()
    private_config_base_dir = os.environ[PRIVATE_CONFIG_DIR_ENV_VAR]
    private_config_sub_dir = account.config_subdir
    os.environ[PRIVATE_CONFIG_DIR_ENV_VAR] = \
        f"{private_config_base_dir}\\{private_config_sub_dir}"

def prompt_for_account() -> Account:
    # TODO prompt for account & convert user input
    return Accounts.LLC_ACCOUNT.value
