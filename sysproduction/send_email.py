from sysdata.data_blob import dataBlob
from syslogdiag.email_via_db_interface import send_production_mail_msg


def send_email(subject: str, body: str = ""):
    data_for_logging = dataBlob()
    always_send_dont_store = True
    send_production_mail_msg(
        data_for_logging,
        body,
        subject,
        email_is_report=always_send_dont_store,
    )
