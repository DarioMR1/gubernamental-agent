#!/usr/bin/env python3
"""Quick development server launcher."""

import sys
from pathlib import Path

# Add src to Python path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root / "src"))

# Import and run the development server
from src.api.main import run_dev_server

if __name__ == "__main__":
    print("🚀 Starting Governmental Agent API Development Server...")
    print("📚 API Documentation: http://localhost:8000/docs")
    print("🔄 Auto-reload enabled")
    print("🛑 Press Ctrl+C to stop")
    print("-" * 50)
    
    try:
        run_dev_server()
    except KeyboardInterrupt:
        print("\n👋 Server stopped")
    except Exception as e:
        print(f"\n❌ Server failed to start: {e}")
        sys.exit(1)