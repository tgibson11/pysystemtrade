import sqlite3
from typing import Callable

from syscore.constants import arg_not_supplied
from syscore.exceptions import missingData
from sysdata.futures.contracts import futuresContractData
from sysdata.sqlite.sqlite_data import sqliteData, _row_to_dict
from syslogging.logger import *
from sysobjects.contract_dates_and_expiries import contractDate, expiryDate, EXPIRY_DATE_FORMAT
from sysobjects.contracts import (
    futuresContract,
    listOfFuturesContracts, parametersForFuturesContract,
)

TABLE_NAME = "futures_contract"

# Columns
INSTRUMENT_CODE = "instrument_code"
CONTRACT_DATE = "contract_date"
EXPIRY_DATE = "expiry_date"
SAMPLING = "sampling"

COLUMN_DEFS = [
    f"{INSTRUMENT_CODE} TEXT",
    f"{CONTRACT_DATE} TEXT",
    f"{EXPIRY_DATE} DATE",
    f"{SAMPLING} BOOL",
    f"PRIMARY KEY ({INSTRUMENT_CODE}, {CONTRACT_DATE})",
]


class sqliteFuturesContractData(futuresContractData, sqliteData):

    def __init__(
        self,
        sqlite_conn: sqlite3.Connection = arg_not_supplied,
        log=get_logger("sqliteFuturesContractData")
    ):
        futuresContractData.__init__(self, log=log)
        sqliteData.__init__(self, sqlite_conn=sqlite_conn)

    def __repr__(self):
        return "sqliteFuturesContractData"

    @property
    def table_name(self) -> str:
        return TABLE_NAME

    @property
    def column_defs(self) -> list:
        return COLUMN_DEFS

    @property
    def _row_factory(self) -> Callable:
        return _futures_contract_factory

    def is_contract_in_data(self, instrument_code: str, contract_date_str: str) -> bool:
        try:
            self._get_contract_data_without_checking(instrument_code, contract_date_str)
        except missingData:
            return False
        return True

    def get_all_contract_objects_for_instrument_code(
        self, instrument_code: str
    ) -> listOfFuturesContracts:
        params = {
            INSTRUMENT_CODE: instrument_code,
        }
        contracts = self._select_many(params)
        return listOfFuturesContracts(contracts)

    def get_list_of_all_instruments_with_contracts(self) -> list:
        sql = f"SELECT DISTINCT {INSTRUMENT_CODE} FROM {self.table_name}"
        rows = self.sqlite_conn.execute(sql).fetchall()
        instruments = [row[0] for row in rows]
        return instruments

    def get_list_of_contract_dates_for_instrument_code(
        self, instrument_code: str
    ) -> list:
        contracts = self.get_all_contract_objects_for_instrument_code(instrument_code)
        contract_dates = [contract.contract_date.date_str for contract in contracts]
        return contract_dates

    def _get_contract_data_without_checking(
        self, instrument_code: str, contract_id: str
    ) -> futuresContract:
        params = {
            INSTRUMENT_CODE: instrument_code,
            CONTRACT_DATE: contract_id,
        }
        return self._select_one(params)

    def _add_contract_object_without_checking_for_existing_entry(
        self, contract_object: futuresContract
    ):
        params = {
            INSTRUMENT_CODE: contract_object.instrument_code,
            CONTRACT_DATE: contract_object.contract_date.date_str,
            EXPIRY_DATE: contract_object.expiry_date.date(),
            SAMPLING: contract_object.currently_sampling,
        }
        self._insert(params, allow_replace=True)

    def _delete_contract_data_without_any_warning_be_careful(
        self, instrument_code: str, contract_date: str
    ):
        params = {
            INSTRUMENT_CODE: instrument_code,
            CONTRACT_DATE: contract_date,
        }
        self._delete(params)


def _futures_contract_factory(cursor, row) -> futuresContract:
    row_dict = _row_to_dict(cursor, row)

    instrument_code = row_dict[INSTRUMENT_CODE]
    contract_date = row_dict[CONTRACT_DATE]
    expiry_date = row_dict[EXPIRY_DATE]
    sampling = row_dict[SAMPLING]

    expiry_date_str = expiry_date.strftime(EXPIRY_DATE_FORMAT)
    expiry_date_object = expiryDate.from_str(expiry_date_str)

    contract_date_object = contractDate(
        contract_date, expiry_date=expiry_date_object
    )

    params_dict = {SAMPLING: sampling}
    params_object = parametersForFuturesContract.from_dict(params_dict)

    contract = futuresContract(
        instrument_object=instrument_code,
        contract_date_object=contract_date_object,
        parameter_object=params_object
    )

    return contract
