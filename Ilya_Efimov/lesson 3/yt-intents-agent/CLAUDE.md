# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Quick Start Commands

### Development Setup
```bash
pip install -r requirements.txt
cp .env.example .env
# Edit .env with your API keys
```

### Running the Application
```bash
# One-time analysis (classic mode)
python main.py

# Interactive Telegram bot (recommended for production)  
python simple_bot.py

# Weekly scheduler only
python scheduler.py once         # Check if time to send request
python scheduler.py force        # Force send weekly request
python scheduler.py continuous   # Run hourly checks

# Combined daemon (bot + scheduler)
python daemon.py
```

### Testing Commands
```bash
# Test scheduler
python scheduler.py force

# Test configuration
python -c "from config import validate_config; validate_config()"

# Test YouTube API connection
python -c "from mcp_tools.youtube_api import YouTubeAPIClient; client = YouTubeAPIClient(); print(len(client.get_recent_videos()))"
```

## Architecture Overview

### Core Data Flow
1. **Input**: YouTube channel URLs (any format: @username, /c/name, /channel/UC..., direct Channel ID)
2. **Data Extraction**: YouTube Data API → recent videos → comments
3. **AI Processing**: OpenRouter/GPT-4 classifies comments into Questions vs Insights/Suggestions  
4. **Deduplication**: RapidFuzz groups similar comments (threshold 0.8)
5. **Output**: Markdown reports via Telegram (text or .md files for large reports)

### Multi-Mode Operation System
The project supports 4 operational modes:
- **Classic**: Single analysis via `main.py` using configured channel
- **Interactive Bot**: `simple_bot.py` accepts dynamic YouTube URLs from users
- **Scheduler**: `scheduler.py` sends weekly channel requests every Saturday at 9:00 AM UTC+3, tracks state in `schedule_state.json`
- **Daemon**: `daemon.py` runs bot + scheduler simultaneously

### Dynamic Channel Handling
**Critical**: The bot uses `YouTubeIntentsAgentDynamic` class (in `simple_bot.py`) which creates YouTube API clients with dynamic channel IDs, bypassing the global config. The main `YouTubeIntentsAgent` class uses fixed config values.

### AI Classification Architecture
- **Dual Mode**: Rule-based (fast) or AI-powered (thorough but slower)
- **AI Processing**: Individual comment classification via OpenRouter → GPT-4
- **Performance**: ~100 comments = ~100 API calls = 50-200 seconds
- **Fallback**: Mock data system for testing without API keys

### Telegram Integration
- **Smart Sizing**: Text messages <4000 chars, larger reports as .md files  
- **Direct API**: Uses requests library, not python-telegram-bot for MCP compatibility issues
- **File Naming**: `youtube_analysis_{channel_id}_{timestamp}.md`

## Key Configuration

### Environment Variables (Required)
- `YOUTUBE_API_KEY`: Google YouTube Data API v3 key
- `TELEGRAM_BOT_TOKEN`: Telegram bot token  
- `TELEGRAM_CHAT_ID`: Target chat for reports
- `OPENROUTER_API_KEY`: Only if `USE_AI_CLASSIFICATION=true`

### URL Processing System
The `utils/url_parser.py` handles all YouTube URL formats and automatically resolves @handles to Channel IDs via YouTube API. The `config.py` module transparently converts any input format to internal Channel ID representation.

## MCP Integration Notes
This project integrates with Model Context Protocol (MCP) servers for YouTube and Telegram, but includes direct API fallbacks. The MCP CLI (`mcp --version`) is required for MCP functionality, though the system gracefully degrades to direct API calls.

## State Management
- `schedule_state.json`: Tracks weekly scheduler timing (auto-generated)
- No database required - stateless design with file-based scheduler persistence

## Scheduler Configuration
- **Schedule**: Every Saturday at 9:00 AM UTC+3 (Moscow time)
- **Logic**: Only sends if current time matches Saturday >= 9:00 AM and hasn't sent this week
- **Next Reminder**: Use `python scheduler.py once` to see next scheduled time
- **Force Send**: Use `python scheduler.py force` for immediate testing