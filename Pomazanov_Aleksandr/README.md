# Pomazanov Aleksandr - AI Product Engineer Projects

## Project Overview

This directory contains my contributions to the AI Product Engineer course, focusing on building practical AI-powered tools and applications.

## Projects

### 1. Feedback Analysis Agent

**Location:** `feedback-analysis-agent/`

An intelligent feedback analysis tool that processes user reviews and generates actionable insights for product teams using AI.

#### Features
- **Multi-format Support**: Processes TXT, CSV, JSON, and Excel files
- **AI-Powered Analysis**: Integration with OpenAI GPT-4 and Anthropic Claude
- **Smart Categorization**: Automatically categorizes feedback into 6 main categories (Bugs, UX/UI, Performance, Functionality, Feature Requests, General)
- **Sentiment Analysis**: Determines positive, negative, or neutral sentiment
- **Priority Detection**: Automatically identifies high-priority issues
- **Actionable Insights**: Generates detailed reports with recommendations
- **CLI Interface**: User-friendly command-line interface with progress tracking

#### Technologies Used
- **Python 3.13+**
- **AI Models**: OpenAI GPT-4, Anthropic Claude 3.5 Sonnet
- **Libraries**: 
  - `openai` - OpenAI API integration
  - `anthropic` - Anthropic API integration
  - `pandas` - Data processing
  - `pydantic` - Data validation and modeling
  - `click` - CLI framework
  - `rich` - Beautiful terminal output
  - `python-dotenv` - Environment variable management

#### Setup Instructions

1. **Clone and Navigate**
   ```bash
   cd Pomazanov_Aleksandr/feedback-analysis-agent
   ```

2. **Install Dependencies**
   ```bash
   python3 -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   pip install -r requirements.txt
   ```

3. **Configure API Keys**
   ```bash
   cp .env.example .env
   # Edit .env file and add your API keys:
   # OPENAI_API_KEY=your_openai_key_here
   # ANTHROPIC_API_KEY=your_anthropic_key_here
   ```

4. **Test Installation**
   ```bash
   python main.py --help
   python main.py create-sample
   python main.py test-connection --provider anthropic
   ```

5. **Run Analysis**
   ```bash
   # Analyze sample data
   python main.py analyze examples/sample_feedback.txt --verbose
   
   # Analyze with specific model and save report
   python main.py analyze data/your_feedback.csv --provider anthropic --model claude-3-5-sonnet-20241022 -o report.json
   ```

#### Usage Examples

**Basic Analysis:**
```bash
python main.py analyze examples/sample_feedback.csv
```

**Advanced Analysis with Custom Settings:**
```bash
python main.py analyze data/user_reviews.json --provider anthropic --model claude-3-5-sonnet-20241022 --verbose -o detailed_report.json
```

**Test Different Providers:**
```bash
python main.py test-connection --provider openai
python main.py test-connection --provider anthropic
```

#### Key Learnings

- **AI Integration**: Implemented robust API handling for multiple LLM providers
- **Data Processing**: Built flexible file processors supporting multiple formats
- **Error Handling**: Implemented graceful fallbacks and comprehensive error reporting
- **Security**: Proper handling of API keys and sensitive data exclusion
- **User Experience**: Created intuitive CLI with progress bars and colored output
- **Code Quality**: Followed Python best practices with type hints and documentation

#### Future Enhancements

- Web dashboard interface
- Real-time feedback monitoring
- Advanced analytics and trends
- Multi-language support
- Custom categorization rules
- Integration with popular feedback platforms

---

*This project demonstrates practical application of AI for product management, combining natural language processing, data analysis, and user-friendly interfaces to solve real business problems.*