import logging

def get_logger(name):
    logger = logging.Logger(name)
    logger.formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    logger.setLevel(logging.INFO)
    logger.addHandler(logging.StreamHandler())
    return logger