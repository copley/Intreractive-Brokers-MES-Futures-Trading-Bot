import pandas as pd
import time
from ib_insync import *
from rich.console import Console
from rich.table import Table

def load_positions_from_csv():
    """Hardcoded positions from CSV file."""
    return pd.DataFrame([
        {"Financial Instrument": "Stock", "Symbol": "AAPL", "Last": 175.20, "Daily P&L": 200.50, "Unrealized P&L": 500.75},
        {"Financial Instrument": "Stock", "Symbol": "TSLA", "Last": 725.10, "Daily P&L": -150.30, "Unrealized P&L": 250.40},
        {"Financial Instrument": "Stock", "Symbol": "MSFT", "Last": 310.85, "Daily P&L": 100.00, "Unrealized P&L": 400.60},
        {"Financial Instrument": "Stock", "Symbol": "GOOGL", "Last": 2850.25, "Daily P&L": 300.75, "Unrealized P&L": 800.90},
        {"Financial Instrument": "Stock", "Symbol": "AMZN", "Last": 3400.50, "Daily P&L": -50.20, "Unrealized P&L": 1200.30}
    ])

def update_positions_table(positions):
    """Display the positions in a dynamically updating table."""
    console = Console()
    while True:
        console.clear()
        table = Table(title="TWS Positions")
        
        # Adding selected columns
        columns = ["Financial Instrument", "Symbol", "Last", "Daily P&L", "Unrealized P&L"]
        for col in columns:
            table.add_column(col, justify="right")
        
        # Adding rows
        for _, row in positions.iterrows():
            table.add_row(*[str(row[col]) for col in columns])
        
        console.print(table)
        time.sleep(2)  # Refresh interval

def main():
    positions = load_positions_from_csv()
    update_positions_table(positions)

if __name__ == "__main__":
    main()
