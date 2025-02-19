Main Entry Point

main.py
Loads the configuration (via helpers.load_config)
Sets up logging (via helpers.setup_logging)
Instantiates the main bot logic by creating an Aggregator object
Aggregator Initialization (in utils/aggregator.py)

Aggregator
Creates an IBConnection (from connection/ib_connection.py) to connect to Interactive Brokers
Creates a trading contract (using create_contract from connection/contract_definition.py)
Instantiates a DataLoader (from data/data_loader.py) to fetch historical data
Instantiates a DataPreprocessor (from data/data_preprocessor.py) to process raw data
Sets up strategy/indicator managers:
EntryManager (from managers/entry_manager.py)
ExitManager (from managers/exit_manager.py)
DynamicStopLoss (from managers/dynamic_stop_loss.py)
StopLossManager (from managers/stop_loss_manager.py)
TakeProfitManager (from managers/take_profit_manager.py)
Creates the TradeExecutor (from execution/trade_execution_logic.py) which handles order execution
Combines all the above into a TradeManager (from managers/trade_manager.py) that oversees the complete trade lifecycle
Running the Bot (inside Aggregator.run())

Fetches historical data via DataLoader.fetch_historical_data
Preprocesses the data using DataPreprocessor.preprocess
Iterates over each data bar while computing indicators using functions such as:
calculate_EMA (from indicators/indicator_logic_EMA.py)
calculate_RSI (from indicators/indicator_logic_RSI.py)
calculate_ATR (from indicators/indicator_logic_ATR.py)
calculate_VWAP (from indicators/indicator_logic_VWAP.py)
For each bar, it calls TradeManager.update which:
Uses EntryManager.evaluate_entry to check for entry signals
Uses ExitManager.evaluate_exit to check for exit signals
If a signal is generated, TradeExecutor.execute_trade is called to place orders via IBConnection
Finalization

Once data processing is complete, the bot disconnects from IB via IBConnection.disconnect
Execution ends with appropriate logging messages
Summary of Key Classes in the Flow:

Aggregator (main orchestrator)
├─ IBConnection
├─ DataLoader
├─ DataPreprocessor
├─ EntryManager
├─ ExitManager
├─ DynamicStopLoss
├─ StopLossManager
├─ TakeProfitManager
├─ TradeExecutor
└─ TradeManager
This is the high-level program flow when you run python3 main.py.




my_scalp_bot/
├── config.yaml  # Central configuration: IB credentials, bar length, indicator params, etc.
├── connection/
│   ├── contract_definition.py  # Encapsulates futures contract details (MES, XINA50, etc.)
│   └── ib_connection.py  # Manages IB connection, event callbacks, reconnection logic
├── data/
│   ├── data_loader.py  # (Optional) For loading historical data if you do backtesting
│   └── data_preprocessor.py  # (Optional) For cleaning/preprocessing historical data
├── execution/
│   ├── limit_order_execution_logic.py
│   ├── long_order_execution_logic.py
│   ├── short_order_execution_logic.py
│   ├── stop_loss_order_execution_logic.py
│   └── trade_execution_logic.py  # Orchestrates how orders would be placed/simulated
├── indicators/
│   ├── indicator_logic_EMA.py  # Example: compute EMA(9) & EMA(21)
│   ├── indicator_logic_RSI.py  # RSI(9)
│   ├── indicator_logic_ATR.py  # ATR(9)
│   ├── indicator_logic_VWAP.py  # Possibly includes volume-based logic
│   └── ...  
├── managers/
│   ├── dynamic_stop_loss.py
│   ├── entry_manager.py
│   ├── exit_manager.py
│   ├── stop_loss_manager.py
│   ├── take_profit_manager.py
│   └── trade_manager.py  # Coordinates entire trade lifecycle, partial fills, logs
├── utils/
│   └── helpers.py  # Utility functions (timestamps, math, concurrency helpers)
├── aggregator.py  # The TradeAggregator class for building bars from tick data
├── list_files.py  # A small utility to list or manage file directories/logs
├── main.py  # Entry point to run the bot:
│   # - loads config.yaml
│   # - connects to IB
│   # - starts aggregator
│   # - processes signals & logs trades
└── trade_record.text  # Logs of each trade or CSV/JSON logs



1. System Overview
1.1 Purpose & Scope
Purpose

Analyze live market data (for MES or other futures, e.g., XINA50 in your sample code) on a short time frame (e.g., 1-minute or 30-second bars).
Identify short-term (scalp) trading opportunities using momentum, volume, and volatility indicators.
Log or simulate trades based on entry/exit conditions. (No actual order placement in this version—though you may expand to real IB orders later.)
Limit concurrency to one trade active at a time (once the first trade closes, the next can begin).
Scope

Real-time data subscription via Interactive Brokers’ TWS API.
Indicator calculations (e.g., EMAs, RSI, ATR, volume filters).
Generate & log signals for potential trades.
Log each trade (entry, exit, partial fills, P/L) for performance analysis.
Produce summary statistics (win/loss, net profit, profit factor, etc.).
1.2 High-Level Workflow
Initialization

Load settings (IB connection info, bar length, indicator periods) from config.yaml.
Connect to TWS via the native Python API (EWrapper/EClient) or a similar approach.
Define contract details (MES, XINA50, etc.).
Data Acquisition

Subscribe to tick-by-tick or frequent snapshot data from IB.
Use an aggregator to convert raw trades (with timestamps & prices) into time-based bars (e.g., 15-second or 30-second).
Indicator Calculation

For each new bar, compute EMA(9 & 21), RSI(9), ATR(9), or any other relevant indicators (VWAP, Relative Volume, etc.).
Signal Generation & Trade Logging

Apply rules (e.g., bullish EMA crossover + above VWAP + high RVOL) to identify potential entries.
Check if no trade is currently active. If free to trade, log a “paper” entry (long or short).
While in a trade, monitor price relative to stop-loss and take-profit levels. Log partial fills if needed.
When the trade exits, record final P/L and exit reason in logs.
End-of-Day / End-of-Trade Reporting

Summarize trades in a final report: total trades, average P/L, total P/L, profit factor, etc.
2. Data Feed Method
2.1 How It Works
You provided a code snippet that shows how you retrieve real-time trades from IB and aggregate them into a bar of configurable length (e.g., 30 seconds). Here’s a condensed view of key points:

IBApi Class

Inherits from EWrapper and EClient.
Receives tick-by-tick trade events via tickByTickAllLast().
TradeAggregator Class

Accumulates trades in a bar until time crosses the bar boundary.
Once time crosses the boundary (e.g., 30 seconds elapsed), it finalizes (prints/stores) the bar and starts a new one.
Bar Construction

For each incoming trade, you update open/high/low/close (OHLC) and accumulate volume.
Once a bar closes, you log or pass the bar data along to your indicator modules.
Important Note: You are currently using a 30-second bar length in the aggregator. You mentioned you might do 15-second intervals or 1-minute intervals—this is easily configurable in TradeAggregator.

3. Event Handling
You are using the native Interactive Brokers Python API (i.e., EClient + EWrapper), not ib_insync in the example code.
Parallel Tasks: A typical approach is to run the IB “message loop” on one thread (as you do in run_loop). You can process bars on the main thread or dispatch them to another queue for concurrency.
You expressed interest in multi-threading but aren’t sure how to implement it. For now, the snippet you showed uses a single background thread for the IB loop. Additional concurrency (e.g., handling indicators or logging in parallel) can be added later if needed.
4. Error Recovery and Reconnection
You’ve requested automatic reconnect logic or a retry mechanism. Here’s what you might do:

On Disconnect: The error callback could detect a lost connection.
Retry Timer: Attempt to reconnect after a short delay (e.g., 5–30 seconds).
Data Gaps: If the connection is down for a while, you might need to fetch historical data to fill in missing bars.
(Implementation details can be added to ib_connection.py so the rest of your bot doesn’t have to worry about reconnection.)

5. Partial Fills
Even though you’re logging trades only, you’d like to store partial fill quantities. For example, you open a trade with size 10 contracts, but you may receive partial fills in increments (e.g., 3, then 4, then 3).

In Logging: Each fill event can be captured, storing:
Fill time
Fill size
Fill price
At the end, your total position is the sum of partial fills until it equals the requested order size. This can be simulated in your trade_manager.py or a dedicated fill manager module.

6. Transition to Real Orders (Future)
Right now, you do not place real orders.
You gave a sample code snippet using ib_insync to place a bracket order (market entry + OCA for stop-loss and limit).
In a future version, your trade_execution_logic.py could be replaced (or extended) to actually place an IB order, wait for a fill, then place bracket stop/limit orders, etc.
Whether you keep the same architecture or introduce new modules is flexible. The approach would be similar—just hooking into real placeOrder() calls.
7. Updated Directory & Module Breakdown
Below is the proposed file structure with an ASCII-based tree diagram. It shows how each folder/module ties together, assuming you want to build out the full system. (You can adopt or adapt as you see fit.)

plaintext
Copy
Edit
my_scalp_bot/
├── config.yaml                 # Central configuration: IB credentials, bar length, indicator params, etc.
├── connection/
│   ├── contract_definition.py  # Encapsulates futures contract details (MES, XINA50, etc.)
│   └── ib_connection.py        # Manages IB connection, event callbacks, reconnection logic
├── data/
│   ├── data_loader.py          # (Optional) For loading historical data if you do backtesting
│   └── data_preprocessor.py    # (Optional) For cleaning/preprocessing historical data
├── execution/
│   ├── limit_order_execution_logic.py
│   ├── long_order_execution_logic.py
│   ├── short_order_execution_logic.py
│   ├── stop_loss_order_execution_logic.py
│   └── trade_execution_logic.py # Orchestrates how orders *would* be placed/simulated
├── indicators/
│   ├── indicator_logic_EMA.py   # Example: compute EMA(9) & EMA(21)
│   ├── indicator_logic_RSI.py   # RSI(9)
│   ├── indicator_logic_ATR.py   # ATR(9)
│   ├── indicator_logic_VWAP.py  # Possibly includes volume-based logic
│   └── ...
├── managers/
│   ├── dynamic_stop_loss.py
│   ├── entry_manager.py
│   ├── exit_manager.py
│   ├── stop_loss_manager.py
│   ├── take_profit_manager.py
│   └── trade_manager.py         # Coordinates entire trade lifecycle, partial fills, logs
├── utils/
│   └── helpers.py               # Utility functions (timestamps, math, concurrency helpers)
├── aggregator.py                # The TradeAggregator class for building bars from tick data
├── list_files.py                # A small utility to list or manage file directories/logs
├── main.py                      # Entry point to run the bot:
│                                # - loads config.yaml
│                                # - connects to IB
│                                # - starts aggregator
│                                # - processes signals & logs trades
└── trade_record.text            # Logs of each trade or CSV/JSON logs
Note: The files with execution/ are placeholders if you later want to do real ordering or advanced logging of hypothetical limit/stop logic. In the immediate version, they can be minimal or empty as you only log trades.

8. Key Functional Requirements
Calibration Period

Wait for enough bars (e.g., 21 bars) to gather a valid EMA(21), RSI(9), or ATR(9) reading.
Don’t generate signals or log trades before the system has enough data.
Single Active Trade

If a trade is open, no new trades can open until it’s fully closed.
For partial fills, treat them as sub-events of the same trade.
Logging Over Execution

For each new “paper” trade, log the entry time/price/size, plus partial fills.
For exit, log the exit reason (stop-loss, take-profit, or manual close) and the final P/L.
Summarize performance once a session ends.
Performance Metrics

Track total trades, net P/L, average P/L per trade, largest drawdown, etc.
Possibly record partial fill details for thorough analysis.
9. Non-Functional Requirements
Reliability:

Should preserve logs on abrupt shutdown (e.g., Ctrl+C).
Consider reconnection logic to TWS if the connection is lost.
Maintainability:

Each module in a dedicated folder (as shown).
Expand or replace logic easily (e.g., adding a new indicator file or a real order method).
Performance:

For quick scalping intervals (15s, 30s, or 1m bars), aggregator and indicator calculations must be efficient.
IB rate limits must be respected (avoid too many data requests).
Security:

Store any IB credentials securely (mask or encrypt them).
Use TWS/Gateway with encrypted connections if possible.
10. Example Live Workflow (Using main.py + Aggregator)
Start the bot

python main.py
Loads config.yaml → obtains bar length (e.g., 30s), indicator periods, IB connection details.
Connects to TWS at host:port.
Aggregator Setup

Creates an instance of TradeAggregator(bar_length=30).
Subscribes to tick-by-tick data for your chosen contract (MES, XINA50, etc.).
For each incoming trade, aggregator updates the current bar’s OHLC and volume.
When time crosses a bar boundary, aggregator “closes” the bar and prints or queues it for indicator calculations.
Indicator & Signal Processing

Once a bar finalizes, your indicator modules compute new values (EMA, RSI, ATR, etc.).
If conditions meet (e.g., bullish crossover + volume confirmation + no current trade), trade_manager.py logs a new entry.
If a trade is open, it monitors partial fills (hypothetical or from real fill events if you eventually go live).
Trade Exit

If price hits the logged “stop-loss” or “take-profit,” exit_manager.py records an exit event.
The trade is considered closed. Now the system is ready to check signals for a new trade.
End-of-Day

Summaries are computed (win/loss ratio, total P/L, average hold time).
The session can be stopped safely.
11. Future Enhancements
Real Order Placement

Use the bracket order logic (as in your ib_insync snippet) to actually place orders.
Extend trade_execution_logic.py to integrate with TWS for real fills.
Advanced Concurrency

Add multi-thread or queue-based architecture to handle aggregator events vs. indicator updates in parallel.
Machine Learning / AI

Integrate an ML model or advanced statistics to refine signals.
GUI Dashboard

Real-time charting or P/L tracking to visualize strategy performance.
Robust Error Handling

Automatic reconnection if TWS restarts or network disruptions occur.
Conclusion
With the above structure, you have:

A clear modular layout for each system component—connection, managers, indicators, etc.
An aggregator that demonstrates how you build bars from incoming tick data.
A plan for logging partial fills and a future path for real trades.
Proposed reconnection logic so you can handle TWS disconnections gracefully.
An ASCII diagram giving a bird’s-eye view of all files/folders.
What I Understand About the App

It’s a scalp-bot concept, focusing on short bar intervals (15s, 30s, 1m).
Data is retrieved via tick-by-tick from TWS and aggregated into bars.
Indicators run after each finalized bar, generating potential “paper trades.”
You only log trades and partial fills—no real executions in the current version.
The system should eventually be robust enough to become a real algo-trading solution (placing bracket orders, stop-loss, limit, etc.) if you update the execution logic.


Core Trade Entry Logic
1. Data & Indicator Preparation
Data Source

Construct 1-minute bars (or aggregate smaller intervals, e.g., 15s or 30s bars, into 1-minute bars).
Each finalized 1-minute bar triggers an indicator update and a decision check.
Indicator Calculations (Per 1-minute Bar)

EMA(9) & EMA(21): Short-term vs. slightly longer short-term momentum.
VWAP (Optional but often recommended for intraday futures): Helps gauge whether price is trading above or below “average value.”
RSI(9): Momentum indicator measuring overbought/oversold conditions.
ATR(9): For volatility-based stop sizing.
Relative Volume (RVOL):
RVOL
=
Current Candle Volume
Average Volume over past N candles
RVOL= 
Average Volume over past N candles
Current Candle Volume
​
 
Pre-Trade Checks

Calibration Period: Wait at least 21 bars (if using EMA(21)) before taking any signals.
Single Active Trade Constraint: Ensure there is no open trade before evaluating a new entry signal.
2. Bullish Entry Conditions (Long Trades)
Trend Confirmation

EMA(9) > EMA(21) on the just-closed 1-minute bar (or the 1-minute bar that is about to form).
Price closing above VWAP (if using VWAP) further supports a bullish bias (optional but recommended).
Momentum & Overbought Check

RSI(9) > 50 to confirm bullish momentum (you can refine or skip if you want a pure crossover system).
If you are very strict, ensure RSI(9) is not over 70 if you prefer to avoid potential overbought zones.
Volume Confirmation

Relative Volume (RVOL) > 1.5 (example threshold).
This suggests higher-than-average participation; you want enough liquidity to make scalping worthwhile.
Entry Trigger

Wait for a crossover of EMA(9) above EMA(21) during or at the close of the 1-minute bar, or check that EMA(9) has been above EMA(21) for at least one bar and conditions remain valid.
Alternatively, use price pullback to EMA(9) or VWAP as a more conservative “pullback entry” after the bullish crossover.
Action

If conditions are met and no trade is open:
Log a new long trade entry (paper trade) at the close price of the 1-minute bar (or you could simulate a “market in next bar open” approach).
Set a stop-loss (based on ATR) and a take-profit (fixed scalp target, e.g., 3 points on MES).
3. Bearish Entry Conditions (Short Trades) [Optional]
(If your strategy is long-only, skip this. If you plan to short MES, use mirror logic.)

Trend Confirmation

EMA(9) < EMA(21)
Price closing below VWAP for added conviction (optional).
Momentum & Oversold Check

RSI(9) < 50 suggests downward momentum.
Some scalpers avoid short trades if RSI(9) is under 30 (deep oversold) unless going for a quick breakdown.
Volume Confirmation

RVOL > 1.5 again. You want strong selling volume to validate short entries.
Entry Trigger

EMA(9) crossing below EMA(21) or a retest of EMA(9) from beneath.
If conditions remain valid, log the short entry.
Stop/Target

Use similar ATR-based stop.
A small fixed take-profit (e.g., 3 points) if you’re purely scalping short.
4. Stop-Loss & Take-Profit Logic
Stop-Loss Placement (Dynamic or Fixed)

ATR-Based: E.g.,
Stop
=
Entry Price
−
(
1.5
×
ATR(9)
)
Stop=Entry Price−(1.5×ATR(9))
for a long trade. You may tighten or loosen the multiplier based on volatility.
Swing High/Low: If the latest swing point is within your risk tolerance, place the stop just beyond that.
Take-Profit Placement

Fixed Scalping Target:
Take-Profit
=
Entry Price
+
3
 points (for long)
Take-Profit=Entry Price+3 points (for long)
Or you can base partial exits on indicator signals (e.g., RSI crossing a certain threshold), but a fixed ~3-point target is often used for MES scalps.
Partial Fills

If simulating partial fills, you might break the trade size into smaller blocks, logging each fill event and fill price.
For your logging-based system, you can simply store them as multiple fill entries with the same “Trade ID.”
5. Example Step-by-Step Trade Entry
Scenario: A new 1-minute candle finalizes, and your aggregator completes a bar. Your indicators get updated:

The bar closes; aggregator prints:
Open: 4500.25, High: 4501.25, Low: 4499.75, Close: 4501.00, Volume: 12,000
You compute:
EMA(9) = 4500.90, EMA(21) = 4500.50 (9 > 21) → bullish short-term trend.
RSI(9) = 55 → bullish momentum.
Price above VWAP (say VWAP = 4499.80) → further bullish confirmation.
RVOL = 1.8 → trading volume is strong.
No current trade is active → check entry signal.
Condition: EMA(9) > EMA(21), RSI(9) > 50, RVOL > 1.5, Price > VWAP
All conditions met.
Enter Long:
You log a new “Long” trade at 4501.00 (bar close).
Stop-Loss (1.5 × ATR) → Suppose ATR(9) = 1.0; stop = 4501.00 - 1.5 = 4499.50.
Take-Profit = 4501.00 + 3.0 = 4504.00.
That data is stored in your logs:
vbnet
Copy
Edit
2025-02-17 12:01:00 | TradeID=ABC123 | Entry=4501.00 | Stop=4499.50 | TP=4504.00 | Size=1
6. Exiting the Trade
Although your question focuses on entry, remember:

If price hits 4499.50 (stop-loss), log a losing trade exit.
If price hits 4504.00 (take-profit), log a winning trade exit.
Possibly re-check signals after the next bar closes to see if a new trade can be opened.
7. Summary of the Core Logic
Wait for bar to finalize → aggregator closes out OHLC data.
Compute indicators → EMA(9 & 21), RSI(9), ATR(9), VWAP, and RVOL.
Check: No current position → Only one active trade is allowed.
If bullish signals all align → log a new long trade with a stop-loss and take-profit.
If short signals all align (optional) → log a new short trade with a stop-loss and take-profit.
Monitor the open trade until it stops out or hits the target.
Partial fills: If simulating them, record each fill event.
Once exited → Look for the next entry signal on subsequent bars.
Final Note
This Core Trade Entry Logic provides a concise, rules-based approach for scalping MES on a 1-minute chart:

Trend (EMA cross + above/below VWAP)
Momentum (RSI filter)
Volume (RVOL threshold)
Single trade at a time
ATR-based or fixed “scalp” profit target (~3 points on MES) and a correspondingly tight stop.
By following these steps:

You ensure trades only occur when short-term momentum and volume support the move.
You keep risk tight with an ATR-based stop.
You aim for a consistent scalp target, ideal for quick in-and-out trades on MES.
You can customize any threshold or indicator to your preference (e.g., different RSI level, 2.5-point vs. 3-point target, etc.), but this framework covers the essential logic for a robust 1-minute scalp strategy on the MES contract.

1. config.yaml (Sample Configuration)
yaml
Copy
Edit
# config.yaml
ib:
  host: "127.0.0.1"
  port: 7497
  clientId: 123

bar_length_seconds: 60  # 1-minute bars
max_trades_per_day: 10

indicators:
  ema_periods: [9, 21]    # For short & medium-term EMAs
  rsi_period: 9
  atr_period: 9
  use_vwap: true

volume:
  rvol_threshold: 1.5     # Relative Volume threshold

contract:
  symbol: "MES"
  secType: "FUT"
  exchange: "CME"
  currency: "USD"
  lastTradeDateOrContractMonth: "20250321"
  localSymbol: "MESH5"  # Example local symbol for March 2025
  multiplier: 5

risk:
  scalp_target_points: 3    # e.g., 3 points target
  atr_stop_multiplier: 1.5  # e.g., 1.5 * ATR for stop
  single_trade_mode: true   # Only one trade at a time

logging:
  log_file: "trade_record.text"
This YAML file contains:

IB connection details
Bar length (in seconds)
Indicator parameters
Contract specs (for MES)
Risk management settings
Logging info
2. connection/contract_definition.py
python
Copy
Edit
# connection/contract_definition.py
from ibapi.contract import Contract
import yaml
import os

def load_config(config_path="config.yaml"):
    with open(config_path, "r") as f:
        return yaml.safe_load(f)

def create_mes_contract(config_path="config.yaml"):
    """
    Reads contract details from config.yaml and returns a Contract object for MES.
    """
    config = load_config(config_path)
    contract_data = config.get("contract", {})

    contract = Contract()
    contract.symbol = contract_data.get("symbol", "MES")
    contract.secType = contract_data.get("secType", "FUT")
    contract.exchange = contract_data.get("exchange", "CME")
    contract.currency = contract_data.get("currency", "USD")
    contract.lastTradeDateOrContractMonth = contract_data.get("lastTradeDateOrContractMonth", "20250321")
    contract.localSymbol = contract_data.get("localSymbol", "MESH5")
    contract.multiplier = str(contract_data.get("multiplier", 5))

    return contract
Purpose: Encapsulates contract details for MES (or other futures).
Usage: In main.py, call create_mes_contract() to get the IB Contract object.

3. connection/ib_connection.py
python
Copy
Edit
# connection/ib_connection.py
import threading
import time
from ibapi.client import EClient
from ibapi.wrapper import EWrapper
from ibapi.common import TickAttribLast
from datetime import datetime
import yaml

class IBConnection(EWrapper, EClient):
    """
    Manages IB connection, event callbacks, partial fill logic, and reconnection logic if needed.
    """
    def __init__(self, aggregator=None, config=None):
        EClient.__init__(self, self)
        self.aggregator = aggregator
        self.config = config or {}
        self.nextOrderId = None

        # For partial fill simulation or real fills
        self.fills = []  # List of fill events if we ever track them

        # Connection / reconnection
        self.host = self.config.get("ib", {}).get("host", "127.0.0.1")
        self.port = self.config.get("ib", {}).get("port", 7497)
        self.clientId = self.config.get("ib", {}).get("clientId", 123)
        self.connected_flag = False

    def connect_and_run(self):
        """
        Establish connection to IB, start the message loop in a separate thread.
        """
        if not self.connected_flag:
            super().connect(self.host, self.port, self.clientId)
            self.run_thread = threading.Thread(target=self.run, daemon=True)
            self.run_thread.start()
            self.connected_flag = True
        else:
            print("[INFO] Already connected.")

    def error(self, reqId, errorCode, errorString):
        # Handle disconnections or errors
        if errorCode in (1100, 1300, 2110):  # e.g., "Connectivity lost"
            print(f"[ERROR] Connection issue: {errorString} (code={errorCode})")
            self.connected_flag = False
            # Implement reconnection logic if desired
        else:
            print(f"[ERROR] ReqId: {reqId}, Code: {errorCode}, Msg: {errorString}")

    def nextValidId(self, orderId: int):
        """
        IB will send the next valid order ID after connection.
        """
        self.nextOrderId = orderId

    def tickByTickAllLast(self, reqId: int, tickType: int, time_: int,
                          price: float, size: int, tickAttribLast: TickAttribLast,
                          exchange: str, specialConditions: str):
        trade_time = datetime.fromtimestamp(time_)
        # Pass the trade to aggregator for building bars
        if self.aggregator:
            self.aggregator.on_new_trade(trade_time, price, size)

    # You can add more callbacks here (e.g. partial fill logic for real trades, orderStatus, etc.)
Highlights:

Extends EClient and EWrapper.
Maintains a background thread to run the IB client loop.
Includes placeholders for reconnection logic and partial fill handling.
Provides the tickByTickAllLast callback to forward trades to aggregator.
4. data/data_loader.py
python
Copy
Edit
# data/data_loader.py
import pandas as pd

def load_historical_data(csv_path):
    """
    (Optional) Loads historical data from a CSV file for backtesting or analysis.
    Expected columns: time, open, high, low, close, volume
    """
    df = pd.read_csv(csv_path, parse_dates=["time"])
    df.sort_values("time", inplace=True)
    df.reset_index(drop=True, inplace=True)
    return df
Purpose: Load historical data from CSV for testing strategies offline.
Usage: Called in backtest mode (if you integrate that feature).

5. data/data_preprocessor.py
python
Copy
Edit
# data/data_preprocessor.py
import pandas as pd

def preprocess_data(df):
    """
    (Optional) Cleans or transforms data if needed (e.g., drop NaNs, resample).
    """
    # Example: Drop rows with any missing fields
    df = df.dropna()
    # ... other cleaning steps ...
    return df
Purpose: Clean or transform historical data before running indicators or a backtest.

6. execution/limit_order_execution_logic.py
python
Copy
Edit
# execution/limit_order_execution_logic.py

def place_limit_order_simulation(price, quantity):
    """
    Simulate placing a limit order at 'price' for 'quantity' contracts.
    In this logging-only version, we simply return a hypothetical fill.
    """
    # For a real IB approach, you'd call ib.placeOrder(...) with a Limit order.
    # Here, we simulate immediate fill at the limit price:
    return {
        "order_type": "LIMIT",
        "status": "Filled",
        "filled_price": price,
        "filled_quantity": quantity
    }
7. execution/long_order_execution_logic.py
python
Copy
Edit
# execution/long_order_execution_logic.py

def place_long_order_simulation(market_price, quantity):
    """
    Simulate going long at a given market price.
    Here we mimic a market order fill or near instant fill.
    """
    # Real IB call would be something like marketOrder("BUY", quantity).
    return {
        "order_type": "LONG_MARKET",
        "status": "Filled",
        "filled_price": market_price,
        "filled_quantity": quantity
    }
8. execution/short_order_execution_logic.py
python
Copy
Edit
# execution/short_order_execution_logic.py

def place_short_order_simulation(market_price, quantity):
    """
    Simulate shorting at a given market price.
    """
    return {
        "order_type": "SHORT_MARKET",
        "status": "Filled",
        "filled_price": market_price,
        "filled_quantity": quantity
    }
9. execution/stop_loss_order_execution_logic.py
python
Copy
Edit
# execution/stop_loss_order_execution_logic.py

def place_stop_loss_order_simulation(stop_price, quantity):
    """
    Simulate placing a stop-loss order.
    For real usage, you'd place a STOP order with IB at 'stop_price'.
    """
    return {
        "order_type": "STOP",
        "status": "Pending",
        "stop_price": stop_price,
        "quantity": quantity
    }
10. execution/trade_execution_logic.py
python
Copy
Edit
# execution/trade_execution_logic.py
from .long_order_execution_logic import place_long_order_simulation
from .short_order_execution_logic import place_short_order_simulation
from .limit_order_execution_logic import place_limit_order_simulation
from .stop_loss_order_execution_logic import place_stop_loss_order_simulation

def execute_trade_simulation(trade_side, entry_price, quantity, stop_price=None, limit_price=None):
    """
    Orchestrates a simple simulation of trade entry + optional SL/TP orders.
    """
    if trade_side.lower() == "long":
        entry_result = place_long_order_simulation(entry_price, quantity)
    else:
        entry_result = place_short_order_simulation(entry_price, quantity)

    stop_result = None
    limit_result = None

    if stop_price:
        stop_result = place_stop_loss_order_simulation(stop_price, quantity)
    if limit_price:
        limit_result = place_limit_order_simulation(limit_price, quantity)

    return {
        "entry": entry_result,
        "stop": stop_result,
        "limit": limit_result
    }
Note: In a real trading environment, these methods would place actual IB orders, handle partial fills, OCA groups, etc.

11. indicators/indicator_logic_EMA.py
python
Copy
Edit
# indicators/indicator_logic_EMA.py
import pandas as pd

def compute_ema(series, period):
    """
    Returns the Exponential Moving Average for a pandas Series.
    By default, Pandas provides a handy method 'ewm'.
    """
    return series.ewm(span=period, adjust=False).mean()

def compute_ema_crossover(df, ema_short=9, ema_long=21):
    """
    Given a DataFrame with 'close' column,
    returns two new columns: 'ema_short', 'ema_long', and a boolean 'bullish_crossover'.
    """
    df[f"EMA_{ema_short}"] = compute_ema(df["close"], ema_short)
    df[f"EMA_{ema_long}"] = compute_ema(df["close"], ema_long)

    # A bullish crossover occurs when EMA_short crosses above EMA_long
    df["bullish_crossover"] = df[f"EMA_{ema_short}"] > df[f"EMA_{ema_long}"]
    return df
12. indicators/indicator_logic_RSI.py
python
Copy
Edit
# indicators/indicator_logic_RSI.py
import pandas as pd

def compute_rsi(series, period=14):
    """
    Compute RSI for a pandas Series using standard formula.
    """
    delta = series.diff(1)
    gain = (delta.where(delta > 0, 0)).ewm(alpha=1/period).mean()
    loss = (-delta.where(delta < 0, 0)).ewm(alpha=1/period).mean()

    rs = gain / loss
    rsi = 100 - (100 / (1 + rs))
    return rsi

def add_rsi_column(df, period=9):
    """
    Adds a 'rsi' column to the DataFrame based on 'close' prices.
    """
    df["rsi"] = compute_rsi(df["close"], period=period)
    return df
13. indicators/indicator_logic_ATR.py
python
Copy
Edit
# indicators/indicator_logic_ATR.py
def compute_atr(df, period=14):
    """
    Compute the Average True Range (ATR) over 'period' bars.
    Expects columns: 'high', 'low', 'close'.
    """
    df["hl"] = df["high"] - df["low"]
    df["hc"] = (df["high"] - df["close"].shift(1)).abs()
    df["lc"] = (df["low"] - df["close"].shift(1)).abs()

    df["tr"] = df[["hl", "hc", "lc"]].max(axis=1)
    df["atr"] = df["tr"].rolling(period).mean()

    return df
(For more precision, you might use Wilder’s smoothing, but this suffices as an example.)

14. indicators/indicator_logic_VWAP.py
python
Copy
Edit
# indicators/indicator_logic_VWAP.py
def compute_vwap(df):
    """
    Compute VWAP (Volume Weighted Average Price) over the entire session.
    For a more accurate rolling VWAP, adjust the approach accordingly.
    Expects columns: 'close', 'volume'.
    """
    df["cum_price_volume"] = (df["close"] * df["volume"]).cumsum()
    df["cum_volume"] = df["volume"].cumsum()
    df["vwap"] = df["cum_price_volume"] / df["cum_volume"]
    return df
15. managers/dynamic_stop_loss.py
python
Copy
Edit
# managers/dynamic_stop_loss.py

def adjust_stop_loss(current_stop, current_price, atr_value, multiplier=1.5):
    """
    Example of adjusting stop loss based on ATR or trailing logic.
    For a long trade, you might move stop up if price moves in your favor.
    """
    # Very simple approach: if price has gone up by X * ATR, raise the stop by the same amount.
    potential_new_stop = current_price - (atr_value * multiplier)
    return max(current_stop, potential_new_stop)  # Avoid lowering the stop
16. managers/entry_manager.py
python
Copy
Edit
# managers/entry_manager.py

def check_long_entry_signals(row, config):
    """
    Check bullish conditions: EMA(9) > EMA(21), RSI > 50, volume filter, etc.
    row is the last bar's data (a dictionary or row from DataFrame).
    config is your loaded config dict.
    """
    short_ema = row.get("EMA_9", None)
    long_ema  = row.get("EMA_21", None)
    rsi       = row.get("rsi", None)
    vwap      = row.get("vwap", None)
    close     = row.get("close", 0)
    volume    = row.get("volume", 0)

    # Relative Volume example (would need average volume reference)
    # Suppose you store a rolling avg volume in row["avg_vol"]?
    rvol_threshold = config.get("volume", {}).get("rvol_threshold", 1.5)
    current_rvol = row.get("rvol", 1)  # Fake example

    # Basic checks
    if short_ema is None or long_ema is None or rsi is None:
        return False  # Not enough data
    if short_ema <= long_ema:
        return False
    if rsi < 50:
        return False
    if vwap is not None and close < vwap:
        return False
    if current_rvol < rvol_threshold:
        return False

    return True  # If all conditions pass

def check_short_entry_signals(row, config):
    """
    Mirror logic for short trades if desired.
    """
    short_ema = row.get("EMA_9", None)
    long_ema  = row.get("EMA_21", None)
    rsi       = row.get("rsi", None)
    vwap      = row.get("vwap", None)
    close     = row.get("close", 0)
    current_rvol = row.get("rvol", 1)
    rvol_threshold = config.get("volume", {}).get("rvol_threshold", 1.5)

    if short_ema is None or long_ema is None or rsi is None:
        return False
    if short_ema >= long_ema:
        return False
    if rsi > 50:
        return False
    if vwap is not None and close > vwap:
        return False
    if current_rvol < rvol_threshold:
        return False

    return True
17. managers/exit_manager.py
python
Copy
Edit
# managers/exit_manager.py

def check_stop_take_profit(current_price, trade):
    """
    Check if the current_price hits trade's stop-loss or take-profit.
    trade is a dict with keys like: "stop_price", "take_profit_price", "side"
    Return "STOP", "TP", or None if neither is triggered.
    """
    side = trade.get("side", "long")
    stop_price = trade.get("stop_price", None)
    take_profit_price = trade.get("take_profit_price", None)

    if side.lower() == "long":
        if current_price <= stop_price:
            return "STOP"
        if current_price >= take_profit_price:
            return "TP"
    else:  # short
        if current_price >= stop_price:
            return "STOP"
        if current_price <= take_profit_price:
            return "TP"

    return None
18. managers/stop_loss_manager.py
python
Copy
Edit
# managers/stop_loss_manager.py

def update_stop_loss(trade, new_stop):
    """
    Update the trade dictionary with a new stop price if it's better (for a long).
    """
    old_stop = trade.get("stop_price")
    if trade["side"].lower() == "long":
        # For a long trade, a 'better' stop is higher
        trade["stop_price"] = max(old_stop, new_stop)
    else:
        # For a short trade, a 'better' stop is lower
        trade["stop_price"] = min(old_stop, new_stop)
19. managers/take_profit_manager.py
python
Copy
Edit
# managers/take_profit_manager.py

def update_take_profit(trade, new_tp):
    """
    Adjust take-profit for a trade if a trailing logic is used.
    """
    old_tp = trade.get("take_profit_price")
    if trade["side"].lower() == "long":
        # For a long, if you want to trail up the TP
        trade["take_profit_price"] = max(old_tp, new_tp)
    else:
        trade["take_profit_price"] = min(old_tp, new_tp)
20. managers/trade_manager.py
python
Copy
Edit
# managers/trade_manager.py
import time
import os

class TradeManager:
    """
    Coordinates entire trade lifecycle, partial fills, logs, etc.
    """
    def __init__(self, config):
        self.config = config
        self.active_trade = None
        self.trades_log_file = self.config.get("logging", {}).get("log_file", "trade_record.text")
        self.max_trades_per_day = self.config.get("max_trades_per_day", 10)
        self.trades_taken = 0

    def can_enter_new_trade(self):
        """
        Check if we can open a new trade (no active trade and hasn't exceeded daily limit).
        """
        if self.active_trade is not None:
            return False
        if self.trades_taken >= self.max_trades_per_day:
            return False
        return True

    def open_trade(self, side, entry_price, stop_price, take_profit_price, quantity=1):
        """
        Sets self.active_trade and logs the entry. 
        """
        self.active_trade = {
            "side": side,
            "entry_price": entry_price,
            "stop_price": stop_price,
            "take_profit_price": take_profit_price,
            "quantity": quantity,
            "status": "OPEN",
            "open_time": time.time(),
        }
        self.trades_taken += 1
        self.log_trade_event("OPEN")

    def close_trade(self, exit_reason, exit_price):
        """
        Closes an active trade, logs outcome, then resets self.active_trade.
        """
        if self.active_trade is None:
            return

        self.active_trade["status"] = "CLOSED"
        self.active_trade["exit_reason"] = exit_reason
        self.active_trade["exit_price"] = exit_price
        self.active_trade["close_time"] = time.time()

        # Calculate P/L for a long or short
        if self.active_trade["side"].lower() == "long":
            pl = (exit_price - self.active_trade["entry_price"]) * self.active_trade["quantity"]
        else:
            pl = (self.active_trade["entry_price"] - exit_price) * self.active_trade["quantity"]

        self.active_trade["pnl"] = pl

        self.log_trade_event("CLOSE")
        self.active_trade = None

    def log_trade_event(self, event_type):
        """
        Writes trade info to 'trade_record.text' or specified log file.
        """
        if not self.active_trade:
            return

        with open(self.trades_log_file, "a") as f:
            f.write(f"{event_type} | {self.active_trade}\n")

    def get_active_trade(self):
        return self.active_trade
21. utils/helpers.py
python
Copy
Edit
# utils/helpers.py
import math
from datetime import datetime

def format_timestamp(ts=None):
    """
    Returns a nicely formatted timestamp string.
    """
    if not ts:
        ts = datetime.now()
    return ts.strftime("%Y-%m-%d %H:%M:%S")

def calculate_rvol(current_volume, avg_volume):
    """
    Relative Volume = current_volume / avg_volume
    """
    if avg_volume == 0:
        return 1.0
    return current_volume / avg_volume
22. aggregator.py
python
Copy
Edit
# aggregator.py
from datetime import datetime, timedelta
import math

def align_to_bar_boundary(dt, bar_length=60):
    """
    Anchors dt to multiples of bar_length seconds.
    """
    second_of_minute = dt.second
    remainder = second_of_minute % bar_length
    anchored_second = second_of_minute - remainder
    return dt.replace(second=anchored_second, microsecond=0)

class TradeAggregator:
    """
    Aggregates raw trades (timestamp, price, size) into bars of 'bar_length' seconds.
    """
    def __init__(self, bar_length=60, on_bar_close=None):
        self.bar_length = bar_length
        self.delta = timedelta(seconds=bar_length)
        self.bar_start = None
        self.on_bar_close = on_bar_close  # Callback to process the bar once it closes

        # Bar Data
        self.open_price = None
        self.high_price = None
        self.low_price = None
        self.close_price = None
        self.volume = 0

    def on_new_trade(self, trade_time, price, size):
        """
        Update or finalize bars based on the incoming trade.
        """
        if self.bar_start is None:
            candidate_start = align_to_bar_boundary(trade_time, self.bar_length)
            while trade_time >= candidate_start + self.delta:
                candidate_start += self.delta
            self.bar_start = candidate_start

        # If trade_time is beyond this bar, finalize
        while trade_time >= self.bar_start + self.delta:
            self.finalize_bar()
            self.bar_start += self.delta

        self.update_current_bar(price, size)

    def update_current_bar(self, price, size):
        if self.open_price is None:
            self.open_price = price
            self.high_price = price
            self.low_price = price
            self.close_price = price
            self.volume = size
        else:
            self.close_price = price
            self.high_price = max(self.high_price, price)
            self.low_price = min(self.low_price, price)
            self.volume += size

    def finalize_bar(self):
        """
        Package up the bar info and send it to on_bar_close callback.
        Then reset for the next bar.
        """
        if self.open_price is not None:
            bar_info = {
                "time": self.bar_start,
                "open": self.open_price,
                "high": self.high_price,
                "low": self.low_price,
                "close": self.close_price,
                "volume": self.volume,
            }

            if self.on_bar_close:
                self.on_bar_close(bar_info)

        # Reset bar data
        self.open_price = None
        self.high_price = None
        self.low_price = None
        self.close_price = None
        self.volume = 0

    def force_finalize(self):
        """
        In case you want to finalize at forced intervals or on shutdown.
        """
        if self.open_price is not None:
            self.finalize_bar()
23. list_files.py
python
Copy
Edit
# list_files.py
import os

def list_all_files(directory="."):
    """
    Lists all files in a given directory.
    """
    return os.listdir(directory)

if __name__ == "__main__":
    for f in list_all_files():
        print(f)
Purpose: Utility to enumerate files/logs. Not critical to trading logic, but can help manage data.

24. main.py
python
Copy
Edit
# main.py
import yaml
import time
import sys
import os
from connection.ib_connection import IBConnection
from connection.contract_definition import create_mes_contract
from aggregator import TradeAggregator
from managers.trade_manager import TradeManager
from managers.entry_manager import check_long_entry_signals, check_short_entry_signals
from managers.exit_manager import check_stop_take_profit
from indicators.indicator_logic_EMA import compute_ema_crossover
from indicators.indicator_logic_RSI import add_rsi_column
from indicators.indicator_logic_ATR import compute_atr
from indicators.indicator_logic_VWAP import compute_vwap
import pandas as pd

def load_config(path="config.yaml"):
    with open(path, "r") as f:
        return yaml.safe_load(f)

class BotApp:
    def __init__(self, config_path="config.yaml"):
        self.config = load_config(config_path)
        self.df = pd.DataFrame()  # We'll accumulate bars here
        self.trade_manager = TradeManager(self.config)
        self.bar_length_seconds = self.config.get("bar_length_seconds", 60)

        self.aggregator = TradeAggregator(
            bar_length=self.bar_length_seconds,
            on_bar_close=self.on_bar_close
        )
        self.ib = IBConnection(aggregator=self.aggregator, config=self.config)

        self.contract = create_mes_contract(config_path)

    def on_bar_close(self, bar_info):
        """
        Callback each time a bar is finalized in aggregator.
        We update self.df, compute indicators, check entry/exit signals, etc.
        """
        # Convert bar_info into a single-row DataFrame, then append
        bar_df = pd.DataFrame([bar_info])
        self.df = pd.concat([self.df, bar_df], ignore_index=True)

        # Compute indicators on the entire DataFrame or the last portion
        self.compute_indicators()

        # The new bar is the last row
        latest_bar = self.df.iloc[-1].to_dict()

        self.handle_exit(latest_bar)
        self.handle_entry(latest_bar)

    def compute_indicators(self):
        # We’ll just compute for the entire dataset for simplicity
        if len(self.df) < 2:
            return

        # EMA cross
        self.df = compute_ema_crossover(self.df, ema_short=self.config["indicators"]["ema_periods"][0],
                                              ema_long=self.config["indicators"]["ema_periods"][1])
        # RSI
        self.df = add_rsi_column(self.df, period=self.config["indicators"]["rsi_period"])

        # ATR
        self.df = compute_atr(self.df, period=self.config["indicators"]["atr_period"])

        # VWAP (if configured)
        if self.config["indicators"].get("use_vwap", False):
            self.df = compute_vwap(self.df)

        # Example: You could also track rolling avg volume for RVOL in df

    def handle_entry(self, latest_bar):
        # If we already have an active trade, do nothing
        if not self.trade_manager.can_enter_new_trade():
            return

        # Check bullish or bearish signals
        can_go_long = check_long_entry_signals(latest_bar, self.config)
        # For a short strategy, can_go_short = check_short_entry_signals(latest_bar, self.config)

        # If bullish
        if can_go_long:
            entry_price = latest_bar["close"]
            # ATR-based stop
            atr_value = latest_bar.get("atr", 1.0)
            multiplier = self.config["risk"]["atr_stop_multiplier"]
            stop_price = entry_price - (atr_value * multiplier)
            # Fixed scalp target
            tp_price = entry_price + self.config["risk"]["scalp_target_points"]

            self.trade_manager.open_trade("long", entry_price, stop_price, tp_price, quantity=1)

    def handle_exit(self, latest_bar):
        active_trade = self.trade_manager.get_active_trade()
        if not active_trade:
            return

        # Check if we hit stop or TP
        exit_signal = check_stop_take_profit(latest_bar["close"], active_trade)
        if exit_signal == "STOP":
            self.trade_manager.close_trade("STOP", latest_bar["close"])
        elif exit_signal == "TP":
            self.trade_manager.close_trade("TP", latest_bar["close"])

    def run(self):
        """
        Connect to IB, request tick data, run indefinitely.
        """
        self.ib.connect_and_run()
        # Request tick-by-tick data
        self.ib.reqTickByTickData(
            reqId=1,
            contract=self.contract,
            tickType="AllLast",
            numberOfTicks=0,
            ignoreSize=False
        )

        print("[INFO] Running bot. Press Ctrl+C to exit.")
        try:
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            print("[INFO] Interrupted by user.")
        finally:
            # Finalize aggregator on shutdown
            self.aggregator.force_finalize()
            self.ib.disconnect()

if __name__ == "__main__":
    app = BotApp("config.yaml")
    app.run()
How main.py Works:

Loads Config from config.yaml.
Initializes an IBConnection (subclass of EClient/EWrapper) + aggregator for 1-minute bars.
Requests tick-by-tick data for the specified contract.
Aggregates trades into bars. Each bar triggers on_bar_close(), which updates indicators and checks entry/exit signals via trade_manager.
Logs trades in trade_record.text.
25. trade_record.text
Initially empty. It will be populated by the TradeManager.log_trade_event() method in real time. For example:

yaml
Copy
Edit
OPEN | {'side': 'long', 'entry_price': 4501.0, 'stop_price': 4499.5, 'take_profit_price': 4504.0, 'quantity': 1, 'status': 'OPEN', 'open_time': 1697594700.9}
CLOSE | {'side': 'long', 'entry_price': 4501.0, 'stop_price': 4499.5, 'take_profit_price': 4504.0, 'quantity': 1, 'status': 'CLOSED', 'open_time': 1697594700.9, 'exit_reason': 'TP', 'exit_price': 4504.0, 'close_time': 1697594720.0, 'pnl': 3.0}
Final Notes
This suite of files represents a conceptual scaffold for an IB-based scalp bot.
In a real-world system you would:
Harden the code against exceptions, disconnections, and partial fills.
Possibly incorporate advanced concurrency or queue-based event handling.
Add a robust way to compute Relative Volume (requires a rolling average of volume).
Use real order placement logic in execution/… if you want to actually trade.
Expand or refine the indicators (e.g., advanced ATR smoothing, precise VWAP for each new session, etc.).
Implement a strategy for detecting / logging partial fills from IB’s order callbacks (e.g., execDetails() in EWrapper) if going live.
With this complete skeleton, you have a working example showing how all the pieces can fit together under your specified directory structure. Adjust or refine each module to match your exact trading strategy requirements, and test thoroughly in a paper trading environment before risking real capital.
