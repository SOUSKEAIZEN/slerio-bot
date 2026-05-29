import logging
import sys

def setup_logger():
    # Create a custom logger
    logger = logging.getLogger("slero_bot")
    
    # Set the base logging level to DEBUG to catch everything
    logger.setLevel(logging.DEBUG)

    # Create handlers: one for the console, one for a log file
    c_handler = logging.StreamHandler(sys.stdout)
    f_handler = logging.FileHandler('bot_activity.log', encoding='utf-8')
    
    # Console shows INFO level and above (keeps terminal clean)
    c_handler.setLevel(logging.INFO) 
    # File saves DEBUG level and above (for deep troubleshooting)
    f_handler.setLevel(logging.DEBUG) 

    # Create formatters and add them to handlers
    log_format = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s', datefmt='%Y-%m-%d %H:%M:%S')
    c_handler.setFormatter(log_format)
    f_handler.setFormatter(log_format)

    # Add handlers to the logger (preventing duplicates)
    if not logger.handlers:
        logger.addHandler(c_handler)
        logger.addHandler(f_handler)

    return logger

# Initialize the logger so other files can just import it
logger = setup_logger()
logger.info("Logging system initialized successfully.")