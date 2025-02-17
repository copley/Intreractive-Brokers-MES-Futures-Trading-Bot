import logging
from utils import helpers
from aggregator import Aggregator

if __name__ == "__main__":
    # Load configuration
    config = helpers.load_config("config.yaml")
    if not config:
        raise SystemExit("Failed to load configuration. Exiting.")
    # Setup logging as per configuration
    log_cfg = config.get('logging', {})
    log_level = log_cfg.get('level', 'INFO')
    log_file = log_cfg.get('file')
    helpers.setup_logging(level=log_level, log_file=log_file)
    logging.info("Trading bot starting...")
    # Initialize and run the aggregator (main bot logic)
    bot = Aggregator(config)
    bot.run()
    logging.info("Trading bot finished execution.")
