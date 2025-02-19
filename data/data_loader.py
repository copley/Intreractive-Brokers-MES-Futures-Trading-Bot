# File: /home/student/MES/data/data_loader.py

import logging
from datetime import datetime, timezone
import time

class DataLoader:
    """
    Responsible for loading historical market data required for indicators and strategy.
    """
    def __init__(self, ib_connection, contract):
        self.ib = ib_connection  # This is your IBConnection object
        self.contract = contract

    def fetch_historical_data(self, days: int, bar_size: str):
        """
        Fetch real OHLCV data from IB for the specified number of days and bar size.
        Returns data as a list of dict bars: [{'time', 'open', 'high', 'low', 'close', 'volume'}, ...]
        """
        if not self.ib.is_connected():
            logging.error("Not connected to IB; cannot fetch historical data.")
            return []

        # Clear old data from the IBApi object
        self.ib.app._historical_data = []
        self.ib.app._historical_data_done.clear()

        # Use IB's recommended date-time format with explicit time zone, e.g. UTC
        # Format: YYYYMMDD-HH:MM:SS <TIMEZONE>
        end_time = datetime.now(timezone.utc).strftime("%Y%m%d-%H:%M:%S")

        duration = f"{days} D"  # e.g. "1 D" for 1 day

        logging.info(f"Requesting real historical data: last {days} day(s), bar size = {bar_size}")
        logging.info(f"Using endDateTime = {end_time} (UTC)")

        try:
            self.ib.app.reqHistoricalData(
                reqId=1,  # Just an ID you pick
                contract=self.contract,
                endDateTime=end_time,       # <-- explicit time zone
                durationStr=duration,
                barSizeSetting=bar_size,
                whatToShow="TRADES",        # or "MIDPOINT", etc.
                useRTH=0,                   # 0 = all hours, 1 = regular trading hours only
                formatDate=1,
                keepUpToDate=False,
                chartOptions=[]
            )
        except Exception as e:
            logging.error(f"Historical data request failed: {e}")
            return []

        # Wait up to 30 seconds for the data to arrive
        wait_seconds = 30
        logging.info(f"Waiting up to {wait_seconds}s for historical data to complete...")
        finished = self.ib.app._historical_data_done.wait(timeout=wait_seconds)

        if not finished:
            logging.warning("Timeout waiting for historical data. Returning partial data.")
        else:
            logging.info("Historical data download signaled complete.")

        data = self.ib.app._historical_data
        logging.info(f"Fetched {len(data)} bars from IB.")
        return data
