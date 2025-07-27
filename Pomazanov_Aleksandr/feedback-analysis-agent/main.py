#!/usr/bin/env python3
"""
Feedback Analysis Agent CLI

This tool analyzes user feedback from files and generates insights for product teams.
"""

import os
import json
import sys
from pathlib import Path
from typing import Optional

import click
from dotenv import load_dotenv
from rich.console import Console
from rich.table import Table
from rich.progress import track

# Load environment variables
load_dotenv()

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent / "src"))

from src.processors import FileProcessor
from src.analyzers.feedback_analyzer import FeedbackAnalyzer, AnalyzerConfig
from src.generators import InsightGenerator
from src.models.feedback import FeedbackCategory, Sentiment, Priority

console = Console()


def save_json_report(report, output_path: str):
    """Save report as JSON file."""
    # Convert Pydantic models to dict for JSON serialization
    report_dict = json.loads(report.model_dump_json())
    
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(report_dict, f, indent=2, ensure_ascii=False, default=str)


def print_summary_table(report):
    """Print a summary table of the analysis results."""
    table = Table(title="Feedback Analysis Summary")
    
    table.add_column("Metric", style="cyan", no_wrap=True)
    table.add_column("Value", style="magenta")
    
    table.add_row("Total Feedback Items", str(report.total_feedback_items))
    
    # Sentiment breakdown
    for sentiment, percentage in report.overall_sentiment.items():
        table.add_row(f"{sentiment.title()} Sentiment", f"{percentage:.1%}")
    
    # High priority count
    table.add_row("High Priority Items", str(len(report.high_priority_items)))
    
    # Top category
    if report.category_insights:
        top_category = max(report.category_insights, key=lambda x: x.total_count)
        table.add_row("Top Category", f"{top_category.category.value} ({top_category.total_count} items)")
    
    console.print(table)


def print_category_details(report):
    """Print detailed category breakdown."""
    if not report.category_insights:
        return
    
    console.print("\n[bold cyan]Category Breakdown:[/bold cyan]")
    
    for insight in report.category_insights:
        console.print(f"\n[bold]{insight.category.value.upper().replace('_', ' ')}[/bold] ({insight.total_count} items)")
        
        # Sentiment distribution
        console.print("  Sentiment:", end=" ")
        for sentiment, count in insight.sentiment_distribution.items():
            if count > 0:
                console.print(f"{sentiment.value}: {count}", end="  ")
        console.print()
        
        # Top issues
        if insight.top_issues:
            console.print("  Top Issues:")
            for issue in insight.top_issues[:3]:
                console.print(f"    • {issue}")
        
        # Recommendations
        if insight.recommendations:
            console.print("  Recommendations:")
            for rec in insight.recommendations:
                console.print(f"    • {rec}")


def print_high_priority_items(report):
    """Print high priority items that need immediate attention."""
    if not report.high_priority_items:
        return
    
    console.print(f"\n[bold red]High Priority Items ({len(report.high_priority_items)}):[/bold red]")
    
    for i, item in enumerate(report.high_priority_items[:5], 1):  # Show top 5
        console.print(f"\n{i}. [bold]{item.category.value}[/bold] - {item.sentiment.value}")
        console.print(f"   Text: {item.feedback_item.text[:100]}...")
        console.print(f"   Summary: {item.summary}")
        if item.actionable_items:
            console.print(f"   Action: {item.actionable_items[0]}")


@click.group()
def cli():
    """Feedback Analysis Agent - Analyze user feedback and generate insights."""
    pass


@cli.command()
@click.argument('input_file', type=click.Path(exists=True))
@click.option('--output', '-o', help='Output JSON file path')
@click.option('--model', default='gpt-4', help='LLM model to use (default: gpt-4)')
@click.option('--provider', default='openai', type=click.Choice(['openai', 'anthropic']), 
              help='LLM provider (default: openai)')
@click.option('--verbose', '-v', is_flag=True, help='Verbose output')
def analyze(input_file: str, output: Optional[str], model: str, provider: str, verbose: bool):
    """Analyze feedback from a file and generate insights."""
    
    try:
        console.print(f"[bold green]Analyzing feedback from:[/bold green] {input_file}")
        
        # Initialize components
        file_processor = FileProcessor()
        
        # Setup analyzer config
        analyzer_config = AnalyzerConfig(
            model_provider=provider,
            model_name=model,
        )
        
        analyzer = FeedbackAnalyzer(analyzer_config)
        insight_generator = InsightGenerator()
        
        # Process file
        console.print("[yellow]Reading feedback data...[/yellow]")
        feedback_items = file_processor.process_file(input_file)
        
        if not feedback_items:
            console.print("[red]No feedback items found in the file.[/red]")
            return
        
        console.print(f"Found {len(feedback_items)} feedback items")
        
        # Analyze feedback
        console.print("[yellow]Analyzing feedback...[/yellow]")
        analysis_results = []
        
        for item in track(feedback_items, description="Processing..."):
            try:
                result = analyzer.analyze_feedback(item)
                analysis_results.append(result)
            except Exception as e:
                if verbose:
                    console.print(f"[red]Error analyzing item {item.id}: {e}[/red]")
                continue
        
        if not analysis_results:
            console.print("[red]Failed to analyze any feedback items.[/red]")
            return
        
        # Generate insights
        console.print("[yellow]Generating insights...[/yellow]")
        report = insight_generator.generate_report(analysis_results)
        
        # Save report if output path specified
        if output:
            save_json_report(report, output)
            console.print(f"[green]Report saved to:[/green] {output}")
        
        # Display results
        console.print("\n" + "="*50)
        print_summary_table(report)
        
        console.print(f"\n[bold cyan]Executive Summary:[/bold cyan]")
        console.print(report.executive_summary)
        
        if verbose:
            print_category_details(report)
            print_high_priority_items(report)
        
        # Show key themes
        if report.key_themes:
            console.print(f"\n[bold cyan]Key Themes:[/bold cyan]")
            for theme in report.key_themes:
                console.print(f"  • {theme}")
        
    except Exception as e:
        console.print(f"[red]Error: {e}[/red]")
        if verbose:
            import traceback
            console.print(traceback.format_exc())
        sys.exit(1)


@cli.command()
@click.option('--provider', default='openai', type=click.Choice(['openai', 'anthropic']))
def test_connection(provider: str):
    """Test connection to LLM provider."""
    try:
        config = AnalyzerConfig(model_provider=provider)
        analyzer = FeedbackAnalyzer(config)
        
        # Test with dummy feedback
        from src.models.feedback import FeedbackItem
        test_item = FeedbackItem(text="This is a test feedback")
        
        console.print(f"Testing connection to {provider}...")
        result = analyzer.analyze_feedback(test_item)
        
        console.print(f"[green]✓ Connection successful![/green]")
        console.print(f"Test analysis result: {result.category.value}, {result.sentiment.value}")
        
    except Exception as e:
        console.print(f"[red]✗ Connection failed: {e}[/red]")
        sys.exit(1)


@cli.command()
def create_sample():
    """Create sample feedback files for testing."""
    sample_data = [
        "The app crashes every time I try to upload a photo. Very frustrating!",
        "Love the new interface design, much cleaner and easier to use.",
        "Loading times are really slow, especially on mobile devices.",
        "Would be great to have a dark mode option for night usage.",
        "The search function doesn't work properly, can't find anything.",
        "Excellent customer support, resolved my issue quickly.",
        "App is buggy and freezes frequently. Needs serious fixes.",
        "Great features overall, but could use better navigation.",
        "Performance has improved significantly after the last update.",
        "Missing important features compared to competitors."
    ]
    
    # Create sample text file
    os.makedirs("data", exist_ok=True)
    
    with open("data/sample_feedback.txt", "w", encoding="utf-8") as f:
        for feedback in sample_data:
            f.write(feedback + "\n")
    
    # Create sample CSV
    import pandas as pd
    df = pd.DataFrame({
        'feedback': sample_data,
        'user_id': [f'user_{i+1}' for i in range(len(sample_data))],
        'timestamp': ['2024-01-01'] * len(sample_data)
    })
    df.to_csv("data/sample_feedback.csv", index=False)
    
    # Create sample JSON
    json_data = [
        {"text": feedback, "user_id": f"user_{i+1}", "timestamp": "2024-01-01"}
        for i, feedback in enumerate(sample_data)
    ]
    
    with open("data/sample_feedback.json", "w", encoding="utf-8") as f:
        json.dump(json_data, f, indent=2, ensure_ascii=False)
    
    console.print("[green]Sample files created in 'data/' directory:[/green]")
    console.print("  • sample_feedback.txt")
    console.print("  • sample_feedback.csv") 
    console.print("  • sample_feedback.json")


if __name__ == '__main__':
    cli()