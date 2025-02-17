Simple Scalp Bot Documentation (Updated)
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
