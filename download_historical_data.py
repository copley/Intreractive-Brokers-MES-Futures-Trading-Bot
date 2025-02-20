#!/usr/bin/env python3

"""
download_historical_bars.py

- Loads IB connection details + contract details from config.yaml
- Connects to IB
- Downloads historical bars (over a certain duration, bar size, etc.)
- Saves them to bars_data.csv in the format: time, open, high, low, close, volume

You can run it via:
    python3 download_historical_bars.py

Then feed bars_data.csv into your backtest with:
    python3 main.py --test --data bars_data.csv
"""

import csv
import logging
import time
from datetime import datetime
from threading import Thread, Event

# If you have the config loader in MES/utils/helpers.py:
from utils.helpers import load_config

from ibapi.client import EClient
from ibapi.wrapper import EWrapper
from ibapi.contract import Contract


class HistDataApp(EWrapper, EClient):
    def __init__(self):
        EClient.__init__(self, self)

        self.bars = []       # Store downloaded bars
        self.done = Event()  # Signals when historicalDataEnd is received

    def error(self, reqId, errorCode, errorString):
        if errorCode not in (2104, 2106, 2158):
            logging.error(f"[ERROR] ID={reqId} Code={errorCode} Msg={errorString}")

    def historicalData(self, reqId, bar):
        row = {
            "time":   bar.date,
            "open":   bar.open,
            "high":   bar.high,
            "low":    bar.low,
            "close":  bar.close,
            "volume": bar.volume
        }
        self.bars.append(row)

    def historicalDataEnd(self, reqId, start, end):
        logging.info(f"Historical data download complete: {len(self.bars)} bars.")
        self.done.set()


def main():
    # -------------------------------------------------------------
    # 1) Load config.yaml
    # -------------------------------------------------------------
    config = load_config("config.yaml")
    if not config:
        raise SystemExit("Failed to load config.yaml. Exiting.")

    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(message)s"
    )

    # -------------------------------------------------------------
    # 2) Pull out IB connection + contract details
    # -------------------------------------------------------------
    ib_cfg = config["interactive_brokers"]
    host = ib_cfg["host"]              # e.g. "127.0.0.1"
    port = ib_cfg["port"]              # e.g. 7496
    client_id = 3   # e.g. 34

    c = config["contract"]
    symbol = c["symbol"]               # e.g. "MES"
    sec_type = c["sec_type"]           # e.g. "FUT"
    exchange = c["exchange"]           # e.g. "CME"
    currency = c["currency"]           # e.g. "USD"
    last_trade = c["lastTradeDateOrContractMonth"]  # e.g. "20250321"
    local_symbol = c["localSymbol"]    # e.g. "MESH5"
    multiplier = c["multiplier"]       # e.g. "5"

    # If you store data bar details in config:
    d = config["data"]
    historical_days = 7   # e.g. 1
    bar_size = d["bar_size"]                 # e.g. "1 min"
    # We'll build a standard "durationStr" like "1 D"
    duration = f"{historical_days} D"

    # Output CSV file name (you can store in config or just pick one):
    output_file = "bars_data.csv"

    # -------------------------------------------------------------
    # 3) Create the IB APP + connect
    # -------------------------------------------------------------
    logging.info(f"Connecting to IB @ {host}:{port}, clientId={client_id}")
    app = HistDataApp()
    app.connect(host, port, client_id)

    api_thread = Thread(target=app.run, daemon=True)
    api_thread.start()

    # -------------------------------------------------------------
    # 4) Build the IB contract from config
    # -------------------------------------------------------------
    contract = Contract()
    contract.symbol = symbol
    contract.secType = sec_type
    contract.exchange = exchange
    contract.currency = currency
    contract.lastTradeDateOrContractMonth = last_trade
    contract.localSymbol = local_symbol
    if multiplier:
        contract.multiplier = multiplier

    # -------------------------------------------------------------
    # 5) Request historical data
    # -------------------------------------------------------------
    logging.info(f"Requesting {duration} of {bar_size} bars for {symbol}...")
    app.reqHistoricalData(
        reqId=1,
        contract=contract,
        endDateTime="",
        durationStr=duration,         # e.g. "1 D"
        barSizeSetting=bar_size,      # e.g. "1 min"
        whatToShow="TRADES",
        useRTH=0,
        formatDate=1,
        keepUpToDate=False,
        chartOptions=[]
    )

    # Wait until done or 60s
    finished = app.done.wait(timeout=60)
    if not finished:
        logging.warning("Timeout waiting for historical data. Possibly partial data.")
    time.sleep(1)  # a small buffer

    # Disconnect from IB
    if app.isConnected():
        app.disconnect()

    # -------------------------------------------------------------
    # 6) Write results to CSV
    # -------------------------------------------------------------
    fieldnames = ["time", "open", "high", "low", "close", "volume"]
    with open(output_file, mode="w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for bar in app.bars:
            writer.writerow(bar)

    logging.info(f"Historical bars saved to {output_file}")
    logging.info("Done.")


if __name__ == "__main__":
    main()
