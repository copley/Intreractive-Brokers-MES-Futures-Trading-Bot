#!/usr/bin/env python3

import time
import threading
import logging
import yaml
import os
from datetime import datetime
from ibapi.client import EClient
from ibapi.wrapper import EWrapper
from ibapi.contract import Contract
from ibapi.common import TickerId

CONFIG_FILE = "config.yaml"


def load_config(config_path=CONFIG_FILE):
    """
    Loads your YAML config file:
      interactive_brokers.host, .port, .client_id (but we will IGNORE .client_id)
      contract: MES details
      logging: level, etc.
    """
    with open(config_path, 'r') as f:
        return yaml.safe_load(f)


class MESLiveWrapper(EWrapper):
    """
    EWrapper methods receive events from IB.
    We'll implement realtimeBar() to handle 5s bar updates.
    """
    def __init__(self):
        super().__init__()
        self.log_file = None  # We'll set this in MESLiveApp

    def realtimeBar(self, reqId: TickerId, time: int, open_: float, high: float,
                    low: float, close: float, volume: int, wap: float, count: int):
        """
        Called every time a new 5s bar completes.
        """
        bar_time = datetime.fromtimestamp(time).strftime("%Y-%m-%d %H:%M:%S")
        line = f"{bar_time},{open_},{high},{low},{close},{volume},{wap},{count}\n"
        
        # Append the bar line to a CSV file:
        if self.log_file:
            with open(self.log_file, "a") as f:
                f.write(line)
        
        logging.info(f"[REALTIME BAR] {bar_time}  O={open_}  H={high}  L={low}  C={close}  V={volume}")

    def error(self, reqId, errorCode, errorString):
        """
        Called by IB if there's an error or warning message.
        For certain codes, you might want additional logic.
        """
        super().error(reqId, errorCode, errorString)
        logging.error(f"IB Error code={errorCode}, message={errorString}")


class MESLiveClient(EClient):
    """
    EClient manages all outbound requests to IB (connections, requests).
    """
    def __init__(self, wrapper):
        super().__init__(wrapper)


class MESLiveApp(MESLiveWrapper, MESLiveClient):
    """
    Combines EWrapper + EClient into one class for simplicity,
    plus a basic reconnection loop.
    """
    def __init__(self, config):
        MESLiveWrapper.__init__(self)
        MESLiveClient.__init__(self, wrapper=self)

        self.config = config

        # Use config for host and port, but ignore config client_id.
        self.host = self.config["interactive_brokers"]["host"]
        self.port = self.config["interactive_brokers"]["port"]
        # HARDCODE A UNIQUE CLIENT_ID:
        self.client_id = 14  # <--- Use a distinct ID

        # We'll log bars to 'live_bars.csv' in current folder
        self.log_file = os.path.abspath("live_bars.csv")
        self.req_id_for_bars = 9001

        # Attempt the initial connect + start the EClient.run() thread
        self._connect_and_start_thread()

        # Start a background thread that checks connectivity
        self._stop_reconnect_checker = False
        self.reconnect_thread = threading.Thread(
            target=self.check_connection_loop, daemon=True
        )
        self.reconnect_thread.start()

    def _connect_and_start_thread(self):
        """Make the IB connection and start the network thread."""
        logging.info(f"Connecting to IB at {self.host}:{self.port} client_id={self.client_id}")
        self.connect(self.host, self.port, self.client_id)

        # Start the EClient.run() loop in a background thread
        self.api_thread = threading.Thread(target=self.run, daemon=True)
        self.api_thread.start()

    def stop(self):
        """
        Disconnect from TWS and join threads, shutting down gracefully.
        """
        logging.info("Stopping app: disconnecting from IB and stopping reconnect thread...")
        self._stop_reconnect_checker = True

        if self.isConnected():
            self.disconnect()
        if self.api_thread and self.api_thread.is_alive():
            self.api_thread.join(timeout=2)

        if self.reconnect_thread and self.reconnect_thread.is_alive():
            self.reconnect_thread.join(timeout=2)
        logging.info("Stopped.")

    def check_connection_loop(self):
        """
        Periodically check if isConnected() is False. If so, attempt reconnect.
        """
        while not self._stop_reconnect_checker:
            time.sleep(5)  # check every 5 seconds
            if not self.isConnected():
                logging.warning("Detected IB disconnect! Attempting to reconnect...")
                self.reconnect_and_resubscribe()

    def reconnect_and_resubscribe(self):
        """
        Attempt to reconnect and re-subscribe if disconnected.
        """
        # Disconnect fully (just in case).
        try:
            if self.isConnected():
                self.disconnect()
        except:
            pass

        # Start fresh
        self._connect_and_start_thread()

        # Wait a moment to ensure the new connection is established
        time.sleep(2)

        # Re-subscribe to real-time bars
        self.request_realtime_bars()

    def request_realtime_bars(self):
        """
        Send the reqRealTimeBars for MES contract using the config
        """
        c_dict = self.config["contract"]
        mes_contract = Contract()
        mes_contract.symbol = c_dict["symbol"]
        mes_contract.secType = c_dict["sec_type"]
        mes_contract.exchange = c_dict["exchange"]
        mes_contract.currency = c_dict["currency"]
        mes_contract.lastTradeDateOrContractMonth = c_dict["lastTradeDateOrContractMonth"]
        mes_contract.localSymbol = c_dict["localSymbol"]
        mes_contract.multiplier = c_dict["multiplier"]

        logging.info("Requesting 5s bars for MES (re)subscription...")
        self.reqRealTimeBars(
            reqId=self.req_id_for_bars,
            contract=mes_contract,
            barSize=5,           # 5-second bars
            whatToShow="TRADES",
            useRTH=False,
            realTimeBarsOptions=[]
        )


def main():
    config = load_config()
    
    # Setup logging
    log_level = getattr(logging, config["logging"]["level"].upper(), logging.INFO)
    logging.basicConfig(
        level=log_level,
        format="%(asctime)s [%(levelname)s] %(message)s"
    )
    
    logging.info("Starting the live MES tracker with auto-reconnect...")

    # Create the app, which connects automatically:
    app = MESLiveApp(config)
    time.sleep(2)  # Let it connect briefly
    
    # Actually subscribe to real-time bars
    app.request_realtime_bars()

    print("[INFO] Subscribed to live 5s bars for MES. Data appended to live_bars.csv.")
    print("Press Ctrl+C to stop.\n")

    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("\n[INFO] Interrupted by user.")
    finally:
        app.stop()


if __name__ == "__main__":
    main()
