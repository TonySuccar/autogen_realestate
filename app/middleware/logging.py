from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.types import ASGIApp
import time
import logging
from datetime import datetime
from app.config import get_settings

settings = get_settings()

# Configure logging
logging.basicConfig(
    level=settings.log_level,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[logging.StreamHandler()],
)


logger = logging.getLogger(__name__)


class LoggingMiddleware(BaseHTTPMiddleware):
    """
    Middleware for logging HTTP requests and responses.
    Tracks request duration, status codes, and request details.
    """
    
    def __init__(self, app: ASGIApp):
        super().__init__(app)
    
    async def dispatch(self, request: Request, call_next) -> Response:
        """
        Process the request and log relevant information.
        
        Args:
            request: Incoming HTTP request
            call_next: Next middleware or route handler
            
        Returns:
            Response: HTTP response
        """
        # Record start time
        start_time = time.time()
        
        # Get request details
        client_host = request.client.host if request.client else "unknown"
        method = request.method
        url_path = request.url.path
        
        # Log incoming request
        logger.info(
            f"Incoming request: {method} {url_path} from {client_host}"
        )
        
        # Process request
        try:
            response = await call_next(request)
            
            # Calculate request duration
            duration = time.time() - start_time
            
            # Log response
            status_code = response.status_code
            log_message = (
                f"Response: {method} {url_path} "
                f"Status: {status_code} "
                f"Duration: {duration:.3f}s"
            )
            
            # Use different log levels based on status code
            if status_code >= 500:
                logger.error(log_message)
            elif status_code >= 400:
                logger.warning(log_message)
            else:
                logger.info(log_message)
            
            # Add custom headers
            response.headers["X-Process-Time"] = str(duration)
            
            return response
            
        except Exception as e:
            # Log exceptions
            duration = time.time() - start_time
            logger.error(
                f"Exception during request: {method} {url_path} "
                f"Error: {str(e)} "
                f"Duration: {duration:.3f}s",
                exc_info=True
            )
            raise
