#!/usr/bin/env python3
import threading
import time
from datetime import datetime, timedelta
from ibapi.client import EClient
from ibapi.wrapper import EWrapper
from ibapi.execution import ExecutionFilter
from ibapi.contract import Contract

class IBTradeHistoryApp(EWrapper, EClient):
    def __init__(self):
        EClient.__init__(self, self)
        self.executions = []  # List to store execution details.
        self.exec_event = threading.Event()

    def nextValidId(self, orderId: int):
        print("Connected to IB Gateway. Requesting trade history...")
        # Create an ExecutionFilter and set its m_time field to 6 months ago.
        execFilter = ExecutionFilter()
        six_months_ago = datetime.now() - timedelta(days=182)
        # IB API expects time in "YYYYMMDD-HH:MM:SS" format.
        execFilter.m_time = six_months_ago.strftime("%Y%m%d-%H:%M:%S")
        print("Using execution filter start time:", execFilter.m_time)
        # You can also set other filter fields (e.g. m_acctCode, m_symbol) if desired.
        self.reqExecutions(1, execFilter)

    def execDetails(self, reqId: int, contract, execution):
        # Store execution details as a tuple:
        # (Execution ID, Time, Symbol, Side, Shares, Price)
        exec_tuple = (
            execution.execId,
            execution.time,
            contract.symbol,
            execution.side,
            execution.shares,
            execution.price,
        )
        self.executions.append(exec_tuple)
        print(f"Received execution: {exec_tuple}")

    def execDetailsEnd(self, reqId: int):
        print("Trade history download finished.")
        self.exec_event.set()

    def error(self, reqId, errorCode, errorString):
        print(f"Error. ReqId: {reqId}, Code: {errorCode}, Msg: {errorString}")

def print_table(header, rows):
    # Calculate column widths.
    col_widths = [len(str(h)) for h in header]
    for row in rows:
        for i, cell in enumerate(row):
            col_widths[i] = max(col_widths[i], len(str(cell)))
    sep = " | "
    header_line = sep.join([f"{h:<{col_widths[i]}}" for i, h in enumerate(header)])
    divider = "-" * len(header_line)
    print(header_line)
    print(divider)
    for row in rows:
        print(sep.join([f"{str(cell):<{col_widths[i]}}" for i, cell in enumerate(row)]))

def main():
    app = IBTradeHistoryApp()
    host = "127.0.0.1"
    port = 4001
    client_id = 20  # Use a unique client id for this script.

    print(f"Connecting to IB Gateway at {host}:{port} with clientId={client_id}...")
    app.connect(host, port, client_id)

    # Start the IB API processing thread.
    api_thread = threading.Thread(target=app.run, daemon=True)
    api_thread.start()

    # Wait for trade history to be downloaded (adjust the timeout as needed).
    if not app.exec_event.wait(timeout=20):
        print("Timeout waiting for trade history.")

    if app.executions:
        header = ["ExecID", "Time", "Symbol", "Side", "Shares", "Price"]
        rows = [list(row) for row in app.executions]
        print("\nTrade History:")
        print_table(header, rows)
    else:
        print("\nNo trade history found for the past 6 months.")

    app.disconnect()
    print("\nDisconnected. Exiting.")

if __name__ == "__main__":
    main()
