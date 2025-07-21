# MBank Reviews Analysis - Refactored Architecture

## Overview

This document describes the refactored architecture of the MBank Reviews Analysis System, which implements best practices for code organization, separation of concerns, and maintainability.

## Project Structure

```
EDU_PROJECT_AI/
├── src/                          # Main source code package
│   ├── __init__.py
│   ├── config/                   # Configuration and settings
│   │   ├── __init__.py
│   │   └── settings.py           # Application configuration
│   ├── models/                   # Data models and structures
│   │   ├── __init__.py
│   │   ├── review.py             # Review data models
│   │   └── summary.py            # Summary and comparison models
│   ├── services/                 # Business logic services
│   │   ├── __init__.py
│   │   ├── analysis_service.py   # Main orchestrator service
│   │   ├── data_service.py       # Data loading/saving operations
│   │   ├── scraper_service.py    # Google Play Store scraping
│   │   └── summarization_service.py  # Text summarization logic
│   ├── ui/                       # User interface components
│   │   ├── __init__.py
│   │   └── components.py         # Reusable UI components
│   └── utils/                    # Utility functions
│       ├── __init__.py
│       ├── charts.py             # Chart creation utilities
│       └── logger.py             # Logging configuration
├── dashboard.py                 # Read-only dashboard
├── main.py                     # CLI interface
├── run_dashboard.py            # Dashboard launcher
├── results/                    # Output files directory
│   ├── README.md               # Results documentation
│   ├── mbank_reviews.json      # Generated review data
│   └── summary_comparison_results.json # Analysis results
├── .env.example                # Environment variables template
└── .gitignore                  # Git ignore file
```

## Architecture Principles

### 1. Separation of Concerns
- **Models**: Pure data structures with validation
- **Services**: Business logic and external integrations  
- **UI**: Presentation layer components
- **Utils**: Shared utilities and helpers
- **Config**: Centralized configuration management

### 2. Clean Code Practices
- ✅ Removed all `print()` statements
- ✅ Replaced with proper logging
- ✅ Added comprehensive docstrings
- ✅ Type hints throughout
- ✅ Error handling with try/catch blocks
- ✅ No hardcoded magic numbers or strings

### 3. Modular Design
- Each service has a single responsibility
- Easy to test individual components
- Pluggable architecture for different summarization methods
- Clear dependencies between layers

## Key Components

### Configuration Layer (`src/config/`)

**`settings.py`**
- Centralized application configuration
- Environment variable handling
- UI styling constants
- API configuration templates

### Data Models (`src/models/`)

**`review.py`**
- `Review`: Individual review data structure
- `ReviewsData`: Container for reviews with metadata
- `ReviewsMetadata`: Scraping metadata

**`summary.py`**
- `SummaryResult`: Individual summary results
- `ComparisonMetrics`: Metrics for comparing summaries
- `ComparisonResult`: Complete analysis results

### Services Layer (`src/services/`)

**`analysis_service.py`** - Main orchestrator
- Coordinates the entire analysis workflow
- Manages data flow between components
- Provides high-level API for analysis operations

**`scraper_service.py`** - Google Play scraping
- Handles Google Play Store API interactions
- Pagination and error handling
- Data validation and cleaning

**`summarization_service.py`** - Text processing
- `ExtractiveService`: Deterministic summarization
- `AbstractiveService`: GPT-based summarization  
- `ComparisonService`: Summary comparison logic

**`data_service.py`** - Data persistence
- File I/O operations
- JSON serialization/deserialization
- Streamlit file upload handling

### UI Components (`src/ui/`)

**`components.py`**
- Reusable Streamlit UI components
- Consistent styling and behavior
- Separation of UI logic from business logic

### Utilities (`src/utils/`)

**`charts.py`**
- Plotly chart creation
- Data visualization utilities
- Consistent chart styling

**`logger.py`**
- Centralized logging configuration
- Different log levels and outputs
- Structured logging for analysis tracking

## Usage

### Command Line Interface

```bash
# Run full analysis
python main.py analyze --app-id com.example.app --count 100 --openai-key your_key

# Analyze existing data
python main.py analyze-existing --reviews-file data.json --openai-key your_key

# Validate setup
python main.py validate --openai-key your_key
```

### Dashboard Interface

```bash
# Run dashboard (default port 8501)
python run_dashboard.py

# Custom port/host
python run_dashboard.py --port 8080 --host 0.0.0.0
```

### Environment Variables

Create a `.env` file (copy from `.env.example`):
```bash
cp .env.example .env
# Edit .env with your OpenAI API key
```

## Benefits of Refactored Architecture

### 1. Maintainability
- Clear separation makes debugging easier
- Changes to one component don't affect others
- Easy to add new features or summarization methods

### 2. Testability
- Each service can be unit tested independently
- Mock dependencies for isolated testing
- Clear interfaces between components

### 3. Scalability
- Easy to add new data sources
- Pluggable summarization algorithms
- Horizontal scaling of services

### 4. Code Quality
- Consistent error handling
- Proper logging throughout
- Type safety with hints
- Documentation with docstrings

### 5. Developer Experience
- IDE support with proper imports
- Clear file organization
- Consistent naming conventions
- Easy onboarding for new developers

## Migration from Legacy Code

✅ **Migration Complete!** The codebase has been fully refactored:
- Old monolithic files have been split into modular services
- `text_summarization_comparison.py` → Split into multiple services in `src/services/`
- All print statements → Proper logging
- Hardcoded values → Configuration management
- Single files → Organized package structure

**Current clean structure:**
- `dashboard.py` - Clean, modular dashboard
- `main.py` - CLI interface with proper argument parsing
- `src/` - Organized package with separated concerns

## Future Enhancements

The refactored architecture enables easy addition of:
- Database persistence layer
- API endpoints (FastAPI/Flask)
- Additional summarization algorithms
- Real-time processing
- Caching layer
- Background job processing
- Unit and integration tests