"""
Streamlit Web Interface for Review Analysis Agent
Simple, intuitive interface for testing both analysis approaches
"""

import streamlit as st
import time
import json
from typing import Dict, Any
import plotly.graph_objects as go
import plotly.express as px
import pandas as pd

# Import our main agent
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))
from main import ReviewAnalysisAgent

# Page configuration
st.set_page_config(
    page_title="Review Analysis Agent",
    page_icon="🤖",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for better styling
st.markdown("""
<style>
    .main-header {
        color: #1f77b4;
        text-align: center;
        padding: 1rem 0;
    }
    .analysis-box {
        background-color: #f8f9fa;
        padding: 1rem;
        border-radius: 0.5rem;
        margin: 1rem 0;
    }
    .metric-box {
        background-color: #e9ecef;
        padding: 0.5rem;
        border-radius: 0.3rem;
        margin: 0.5rem 0;
    }
    .speed-comparison {
        background-color: #fff3cd;
        padding: 1rem;
        border-radius: 0.5rem;
        border-left: 4px solid #ffc107;
    }
</style>
""", unsafe_allow_html=True)

@st.cache_resource
def initialize_agent():
    """Initialize and cache the agent"""
    try:
        agent = ReviewAnalysisAgent()
        return agent, None
    except Exception as e:
        return None, str(e)

def display_analysis_results(results: Dict[str, Any]):
    """Display analysis results in organized tabs"""
    
    if "error" in results:
        st.error(f"Analysis failed: {results['error']}")
        return
    
    # Create tabs for different views
    tab1, tab2, tab3, tab4 = st.tabs(["📊 Quick Summary", "🔍 Detailed Analysis", "📋 PM Report", "📈 Performance"])
    
    with tab1:
        st.subheader("🎯 Quick Summary")
        
        # Performance metrics
        col1, col2, col3 = st.columns(3)
        
        with col1:
            total_time = results['performance']['total_processing_time']
            st.metric("Total Processing Time", f"{total_time:.2f}s")
        
        with col2:
            det_sentiment = results['deterministic_results'].get('sentiment', 'unknown')
            st.metric("Deterministic Sentiment", det_sentiment.title())
        
        with col3:
            llm_sentiment = results['llm_results'].get('sentiment', 'unknown')
            st.metric("LLM Sentiment", llm_sentiment)
        
        # Speed comparison
        speed_adv = results['performance']['speed_advantage']
        st.markdown(f"""
        <div class="speed-comparison">
            <h4>⚡ Speed Comparison</h4>
            <p>{speed_adv}</p>
        </div>
        """, unsafe_allow_html=True)
        
        # Key insights
        st.subheader("💡 Key Insights")
        det_keywords = results['deterministic_results'].get('top_keywords', [])
        llm_insights = results['llm_results'].get('insights', 'No insights available')
        
        col1, col2 = st.columns(2)
        with col1:
            st.write("**Top Keywords (Deterministic):**")
            st.write(", ".join(det_keywords[:5]))
        
        with col2:
            st.write("**LLM Insights:**")
            st.write(llm_insights)
    
    with tab2:
        st.subheader("🔍 Detailed Analysis Comparison")
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("### 📊 Deterministic Analysis (NLTK)")
            det_results = results['deterministic_results']
            
            # Sentiment scores
            sentiment_scores = det_results.get('sentiment_scores', {})
            st.write(f"**Sentiment:** {det_results.get('sentiment', 'unknown').title()}")
            st.write(f"**Compound Score:** {sentiment_scores.get('compound', 0):.3f}")
            
            # Create sentiment score chart
            if sentiment_scores:
                fig = go.Figure(data=[
                    go.Bar(
                        x=['Positive', 'Negative', 'Neutral'],
                        y=[sentiment_scores.get('positive', 0), 
                           sentiment_scores.get('negative', 0), 
                           sentiment_scores.get('neutral', 0)],
                        marker_color=['green', 'red', 'gray']
                    )
                ])
                fig.update_layout(title="Sentiment Score Breakdown", height=300)
                st.plotly_chart(fig, use_container_width=True)
            
            # Keywords
            st.write("**Top Keywords:**")
            keywords = det_results.get('keywords', [])
            if keywords:
                keyword_df = pd.DataFrame(keywords[:10])
                st.dataframe(keyword_df)
            
            # Feature categories
            st.write("**Feature Categories:**")
            feature_cats = det_results.get('feature_categories', {})
            if feature_cats:
                fig = px.bar(
                    x=list(feature_cats.keys()),
                    y=list(feature_cats.values()),
                    title="Feature Mentions"
                )
                st.plotly_chart(fig, use_container_width=True)
            
            # Issues found
            issues = det_results.get('issues_found', [])
            if issues:
                st.write("**Issues Identified:**")
                for issue in issues:
                    st.write(f"• {issue}")
        
        with col2:
            st.markdown("### 🧠 LLM Analysis (OpenAI)")
            llm_results = results['llm_results']
            
            st.write(f"**Model:** {llm_results.get('model_used', 'unknown')}")
            st.write(f"**Tokens Used:** {llm_results.get('tokens_used', 0)}")
            st.write(f"**Sentiment:** {llm_results.get('sentiment', 'unknown')}")
            
            # Analysis sections
            analysis_sections = [
                ("Insights", llm_results.get('insights', 'No insights available')),
                ("Features", llm_results.get('features', 'No features mentioned')),
                ("Issues", llm_results.get('issues', 'No issues identified')),
                ("Recommendations", llm_results.get('recommendations', 'No recommendations'))
            ]
            
            for title, content in analysis_sections:
                st.write(f"**{title}:**")
                st.write(content)
                st.write("---")
    
    with tab3:
        st.subheader("📋 Product Manager Report")
        
        pm_report = results.get('pm_report', 'No report available')
        st.markdown(pm_report)
        
        # Download buttons
        col1, col2 = st.columns(2)
        with col1:
            st.download_button(
                label="📄 Download Markdown Report",
                data=pm_report,
                file_name="review_analysis_report.md",
                mime="text/markdown"
            )
        
        with col2:
            json_export = results.get('json_export', '{}')
            st.download_button(
                label="📊 Download JSON Data",
                data=json_export,
                file_name="review_analysis_data.json",
                mime="application/json"
            )
    
    with tab4:
        st.subheader("📈 Performance Analysis")
        
        perf = results['performance']
        
        # Processing times comparison
        times_data = {
            'Method': ['Deterministic', 'LLM'],
            'Processing Time (s)': [perf['deterministic_time'], perf['llm_time']],
            'Color': ['#1f77b4', '#ff7f0e']
        }
        
        fig = px.bar(
            times_data,
            x='Method',
            y='Processing Time (s)',
            color='Color',
            title="Processing Time Comparison"
        )
        st.plotly_chart(fig, use_container_width=True)
        
        # Performance metrics
        col1, col2 = st.columns(2)
        with col1:
            st.metric("Deterministic Time", f"{perf['deterministic_time']:.3f}s")
            st.metric("LLM Time", f"{perf['llm_time']:.1f}s")
        
        with col2:
            st.metric("Total Time", f"{perf['total_processing_time']:.2f}s")
            st.metric("Speed Advantage", perf['speed_advantage'])

def main():
    """Main Streamlit app"""
    
    # Header
    st.markdown('<h1 class="main-header">🤖 Review Analysis Agent</h1>', unsafe_allow_html=True)
    st.markdown('<p style="text-align: center; color: #666;">AI Product Engineer Season 2 - Comparing Deterministic vs Probabilistic Analysis</p>', unsafe_allow_html=True)
    
    # Initialize agent
    agent, error = initialize_agent()
    
    if error:
        st.error(f"Failed to initialize agent: {error}")
        st.info("Please check your .env file and ensure OPENAI_API_KEY is set correctly.")
        return
    
    # Sidebar
    st.sidebar.title("⚙️ Configuration")
    
    # Processing mode
    parallel_mode = st.sidebar.checkbox("Parallel Processing", value=True, help="Run both analyses simultaneously")
    
    # Agent status
    status = agent.get_status()
    st.sidebar.success(f"Agent Status: {status['status'].title()}")
    st.sidebar.info(f"OpenAI Model: {status['environment']['openai_model']}")
    
    # Main interface
    st.subheader("📝 Input Review")
    
    # Input options
    input_method = st.radio("Choose input method:", ["Text Input", "Sample Reviews"])
    
    if input_method == "Text Input":
        review_text = st.text_area(
            "Enter AppStore review to analyze:",
            height=150,
            placeholder="Paste your app review here..."
        )
    else:
        # Sample reviews
        sample_reviews = {
            "Positive Review": "This app is amazing! The interface is so intuitive and easy to use. Great customer support too. Highly recommend!",
            "Negative Review": "Terrible experience. App crashes constantly when I try to upload files. Very frustrating and needs fixing immediately.",
            "Mixed Review": "Good app with nice design, but performance is slow sometimes. The features are useful but needs optimization.",
            "Detailed Review": "I love the clean interface and the app works great most of the time. However, I've noticed that it crashes sometimes when I try to upload large files. The customer support is responsive though. Overall good but the stability issues need to be addressed."
        }
        
        selected_sample = st.selectbox("Choose a sample review:", list(sample_reviews.keys()))
        review_text = sample_reviews[selected_sample]
        st.text_area("Review text:", value=review_text, height=100, disabled=True)
    
    # Analysis button
    if st.button("🔍 Analyze Review", type="primary"):
        if not review_text.strip():
            st.warning("Please enter a review to analyze.")
            return
        
        # Show processing message
        with st.spinner("🤖 Agent is analyzing the review..."):
            progress_bar = st.progress(0)
            
            # Simulate progress
            for i in range(100):
                time.sleep(0.01)
                progress_bar.progress(i + 1)
            
            # Run analysis
            results = agent.process_review(review_text, parallel=parallel_mode)
        
        # Display results
        if results:
            display_analysis_results(results)
        else:
            st.error("Analysis failed. Please try again.")
    
    # Batch processing section
    st.subheader("📊 Batch Processing")
    
    if st.button("🔄 Process Sample Batch"):
        sample_batch = [
            "Great app! Easy to use and fast.",
            "Terrible experience. App crashes all the time.",
            "Good interface but needs more features.",
            "Love the design but performance is slow."
        ]
        
        with st.spinner("Processing batch of reviews..."):
            batch_results = agent.batch_process(sample_batch, parallel=parallel_mode)
        
        if batch_results:
            st.success(f"Batch processing completed!")
            
            # Show batch summary
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("Total Reviews", batch_results['batch_info']['total_reviews'])
            with col2:
                st.metric("Successful", batch_results['batch_info']['successful'])
            with col3:
                st.metric("Failed", batch_results['batch_info']['failed'])
            
            # Performance summary
            st.subheader("Performance Summary")
            perf = batch_results['performance']
            
            col1, col2 = st.columns(2)
            with col1:
                st.metric("Total Batch Time", f"{perf['total_batch_time']:.2f}s")
                st.metric("Avg Deterministic Time", f"{perf['avg_deterministic_time']:.3f}s")
            with col2:
                st.metric("Avg LLM Time", f"{perf['avg_llm_time']:.2f}s")
                st.metric("Processing Mode", batch_results['batch_info']['processing_mode'])
    
    # Footer
    st.markdown("---")
    st.markdown("*Built with Streamlit • Powered by OpenAI • AI Product Engineer Season 2*")

if __name__ == "__main__":
    main()