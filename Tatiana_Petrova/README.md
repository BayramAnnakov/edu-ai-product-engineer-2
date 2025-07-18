# Tatiana_Petrova - AI Product Engineer Course

## Project Overview

This directory contains my project submission for the AI Product Engineer course. The project demonstrates practical application of AI technologies in product management and customer feedback analysis.

### Amazon Review Analyzer - Product Pulse Dashboard

A comprehensive AI-powered dashboard that leverages Google's Gemini AI to analyze Amazon product reviews and provide actionable insights for product managers. The system implements multi-dimensional analysis including product analytics, date-based trends, and user behavior patterns.

## Tools and Technologies Used

### AI/ML Technologies
- **Google Gemini AI**: Selected for its advanced natural language processing capabilities and cost-effective API pricing
- **LangChain**: Chosen for seamless integration with Google's AI services and robust prompt management
- **LangGraph**: Utilized for complex AI workflow orchestration, enabling parallel processing of multiple analysis tasks

### Backend Technologies
- **Python 3.8+**: Core programming language for robust data processing and AI integration
- **Pandas**: Essential for efficient data manipulation and CSV processing
- **Python-dotenv**: Secure environment variable management for API keys

### Frontend & Visualization
- **Streamlit**: Selected for rapid prototyping and intuitive web interface development
- **Plotly Express**: Chosen for interactive data visualizations and professional charts
- **Multi-page Navigation**: Implemented for organized user experience across different analytics views

### Development Tools
- **Git**: Version control and collaborative development
- **Virtual Environment**: Isolated dependency management
- **Environment Variables**: Secure API key management

## Setup Instructions

### Prerequisites
- Python 3.8 or higher
- Google API key for Gemini AI
- CSV dataset with product reviews

### Installation Steps

1. **Navigate to Project Directory**
   ```bash
   cd Tatiana_Petrova/amazon-review-analyzer
   ```

2. **Create Virtual Environment**
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install Dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Configure Environment Variables**
   ```bash
   cp .env.example .env
   # Edit .env file and add your Google API key:
   # GOOGLE_API_KEY="your_actual_api_key_here"
   ```

5. **Prepare Data**
   - Place your reviews CSV file in the `data/` directory as `reviews.csv`
   - Expected format: ProductId, Text, Score, Time, UserId columns

6. **Run the Application**
   ```bash
   streamlit run dashboard.py
   ```

7. **Access Dashboard**
   - Open your browser to `http://localhost:8501`
   - Navigate between Product Analysis, Date Analytics, and User Analytics pages

### Expected Data Format
```csv
ProductId,Text,Score,Time,UserId
B001GVISJM,"Great product!",5,1234567890,user123
B001GVISJM,"Not as expected",2,1234567891,user456
```

## Key Features Implemented

### Product Analysis Page
- **Dual Selection Method**: Search by Product ID or browse categorized top products
- **AI-Powered Analysis**: Extractive and abstractive summarization using Google Gemini
- **Thematic Analysis**: Automated grouping of reviews by themes with relevant quotes
- **Interactive Visualizations**: Rating distribution histograms and sentiment trends
- **Review Explorer**: Paginated review browsing with rating-based filtering

### Date Analytics Page
- **Temporal Analysis**: Rating trends and review volume over time
- **Monthly Deep Dive**: Detailed exploration of reviews by selected months
- **Pattern Detection**: Identification of seasonal trends and anomalies
- **Interactive Charts**: Time-series visualizations with hover details

### User Analytics Page
- **Behavior Pattern Analysis**: Review frequency and rating distribution per user
- **Suspicious Activity Detection**: Identification of potentially fake reviews
- **Activity Timeline**: Temporal tracking of user engagement
- **Statistical Insights**: User activity metrics and patterns

## Technical Architecture

### AI Workflow (LangGraph)
```
Review Fetching → Parallel Processing:
                 ├── Extractive Summarization
                 ├── Abstractive Summarization
                 └── Thematic Analysis
                 ↓
                 Final Report Generation
```

### Data Processing Pipeline
1. **Data Ingestion**: CSV parsing with flexible column mapping
2. **Data Validation**: Missing value handling and type conversion
3. **AI Processing**: Multi-threaded analysis with Google Gemini
4. **Caching**: Session-based storage for performance optimization
5. **Visualization**: Real-time chart generation with Plotly

## Learning Outcomes

This project demonstrates practical application of modern AI technologies in product management:

- **AI Integration**: Successfully implemented Google Gemini AI for natural language processing tasks
- **Workflow Orchestration**: Designed and implemented complex AI workflows using LangGraph
- **Data Visualization**: Created intuitive, interactive dashboards for business intelligence
- **Product Management**: Built tools that transform customer feedback into actionable insights
- **Software Engineering**: Applied best practices for code organization, security, and documentation
- **User Experience**: Designed multi-page applications with intuitive navigation and real-time feedback

## Security Considerations

- **API Key Management**: Secure storage using environment variables
- **Data Privacy**: No sensitive customer data stored or transmitted
- **Error Handling**: Graceful degradation when AI services are unavailable
- **Input Validation**: Sanitization of user inputs and file uploads

## Future Enhancements

- Integration with additional AI models for comparison
- Real-time data streaming capabilities
- Advanced machine learning models for sentiment analysis
- Export functionality for analysis results
- Multi-language support for international reviews

---

*This project was developed as part of the AI Product Engineer course, demonstrating the practical application of AI technologies in product management and customer feedback analysis.*