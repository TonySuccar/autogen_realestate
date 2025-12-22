#!/usr/bin/env python3
"""
Phoenix Server Launcher
Starts the Arize Phoenix observability server for monitoring AI agents.

Usage: python run_phoenix.py

Access the Phoenix UI at: http://localhost:6006

No API key needed for local deployment!
"""

import sys
import subprocess
from pathlib import Path


def main():
    print("=" * 60)
    print("🔍 Starting Arize Phoenix Observability Server")
    print("=" * 60)
    print()
    print("📊 Phoenix will track:")
    print("  ✓ OrchestratorAgent - Multi-agent coordination")
    print("  ✓ PropertyAgent - Property searches")
    print("  ✓ BookingAgent - Viewing bookings")
    print("  ✓ FAQAgent - RAG semantic searches")
    print("  ✓ OpenAI API calls - LLM interactions")
    print()
    print("💡 No API key needed for local deployment!")
    print()
    print("🌐 Phoenix UI will be available at: http://localhost:6006")
    print()
    print("Press Ctrl+C to stop the server")
    print("=" * 60)
    print()
    
    try:
        # Run Phoenix server
        subprocess.run(
            [sys.executable, "-m", "phoenix.server.main", "serve"],
            check=True
        )
    except KeyboardInterrupt:
        print("\n\n👋 Phoenix server stopped")
    except subprocess.CalledProcessError as e:
        print(f"\n❌ Error starting Phoenix: {e}")
        print("\nMake sure Phoenix is installed:")
        print("  pip install arize-phoenix arize-phoenix-otel")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Unexpected error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
