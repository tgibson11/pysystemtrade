import queue
import time

ACCOUNT_UPDATE_FLAG = "update"
ACCOUNT_VALUE_FLAG = "value"
ACCOUNT_TIME_FLAG = "time"


class identified_as(object):
    """
    Used to identify
    """

    def __init__(self, label, data):
        self.label = label
        self.data = data

    def __repr__(self):
        return "Identified as %s" % self.label


class list_of_identified_items(list):
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


# cache used for accounting data
class simpleCache(object):
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

    def update_data(self, accountName):
        raise Exception("You need to set this method in an inherited class")

    def _get_last_updated_time(self, accountName, cache_label):
        if accountName not in self._cache_updated_local_time.keys():
            return None

        if cache_label not in self._cache_updated_local_time[accountName]:
            return None

        return self._cache_updated_local_time[accountName][cache_label]

    def _set_time_of_updated_cache(self, accountName, cache_label):
        # make sure we know when the cache was updated
        if accountName not in self._cache_updated_local_time.keys():
            self._cache_updated_local_time[accountName] = {}

        self._cache_updated_local_time[accountName][cache_label] = time.time()

    def _is_data_stale(self, accountName, cache_label, ):
        """
        Check to see if the cached data has been updated recently for a given account and label, or if it's stale
        :return: bool
        """

        last_update = self._get_last_updated_time(accountName, cache_label)

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

    def _check_cache_empty(self, accountName, cache_label):
        """
        :param accountName: str
        :param cache_label: str
        :return: bool
        """

        cache = self._cache
        if accountName not in cache.keys():
            return self.CACHE_EMPTY

        cache_this_account = cache[accountName]
        if cache_label not in cache_this_account.keys():
            return self.CACHE_EMPTY

        return self.CACHE_PRESENT

    def _return_cache_values(self, accountName, cache_label):
        """
        :param accountName: str
        :param cache_label: str
        :return: None or cache contents
        """

        if self._check_cache_empty(accountName, cache_label):
            return None

        return self._cache[accountName][cache_label]

    def _create_cache_element(self, accountName, cache_label):

        cache = self._cache
        if accountName not in cache.keys():
            cache[accountName] = {}

        cache_this_account = cache[accountName]
        if cache_label not in cache_this_account.keys():
            cache[accountName][cache_label] = None

    def get_updated_cache(self, accountName, cache_label):
        """
        Checks for stale cache, updates if needed, returns up to date value
        :param accountName: str
        :param cache_label:  str
        :return: updated part of cache
        """

        if self._is_data_stale(accountName, cache_label) or self._check_cache_empty(accountName, cache_label):
            self.update_data(accountName)

        return self._return_cache_values(accountName, cache_label)

    def update_cache(self, accountName, dict_with_data):
        """
        :param accountName: str
        :param dict_with_data: dict, which has keynames with cache labels
        :return: nothing
        """

        all_labels = dict_with_data.keys()
        for cache_label in all_labels:
            self._create_cache_element(accountName, cache_label)
            self._cache[accountName][cache_label] = dict_with_data[cache_label]
            self._set_time_of_updated_cache(accountName, cache_label)


class finishableQueue(object):
    """
    Creates a queue which will finish at some point
    """

    # marker for when queue is finished
    FINISHED = object()
    STARTED = object()
    TIME_OUT = object()

    def __init__(self, queue_to_finish):

        self._queue = queue_to_finish
        self.status = self.STARTED

    def get(self, timeout):
        """
        Returns a list of queue elements once timeout is finished, or a FINISHED flag is received in the queue
        :param timeout: how long to wait before giving up
        :return: list of queue elements
        """
        contents_of_queue = []
        finished = False

        while not finished:
            try:
                current_element = self._queue.get(timeout=timeout)
                if current_element is self.FINISHED:
                    finished = True
                    self.status = self.FINISHED
                else:
                    contents_of_queue.append(current_element)
                    # keep going and try and get more data

            except queue.Empty:
                # If we hit a time out it's most probable we're not getting a finished element any time soon
                # give up and return what we have
                finished = True
                self.status = self.TIME_OUT

        return contents_of_queue

    def timed_out(self):
        return self.status is self.TIME_OUT
