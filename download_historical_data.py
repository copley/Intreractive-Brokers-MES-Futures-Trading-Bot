#!/usr/bin/env python3

"""
download_historical_bars_parallel_limited.py

- Loads IB connection details + contract details from config.yaml
- Splits the total requested days (e.g. 29) into smaller "chunks" (e.g. 9-10 days each).
- Fetches them in parallel with up to N=6 simultaneous connections.
- Waits 0.3s after launching each thread to stagger the connections.
- Each thread uses a unique clientId so IB sees them as distinct connections.
- Collects the bars in chronological order, then writes them to CSV.
"""

import csv
import logging
import time
from datetime import datetime, timedelta, timezone
from threading import Thread, Event

from utils.helpers import load_config  # your config loader

from ibapi.client import EClient
from ibapi.wrapper import EWrapper
from ibapi.contract import Contract


# ---------------------------------------------------------------------------
#   1) IB App Class
# ---------------------------------------------------------------------------
class HistDataApp(EWrapper, EClient):
    def __init__(self):
        EClient.__init__(self, self)
        self.bars = []       # store downloaded bars
        self.done = Event()  # signals when historicalDataEnd is received

    def error(self, reqId, errorCode, errorString):
        # ignore common "warning" codes for data-farm connection statuses
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
        logging.info(f"Thread {self._threadName}: Completed download: {len(self.bars)} bars.")
        self.done.set()


# ---------------------------------------------------------------------------
#   2) Worker function for a single chunk
# ---------------------------------------------------------------------------
def fetch_chunk_in_thread(thread_id, host, port, contract, endDateTime, durationStr, bar_size,
                          what_to_show, useRTH, formatDate, timeout, results_dict):
    """
    Connects to TWS/IB Gateway with a unique clientId, requests this chunk,
    waits up to `timeout` seconds, then stores the bars in results_dict[thread_id].
    """
    app = HistDataApp()
    app._threadName = f"T{thread_id}"  # just for logging

    # unique clientId for each thread
    client_id = 100 + thread_id

    logging.info(f"[Thread {thread_id}] Connecting to IB @ {host}:{port}, clientId={client_id}")
    app.connect(host, port, client_id)

    api_thread = Thread(target=app.run, daemon=True)
    api_thread.start()

    # request data
    req_id = thread_id
    logging.info(f"[Thread {thread_id}] Request: {durationStr} of {bar_size} ending='{endDateTime}'")
    app.reqHistoricalData(
        reqId=req_id,
        contract=contract,
        endDateTime=endDateTime,
        durationStr=durationStr,
        barSizeSetting=bar_size,
        whatToShow=what_to_show,
        useRTH=useRTH,
        formatDate=formatDate,
        keepUpToDate=False,
        chartOptions=[]
    )

    # wait for the chunk to finish
    finished = app.done.wait(timeout=timeout)
    if not finished:
        logging.warning(f"[Thread {thread_id}] Timeout waiting for historical data.")

    # short delay to ensure all bars are received
    time.sleep(1)

    # disconnect
    if app.isConnected():
        app.disconnect()

    # store results
    results_dict[thread_id] = app.bars[:]


# ---------------------------------------------------------------------------
#   3) Helper to parse IB date strings -> Python datetime
# ---------------------------------------------------------------------------
def parse_ib_datetime(ib_date_str):
    """
    If 'YYYYMMDD' -> daily bar
    If 'YYYYMMDD  HH:MM:SS' -> intraday bar
    (No timezone info in the bars themselves, so no tz parse.)
    """
    if len(ib_date_str) == 8:
        return datetime.strptime(ib_date_str, "%Y%m%d")
    else:
        return datetime.strptime(ib_date_str, "%Y%m%d  %H:%M:%S")


# ---------------------------------------------------------------------------
#   4) Generate chunk definitions
# ---------------------------------------------------------------------------
def compute_chunk_info(total_days, chunk_size):
    """
    Return a list of (chunkIndex, endDate, durationStr).
    We break total_days into chunks of chunk_size, each with
    an explicit UTC timestamp in 'YYYYMMDD HH:MM:SS UTC' format.
    """
    # Make 'now' in UTC to ensure we're labeling times correctly.
    now_utc = datetime.now(timezone.utc)
    chunk_info_list = []

    chunk_count = (total_days + chunk_size - 1) // chunk_size  # ceil division
    for i in range(chunk_count):
        # how many days for this chunk
        days_for_this_chunk = min(chunk_size, total_days - i * chunk_size)

        # Compute chunk end time in UTC
        end_dt_utc = now_utc - timedelta(days=i * chunk_size)
        # Format with explicit 'UTC' suffix to comply with IB's recommended format
        end_date_str = end_dt_utc.strftime("%Y%m%d %H:%M:%S UTC")

        duration_str = f"{days_for_this_chunk} D"
        chunk_info_list.append((i, end_date_str, duration_str))

    return chunk_info_list


# ---------------------------------------------------------------------------
#   5) Main
# ---------------------------------------------------------------------------
def main():
    # 1) Load config.yaml
    config = load_config("config.yaml")
    if not config:
        raise SystemExit("Failed to load config.yaml. Exiting.")

    logging.basicConfig(level=logging.INFO,
                        format="%(asctime)s [%(levelname)s] %(message)s")

    # 2) IB connection details
    ib_cfg = config["interactive_brokers"]
    host = ib_cfg["host"]     # e.g. "127.0.0.1"
    port = ib_cfg["port"]     # e.g. 7496

    # 3) Contract details
    c = config["contract"]
    symbol = c["symbol"]               # e.g. "MES"
    sec_type = c["sec_type"]           # e.g. "FUT"
    exchange = c["exchange"]           # e.g. "CME"
    currency = c["currency"]           # e.g. "USD"
    last_trade = c["lastTradeDateOrContractMonth"]  # e.g. "20250321"
    local_symbol = c["localSymbol"]    # e.g. "MESH5"
    multiplier = c["multiplier"]       # e.g. "5"

    # 4) Data request settings
    d = config["data"]
    total_days = 365             # total number of days you want
    chunk_days = 9               # each chunk is 3 days, for example
    bar_size = d["bar_size"]     # e.g. "1 min"
    what_to_show = "TRADES"
    useRTH = 0
    formatDate = 1
    timeout = 180  # per-chunk timeout (seconds)
    timestamp_str = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_file = f"bars_data_{timestamp_str}.csv"
    # build IB Contract
    contract = Contract()
    contract.symbol = symbol
    contract.secType = sec_type
    contract.exchange = exchange
    contract.currency = currency
    contract.lastTradeDateOrContractMonth = last_trade
    contract.localSymbol = local_symbol
    if multiplier:
        contract.multiplier = multiplier

    # 5) Figure out the chunk definitions
    chunk_defs = compute_chunk_info(total_days, chunk_days)
    chunk_count = len(chunk_defs)
    logging.info(f"Will fetch {chunk_count} chunks total (each up to {chunk_days} days).")

    # 6) We'll limit concurrency to 6 connections at once
    max_concurrency = 8

    # We'll store chunk results in a dictionary: {chunkIndex: [list_of_bars]}
    results_dict = {}

    # 7) Submit chunks in waves of up to 6 parallel threads
    i = 0
    while i < chunk_count:
        wave = chunk_defs[i : i + max_concurrency]  # slice up to concurrency
        wave_threads = []

        # launch each chunk in this wave
        for (chunkIndex, end_dt, dur_str) in wave:
            t = Thread(
                target=fetch_chunk_in_thread,
                args=(
                    chunkIndex,
                    host,
                    port,
                    contract,
                    end_dt,
                    dur_str,
                    bar_size,
                    what_to_show,
                    useRTH,
                    formatDate,
                    timeout,
                    results_dict
                ),
                daemon=True
            )
            wave_threads.append(t)
            t.start()

            # *** ADD A DELAY AFTER STARTING EACH THREAD ***
            time.sleep(0.5)  # 300-500 ms to stagger connection attempts

        # wait for all threads in this wave to finish
        for t in wave_threads:
            t.join()

        i += max_concurrency  # proceed to the next wave

    # 8) Combine all bars from results_dict
    all_bars = []
    for chunk_id in sorted(results_dict.keys()):
        all_bars.extend(results_dict[chunk_id])

    # sort everything by time
    def sort_key(bar):
        return parse_ib_datetime(bar["time"])
    all_bars.sort(key=sort_key)

    logging.info(f"Total bars collected across all chunks: {len(all_bars)}")

    # 9) Write to CSV
    fieldnames = ["time", "open", "high", "low", "close", "volume"]
    with open(output_file, mode="w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for bar in all_bars:
            writer.writerow(bar)

    logging.info(f"Historical bars saved to {output_file}")
    logging.info("Done.")


if __name__ == "__main__":
    main()
