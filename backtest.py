#!/usr/bin/env python3
import logging
import pandas as pd
from datetime import datetime

from managers.trade_manager import TradeManager
from managers.entry_manager import EntryManager
from managers.exit_manager import ExitManager
from managers.dynamic_stop_loss import DynamicStopLoss
from managers.stop_loss_manager import StopLossManager
from managers.take_profit_manager import TakeProfitManager
from execution.trade_execution_logic import TradeExecutor

from indicators.indicator_logic_EMA import calculate_EMA_series
from indicators.indicator_logic_RSI import calculate_RSI_series
from indicators.indicator_logic_ATR import calculate_ATR_series

from utils.helpers import load_config
from compute_trade_stats import compute_trade_stats

class Backtester:
    def __init__(self, csv_file, trade_log_file="trade_log.csv"):
        self.csv_file = csv_file
        self.trade_log_file = trade_log_file
        
        # Optionally load config for strategy thresholds, etc.
        self.config = load_config("config.yaml") or {}

        # Setup our offline managers (no IB connection needed for backtesting)
        self.entry_manager = EntryManager(self.config.get('strategy', {}))
        self.exit_manager = ExitManager()
        self.dynamic_stop_loss = DynamicStopLoss(initial_offset=2.0, trailing=True)
        self.stop_loss_manager = StopLossManager(self.dynamic_stop_loss)
        self.take_profit_manager = TakeProfitManager(take_profit_pct=0.01)

        # Create a mock TradeExecutor (no real orders)
        self.trade_executor = TradeExecutor(ib_connection=None, contract=None, config=self.config)

        # Combine them into a single TradeManager.
        # Note: Pass the unique trade log filename as a keyword argument.
        self.trade_manager = TradeManager(
            self.entry_manager,
            self.exit_manager,
            self.stop_loss_manager,
            self.take_profit_manager,
            self.trade_executor,
            self.config,
            log_filename=self.trade_log_file
        )

    def load_historical_csv(self):
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

        # 1) Compute a full series-based EMA, RSI, ATR 
        df['ema20'] = calculate_EMA_series(df, price_col='close', period=20)
        df['rsi14'] = calculate_RSI_series(df, price_col='close', period=14)
        df['atr14'] = calculate_ATR_series(df, high_col='high', low_col='low', close_col='close', period=14)

        # OPTIONAL: Print a small sample
        print("\n[DEBUG] Sample rows with RSI/EMA/ATR:\n")
        print(df[['time','close','ema20','rsi14','atr14']].head(50))

        # 2) Now iterate over each row, sending the correct indicators to trade_manager
        for idx, row in df.iterrows():
            bar_data = {
                'time': row['time'],
                'open': row['open'],
                'high': row['high'],
                'low': row['low'],
                'close': row['close'],
                'volume': row.get('volume', 0),
            }
            # Gather indicator values
            indicators = {
                'EMA': row['ema20'],
                'RSI': row['rsi14'],
                'ATR': row['atr14'],
            }
            self.trade_manager.update(bar_data, indicators)

        logging.info("Backtest complete. You can review trades in `trade_record.text` ...")
        compute_trade_stats(csv_path=self.trade_log_file, initial_capital=10000.0)

if __name__ == "__main__":
    # Replace "your_csv_file.csv" with the actual CSV path when running interactively.
    Backtester(csv_file="your_csv_file.csv").run_backtest()
