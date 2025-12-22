"""Phoenix tracer initialization for monitoring AutoGen agents and OpenAI calls."""

import os
from typing import Optional, Dict, Any
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.trace import Status, StatusCode, get_tracer
from contextlib import contextmanager

from app.config.settings import get_settings
from app.middleware.logging import logger


_tracer_provider: Optional[TracerProvider] = None
_tracer = None


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
        
        # Initialize tracer for custom spans
        global _tracer
        _tracer = get_tracer("realestate_agents", "1.0.0")
        
        logger.info(f"Phoenix tracing initialized for project: {settings.phoenix_project_name}")
        logger.info("🔍 Agent tracking enabled: Orchestrator, PropertyAgent, BookingAgent, FAQAgent")
        
        # Determine Phoenix UI URL
        if settings.phoenix_collector_endpoint:
            logger.info(f"View traces at: {settings.phoenix_collector_endpoint.replace('/v1/traces', '')}")
        else:
            logger.info("View traces at: http://localhost:6006 (run 'python -m phoenix.server.main serve' if not running)")
            logger.info("💡 No API key needed for local Phoenix deployment!")
        
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


@contextmanager
def trace_agent_action(agent_name: str, action: str, **attributes):
    """
    Context manager to trace individual agent actions with custom spans.
    
    Args:
        agent_name: Name of the agent (e.g., 'PropertyAgent', 'BookingAgent', 'FAQAgent', 'Orchestrator')
        action: Action being performed (e.g., 'search_properties', 'create_booking', 'rag_search')
        **attributes: Additional attributes to add to the span
    
    Usage:
        with trace_agent_action("PropertyAgent", "search_properties", city="New York", price_range="500k-1M"):
            # Your agent code here
            properties = search_properties(...)
    """
    if not is_phoenix_enabled() or _tracer is None:
        # If Phoenix is disabled, just yield without tracing
        yield
        return
    
    try:
        span_name = f"{agent_name}.{action}"
        with _tracer.start_as_current_span(span_name) as span:
            # Add standard attributes
            span.set_attribute("agent.name", agent_name)
            span.set_attribute("agent.action", action)
            
            # Add custom attributes
            for key, value in attributes.items():
                if value is not None:
                    span.set_attribute(f"agent.{key}", str(value))
            
            logger.debug(f"🔍 Tracing: {span_name}")
            
            try:
                yield span
                span.set_status(Status(StatusCode.OK))
            except Exception as e:
                span.set_status(Status(StatusCode.ERROR, str(e)))
                span.record_exception(e)
                raise
    except Exception as e:
        logger.error(f"Error creating trace span: {e}")
        yield


def add_agent_metadata(span, metadata: Dict[str, Any]):
    """
    Add metadata to a span for agent tracking.
    
    Args:
        span: OpenTelemetry span object
        metadata: Dictionary of metadata to add
    """
    if span is None:
        return
    
    for key, value in metadata.items():
        if value is not None:
            try:
                span.set_attribute(f"agent.metadata.{key}", str(value))
            except Exception as e:
                logger.warning(f"Failed to set span attribute {key}: {e}")
