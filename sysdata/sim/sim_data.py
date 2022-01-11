import pandas as pd
import datetime

from syscore.objects import get_methods, missing_data
from syscore.dateutils import ARBITRARY_START
from syscore.pdutils import prices_to_daily_prices
from sysdata.base_data import baseData

from sysobjects.spot_fx_prices import fxPrices
from sysobjects.instruments import instrumentCosts, instrumentMetaData


class simData(baseData):
    """
    Core data object - Base class for simulation

    simData objects are used to get a collection of data

    The bare simData class isn't much good and holds only price and fx data

    Normally we'd inherit from this for specific asset classes (eg carry data for futures), and then for a
      specific source of data (eg csv files, databases, ...)

    The inheritance is:

    -> asset class specific eg futuresdata.FuturesData
    -> source specific eg legacy.csvFuturesSimData

    We can plug in different sources if desired

    """

    def __repr__(self):
        return "simData object with %d instruments" % len(self.get_instrument_list())

    def __getitem__(self, keyname: str):
        """
         convenience method to get the price, make it look like a dict

        :param keyname: instrument to get prices for
        :type keyname: str

        :returns: pd.DataFrame
        """
        price = self.get_raw_price(keyname)

        return price

    def keys(self) -> list:
        """
        list of instruments in this data set

        :returns: list of str

        >>> data=simData()
        >>> data.keys()
        []
        """
        return self.get_instrument_list()

    def system_init(self, base_system: "System"):
        """
        This is run when added to a base system

        :param base_system
        :return: nothing
        """

        # inherit the log
        self._log = base_system.log.setup(stage="data")
        self._parent = base_system

    @property
    def parent(self):
        return self._parent

    def start_date_for_data(self):
        start_date = getattr(self, "_start_date_for_data_from_config", missing_data)

        if start_date is missing_data:
            start_date = self._get_and_set_start_date_for_data_from_config()
        return start_date

    def _get_and_set_start_date_for_data_from_config(self) -> datetime:
        start_date = _resolve_start_date(self)
        self._start_date_for_data_from_config = start_date

        return start_date

    def methods(self) -> list:
        return get_methods(self)

    def daily_prices(self, instrument_code: str) -> pd.Series:
        """
        Gets daily prices

        :param instrument_code: Instrument to get prices for
        :type trading_rules: str

        :returns: Tx1 pd.Series

        """
        instrprice = self.get_raw_price(instrument_code)
        if len(instrprice) == 0:
            raise Exception("No adjusted daily prices for %s" % instrument_code)
        dailyprice = prices_to_daily_prices(instrprice)

        return dailyprice

    def get_fx_for_instrument(
        self, instrument_code: str, base_currency: str
    ) -> fxPrices:
        """
        Get the FX rate between the FX rate for the instrument and the base (account) currency

        :param instrument_code: instrument to value for
        :type instrument_code: str

        :param base_currency: instrument to value for
        :type instrument_code: str

        :returns: Tx1 pd.Series

        >>> data=simData()
        >>> data.get_fx_for_instrument("wibble", "USD").tail(5)
        2040-12-04    1.0
        2040-12-05    1.0
        2040-12-06    1.0
        2040-12-07    1.0
        2040-12-10    1.0
        Freq: B, dtype: float64
        """

        instrument_currency = self.get_instrument_currency(instrument_code)
        fx_rate_series = self._get_fx_data(instrument_currency, base_currency)

        return fx_rate_series

    def get_raw_price(self, instrument_code: str) -> pd.Series:
        """
        Default method to get instrument price at 'natural' frequency

        Will usually be overriden when inherited with specific data source

        :param instrument_code: instrument to get prices for
        :type instrument_code: str

        :returns: pd.Series

        """
        start_date = self.start_date_for_data()

        return self.get_raw_price_from_start_date(
            instrument_code, start_date=start_date
        )

    def get_raw_price_from_start_date(
        self, instrument_code: str, start_date: datetime.datetime
    ) -> pd.Series:
        """
        Default method to get instrument price at 'natural' frequency

        Will usually be overriden when inherited with specific data source

        :param instrument_code: instrument to get prices for
        :type instrument_code: str

        :returns: pd.Series

        """
        raise NotImplementedError("Need to inherit from simData")

    def get_instrument_list(self) -> list:
        """
        list of instruments in this data set

        :returns: list of str

        """
        raise NotImplementedError("Need to inherit from simData")

    def get_value_of_block_price_move(self, instrument_code: str) -> float:
        """
        How much does a $1 (or whatever) move in the price of an instrument block affect its value?
        eg 100.0 for 100 shares

        :param instrument_code: instrument to value for
        :type instrument_code: str

        :returns: float

        """
        self.log.warn(
            "Using base method of simData, value of block price move may not be accurate"
        )

        return 1.0

    def get_raw_cost_data(self, instrument_code: str) -> instrumentCosts:
        """
        Get cost data

        Execution slippage [half spread] price units
        Commission (local currency) per block
        Commission - percentage of value (0.01 is 1%)
        Commission (local currency) per block

        :param instrument_code: instrument to value for
        :type instrument_code: str

        :returns: dict of floats

        """

        self.log.warn("Using base method of simData, using zero costs")

        return instrumentCosts()

    def get_instrument_currency(self, instrument_code: str) -> str:
        """
        Get the currency for a particular instrument

        :param instrument_code: instrument to value for
        :type instrument_code: str

        :returns: str

        """

        raise NotImplementedError(
            "Need to inherit from base class for specific data source"
        )

    def _get_fx_data(self, currency1: str, currency2: str) -> fxPrices:
        """
        Get the FX rate currency1/currency2 between two currencies
        Or return None if not available

        (Normally we'd over ride this with a specific source)


        """
        start_date = self.start_date_for_data()

        return self._get_fx_data_from_start_date(
            currency1, currency2, start_date=start_date
        )

    def _get_fx_data_from_start_date(
        self, currency1: str, currency2: str, start_date: datetime.datetime
    ) -> fxPrices:
        """
        Get the FX rate currency1/currency2 between two currencies
        Or return None if not available

        (Normally we'd over ride this with a specific source)


        """
        raise NotImplementedError("Need to inherit for a specific data source")


def _resolve_start_date(sim_data: simData):

    config = _resolve_config(sim_data)

    if config is missing_data:
        start_date = missing_data
    else:
        start_date = getattr(config, "start_date", missing_data)

    if start_date is missing_data:
        start_date = ARBITRARY_START
    else:
        if isinstance(start_date, datetime.date):
            # yaml parses unquoted date like 2000-01-01 to datetime.date
            start_date = datetime.datetime.combine(
                start_date, datetime.datetime.min.time()
            )
        elif not isinstance(start_date, datetime.datetime):
            try:
                start_date = datetime.datetime.strptime(start_date, "%Y-%m-%d")
            except:
                raise Exception(
                    "Parameter start_date %s in config file does not conform to pattern 2020-03-19"
                    % str(start_date)
                )

    return start_date


def _resolve_config(sim_data: simData):
    try:
        config = sim_data.parent.config
        return config
    except:
        return missing_data
