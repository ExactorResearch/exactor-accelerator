"""
Launcher for Exactor Engram Associative Memory Web Server & REST API.
"""

import os
import sys
import uvicorn

try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

# Ensure package is on sys.path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))


def main():
    host = os.environ.get("HOST", "127.0.0.1")
    port = int(os.environ.get("PORT", 8080))
    print("=" * 75)
    print(f" 🧠 EXACTOR ENGRAM MEMORY - Memoria Asociativa Determinista")
    print(f" Dashboard interactivo: http://{host}:{port}")
    print(f" Documentación OpenAPI: http://{host}:{port}/docs")
    print("=" * 75)

    uvicorn.run(
        "exactor_engram.api.server:app",
        host=host,
        port=port,
        reload=False,
        log_level="info",
    )


if __name__ == "__main__":
    main()
