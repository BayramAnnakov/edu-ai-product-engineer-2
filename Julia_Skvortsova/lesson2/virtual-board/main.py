"""
Main entry point for Virtual Board using OpenAI Agents SDK
"""
import asyncio
import os
from pathlib import Path
from openai import AsyncOpenAI
from dotenv import load_dotenv
from agents import set_default_openai_key

from src.config import load_config
from src.virtual_board_agents.orchestrator import VirtualBoardOrchestrator


async def main():
    """Run Virtual Board session with SDK agents"""
    # Load environment variables
    load_dotenv()
    
    # Set OpenAI key for Agents SDK
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        raise ValueError("OPENAI_API_KEY environment variable not set")
    
    set_default_openai_key(api_key)
    
    # Load configuration
    config_path = Path("config/board_config.yml")
    if not config_path.exists():
        print(f"❌ Config file not found: {config_path}")
        print("Creating example config...")
        create_example_config()
        print(f"✅ Created {config_path}. Please edit it and run again.")
        return
    
    config = load_config(str(config_path))
    print(f"✅ Loaded config: {config.product.name}")
    
    # Create and run orchestrator
    orchestrator = VirtualBoardOrchestrator(config)
    
    try:
        report = await orchestrator.run_session()
        
        # Print summary
        print("\n" + "="*60)
        print("📊 SESSION SUMMARY")
        print("="*60)
        print(f"Duration: {(report.end_time - report.start_time).total_seconds():.1f}s")
        print(f"Coverage: {report.coverage_achieved:.0%}")
        print(f"\n🔍 Key Insights:")
        for insight in report.key_insights:
            print(f"  • {insight}")
        print(f"\n💡 Recommendations:")
        for rec in report.recommendations:
            print(f"  • {rec}")
        print("="*60)
        
    except Exception as e:
        print(f"\n❌ Session failed: {e}")
        import traceback
        traceback.print_exc()


def create_example_config():
    """Create an example configuration file"""
    example_config = """# Virtual Board Configuration using OpenAI Agents SDK

product:
  name: "AI Code Assistant"
  description: "An AI-powered coding assistant that helps developers write better code faster"

hypotheses:
  - id: "h1"
    description: "Developers struggle with understanding complex codebases"
  - id: "h2"
    description: "AI assistance can significantly speed up development"
  - id: "h3"
    description: "Developers are willing to pay for AI coding tools"

personas:
  - id: "p1"
    name: "Sarah"
    background: "Senior full-stack developer at a startup, 8 years experience, uses VS Code"
  - id: "p2"
    name: "Mike"
    background: "Junior developer learning Python, 2 years experience, self-taught"
  - id: "p3"
    name: "Elena"
    background: "Tech lead at enterprise company, 12 years experience, focuses on Java"

phase_config:
  diverge:
    main_questions:
      - "What are your biggest pain points when working with code?"
      - "How do you currently handle code documentation and understanding?"
      - "What would an ideal AI coding assistant do for you?"
    max_follow_ups: 2
  reflect:
    share_raw_answers: false
    share_synthesized_themes: true
  converge:
    force_tradeoffs: true
    ranking_method: "points"

policy:
  min_personas: 3
  max_personas: 5
  target_coverage: 0.8
  allow_early_convergence: true
"""
    
    config_dir = Path("config")
    config_dir.mkdir(exist_ok=True)
    
    config_path = config_dir / "board_config.yml"
    with open(config_path, 'w') as f:
        f.write(example_config)


if __name__ == "__main__":
    asyncio.run(main())