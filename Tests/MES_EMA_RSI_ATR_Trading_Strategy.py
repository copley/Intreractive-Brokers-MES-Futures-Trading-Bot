#!/usr/bin/env python3
import argparse
import pandas as pd
import numpy as np
import time
import logging
from datetime import datetime, timedelta
from ib_insync import IB, util, Contract

class EmaRsiAtrStrategy:
    def __init__(self, live_mode=False, historical_file=None, duration='5 D'):
        """
        Strategy using EMA(9), EMA(21), RSI(9), Volume, and ATR(9).
        Only one trade at a time.
        Logs to trade_log.txt and writes trades to trade_results.csv with detailed info.
        """
        self.live_mode = live_mode
        self.historical_file = historical_file
        self.duration = duration
        
        # 1 MES point = $5, used for approximate PnL calculation
        self.tick_value = 5
        
        # Create an IB instance only if needed (to download or run live)
        if self.live_mode or self.historical_file is None:
            self.ib = IB()
        else:
            self.ib = None
        
        self.active_trade = None
        self.results = []
        self.recent_bars = []  # rolling storage of bars (dicts)
        self.trade_count = 0   # increments each time we open a new trade
        
        # -------------------------------------------------------------
        # Contract: MESH5 (Mar 2025)
        # -------------------------------------------------------------
        self.contract = Contract()
        self.contract.symbol = "MES"
        self.contract.secType = "FUT"
        self.contract.exchange = "CME"
        self.contract.currency = "USD"
        self.contract.lastTradeDateOrContractMonth = "20250321"
        self.contract.localSymbol = "MESH5"
        self.contract.multiplier = "5"
        
        # Connect if we created an IB instance
        if self.ib:
            self.ib.connect()
        
        # Configure logging
        logging.basicConfig(
            filename='trade_log.txt',
            level=logging.INFO,
            format='%(asctime)s - %(message)s'
        )

    # -------------------------------------------------------------------------
    # INDICATOR CALCULATIONS
    # -------------------------------------------------------------------------
    def compute_indicators(self, df):
        """
        Compute EMA(9), EMA(21), RSI(9), ATR(9) for the entire DataFrame.
        Assumes columns: [time, price, high, low, volume].
        """
        df['ema9'] = df['price'].ewm(span=9, adjust=False).mean()
        df['ema21'] = df['price'].ewm(span=21, adjust=False).mean()
        df['rsi9'] = self.compute_rsi(df['price'], period=9)
        df['atr9'] = self.compute_atr(df, period=9)
        return df

    def compute_rsi(self, series, period=14):
        """
        Standard RSI calculation on 'series' (usually the close).
        """
        delta = series.diff()
        gain = np.where(delta > 0, delta, 0.0)
        loss = np.where(delta < 0, -delta, 0.0)
        
        avg_gain = pd.Series(gain).ewm(span=period, adjust=False).mean()
        avg_loss = pd.Series(loss).ewm(span=period, adjust=False).mean()
        
        rs = avg_gain / avg_loss
        rsi = 100 - (100 / (1 + rs))
        return pd.Series(rsi).fillna(50)  # neutral if no data

    def compute_atr(self, df, period=14):
        """
        Standard ATR(14) using columns [price (close), high, low].
        """
        prev_close = df['price'].shift(1)
        high_low = df['high'] - df['low']
        high_close = (df['high'] - prev_close).abs()
        low_close = (df['low'] - prev_close).abs()
        tr = high_low.combine(high_close, max).combine(low_close, max)
        atr = tr.ewm(span=period, adjust=False).mean()
        # Fill from bottom up, then zero if still NaN
        atr = atr.bfill().fillna(0)
        return atr

    # -------------------------------------------------------------------------
    # DATA / BACKTEST / LIVE
    # -------------------------------------------------------------------------
    def download_historical_data(self):
        """
        Downloads 1-minute historical data from IB for 'duration'.
        """
        if not self.ib:
            logging.info("IB instance not available. Cannot download historical data.")
            return None
        
        try:
            qualified_contracts = self.ib.qualifyContracts(self.contract)
            if not qualified_contracts:
                logging.info("No valid contract found for MESH5.")
                return None
            
            self.contract = qualified_contracts[0]
            logging.info(f"Downloading {self.duration} of 1-min bars for MESH5...")
            bars = self.ib.reqHistoricalData(
                self.contract,
                endDateTime='',
                durationStr=self.duration,
                barSizeSetting='1 min',
                whatToShow='TRADES',
                useRTH=False,
                formatDate=1,
                keepUpToDate=False
            )
            if not bars or len(bars) == 0:
                logging.info("No historical data returned.")
                return None
            
            df = util.df(bars)
            if df.empty:
                logging.info("Historical data is empty.")
                return None
            
            df.rename(columns={'date': 'time', 'close': 'price'}, inplace=True)
            df['time'] = pd.to_datetime(df['time'])
            return df
        except Exception as e:
            logging.error(f"Error downloading data: {e}")
            return None

    def monitor_market(self):
        """
        Entry point: run in live mode or backtest mode.
        """
        if self.live_mode:
            self.run_live()
        else:
            self.run_backtest()

    def run_live(self):
        """
        Subscribes to real-time data from IB.
        """
        self.ib.qualifyContracts(self.contract)
        self.ib.reqMktData(self.contract, '', False, False)
        logging.info("Running LIVE on MESH5 (2025-03-21).")
        
        while True:
            ticker = self.ib.ticker(self.contract)
            if ticker and ticker.marketPrice():
                bar = {
                    'time': datetime.now(),
                    'price': ticker.marketPrice(),
                    'high': ticker.high or ticker.marketPrice(),
                    'low': ticker.low or ticker.marketPrice(),
                    'volume': ticker.volume or 0,
                    'ema9': None,
                    'ema21': None,
                    'rsi9': None,
                    'atr9': None,
                    'bar_index': None
                }
                self.process_tick(bar)
            time.sleep(1)

    def run_backtest(self):
        """
        Loads data from CSV or downloads from IB, computes indicators,
        and processes bars with a 1-hour warm-up period before opening trades.
        """
        if self.historical_file:
            df = pd.read_csv(self.historical_file)
            # Minimal cleanup
            if 'date' in df.columns and 'time' not in df.columns:
                df.rename(columns={'date': 'time'}, inplace=True)
            if 'close' in df.columns and 'price' not in df.columns:
                df.rename(columns={'close': 'price'}, inplace=True)
            if 'high' not in df.columns:
                df['high'] = df['price']
            if 'low' not in df.columns:
                df['low'] = df['price']
            df['time'] = pd.to_datetime(df['time'])
            df.sort_values(by='time', inplace=True)
        else:
            df = self.download_historical_data()
            if df is None or df.empty:
                logging.info("No data for backtest. Exiting.")
                return
        
        # Ensure minimal columns
        df = df[['time', 'price', 'high', 'low', 'volume']]
        # Compute indicators
        df = self.compute_indicators(df)
        
        logging.info("Running backtest with EMA(9), EMA(21), RSI(9), ATR(9).")
        
        # -------------------------------------------
        # WARM-UP PERIOD: 1 HOUR from the first bar
        # -------------------------------------------
        if not df.empty:
            first_timestamp = df['time'].iloc[0]
            warmup_cutoff = first_timestamp + pd.Timedelta(hours=1)
        else:
            warmup_cutoff = None
        
        # Process each bar
        for idx, row in df.iterrows():
            tick = row.to_dict()
            tick['bar_index'] = idx
            self.process_tick(tick, warmup_cutoff=warmup_cutoff)
        
        self.print_backtest_summary()

    # -------------------------------------------------------------------------
    # STRATEGY LOGIC
    # -------------------------------------------------------------------------
    def detect_trade_signal(self):
        """
        Basic bullish condition: EMA(9) > EMA(21) and RSI(9) > 50.
        """
        if not self.recent_bars:
            return False
        
        last_bar = self.recent_bars[-1]
        # If any indicator is missing, skip
        if any(last_bar.get(ind) is None for ind in ['ema9','ema21','rsi9','atr9']):
            return False
        
        ema_condition = (last_bar['ema9'] > last_bar['ema21'])
        rsi_condition = (last_bar['rsi9'] > 50)
        return (ema_condition and rsi_condition)

    def process_tick(self, tick, warmup_cutoff=None):
        """
        Processes each bar (tick in backtest).
        - Checks bar order
        - Appends to recent bars
        - Skips opening new trades if still in warm-up
        """
        self.check_bar_order(tick)
        self.recent_bars.append(tick)
        if len(self.recent_bars) > 50:
            self.recent_bars.pop(0)
        
        # If there's already an open trade, manage it
        if self.active_trade is not None:
            self.manage_trade(tick)
            return
        
        # If we're still in the warm-up period, do not open trades yet
        if warmup_cutoff is not None and tick['time'] < warmup_cutoff:
            return
        
        # Otherwise, check for a new setup
        self.check_for_trade_setup(tick)

    def check_bar_order(self, tick):
        """
        Ensure the new bar's timestamp is strictly after the last bar's timestamp.
        """
        if self.recent_bars:
            last_time = self.recent_bars[-1]['time']
            if tick['time'] <= last_time:
                msg = f"Timestamp error: {tick['time']} is not after {last_time}"
                logging.error(msg)
                raise ValueError(msg)

    def check_for_trade_setup(self, tick):
        """
        If detect_trade_signal() returns True, open a new LONG trade.
        """
        if self.detect_trade_signal():
            atr_val = tick.get('atr9', 0)
            if not atr_val or atr_val <= 0:
                # fallback if missing
                atr_val = 2.0
            
            stop_loss = tick['price'] - (atr_val * 1.5)
            take_profit = tick['price'] + (atr_val * 3)
            
            self.trade_count += 1
            self.active_trade = {
                'Trade #': self.trade_count,
                'Entry Bar': tick.get('bar_index'),
                'Entry Time': tick['time'],
                'Entry Price': tick['price'],
                'Stop Loss': stop_loss,
                'Take Profit': take_profit,
                'Exit Bar': None,
                'Exit Time': None,
                'Exit Price': None,
                'Result': None,
                'PnL': 0.0
            }
            
            logging.info(
                f"[Trade] OPEN #{self.trade_count} at bar {tick.get('bar_index')} "
                f"(price={tick['price']}, SL={stop_loss}, TP={take_profit}, time={tick['time']})"
            )

    def manage_trade(self, tick):
        """
        Checks if price hits SL or TP, closes the trade if so.
        """
        price = tick['price']
        if price >= self.active_trade['Take Profit']:
            self.log_trade(tick, 'Profit')
        elif price <= self.active_trade['Stop Loss']:
            self.log_trade(tick, 'Loss')

    def log_trade(self, tick, result):
        """
        Closes out the trade, computes PnL, logs it, and saves to CSV.
        """
        self.active_trade['Exit Bar'] = tick.get('bar_index')
        self.active_trade['Exit Time'] = tick['time']
        self.active_trade['Exit Price'] = tick['price']
        self.active_trade['Result'] = result
        
        # For a single LONG MES contract
        points = tick['price'] - self.active_trade['Entry Price']
        self.active_trade['PnL'] = points * self.tick_value
        
        trade_num = self.active_trade['Trade #']
        logging.info(
            f"[Trade] CLOSE #{trade_num} with {result} at bar {tick.get('bar_index')} "
            f"(price={tick['price']}, time={tick['time']}, PnL={self.active_trade['PnL']})"
        )
        
        self.results.append(self.active_trade.copy())
        self.active_trade = None
        self.save_results()

    def save_results(self):
        """
        Saves trade history to 'trade_results.csv' after each closed trade
        with the EXACT columns you requested, in the same order.
        """
        # Force the columns to appear in the exact sequence you specified:
        columns_order = [
            'Trade #', 'Entry Bar', 'Entry Time', 'Entry Price',
            'Stop Loss', 'Take Profit', 'Exit Bar', 'Exit Time',
            'Exit Price', 'Result', 'PnL'
        ]
        df = pd.DataFrame(self.results, columns=columns_order)
        df.to_csv('trade_results.csv', index=False)

    def print_backtest_summary(self):
        """
        Logs final stats: # trades, winners, losers, total PnL, profit factor, etc.
        """
        total_trades = len(self.results)
        winners = sum(1 for t in self.results if t['Result'] == 'Profit')
        losers = sum(1 for t in self.results if t['Result'] == 'Loss')
        total_pnl = sum(t['PnL'] for t in self.results)

        # Calculate profit factor: (Sum of winning PnL) / (absolute sum of losing PnL)
        winning_pnl = sum(t['PnL'] for t in self.results if t['PnL'] > 0)
        losing_pnl = sum(t['PnL'] for t in self.results if t['PnL'] < 0)
        if losing_pnl != 0:
            profit_factor = winning_pnl / abs(losing_pnl)
            profit_factor_str = f"{profit_factor:.2f}"
        else:
            profit_factor_str = "N/A"  # No losing trades => no negative PnL

        summary_str = (
            f"Backtest complete (MESH5, 20250321). "
            f"Total Trades: {total_trades}, Winners: {winners}, Losers: {losers}, "
            f"Total PnL: ${total_pnl:.2f}, "
            f"Profit Factor: {profit_factor_str}, "
            f"Duration={self.duration}"
        )
        logging.info(summary_str)
        # No print statement—only log

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--live', action='store_true', help='Run in live mode')
    parser.add_argument('--file', type=str, help='CSV file for historical data')
    parser.add_argument('--duration', type=str, default='7 D', help='Historical duration (e.g. 5 D)')
    args = parser.parse_args()

    strategy = EmaRsiAtrStrategy(
        live_mode=args.live,
        historical_file=args.file,
        duration=args.duration
    )
    strategy.monitor_market()
