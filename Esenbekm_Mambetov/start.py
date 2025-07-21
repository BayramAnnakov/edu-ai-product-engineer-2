#!/usr/bin/env python3
"""
Start script for MBank Reviews Analysis System.
Ensures analysis is completed before running dashboard.
"""

import sys
import os
import subprocess
import argparse

# Add src to path
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

from src.config.settings import AppConfig, get_openai_config
from src.services.data_service import DataService
from src.utils.logger import Logger


def check_analysis_status():
    """Check if analysis has been completed."""
    data_service = DataService()
    has_reviews = data_service.file_exists(AppConfig.DEFAULT_REVIEWS_FILE)
    has_results = data_service.file_exists(AppConfig.DEFAULT_RESULTS_FILE)
    return has_reviews and has_results


def check_openai_config():
    """Check if OpenAI is configured."""
    config = get_openai_config()
    return config.get('api_key') is not None


def run_analysis(review_count=None):
    """Run analysis using the CLI."""
    logger = Logger.setup_logger()
    
    count = review_count or AppConfig.DEFAULT_REVIEW_COUNT
    
    print(f"🚀 Запуск анализа отзывов (количество: {count})...")
    logger.info(f"Starting analysis with {count} reviews")
    
    if not check_openai_config():
        print("❌ OpenAI API ключ не найден.")
        print("📝 Создайте .env файл с вашим API ключом:")
        print("   cp .env.example .env")
        print("   # Отредактируйте .env и добавьте OPENAI_API_KEY=your_key")
        logger.error("OpenAI API key not found")
        return False
    
    logger.info("OpenAI configuration validated")
    
    try:
        print("📊 Выполняется анализ...")
        print("   - Загрузка отзывов из Google Play")
        print("   - Создание извлекающих резюме")
        print("   - Генерация абстрактивных резюме с GPT-4")
        print("   - Сравнение и оценка результатов")
        
        logger.info("Starting subprocess for analysis")
        result = subprocess.run([
            sys.executable, "main.py", "analyze",
            "--app-id", AppConfig.DEFAULT_APP_ID,
            "--count", str(count)
        ], check=True, capture_output=True, text=True)
        
        # Log subprocess output
        if result.stdout:
            logger.info(f"Analysis stdout: {result.stdout}")
        if result.stderr:
            logger.warning(f"Analysis stderr: {result.stderr}")
        
        print("✅ Анализ завершен успешно!")
        logger.info("Analysis completed successfully")
        return True
        
    except subprocess.CalledProcessError as e:
        print(f"❌ Ошибка при выполнении анализа: {e}")
        print(f"Код возврата: {e.returncode}")
        if e.stdout:
            print(f"Вывод: {e.stdout}")
        if e.stderr:
            print(f"Ошибки: {e.stderr}")
        
        logger.error(f"Analysis failed with return code {e.returncode}")
        logger.error(f"stdout: {e.stdout}")
        logger.error(f"stderr: {e.stderr}")
        return False


def run_dashboard():
    """Run the dashboard."""
    print("🌐 Запуск панели управления...")
    try:
        subprocess.run([sys.executable, "run_dashboard.py"])
    except KeyboardInterrupt:
        print("\n🛑 Панель управления остановлена")


def main():
    """Main workflow."""
    parser = argparse.ArgumentParser(
        description="MBank Reviews Analysis System - Complete Workflow",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python start.py                    # Default 100 reviews
  python start.py --count 50         # Analyze 50 reviews
  python start.py --count 200        # Analyze 200 reviews
  python start.py --force-new        # Force new analysis
        """
    )
    
    parser.add_argument(
        '--count',
        type=int,
        default=AppConfig.DEFAULT_REVIEW_COUNT,
        help=f'Number of reviews to analyze (default: {AppConfig.DEFAULT_REVIEW_COUNT})'
    )
    
    parser.add_argument(
        '--force-new',
        action='store_true',
        help='Force new analysis even if data exists'
    )
    
    parser.add_argument(
        '--no-dashboard',
        action='store_true',
        help='Run analysis only, skip dashboard'
    )
    
    args = parser.parse_args()
    
    # Setup logging
    logger = Logger.setup_logger()
    
    print("="*60)
    print("📊 MBank Reviews Analysis System")
    print("="*60)
    
    logger.info(f"Starting with parameters: count={args.count}, force_new={args.force_new}, no_dashboard={args.no_dashboard}")
    
    # Check if analysis is already complete
    analysis_exists = check_analysis_status()
    
    if analysis_exists and not args.force_new:
        print("✅ Анализ уже выполнен")
        print(f"📊 Параметры: {args.count} отзывов")
        
        if not args.no_dashboard:
            response = input("🔄 Хотите запустить новый анализ? (y/N): ").lower()
        else:
            response = 'y'
        
        if response in ['y', 'yes', 'да']:
            # Remove existing files
            try:
                if os.path.exists(AppConfig.DEFAULT_REVIEWS_FILE):
                    os.remove(AppConfig.DEFAULT_REVIEWS_FILE)
                    logger.info("Removed existing reviews file")
                if os.path.exists(AppConfig.DEFAULT_RESULTS_FILE):
                    os.remove(AppConfig.DEFAULT_RESULTS_FILE)
                    logger.info("Removed existing results file")
                print("🗑️ Существующие файлы удалены")
            except Exception as e:
                print(f"⚠️ Ошибка при удалении файлов: {e}")
                logger.error(f"Error removing files: {e}")
            
            # Run new analysis
            if not run_analysis(args.count):
                return
        else:
            print("📊 Используются существующие результаты анализа")
            logger.info("Using existing analysis results")
    else:
        if args.force_new:
            print("🔄 Принудительный запуск нового анализа...")
            logger.info("Forced new analysis requested")
        else:
            print("⏳ Анализ не выполнен. Запуск анализа...")
            logger.info("No existing analysis found, starting new analysis")
        
        if not run_analysis(args.count):
            return
    
    if not args.no_dashboard:
        print("\n" + "="*60)
        print("🎯 Анализ готов! Запуск панели управления...")
        print("📊 URL: http://localhost:8501")
        print("🔄 Для остановки нажмите Ctrl+C")
        print("="*60)
        
        # Run dashboard
        run_dashboard()
    else:
        print("\n" + "="*60)
        print("✅ Анализ завершен!")
        print("📊 Результаты сохранены в JSON файлы")
        print("🌐 Для просмотра запустите: python run_dashboard.py")
        print("="*60)
        logger.info("Analysis completed, dashboard skipped")


if __name__ == "__main__":
    main()