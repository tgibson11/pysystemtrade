from sysbrokers.IB.ib_futures_contract_price_data import ibFuturesContractPriceData
from sysbrokers.broker_factory import get_ib_class_list
from sysdata.barchart.bc_futures_contract_price_data import BarchartFuturesContractPriceData


def get_ib_class_list_with_barchart() -> list:
    ib_class_list = get_ib_class_list()
    ib_class_list.remove(ibFuturesContractPriceData)
    ib_class_list.append(BarchartFuturesContractPriceData)
    return ib_class_list
