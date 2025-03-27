import os
from enum import Enum

from sysbrokers.IB.ib_connection import get_broker_account
from syscore.interactive.input import true_if_answer_is_yes
from sysdata.config.private_directory import PRIVATE_CONFIG_DIR_ENV_VAR
from sysdata.data_blob import dataBlob


class Account:
    def __init__(self, config_subdir: str):
        self.config_subdir = config_subdir


class Accounts(Enum):
    LLC_ACCOUNT = Account("llc")
    PERSONAL_ACCOUNT = Account("personal")


def use_account(account: Account | None = None, check_ib_conn: bool = True):
    if account is None:
        account = prompt_for_account()
        check_ib_conn = prompt_to_check_ib_conn()
    private_config_base_dir = os.environ[PRIVATE_CONFIG_DIR_ENV_VAR]
    private_config_sub_dir = account.config_subdir
    os.environ[PRIVATE_CONFIG_DIR_ENV_VAR] = \
        f"{private_config_base_dir}\\{private_config_sub_dir}"
    if check_ib_conn:
        check_ib_connection()

def prompt_for_account() -> Account:
    # TODO prompt for account & convert user input
    return Accounts.LLC_ACCOUNT.value

def prompt_to_check_ib_conn() -> bool:
    return true_if_answer_is_yes("Do you require an IB connection?")

def check_ib_connection():
    configured_broker_account = get_broker_account()
    ib_conn = dataBlob().ib_conn
    ib_accounts = ib_conn.ib.managedAccounts()
    if configured_broker_account not in ib_accounts:
        ib_accounts_as_str = ",".join(ib_accounts)
        message = (f"Configured broker_account {configured_broker_account} "
                   f"does not match the current IB connection {ib_accounts_as_str}")
        raise Exception(message)
