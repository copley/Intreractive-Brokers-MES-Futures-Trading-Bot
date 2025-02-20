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

1) We build a list of parameter combinations (stop_loss, take_profit, RSI_overbought, RSI_oversold).
2) We spin up a pool of worker processes (default 5).
3) Each process runs a single backtest by calling main.py with --test and a temporary config file.
4) We collect the results in a CSV for later analysis.
5) This is much faster than running everything sequentially!
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

def run_single_test(param_tuple):
    """
    Worker function that receives a single parameter combination and:
      1) Writes a temporary config file with those parameters.
      2) Calls 'main.py --test --config <tmp_config>' (plus optional --no-disconnect).
      3) Captures stdout/stderr/returncode.
      4) Deletes the temp config file.
      5) Returns a dictionary with all relevant info.
    """
    (base_config, stop_loss, take_profit, rsi_overbought, rsi_oversold, no_disconnect) = param_tuple

    # 1) Copy the base config dictionary
    config = base_config.copy()

    # 2) Update relevant fields in the config
    config["trading"]["stop_loss_pct"] = stop_loss
    config["trading"]["take_profit_pct"] = take_profit
    config["strategy"]["RSI_overbought"] = rsi_overbought
    config["strategy"]["RSI_oversold"] = rsi_oversold

    # 3) Write to a temporary YAML file
    with tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False) as tmp:
        yaml.dump(config, tmp)
        tmp_config_path = tmp.name

    # 4) Build the command to run main.py in backtest mode with this config
    cmd = ["python3", "main.py", "--test", "--data", "bars_data.csv", "--config", tmp_config_path]
    if no_disconnect:
        cmd.append("--no-disconnect")  # if your main.py uses it

    # 5) Run the command and capture output
    proc = subprocess.run(cmd, capture_output=True, text=True)

    # 6) Build a results dictionary
    result = {
        "stop_loss_pct": stop_loss,
        "take_profit_pct": take_profit,
        "RSI_overbought": rsi_overbought,
        "RSI_oversold": rsi_oversold,
        "stdout": proc.stdout.strip(),
        "stderr": proc.stderr.strip(),
        "returncode": proc.returncode
    }

    # 7) Remove the temporary file
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
    # 3) Define parameter ranges (example)
    # -------------------------------------------------------------
    stop_loss_values = [0.003, 0.005, 0.007]       # e.g. 0.3%, 0.5%, 0.7%
    take_profit_values = [0.007, 0.01, 0.012]      # e.g. 0.7%, 1%, 1.2%
    rsi_overbought_values = [55, 60, 65]
    rsi_oversold_values = [35, 30, 25]

    # Build a list of all parameter combinations
    all_params = []
    for sl in stop_loss_values:
        for tp in take_profit_values:
            for rsi_ob in rsi_overbought_values:
                for rsi_os in rsi_oversold_values:
                    all_params.append((base_config, sl, tp, rsi_ob, rsi_os, args.no_disconnect))

    # -------------------------------------------------------------
    # 4) Run in parallel using multiprocessing.Pool
    # -------------------------------------------------------------
    logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
    logging.info(f"Starting parallel parameter tests with {args.num_workers} workers...")

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
