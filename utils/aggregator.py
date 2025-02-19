import logging
from utils.helpers import load_config
from connection.contract_definition import create_contract
from connection.ib_connection import IBConnection
from data.data_loader import DataLoader
from data.data_preprocessor import DataPreprocessor
from indicators.indicator_logic_EMA import calculate_EMA
from indicators.indicator_logic_RSI import calculate_RSI
from indicators.indicator_logic_ATR import calculate_ATR
from indicators.indicator_logic_VWAP import calculate_VWAP
from managers.entry_manager import EntryManager
from managers.exit_manager import ExitManager
from managers.dynamic_stop_loss import DynamicStopLoss
from managers.stop_loss_manager import StopLossManager
from managers.take_profit_manager import TakeProfitManager
from managers.trade_manager import TradeManager
from execution.trade_execution_logic import TradeExecutor
from connection.contract_definition import create_contract

class Aggregator:
    def __init__(self, config: dict):
        ib_cfg = config.get('interactive_brokers', {})
        contract_cfg = config.get('contract', {})

        # 1) Connect to IB
        self.ib_connection = IBConnection(
            host=ib_cfg.get('host', '127.0.0.1'),
            port=ib_cfg.get('port', 7497),
            client_id=ib_cfg.get('client_id', 1)
        )

        # 2) Create the IB contract with all relevant fields
        self.contract = create_contract(
            symbol=contract_cfg.get('symbol'),
            sec_type=contract_cfg.get('sec_type'),
            exchange=contract_cfg.get('exchange'),
            currency=contract_cfg.get('currency'),
            last_trade_date=contract_cfg.get('lastTradeDateOrContractMonth'),
            local_symbol=contract_cfg.get('localSymbol'),
            multiplier=contract_cfg.get('multiplier')
        )

    def __init__(self, config: dict):
        self.config = config
        # Initialize connection to Interactive Brokers
        ib_cfg = config.get('interactive_brokers', {})
        self.ib_connection = IBConnection(ib_cfg.get('host', '127.0.0.1'),
                                          ib_cfg.get('port', 7496),
                                          ib_cfg.get('client_id', 1))
        # Create trading contract
        contract_cfg = config.get('contract', {})
        self.contract = create_contract(contract_cfg.get('symbol'), contract_cfg.get('sec_type'),
                                        contract_cfg.get('exchange'), contract_cfg.get('currency'))
        # Initialize data components
        self.data_loader = DataLoader(self.ib_connection, self.contract)
        self.data_preprocessor = DataPreprocessor()
        # Initialize indicator and strategy managers
        strat_cfg = config.get('strategy', {})
        self.entry_manager = EntryManager(strat_cfg)
        self.exit_manager = ExitManager()
        # Dynamic stop-loss (trailing) with offset = entry_price * stop_loss_pct (to be set per trade)
        sl_offset = 0  # placeholder, will set when trade opens
        self.dynamic_stop_loss = DynamicStopLoss(initial_offset=sl_offset, trailing=True)
        self.stop_loss_manager = StopLossManager(self.dynamic_stop_loss)
        tp_pct = config.get('trading', {}).get('take_profit_pct', 0.0)
        self.take_profit_manager = TakeProfitManager(tp_pct)
        self.trade_executor = TradeExecutor(self.ib_connection, self.contract, config)
        self.trade_manager = TradeManager(self.entry_manager, self.exit_manager,
                                          self.stop_loss_manager, self.take_profit_manager,
                                          self.trade_executor, config)

    def run(self):
        """
        Run the trading loop: fetch data, compute indicators, and trigger trade decisions.
        For demonstration, this runs through a set of historical data once.
        """
        logging.info("Aggregator: Starting main run loop.")
        days = self.config.get('data', {}).get('historical_days', 1)
        bar_size = self.config.get('data', {}).get('bar_size', "1 min")
        raw_data = self.data_loader.fetch_historical_data(days, bar_size)
        data = self.data_preprocessor.preprocess(raw_data)
        # Iterate through historical data points to simulate real-time feed
        prices = []   # to accumulate closing prices for indicator calculations
        highs = []
        lows = []
        closes = []
        volumes = []
        for bar in data:
            # Append current bar values to lists
            closes.append(bar.get('close'))
            highs.append(bar.get('high'))
            lows.append(bar.get('low'))
            volumes.append(bar.get('volume', 0))
            prices.append(bar.get('close'))
            # Compute indicators for the current bar (using all data up to current index)
            ema_val = calculate_EMA(closes, self.config['indicators']['EMA_period'])
            rsi_val = calculate_RSI(closes, self.config['indicators']['RSI_period'])
            atr_val = calculate_ATR(highs, lows, closes, self.config['indicators']['ATR_period'])
            vwap_val = calculate_VWAP(closes, volumes)
            indicators = {
                'EMA': ema_val,
                'RSI': rsi_val,
                'ATR': atr_val,
                'VWAP': vwap_val
            }
            # Update trade logic with the new data point and computed indicators
            self.trade_manager.update(bar, indicators)
        # Once done, disconnect from IB
        self.ib_connection.disconnect()
        logging.info("Aggregator: Run loop completed.")
