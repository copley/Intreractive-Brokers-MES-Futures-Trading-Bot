import datetime
import backtrader as bt

class OpeningBreakoutStrategy(bt.Strategy):
    params = dict(
        # Indicators
        ema_period=20,
        rsi_period=14,
        atr_period=14,
        
        # Trading rules
        rsi_overbought=70,
        rsi_oversold=30,
        
        # Stop loss / Take profit (as fraction of entry price)
        stop_loss_pct=0.005,     # 0.5%
        take_profit_pct=0.01,    # 1%
        
        # Session times (adjust to your broker/exchange)
        session_start_time=datetime.time(9, 30),
        session_open_range_minutes=30,
        
        # Maximum positions
        max_position=1,
    )

    def __init__(self):
        """
        Initialize indicators and placeholders.
        """
        # 1) Indicators
        self.ema = bt.indicators.ExponentialMovingAverage(
            self.data.close, period=self.params.ema_period
        )
        self.rsi = bt.indicators.RSI(self.data.close, period=self.params.rsi_period)
        self.atr = bt.indicators.ATR(self.data, period=self.params.atr_period)
        
        # 2) Variables to store the opening range high/low
        self.open_range_high = None
        self.open_range_low = None
        
        # Flag to mark when we’ve captured the opening range
        self.open_range_recorded = False

    def start(self):
        """
        Called once when the strategy starts.
        You can also do any precomputation here if needed.
        """
        pass

    def next(self):
        """
        The main logic that runs on every bar (e.g., every minute).
        """
        current_time = self.data.datetime.time(0)
        current_date = self.data.datetime.date(0)
        
        # 1) Check if it's a new day/session -> reset opening range
        if self._is_new_session():
            self.open_range_high = None
            self.open_range_low = None
            self.open_range_recorded = False
        
        # 2) During the opening range (e.g. first 30 minutes), track high/low
        session_start = datetime.datetime.combine(current_date, self.params.session_start_time)
        session_open_range_end = session_start + datetime.timedelta(minutes=self.params.session_open_range_minutes)
        
        # Convert current backtrader datetime to a Python datetime
        # (Backtrader's data feed often merges date+time in a single float).
        # This is a simplistic approach:
        bar_datetime = bt.num2date(self.data.datetime[0])
        
        if bar_datetime < session_open_range_end:
            # Update the opening range high/low
            if self.open_range_high is None or self.data.high[0] > self.open_range_high:
                self.open_range_high = self.data.high[0]
            if self.open_range_low is None or self.data.low[0] < self.open_range_low:
                self.open_range_low = self.data.low[0]
        else:
            # Once past the opening range window, mark it as recorded
            if not self.open_range_recorded:
                self.open_range_recorded = True

            # If we haven't opened any positions yet, check for breakout signals
            if len(self.positions) < self.params.max_position:
                # 3) Entry Logic
                # Check if price breaks above the opening range high
                if self.open_range_recorded and self.data.close[0] > self.open_range_high:
                    # Optional RSI condition (e.g., ensure RSI not overbought)
                    if self.rsi[0] < self.params.rsi_overbought:
                        self._enter_position(direction='long')
                
                # Check if price breaks below the opening range low
                elif self.open_range_recorded and self.data.close[0] < self.open_range_low:
                    # Optional RSI condition (e.g., ensure RSI not oversold)
                    if self.rsi[0] > self.params.rsi_oversold:
                        self._enter_position(direction='short')

    def _enter_position(self, direction='long'):
        """
        Helper method to enter a trade (long or short)
        and place associated stop-loss & take-profit orders.
        """
        if direction == 'long':
            size = self._calc_position_size()
            entry_price = self.data.close[0]
            stop_price = entry_price * (1.0 - self.params.stop_loss_pct)
            take_profit_price = entry_price * (1.0 + self.params.take_profit_pct)
            
            # Enter Long
            buy_order = self.buy(size=size)
            
            # Place bracket orders (stop-loss and take-profit)
            self.sell(size=size, exectype=bt.Order.Stop, price=stop_price, parent=buy_order)
            self.sell(size=size, exectype=bt.Order.Limit, price=take_profit_price, parent=buy_order)
        
        elif direction == 'short':
            size = self._calc_position_size()
            entry_price = self.data.close[0]
            stop_price = entry_price * (1.0 + self.params.stop_loss_pct)
            take_profit_price = entry_price * (1.0 - self.params.take_profit_pct)
            
            # Enter Short
            sell_order = self.sell(size=size)
            
            # Place bracket orders
            self.buy(size=size, exectype=bt.Order.Stop, price=stop_price, parent=sell_order)
            self.buy(size=size, exectype=bt.Order.Limit, price=take_profit_price, parent=sell_order)

    def _calc_position_size(self):
        """
        Placeholder for any position sizing logic.
        For a futures contract, you might have to incorporate multiplier, margin, etc.
        """
        return 1

    def _is_new_session(self):
        """
        Check if this bar's date is different from the previous bar's date
        (meaning a new day/session).
        """
        # Only execute logic if we have data from previous day
        if len(self) < 2:
            return False
        
        prev_date = self.data.datetime.date(-1)
        curr_date = self.data.datetime.date(0)
        return curr_date != prev_date


# --- RUN THE BACKTEST ---

if __name__ == '__main__':
    # 1) Create a Cerebro engine
    cerebro = bt.Cerebro()

    # 2) Add our custom strategy
    cerebro.addstrategy(OpeningBreakoutStrategy)

    # 3) Load Data
    # For example, reading a CSV file with 1-minute bars (datetime, open, high, low, close, volume, etc.)
    # Make sure it has a 'Date' and 'Time' or combined 'datetime' column suitable for Backtrader.
    data = bt.feeds.GenericCSVData(
        dataname='MES-1min.csv',  
        dtformat='%Y-%m-%d %H:%M:%S',
        openinterest=-1,
        timeframe=bt.TimeFrame.Minutes, 
        compression=1
    )
    
    cerebro.adddata(data)

    # 4) Set broker parameters
    cerebro.broker.set_cash(100000.0)  # starting capital
    cerebro.broker.setcommission(commission=2.0, margin=None)  # example commission

    # 5) Run the backtest
    results = cerebro.run()
    final_value = cerebro.broker.getvalue()
    print(f"Final Portfolio Value: {final_value}")

    # 6) Plot if you want
    # cerebro.plot()
