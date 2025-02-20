#!/usr/bin/env python3

import sys
import re

def main():
    if len(sys.argv) < 2:
        print(f"Usage: {sys.argv[0]} <logfile>")
        sys.exit(1)
    
    logfile = sys.argv[1]

    with open(logfile, 'r', encoding='utf-8') as f:
        lines = f.readlines()

    # This list will hold tuples of the form:
    # (line_number, extracted_win_rate_float, original_line_text)
    found_win_rates = []

    # Regex to match lines like:
    #   Win Rate:              28.88%
    # We'll capture the numeric portion (e.g. 28.88)
    pattern = re.compile(r"Win Rate:\s*([\d.]+)%")

    for idx, line in enumerate(lines, start=1):
        match = pattern.search(line)
        if match:
            # Extract the numeric portion from the group
            win_rate_str = match.group(1)  # e.g. "28.88"
            try:
                win_rate_val = float(win_rate_str)
            except ValueError:
                # If conversion fails for some reason, skip
                continue
            
            found_win_rates.append((idx, win_rate_val, line.strip()))

    # Sort by the win_rate_val descending
    found_win_rates.sort(key=lambda x: x[1], reverse=True)

    # Print top 10
    print("Top 10 Win Rates found in the log:")
    for i, (line_num, rate, text) in enumerate(found_win_rates[:10], start=1):
        print(f"{i}. Line {line_num}: Win Rate = {rate}% | Full line: {text}")

if __name__ == "__main__":
    main()
