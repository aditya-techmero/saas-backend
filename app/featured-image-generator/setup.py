#!/usr/bin/env python3
"""
Setup script for Featured Image Generator
This script sets up the environment and installs dependencies
"""
import os
import sys
import subprocess
from pathlib import Path

def check_python_version():
    """Check if Python version is compatible"""
    if sys.version_info < (3, 8):
        print("❌ Python 3.8+ is required")
        print(f"   Current version: {sys.version}")
        return False
    
    print(f"✅ Python version: {sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}")
    return True

def install_dependencies():
    """Install Python dependencies"""
    print("📦 Installing dependencies...")
    
    try:
        # Try pip install
        result = subprocess.run([
            sys.executable, "-m", "pip", "install", "-r", "requirements.txt"
        ], capture_output=True, text=True)
        
        if result.returncode == 0:
            print("✅ Dependencies installed successfully")
            return True
        else:
            print(f"❌ Pip installation failed: {result.stderr}")
            return False
            
    except Exception as e:
        print(f"❌ Error installing dependencies: {e}")
        return False

def check_fonts():
    """Check if Google Fonts are available"""
    fonts_dir = Path("fonts")
    
    required_fonts = [
        "Poppins-Bold.ttf",
        "Poppins-Regular.ttf", 
        "Poppins-SemiBold.ttf",
        "Inter-Bold.ttf",
        "Inter-Regular.ttf"
    ]
    
    print("🔍 Checking Google Fonts...")
    
    if not fonts_dir.exists():
        print("❌ Fonts directory not found")
        return False
    
    missing_fonts = []
    for font in required_fonts:
        if not (fonts_dir / font).exists():
            missing_fonts.append(font)
    
    if missing_fonts:
        print(f"⚠️  Missing fonts: {', '.join(missing_fonts)}")
        print("💡 Run 'python download_fonts.py' to download missing fonts")
        return False
    
    print("✅ All Google Fonts are available")
    return True

def create_example_env():
    """Create example environment file"""
    env_file = Path(".env.example")
    if not env_file.exists():
        env_content = """# Featured Image Generator Environment Variables
# Copy this file to .env and modify as needed

# Server Configuration
HOST=0.0.0.0
PORT=8000
DEBUG=True

# Image Processing
MAX_IMAGE_SIZE=10485760  # 10MB in bytes
QUALITY=85
FORMAT=WEBP

# Font Configuration
FONT_DIR=fonts
DEFAULT_FONT_SIZE=32
TITLE_FONT_SIZE=55
"""
        env_file.write_text(env_content)
        print("✅ Created .env.example file")

def main():
    """Main setup function"""
    print("🚀 Setting up Featured Image Generator")
    print("=" * 50)
    
    # Check Python version
    if not check_python_version():
        sys.exit(1)
    
    # Install dependencies
    if not install_dependencies():
        print("❌ Setup failed: Could not install dependencies")
        sys.exit(1)
    
    # Check fonts
    fonts_available = check_fonts()
    
    # Create example environment
    create_example_env()
    
    print("\n🎉 Setup complete!")
    print("=" * 50)
    print("📁 Project structure:")
    print("   ├── main.py              # Main API application")
    print("   ├── run_server.py        # Server startup script")
    print("   ├── example.py           # Usage example")
    print("   ├── requirements.txt     # Dependencies")
    print("   ├── fonts/               # Google Fonts directory")
    print("   └── README.md            # Documentation")
    
    print("\n🚀 Next steps:")
    print("1. Start the server: python run_server.py")
    print("2. Test the API: python example.py")
    print("3. Visit: http://localhost:8000/docs")
    
    if not fonts_available:
        print("\n💡 Optional: Download Google Fonts with: python download_fonts.py")
    
    print("\n✨ Your Featured Image Generator is ready!")

if __name__ == "__main__":
    main()
