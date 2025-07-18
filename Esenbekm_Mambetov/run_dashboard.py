#!/usr/bin/env python3
"""
Dashboard launcher for MBank Reviews Analysis System.
Provides options to run original or refactored version.
"""

import subprocess
import sys
import argparse
from pathlib import Path


def check_dependencies():
    """Check if required dependencies are installed."""
    try:
        return True
    except ImportError:
        return False


def install_dependencies():
    """Install required dependencies."""
    requirements_file = Path(__file__).parent / "requirements.txt"
    if not requirements_file.exists():
        raise FileNotFoundError("requirements.txt not found")
    
    subprocess.check_call([
        sys.executable, "-m", "pip", "install", "-r", str(requirements_file)
    ])


def run_dashboard(dashboard_file: str, port: int = 8501, host: str = "localhost"):
    """
    Run the Streamlit dashboard.
    
    Args:
        dashboard_file: Path to dashboard file
        port: Port number
        host: Host address
    """
    dashboard_path = Path(__file__).parent / dashboard_file
    
    if not dashboard_path.exists():
        raise FileNotFoundError(f"Dashboard file not found: {dashboard_path}")
    
    try:
        subprocess.run([
            sys.executable, "-m", "streamlit", "run", str(dashboard_path),
            "--server.port", str(port),
            "--server.address", host
        ])
    except KeyboardInterrupt:
        pass


def check_analysis_files():
    """Check if analysis files exist."""
    reviews_file = Path(__file__).parent / "results" / "mbank_reviews.json"
    results_file = Path(__file__).parent / "results" / "summary_comparison_results.json"
    return reviews_file.exists() and results_file.exists()


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Run MBank Reviews Analysis Dashboard"
    )
    parser.add_argument(
        "--port",
        type=int,
        default=8501,
        help="Port number (default: 8501)"
    )
    parser.add_argument(
        "--host",
        default="localhost",
        help="Host address (default: localhost)"
    )
    parser.add_argument(
        "--force",
        action="store_true",
        help="Force run dashboard even without analysis"
    )
    
    args = parser.parse_args()
    
    # Check if analysis is complete (unless forced)
    if not args.force and not check_analysis_files():
        print("⚠️  Данные анализа не найдены!")
        print("📋 Варианты:")
        print("   1. Запустите полный процесс: python start.py")
        print("   2. Выполните анализ: python main.py analyze")
        print("   3. Запустите панель без данных: python run_dashboard.py --force")
        print("")
        print("ℹ️  Панель управления теперь предназначена только для просмотра.")
        print("   Анализ выполняется через командную строку.")
        sys.exit(1)
    
    # Use the main dashboard file
    dashboard_file = "dashboard.py"
    
    try:
        # Check dependencies
        if not check_dependencies():
            install_dependencies()
        
        # Run dashboard
        run_dashboard(dashboard_file, args.port, args.host)
        
    except FileNotFoundError as e:
        sys.exit(f"Error: {e}")
    except subprocess.CalledProcessError:
        sys.exit("Error: Failed to install dependencies")
    except Exception as e:
        sys.exit(f"Error: {e}")


if __name__ == "__main__":
    main()