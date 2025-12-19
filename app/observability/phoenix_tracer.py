"""Phoenix tracer initialization for monitoring AutoGen agents and OpenAI calls."""

import os
from typing import Optional
from opentelemetry.sdk.trace import TracerProvider

from app.config.settings import get_settings
from app.middleware.logging import logger


_tracer_provider: Optional[TracerProvider] = None


def initialize_phoenix() -> Optional[TracerProvider]:
    """
    Initialize Phoenix tracing for observability.
    
    This will automatically trace:
    - All OpenAI API calls (used by AutoGen)
    - AutoGen agent interactions
    - Function calls and tool usage
    - Conversation flows
    
    Returns:
        TracerProvider instance if successful, None otherwise
    """
    global _tracer_provider
    
    if _tracer_provider is not None:
        logger.info("Phoenix tracer already initialized")
        return _tracer_provider
    
    settings = get_settings()
    
    # Set Phoenix environment variables if configured
    if settings.phoenix_api_key:
        os.environ["PHOENIX_API_KEY"] = settings.phoenix_api_key
        logger.info("Phoenix API key configured")
    
    if settings.phoenix_collector_endpoint:
        os.environ["PHOENIX_COLLECTOR_ENDPOINT"] = settings.phoenix_collector_endpoint
        logger.info(f"Phoenix collector endpoint: {settings.phoenix_collector_endpoint}")
    
    try:
        from phoenix.otel import register
        
        # Register Phoenix tracer with auto-instrumentation
        _tracer_provider = register(
            project_name=settings.phoenix_project_name,
            auto_instrument=True  # Auto-instrument OpenAI and other dependencies
        )
        
        logger.info(f"Phoenix tracing initialized for project: {settings.phoenix_project_name}")
        
        # Determine Phoenix UI URL
        if settings.phoenix_collector_endpoint:
            logger.info(f"View traces at: {settings.phoenix_collector_endpoint.replace('/v1/traces', '')}")
        else:
            logger.info("View traces at: http://localhost:6006 (run 'python -m phoenix.server.main serve' if not running)")
        
        return _tracer_provider
        
    except ImportError as e:
        logger.warning(f"Phoenix packages not installed: {e}")
        logger.warning("Install with: pip install arize-phoenix arize-phoenix-otel openinference-instrumentation-openai")
        return None
        
    except Exception as e:
        logger.error(f"Failed to initialize Phoenix tracing: {e}", exc_info=True)
        return None


def shutdown_phoenix():
    """Shutdown Phoenix tracing gracefully."""
    global _tracer_provider
    
    if _tracer_provider is None:
        return
    
    try:
        # Force flush any pending traces
        if hasattr(_tracer_provider, 'force_flush'):
            _tracer_provider.force_flush()
        
        logger.info("Phoenix tracer shutdown complete")
        _tracer_provider = None
        
    except Exception as e:
        logger.error(f"Error shutting down Phoenix tracer: {e}", exc_info=True)


def is_phoenix_enabled() -> bool:
    """Check if Phoenix tracing is currently enabled."""
    return _tracer_provider is not None
