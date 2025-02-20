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
    """

    # --------------------------------------------------------------------
    # 1. Parse command-line arguments
    # --------------------------------------------------------------------
    parser = argparse.ArgumentParser(description="Run either live or historical backtest mode.")
    parser.add_argument("--test", action="store_true",
                        help="Run in historical/backtest mode using CSV data")
    parser.add_argument("--data", type=str, default=None,
                        help="Path to the CSV file for backtesting")
    parser.add_argument("--config", type=str, default=None,
                        help="Optional YAML config file path (for parameter testing or custom config)")
    args = parser.parse_args()

    # --------------------------------------------------------------------
    # 2. Load config
    # --------------------------------------------------------------------
    # If --config is provided, load that file. Otherwise, fall back to 'config.yaml'
    config = None
    if args.config:
        # The user passed --config <filename>. We'll try to load it
        if not os.path.exists(args.config):
            print(f"[ERROR] The specified config file does not exist: {args.config}", file=sys.stderr)
            sys.exit(1)
        print(f"[INFO] Loading custom config from {args.config}")
        with open(args.config, "r") as f:
            config = yaml.safe_load(f)
    else:
        # Fallback to normal config.yaml
        config = helpers.load_config("config.yaml")
        if not config:
            raise SystemExit("Failed to load configuration from config.yaml. Exiting.")

    # --------------------------------------------------------------------
    # 3. Backtest Mode vs. Live Mode
    # --------------------------------------------------------------------
    if args.test:
        # -----------------------------
        # Run Historical Backtest Mode
        # -----------------------------
        if not args.data:
            print("ERROR: You must supply a CSV file via --data when using --test", file=sys.stderr)
            sys.exit(1)

        # Setup logging for test mode (to console)
        logging.basicConfig(
            level=logging.INFO,
            format="%(asctime)s [%(levelname)s] %(message)s"
        )
        print(f"[INFO] Starting historical test mode with CSV: {args.data}")

        # Create backtester
        backtester = Backtester(csv_file=args.data)

        # Overwrite or merge config here if you want the backtester to see the new params:
        backtester.config = config  # This ensures the updated parameters are used

        # Run the backtest
        backtester.run_backtest()  # logs trades to trade_log.csv

        # Compute stats
        compute_trade_stats(csv_path="trade_log.csv", initial_capital=10000.0)

    else:
        # -----------------------------
        # Run Normal Live Trading Mode
        # -----------------------------
        log_cfg = config.get("logging", {})
        helpers.setup_logging(
            level=log_cfg.get("level", "INFO"),
            log_file=log_cfg.get("file", None)
        )

        logging.info("Launching live trading mode...")

        # Create aggregator with loaded config
        bot = Aggregator(config)
        bot.run()

        logging.info("Live trading finished.")


if __name__ == "__main__":
    main()
