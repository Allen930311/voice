"""Entry point for the voicebox backend.

Imports the configured FastAPI app and provides a ``python -m backend.main``
entry point for development.
"""

import argparse
import uvicorn
import os
import sys

# We move the import inside the startup logic to ensure environment variables are set
# BEFORE any backend-specific logic is triggered in the app module.

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="voicebox backend server")
    parser.add_argument(
        "--host",
        type=str,
        default="127.0.0.1",
        help="Host to bind to (use 0.0.0.0 for remote access)",
    )
    parser.add_argument(
        "--port",
        type=int,
        default=8000,
        help="Port to bind to",
    )
    parser.add_argument(
        "--data-dir",
        type=str,
        default=None,
        help="Data directory for database, profiles, and generated audio",
    )
    parser.add_argument(
        "--backend",
        type=str,
        default=None,
        help="Force backend type (e.g., openvino, pytorch, mlx)",
    )
    args = parser.parse_args()

    if args.backend:
        os.environ["VOICEBOX_BACKEND"] = args.backend
        print(f"DEBUG: Manually setting VOICEBOX_BACKEND={args.backend}")

    # Set some sensible defaults for Windows OpenVINO performance
    if os.environ.get("VOICEBOX_BACKEND") == "openvino":
        os.environ["VOICEBOX_BACKEND_VARIANT"] = "openvino"
        # Ensure we don't have buffering issues in tools
        os.environ["PYTHONUNBUFFERED"] = "1"

    from . import config, database
    if args.data_dir:
        config.set_data_dir(args.data_dir)

    database.init_db()

    # Import the app ONLY after environment variables are configured
    from .app import app
    
    print(f"Starting server with backend: {os.environ.get('VOICEBOX_BACKEND', 'auto')}")

    uvicorn.run(
        app, # Use the app object directly to avoid re-importing and losing env vars
        host=args.host,
        port=args.port,
        reload=False,
    )
