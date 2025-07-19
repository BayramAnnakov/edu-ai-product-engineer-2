# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is an educational project for **AI Product Engineer Season 2, Lesson 1** that demonstrates the comparison between deterministic and probabilistic (LLM-powered) programming paradigms through a reviews analysis agent.

**Core Objective**: Build an agent using OpenAI Agents SDK that analyzes AppStore reviews with both deterministic (NLTK) and LLM (OpenAI API) approaches, then generates PM-style reports.

## Architecture & Design Principles

### Keep It Simple (KISS)
- **Minimal dependencies**: Only essential libraries (openai, nltk, pandas, streamlit)
- **Clear separation**: 3 main components (deterministic analyzer, LLM analyzer, report generator)
- **No over-engineering**: Focus on demonstrating core concepts, not complex patterns

### File Structure
```
project/
├── main.py                      # OpenAI Agent orchestrator
├── run_streamlit.py            # Streamlit launcher script
├── requirements.txt            # Minimal dependencies
├── src/                        # Source code
│   ├── analyzers/             # Analysis modules
│   │   ├── deterministic.py   # NLTK-based analysis
│   │   └── llm_analyzer.py    # OpenAI API integration
│   ├── reports/               # Report generation
│   │   └── report_generator.py # PM report generator
│   ├── ui/                    # User interfaces
│   │   ├── streamlit_app.py   # Web interface
│   │   └── interactive_demo.py # CLI interface
│   ├── advanced_agent.py      # Advanced agent with tools
│   └── agent_comparison.py    # Agent comparison utility
├── tests/                     # Test files
│   ├── test_agent.py         # Agent tests
│   └── demo_report.py        # Demo report generator
├── docs/                      # Documentation
│   └── *.md                  # Project documentation
├── reports/                   # Generated reports
│   └── generated/            # Auto-generated reports
└── config/                    # Configuration files
```

### Code Style & Standards

#### Python Code
- **PEP 8 compliance**: Use black formatter and flake8 linter
- **Type hints**: Add type annotations for main functions
- **Docstrings**: Simple docstrings for public functions
- **Error handling**: Basic try-catch for API calls and file operations

#### Function Naming
- `deterministic_analyze()` - NLTK analysis
- `llm_analyze()` - OpenAI analysis  
- `generate_report()` - PM report generation
- `process_review()` - main orchestration

#### Constants
- API endpoints, model names, and configuration in constants at top of files
- Use environment variables for sensitive data

## Development Commands

### Setup
```bash
# Install dependencies
pip install -r requirements.txt

# Set up environment
cp .env.example .env  # Add your OpenAI API key

# Download NLTK data
python -c "import nltk; nltk.download('vader_lexicon'); nltk.download('punkt')"
```

### Running the Application
```bash
# Run Streamlit app (recommended)
python run_streamlit.py
# OR
streamlit run src/ui/streamlit_app.py

# Run interactive demo
python src/ui/interactive_demo.py

# Test individual components
python tests/test_agent.py
python tests/demo_report.py

# Run main agent directly
python main.py

# Compare agents
python src/agent_comparison.py
```

### Development Workflow
```bash
# Format code
black .

# Check linting
flake8 .

# Test API connection
python -c "from llm_analyzer import test_openai_connection; test_openai_connection()"
```

## Key Implementation Guidelines

### Deterministic Analysis (deterministic.py)
- **Speed target**: < 0.5 seconds per review
- **Reproducible**: Same input always produces same output
- **Metrics**: Sentiment score, keyword extraction (TF-IDF), basic statistics
- **Libraries**: NLTK for sentiment analysis, scikit-learn for TF-IDF

### LLM Analysis (llm_analyzer.py)
- **Speed target**: < 5 seconds per review
- **Model**: Start with GPT-4 for baseline, then optimize to GPT-3.5-turbo
- **Prompts**: Store prompts as constants, make them modular
- **Error handling**: Implement retries and fallbacks for API failures

### OpenAI Agent Integration
- **Framework**: OpenAI Agents SDK for orchestration
- **Parallel processing**: Run deterministic and LLM analysis concurrently
- **State management**: Simple state tracking for agent workflow

### Report Generation (report_generator.py)
- **Format**: Markdown output with clear sections
- **Structure**: Executive summary, key metrics, insights, recommendations
- **Comparison**: Side-by-side comparison of both approaches
- **Actionable**: Include specific next steps for product improvement

## Testing & Validation

### Test Data
- Use sample AppStore reviews (anonymized)
- Include positive, negative, and neutral examples
- Test with various review lengths (short, medium, long)

### Evaluation Metrics
```python
# Deterministic metrics
deterministic_metrics = {
    "processing_time": "<0.5s",
    "reproducibility": "100%",
    "sentiment_accuracy": ">85%"
}

# LLM metrics
llm_metrics = {
    "processing_time": "<5s",
    "insight_quality": ">4.0/5.0",
    "hallucination_rate": "<5%"
}
```

### Manual Testing Checklist
- [ ] API connection works
- [ ] Deterministic analysis produces consistent results
- [ ] LLM analysis generates meaningful insights
- [ ] Report combines both approaches effectively
- [ ] Streamlit interface is responsive
- [ ] Error handling works for API failures

## API Keys & Environment

### Required Environment Variables
```bash
OPENAI_API_KEY=your_openai_key_here
OPENAI_MODEL=gpt-4  # or gpt-3.5-turbo for cost optimization
```

### API Usage Optimization
- **Batch requests** when possible
- **Cache results** for repeated reviews
- **Monitor costs** - set up usage alerts
- **Rate limiting** - respect OpenAI API limits

## Deployment

### Streamlit Cloud Deployment
- **Requirements**: Ensure requirements.txt is complete
- **Secrets**: Add OpenAI API key to Streamlit secrets
- **URL**: Deploy to https://appname.streamlit.app

### GitHub Integration
- **Branches**: Use main branch for stable code
- **Commits**: Clear commit messages following conventional commits
- **Issues**: Use GitHub issues for bug tracking
- **Documentation**: Keep README.md updated with setup instructions

## Common Issues & Solutions

### API Rate Limits
- Implement exponential backoff for retries
- Add request queuing for high-volume processing
- Use cheaper models for development/testing

### NLTK Download Issues
- Ensure NLTK data is downloaded during setup
- Add data download to requirements or setup script
- Handle missing data gracefully

### Streamlit Deployment Issues
- Pin exact versions in requirements.txt
- Use st.cache_data for expensive operations
- Handle secrets properly in cloud deployment

## Learning Objectives Tracking

Throughout development, ensure the project demonstrates:
- [x] **Deterministic vs Probabilistic paradigms**: Clear comparison of both approaches
- [x] **OpenAI Agents SDK usage**: Practical implementation of agent framework
- [x] **Evaluation-Driven Development**: Metrics and testing for both approaches
- [x] **PM Report Generation**: Automated product insights from user feedback
- [x] **Cost-Performance Trade-offs**: Understanding of speed vs quality decisions

## Code Quality Standards

### Before Committing
1. Run `black .` to format code
2. Run `flake8 .` to check style
3. Test main functionality manually
4. Update documentation if needed
5. Check that sensitive data is not included

### PR Review Checklist
- [ ] Code follows established patterns
- [ ] Error handling is appropriate
- [ ] Performance targets are met
- [ ] Documentation is updated
- [ ] No hardcoded secrets or API keys