#!/usr/bin/env python3
import argparse
import logging
import sys
import os
import yaml  # for loading the custom config

from utils import helpers
from utils.aggregator import Aggregator
from backtest import Backtester
from compute_trade_stats import compute_trade_stats

def main():
    """
    main.py supports:
      --test          : run historical backtest mode
      --data <path>   : CSV for historical data
      --config <path> : if present, load custom YAML instead of config.yaml
      --trade-log-file <path> : file to store trade log (default: trade_log.csv)
    """

    # --------------------------------------------------------------------
    # 1. Parse command-line arguments
    # --------------------------------------------------------------------
    parser = argparse.ArgumentParser(description="Run either live or historical backtest mode.")
    parser.add_argument("--test", action="store_true",
                        help="Run in historical/backtest mode using CSV data")
    parser.add_argument("--data", type=str, default=None,
                        help="Path to the CSV file for backtesting")
    parser.add_argument("--trade-log-file", type=str, default="trade_log.csv",
                        help="File to store trade log")
    parser.add_argument("--config", type=str, default=None,
                        help="Optional YAML config file path (for parameter testing or custom config)")
    args = parser.parse_args()

    # --------------------------------------------------------------------
    # 2. Load config
    # --------------------------------------------------------------------
    config = None
    if args.config:
        if not os.path.exists(args.config):
            print(f"[ERROR] The specified config file does not exist: {args.config}", file=sys.stderr)
            sys.exit(1)
        print(f"[INFO] Loading custom config from {args.config}")
        with open(args.config, "r") as f:
            config = yaml.safe_load(f)
    else:
        config = helpers.load_config("config.yaml")
        if not config:
            raise SystemExit("Failed to load configuration from config.yaml. Exiting.")

    # --------------------------------------------------------------------
    # 3. Choose mode
    # --------------------------------------------------------------------
    if args.test:
        if not args.data:
            print("ERROR: You must supply a CSV file via --data when using --test", file=sys.stderr)
            sys.exit(1)

        logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
        print(f"[INFO] Starting historical test mode with CSV: {args.data}")

        # Create backtester with the specified CSV and trade log file
        backtester = Backtester(csv_file=args.data, trade_log_file=args.trade_log_file)
        # Overwrite config if needed
        backtester.config = config
        backtester.run_backtest()
        compute_trade_stats(csv_path=args.trade_log_file, initial_capital=10000.0)
    else:
        log_cfg = config.get("logging", {})
        helpers.setup_logging(level=log_cfg.get("level", "INFO"), log_file=log_cfg.get("file", None))
        logging.info("Launching live trading mode...")
        bot = Aggregator(config)
        bot.run()
        logging.info("Live trading finished.")

if __name__ == "__main__":
    main()
