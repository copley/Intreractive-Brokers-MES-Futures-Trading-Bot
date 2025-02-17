import logging

class DataPreprocessor:
    """
    Handles preprocessing of raw data into a format suitable for indicator calculations and strategy logic.
    """
    def __init__(self):
        pass

    def preprocess(self, raw_data):
        """
        Perform any necessary preprocessing on raw data.
        For example: sorting data by time, handling missing values, etc.
        Returns processed data (e.g., list of bar dictionaries).
        """
        if not raw_data:
            logging.warning("No data to preprocess.")
            return []
        # Sort data by timestamp if not already sorted
        data = sorted(raw_data, key=lambda x: x.get("time", 0))
        # Potentially handle missing data or outliers here (not implemented for simplicity)
        logging.info(f"Preprocessed {len(data)} data points.")
        return data
