import datetime
import sqlite3
from typing import Callable

from syscore.constants import arg_not_supplied
from sysdata.sqlite.sqlite_data import sqliteData, _row_to_dict
from syslogdiag.email_control import emailControlData
from syslogging.logger import get_logger

TABLE_NAME = "email_control"

# Columns
TYPE = "type"
SUBJECT = "subject"
DATE = "datetime"
BODY = "body"

# Type values
LAST_EMAIL_SENT = "last_email_sent"
LAST_WARNING_SENT = "last_warning_sent"
STORED_MSG = "stored_message"

COLUMN_DEFS = [
    f"{TYPE} TEXT",
    f"{SUBJECT} TEXT",
    f"{DATE} DATETIME",
    f"{BODY} TEXT",
    f"PRIMARY KEY ({TYPE}, {SUBJECT})",
]


class sqliteEmailControlData(emailControlData, sqliteData):
    def __init__(
        self,
        sqlite_conn: sqlite3.Connection = arg_not_supplied,
        log=get_logger("sqliteEmailControlData")
    ):
        emailControlData.__init__(self, log=log)
        sqliteData.__init__(self, sqlite_conn=sqlite_conn)

    def __repr__(self):
        return "sqliteEmailControlData"

    @property
    def table_name(self) -> str:
        return TABLE_NAME

    @property
    def column_defs(self) -> list:
        return COLUMN_DEFS

    @property
    def _row_factory(self) -> Callable:
        return _email_control_factory

    def get_time_last_email_sent_with_this_subject(self, subject):
        result_as_datetime = self._get_time_last_email_of_type_sent_with_this_subject(
            subject, LAST_EMAIL_SENT
        )

        return result_as_datetime

    def get_time_last_warning_email_sent_with_this_subject(self, subject):
        result_as_datetime = self._get_time_last_email_of_type_sent_with_this_subject(
            subject, LAST_WARNING_SENT
        )

        return result_as_datetime

    def _get_time_last_email_of_type_sent_with_this_subject(self, subject, email_type):
        params = {
            TYPE: email_type,
            SUBJECT: subject,
        }
        result_dict = self._select_one(params)

        time_last_sent = result_dict[DATE]

        return time_last_sent

    def record_date_of_email_send(self, subject):
        self._record_date_of_email_type_send(subject, email_type=LAST_EMAIL_SENT)

    def record_date_of_email_warning_send(self, subject):
        self._record_date_of_email_type_send(subject, email_type=LAST_WARNING_SENT)

    def _record_date_of_email_type_send(self, subject, email_type):
        datetime_now = datetime.datetime.now()
        params = {
            TYPE: email_type,
            SUBJECT: subject,
            DATE: datetime_now,
        }
        self._insert(params, allow_replace=True)


def _email_control_factory(cursor, row) -> dict:
    return _row_to_dict(cursor, row)
