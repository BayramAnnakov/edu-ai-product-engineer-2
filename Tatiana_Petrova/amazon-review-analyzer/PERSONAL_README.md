# Tatiana_Petrova - AI Product Engineer Course

## About This Submission

This directory contains my project submission for the AI Product Engineer course. The project demonstrates practical application of AI technologies in product management and customer feedback analysis.

## Project: Amazon Review Analyzer - Product Pulse Dashboard

### Overview
A comprehensive dashboard that leverages Google's Gemini AI to analyze Amazon product reviews and provide actionable insights for product managers.

### Key Learning Outcomes
- **AI Integration**: Implemented Google Gemini AI for natural language processing
- **Workflow Orchestration**: Used LangGraph for complex AI agent workflows
- **Data Visualization**: Created interactive dashboards with Streamlit and Plotly
- **Product Management**: Built tools for customer feedback analysis and decision support

### Technologies Explored
- **AI/ML**: Google Gemini AI, LangChain
- **Backend**: Python, Pandas, LangGraph
- **Frontend**: Streamlit
- **Data Visualization**: Plotly Express
- **Development**: Git, Virtual Environments

### Project Structure
```
amazon-review-analyzer/
├── dashboard.py          # Main Streamlit application
├── main.py              # Core AI workflow logic
├── requirements.txt     # Dependencies
├── .env.example         # Environment template
├── .gitignore          # Git ignore rules
├── README.md           # Project documentation
└── test_streamlit.py   # Testing utilities
```

### How to Run
1. Follow setup instructions in README.md
2. Add your Google API key to .env file
3. Run `streamlit run dashboard.py`
4. Access dashboard at http://localhost:8501

### Key Features Implemented
- Multi-page dashboard with Product, Date, and User Analytics
- AI-powered review summarization and thematic analysis
- Interactive charts and data visualization
- Real-time product analysis with caching
- User behavior pattern detection

### Course Application
This project demonstrates the practical application of AI in product management, showing how modern AI tools can transform customer feedback into actionable business insights.