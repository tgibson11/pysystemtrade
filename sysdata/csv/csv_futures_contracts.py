import pandas as pd
from pandas import DataFrame

from syscore.constants import arg_not_supplied
from syscore.exceptions import ContractNotFound
from sysdata.config.production_config import get_production_config
from sysdata.futures.contracts import futuresContractData, listOfFuturesContracts
from syslogging.logger import *
from sysobjects.contract_dates_and_expiries import listOfContractDateStr, contractDate, expiryDate
from sysobjects.contracts import futuresContract, parametersForFuturesContract
from sysobjects.instruments import futuresInstrument

DEFAULT_DIR = "futures_contracts"


class csvFuturesContractData(futuresContractData):

    def __init__(
        self, datapath=arg_not_supplied, log=get_logger("csvFuturesContractData")
    ):
        super().__init__(log=log)

        if datapath is arg_not_supplied:
            config = get_production_config()
            csv_store = config.get_element("csv_store")
            datapath = os.path.join(csv_store, DEFAULT_DIR)

        self._datapath = datapath

    def __repr__(self):
        return "Futures contract data from %s" % self.datapath

    @property
    def datapath(self):
        return self._datapath

    def _filename_for_instrument_code(self, instrument_code: str):
        return resolve_path_and_filename_for_package(
            self.datapath, "%s.csv" % instrument_code
        )

    def write_contract_list_as_df(
        self, instrument_code: str, contract_list: listOfFuturesContracts
    ):
        list_of_expiry = [x.expiry_date.as_str() for x in contract_list]
        list_of_contract_date = [x.date_str for x in contract_list]
        list_of_sampling = [x.currently_sampling for x in contract_list]

        df = pd.DataFrame(
            dict(
                date=list_of_contract_date,
                sampling=list_of_sampling,
                expiry=list_of_expiry,
            )
        )
        filename = self._filename_for_instrument_code(instrument_code)
        df.to_csv(filename)

    def get_list_of_contract_dates_for_instrument_code(
        self, instrument_code, allow_expired: bool = False
    ) -> listOfContractDateStr:
        # MongoDB implementation ignores allow_expired, so we will too
        df = self._read_csv(instrument_code)
        contract_dates = df["date"].to_list()
        return listOfContractDateStr(contract_dates)

    def get_all_contract_objects_for_instrument_code(
        self, instrument_code
    ) -> listOfFuturesContracts:
        df = self._read_csv(instrument_code)
        list_of_futures_contracts = listOfFuturesContracts()
        for row in df.itertuples():
            futures_contract = _convert_row_to_futures_contract(instrument_code, row)
            list_of_futures_contracts.append(futures_contract)
        return list_of_futures_contracts

    def _delete_contract_data_without_any_warning_be_careful(
        self, instrument_code: str, contract_date: str
    ):
        filename = self._filename_for_instrument_code(instrument_code)
        df = _read_csv_given_filename(filename)
        delete = _find_by_contract_date(df, contract_date)
        df.drop(delete.index, inplace=True)
        df.to_csv(filename)

    def is_contract_in_data(self, instrument_code: str, contract_date_str: str) -> bool:
        df = self._read_csv(instrument_code)
        match = _find_by_contract_date(df, contract_date_str)
        return not match.empty

    def _add_contract_object_without_checking_for_existing_entry(self, contract_object):
        instrument_code = contract_object.instrument_code
        filename = self._filename_for_instrument_code(instrument_code)
        df = _read_csv_given_filename(filename)
        # Uses of this method assume a database-like implementation where adding an
        # object with the same key as an existing object will do an update. With CSV,
        # we need to check.
        match = _find_by_contract_date(df, contract_object.date_str)
        if match.empty:
            new_row = pd.Series(
                {
                    'date': contract_object.date_str,
                    'sampling': contract_object.currently_sampling,
                    'expiry': contract_object.expiry_date.as_str(),
                }
            )
            df = pd.concat([df, new_row.to_frame().T], ignore_index=True)
        else:
            df.loc[match.index, ['sampling', 'expiry']] = \
                [contract_object.currently_sampling, contract_object.expiry_date.as_str()]
        df.to_csv(filename)

    def _get_contract_data_without_checking(
        self, instrument_code: str, contract_date: str
    ) -> futuresContract:
        df = self._read_csv(instrument_code)
        matches = _find_by_contract_date(df, contract_date)
        for match in matches.itertuples():
            return _convert_row_to_futures_contract(instrument_code, match)
        raise ContractNotFound(
            "Contract %s/%s not found" % (instrument_code, contract_date)
        )

    def _read_csv(self, instrument_code: str) -> DataFrame:
        filename = self._filename_for_instrument_code(instrument_code)
        return _read_csv_given_filename(filename)


def _read_csv_given_filename(filename: str) -> DataFrame:
    return pd.read_csv(
        filename, index_col=0, dtype={'date': str, 'sampling': bool, 'expiry': str}
    )


def _find_by_contract_date(df: DataFrame, contract_date: str) -> DataFrame:
    return df[df["date"] == contract_date]


def _convert_row_to_futures_contract(instrument_code: str, row) -> futuresContract:
    instrument_object = futuresInstrument(instrument_code)
    expiry_date = expiryDate.from_str(row.expiry)
    contract_date_object = contractDate(row.date, expiry_date=expiry_date)
    parameter_object = parametersForFuturesContract(sampling=row.sampling)
    futures_contract = futuresContract(
        instrument_object, contract_date_object, parameter_object=parameter_object
    )
    return futures_contract
