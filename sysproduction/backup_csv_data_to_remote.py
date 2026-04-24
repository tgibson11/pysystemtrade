import os
import platform

from sysdata.config.production_config import get_production_config

from sysproduction.data.directories import get_parquet_backup_directory, get_csv_backup_directory

from sysdata.data_blob import dataBlob


def backup_csv_data_to_remote():
    data = dataBlob(log_name="backup_csv_data_to_remote")
    backup_object = backupCsv(data)
    backup_object.backup_csv()

    return None


def get_csv_directory(data):
    config = get_production_config()
    return config.get_element("csv_store")


class backupCsv(object):
    def __init__(self, data):
        self.data = data

    def backup_csv(self):
        data = self.data
        log = data.log
        log.debug("Copying data to offsystem backup destination")
        backup_csv_data_to_remote_with_data(data)


def backup_csv_data_to_remote_with_data(data):
    source_path = get_csv_directory(data)
    destination_path = get_csv_backup_directory()
    data.log.debug("Copy from %s to %s" % (source_path, destination_path))
    options = get_production_config().get_element("offsystem_backup_options")
    if platform.system() == "Windows":
        os.system(f"robocopy \"{source_path}\" \"{destination_path}\" {options}")
    else:
        os.system(f"rsync {options} {source_path} {destination_path}")


if __name__ == "__main__":
    backup_csv_data_to_remote()
