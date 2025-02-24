# File: get_trade_results_from_1000_files.py

import sys
import os
from compute_trade_stats import compute_trade_stats

def main():
    if len(sys.argv) < 2:
        print("Usage: python get_trade_results_from_1000_files.py <csv_file(s)>")
        sys.exit(1)

    results = []

    for csv_file in sys.argv[1:]:
        # If shell expansion didn't work, or Windows doesn't handle '*' well,
        # you might get literal 'trade_log*.csv'. Make sure file actually exists:
        if not os.path.isfile(csv_file):
            print(f"Could not parse '{csv_file}': file not found.")
            continue

        try:
            stats_dict = compute_trade_stats(
                csv_path=csv_file,
                initial_capital=10000.0
            )
            net_profit = stats_dict["net_profit"]
            results.append((csv_file, net_profit, stats_dict))

        except Exception as e:
            # If we have a CSV parse error or missing columns, etc.
            print(f"Could not parse '{csv_file}': {e}")
            continue

    # Sort by net profit descending
    results.sort(key=lambda x: x[1], reverse=True)

    # Print top 10 on screen
    print("\nTop 10 by total P/L:")
    top_10 = results[:10]
    for (csv_file, net_profit, _) in top_10:
        print(f"{csv_file}: {net_profit:.2f}")

    # Also write top 10 results to an output file
    with open("top_10_results.txt", "w") as out_f:
        out_f.write("Top 10 by total P/L:\n")
        for (csv_file, net_profit, stats_dict) in top_10:
            out_f.write(f"{csv_file}: Net Profit = {net_profit:.2f}\n")
            out_f.write(f"  Final Equity:    {stats_dict['final_equity']:.2f}\n")
            out_f.write(f"  Max Drawdown:    {stats_dict['max_drawdown']:.2f}\n")
            out_f.write("\n")

if __name__ == "__main__":
    main()
