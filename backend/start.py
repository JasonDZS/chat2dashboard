#!/usr/bin/env python3
import subprocess
import sys
import os

def install_requirements():
    """Install required packages"""
    try:
        subprocess.check_call([sys.executable, "-m", "pip", "install", "-r", "requirements.txt"])
        print("✅ Requirements installed successfully!")
    except subprocess.CalledProcessError as e:
        print(f"❌ Error installing requirements: {e}")
        return False
    return True

def start_server():
    """Start the FastAPI server"""
    try:
        print("🚀 Starting Data Visualization Agent...")
        print("📊 Server will be available at: http://localhost:8000")
        print("⭐ Press Ctrl+C to stop the server")
        subprocess.run([sys.executable, "main.py"])
    except KeyboardInterrupt:
        print("\n👋 Server stopped.")
    except Exception as e:
        print(f"❌ Error starting server: {e}")

if __name__ == "__main__":
    print("🎨 Data Visualization Agent Setup")
    print("=" * 40)
    
    if install_requirements():
        start_server()
    else:
        print("❌ Setup failed. Please check the error messages above.")
        sys.exit(1)