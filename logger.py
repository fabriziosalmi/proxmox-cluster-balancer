import logging
from colorama import init, Fore, Style

def setup_logging():
    logging.basicConfig(
        level=logging.INFO,
        format=f'%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    logger = logging.getLogger(__name__)
    return logger

# Initialize colorama
init(autoreset=True)
