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

    # Remove existing handlers to avoid duplicates on reconfiguration
    for handler in logger.handlers[:]:
        logger.removeHandler(handler)

    # Create file handler only if the log file path is valid and writable
    if log_file:
        # Ensure the directory exists where the log file will be created
        log_dir = os.path.dirname(log_file)
        if log_dir and not os.path.exists(log_dir):
            try:
                os.makedirs(log_dir)
            except OSError:
                # If we cannot create the directory, skip the file handler
                # The logger will still work via the console handler
                log_file = None
        
        if log_file:
            try:
                file_handler = logging.FileHandler(log_file)
                file_handler.setLevel(logging.DEBUG) # Log everything to file
                file_formatter = logging.Formatter(log_format)
                file_handler.setFormatter(file_formatter)
                logger.addHandler(file_handler)
            except (IOError, OSError):
                # If we cannot open the file (e.g., permission denied), skip the file handler
                # The logger will still work via the console handler
                pass

    # Create console handler
    console_handler = logging.StreamHandler()
    console_handler.setLevel(log_level)
    console_formatter = logging.Formatter(log_format)
    console_handler.setFormatter(console_formatter)
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
