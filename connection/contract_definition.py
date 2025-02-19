# File: /home/student/MES/connection/contract_definition.py

import logging
try:
    from ibapi.contract import Contract
except ImportError:
    Contract = None

def create_contract(symbol: str,
                    sec_type: str,
                    exchange: str,
                    currency: str,
                    last_trade_date: str = None,
                    local_symbol: str = None,
                    multiplier: str = None):
    """
    Create and return an Interactive Brokers Contract object.
    """
    if Contract is None:
        logging.warning("IB API is not available. Returning contract info as dict.")
        return {
            "symbol": symbol,
            "secType": sec_type,
            "exchange": exchange,
            "currency": currency,
            "lastTradeDateOrContractMonth": last_trade_date,
            "localSymbol": local_symbol,
            "multiplier": multiplier
        }

    contract = Contract()
    contract.symbol = symbol
    contract.secType = sec_type
    contract.exchange = exchange
    contract.currency = currency

    if last_trade_date:
        contract.lastTradeDateOrContractMonth = last_trade_date
    if local_symbol:
        contract.localSymbol = local_symbol
    if multiplier:
        contract.multiplier = multiplier

    logging.info(f"Contract created: {symbol} {sec_type} on {exchange} in {currency}")
    return contract
