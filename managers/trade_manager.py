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
    Oversees the entire trade lifecycle: entries, exits, and order management for stop-loss
    and take-profit, plus logs trades. The trade log will have 14 columns:
    
      Trade #, Date, Time, Symbol, Entry Price, Stop Loss, Target Price,
      Exit Price, Exit Date, Exit Time, Result, P/L, Comments, Side
    """
    def __init__(self,
                 entry_manager: EntryManager,
                 exit_manager: ExitManager,
                 stop_loss_manager: StopLossManager,
                 take_profit_manager: TakeProfitManager,
                 trade_executor: TradeExecutor,
                 config: dict,
                 log_filename: str = "trade_log.csv"):
        self.entry_manager = entry_manager
        self.exit_manager = exit_manager
        self.stop_loss_manager = stop_loss_manager
        self.take_profit_manager = take_profit_manager
        self.trade_executor = trade_executor
        self.config = config
        self.log_filename = log_filename

        self.current_position = None  # holds info about the open position (if any)
        self.trade_counter = 0        # increments for every new trade

        self._ensure_log_headers()

    def _ensure_log_headers(self):
        """
        Ensure that the trade log file is created with the correct header.
        If an old version exists, please delete it so that the new header (with 14 columns)
        is written.
        """
        header = [
            "Trade #", "Date", "Time", "Symbol", "Entry Price", "Stop Loss",
            "Target Price", "Exit Price", "Exit Date", "Exit Time", "Result",
            "P/L", "Comments", "Side"
        ]
        if not os.path.isfile(self.log_filename):
            with open(self.log_filename, mode="w", newline="", encoding="utf-8") as f:
                writer = csv.writer(f)
                writer.writerow(header)
        else:
            with open(self.log_filename, mode="r", newline="", encoding="utf-8") as f:
                existing_header = next(csv.reader(f))
            if len(existing_header) != len(header):
                with open(self.log_filename, mode="w", newline="", encoding="utf-8") as f:
                    writer = csv.writer(f)
                    writer.writerow(header)

    def update(self, data_point: dict, indicators: dict):
        """
        Called for every new bar (or tick). Decides if we open or close trades.
        """
        price = data_point.get('close')
        if self.current_position is None:
            # No open position; check for an entry signal.
            entry_signal = self.entry_manager.evaluate_entry(data_point, indicators)
            if entry_signal:
                self._open_position(entry_signal, price, data_point)
        else:
            # Manage the existing position.
            self._manage_open_position(data_point, indicators)

    def _open_position(self, entry_signal, price, data_point):
        """Handles opening a new position (LONG or SHORT)."""
        self.trade_counter += 1
        trade_id = self.trade_counter

        # Get basic data.
        symbol = self.config.get("contract", {}).get("symbol", "N/A")
        dt = data_point.get('time', datetime.now())
        trade_date = dt.strftime("%Y-%m-%d")
        trade_time = dt.strftime("%H:%M:%S")

        quantity = 1  # This may be set from risk management or config.
        pos_type = entry_signal['type']
        sl_pct = self.config['trading']['stop_loss_pct']
        tp_pct = self.config['trading']['take_profit_pct']

        if pos_type == 'LONG':
            stop_loss_price = price * (1 - sl_pct)
            take_profit_price = price * (1 + tp_pct)
        else:
            stop_loss_price = price * (1 + sl_pct)
            take_profit_price = price * (1 - tp_pct)

        if stop_loss_price:
            self.stop_loss_manager.set_initial_stop(price, pos_type)

        # Prepare the trade signal (market order).
        trade_signal = {
            'type': pos_type,
            'quantity': quantity,
            'price': None,
            'stop_loss': stop_loss_price,
            'take_profit': take_profit_price
        }
        self.trade_executor.execute_trade(trade_signal)

        self.current_position = {
            'trade_id': trade_id,
            'date': trade_date,
            'time': trade_time,
            'symbol': symbol,
            'entry_price': price,
            'stop_loss': stop_loss_price,
            'take_profit': take_profit_price,
            'type': pos_type,  # "LONG" or "SHORT"
            'quantity': quantity
        }

        with open("trade_record.text", "a") as f:
            f.write(f"ENTRY {pos_type} @ {price:.4f}\n")

    def _manage_open_position(self, data_point, indicators):
        """Checks whether to exit the open position (via signal, TP, or SL)."""
        price = data_point.get('close')
        pos_type = self.current_position['type']
        entry_price = self.current_position['entry_price']
        quantity = self.current_position['quantity']
        stop_price = self.current_position.get('stop_loss')
        take_price = self.current_position.get('take_profit')

        new_stop = self.stop_loss_manager.update_stop_loss(price, pos_type)
        if new_stop:
            self.current_position['stop_loss'] = new_stop

        exit_signal = self.exit_manager.evaluate_exit(data_point, indicators, self.current_position)
        exit_reason = exit_signal.get('reason', 'strategy_exit') if exit_signal else None

        hit_tp = False
        hit_sl = False
        if pos_type == 'LONG':
            if take_price and price >= take_price:
                hit_tp = True
                exit_reason = 'take_profit_hit'
            if stop_price and price <= stop_price:
                hit_sl = True
                exit_reason = 'stop_loss_hit'
        else:
            if take_price and price <= take_price:
                hit_tp = True
                exit_reason = 'take_profit_hit'
            if stop_price and price >= stop_price:
                hit_sl = True
                exit_reason = 'stop_loss_hit'

        if exit_signal or hit_tp or hit_sl:
            exit_trade_signal = {
                'type': 'EXIT',
                'position_type': pos_type,
                'quantity': quantity,
                'price': None
            }
            self.trade_executor.execute_trade(exit_trade_signal)
            if pos_type == 'LONG':
                profit = (price - entry_price) * quantity
            else:
                profit = (entry_price - price) * quantity
            self._finalize_trade(data_point, profit, exit_reason)

    def _finalize_trade(self, data_point, profit, exit_reason):
        """
        Closes out the trade, logs the trade details to the CSV file, and clears current_position.
        """
        dt_exit = data_point.get('time', datetime.now())
        exit_date = dt_exit.strftime("%Y-%m-%d")
        exit_time = dt_exit.strftime("%H:%M:%S")
        result_str = "Win" if profit >= 0 else "Loss"

        with open("trade_record.text", "a") as f:
            f.write(f"EXIT {self.current_position['type']} @ {data_point['close']:.4f}, "
                    f"P/L: {profit:.2f}, Reason: {exit_reason}\n")

        self._log_trade_to_csv(
            trade_id=self.current_position['trade_id'],
            date=self.current_position['date'],
            time=self.current_position['time'],
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
            side=self.current_position['type'].upper()
        )

        logging.info(f"TradeManager: Exited {self.current_position['type']} at {data_point['close']:.4f} "
                     f"(Reason: {exit_reason}), P/L={profit:.2f}")
        self.current_position = None

    def _log_trade_to_csv(self,
                          trade_id,
                          date,         # entry date
                          time,         # entry time
                          symbol,
                          entry_price,
                          stop_loss,
                          target_price,
                          exit_price,
                          exit_date,    # exit date
                          exit_time,
                          result,
                          pnl,
                          comments,
                          side):
        """
        Appends a single trade row to the CSV file.
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
                exit_date,             # Exit Date
                exit_time,
                result,                # Result (Win/Loss)
                f"{pnl:.2f}",
                comments,
                side                   # Side ("LONG" or "SHORT")
            ])
