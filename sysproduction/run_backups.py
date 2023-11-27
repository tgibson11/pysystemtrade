from syscontrol.run_process import processToRun
from sysproduction.backup_db_to_csv import backupDbToCsv
from sysproduction.backup_mongo_data_as_dump import backupMongo
from sysproduction.backup_state_files import backupStateFiles
from sysproduction.backup_parquet_data_to_remote import backupParquet
from sysdata.data_blob import dataBlob


def run_backups():
    process_name = "run_backups"
    data = dataBlob(log_name=process_name)
    list_of_timer_names_and_functions = get_list_of_timer_functions_for_backup()
    backup_process = processToRun(process_name, data, list_of_timer_names_and_functions)
    backup_process.run_process()


def get_list_of_timer_functions_for_backup():
    data_db_backups = dataBlob(log_name="backup_db_to_csv")
    data_state_files = dataBlob(log_name="backup_files")
    data_mongo_dump = dataBlob(log_name="backup_mongo_data_as_dump")
    data_parquet_backup = dataBlob(log_name="backup_parquet_to_remote")

    db_backup_object = backupDbToCsv(data_db_backups)
    statefile_backup_object = backupStateFiles(data_state_files)
    mongodump_backup_object = backupMongo(data_mongo_dump)
    parquet_backup_object = backupParquet(data_parquet_backup)

    list_of_timer_names_and_functions = [
        ("backup_db_to_csv", db_backup_object),
        ("backup_mongo_data_as_dump", mongodump_backup_object),
        ("backup_files", statefile_backup_object),
        ("backup_parquet", parquet_backup_object),
    ]

    return list_of_timer_names_and_functions


if __name__ == "__main__":
    run_backups()
