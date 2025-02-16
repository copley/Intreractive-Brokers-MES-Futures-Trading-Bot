MES_Backtest_program/
│
├── main.py                   # Entry point of the application
├── config.yaml               # Centralized configuration file for parameters
│
├── indicators/               # Folder containing indicator calculation logic
│   ├── atr_logic.py          # Logic to calculate ATR
│   ├── rsi_logic.py          # Logic to calculate RSI
│   └── ema_logic.py          # Logic to calculate EMA
│
├── managers/                 # Core management logic for different components
│   ├── trade_manager.py      # Handles trade execution and management
│   ├── entry_manager.py      # Determines optimal entry points for LONG/SHORT trades
│   ├── exit_manager.py       # Manages exits based on Stop-Loss and Take-Profit logic
│   ├── stop_loss_manager.py  # Adjusts stop-loss dynamically based on market conditions
│   ├── take_profit_manager.py# Sets and adjusts take-profit levels
│   └── dynamic_stop_loss.py  # Additional logic for adaptive stop-loss adjustments
│
├── execution/                # Handles the execution of different trade operations
│   ├── trade_execution_logic.py  # General trade execution logic
│   ├── long_order_execution_logic.py # Logic for executing LONG trades
│   ├── short_order_execution_logic.py # Logic for executing SHORT trades
│   ├── stop_loss_order_execution_logic.py # Logic to manage stop-loss orders
│   └── limit_order_execution_logic.py # Logic to manage limit orders
│
├── data/                     # Handles all data-related processes
│   ├── data_loader.py        # Loads market data for backtesting
│   └── data_preprocessor.py  # Processes data for analysis and indicator calculations
│
└── utils/                    # Utility files for logging and supporting functions
    ├── program_log_logic.py  # Handles logging of program actions and errors
    └── helpers.py            # Additional utility functions
