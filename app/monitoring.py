import logging
import logging.handlers
import os
from datetime import datetime
from typing import Dict, Any, Optional
from fastapi import Request, Response
import json
import time
from contextvars import ContextVar
from uuid import uuid4

# Context variable to store request ID
request_id_ctx = ContextVar('request_id', default=None)

def setup_logging():
    """Configure logging with file rotation and console output."""
    log_dir = "logs"
    os.makedirs(log_dir, exist_ok=True)
    
    # Create a custom formatter
    class RequestIdFilter(logging.Filter):
        def filter(self, record):
            record.request_id = request_id_ctx.get() or 'system'
            return True
    
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - [%(request_id)s] - %(message)s'
    )
    
    # Root logger
    logger = logging.getLogger()
    logger.setLevel(logging.INFO)
    
    # Add filter to all handlers
    for handler in logger.handlers:
        handler.addFilter(RequestIdFilter())
    
    # Console handler
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(formatter)
    console_handler.addFilter(RequestIdFilter())
    
    # File handler with rotation
    file_handler = logging.handlers.RotatingFileHandler(
        os.path.join(log_dir, 'bi_chatbot.log'),
        maxBytes=10*1024*1024,  # 10MB
        backupCount=5
    )
    file_handler.setFormatter(formatter)
    file_handler.addFilter(RequestIdFilter())
    
    # Error file handler
    error_file_handler = logging.handlers.RotatingFileHandler(
        os.path.join(log_dir, 'bi_chatbot_errors.log'),
        maxBytes=10*1024*1024,  # 10MB
        backupCount=5
    )
    error_file_handler.setLevel(logging.ERROR)
    error_file_handler.setFormatter(formatter)
    error_file_handler.addFilter(RequestIdFilter())
    
    # Add handlers
    logger.addHandler(console_handler)
    logger.addHandler(file_handler)
    logger.addHandler(error_file_handler)

def log_request(request: Request, response: Response, process_time: float):
    """Log HTTP request details."""
    logger = logging.getLogger("api")
    
    # Skip health checks and other noise
    if request.url.path == "/health":
        return
    
    log_data = {
        "method": request.method,
        "path": request.url.path,
        "query_params": dict(request.query_params),
        "status_code": response.status_code,
        "process_time": round(process_time, 3),
        "client_ip": request.client.host,
        "user_agent": request.headers.get("user-agent"),
    }
    
    # Log the request
    if 400 <= response.status_code < 500:
        logger.warning(f"Client error: {log_data}")
    elif response.status_code >= 500:
        logger.error(f"Server error: {log_data}")
    else:
        logger.info(f"Request processed: {log_data}")

class RequestLoggerMiddleware:
    """Middleware to log requests and responses."""
    
    async def __call__(self, request: Request, call_next):
        # Generate a unique request ID
        request_id = str(uuid4())
        request_id_ctx.set(request_id)
        
        # Add request ID to response headers
        response = await call_next(request)
        response.headers["X-Request-ID"] = request_id
        
        # Log the request
        process_time = time.time() - request.scope.get("start_time", time.time())
        log_request(request, response, process_time)
        
        return response

class SQLQueryLogger:
    """Log SQL queries for performance monitoring."""
    
    def __init__(self):
        self.logger = logging.getLogger("sql")
        self.logger.setLevel(logging.INFO)
    
    def log_query(self, query: str, params: Dict, duration: float):
        """Log a SQL query with its parameters and execution time."""
        self.logger.info(
            f"SQL Query ({(duration*1000):.2f}ms): {query} | Params: {params}"
        )

# Initialize logging when module is imported
setup_logging()

# Create loggers
logger = logging.getLogger(__name__)
sql_logger = SQLQueryLogger()
