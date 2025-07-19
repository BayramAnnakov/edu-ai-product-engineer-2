#!/usr/bin/env python3
"""
Streamlit App Launcher
"""

import subprocess
import os
import sys

def main():
    """Launch Streamlit app with correct path configuration"""
    
    # Set up path
    current_dir = os.path.dirname(os.path.abspath(__file__))
    os.chdir(current_dir)
    
    # Add current directory to Python path
    if current_dir not in sys.path:
        sys.path.insert(0, current_dir)
    
    # Launch Streamlit
    streamlit_app_path = os.path.join(current_dir, "src", "ui", "streamlit_app.py")
    
    print(f"🚀 Launching Streamlit app from: {streamlit_app_path}")
    print(f"📁 Working directory: {current_dir}")
    
    subprocess.run([
        sys.executable, "-m", "streamlit", "run", streamlit_app_path
    ])

if __name__ == "__main__":
    main()