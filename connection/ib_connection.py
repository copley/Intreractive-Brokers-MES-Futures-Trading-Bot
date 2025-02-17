import logging
import threading
# Import IB API classes if available
try:
    from ibapi.client import EClient
    from ibapi.wrapper import EWrapper
except ImportError:
    EClient = object
    EWrapper = object

class IBApi(EWrapper, EClient):
    """
    IBApi combines EWrapper and EClient to interact with IB TWS/Gateway.
    It will handle incoming and outgoing messages with IB's API.
    """
    def __init__(self):
        EClient.__init__(self, self)
        # You can initialize any required variables here (e.g., currentOrderId, etc.)
        self.nextOrderId = None

    # Overriding EWrapper methods for connection and next valid order ID
    def nextValidId(self, orderId: int):
        super().nextValidId(orderId)
        self.nextOrderId = orderId
        logging.info(f"Received next valid Order ID: {orderId}")

    def error(self, reqId, errorCode, errorString):
        logging.error(f"IB Error {errorCode} (reqId {reqId}): {errorString}")

class IBConnection:
    """
    Manages connection to Interactive Brokers TWS or Gateway.
    Provides methods to connect, disconnect, and place orders.
    """
    def __init__(self, host: str, port: int, client_id: int):
        self.app = IBApi()
        logging.info(f"Connecting to IB on {host}:{port} with client ID {client_id}...")
        self.app.connect(host, port, client_id)
        # Launch the IB API network thread
        self.thread = threading.Thread(target=self.app.run, daemon=True)
        self.thread.start()
        # Wait a short time for connection to establish
        logging.info("IB connection thread started.")

    def is_connected(self) -> bool:
        """Check if the IB connection is established."""
        # EClient.isConnected() can be used if available
        return hasattr(self.app, "isConnected") and self.app.isConnected()

    def disconnect(self):
        """Disconnect from IB."""
        if self.app:
            logging.info("Disconnecting from IB...")
            self.app.disconnect()
            if self.thread.is_alive():
                self.thread.join(timeout=1.0)
            logging.info("Disconnected from IB.")

    def place_order(self, contract, order):
        """
        Place an order via the IB API. Expects an IB contract and order object.
        """
        if not self.is_connected():
            logging.error("Cannot place order: not connected to IB.")
            return
        # Ensure we have a valid order ID
        if hasattr(self.app, "nextOrderId") and self.app.nextOrderId is not None:
            order_id = self.app.nextOrderId
            self.app.nextOrderId += 1  # increment for next order
        else:
            order_id = 1  # fallback order id
        logging.info(f"Placing order {order_id}: {order}")
        try:
            self.app.placeOrder(order_id, contract, order)
        except Exception as e:
            logging.exception(f"Order placement failed: {e}")
