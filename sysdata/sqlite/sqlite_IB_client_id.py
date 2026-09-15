import sqlite3
from typing import Callable

from sysbrokers.IB.client.ib_client_id import ibBrokerClientIdData
from syscore.constants import arg_not_supplied
from sysdata.sqlite.sqlite_data import sqliteData, _row_to_dict
from syslogging.logger import *

TABLE_NAME = "ib_client_id"

# Columns
CLIENT_ID = "client_id"

COLUMN_DEFS = [
    f"{CLIENT_ID} INTEGER PRIMARY KEY",
]


class sqliteIbBrokerClientIdData(ibBrokerClientIdData, sqliteData):
    """
    Read and write data class to get next used client id
    """

    def __init__(
        self,
        sqlite_conn: sqlite3.Connection = arg_not_supplied,
        idoffset=arg_not_supplied,
        log=get_logger("sqliteIDTracker"),
    ):
        ibBrokerClientIdData.__init__(self, log=log, idoffset=idoffset)
        sqliteData.__init__(self, sqlite_conn=sqlite_conn)

    def __repr__(self):
        return "Tracking IB client IDs"

    @property
    def table_name(self) -> str:
        return TABLE_NAME

    @property
    def column_defs(self) -> list:
        return COLUMN_DEFS

    @property
    def _row_factory(self) -> Callable:
        return _ib_client_id_factory

    def _get_list_of_clientids(self) -> list:
        client_ids = self._select_all()
        return client_ids

    def _lock_clientid(self, next_id: int):
        self._insert({CLIENT_ID: next_id})
        self.log.debug(f"Locked IB client ID {next_id}")

    def release_clientid(self, clientid: int):
        self._delete({CLIENT_ID: clientid})
        self.log.debug(f"Released IB client ID {clientid}")


def _ib_client_id_factory(cursor, row) -> int:
    row_dict = _row_to_dict(cursor, row)
    client_id = row_dict.get(CLIENT_ID)
    return client_id
