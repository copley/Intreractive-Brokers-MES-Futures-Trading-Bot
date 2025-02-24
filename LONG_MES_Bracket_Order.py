from ibapi.client import EClient
from ibapi.wrapper import EWrapper
from ibapi.contract import Contract
from ibapi.order import Order
from ibapi.common import OrderId
from concurrent.futures import ThreadPoolExecutor
import threading
import time

class BracketOrderApp(EWrapper, EClient):
    def __init__(self):
        EClient.__init__(self, self)
        self.next_order_id = None
        self.executor = ThreadPoolExecutor(max_workers=3)  # For concurrent processing

    def connect_and_start(self):
        print("Connecting to IB Gateway/TWS...")
        self.connect("127.0.0.1", 7497, clientId=2)

        thread = threading.Thread(target=self.run)
        thread.start()

        # Use an event-based approach to wait for connection
        self.executor.submit(self.wait_for_order_id)

    def wait_for_order_id(self):
        # Wait for the next valid order ID to be set
        while self.next_order_id is None:
            time.sleep(0.1)  # Use a short, non-blocking sleep for responsiveness

        # Once connected, start placing orders
        contract = self.create_mes_contract()
        self.place_short_bracket_order(contract)

    def create_mes_contract(self):
        contract = Contract()
        contract.symbol = "MES"  # Micro E-mini S&P 500
        contract.secType = "FUT"  # Futures contract
        contract.exchange = "CME"  # Chicago Mercantile Exchange (CME)
        contract.currency = "USD"  # U.S. Dollar
        contract.lastTradeDateOrContractMonth = "202412"  # DEC 2024 contract
        return contract

    def place_short_bracket_order(self, contract):
        parent_order_id = self.next_order_id
        take_profit_order_id = parent_order_id + 1
        stop_loss_order_id = parent_order_id + 2

        # Create parent, take-profit, and stop-loss orders
        parent_order = self.create_order(parent_order_id, "SELL", "MKT", 1, transmit=False)
        take_profit_order = self.create_order(take_profit_order_id, "BUY", "LMT", 1, transmit=False, lmtPrice=5820.00)
        stop_loss_order = self.create_order(stop_loss_order_id, "BUY", "STP", 1, transmit=True, auxPrice=5845.00)

        # Set parent-child relationships
        take_profit_order.parentId = parent_order_id
        stop_loss_order.parentId = parent_order_id

        # Submit orders concurrently for faster processing
        self.executor.submit(self.placeOrder, parent_order_id, contract, parent_order)
        self.executor.submit(self.placeOrder, take_profit_order_id, contract, take_profit_order)
        self.executor.submit(self.placeOrder, stop_loss_order_id, contract, stop_loss_order)

        print("Short bracket order placed with take-profit and stop-loss.")
        self.next_order_id += 3

    def create_order(self, order_id, action, order_type, quantity, transmit, lmtPrice=None, auxPrice=None):
        order = Order()
        order.orderId = order_id
        order.action = action
        order.orderType = order_type
        order.totalQuantity = quantity
        order.transmit = transmit
        if lmtPrice is not None:
            order.lmtPrice = lmtPrice
        if auxPrice is not None:
            order.auxPrice = auxPrice
        return order

    def nextValidId(self, orderId: OrderId):
        super().nextValidId(orderId)
        self.next_order_id = orderId
        print(f"Next valid order ID: {orderId}")

    def error(self, reqId, errorCode, errorString, advancedOrderRejectJson=None):
        print(f"Error: {reqId}, {errorCode}, {errorString}")
        if advancedOrderRejectJson:
            print(f"Advanced Order Reject Info: {advancedOrderRejectJson}")
        # Attempt to reconnect if there's a critical error
        if errorCode == 1100:  # "Connectivity between IB and TWS has been lost"
            self.reconnect()

    def reconnect(self):
        print("Reconnecting to IB Gateway/TWS...")
        self.disconnect()
        time.sleep(2)  # Give some time before reconnecting
        self.connect_and_start()

def main():
    app = BracketOrderApp()
    app.connect_and_start()

    # Use event-driven or callback-based looping
    try:
        while True:
            time.sleep(0.1)
    except KeyboardInterrupt:
        print("Disconnecting...")
        app.disconnect()

if __name__ == "__main__":
    main()
