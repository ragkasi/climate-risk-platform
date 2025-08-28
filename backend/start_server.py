#!/usr/bin/env python3
"""
Simple server startup script for development.
"""

import uvicorn
from app.main import create_app

if __name__ == "__main__":
    app = create_app()
    uvicorn.run(app, host="0.0.0.0", port=8000, reload=True)
