import logging
# Import IB API Contract class if available
try:
    from ibapi.contract import Contract
except ImportError:
    Contract = None

def create_contract(symbol: str, sec_type: str, exchange: str, currency: str):
    """
    Create and return an Interactive Brokers Contract object for the given parameters.
    """
    if Contract is None:
        logging.warning("IB API is not available. Returning contract info as dict.")
        # Fallback: return contract details as a dictionary if IB API is not installed
        return {"symbol": symbol, "secType": sec_type, "exchange": exchange, "currency": currency}
    contract = Contract()
    contract.symbol = symbol
    contract.secType = sec_type
    contract.exchange = exchange
    contract.currency = currency
    logging.info(f"Contract created: {symbol} {sec_type} on {exchange} in {currency}")
    return contract
