import logging
import sys
import json
from datetime import datetime
from app.core.config import settings

class StructuredFormatter(logging.Formatter):
    """
    Formatter that outputs logs as a JSON string for structured production logging.
    """
    def format(self, record):
        log_record = {
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "level": record.levelname,
            "name": record.name,
            "message": record.getMessage(),
            "module": record.module,
            "filename": record.filename,
            "line_number": record.lineno
        }
        # If there is exception info, format it and append
        if record.exc_info:
            log_record["exception"] = self.formatException(record.exc_info)
        return json.dumps(log_record)

def get_logger(name: str) -> logging.Logger:
    """
    Get a configured structured logger.
    """
    logger = logging.getLogger(name)
    
    # Prevent propagation of logs to the root logger to avoid duplicate log outputs
    logger.propagate = False
    
    # Set level based on configuration
    logger.setLevel(logging.DEBUG if settings.DEBUG else logging.INFO)
    
    if not logger.handlers:
        handler = logging.StreamHandler(sys.stdout)
        
        # Production gets JSON logs, development gets clean, color-like structured strings
        if settings.ENV.lower() == "production":
            handler.setFormatter(StructuredFormatter())
        else:
            formatter = logging.Formatter(
                fmt="[%(asctime)s] %(levelname)-7s - %(name)s - %(message)s",
                datefmt="%Y-%m-%d %H:%M:%S"
            )
            handler.setFormatter(formatter)
            
        logger.addHandler(handler)
        
    return logger
