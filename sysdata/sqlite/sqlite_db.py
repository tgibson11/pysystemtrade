import sqlite3

from syscore.constants import arg_not_supplied
from sysdata.config.production_config import get_production_config
from sysdata.generic_db import genericDb


class sqliteDb(genericDb):
    """
    Keeps track of SQLite database we are connected to
    """

    def __init__(
        self,
        sqlite_db_file: str = arg_not_supplied,
    ):
        if sqlite_db_file is arg_not_supplied:
            sqlite_db_file = get_default_db_file()

        self.sqlite_db_file = sqlite_db_file

        sqlite_conn = sqlite3.connect(
            sqlite_db_file, detect_types=sqlite3.PARSE_DECLTYPES, autocommit=True
        )

        self.sqlite_conn = sqlite_conn

    def __repr__(self):
        return f"SQLite database: {self.sqlite_db_file}"

    def close_connection(self):
        self.sqlite_conn.close()


def get_default_db_file():
    config = get_production_config()
    default_db_file = config.get_element("sqlite_database")
    return default_db_file
