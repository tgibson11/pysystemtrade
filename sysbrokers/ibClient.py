import queue

from ibapi.client import EClient

from sysbrokers.baseClient import brokerClient
from sysbrokers.ibUtils import simpleCache, finishableQueue, list_of_identified_items, \
    ACCOUNT_UPDATE_FLAG, ACCOUNT_VALUE_FLAG


class ibClient(EClient, brokerClient):
    """
    Client specific to interactive brokers

    Overrides the methods in the base class specifically for IB

    """

    def __init__(self, wrapper):
        # Set up with a wrapper inside
        EClient.__init__(self, wrapper)
        # We use these to store accounting data
        self._account_cache = simpleCache(max_staleness_seconds=5*60)
        # override function
        self._account_cache.update_data = self._update_accounting_data

    def speakingClock(self):
        """
        Basic example to tell the time
        :return: unix time, as an int
        """

        print("Getting the time from the server... ")

        # Make a place to store the time we're going to return
        # This is a queue
        time_storage = self.wrapper.init_time()

        # This is the native method in EClient, asks the server to send us the time please
        self.reqCurrentTime()

        # Try and get a valid time
        try:
            current_time = time_storage.get(timeout=10)
        except queue.Empty:
            print("Exceeded maximum wait for wrapper to respond")
            current_time = None

        while self.wrapper.is_error():
            print(self.wrapper.get_error())

        return current_time

    def get_current_positions(self):
        """
        Current positions held
        :return:
        """

        # Make a place to store the data we're going to return
        positions_queue = finishableQueue(self.wrapper.init_positions())

        # ask for the data
        self.reqPositions()

        # poll until we get a termination or die of boredom
        positions_list = positions_queue.get(timeout=10)

        while self.wrapper.is_error():
            print(self.wrapper.get_error())

        if positions_queue.timed_out():
            print("Exceeded maximum wait for wrapper to confirm finished whilst getting positions")

        return positions_list

    def _update_accounting_data(self, accountName):
        """
        Update the accounting data in the cache
        :param accountName: account we want to get data for
        :return: nothing
        """

        # Make a place to store the data we're going to return
        accounting_queue = finishableQueue(self.wrapper.init_accounts(accountName))

        # ask for the data
        self.reqAccountUpdates(True, accountName)

        # poll until we get a termination or die of boredom
        accounting_list = accounting_queue.get(timeout=10)

        while self.wrapper.is_error():
            print(self.wrapper.get_error())

        if accounting_queue.timed_out():
            print("Exceeded maximum wait for wrapper to confirm finished whilst getting accounting data")

        # separate things out, because this is one big queue of data with different things in it
        accounting_list = list_of_identified_items(accounting_list)
        separated_accounting_data = accounting_list.separate_into_dict()

        # update the cache with different elements
        self._account_cache.update_cache(accountName, separated_accounting_data)

        # return nothing, information is accessed via get_... methods

    def get_accounting_values(self, accountName):
        """
        Get the accounting values from IB server
        :return: accounting values as served up by IB
        """

        # All these functions follow the same pattern: check if stale, if not return cache, else update values

        return self._account_cache.get_updated_cache(accountName, ACCOUNT_VALUE_FLAG)

    def get_accounting_updates(self, accountName):
        """
        Get the accounting updates from IB server
        :return: accounting updates as served up by IB
        """

        # All these functions follow the same pattern: check if stale, if not return cache, else update values

        return self._account_cache.get_updated_cache(accountName, ACCOUNT_UPDATE_FLAG)
