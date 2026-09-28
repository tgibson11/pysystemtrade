import os
import platform

from sysdata.config.production_config import get_production_config

from sysdata.data_blob import dataBlob
from sysproduction.data.directories import get_sqlite_dump_directory, get_sqlite_backup_directory


def backup_sqlite_data_as_dump():
    data = dataBlob(log_name="backup_sqlite_data_as_dump")
    backup_object = backupSqlite(data)
    backup_object.backup_db_as_dump()

    return None


class backupSqlite(object):
    def __init__(self, data):
        self.data = data

    def backup_db_as_dump(self):
        data = self.data
        log = data.log
        log.debug("Exporting sqlite data")
        dump_sqlite_data(data)
        log.debug("Copying data to offsystem backup destination")
        backup_sqlite_dump(data)


def dump_sqlite_data(data: dataBlob):
    config = data.config
    db_file = config.get_element("sqlite_database")

    dump_path = get_sqlite_dump_directory()
    dump_file = os.path.join(dump_path, "dump.sql")

    data.log.debug(f"Dumping ALL sqlite data to {dump_file}")
    os.system(f"sqlite3 {db_file} .dump > {dump_file}")

    data.log.debug("Dumped")


def backup_sqlite_dump(data):
    source_path = get_sqlite_dump_directory()
    destination_path = get_sqlite_backup_directory()
    data.log.debug("Copy from %s to %s" % (source_path, destination_path))
    options = get_production_config().get_element("offsystem_backup_options")
    if platform.system() == "Windows":
        os.system(f"robocopy \"{source_path}\" \"{destination_path}\" {options}")
    else:
        os.system(f"rsync {options} {source_path} {destination_path}")


if __name__ == "__main__":
    backup_sqlite_data_as_dump()
