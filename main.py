#!/usr/bin/env python3
import argparse
import logging
import sys

from utils import helpers
from utils.aggregator import Aggregator
from backtest import Backtester

def main():
    # Parse command-line arguments
    parser = argparse.ArgumentParser(description="Run either live or historical backtest mode.")
    parser.add_argument("--test", action="store_true",
                        help="Run in historical/backtest mode using CSV data")
    parser.add_argument("--data", type=str, default=None,
                        help="Path to the CSV file for backtesting")
    args = parser.parse_args()

    if args.test:
        # -----------------------------
        # Run Historical Backtest Mode
        # -----------------------------
        if not args.data:
            print("ERROR: You must supply a CSV file via --data when using --test", file=sys.stderr)
            sys.exit(1)

        # (Optional) Setup logging for test mode
        logging.basicConfig(
            level=logging.INFO,
            format="%(asctime)s [%(levelname)s] %(message)s"
        )
        print(f"[INFO] Starting historical test mode with CSV: {args.data}")

        backtester = Backtester(csv_file=args.data)
        backtester.run_backtest()  # This logs trades to trade_log.csv

        # After backtest, compute trade statistics
        from compute_trade_stats import compute_trade_stats
        compute_trade_stats(
            csv_path="trade_log.csv",
            initial_capital=10000.0
        )

    else:
        # -----------------------------
        # Run Normal Live Trading Mode
        # -----------------------------
        config = helpers.load_config("config.yaml")
        if not config:
            raise SystemExit("Failed to load configuration. Exiting.")

        log_cfg = config.get("logging", {})
        helpers.setup_logging(
            level=log_cfg.get("level", "INFO"),
            log_file=log_cfg.get("file", None)
        )

        logging.info("Launching live trading mode...")
        bot = Aggregator(config)
        bot.run()
        logging.info("Live trading finished.")

if __name__ == "__main__":
    main()
