# Product Pulse Dashboard

A comprehensive Amazon review analysis tool built with Python, Streamlit, and Google's Gemini AI. This dashboard provides product managers with deep insights into customer feedback through multi-dimensional analysis.

## Project Overview

This project was developed as part of the AI Product Engineer course. It demonstrates the application of AI technologies for product management, specifically focusing on customer feedback analysis and business intelligence.

## Tools and Technologies Used

- **AI/ML**: Google Gemini AI (langchain-google-genai) for natural language processing
- **Framework**: LangGraph for AI workflow orchestration
- **Frontend**: Streamlit for interactive web dashboard
- **Data Processing**: Pandas for data manipulation and analysis
- **Visualization**: Plotly Express for interactive charts and graphs
- **Environment**: Python 3.8+ with virtual environment management

## Features

### 📊 Product Analysis
- **Dual Product Selection**: Search by Product ID or browse top products by category
- **Comprehensive Metrics**: Total reviews, average rating, first/last review dates
- **Interactive Charts**: Rating distribution histograms and time-based trends
- **Review Explorer**: Paginated review browsing with rating filters
- **AI-Powered Analysis**: Extractive summaries, abstractive pros/cons, and thematic analysis

### 📅 Date Analytics
- **Time-Based Insights**: Rating trends and review volume over time
- **Monthly Deep Dive**: Detailed review exploration by month
- **Pattern Detection**: Identify seasonal trends and rating patterns

### 👥 User Analytics
- **User Behavior Analysis**: Review frequency and rating patterns
- **Suspicious Activity Detection**: Identify potential fake reviews
- **Activity Timeline**: Track user engagement over time

## Technology Stack

- **Frontend**: Streamlit for web interface
- **AI/ML**: Google Gemini AI (langchain-google-genai) for text analysis
- **Data Processing**: Pandas for data manipulation
- **Visualization**: Plotly Express for interactive charts
- **Workflow**: LangGraph for AI agent orchestration

## Setup Instructions

### Prerequisites
- Python 3.8 or higher
- Google API key for Gemini AI
- CSV dataset with product reviews

### Installation

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd amazon-review-analyzer
   ```

2. **Create virtual environment**
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Set up environment variables**
   ```bash
   cp .env.example .env
   # Edit .env file and add your Google API key
   ```

5. **Prepare your data**
   Place your reviews CSV file in the `data/` directory as `reviews.csv`
   
   Expected CSV format:
   - `ProductId`: Product identifier
   - `Text`: Review text content
   - `Score`: Rating (1-5 scale)
   - `Time`: Unix timestamp
   - `UserId`: User identifier

## Usage

1. **Start the dashboard**
   ```bash
   streamlit run dashboard.py
   ```

2. **Access the application**
   Open your browser and navigate to `http://localhost:8501`

3. **Navigate between pages**
   Use the sidebar to switch between Product Analysis, Date Analytics, and User Analytics

## Core Components

### LangGraph Workflow
The application uses a sophisticated AI workflow with parallel processing:
- **Review Fetching**: Extracts reviews for specific products
- **Extractive Summarization**: Selects key quotes from reviews
- **Abstractive Summarization**: Creates structured pros/cons analysis
- **Thematic Analysis**: Groups reviews by themes and topics
- **Final Report**: Combines all analyses into comprehensive insights

### Data Processing
- Flexible CSV column mapping for different data formats
- Robust error handling and data validation
- Efficient caching with Streamlit session state

### Interactive Features
- **Pagination**: Handle large datasets with 5-review pages
- **Filtering**: Sort and filter reviews by rating, date, and themes
- **Product Discovery**: Browse top products by various metrics
- **Real-time Analysis**: On-demand AI analysis with loading indicators

## Project Structure

```
amazon-review-analyzer/pythonProject/
├── dashboard.py          # Main Streamlit application
├── main.py              # Core analysis logic and LangGraph workflow
├── requirements.txt     # Python dependencies
├── .env                # Environment variables
├── data/               # Data directory
│   └── reviews.csv     # Reviews dataset
└── README.md           # This file
```

## Key Functions

### Analysis Functions
- `get_reviews_for_product()`: Extracts and processes review data
- `thematic_analysis_node()`: Identifies themes and groups quotes
- `extractive_summarizer_node()`: Selects representative quotes
- `abstractive_summarizer_node()`: Creates structured summaries

### Visualization Functions
- `create_sentiment_chart()`: Time-based rating trends
- `create_rating_histogram()`: Rating distribution charts
- `create_review_count_chart()`: Review volume over time

### Utility Functions
- `get_product_metrics()`: Calculate product statistics
- `get_top_products()`: Rank products by various criteria
- `detect_suspicious_users()`: Identify unusual review patterns

## Data Requirements

Your CSV file should contain reviews with the following information:
- Product identifiers
- Review text content
- Numerical ratings (1-5 scale)
- Timestamps
- User identifiers (optional, for user analytics)

## Performance Features

- **Session State Caching**: Avoid re-analysis of the same products
- **Parallel Processing**: LangGraph enables concurrent AI operations
- **Lazy Loading**: Charts and data load on-demand
- **Efficient Filtering**: Optimized data queries and transformations

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Test thoroughly
5. Submit a pull request

## License

This project is open source and available under the MIT License.

## Support

For issues, questions, or feature requests, please open an issue in the repository.