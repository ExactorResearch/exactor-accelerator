"""
Launcher for EXACTOR + Jev Web Server and API.
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
    port = int(os.environ.get("PORT", 8000))
    print("=" * 70)
    print(f" Starting EXACTOR + JEV server at http://{host}:{port}")
    print(" Web Dashboard available at http://localhost:8000")
    print(" Swagger OpenAPI documentation at http://localhost:8000/docs")
    print("=" * 70)

    uvicorn.run(
        "exactor_accelerator.api.server:app",
        host=host,
        port=port,
        reload=False,
        log_level="info",
    )


if __name__ == "__main__":
    main()
