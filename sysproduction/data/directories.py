import os

from syscore.fileutils import get_resolved_pathname
from syscore.objects import missing_data
from sysdata.config.production_config import get_production_config
from sysproduction.data.backtest import get_directory_store_backtests

production_config = get_production_config()

def get_main_backup_directory():

    ans = production_config.get_element_or_missing_data("offsystem_backup_directory")
    if ans is missing_data:
        raise Exception(
            "Can't backup without setting 'offsystem_backup_directory' in private_config.yaml"
        )
    return get_resolved_pathname(ans)


def get_csv_backup_directory():
    main_backup = get_main_backup_directory()
    ans = os.path.join(main_backup, "csv")

    return ans


def get_csv_dump_dir():
    return production_config.get_element_or_missing_data("csv_backup_directory")

def get_mongo_dump_directory():
    ans = production_config.get_element_or_missing_data("mongo_dump_directory")
    return get_resolved_pathname(ans)


def get_mongo_backup_directory():
    main_backup = get_main_backup_directory()
    ans = os.path.join(main_backup, "mongo")

    return ans


def get_statefile_directory():
    ans = get_directory_store_backtests()
    return get_resolved_pathname(ans)


def get_statefile_backup_directory():
    main_backup = get_main_backup_directory()
    ans = os.path.join(main_backup, "statefile")

    return ans

def get_echo_file_directory():
    ans = production_config.get_element_or_missing_data("echo_directory")

    return ans

def get_echo_extension():
    ans = production_config.get_element_or_missing_data("echo_extension")

    return ans


