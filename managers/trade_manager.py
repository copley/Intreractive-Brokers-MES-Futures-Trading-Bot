import logging
from managers.entry_manager import EntryManager
from managers.exit_manager import ExitManager
from managers.stop_loss_manager import StopLossManager
from managers.take_profit_manager import TakeProfitManager
from execution.trade_execution_logic import TradeExecutor

class TradeManager:
    """
    Oversees the entire trade lifecycle: entries, exits, and order management for stop-loss and take-profit.
    """
    def __init__(self, entry_manager: EntryManager, exit_manager: ExitManager,
                 stop_loss_manager: StopLossManager, take_profit_manager: TakeProfitManager,
                 trade_executor: TradeExecutor, config: dict):
        self.entry_manager = entry_manager
        self.exit_manager = exit_manager
        self.stop_loss_manager = stop_loss_manager
        self.take_profit_manager = take_profit_manager
        self.trade_executor = trade_executor
        self.config = config
        self.current_position = None  # holds info about the open position (if any)

    def update(self, data_point: dict, indicators: dict):
        """
        Update the trading logic with a new market data point and corresponding indicators.
        This will check for entry or exit signals and execute trades accordingly.
        """
        price = data_point.get('close')
        if self.current_position is None:
            # No open position, check for entry signal
            entry_signal = self.entry_manager.evaluate_entry(data_point, indicators)
            if entry_signal:
                # Determine quantity to trade (could be from config risk management; here fixed 1)
                quantity = 1
                entry_price = price
                pos_type = entry_signal['type']
                # Set initial stop-loss and take-profit based on config percentages
                stop_loss_price = None
                take_profit_price = None
                sl_pct = self.config['trading']['stop_loss_pct']
                tp_pct = self.config['trading']['take_profit_pct']
                if pos_type == 'LONG':
                    stop_loss_price = entry_price * (1 - sl_pct)
                    take_profit_price = entry_price * (1 + tp_pct)
                elif pos_type == 'SHORT':
                    stop_loss_price = entry_price * (1 + sl_pct)
                    take_profit_price = entry_price * (1 - tp_pct)
                # Use managers for any dynamic adjustments (e.g., round to tick, etc.)
                # Set initial stop using StopLossManager
                if stop_loss_price:
                    self.stop_loss_manager.set_initial_stop(entry_price, pos_type)
                # Prepare trade signal dict for execution
                trade_signal = {
                    'type': pos_type,
                    'quantity': quantity,
                    'price': None,             # None indicates market order
                    'stop_loss': stop_loss_price,
                    'take_profit': take_profit_price
                }
                # Execute the entry trade
                self.trade_executor.execute_trade(trade_signal)
                # Record the current position details
                self.current_position = {
                    'type': pos_type,
                    'entry_price': entry_price,
                    'quantity': quantity,
                    'stop_loss': stop_loss_price,
                    'take_profit': take_profit_price
                }
                # Log trade entry in trade record file
                with open("trade_record.text", "a") as f:
                    f.write(f"ENTRY {pos_type} @ {entry_price:.4f}\n")
        else:
            # There is an open position, manage it
            pos_type = self.current_position['type']
            entry_price = self.current_position['entry_price']
            quantity = self.current_position['quantity']
            stop_price = self.current_position.get('stop_loss')
            take_price = self.current_position.get('take_profit')
            # Update trailing stop-loss if applicable
            new_stop = self.stop_loss_manager.update_stop_loss(price, pos_type)
            if new_stop:
                # Update stored stop-loss price
                self.current_position['stop_loss'] = new_stop
                # In a live scenario, would modify the existing stop order via ib_connection
            # Check for exit signal from strategy (indicator-based)
            exit_signal = self.exit_manager.evaluate_exit(data_point, indicators, self.current_position)
            exit_reason = None
            if exit_signal:
                exit_reason = exit_signal.get('reason', 'strategy_exit')
            # Also check if price has hit take-profit or stop-loss levels
            hit_tp = False
            hit_sl = False
            if pos_type == 'LONG':
                if take_price and price >= take_price:
                    hit_tp = True
                    exit_reason = 'take_profit_hit'
                if stop_price and price <= stop_price:
                    hit_sl = True
                    exit_reason = 'stop_loss_hit'
            elif pos_type == 'SHORT':
                if take_price and price <= take_price:
                    hit_tp = True
                    exit_reason = 'take_profit_hit'
                if stop_price and price >= stop_price:
                    hit_sl = True
                    exit_reason = 'stop_loss_hit'
            if exit_signal or hit_tp or hit_sl:
                # If any exit condition met, execute exit trade
                exit_trade_signal = {
                    'type': 'EXIT',
                    'position_type': pos_type,
                    'quantity': quantity,
                    'price': None  # market exit
                }
                self.trade_executor.execute_trade(exit_trade_signal)
                # Log exit in trade record
                exit_price = price
                profit = 0.0
                if pos_type == 'LONG':
                    profit = (exit_price - entry_price) * quantity
                elif pos_type == 'SHORT':
                    profit = (entry_price - exit_price) * quantity
                with open("trade_record.text", "a") as f:
                    f.write(f"EXIT {pos_type} @ {exit_price:.4f}, P/L: {profit:.2f}, Reason: {exit_reason}\n")
                logging.info(f"TradeManager: Exited {pos_type} position at {exit_price:.4f} (Reason: {exit_reason})")
                # Clear current position
                self.current_position = None
