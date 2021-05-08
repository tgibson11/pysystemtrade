from syscore.fileutils import delete_old_files_with_extension_in_pathname
from sysproduction.data.directories import get_directory_store_backtests
from sysproduction.data.directories import get_statefile_backup_directory
from sysdata.data_blob import dataBlob


def clean_truncate_backtest_states():
    data = dataBlob()
    cleaner = cleanTruncateBacktestStates(data)
    cleaner.clean_backtest_states()

    return None


class cleanTruncateBacktestStates:
    def __init__(self, data: dataBlob):
        self.data = data

    def clean_backtest_states(self):
        directory_to_use = get_directory_store_backtests()
        self.data.log.msg(
            "Deleting old .pck and .yaml backtest state files in directory %s"
            % directory_to_use
        )
        delete_old_files_with_extension_in_pathname(
            directory_to_use, days_old=1, extension=".pck"
        )
        delete_old_files_with_extension_in_pathname(
            directory_to_use, days_old=1, extension=".yaml"
        )

        # Also remove old backtests from backup directory to save space
        directory_to_use = get_statefile_backup_directory()
        self.data.log.msg(
            "Deleting old .pck and .yaml backtest state files in directory %s"
            % directory_to_use
        )
        delete_old_files_with_extension_in_pathname(
            directory_to_use, days_old=1, extension=".pck"
        )
        delete_old_files_with_extension_in_pathname(
            directory_to_use, days_old=1, extension=".yaml"
        )


if __name__ == '__main__':
    clean_truncate_backtest_states()
