#!/usr/bin/env python3
"""
Build script for StreamlinkTorGUI
This script will build the application using PyInstaller
"""

import os
import sys
import subprocess
import shutil
from pathlib import Path

def run_command(cmd, description):
    """Run a command and handle errors"""
    print(f"\n{description}")
    print("=" * 50)
    
    try:
        result = subprocess.run(cmd, shell=True, check=True, capture_output=True, text=True)
        print("SUCCESS")
        if result.stdout:
            print(result.stdout)
        return True
    except subprocess.CalledProcessError as e:
        print(f"FAILED: {e}")
        if e.stderr:
            print(f"Error output: {e.stderr}")
        return False

def main():
    print("StreamlinkTorGUI Build Script")
    print("=" * 50)
    
    # Check Python version
    if sys.version_info < (3, 7):
        print("Error: Python 3.7 or higher required")
        sys.exit(1)
    
    print(f"Python version: {sys.version}")
    
    # Install requirements
    if not run_command("pip install -r requirements.txt", "Installing requirements..."):
        print("Failed to install requirements")
        sys.exit(1)
    
    # Clean previous builds
    print("\nCleaning previous builds...")
    for path in ['build', 'dist', '__pycache__']:
        if os.path.exists(path):
            shutil.rmtree(path)
            print(f"Removed {path}")
    
    # Keep our custom .spec file
    if not os.path.exists("streamlink_tor_gui.spec"):
        print("Error: streamlink_tor_gui.spec file not found!")
        print("Make sure the .spec file is in the same directory as this script")
        sys.exit(1)
    
    # Build with PyInstaller
    build_cmd = "pyinstaller streamlink_tor_gui.spec --clean --noconfirm"
    if not run_command(build_cmd, "Building with PyInstaller..."):
        print("Build failed")
        sys.exit(1)
    
    # Check if build was successful
    if sys.platform.startswith('win'):
        exe_path = "dist/StreamlinkTorGUI.exe"
    else:
        exe_path = "dist/StreamlinkTorGUI"
    
    if os.path.exists(exe_path):
        print(f"\nBuild successful! Executable created at: {exe_path}")
        
        # Get file size
        size = os.path.getsize(exe_path)
        size_mb = size / (1024 * 1024)
        print(f"Executable size: {size_mb:.1f} MB")
        
    else:
        print("Build failed - executable not found")
        sys.exit(1)
    
    print("\nBuild completed successfully!")
    print(f"You can find the executable in the 'dist' folder")

if __name__ == "__main__":
    main()