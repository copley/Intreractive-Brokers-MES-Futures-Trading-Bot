from ib_insync import IB, Contract, Order
from datetime import datetime

def place_scalping_bracket_order():
    """
    Place a market order, retrieve the fill price, and create OCA stop-loss and limit orders.
    """
    ib = IB()
    try:
        # Connect to TWS or IB Gateway
        ib.connect('127.0.0.1', 7497, clientId=21)

        # Define the hard-coded XINA50 contract
        contract = Contract()
        contract.symbol = "XINA50"
        contract.secType = "FUT"
        contract.exchange = "SGX"
        contract.currency = "USD"
        contract.lastTradeDateOrContractMonth = "20250124"  # Hard-coded expiry
        contract.localSymbol = "CNF25"  # Hard-coded local symbol
        contract.multiplier = "1"

        # Ensure the contract is valid
        ib.qualifyContracts(contract)
        contractQuantity = 5
        # Step 1: Place a market order
        market_order = Order()
        market_order.action = 'BUY'  # Change to 'SELL' for short position
        market_order.totalQuantity = contractQuantity
        market_order.orderType = 'MKT'
        market_order.transmit = True  # Transmit immediately

        print("[INFO] Placing market order...")
        trade = ib.placeOrder(contract, market_order)

        # Wait for the market order to fill
        timeout = 10  # Timeout in seconds
        while not trade.isDone() and timeout > 0:
            ib.sleep(1)
            timeout -= 1

        if not trade.isDone():
            raise RuntimeError("[ERROR] Market order did not fill in time.")

        if trade.orderStatus.status != 'Filled':
            raise RuntimeError("[ERROR] Market order failed to execute.")

        # Retrieve the fill price
        fill_price = trade.orderStatus.avgFillPrice
        print(f"[INFO] Market order filled at {fill_price}.")

        # Step 2: Calculate OCA prices
        stop_price = round(fill_price - 5, 1)  # 5 points below entry for stop-loss
        limit_price = round(fill_price + 5, 1)  # 5 points above entry for profit target
        print(f"[DEBUG] Stop-loss price: {stop_price}, Limit price: {limit_price}")

        # Step 3: Create OCA stop-loss and limit orders
        oca_group = f"OCA#{datetime.now().strftime('%Y%m%d%H%M%S')}"

        # Stop-loss order
        stop_loss_order = Order()
        stop_loss_order.action = 'SELL'  # Opposite of market order
        stop_loss_order.totalQuantity = contractQuantity
        stop_loss_order.orderType = 'STP'
        stop_loss_order.auxPrice = stop_price
        stop_loss_order.ocaGroup = oca_group
        stop_loss_order.ocaType = 1  # Cancel the other order if executed
        stop_loss_order.transmit = True  # Do not transmit until limit order is ready

        # Limit order
        limit_order = Order()
        limit_order.action = 'SELL'  # Opposite of market order
        limit_order.totalQuantity = contractQuantity
        limit_order.orderType = 'LMT'
        limit_order.lmtPrice = limit_price
        limit_order.ocaGroup = oca_group
        limit_order.ocaType = 1  # Cancel the other order if executed
        limit_order.transmit = True  # Transmit the entire OCA group

        # Step 4: Place the OCA orders with a small delay between them
        print(f"[INFO] Placing stop-loss order at {stop_price}...")
        ib.placeOrder(contract, stop_loss_order)
        ib.sleep(0.1)  # Small delay to ensure proper sequencing

        print(f"[INFO] Placing limit order at {limit_price}...")
        ib.placeOrder(contract, limit_order)

        print(f"[INFO] Stop-loss and limit orders placed successfully.")
    finally:
        # Disconnect from TWS/IB Gateway
        ib.disconnect()


# Example Usage
if __name__ == "__main__":
    place_scalping_bracket_order()
