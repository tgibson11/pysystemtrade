from copy import copy
from ib_insync import Contract

from sysbrokers.IB.client.ib_client import ibClient
from sysbrokers.IB.ib_instruments import ib_futures_instrument_just_symbol, futuresInstrumentWithIBConfigData, \
    ib_futures_instrument
from sysbrokers.IB.ib_trading_hours import get_trading_hours
from sysbrokers.IB.ib_contracts import (
    ibcontractWithLegs, get_ib_contract_with_specific_expiry, resolve_unique_contract_from_ibcontract_list,
    _add_legs_to_ib_contract)

from syscore.objects import missing_contract
from syscore.genutils import list_of_ints_with_highest_common_factor_positive_first

from syslogdiag.logger import logger

from sysobjects.contracts import futuresContract, contractDate
from sysexecution.trade_qty import tradeQuantity


class ibContractsClient(ibClient):
    def broker_get_futures_contract_list(
            self, futures_instrument_with_ib_data: futuresInstrumentWithIBConfigData) -> list:
        ## Returns list of contract date strings YYYYMMDD

        specific_log = self.log.setup(
            instrument_code=futures_instrument_with_ib_data.instrument_code
        )

        ibcontract_pattern = ib_futures_instrument(
            futures_instrument_with_ib_data)
        contract_list = self.ib_get_contract_chain(ibcontract_pattern)
        # if no contracts found will be empty

        # Extract expiry date strings from these
        contract_dates = [
            ibcontract.lastTradeDateOrContractMonth for ibcontract in contract_list]

        return contract_dates



    def broker_get_single_contract_expiry_date(
            self, futures_contract_with_ib_data: futuresContract) -> str:
        """
        Return the exact expiry date for a given contract

        :param futures_contract_with_ib_data:  contract where instrument has ib metadata
        :return: YYYYMMDD str
        """
        specific_log = futures_contract_with_ib_data.specific_log(self.log)
        if futures_contract_with_ib_data.is_spread_contract():
            specific_log.warn("Can only find expiry for single leg contract!")
            return missing_contract

        ibcontract = self.ib_futures_contract(
            futures_contract_with_ib_data, always_return_single_leg=True)

        if ibcontract is missing_contract:
            specific_log.warn("Contract is missing can't get expiry")
            return missing_contract

        expiry_date = ibcontract.lastTradeDateOrContractMonth

        return expiry_date


    def ib_get_trading_hours(self, contract_object_with_ib_data: futuresContract) -> list:
        specific_log = contract_object_with_ib_data.specific_log(self.log)
        ib_contract = self.ib_futures_contract(
            contract_object_with_ib_data, always_return_single_leg=True
        )
        if ib_contract is missing_contract:
            specific_log.warn("Can't get trading hours as contract is missing")
            return missing_contract

        # returns a list but should only have one element
        ib_contract_details_list = self.ib.reqContractDetails(ib_contract)
        ib_contract_details = ib_contract_details_list[0]

        try:
            trading_hours = get_trading_hours(ib_contract_details)
        except Exception as e:
            specific_log.warn("%s when getting trading hours from %s!" % (str(e), str(ib_contract_details)))
            return missing_contract

        return trading_hours

    def ib_get_min_tick_size(self, contract_object_with_ib_data: futuresContract) -> float:
        specific_log = contract_object_with_ib_data.specific_log(self.log)
        ib_contract = self.ib_futures_contract(
            contract_object_with_ib_data, always_return_single_leg=True
        )
        if ib_contract is missing_contract:
            specific_log.warn("Can't get tick size as contract missing")
            return missing_contract

        ib_contract_details = self.ib.reqContractDetails(ib_contract)[0]

        try:
            min_tick = ib_contract_details.minTick
        except Exception as e:
            specific_log.warn("%s when getting min tick size from %s!" % (str(e), str(ib_contract_details)))
            return missing_contract

        return min_tick

    def ib_futures_contract(self,
                            futures_contract_with_ib_data: futuresContract,
                            always_return_single_leg=False,
                            trade_list_for_multiple_legs: tradeQuantity = None
                            ) -> Contract:

        ibcontract_with_legs = self.ib_futures_contract_with_legs(futures_contract_with_ib_data=futures_contract_with_ib_data,
                                                                  always_return_single_leg=always_return_single_leg,
                                                                  trade_list_for_multiple_legs=trade_list_for_multiple_legs)
        return ibcontract_with_legs.ibcontract


    def ib_futures_contract_with_legs(
        self,
        futures_contract_with_ib_data: futuresContract,
        always_return_single_leg=False,
        trade_list_for_multiple_legs: tradeQuantity=None
    ) -> ibcontractWithLegs:
        """
        Return a complete and unique IB contract that matches contract_object_with_ib_data
        Doesn't actually get the data from IB, tries to get from cache

        :param futures_contract_with_ib_data: contract, containing instrument metadata suitable for IB
        :return: a single ib contract object
        """
        contract_object_to_use = copy(futures_contract_with_ib_data)
        if always_return_single_leg and contract_object_to_use.is_spread_contract():
            contract_object_to_use = contract_object_to_use.new_contract_with_first_contract_date()

        ibcontract_with_legs = self._get_stored_or_live_contract(contract_object_to_use=contract_object_to_use,
                                                                 trade_list_for_multiple_legs=trade_list_for_multiple_legs)


        return ibcontract_with_legs

    def _get_stored_or_live_contract(self, contract_object_to_use: futuresContract,
                                            trade_list_for_multiple_legs: tradeQuantity = None):


        ibcontract_with_legs = self._get_ib_futures_contract_from_cache(contract_object_to_use=contract_object_to_use,
                                                                        trade_list_for_multiple_legs=trade_list_for_multiple_legs)
        if ibcontract_with_legs is missing_contract:
            ibcontract_with_legs = self._get_ib_futures_contract_from_broker(
                contract_object_to_use,
                trade_list_for_multiple_legs=trade_list_for_multiple_legs,
            )
            self._store_contract_in_cache(contract_object_to_use=contract_object_to_use,
                                          trade_list_for_multiple_legs=trade_list_for_multiple_legs,
                                          ibcontract_with_legs=ibcontract_with_legs)

        return ibcontract_with_legs

    @property
    def contract_cache(self):
        if getattr(self, "_futures_contract_cache", None) is None:
            self._futures_contract_cache = {}

        cache = self._futures_contract_cache

        return cache

    def _get_ib_futures_contract_from_cache(self, contract_object_to_use: futuresContract,
                                            trade_list_for_multiple_legs: tradeQuantity = None) -> ibcontractWithLegs:

        key = self._get_contract_cache_key(contract_object_to_use=contract_object_to_use,
                                           trade_list_for_multiple_legs=trade_list_for_multiple_legs)
        cache = self.contract_cache
        ibcontract_with_legs = cache.get(key, missing_contract)

        return ibcontract_with_legs

    def _store_contract_in_cache(self,  contract_object_to_use: futuresContract,
                                 ibcontract_with_legs: ibcontractWithLegs,
                                 trade_list_for_multiple_legs: tradeQuantity = None
                                 ):
        cache = self.contract_cache
        key = self._get_contract_cache_key(contract_object_to_use=contract_object_to_use,
                                           trade_list_for_multiple_legs=trade_list_for_multiple_legs)

        cache[key] = ibcontract_with_legs

    def _get_contract_cache_key(self, contract_object_to_use: futuresContract,
                                            trade_list_for_multiple_legs: tradeQuantity = None) -> str:

        if not contract_object_to_use.is_spread_contract():
            trade_list_suffix = ""
        else:
            # WANT TO TREAT EG -2,2 AND -4,4 AS THE SAME BUT DIFFERENT FROM
            # -2,1 OR -1,2,-1...
            trade_list_suffix = str(
                list_of_ints_with_highest_common_factor_positive_first(
                    trade_list_for_multiple_legs
                )
            )

        key = contract_object_to_use.key + trade_list_suffix

        return key

    def _get_ib_futures_contract_from_broker(
        self, contract_object_with_ib_data: futuresContract,
            trade_list_for_multiple_legs: tradeQuantity=None
    ) -> ibcontractWithLegs:
        """
        Return a complete and unique IB contract that matches futures_contract_object
        This is expensive so not called directly, only by ib_futures_contract which does caching

        :param contract_object_with_ib_data: contract, containing instrument metadata suitable for IB
        :return: a single ib contract object
        """
        # Convert to IB world
        futures_instrument_with_ib_data = contract_object_with_ib_data.instrument
        contract_date = contract_object_with_ib_data.contract_date

        if contract_object_with_ib_data.is_spread_contract():
            ibcontract_with_legs = self._get_spread_ib_futures_contract(
                futures_instrument_with_ib_data,
                contract_date,
                trade_list_for_multiple_legs=trade_list_for_multiple_legs,
            )
        else:
            ibcontract_with_legs = self._get_vanilla_ib_futures_contract_with_legs(futures_instrument_with_ib_data=futures_instrument_with_ib_data,
                                                                                   contract_date=contract_date)

        return ibcontract_with_legs

    def _get_vanilla_ib_futures_contract_with_legs(
        self, futures_instrument_with_ib_data: futuresInstrumentWithIBConfigData,
            contract_date: contractDate
    ) -> ibcontractWithLegs:

        ibcontract = self._get_vanilla_ib_futures_contract(
            futures_instrument_with_ib_data,
            contract_date,
        )
        legs = []

        return ibcontractWithLegs(ibcontract, legs)


    def _get_spread_ib_futures_contract(
        self,
        futures_instrument_with_ib_data: futuresInstrumentWithIBConfigData,
        contract_date: contractDate,
        trade_list_for_multiple_legs: tradeQuantity=None,
    ) -> ibcontractWithLegs:
        """
        Return a complete and unique IB contract that matches contract_object_with_ib_data
        This is expensive so not called directly, only by ib_futures_contract which does caching

        :param contract_object_with_ib_data: contract, containing instrument metadata suitable for IB
        :return: a single ib contract object
        """
        if trade_list_for_multiple_legs is None:
            raise Exception("Multiple leg order must have trade list")

        # Convert to IB world
        ibcontract = ib_futures_instrument(futures_instrument_with_ib_data)
        ibcontract.secType = "BAG"

        list_of_contract_dates = contract_date.list_of_single_contract_dates
        resolved_legs = [
            self._get_vanilla_ib_futures_contract(
                futures_instrument_with_ib_data, contract_date
            )
            for contract_date in list_of_contract_dates
        ]

        ibcontract_with_legs = _add_legs_to_ib_contract(ibcontract = ibcontract,
                                                        resolved_legs = resolved_legs,
                                                        trade_list_for_multiple_legs=trade_list_for_multiple_legs)

        return ibcontract_with_legs


    def _get_vanilla_ib_futures_contract(
        self, futures_instrument_with_ib_data: futuresInstrumentWithIBConfigData,
            contract_date: contractDate
    ) -> Contract:
        """
        Return a complete and unique IB contract that matches contract_object_with_ib_data
        This is expensive so not called directly, only by ib_futures_contract which does caching

        :param contract_object_with_ib_data: contract, containing instrument metadata suitable for IB
        :return: a single ib contract object
        """

        ibcontract = get_ib_contract_with_specific_expiry(contract_date=contract_date,
                                                          futures_instrument_with_ib_data = futures_instrument_with_ib_data)

        # We could get multiple contracts here in case we have 'yyyymm' and not
        #    specified expiry date for VIX
        ibcontract_list = self.ib_get_contract_chain(ibcontract)

        try:
            resolved_contract = resolve_unique_contract_from_ibcontract_list(ibcontract_list=ibcontract_list,
                                                                             futures_instrument_with_ib_data=futures_instrument_with_ib_data)
        except Exception as exception:
            self.log.warn(
                "%s could not resolve contracts: %s"
                % (str(futures_instrument_with_ib_data), exception.args[0])
            )
            return missing_contract

        return resolved_contract

    def ib_resolve_unique_contract(self, ibcontract_pattern, log:logger=None):
        """
        Returns the 'resolved' IB contract based on a pattern. We expect a unique contract.

        This is used for FX only, since for futures things are potentially funkier

        :param ibcontract_pattern: ibContract
        :param log: log object
        :return: ibContract or missing_contract
        """
        if log is None:
            log = self.log

        contract_chain = self.ib_get_contract_chain(ibcontract_pattern)

        if len(contract_chain) > 1:
            log.warn(
                "Got multiple contracts for %s when only expected a single contract: Check contract date" %
                str(ibcontract_pattern))
            return missing_contract

        if len(contract_chain) == 0:
            log.warn("Failed to resolve contract %s" % str(ibcontract_pattern))
            return missing_contract

        resolved_contract = contract_chain[0]

        return resolved_contract

    def ib_get_contract_with_conId(self, symbol: str, conId) -> Contract:
        contract_chain = self._get_contract_chain_for_symbol(symbol)
        conId_list = [contract.conId for contract in contract_chain]
        try:
            contract_idx = conId_list.index(conId)
        except ValueError:
            return missing_contract

        required_contract = contract_chain[contract_idx]

        return required_contract

    def _get_contract_chain_for_symbol(self, symbol: str) -> list:
        ibcontract_pattern = ib_futures_instrument_just_symbol(symbol)
        contract_chain = self.ib_get_contract_chain(ibcontract_pattern)

        return contract_chain

    def ib_get_contract_chain(self, ibcontract_pattern: Contract) -> list:
        """
        Get all the IB contracts matching a pattern.

        :param ibcontract_pattern: ibContract which may not fully specify the contract
        :return: list of ibContracts
        """

        new_contract_details_list = self.ib.reqContractDetails(
            ibcontract_pattern)

        ibcontract_list = [
            contract_details.contract for contract_details in new_contract_details_list]

        return ibcontract_list

