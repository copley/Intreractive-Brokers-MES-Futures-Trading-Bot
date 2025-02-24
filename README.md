# MES Trading & Backtesting Application

Welcome to the **MES** (Micro E-mini S&P) trading and backtesting application! This project demonstrates how to connect to Interactive Brokers (IB) to retrieve account/position data, manage live trades with advanced order logic, backtest strategies using CSV-based historical data, and compute trade statistics.

Below is an extensive overview of the project structure, key scripts, and how to use them.

---

## Table of Contents

1. [Overview](#overview)  
2. [Directory Structure](#directory-structure)  
3. [Setup & Installation](#setup--installation)  
4. [Configuration (config.yaml)](#configuration-configyaml)  
5. [Key Scripts](#key-scripts)  
   1. [account_and_positions.py](#1-account_and_positionspy)  
   2. [backtest.py](#2-backtestpy)  
   3. [compute_trade_stats.py](#3-compute_trade_statspy)  
   4. [current_positions.py](#4-current_positionspy)  
   5. [download_historical_data.py](#5-download_historical_datapy)  
   6. [ensure_init_py.py](#6-ensure_init_pypy)  
   7. [expand_and_run.py](#7-expand_and_runpy)  
   8. [export_python_files.py](#8-export_python_filespy)  
   9. [find_highest_win_rate.py](#9-find_highest_win_ratepy)  
   10. [get_contract_details.py](#10-get_contract_detailspy)  
   11. [get_trade_results_from_1000_files.py](#11-get_trade_results_from_1000_filespy)  
   12. [live_mes_data_downloader.py](#12-live_mes_data_downloaderpy)  
   13. [main.py](#13-mainpy)  
   14. [parameter_tester.py / parameter_tester2.py](#14-parameter_testerpy--parameter_tester2py)  
   15. [trade_history.py](#15-trade_historypy)  
   16. [XINA50_live_date_terminal_print.py](#16-xina50_live_date_terminal_printpy)  
6. [Additional Files & Directories](#additional-files--directories)  
7. [Backtesting with Tests/ Scripts](#backtesting-with-tests-scripts)  
8. [Utilities & Modules](#utilities--modules)  
9. [Examples & Usage](#examples--usage)  
10. [Disclaimer](#disclaimer)

---

## Overview

This MES project provides examples and tooling for:

- **Connecting to Interactive Brokers (IB)** via the Python `ibapi` and/or `ib_insync`.
- **Retrieving account balances**, open positions, trade execution history, and more.
- **Backtesting** custom trading strategies (EMA/RSI/ATR-based) using CSV files.
- **Computing trade statistics** (win rate, P/L, drawdown, etc.).
- **Live trading** with automatic stop-loss, take-profit, dynamic trailing stops, etc.
- **Batch parameter testing** over many CSV or config combos to find optimal strategy parameters.

Everything is configurable through a `config.yaml` file (host/port for IB, contract details, strategy thresholds). Scripts can run in local or remote server environments.

---

## Directory Structure

Below is a high-level view of the repository:

```java
MES/
├── account_and_positions.py
├── backtest.py
├── compute_trade_stats.py
├── current_positions.py
├── download_historical_data.py
├── ensure_init_py.py
├── expand_and_run.py
├── export_python_files.py
├── find_highest_win_rate.py
├── get_contract_details.py
├── get_trade_results_from_1000_files.py
├── live_mes_data_downloader.py
├── main.py
├── parameter_tester.py
├── parameter_tester2.py
├── trade_history.py
├── XINA50_live_date_terminal_print.py
├── config.yaml                  <- Main YAML config for IB host/port, contract, strategy settings
├── connection/                  <- Connection & contract creation logic (ib_connection.py, contract_definition.py)
├── data/                        <- Data loading / preprocessing modules
├── execution/                   <- Execution logic (limit, market, stop-loss, trade_execution_logic)
├── indicators/                  <- Indicator calculations (EMA, RSI, ATR, VWAP)
├── managers/                    <- Classes that manage entries, exits, stops, take-profits, trade logging
├── utils/                       <- Utilities (helpers, aggregator, listing files, etc.)
└── Tests/                       <- Example custom strategies & backtest scripts (Backtrader, etc.)
Setup & Installation
1. Python Environment
Make sure you have Python 3.7+ installed. It’s strongly recommended to use a virtual environment (e.g., venv or conda).

bash
Copy
# Example: create and activate a virtual environment
python3 -m venv venv
source venv/bin/activate  # on Windows: venv\Scripts\activate
2. Install Dependencies
Install required packages, such as:

ibapi (official API from Interactive Brokers).
ib_insync (optional but recommended for simpler IB usage).
pandas.
numpy.
pyyaml for config files.
rich for fancy console output in some scripts.
backtrader for advanced backtesting (in Tests folder).
A typical install (if you use many of these scripts) might be:

bash
Copy
pip install ibapi ib-insync pandas numpy pyyaml rich backtrader
3. Interactive Brokers Setup
Make sure you have TWS (Trader Workstation) or IB Gateway running.
Enable API connections on the configured host & port (e.g. 127.0.0.1:7497 or 4001).
In TWS, check Global Configuration → API → Settings → “Enable ActiveX and Socket Clients”, etc.
Ensure your account has paper trading or real trading enabled for advanced scripts.
Configuration (config.yaml)
Nearly all scripts read from config.yaml (or a custom file) containing:

yaml
Copy
interactive_brokers:
  host: "127.0.0.1"
  port: 7496
  client_id: 1

contract:
  symbol: "MES"
  sec_type: "FUT"
  exchange: "CME"
  currency: "USD"
  lastTradeDateOrContractMonth: "20250321"
  localSymbol: "MESH5"
  multiplier: "5"

trading:
  stop_loss_pct: 0.005
  take_profit_pct: 0.01

strategy:
  RSI_overbought: 70
  RSI_oversold: 30

logging:
  level: "INFO"
  file: null  # or "my_log.log"

data:
  bar_size: "1 min"
Feel free to adjust any parameters (host/port, contract, strategy thresholds, log level, etc.). Some scripts allow you to specify --config <path> to override the default config.yaml.

Key Scripts
Below is a summary of main Python files and their usage.

1) account_and_positions.py
Purpose: Connects to IB, downloads current account balances/values and open positions.
Features:
Prints a table of positions with average cost, real-time last price, computed PnL.
Prints account values (cash balance, net liquidity, etc.).
Usage:
bash
Copy
python account_and_positions.py
Make sure your IB Gateway or TWS is running at the configured port (e.g., 4001).
2) backtest.py
Purpose: Runs a backtest using a CSV file of historical data. Demonstrates:
Loading & sorting data from CSV
Computing indicators (EMA, RSI, ATR)
Managing trades via TradeManager-like classes in a “mock” environment
Usage:
bash
Copy
python backtest.py
By default, it looks for "your_csv_file.csv" (you may change that to any CSV path).
It logs trades in trade_log.csv and prints results.
You can combine it with compute_trade_stats.py to get a final trade stats summary.
3) compute_trade_stats.py
Purpose: Reads a CSV of trades (trade_log.csv or custom) and computes:
Win rate, total trades, average P/L, largest win/loss, profit factor, etc.
Running equity curve, max drawdown, final net profit.
Usage:
bash
Copy
python compute_trade_stats.py -- (optional arguments)
Or simply:
bash
Copy
python compute_trade_stats.py
which assumes a file named trade_log.csv.
4) current_positions.py
Purpose: A simple example that loads positions from a CSV (hard-coded) and uses rich to display them in a dynamic table.
Mostly an example of how you might update a UI with positions in real-time, though it’s just CSV data here.
Usage:
bash
Copy
python current_positions.py
Press Ctrl+C to exit its loop.
5) download_historical_data.py
Purpose: Demonstrates chunked historical data download from IB in parallel threads.
Features:
Splits your total requested days (e.g. 30) into multiple chunks (e.g. 5–10 days each).
Spawns multiple threads to download data concurrently.
Aggregates results, sorts them by date, writes to CSV.
Usage:
Edit config.yaml with symbol, sec_type, etc.
Update total_days in the script as needed.
Run:
bash
Copy
python download_historical_data.py
Final bars will appear in something like bars_data_YYYYMMDD_HHMMSS.csv.
6) ensure_init_py.py
Purpose: Recursively ensures every directory has an __init__.py. Handy if you’re making them into Python modules.
Usage:
bash
Copy
python ensure_init_py.py
It will create empty __init__.py files where needed.
7) expand_and_run.py
Purpose: Expands glob patterns of CSV files (e.g. trade_log*.csv) and processes them.
Example usage might compute total P/L for each file, then find the top 10.
Usage:
bash
Copy
python expand_and_run.py "trade_log*.csv"
Results are stored in top_10_results.txt.
8) export_python_files.py
Purpose: Walks through the directory, collects all .py source files, and concatenates them into output.txt.
Usage:
bash
Copy
python export_python_files.py
Great for archiving code or sharing a single file.
9) find_highest_win_rate.py
Purpose: Scans a log file for lines containing Win Rate: X% to find top 10 lines with the highest win rate.
Usage:
bash
Copy
python find_highest_win_rate.py your_log_file.txt
Prints top 10 lines where Win Rate: <num>% is found.
10) get_contract_details.py
Purpose: Connects to IB, fetches all contract variations (e.g. different expiry months) for a given symbol, prints them, and requests market data.
Usage:
bash
Copy
python get_contract_details.py
In code, the symbol is set to 'MHNG' (or 'MES')—adjust as needed.
11) get_trade_results_from_1000_files.py
Purpose: Another bulk script that loops over many CSV files (like trade_log_*.csv), computing stats via compute_trade_stats and sorting the best results.
Usage:
bash
Copy
python get_trade_results_from_1000_files.py trade_log_*.csv
12) live_mes_data_downloader.py
Purpose: Live data script using IB’s real-time 5s bars for MES.
Features:
Subscribes to real-time bars and logs them to a CSV file (live_bars.csv).
Tries to reconnect if IB goes offline.
Usage:
bash
Copy
python live_mes_data_downloader.py
Watch live_bars.csv populate with new bars.
13) main.py
Purpose: A unified “entry-point” script that can run either:
Live trading mode (aggregator logic, placing real trades).
Historical backtest mode (by specifying --test and a CSV file).
Usage:
bash
Copy
# Backtest mode:
python main.py --test --data your_csv_file.csv --trade-log-file my_trades.csv

# Live mode:
python main.py
By default, it loads config.yaml. Use --config <path> to override.
14) parameter_tester.py / parameter_tester2.py
Purpose: Demonstrate batch parameter testing:
Vary stop-loss, take-profit, RSI thresholds, etc.
Write temporary YAML config, run a backtest, capture results.
Output consolidated results to parameter_test_results.csv.
Usage:
bash
Copy
python parameter_tester.py --enable-parameter-testing --num-workers 5
or
bash
Copy
python parameter_tester2.py --enable-parameter-testing
Ensure you have a backtest environment set up and that main.py can handle --test properly.
15) trade_history.py
Purpose: Requests past 6 months of trades from IB using the ExecDetails endpoint.
Usage:
bash
Copy
python trade_history.py
It prints all the trades in a table to stdout.
16) XINA50_live_date_terminal_print.py
Purpose: Subscribes to IB tick-by-tick data for a XINA50 futures contract, aggregates trades into 30-second bars, and prints them in real-time.
Usage:
bash
Copy
python XINA50_live_date_terminal_print.py
Modify contract details (symbol, localSymbol, expiry) for your instrument.
Additional Files & Directories
__init__.py files in each folder help keep them recognized as Python packages.
.git/ folder is your Git repository—generally hidden.
Backtesting with Tests/ Scripts
Inside the Tests/ folder, you will find advanced or specialized examples:

MES_EMA_RSI_ATR_Trading_Strategy.py
A direct script that uses a custom approach (pandas-based or IB-based) to run a strategy on historical bars. Logs results to trade_results.csv.

opening_breakout_strategy.py
An example strategy using Backtrader with a session-based opening range breakout logic.

How to use them:

Install Backtrader if you haven’t (pip install backtrader).
Provide a CSV data feed or direct broker feed.
Run the script:
bash
Copy
python opening_breakout_strategy.py
or
bash
Copy
python MES_EMA_RSI_ATR_Trading_Strategy.py
Utilities & Modules
connection/
ib_connection.py: Manages a combined EClient/EWrapper (IBApi) to connect to TWS or IB Gateway, place orders, and handle events in a separate thread.
contract_definition.py: Utility to create a valid IB contract object from simple parameters (symbol, exchange, etc.).
data/
data_loader.py: Downloads or fetches historical data (if live connection is available).
data_preprocessor.py: Basic transformations like sorting, cleaning, etc.
execution/
trade_execution_logic.py: Single class that unifies buy/short/exit signals into actual IB orders.
long_order_execution_logic.py, short_order_execution_logic.py, limit_order_execution_logic.py, stop_loss_order_execution_logic.py: Specialized functions for each order type.
indicators/
indicator_logic_EMA.py, indicator_logic_RSI.py, indicator_logic_ATR.py, indicator_logic_VWAP.py:
Straightforward indicator computations using pandas or list-based approach.
managers/
entry_manager.py: Decides when to enter trades (based on RSI oversold/overbought, crossing EMAs, etc.).
exit_manager.py: Decides when to exit trades (besides stops/targets).
dynamic_stop_loss.py: Example trailing stop logic.
stop_loss_manager.py, take_profit_manager.py: Responsible for computing or updating stop-loss / take-profit levels.
trade_manager.py: Central orchestrator for a single open position, controlling the entire lifecycle (entry, exit, logging to CSV).
utils/
helpers.py: Loads config, sets up logging, etc.
aggregator.py: Example aggregator for real-time bar usage in a live environment, hooking up the managers and TradeExecutor.
list_files.py: A script to recursively list all files in the repository.
Examples & Usage
Below are some typical commands or workflows:

View Account & Positions

bash
Copy
python account_and_positions.py
Displays your account code, balances, open positions, real-time PnL.

Backtest a Strategy

Prepare a CSV with columns [time, open, high, low, close, volume].
Run:
bash
Copy
python backtest.py
See trade logs in trade_log.csv.
Analyze results:
bash
Copy
python compute_trade_stats.py
Download Historical Data

bash
Copy
python download_historical_data.py
Adjust total_days, chunk size, bar_size, etc. in the script or config.

Live 5-Second Bars

bash
Copy
python live_mes_data_downloader.py
Writes bars to live_bars.csv. Automatic reconnect logic included.

Main Aggregator

For a backtest:
bash
Copy
python main.py --test --data your_csv_file.csv --trade-log-file out_trades.csv
For live:
bash
Copy
python main.py
Parameter Testing

bash
Copy
python parameter_tester.py --enable-parameter-testing --num-workers 4
Iterates multiple parameter combos, spawns processes, collects results in parameter_test_results.csv.

Disclaimer
This codebase is for educational and demonstration purposes. Real trading in futures or any other markets involves substantial risk. This repository does not provide financial advice. Always test thoroughly in a paper trading environment before using real funds. The maintainers/authors are not responsible for losses or damages.

Contributions & Further Reading

Feel free to fork, modify, or open issues/pull requests.
Refer to Interactive Brokers API Docs and ib_insync Documentation for more usage details.
If you use Backtrader, see the Tests/ folder scripts for advanced integration examples.
Copy
