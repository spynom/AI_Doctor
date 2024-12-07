import logging

def get_logger():

    # Configure logging
    logging.basicConfig(
        level=logging.INFO,  # Log level: DEBUG, INFO, WARNING, ERROR, CRITICAL
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler("app.log"),  # Logs saved in 'app.log'
            logging.StreamHandler()  # Also logs to console
        ]
    )

    return logging.getLogger(__name__)