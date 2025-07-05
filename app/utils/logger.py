# app/utils/logger.py
import logging
from loguru import logger
import sys
from pathlib import Path

def setup_logger():
    """Configure and setup loguru logger"""
    
    # Remove default handler
    logger.remove()
    
    # Add console handler with formatting
    logger.add(
        sys.stdout,
        format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - <level>{message}</level>",
        level="INFO"
    )
    
    # Add file handler
    log_dir = Path("logs")
    log_dir.mkdir(exist_ok=True)
    
    logger.add(
        log_dir / "app.log",
        rotation="500 MB",
        retention="10 days",
        format="{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | {name}:{function}:{line} - {message}",
        level="DEBUG"
    )
    
    return logger

# Create a logger instance
app_logger = setup_logger()

def get_logger():
    """Get the configured logger instance"""
    return app_logger