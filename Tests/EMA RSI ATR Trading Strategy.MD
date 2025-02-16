# EMA RSI ATR Trading Strategy

## Overview
This Python script implements a trading strategy based on Exponential Moving Averages (EMA), the Relative Strength Index (RSI), and the Average True Range (ATR). The strategy is designed to trade the Micro E-mini S&P 500 (MES) futures contract. It can run in both live trading and backtesting modes.

## Features
- Uses EMA(9), EMA(21), RSI(9), ATR(9), and Volume for trade decisions.
- Can operate in **live trading mode** using Interactive Brokers (IBAPI) or **backtesting mode** with historical data.
- Logs trades to `trade_log.txt` and saves trade results to `trade_results.csv`.
- Runs on a **1-minute timeframe** and evaluates conditions for entry and exit.

## Requirements
### Python Libraries
Ensure you have the following Python libraries installed:

```bash
pip install ib-insync pandas numpy argparse
```

### Interactive Brokers (IBAPI) Setup
- Ensure the **IB Gateway** or **TWS (Trader Workstation)** is running and configured to accept API connections.
- The script is configured to connect to IB on `192.168.1.77:7496` with `clientId=19`. Update this if needed.

## How to Run

### 1. Live Trading Mode
To run in live mode, where the script connects to Interactive Brokers and subscribes to real-time market data:

```bash
python script.py --live
```

### 2. Backtest Mode with Historical Data
To backtest using a CSV file containing historical market data:

```bash
python script.py --file historical_data.csv
```

### 3. Download Historical Data and Backtest
To download historical data from Interactive Brokers and run a backtest:

```bash
python script.py --duration "5 D"
```

This will download **5 days** of 1-minute bars and execute the strategy on that data.

## Trade Execution Logic
1. **Entry Conditions:**
   - EMA(9) crosses above EMA(21).
   - RSI(9) is above 50.
   - Trade is not currently active.

2. **Exit Conditions:**
   - Price hits **Take Profit (3x ATR)** or **Stop Loss (1.5x ATR)**.

## Output
- **Logs:** Recorded in `trade_log.txt`.
- **Results:** Saved in `trade_results.csv`, including trade details and PnL.

## Notes
- The script is pre-configured for trading MES futures (`MESH5` for March 2025). Adjust contract details as needed.
- Ensure API permissions are enabled in IB Gateway/TWS before running the script in live mode.

## Disclaimer
This script is for educational and experimental purposes only. Trade at your own risk!

