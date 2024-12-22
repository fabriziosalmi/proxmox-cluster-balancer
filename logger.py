import logging
import os
from colorama import init, Fore, Style

# Initialize colorama
init(autoreset=True)

DEFAULT_LOG_FORMAT = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
DEFAULT_LOG_FILE = 'proxmox_balancer.log'

def setup_logging(log_level=logging.INFO, log_format=DEFAULT_LOG_FORMAT, log_file=DEFAULT_LOG_FILE):
    """
    Sets up logging for the application with console and file outputs.

    Args:
        log_level (int, optional): The logging level (e.g., logging.INFO, logging.DEBUG). Defaults to logging.INFO.
        log_format (str, optional): The format for the log messages. Defaults to DEFAULT_LOG_FORMAT.
        log_file (str, optional): The name of the log file. Defaults to DEFAULT_LOG_FILE.

    Returns:
        logging.Logger: A logger instance.
    """

    logger = logging.getLogger('proxmox_balancer') # Set a global logger name
    logger.setLevel(log_level)


    # Create file handler
    file_handler = logging.FileHandler(log_file)
    file_handler.setLevel(logging.DEBUG) # Log everything to file
    file_formatter = logging.Formatter(log_format)
    file_handler.setFormatter(file_formatter)

    # Create console handler
    console_handler = logging.StreamHandler()
    console_handler.setLevel(log_level)
    console_formatter = logging.Formatter(log_format)
    console_handler.setFormatter(console_formatter)

    logger.addHandler(file_handler)
    logger.addHandler(console_handler)
    return logger

if __name__ == "__main__":
    # Example Usage
    logger = setup_logging(log_level=logging.DEBUG)  # Set logging level to DEBUG for testing

    logger.debug("This is a debug message")
    logger.info("This is an info message")
    logger.warning("This is a warning message")
    logger.error("This is an error message")
    logger.critical("This is a critical message")
    try:
      raise Exception ("Test exception")
    except Exception as e:
      logger.exception("Exception Example", exc_info=True)

    print("Log messages have been generated in the console and 'proxmox_balancer.log' file.")
