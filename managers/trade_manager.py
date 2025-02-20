#!/usr/bin/env python3
import os
import csv
import logging
from datetime import datetime

from managers.entry_manager import EntryManager
from managers.exit_manager import ExitManager
from managers.stop_loss_manager import StopLossManager
from managers.take_profit_manager import TakeProfitManager
from execution.trade_execution_logic import TradeExecutor

class TradeManager:
    """
    Oversees the entire trade lifecycle: entries, exits, and order
    management for stop-loss and take-profit, plus logs trades.
    """

    def __init__(self,
                 entry_manager: EntryManager,
                 exit_manager: ExitManager,
                 stop_loss_manager: StopLossManager,
                 take_profit_manager: TakeProfitManager,
                 trade_executor: TradeExecutor,
                 config: dict):
        self.entry_manager = entry_manager
        self.exit_manager = exit_manager
        self.stop_loss_manager = stop_loss_manager
        self.take_profit_manager = take_profit_manager
        self.trade_executor = trade_executor
        self.config = config

        self.current_position = None  # holds info about the open position (if any)
        self.trade_counter = 0       # increments for every new trade

        # The file to which we log completed trades
        self.log_filename = "trade_log.csv"
        self._ensure_log_headers()

    def _ensure_log_headers(self):
        """
        Ensure 'trade_log.csv' has a header row, so we can append trades easily.
        We add 'Side' and 'Exit Date' columns so compute_trade_stats.py can do LONG/SHORT separation
        and we store exit dates as well.
        """
        if not os.path.isfile(self.log_filename):
            with open(self.log_filename, mode="w", newline="", encoding="utf-8") as f:
                writer = csv.writer(f)
                writer.writerow([
                    "Trade #",
                    "Date",         # Entry date
                    "Time",         # Entry time
                    "Symbol",
                    "Entry Price",
                    "Stop Loss",
                    "Target Price",
                    "Exit Price",
                    "Exit Date",    # new
                    "Exit Time",
                    "Result",
                    "P/L",
                    "Comments",
                    "Side"          # "LONG" or "SHORT"
                ])

    def update(self, data_point: dict, indicators: dict):
        """
        Called for every new bar (or tick). Decides if we open or close trades.
        """
        price = data_point.get('close')
        if self.current_position is None:
            # No open position, check for entry signal
            entry_signal = self.entry_manager.evaluate_entry(data_point, indicators)
            if entry_signal:
                self._open_position(entry_signal, price, data_point)
        else:
            # Manage an existing position
            self._manage_open_position(data_point, indicators)

    def _open_position(self, entry_signal, price, data_point):
        """
        Handles opening a new position (LONG or SHORT).
        """
        # Step 1: increment trade counter for a new trade
        self.trade_counter += 1
        trade_id = self.trade_counter

        # Basic data from the bar
        symbol = self.config.get("contract", {}).get("symbol", "N/A")
        dt = data_point['time'] if data_point.get('time') else datetime.now()
        trade_date = dt.strftime("%Y-%m-%d")
        trade_time = dt.strftime("%H:%M:%S")

        # Decide quantity, side, and price levels
        quantity = 1  # or from config
        pos_type = entry_signal['type']
        sl_pct = self.config['trading']['stop_loss_pct']
        tp_pct = self.config['trading']['take_profit_pct']

        if pos_type == 'LONG':
            stop_loss_price = price * (1 - sl_pct)
            take_profit_price = price * (1 + tp_pct)
        else:  # 'SHORT'
            stop_loss_price = price * (1 + sl_pct)
            take_profit_price = price * (1 - tp_pct)

        # If you want dynamic trailing stops:
        if stop_loss_price:
            self.stop_loss_manager.set_initial_stop(price, pos_type)

        # Prepare the trade signal (market order)
        trade_signal = {
            'type': pos_type,
            'quantity': quantity,
            'price': None,  # None => Market
            'stop_loss': stop_loss_price,
            'take_profit': take_profit_price
        }
        self.trade_executor.execute_trade(trade_signal)

        # Record the “position” in memory
        self.current_position = {
            'trade_id':      trade_id,
            'date':          trade_date,
            'time':          trade_time,
            'symbol':        symbol,
            'entry_price':   price,
            'stop_loss':     stop_loss_price,
            'take_profit':   take_profit_price,
            'type':          pos_type,    # "LONG" or "SHORT"
            'quantity':      quantity
        }

        # Optionally log to a text file
        with open("trade_record.text", "a") as f:
            f.write(f"ENTRY {pos_type} @ {price:.4f}\n")

    def _manage_open_position(self, data_point, indicators):
        """
        Checks if we need to exit due to an exit signal, stop-loss, or take-profit.
        """
        price = data_point.get('close')
        pos_type = self.current_position['type']
        entry_price = self.current_position['entry_price']
        quantity = self.current_position['quantity']
        stop_price = self.current_position.get('stop_loss')
        take_price = self.current_position.get('take_profit')

        # 1) Possibly update a trailing stop-loss
        new_stop = self.stop_loss_manager.update_stop_loss(price, pos_type)
        if new_stop:
            self.current_position['stop_loss'] = new_stop

        # 2) Check if the exit manager triggers a strategy-based exit
        exit_signal = self.exit_manager.evaluate_exit(data_point, indicators, self.current_position)
        exit_reason = None
        if exit_signal:
            exit_reason = exit_signal.get('reason', 'strategy_exit')

        # 3) Also check if price hits TP or SL
        hit_tp = False
        hit_sl = False
        if pos_type == 'LONG':
            if take_price and price >= take_price:
                hit_tp = True
                exit_reason = 'take_profit_hit'
            if stop_price and price <= stop_price:
                hit_sl = True
                exit_reason = 'stop_loss_hit'
        else:  # SHORT
            if take_price and price <= take_price:
                hit_tp = True
                exit_reason = 'take_profit_hit'
            if stop_price and price >= stop_price:
                hit_sl = True
                exit_reason = 'stop_loss_hit'

        if exit_signal or hit_tp or hit_sl:
            # Time to exit
            exit_trade_signal = {
                'type': 'EXIT',
                'position_type': pos_type,
                'quantity': quantity,
                'price': None  # market exit
            }
            self.trade_executor.execute_trade(exit_trade_signal)

            # Calculate final P/L
            if pos_type == 'LONG':
                profit = (price - entry_price) * quantity
            else:  # SHORT
                profit = (entry_price - price) * quantity

            self._finalize_trade(data_point, profit, exit_reason)

    def _finalize_trade(self, data_point, profit, exit_reason):
        """
        Closes out the trade, writes one row to CSV, and clears self.current_position.
        """
        dt_exit = data_point['time'] if data_point.get('time') else datetime.now()
        exit_date = dt_exit.strftime("%Y-%m-%d")
        exit_time = dt_exit.strftime("%H:%M:%S")

        result_str = "Win" if profit >= 0 else "Loss"

        # Optional text log
        with open("trade_record.text", "a") as f:
            f.write(
                f"EXIT {self.current_position['type']} @ {data_point['close']:.4f}, "
                f"P/L: {profit:.2f}, Reason: {exit_reason}\n"
            )

        # Append a row to trade_log.csv
        self._log_trade_to_csv(
            trade_id=self.current_position['trade_id'],
            date=self.current_position['date'],  # Entry date
            time=self.current_position['time'],  # Entry time
            symbol=self.current_position['symbol'],
            entry_price=self.current_position['entry_price'],
            stop_loss=self.current_position['stop_loss'],
            target_price=self.current_position['take_profit'],
            exit_price=data_point['close'],
            exit_date=exit_date,
            exit_time=exit_time,
            result=result_str,
            pnl=profit,
            comments=exit_reason or "",
            side=self.current_position['type'].upper()  # "LONG" or "SHORT"
        )

        logging.info(
            f"TradeManager: Exited {self.current_position['type']} at {data_point['close']:.4f} "
            f"(Reason: {exit_reason}), P/L={profit:.2f}"
        )

        # Reset the current position
        self.current_position = None

    def _log_trade_to_csv(self,
                          trade_id,
                          date,       # entry date
                          time,       # entry time
                          symbol,
                          entry_price,
                          stop_loss,
                          target_price,
                          exit_price,
                          exit_date,  # new
                          exit_time,
                          result,
                          pnl,
                          comments,
                          side):
        """
        Actually append a single trade row to trade_log.csv, including 'Side' and 'Exit Date'.
        """
        with open(self.log_filename, mode="a", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            writer.writerow([
                trade_id,              # Trade #
                date,                  # Entry Date
                time,                  # Entry Time
                symbol,
                f"{entry_price:.2f}",
                f"{stop_loss:.2f}" if stop_loss else "",
                f"{target_price:.2f}" if target_price else "",
                f"{exit_price:.2f}",
                exit_date,             # new
                exit_time,
                result,                # "Win" or "Loss"
                f"{pnl:.2f}",
                comments,
                side                   # "LONG" or "SHORT"
            ])
