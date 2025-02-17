import logging
import yaml

def load_config(config_path: str = "config.yaml"):
    """
    Load configuration from a YAML file.
    """
    try:
        with open(config_path, 'r') as f:
            config = yaml.safe_load(f)
            return config
    except Exception as e:
        logging.error(f"Failed to load config file {config_path}: {e}")
        return None

def setup_logging(level: str = "INFO", log_file: str = None):
    """
    Configure logging for the trading bot. Outputs to console or file based on config.
    """
    log_level = getattr(logging, level.upper(), logging.INFO)
    if log_file:
        logging.basicConfig(filename=log_file, level=log_level,
                            format="%(asctime)s [%(levelname)s] %(message)s")
    else:
        logging.basicConfig(level=log_level,
                            format="%(asctime)s [%(levelname)s] %(message)s")
    logging.info("Logging is configured.")
