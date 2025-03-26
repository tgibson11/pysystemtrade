import os
from enum import Enum

from sysbrokers.IB.ib_connection import get_broker_account
from sysdata.config.private_directory import PRIVATE_CONFIG_DIR_ENV_VAR
from sysdata.data_blob import dataBlob

class Account:
    def __init__(self, config_subdir):
        self.config_subdir = config_subdir

class Accounts(Enum):
    LLC_ACCOUNT = Account("llc")
    PERSONAL_ACCOUNT = Account("personal")

def use_account(account: Account):
    private_config_base_dir = os.environ[PRIVATE_CONFIG_DIR_ENV_VAR]
    private_config_sub_dir = account.config_subdir
    os.environ[PRIVATE_CONFIG_DIR_ENV_VAR] = \
        f"{private_config_base_dir}\\{private_config_sub_dir}"
    check_ib_account()

def check_ib_account():
    configured_broker_account = get_broker_account()
    ib_conn = dataBlob().ib_conn
    ib_accounts = ib_conn.ib.managedAccounts()
    if configured_broker_account not in ib_accounts:
        ib_accounts_as_str = ",".join(ib_accounts)
        raise Exception(f"Configured broker_account {configured_broker_account} "
                        f"does not match the current IB connection {ib_accounts_as_str}")