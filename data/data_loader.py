import logging
from datetime import datetime, timedelta

class DataLoader:
    """
    Responsible for loading historical market data required for indicators and strategy.
    """
    def __init__(self, ib_connection, contract):
        self.ib = ib_connection
        self.contract = contract

    def fetch_historical_data(self, days: int, bar_size: str):
        """
        Fetch historical OHLCV data for the specified number of days and bar size.
        Returns data as a list of bars (each bar could be a dict with open, high, low, close, volume).
        """
        logging.info(f"Fetching historical data: last {days} day(s), bar size = {bar_size}.")
        data = []
        # If connected to IB, request historical data via IB API
        if self.ib and hasattr(self.ib.app, 'reqHistoricalData'):
            try:
                end_time = datetime.now()
                duration = f"{days} D"  # e.g., "1 D" for 1 day
                # Use IB API to request historical data (this is a placeholder; actual IB call is asynchronous)
                # self.ib.app.reqHistoricalData(reqId=1, contract=self.contract, endDateTime=end_time.strftime("%Y%m%d %H:%M:%S"),
                #                               durationStr=duration, barSizeSetting=bar_size, whatToShow="MIDPOINT", useRTH=1, formatDate=1, keepUpToDate=False, chartOptions=[])
                # For demonstration, we'll simulate data as an empty list or dummy data.
            except Exception as e:
                logging.error(f"Historical data request failed: {e}")
        # Dummy data generation (for example purposes only)
        # In a real scenario, data would be populated by the IB callback (historicalData) with OHLCV values.
        now = datetime.now()
        for i in range(days * 390):  # assuming 390 minutes per trading day for 1-min bars
            # Generate a dummy price series (e.g., a simple random walk or sine wave)
            bar_time = now - timedelta(minutes=(days * 390 - i))
            price = 100 + (i * 0.01)  # dummy price that gradually increases
            bar = {
                "time": bar_time,
                "open": price,
                "high": price * 1.001,
                "low": price * 0.999,
                "close": price,
                "volume": 1000  # dummy volume
            }
            data.append(bar)
        logging.info(f"Historical data fetched: {len(data)} bars.")
        return data
