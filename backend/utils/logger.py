import logging
import sys
from datetime import datetime
import os

def setup_logger(name: str = "trip_planner", level: str = "INFO") -> logging.Logger:
    """
    Set up a logger with proper formatting and handlers
    
    Args:
        name: Logger name
        level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
    
    Returns:
        Configured logger instance
    """
    
    # Create logger
    logger = logging.getLogger(name)
    logger.setLevel(getattr(logging, level.upper()))
    
    # Prevent duplicate handlers
    if logger.handlers:
        return logger
    
    # Create formatter
    formatter = logging.Formatter(
        fmt='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    
    # Create console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(logging.INFO)
    console_handler.setFormatter(formatter)
    
    # Create file handler (optional)
    log_dir = os.getenv("LOG_DIR", "logs")
    if not os.path.exists(log_dir):
        os.makedirs(log_dir)
    
    log_file = os.path.join(log_dir, f"trip_planner_{datetime.now().strftime('%Y%m%d')}.log")
    file_handler = logging.FileHandler(log_file)
    file_handler.setLevel(logging.DEBUG)
    file_handler.setFormatter(formatter)
    
    # Add handlers to logger
    logger.addHandler(console_handler)
    logger.addHandler(file_handler)
    
    # Log initial message
    logger.info(f"Logger '{name}' initialized with level {level}")
    
    return logger

def log_agent_step(logger: logging.Logger, step: str, details: str = None):
    """Log an agent execution step"""
    message = f"Agent Step: {step}"
    if details:
        message += f" - {details}"
    logger.info(message)

def log_api_call(logger: logging.Logger, tool_name: str, params: dict, duration: float = None):
    """Log an API/tool call"""
    message = f"Tool Call: {tool_name} with params {params}"
    if duration:
        message += f" (took {duration:.2f}s)"
    logger.info(message)
