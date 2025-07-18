# MBank Reviews Analysis

This project analyzes MBank mobile app reviews from Google Play Store using hybrid summarization techniques (extractive and abstractive). It combines deterministic methods with GPT-4 to provide comprehensive review insights.

## Features

- **Google Play Store Scraping**: Automatically fetch app reviews
- **Hybrid Summarization**: 
  - Extractive: Uses LexRank algorithm for deterministic summaries
  - Abstractive: Uses GPT-4 for human-like summaries
- **Comparative Analysis**: Evaluates and compares both summarization methods
- **Read-Only Dashboard**: Streamlit-based web interface for visualization
- **CLI-Based Analysis**: Analysis is performed via command line interface
- **Export Capabilities**: Save results in JSON format

## Requirements

- Python 3.8+
- OpenAI API key
- Internet connection for Google Play Store scraping

## Quick Start

### Option 1: Automated Setup (Recommended)

```bash
# 1. Set up environment
cp .env.example .env
# Edit .env and add your OpenAI API key

# 2. Run complete analysis and dashboard
python start.py                    # Default 100 reviews
python start.py --count 50         # Analyze 50 reviews  
python start.py --count 200        # Analyze 200 reviews
python start.py --force-new        # Force new analysis
python start.py --no-dashboard     # Analysis only, no dashboard
```

### Option 2: Step-by-Step

```bash
# 1. Install dependencies
pip install -r requirements.txt

# 2. Set up environment
cp .env.example .env
# Edit .env file with your OpenAI API key

# 3. Run analysis
python main.py analyze --app-id com.maanavan.mb_kyrgyzstan --count 100

# 4. Start dashboard
python run_dashboard.py
```

## Usage

### Command Line Interface

```bash
# Run full analysis
python main.py analyze --app-id com.example.app --count 100 --openai-key your_key

# Analyze existing reviews
python main.py analyze-existing --reviews-file data.json --openai-key your_key

# Validate setup
python main.py validate --openai-key your_key
```

### Dashboard Interface

The dashboard is **read-only** and displays analysis results:

1. **No Analysis**: Shows instructions screen
2. **Analysis Complete**: Shows all visualization features

```bash
# Option 1: Use start script (handles everything)
python start.py

# Option 2: Manual steps
python main.py analyze  # First run analysis
python run_dashboard.py # Then start dashboard

# Option 3: View dashboard without data
python run_dashboard.py --force
```

### Dashboard Features

#### Read-Only Display:
- **Overview**: Review statistics and analysis summary
- **Summary Comparison**: Side-by-side extractive vs abstractive summaries
- **Reviews Table**: Searchable and filterable review data
- **Analytics**: Interactive charts and visualizations
- **Status Sidebar**: Shows current data status and metadata

#### Analysis Instructions:
- **Setup Guidance**: Clear CLI commands for running analysis
- **No File Upload**: All data loading is from standard files
- **No Web Analysis**: Analysis must be run via command line

## Project Structure

```
MBank-Reviews-Analysis/
├── src/                    # Modular source code
│   ├── config/            # Configuration management
│   ├── models/            # Data models
│   ├── services/          # Business logic
│   ├── ui/                # UI components
│   └── utils/             # Utilities
├── dashboard.py           # Read-only dashboard
├── main.py               # CLI interface
├── start.py              # Automated startup
├── run_dashboard.py      # Dashboard launcher with checks
├── results/              # Output files directory
│   ├── README.md         # Results documentation
│   ├── mbank_reviews.json # Generated review data
│   └── summary_comparison_results.json # Analysis results
├── .env.example          # Environment template
└── ARCHITECTURE.md       # Technical documentation
```

## Configuration

### Environment Variables (.env)
```bash
OPENAI_API_KEY=your_openai_api_key_here
OPENAI_MODEL=gpt-4
OPENAI_MAX_TOKENS=500
OPENAI_TEMPERATURE=0.3
```

### Application Settings
Key parameters in `src/config/settings.py`:
- Default app ID and review counts
- Summarization parameters
- UI configuration

## Analysis Methods

### Extractive Summarization
- **Algorithm**: LexRank
- **Language**: Russian
- **Approach**: Selects most representative sentences
- **Benefits**: Deterministic, preserves original text

### Abstractive Summarization  
- **Model**: OpenAI GPT-4
- **Temperature**: 0.3 for consistency
- **Approach**: Generates human-like summaries
- **Benefits**: Context-aware, natural language

### Evaluation Metrics
- **Content Overlap**: Shared vocabulary between summaries
- **Length Ratio**: Relative summary lengths
- **Readability**: Text complexity assessment
- **GPT-4 Evaluation**: Automated quality comparison

## Workflow

### CLI-First Approach
1. **Analysis Execution**: All analysis performed via command line
2. **Data Generation**: Creates standard JSON files with results
3. **Dashboard Launch**: Read-only visualization of results
4. **Clear Separation**: Analysis logic separate from presentation
5. **Reanalysis**: Re-run CLI commands to update data

### File Dependencies
- `results/mbank_reviews.json`: Raw scraped review data with metadata
- `results/summary_comparison_results.json`: Complete analysis results

All output files are automatically saved in the `results/` directory to keep the project root clean and organized.

### Logging and Progress Tracking

The system provides detailed logging throughout the analysis process:

#### Review Scraping Progress:
- App information fetching
- Batch-by-batch review downloading
- Review parsing and validation
- Success/failure statistics

#### Analysis Progress:
- Step-by-step workflow tracking
- Processing times for each summary type
- Comparison metrics calculation
- File save operations

#### Example Log Output:
```
INFO - Starting review scraping for app: com.maanavan.mb_kyrgyzstan
INFO - Target count: 50, language: ru, country: kg
INFO - App found: MBank
INFO - Using single batch mode for 50 reviews
INFO - Fetched 50 reviews in single batch
INFO - Review parsing completed:
INFO -   - Valid reviews: 48
INFO -   - Invalid reviews: 2
INFO -   - Success rate: 96.0%
```

## Technical Stack

- **Architecture**: Clean, modular, service-oriented
- **Web Scraping**: google-play-scraper with detailed progress logging
- **NLP Processing**: NLTK, sumy
- **AI/ML**: OpenAI GPT-4 API
- **Web Interface**: Streamlit (read-only dashboard)
- **Visualization**: Plotly
- **Data Format**: JSON
- **Logging**: Comprehensive logging with review parsing progress
- **CLI**: Rich argument parsing with flexible options

## Troubleshooting

### Common Issues

1. **Dashboard shows instructions screen**
   ```bash
   # Analysis not complete - run analysis first
   python main.py analyze
   # OR use automated setup
   python start.py
   ```

2. **Missing OpenAI API Key**
   ```bash
   cp .env.example .env
   # Edit .env and add OPENAI_API_KEY=your_key
   ```

3. **Dashboard won't start**
   ```bash
   # Check if analysis is complete
   python main.py validate
   
   # Force start dashboard
   python run_dashboard.py --force
   ```

4. **Analysis fails**
   ```bash
   # Check API key and internet connection
   python main.py validate --openai-key your_key
   ```

## Best Practices

1. **Analysis via CLI only** - Dashboard is read-only
2. **Use .env file** for API key management  
3. **Start with start.py** for new users
4. **Dashboard for visualization** - No editing capabilities
5. **Clear separation** - Analysis logic separate from presentation

## License

This project is for educational and research purposes.