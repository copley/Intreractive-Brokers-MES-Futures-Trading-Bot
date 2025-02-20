# File: compute_trade_stats.py
import pandas as pd
import math

def compute_trade_stats(csv_path="trade_log.csv", initial_capital=10000.0):
    """
    Reads trades from 'trade_log.csv' and computes overall stats + separate LONG/SHORT stats.
    Also does a running equity simulation to find net profit, drawdown, etc.
    """
    try:
        df = pd.read_csv(csv_path)
    except FileNotFoundError:
        print(f"No trades found: {csv_path} does not exist.")
        return

    # If your log has these columns (including the new "Side" column):
    # ["Trade #", "Date", "Time", "Symbol", "Entry Price", "Stop Loss",
    #  "Target Price", "Exit Price", "Exit Time", "Result", "P/L", "Comments", "Side"]

    if "Side" not in df.columns:
        print("No 'Side' column found; can't separate LONG vs SHORT. Please ensure your CSV has this column.")
        return

    # Convert P/L to float, in case it's string
    df["P/L"] = pd.to_numeric(df["P/L"], errors="coerce").fillna(0.0)

    # Optional: if you have 'Entry Bar' / 'Exit Bar' columns, we can compute bar counts
    # e.g. "Avg # bars in winning trades" vs losing trades
    bar_counts = None
    if "Entry Bar" in df.columns and "Exit Bar" in df.columns:
        df["bar_count"] = df["Exit Bar"] - df["Entry Bar"]
    else:
        # We'll skip bar counts if not present
        pass

    # A) QUICK AGGREGATES

    # 1) Overall trade stats
    overall_stats = _compute_subset_stats(df, label="ALL")

    # 2) Long-only stats
    long_df = df[df["Side"] == "LONG"]
    long_stats = _compute_subset_stats(long_df, label="LONG")

    # 3) Short-only stats
    short_df = df[df["Side"] == "SHORT"]
    short_stats = _compute_subset_stats(short_df, label="SHORT")

    # B) RUNNING EQUITY & DRAWDOWN

    # Sort by "Trade #" or by "Date" if you prefer chronological order
    # (If you always increment "Trade #" in order, we can just sort by that.)
    df = df.sort_values(by="Trade #")

    # We'll track equity from initial_capital
    equity = initial_capital
    max_equity = initial_capital
    min_equity = initial_capital
    equity_curve = [initial_capital]  # store after each trade

    for idx, row in df.iterrows():
        equity += row["P/L"]  # add the trade's profit/loss
        equity_curve.append(equity)
        if equity > max_equity:
            max_equity = equity
        if equity < min_equity:
            min_equity = equity

    net_profit = equity - initial_capital
    max_runup = max_equity - initial_capital
    max_drawdown = initial_capital - min_equity
    # Or measure “% run-up” and “% drawdown” if you prefer.

    # PRINT A SUMMARY
    print("----- TRADE STATS SUMMARY -----")
    print("Initial Capital:    $%.2f" % initial_capital)
    print("Final Equity:       $%.2f" % equity)
    print("Net Profit:         $%.2f (%.2f%%)" % (net_profit, 100.0 * net_profit / initial_capital if initial_capital else 0))
    print("Max Equity Run-up:  $%.2f" % max_runup)
    print("Max Drawdown:       $%.2f" % max_drawdown)
    print()

    # Print each subset's stats
    for subset_stats in [overall_stats, long_stats, short_stats]:
        _pretty_print_stats(subset_stats)

def _compute_subset_stats(df, label="ALL"):
    """
    Given a subset of trades (all, long, short), compute various metrics:
      - total trades, winners, losers
      - win rate
      - average P/L
      - largest win/loss
      - ratio of avg win to avg loss
      - average bar count, etc.
    Returns a dictionary with these values.
    """
    if len(df) == 0:
        return {
            "label": label,
            "total_trades": 0,
            "winning_trades": 0,
            "losing_trades": 0,
            "win_rate": 0.0,
            "avg_pl": 0.0,
            "largest_win": 0.0,
            "largest_loss": 0.0,
            "profit_factor": 0.0,
            "avg_win": 0.0,
            "avg_loss": 0.0,
            "avg_bar_count": None,
        }

    total_trades = len(df)
    winners = df[df["P/L"] > 0]
    losers  = df[df["P/L"] < 0]
    winning_trades = len(winners)
    losing_trades  = len(losers)
    win_rate = 100.0 * winning_trades / total_trades

    avg_pl = df["P/L"].mean()
    largest_win  = winners["P/L"].max() if not winners.empty else 0.0
    largest_loss = losers["P/L"].min() if not losers.empty else 0.0
    # We typically store the largest losing trade as a positive magnitude, so do abs():
    largest_loss = abs(largest_loss)

    # Profit factor = sum(wins) / sum(abs(losses))
    sum_wins = winners["P/L"].sum()
    sum_losses = losers["P/L"].sum()  # negative
    profit_factor = 0.0
    if sum_losses != 0:
        profit_factor = sum_wins / abs(sum_losses)

    # average winner / average loser
    avg_win_val = winners["P/L"].mean() if not winners.empty else 0.0
    avg_loss_val = losers["P/L"].mean() if not losers.empty else 0.0
    ratio_avg_win_loss = 0.0
    if avg_loss_val != 0:
        ratio_avg_win_loss = avg_win_val / abs(avg_loss_val)

    # average # bars in trade, if you have bar_count
    if "bar_count" in df.columns:
        avg_bars = df["bar_count"].mean()
    else:
        avg_bars = None

    return {
        "label": label,
        "total_trades": total_trades,
        "winning_trades": winning_trades,
        "losing_trades": losing_trades,
        "win_rate": win_rate,
        "avg_pl": avg_pl,
        "largest_win": largest_win,
        "largest_loss": largest_loss,
        "profit_factor": profit_factor,
        "avg_win": avg_win_val,
        "avg_loss": avg_loss_val,
        "ratio_avg_win_loss": ratio_avg_win_loss,
        "avg_bar_count": avg_bars,
    }

def _pretty_print_stats(stats):
    """
    Print a formatted block of stats for one subset.
    """
    label = stats["label"]
    print(f"=== {label} Trades ===")
    print(f"Total Trades:          {stats['total_trades']}")
    print(f"Winners / Losers:     {stats['winning_trades']} / {stats['losing_trades']}")
    print(f"Win Rate:             {stats['win_rate']:.2f}%")
    print(f"Avg P/L:              {stats['avg_pl']:.2f}")
    print(f"Largest Win:          {stats['largest_win']:.2f}")
    print(f"Largest Loss:         {stats['largest_loss']:.2f}")
    print(f"Profit Factor:        {stats['profit_factor']:.3f}")
    print(f"Avg Win / Avg Loss:   {stats['ratio_avg_win_loss']:.3f}")
    if stats["avg_bar_count"] is not None:
        print(f"Avg # bars in trades: {stats['avg_bar_count']:.1f}")
    print()
