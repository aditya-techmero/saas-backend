#!/usr/bin/env python3
"""
Quick start script for Featured Image Generator
This script handles everything needed to get started
"""
import subprocess
import sys
import os
from pathlib import Path

def main():
    """Quick start the Featured Image Generator"""
    print("🚀 Featured Image Generator - Quick Start")
    print("=" * 50)
    
    # Check if we're in the right directory
    if not Path("main.py").exists():
        print("❌ Error: main.py not found")
        print("💡 Make sure you're in the featured-image-generator directory")
        sys.exit(1)
    
    # Run setup
    print("1️⃣ Running setup...")
    try:
        subprocess.run([sys.executable, "setup.py"], check=True)
    except subprocess.CalledProcessError:
        print("❌ Setup failed")
        sys.exit(1)
    
    # Start the server
    print("\n2️⃣ Starting the server...")
    print("🌐 Server will be available at: http://localhost:8000")
    print("📖 API docs will be available at: http://localhost:8000/docs")
    print("🔄 Press Ctrl+C to stop the server")
    print("\n" + "=" * 50)
    
    try:
        subprocess.run([sys.executable, "run_server.py"])
    except KeyboardInterrupt:
        print("\n👋 Server stopped")
    except Exception as e:
        print(f"❌ Error starting server: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
