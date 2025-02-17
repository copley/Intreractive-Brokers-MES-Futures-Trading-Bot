#!/usr/bin/env python3

from ibapi.client import EClient
from ibapi.wrapper import EWrapper
from ibapi.contract import Contract
from ibapi.common import TickAttribLast
import time
import threading
from datetime import datetime, timedelta


def align_to_bar_boundary(dt, bar_length=30):
    """
    Returns a new datetime 'anchored' to the most recent
    bar boundary in multiples of 'bar_length' seconds.
    For bar_length=30, those boundaries are :00 and :30.
    """
    # e.g. if dt.second is 37 and bar_length=30, remainder = 7
    # so anchored_second = 30
    second_of_minute = dt.second
    remainder = second_of_minute % bar_length
    anchored_second = second_of_minute - remainder
    # Zero out microseconds so we don't drift
    return dt.replace(second=anchored_second, microsecond=0)


class IBApi(EWrapper, EClient):
    def __init__(self, aggregator):
        EClient.__init__(self, self)
        self.aggregator = aggregator

    def error(self, reqId, errorCode, errorString):
        # Filter out standard "farm connection is OK" messages
        if errorCode in (2104, 2106, 2158):
            print(f"[INFO] {errorString} (code={errorCode})")
        else:
            print(f"[ERROR] ReqId: {reqId}, Code: {errorCode}, Msg: {errorString}")

    def tickByTickAllLast(self, reqId: int, tickType: int,
                          time_: int, price: float, size: int,
                          tickAttribLast: TickAttribLast,
                          exchange: str, specialConditions: str):
        trade_time = datetime.fromtimestamp(time_)
        self.aggregator.on_new_trade(trade_time, price, size)


class TradeAggregator:
    """
    Aggregates raw trades into bars of 'bar_length' seconds,
    anchored to clock boundaries (so bars start at :00 or :30).
    """
    def __init__(self, bar_length=30):
        self.bar_length = bar_length
        self.delta = timedelta(seconds=bar_length)
        self.bar_start = None  # Keep track of the current bar's start
        self.open_price = None
        self.high_price = None
        self.low_price = None
        self.close_price = None
        self.volume = 0

    def on_new_trade(self, trade_time, price, size):
        """
        Update or finalize bars based on the incoming trade.
        1) If we have no current bar, anchor to the clock boundary.
        2) If trade_time has moved beyond the current bar’s boundary,
           finalize the old bar(s), step forward in 30s increments,
           then record the trade in the new bar.
        """
        # If we have no bar in progress, create one anchored to the last boundary
        if self.bar_start is None:
            candidate_start = align_to_bar_boundary(trade_time, self.bar_length)
            while trade_time >= candidate_start + self.delta:
                candidate_start += self.delta
            self.bar_start = candidate_start

        # If this trade is beyond the end of the current bar window,
        # finalize the bar(s) and move forward.
        while trade_time >= self.bar_start + self.delta:
            self.finalize_bar()
            self.bar_start += self.delta

        # Now trade_time is within self.bar_start..self.bar_start + self.delta
        self.update_current_bar(price, size)

    def update_current_bar(self, price, size):
        """
        Update open/high/low/close/volume for the current bar.
        If this is the first trade of the new bar, initialize OHLCV.
        """
        if self.open_price is None:
            self.open_price = price
            self.high_price = price
            self.low_price = price
            self.close_price = price
            self.volume = size
        else:
            self.close_price = price
            self.high_price = max(self.high_price, price)
            self.low_price = min(self.low_price, price)
            self.volume += size

    def finalize_bar(self):
        """
        Print (or store) the bar, then reset only OHLCV and volume.
        NOTE: We *do not* reset self.bar_start here, because
        we increment it in on_new_trade() if needed.
        """
        if self.open_price is not None:
            bar_end_time = self.bar_start + self.delta
            print(
                f"[{self.bar_start.strftime('%H:%M:%S')} - "
                f"{bar_end_time.strftime('%H:%M:%S')}] "
                f"O:{self.open_price:.2f} H:{self.high_price:.2f} "
                f"L:{self.low_price:.2f} C:{self.close_price:.2f} "
                f"V:{self.volume}"
            )

        # Reset only the bar contents, but keep the same self.bar_start
        self.open_price = None
        self.high_price = None
        self.low_price = None
        self.close_price = None
        self.volume = 0

    def check_force_finalize(self):
        """
        Optionally force‐close a bar if we haven't seen trades for a while,
        or you can finalize on a schedule. Not used here, but can be useful.
        """
        pass


def create_xina50_contract():
    contract = Contract()
    contract.symbol = "XINA50"
    contract.secType = "FUT"
    contract.exchange = "SGX"
    contract.currency = "USD"
    contract.lastTradeDateOrContractMonth = "20250227"
    contract.localSymbol = "CNG25"  # or whichever
    contract.multiplier = "1"
    return contract


def run_loop(app):
    app.run()


def main():
    aggregator = TradeAggregator(bar_length=30)
    app = IBApi(aggregator)

    # Connect to IB
    app.connect("192.168.1.77", 7496, clientId=1)

    # Start the API thread
    thread = threading.Thread(target=run_loop, args=(app,), daemon=True)
    thread.start()
    time.sleep(2)

    contract = create_xina50_contract()

    # Request tick-by-tick data
    app.reqTickByTickData(
        reqId=1,
        contract=contract,
        tickType="AllLast",
        numberOfTicks=0,
        ignoreSize=False
    )

    try:
        print("[INFO] Receiving tick-by-tick trades. Press Ctrl+C to exit.")
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("[INFO] Interrupted by user.")
    finally:
        # Finalize any open bar before exiting
        aggregator.finalize_bar()
        app.disconnect()


if __name__ == "__main__":
    main()
