from ib_insync import IB, Future

def connect_to_ib():
    """
    Connect to IB API and return an IB object.
    """
    ib = IB()
    ib.connect('127.0.0.1', 7497, clientId=8)  # Use unique client ID
    print("[INFO] Connected to IB API.")
    return ib

def fetch_contract_details(ib, symbol):
    """
    Fetch and print all available contract details for a given symbol.
    """
    contract = Future(symbol=symbol)
    details = ib.reqContractDetails(contract)

    if not details:
        print(f"[ERROR] No contract details found for symbol {symbol}.")
        return None

    # Print available contracts
    print(f"[INFO] Found {len(details)} contracts for {symbol}:")
    for detail in details:
        contract = detail.contract
        print(f"  - Symbol: {contract.symbol}, "
              f"Exchange: {contract.exchange}, "
              f"Expiry: {contract.lastTradeDateOrContractMonth}, "
              f"Currency: {contract.currency}, "
              f"LocalSymbol: {contract.localSymbol}")

    return details[0].contract  # Return the first valid contract

def request_market_data(ib, contract):
    """
    Request market data for a given contract.
    """
    print("[INFO] Requesting market data...")
    ticker = ib.reqMktData(contract)
    if not ticker:
        print("[ERROR] Market data request failed.")
    else:
        print(f"[INFO] Market data: {ticker}")

def print_contract_details(contract):
    """
    Print details of the given contract.
    """
    print("\n[INFO] Constructing contract definition:")
    print("   contract = Contract()")
    print(f"   contract.symbol = \"{contract.symbol}\"  # Symbol")
    print(f"   contract.secType = \"{contract.secType}\"  # Security Type")
    print(f"   contract.exchange = \"{contract.exchange}\"  # Exchange")
    print(f"   contract.currency = \"{contract.currency}\"  # Currency")
    print(f"   contract.lastTradeDateOrContractMonth = \"{contract.lastTradeDateOrContractMonth}\"  # Expiry")
    print(f"   contract.localSymbol = \"{contract.localSymbol}\"  # Local Symbol")
    print(f"   contract.multiplier = \"{contract.multiplier}\"  # Multiplier")

def main():
    ib = connect_to_ib()

    try:
        # Define the symbol
        symbol = 'MES'
        #symbol = 'MES'
        # Fetch the complete contract details dynamically
        contract = fetch_contract_details(ib, symbol)

        if contract:
            print(f"[INFO] Using contract: {contract}")
            # Request market data
            request_market_data(ib, contract)
            # Print contract details
            print_contract_details(contract)

    finally:
        # Disconnect from IB API
        ib.disconnect()
        print("[INFO] Disconnected from IB API.")

if __name__ == "__main__":
    main()
