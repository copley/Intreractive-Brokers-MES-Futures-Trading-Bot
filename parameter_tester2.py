#!/usr/bin/env python3
"""
parameter_tester.py

Runs parameter testing in parallel using multiprocessing.
To prevent accidental use, you must explicitly enable parameter testing by using:
    python3 parameter_tester.py --enable-parameter-testing

Usage:
    python3 parameter_tester.py --enable-parameter-testing [--num-workers 5]

---------------------------------------------------------
Brief Explanation:

1) We build a list of parameter combinations including trading parameters (stop_loss, take_profit, RSI_overbought, RSI_oversold)
   and indicator parameters (EMA_period, RSI_period, ATR_period, VWAP_period).
2) We add a fixed market time window (market_time) to restrict backtesting to the first two hours of the MES futures market open.
3) We spin up a pool of worker processes (default 5) to run backtests in parallel.
4) Each process calls main.py with a temporary config file.
5) Results are collected in a CSV for later analysis.
---------------------------------------------------------
"""

import argparse
import csv
import logging
import os
import subprocess
import tempfile
import yaml
import multiprocessing
import random

def run_single_test(param_tuple):
    (base_config, sl, tp, rsi_ob, rsi_os, ema, rsi_p, atr, vwap, no_disconnect) = param_tuple

    # -- Add a unique trade-log file name here --
    unique_trade_log = f"trade_log_{sl}_{tp}_{rsi_ob}_{rsi_os}_{ema}_{rsi_p}_{atr}_{vwap}.csv"

    # 1) Copy the base config dictionary, etc...
    config = base_config.copy()
    # ... set the strategy parameters ...

    # 2) Write to temp config as usual
    with tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False) as tmp:
        yaml.dump(config, tmp)
        tmp_config_path = tmp.name

    # 3) Build the command to run main.py
    #    Pass --trade-log-file <unique_trade_log> to main.py
    cmd = [
        "python3", "main.py",
        "--test",
        "--data", "mes_1yr_1min_bars_history.csv",
        "--config", tmp_config_path,
        "--trade-log-file", unique_trade_log
    ]
    if no_disconnect:
        cmd.append("--no-disconnect")

    # 7) Run the command and capture output
    proc = subprocess.run(cmd, capture_output=True, text=True)

    # 8) Build a results dictionary
    result = {
        "stop_loss_pct": sl,
        "take_profit_pct": tp,
        "RSI_overbought": rsi_ob,
        "RSI_oversold": rsi_os,
        "EMA_period": ema,
        "RSI_period": rsi_p,
        "ATR_period": atr,
        "VWAP_period": vwap,
        "stdout": proc.stdout.strip(),
        "stderr": proc.stderr.strip(),
        "returncode": proc.returncode
    }

    # 9) Remove the temporary file
    os.remove(tmp_config_path)

    return result

def main():
    # -------------------------------------------------------------
    # 1) Parse arguments
    # -------------------------------------------------------------
    parser = argparse.ArgumentParser(
        description="Run parameter testing for the trading bot, in parallel. "
                    "Use --enable-parameter-testing to proceed."
    )
    parser.add_argument("--enable-parameter-testing",
                        action="store_true",
                        help="Enable parameter testing mode (required)")
    parser.add_argument("--no-disconnect",
                        action="store_true",
                        help="Pass --no-disconnect to main.py if supported")
    parser.add_argument("--num-workers",
                        type=int,
                        default=5,
                        help="Number of parallel worker processes. Default=5.")
    args = parser.parse_args()

    if not args.enable_parameter_testing:
        print("Error: You must provide --enable-parameter-testing to run this script.")
        exit(1)

    # -------------------------------------------------------------
    # 2) Load the *base* config from config.yaml
    # -------------------------------------------------------------
    base_config_path = "config.yaml"  # your default config
    with open(base_config_path, "r") as f:
        base_config = yaml.safe_load(f)

    # -------------------------------------------------------------
    # 3) Define parameter ranges
    # -------------------------------------------------------------
    # Trading parameters
    stop_loss_values = [0.003, 0.005, 0.007]       # e.g. 0.3%, 0.5%, 0.7%
    take_profit_values = [0.007, 0.01, 0.012]        # e.g. 0.7%, 1%, 1.2%
    rsi_overbought_values = [55, 60, 65]
    rsi_oversold_values = [35, 30, 25]

    # Indicator parameters
    ema_period_values = [10, 20, 30]
    rsi_period_values = [10, 14, 20]
    atr_period_values = [10, 14, 20]
    vwap_period_values = [0, 10, 20]  # Assuming 0 means no VWAP calculation

    # Build a list of all parameter combinations
    all_params = []
    for sl in stop_loss_values:
        for tp in take_profit_values:
            for rsi_ob in rsi_overbought_values:
                for rsi_os in rsi_oversold_values:
                    for ema in ema_period_values:
                        for rsi_p in rsi_period_values:
                            for atr in atr_period_values:
                                for vwap in vwap_period_values:
                                    all_params.append((
                                        base_config, sl, tp, rsi_ob, rsi_os,
                                        ema, rsi_p, atr, vwap, args.no_disconnect
                                    ))

    # -------------------------------------------------------------
    # 4) Run in parallel using multiprocessing.Pool
    # -------------------------------------------------------------
    MAX_TESTS = 1000
    if len(all_params) > MAX_TESTS:
        all_params = random.sample(all_params, MAX_TESTS)
        print(f"Randomly sampled {MAX_TESTS} out of {len(all_params)} total combinations.")

    logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
    logging.info(f"Starting parallel parameter tests with {args.num_workers} workers...")
    logging.info(f"Total parameter combinations: {len(all_params)}")

    with multiprocessing.Pool(processes=args.num_workers) as pool:
        results = pool.map(run_single_test, all_params)

    # -------------------------------------------------------------
    # 5) Save results to CSV
    # -------------------------------------------------------------
    output_csv = "parameter_test_results.csv"
    fieldnames = [
        "stop_loss_pct",
        "take_profit_pct",
        "RSI_overbought",
        "RSI_oversold",
        "EMA_period",
        "RSI_period",
        "ATR_period",
        "VWAP_period",
        "returncode",
        "stdout",
        "stderr"
    ]

    with open(output_csv, "w", newline="", encoding="utf-8") as csvfile:
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        writer.writeheader()
        for r in results:
            writer.writerow(r)

    logging.info(f"All tests complete. Results saved to {output_csv}")

if __name__ == "__main__":
    main()
