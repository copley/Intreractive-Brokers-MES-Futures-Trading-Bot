# File: /home/student/MES/utils/aggregator.py

import logging
import time
from threading import Event

# Contract + IB Connection
from connection.contract_definition import create_contract
from connection.ib_connection import IBConnection

# Simple indicator calculations
from indicators.indicator_logic_EMA import calculate_EMA
from indicators.indicator_logic_RSI import calculate_RSI
from indicators.indicator_logic_ATR import calculate_ATR
from indicators.indicator_logic_VWAP import calculate_VWAP

# Managers and trade logic
from managers.entry_manager import EntryManager
from managers.exit_manager import ExitManager
from managers.dynamic_stop_loss import DynamicStopLoss
from managers.stop_loss_manager import StopLossManager
from managers.take_profit_manager import TakeProfitManager
from managers.trade_manager import TradeManager
from execution.trade_execution_logic import TradeExecutor

class Aggregator:
    """
    Orchestrates *live* market-data subscription, indicator computation, 
    and trade management. (No historical data.)
    """

    def __init__(self, config: dict):
        self.config = config

        # 1) Connect to IB
        ib_cfg = config.get('interactive_brokers', {})
        self.ib_connection = IBConnection(
            host=ib_cfg.get('host', '127.0.0.1'),
            port=ib_cfg.get('port', 7496),
            client_id=ib_cfg.get('client_id', 1)
        )

        # 2) Create the IB contract
        contract_cfg = config.get('contract', {})
        self.contract = create_contract(
            symbol=contract_cfg.get('symbol'),
            sec_type=contract_cfg.get('sec_type'),
            exchange=contract_cfg.get('exchange'),
            currency=contract_cfg.get('currency'),
            last_trade_date=contract_cfg.get('lastTradeDateOrContractMonth'),
            local_symbol=contract_cfg.get('localSymbol'),
            multiplier=contract_cfg.get('multiplier')
        )

        # 3) Initialize indicator and strategy managers
        strat_cfg = config.get('strategy', {})
        self.entry_manager = EntryManager(strat_cfg)
        self.exit_manager = ExitManager()

        sl_offset = 0.0
        self.dynamic_stop_loss = DynamicStopLoss(initial_offset=sl_offset, trailing=True)
        self.stop_loss_manager = StopLossManager(self.dynamic_stop_loss)
        tp_pct = config.get('trading', {}).get('take_profit_pct', 0.0)
        self.take_profit_manager = TakeProfitManager(tp_pct)

        self.trade_executor = TradeExecutor(self.ib_connection, self.contract, config)
        self.trade_manager = TradeManager(
            self.entry_manager,
            self.exit_manager,
            self.stop_loss_manager,
            self.take_profit_manager,
            self.trade_executor,
            config
        )

        # For live data updates:
        self._stop_event = Event()

        # Optionally store rolling price/volume for multi-bar indicators:
        self.closes = []
        self.highs = []
        self.lows = []
        self.volumes = []

        # Keep track of the last bar time so we only process new bars
        self._latest_bar_time = None

    def run(self):
        """
        Called from main.py. This will start live-data subscription and 
        continuously process incoming bars until user stops.
        """
        logging.info("Aggregator: run() -> starting live subscription.")
        self.run_live()

    def run_live(self):
        """
        Subscribes to real-time bars (~5 second resolution), prints them to screen,
        and passes them to the trade_manager for signal generation.
        """
        logging.info("Aggregator: Subscribing to real-time bars...")

        # Subscribe to IB realTimeBars
        self.ib_connection.app.reqRealTimeBars(
            reqId=9001,
            contract=self.contract,
            barSize=5,           # a 5-second bar
            whatToShow="TRADES",
            useRTH=False,
            realTimeBarsOptions=[]
        )

        print("[INFO] Now listening to real-time bars. Press Ctrl+C to stop.\n")

        try:
            while not self._stop_event.is_set():
                time.sleep(1)
                # IBApi.realtimeBar(...) callback will store data in some shared variable
                # if you have coded that. Here we check something like:
                bar_data = getattr(self.ib_connection.app, "last_realtime_bar", None)

                if bar_data and bar_data.time != self._latest_bar_time:
                    # It's a new bar
                    self._latest_bar_time = bar_data.time

                    # Print so we confirm it's "listening"
                    print(f"[LIVE BAR] Time={bar_data.time}, "
                          f"Open={bar_data.open}, High={bar_data.high}, "
                          f"Low={bar_data.low}, Close={bar_data.close}")

                    # Update rolling arrays so we can compute multi-bar indicators
                    self.closes.append(bar_data.close)
                    self.highs.append(bar_data.high)
                    self.lows.append(bar_data.low)
                    self.volumes.append(bar_data.volume)

                    # For bigger indicator windows, you might keep a limit 
                    # on how many bars you store, e.g.:
                    max_bars = 200
                    if len(self.closes) > max_bars:
                        self.closes.pop(0)
                        self.highs.pop(0)
                        self.lows.pop(0)
                        self.volumes.pop(0)

                    # Compute your indicators up to now:
                        ema_val = calculate_EMA(self.closes, self.config['indicators']['EMA_period'])
                        rsi_val = calculate_RSI(self.closes, self.config['indicators']['RSI_period'])
                        atr_val = calculate_ATR(self.highs, self.lows, self.closes, self.config['indicators']['ATR_period'])
                        vwap_val = calculate_VWAP(self.closes, self.volumes)

                    indicators = {
                        'EMA': ema_val,
                        'RSI': rsi_val,
                        'ATR': atr_val,
                        'VWAP': vwap_val
                    }

                    # Construct a dict representing "the latest bar"
                    # which your TradeManager expects
                    bar_dict = {
                        'time': bar_data.time,
                        'open': bar_data.open,
                        'high': bar_data.high,
                        'low': bar_data.low,
                        'close': bar_data.close,
                        'volume': bar_data.volume
                    }

                    # Let the trade manager decide if signals are generated
                    self.trade_manager.update(bar_dict, indicators)

        except KeyboardInterrupt:
            print("[INFO] Interrupted by user (KeyboardInterrupt).")

        finally:
            # Cancel subscription and disconnect
            self.ib_connection.app.cancelRealTimeBars(9001)
            self.ib_connection.disconnect()
            logging.info("Aggregator: run_live() stopped. Disconnected from IB.")

    def stop(self):
        """ Stop the live loop from outside if needed. """
        self._stop_event.set()
