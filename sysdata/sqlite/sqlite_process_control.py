import sqlite3
from typing import Callable

from sysdata.sqlite.sqlite_data import sqliteData, _row_to_dict
from sysobjects.production.process_control import controlProcess, start_run_idx, end_run_idx
from sysdata.production.process_control_data import controlProcessData
from syscore.constants import arg_not_supplied

from syslogging.logger import *

PROCESS_TABLE_NAME = "process_control"
METHODS_TABLE_NAME = "process_methods"

# Columns
PROCESS_NAME = "process_name"
LAST_START_TIME = "last_start_time"
LAST_END_TIME = "last_end_time"
STATUS = "status"
CURRENTLY_RUNNING = "currently_running"
PROCESS_ID = "process_id"
RECENTLY_CRASHED = "recently_crashed"
METHOD_NAME = "method_name"
RUNNING_METHODS = "running_methods"  # dict key, not a column

PROCESS_COLUMN_DEFS = [
    f"{PROCESS_NAME} TEXT PRIMARY KEY",
    f"{LAST_START_TIME} DATETIME",
    f"{LAST_END_TIME} DATETIME",
    f"{STATUS} TEXT",
    f"{CURRENTLY_RUNNING} BOOL",
    f"{PROCESS_ID} INTEGER",
    f"{RECENTLY_CRASHED} BOOL",
]

METHODS_COLUMN_DEFS = [
    f"{PROCESS_NAME} TEXT",
    f"{METHOD_NAME} TEXT",
    f"{LAST_START_TIME} DATETIME",
    f"{LAST_END_TIME} DATETIME",
]


class sqliteControlProcessData(controlProcessData, sqliteData):
    """
    Read and write data class to get process control data


    """

    def __init__(
        self,
        sqlite_conn: sqlite3.Connection = arg_not_supplied,
        log=get_logger("sqliteControlProcessData")
    ):
        controlProcessData.__init__(self, log=log)
        sqliteData.__init__(self, sqlite_conn=sqlite_conn)
        self._method_data = sqliteProcessMethodData(sqlite_conn)

    def __repr__(self):
        return "SQLite data connection for process control"

    @property
    def table_name(self) -> str:
        return PROCESS_TABLE_NAME

    @property
    def column_defs(self) -> list:
        return PROCESS_COLUMN_DEFS

    @property
    def _row_factory(self) -> Callable:
        return _process_control_factory

    @property
    def method_data(self):
        return self._method_data

    def get_list_of_process_names(self):
        sql = f"SELECT {PROCESS_NAME} FROM {self.table_name}"
        rows = self.sqlite_conn.execute(sql).fetchall()
        process_names = [row[0] for row in rows]
        return process_names

    def _get_control_for_process_name_without_default(self, process_name):
        # Get the process as a dict
        params = {PROCESS_NAME: process_name}
        process_dict = self._select_one(params)

        # Get the methods as a dict
        methods_dict = dict(self.method_data._select_many(params))

        # Add the methods to the process dict
        process_dict[RUNNING_METHODS] = methods_dict

        control_object = controlProcess.from_dict(process_dict)
        return control_object

    def _modify_existing_control_for_process_name(
        self, process_name, new_control_object
    ):
        self._insert_update_process(
            process_name, new_control_object, allow_replace=True
        )

    def _add_control_for_process_name(self, process_name, new_control_object):
        self._insert_update_process(
            process_name, new_control_object, allow_replace=False
        )

    def _insert_update_process(
        self, process_name, new_control_object, allow_replace: bool
    ):
        # Insert/update process
        params = new_control_object.as_dict()
        params[PROCESS_NAME] = process_name
        method_dict = params.pop(RUNNING_METHODS)
        self._insert(params, allow_replace=allow_replace)

        # Insert/update methods
        method_params = [
            {
                PROCESS_NAME: process_name,
                METHOD_NAME: k,
                # Are there situations where the list of start & end times might be empty?
                # Or only have 1 item? Or where the items aren't actually datetimes?
                LAST_START_TIME: v[start_run_idx],
                LAST_END_TIME: v[end_run_idx],
            }
            for k, v in method_dict.items()
        ]
        self._method_data._insert_many(method_params, allow_replace=allow_replace)

    def delete_control_for_process_name(self, process_name):
        params = {PROCESS_NAME: process_name}
        self._delete(params)


def _process_control_factory(cursor, row) -> dict:
    row_dict = _row_to_dict(cursor, row)
    row_dict.pop(PROCESS_NAME)
    return row_dict


class sqliteProcessMethodData(sqliteData):
    def __init__(
        self,
        sqlite_conn: sqlite3.Connection = arg_not_supplied,
    ):
        super().__init__(sqlite_conn=sqlite_conn)

    def __repr__(self):
        return "SQLite data connection for process methods"

    @property
    def table_name(self) -> str:
        return METHODS_TABLE_NAME

    @property
    def column_defs(self) -> list:
        return METHODS_COLUMN_DEFS

    @property
    def _row_factory(self) -> Callable:
        return _process_method_factory


def _process_method_factory(cursor, row) -> tuple[str, list]:
    row_dict = _row_to_dict(cursor, row)
    method = (
        row_dict[METHOD_NAME], [row_dict[LAST_START_TIME], row_dict[LAST_END_TIME]]
    )
    return method
