from syslogdiag.log import accessLogFromMongodb


def clean_truncate_log_files():
    mlog = accessLogFromMongodb()
    mlog.delete_log_items_from_before_n_days(days=365)


if __name__ == '__main__':
    clean_truncate_log_files()
