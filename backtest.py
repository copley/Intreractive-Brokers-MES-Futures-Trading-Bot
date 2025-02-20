#!/usr/bin/env python3
import logging
import pandas as pd
from datetime import datetime

# Example imports from your existing code
from managers.trade_manager import TradeManager
from managers.entry_manager import EntryManager
from managers.exit_manager import ExitManager
from managers.dynamic_stop_loss import DynamicStopLoss
from managers.stop_loss_manager import StopLossManager
from managers.take_profit_manager import TakeProfitManager
from execution.trade_execution_logic import TradeExecutor

# Indicators from your existing files
from indicators.indicator_logic_EMA import calculate_EMA
from indicators.indicator_logic_RSI import calculate_RSI
from indicators.indicator_logic_ATR import calculate_ATR

# For reading config if needed
from utils.helpers import load_config
from compute_trade_stats import compute_trade_stats

class Backtester:
    def __init__(self, csv_file):
        self.csv_file = csv_file

        # Optionally load config for strategy thresholds, etc.
        self.config = load_config("config.yaml") or {}

        # Setup our “offline” managers the same way as live
        # but no actual IB connection needed
        self.entry_manager = EntryManager(self.config.get('strategy', {}))
        self.exit_manager = ExitManager()
        self.dynamic_stop_loss = DynamicStopLoss(initial_offset=2.0, trailing=True)
        self.stop_loss_manager = StopLossManager(self.dynamic_stop_loss)
        self.take_profit_manager = TakeProfitManager(take_profit_pct=0.01)

        # A mock TradeExecutor that doesn't place real orders
        # (We just want the same logic to run)
        self.trade_executor = TradeExecutor(ib_connection=None, contract=None, config=self.config)

        # Combine them into a single trade manager
        self.trade_manager = TradeManager(
            self.entry_manager,
            self.exit_manager,
            self.stop_loss_manager,
            self.take_profit_manager,
            self.trade_executor,
            self.config
        )

    def load_historical_csv(self):
        """
        Load the user-provided CSV and return a DataFrame.
        We assume columns: time, close, high, low, volume, etc.
        """
        try:
            df = pd.read_csv(self.csv_file)
            df['time'] = pd.to_datetime(df['time'])
            df.sort_values('time', inplace=True)
            logging.info(f"Loaded {len(df)} rows from {self.csv_file}")
            return df
        except Exception as e:
            logging.error(f"Failed to load CSV {self.csv_file}: {e}")
            return None

    def run_backtest(self):
        df = self.load_historical_csv()
        if df is None or df.empty:
            logging.warning("No data to backtest.")
            return

        # Compute indicators: (example: last 20 bars for EMA, etc.)
        closes = df['close'].tolist()
        highs  = df['high'].tolist()
        lows   = df['low'].tolist()

        df['ema20'] = calculate_EMA(closes, period=20)
        df['rsi14'] = calculate_RSI(closes, period=14)
        df['atr14'] = calculate_ATR(highs, lows, closes, period=14)

        for idx, row in df.iterrows():
            # Construct the “bar_data” dict, matching the shape used in live.
            # Adjust for whether you have an 'open' column:
            bar_data = {
                'time':   row['time'],
                'open':   row['close'],  # or row['open'] if you do have a separate "open" column
                'high':   row['high'],
                'low':    row['low'],
                'close':  row['close'],
                'volume': row.get('volume', 0),
            }

            # Gather indicator values
            indicators = {
                'EMA': row['ema20'],
                'RSI': row['rsi14'],
                'ATR': row['atr14'],
                # add more if needed
            }

            # Pass to TradeManager: checks for entries/exits
            self.trade_manager.update(bar_data, indicators)

        logging.info("Backtest complete. You can review trades in `trade_record.text` or wherever it's written.")
    # somewhere after backtester finishes

    compute_trade_stats(
        csv_path="trade_log.csv",   # or wherever your trades are logged
        initial_capital=10000.0
    )
