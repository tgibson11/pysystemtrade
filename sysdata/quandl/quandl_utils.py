from sysdata.config.production_config import get_production_config
from syscore.objects import missing_data


def load_private_key():
    """
    Tries to load a private key

    :return: key
    """
    dict_key = "quandl_key"

    key = getattr(get_production_config(), dict_key)
    if key is missing_data:
        # no private key
        print("No private key found for QUANDL - you will be subject to data limits")
        key = None

    return key
