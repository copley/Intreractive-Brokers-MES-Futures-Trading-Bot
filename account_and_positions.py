#!/usr/bin/env python3
import threading
import time
from ibapi.client import EClient
from ibapi.wrapper import EWrapper
from ibapi.contract import Contract

class IBTerminalApp(EWrapper, EClient):
    def __init__(self):
        EClient.__init__(self, self)
        # Store positions as tuples: (account, contract, position, avgCost)
        self.positions = []
        self.account_values = {}  # Dict of key -> (value, currency)
        # For snapshot market data: maps reqId to last price.
        self.market_data_prices = {}
        # Map reqId to position index.
        self.position_mkt_req_map = {}
        # Events for when downloads complete.
        self.positions_event = threading.Event()
        self.account_event = threading.Event()
        self.account_code = None

    def managedAccounts(self, accountsList: str):
        print("Managed accounts:", accountsList)
        if accountsList:
            # Use the first account from the comma-separated list.
            self.account_code = accountsList.split(",")[0]

    def nextValidId(self, orderId: int):
        print("Connected to IB Gateway. Requesting account updates and positions...")
        account = self.account_code if self.account_code else ""
        self.reqAccountUpdates(True, account)
        self.reqPositions()

    def updateAccountValue(self, key: str, val: str, currency: str, accountName: str):
        self.account_values[key] = (val, currency)

    def accountDownloadEnd(self, accountName: str):
        print("Account update download finished for account:", accountName)
        self.account_event.set()

    def position(self, account: str, contract, pos: float, avgCost: float):
        # Store the full contract as provided.
        self.positions.append((account, contract, pos, avgCost))

    def positionEnd(self):
        print("Positions download finished.")
        self.positions_event.set()

    def tickPrice(self, reqId, tickType, price, attrib):
        # Use tickType 4 (Last Price) for snapshot market data.
        if tickType == 4:
            self.market_data_prices[reqId] = price

    def error(self, reqId, errorCode, errorString):
        print(f"Error. ReqId: {reqId}, Code: {errorCode}, Msg: {errorString}")

    def request_market_data_for_positions(self):
        """
        For each stored position, create a new contract (filling in any missing details)
        and request snapshot market data.
        """
        self.market_data_prices = {}
        self.position_mkt_req_map = {}
        reqId_start = 1000
        for i, (account, contract, pos, avgCost) in enumerate(self.positions):
            reqId = reqId_start + i
            self.position_mkt_req_map[reqId] = i

            # Create a fresh contract and copy available details.
            new_contract = Contract()
            new_contract.symbol = contract.symbol
            new_contract.secType = contract.secType

            # Fill in exchange if missing.
            if not contract.exchange or contract.exchange.strip() == "":
                if contract.secType == "STK":
                    new_contract.exchange = "SMART"
                elif contract.secType == "FUT":
                    new_contract.exchange = "GLOBEX"
                else:
                    new_contract.exchange = "SMART"
            else:
                new_contract.exchange = contract.exchange

            # Fill in currency if missing.
            if not contract.currency or contract.currency.strip() == "":
                new_contract.currency = "USD"
            else:
                new_contract.currency = contract.currency

            # For futures, localSymbol is often required.
            if hasattr(contract, "localSymbol") and contract.localSymbol:
                new_contract.localSymbol = contract.localSymbol
            else:
                new_contract.localSymbol = contract.symbol

            # Copy multiplier if available, otherwise default to "1".
            if hasattr(contract, "multiplier") and contract.multiplier:
                new_contract.multiplier = contract.multiplier
            else:
                new_contract.multiplier = "1"

            # Request snapshot market data using the new contract.
            self.reqMktData(reqId, new_contract, "", True, False, [])
        # Allow time for snapshot data to arrive.
        time.sleep(5)
        # Cancel all market data subscriptions.
        for reqId in self.position_mkt_req_map:
            self.cancelMktData(reqId)

def print_table(header, rows):
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
    app = IBTerminalApp()
    host = "127.0.0.1"
    port = 4001
    client_id = 19

    print(f"Connecting to IB Gateway at {host}:{port} with clientId={client_id}...")
    app.connect(host, port, client_id)

    api_thread = threading.Thread(target=app.run, daemon=True)
    api_thread.start()

    # Increase timeouts to ensure complete downloads.
    if not app.positions_event.wait(timeout=15):
        print("Timeout waiting for positions.")
    if not app.account_event.wait(timeout=15):
        print("Timeout waiting for account update.")

    if app.positions:
        app.request_market_data_for_positions()

    pos_header = ["Account", "Symbol", "SecType", "Position", "AvgCost", "Current Price", "Total PnL"]
    pos_rows = []
    for i, (account, contract, pos, avgCost) in enumerate(app.positions):
        reqId = 1000 + i
        current_price = app.market_data_prices.get(reqId, "N/A")
        if current_price != "N/A" and isinstance(current_price, (float, int)):
            try:
                multiplier = float(contract.multiplier) if hasattr(contract, "multiplier") and contract.multiplier and contract.multiplier.strip() != "" else 1.0
            except Exception:
                multiplier = 1.0
            pnl = (current_price - avgCost) * pos * multiplier
            pnl = round(pnl, 2)
            current_price = round(current_price, 2)
        else:
            pnl = "N/A"
        pos_rows.append([
            account,
            contract.symbol,
            contract.secType,
            pos,
            avgCost,
            current_price,
            pnl
        ])

    if pos_rows:
        print("\nCurrent Positions:")
        print_table(pos_header, pos_rows)
    else:
        print("\nNo positions received.")

    if app.account_values:
        print("\nAccount Balances / Values:")
        acc_header = ["Key", "Value (Currency)"]
        acc_rows = []
        for key, (val, curr) in sorted(app.account_values.items()):
            acc_rows.append([key, f"{val} {curr}"])
        print_table(acc_header, acc_rows)
    else:
        print("\nNo account values received.")

    app.reqAccountUpdates(False, app.account_code if app.account_code else "")
    time.sleep(1)
    app.disconnect()
    print("\nDisconnected. Exiting.")

if __name__ == "__main__":
    main()
