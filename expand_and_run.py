#!/usr/bin/env python3

import sys
import glob
import pandas as pd

def main():
    # 1) Get patterns from command line (like trade_log*.csv), expand them:
    if len(sys.argv) < 2:
        print("Usage: python parse_all.py <pattern1> <pattern2> ...")
        print("Example: python parse_all.py trade_log*.csv")
        sys.exit(1)

    all_files = []
    for pattern in sys.argv[1:]:
        matches = glob.glob(pattern)
        all_files.extend(matches)

    if not all_files:
        print("No CSV files found matching your patterns!")
        sys.exit(0)

    # 2) Parse each file, gather results
    #    For example: keep track of total P/L in a list.
    results = []
    for csv_file in all_files:
        try:
            df = pd.read_csv(csv_file)
            # Make sure "P/L" is numeric
            df["P/L"] = pd.to_numeric(df["P/L"], errors="coerce").fillna(0.0)
            total_pl = df["P/L"].sum()
            # Save (filename, total_pl) for sorting
            results.append((csv_file, total_pl))
        except Exception as e:
            # Show the error if you want more detail
            print(f"Could not parse '{csv_file}': {e}")
            # or skip silently

    if not results:
        print("No valid data to show after parsing.")
        sys.exit(0)

    # 3) Sort by total P/L (descending) and show top 10
    #    If you want “largest winning,” use reverse=True. 
    #    For “largest losing,” keep reverse=False. Usually we do largest net profit at the top:
    results.sort(key=lambda x: x[1], reverse=True)

    top_10 = results[:10]
    print("\nTop 10 by total P/L:")
    for filename, pl in top_10:
        print(f"{filename}: {pl}")

    # Also write them to a text file
    with open("top_10_results.txt", "w", encoding="utf-8") as f:
        f.write("Top 10 by total P/L:\n")
        for filename, pl in top_10:
            f.write(f"{filename}: {pl}\n")

if __name__ == "__main__":
    main()
