"""Phoenix observability for tracking agent activities."""

from app.observability.phoenix_tracer import initialize_phoenix, shutdown_phoenix

__all__ = ["initialize_phoenix", "shutdown_phoenix"]
