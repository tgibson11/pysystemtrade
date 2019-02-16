import time

from sysbrokers.baseServer import finishableQueue
from syslogdiag.log import logtoscreen


ACCOUNT_VALUE_FLAG = "value"


class IbAccountData:

    def __init__(self, ib_connection, log=logtoscreen):
        self.ib_connection = ib_connection
        self.log = log
        # We use these to store accounting data
        self._account_cache = SimpleCache(max_staleness_seconds=5*60)
        # override function
        self._account_cache.update_data = self._update_accounting_data

    def __repr__(self):
        return "IB account data"

    def _update_accounting_data(self, account_name):
        """
        Update the accounting data in the cache
        :param account_name: account we want to get data for
        :return: nothing
        """

        # Make a place to store the data we're going to return
        accounting_queue = finishableQueue(self.ib_connection.init_accounts(account_name))

        # ask for the data
        self.ib_connection.reqAccountUpdates(True, account_name)

        # poll until we get a termination or die of boredom
        accounting_list = accounting_queue.get(timeout=10)

        while self.ib_connection.broker_is_error():
            print(self.ib_connection.broker_get_error())

        if accounting_queue.timed_out():
            print("Exceeded maximum wait for wrapper to confirm finished whilst getting accounting data")

        # separate things out, because this is one big queue of data with different things in it
        accounting_list = ListOfIdentifiedItems(accounting_list)
        separated_accounting_data = accounting_list.separate_into_dict()

        # update the cache with different elements
        self._account_cache.update_cache(account_name, separated_accounting_data)

        # return nothing, information is accessed via get_... methods

    def get_accounting_values(self, account_name):
        """
        Get the accounting values from IB server
        :return: accounting values as served up by IB
        """

        # All these functions follow the same pattern: check if stale, if not return cache, else update values

        return self._account_cache.get_updated_cache(account_name, ACCOUNT_VALUE_FLAG)

    def get_accounting_value(self, account_name, key):
        values = self.get_accounting_values(account_name)
        val = [item for item in values if item[0] == key][0][1]
        return val


# cache used for accounting data
class SimpleCache(object):
    """
    Cache is stored in _cache in nested dict, outer key is accountName, inner key is cache label
    """

    STALE = True
    NOT_STALE = False

    CACHE_EMPTY = True
    CACHE_PRESENT = False

    def __init__(self, max_staleness_seconds):
        self._cache = dict()
        self._cache_updated_local_time = dict()

        self._max_staleness_seconds = max_staleness_seconds

    def __repr__(self):
        return "Cache with labels" + ",".join(self._cache.keys())

    def update_data(self, account_name):
        raise Exception("You need to set this method in an inherited class")

    def _get_last_updated_time(self, account_name, cache_label):
        if account_name not in self._cache_updated_local_time.keys():
            return None

        if cache_label not in self._cache_updated_local_time[account_name]:
            return None

        return self._cache_updated_local_time[account_name][cache_label]

    def _set_time_of_updated_cache(self, account_name, cache_label):
        # make sure we know when the cache was updated
        if account_name not in self._cache_updated_local_time.keys():
            self._cache_updated_local_time[account_name] = {}

        self._cache_updated_local_time[account_name][cache_label] = time.time()

    def _is_data_stale(self, account_name, cache_label, ):
        """
        Check to see if the cached data has been updated recently for a given account and label, or if it's stale
        :return: bool
        """

        last_update = self._get_last_updated_time(account_name, cache_label)

        if last_update is None:
            # we haven't got any data, so by construction our data is stale
            return self.STALE

        time_now = time.time()
        time_since_updated = time_now - last_update

        if time_since_updated > self._max_staleness_seconds:
            return self.STALE
        else:
            # recently updated
            return self.NOT_STALE

    def _check_cache_empty(self, account_name, cache_label):
        """
        :param account_name: str
        :param cache_label: str
        :return: bool
        """

        cache = self._cache
        if account_name not in cache.keys():
            return self.CACHE_EMPTY

        cache_this_account = cache[account_name]
        if cache_label not in cache_this_account.keys():
            return self.CACHE_EMPTY

        return self.CACHE_PRESENT

    def _return_cache_values(self, account_name, cache_label):
        """
        :param account_name: str
        :param cache_label: str
        :return: None or cache contents
        """

        if self._check_cache_empty(account_name, cache_label):
            return None

        return self._cache[account_name][cache_label]

    def _create_cache_element(self, account_name, cache_label):

        cache = self._cache
        if account_name not in cache.keys():
            cache[account_name] = {}

        cache_this_account = cache[account_name]
        if cache_label not in cache_this_account.keys():
            cache[account_name][cache_label] = None

    def get_updated_cache(self, account_name, cache_label):
        """
        Checks for stale cache, updates if needed, returns up to date value
        :param account_name: str
        :param cache_label:  str
        :return: updated part of cache
        """

        if self._is_data_stale(account_name, cache_label) or self._check_cache_empty(account_name, cache_label):
            self.update_data(account_name)

        return self._return_cache_values(account_name, cache_label)

    def update_cache(self, account_name, dict_with_data):
        """
        :param account_name: str
        :param dict_with_data: dict, which has keynames with cache labels
        :return: nothing
        """

        all_labels = dict_with_data.keys()
        for cache_label in all_labels:
            self._create_cache_element(account_name, cache_label)
            self._cache[account_name][cache_label] = dict_with_data[cache_label]
            self._set_time_of_updated_cache(account_name, cache_label)


class ListOfIdentifiedItems(list):
    """
    A list of elements, each of class identified_as (or duck equivalent)
    Used to separate out accounting data
    """

    def separate_into_dict(self):
        """
        :return: dict, keys are labels, each element is a list of items matching label
        """

        all_labels = [element.label for element in self]
        dict_data = dict([
            (label,
             [element.data for element in self if element.label == label])
            for label in all_labels])

        return dict_data
