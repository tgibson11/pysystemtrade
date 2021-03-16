from syslogdiag.log_to_screen import logtoscreen
from syscore.objects import missing_data
lock_on = "ON"
lock_off = "OFF"


class lockData(object):
    def __init__(self, log=logtoscreen("Locks")):
        self.log = log

    def is_instrument_locked(self, instrument_code: str)-> bool:
        if self.get_lock_for_instrument(instrument_code) == lock_on:
            return True
        else:
            return False

    def get_lock_for_instrument(self, instrument_code: str) -> str:

        lock = self._get_lock_for_instrument_no_checking(instrument_code)
        if lock is missing_data:
            return lock_off

        return lock

    def add_lock_for_instrument(self, instrument_code: str):
        raise NotImplementedError

    def remove_lock_for_instrument(self, instrument_code: str):
        raise NotImplementedError

    def get_list_of_locked_instruments(self) -> list:
        raise NotImplementedError

    def _get_lock_for_instrument_no_checking(self, instrument_code: str) -> str:
        raise NotImplementedError