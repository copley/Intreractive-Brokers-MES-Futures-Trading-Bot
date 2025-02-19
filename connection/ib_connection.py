# File: /home/student/MES/connection/ib_connection.py

import logging
import threading
from datetime import datetime

try:
    from ibapi.client import EClient
    from ibapi.wrapper import EWrapper
    from ibapi.common import BarData
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
        self.nextOrderId = None

        # Store historical data results here
        self._historical_data = []
        # Event used to signal that the historical data download is done
        self._historical_data_done = threading.Event()

    def nextValidId(self, orderId: int):
        super().nextValidId(orderId)
        self.nextOrderId = orderId
        logging.info(f"Received next valid Order ID: {orderId}")

    def error(self, reqId, errorCode, errorString):
        # Some IB "error" codes are actually just info messages about data farms, etc.
        logging.error(f"IB Error {errorCode} (reqId {reqId}): {errorString}")

    # -------------------------------------------------------------------------
    # Historical Data Callbacks
    # -------------------------------------------------------------------------
    def historicalData(self, reqId, bar):
        """
        Called for each bar of historical data.
        'bar' is an object of type BarData with fields:
            date, open, high, low, close, volume, barCount, WAP
        """
        # Convert the bar to a dictionary
        try:
            bar_time = datetime.strptime(bar.date, "%Y%m%d  %H:%M:%S")
        except ValueError:
            # Sometimes IB returns a date like '20230615', meaning daily or larger timeframe
            # If you need intraday bars, it should return "YYYYMMDD HH:MM:SS".
            bar_time = datetime.strptime(bar.date, "%Y%m%d")

        bar_dict = {
            "time": bar_time,
            "open": bar.open,
            "high": bar.high,
            "low": bar.low,
            "close": bar.close,
            "volume": bar.volume
        }
        self._historical_data.append(bar_dict)

    def historicalDataEnd(self, reqId, start, end):
        """
        Called once all requested historical bars have been received.
        """
        logging.info(
            f"Historical data download complete. "
            f"Received {len(self._historical_data)} bars."
        )
        # Signal that the data is done
        self._historical_data_done.set()

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
        if hasattr(self.app, "isConnected"):
            return self.app.isConnected()
        return False

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
