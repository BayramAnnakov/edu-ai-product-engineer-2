# YouTube Intents Agent

A Python project that analyzes YouTube comments and sends summaries to Telegram using MCP servers. Now with interactive bot mode and weekly scheduling!

## Features

- Fetches comments from YouTube videos published in the last 7 days
- Classifies comments into Questions vs Insights/Suggestions (rule-based or AI-powered)
- Supports multiple AI models including ChatGPT 4.1 via OpenRouter
- Groups similar comments using fuzzy deduplication (RapidFuzz, threshold 0.8)
- Sends consolidated Markdown report to Telegram
- **NEW:** Interactive Telegram bot for on-demand analysis
- **NEW:** Weekly scheduler for automated channel requests
- **NEW:** Supports any YouTube channel URL format

## Setup

1. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

2. **Configure environment:**
   - Copy `.env.example` to `.env`
   - Fill in your configuration values:
     - `YOUTUBE_CHANNEL_URL`: YouTube channel URL (любой формат - @username, /c/name, /channel/UCxxx, или прямой Channel ID) - optional for bot mode
     - `YOUTUBE_API_KEY`: Your YouTube Data API key
     - `TELEGRAM_BOT_TOKEN`: Your Telegram bot token
     - `TELEGRAM_CHAT_ID`: Target chat ID for reports
     - `OPENROUTER_API_KEY`: Your OpenRouter API key (required only if USE_AI_CLASSIFICATION=true)
     - `USE_AI_CLASSIFICATION`: Set to true for AI-powered classification (optional)
     - `AI_MODEL`: AI model to use (default: openai/gpt-4o-2024-11-20)

3. **Ensure MCP CLI is available:**
   ```bash
   mcp --version
   ```

## Usage Modes

### 1. One-time Analysis (Classic Mode)
```bash
python main.py
```

### 2. Interactive Bot Mode  
```bash
python bot.py
```
The bot responds to:
- `/start` - Welcome message
- `/analyze` - Request channel analysis  
- `/help` - Show help
- Any YouTube URL sent to the bot

### 3. Weekly Scheduler
```bash
# Check if weekly request should be sent
python scheduler.py once

# Force send weekly request (for testing)
python scheduler.py force

# Run continuous scheduler (checks every hour)
python scheduler.py continuous
```

### 4. Combined Daemon Mode (Bot + Scheduler)
```bash
python daemon.py
```
Runs both the interactive bot AND weekly scheduler simultaneously.

## Project Structure

```
yt-intents-agent/
├── main.py              # Entry point (one-time analysis)
├── bot.py               # Interactive Telegram bot
├── scheduler.py         # Weekly scheduler  
├── daemon.py            # Combined bot + scheduler mode
├── config.py            # Configuration management
├── mcp_tools/           # MCP client wrappers
│   ├── youtube.py       # YouTube MCP integration
│   ├── telegram.py      # Telegram MCP integration
│   ├── youtube_api.py   # Direct YouTube API client
│   └── mock_data.py     # Mock data for testing
├── processors/          # Comment processing logic
│   ├── classifier.py    # Comment categorization
│   ├── ai_classifier.py # AI-powered classification
│   └── deduplicator.py  # Fuzzy grouping
├── utils/               # Utility functions
│   └── url_parser.py    # YouTube URL parsing
├── requirements.txt     # Dependencies
├── schedule_state.json  # Scheduler state (auto-generated)
└── .env.example         # Environment template
```

## Configuration Options

- `DAYS_TO_ANALYZE`: Number of days back to analyze (default: 7)
- `MAX_COMMENTS_PER_VIDEO`: Maximum comments per video (default: 200)
- `SIMILARITY_THRESHOLD`: Fuzzy matching threshold (default: 0.8)

## Supported YouTube URL Formats

The app automatically extracts Channel ID from any of these formats:

```bash
# New handle format (@username)
https://www.youtube.com/@Natalya_Zubareva

# Direct channel URL
https://www.youtube.com/channel/UC4YDSeYyULq_zcztYWuQeuQ

# Custom name format  
https://www.youtube.com/c/ChannelName

# Legacy username format
https://www.youtube.com/user/username

# Direct Channel ID
UC4YDSeYyULq_zcztYWuQeuQ
```

Just paste any YouTube channel URL into `YOUTUBE_CHANNEL_URL` and the app will automatically find the correct Channel ID!

## MCP Servers Used

1. **YouTube MCP**: https://server.smithery.ai/@xianxx17/my-youtube-mcp-server
   - Tools: `search_videos`, `get-video-comments`

2. **Telegram MCP**: https://server.smithery.ai/@NexusX-MCP/telegram-mcp-server
   - Auto-detects appropriate send message tool