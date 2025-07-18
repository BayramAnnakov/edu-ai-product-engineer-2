import os
import pandas as pd
from typing import List, Dict, Any, TypedDict
from dotenv import load_dotenv
from langchain_google_genai import ChatGoogleGenerativeAI
from langgraph.graph import StateGraph, END
import streamlit as st
import plotly.express as px
import json

# Load environment variables from .env file
load_dotenv()

# Initialize Gemini model
llm = ChatGoogleGenerativeAI(
    model="gemini-1.5-flash-latest",
    google_api_key=os.getenv("GOOGLE_API_KEY")
)

def get_reviews_for_product(product_id: str) -> pd.DataFrame:
    """
    Read reviews from CSV file and return DataFrame with reviewText, overall (rating), and reviewTime (date).
    
    Args:
        product_id: The ID of the product to get reviews for
        
    Returns:
        DataFrame with columns: reviewText, overall, reviewTime
    """
    try:
        # Read the reviews CSV file
        df = pd.read_csv('data/reviews.csv')
        
        # Filter reviews for the specific product ID
        product_reviews = df[df['ProductId'] == product_id].copy()
        
        if product_reviews.empty:
            return pd.DataFrame(columns=['reviewText', 'overall', 'reviewTime'])
        
        # Create result DataFrame with standardized column names
        result_df = pd.DataFrame()
        
        # Handle review text column
        if 'Text' in product_reviews.columns:
            result_df['reviewText'] = product_reviews['Text']
        elif 'reviewText' in product_reviews.columns:
            result_df['reviewText'] = product_reviews['reviewText']
        else:
            # Try to find a column that might contain review text
            text_columns = [col for col in product_reviews.columns if 'text' in col.lower()]
            if text_columns:
                result_df['reviewText'] = product_reviews[text_columns[0]]
            else:
                raise ValueError("Could not find review text column in CSV")
        
        # Handle rating column
        if 'Score' in product_reviews.columns:
            result_df['overall'] = product_reviews['Score']
        elif 'overall' in product_reviews.columns:
            result_df['overall'] = product_reviews['overall']
        else:
            # Try to find a rating column
            rating_columns = [col for col in product_reviews.columns if 'score' in col.lower() or 'rating' in col.lower()]
            if rating_columns:
                result_df['overall'] = product_reviews[rating_columns[0]]
            else:
                # Default to 5 if no rating found
                result_df['overall'] = 5
        
        # Handle time column
        if 'Time' in product_reviews.columns:
            result_df['reviewTime'] = pd.to_datetime(product_reviews['Time'], unit='s')
        elif 'reviewTime' in product_reviews.columns:
            result_df['reviewTime'] = pd.to_datetime(product_reviews['reviewTime'], unit='s')
        else:
            # Try to find a time column
            time_columns = [col for col in product_reviews.columns if 'time' in col.lower() or 'date' in col.lower()]
            if time_columns:
                result_df['reviewTime'] = pd.to_datetime(product_reviews[time_columns[0]], unit='s')
            else:
                # Default to current date if no time found
                result_df['reviewTime'] = pd.Timestamp.now()
        
        # Remove rows with missing essential data
        result_df = result_df.dropna(subset=['reviewText'])
        
        return result_df
        
    except FileNotFoundError:
        print("Error: reviews.csv file not found in data directory")
        return pd.DataFrame(columns=['reviewText', 'overall', 'reviewTime'])
    except Exception as e:
        print(f"Error reading reviews: {str(e)}")
        return pd.DataFrame(columns=['reviewText', 'overall', 'reviewTime'])


class GraphState(TypedDict):
    """
    State structure for the LangGraph application.
    This defines all the data that will be passed between nodes in the graph.
    """
    product_id: str
    reviews: List[str]
    reviews_df: pd.DataFrame
    extractive_summary: str
    abstractive_summary: str
    thematic_analysis: Dict[str, List[str]]
    final_report: str


def fetch_reviews_node(state: GraphState) -> Dict[str, Any]:
    """
    Node to fetch reviews for a given product ID.
    
    Args:
        state: Current graph state containing product_id
        
    Returns:
        Dictionary with reviews and reviews_df to update the state
    """
    product_id = state["product_id"]
    reviews_df = get_reviews_for_product(product_id)
    reviews = reviews_df['reviewText'].tolist()
    return {"reviews": reviews, "reviews_df": reviews_df}


def extractive_summarizer_node(state: GraphState) -> Dict[str, Any]:
    """
    Node to create an extractive summary by selecting key quotes from reviews.
    
    Args:
        state: Current graph state containing reviews
        
    Returns:
        Dictionary with extractive_summary to update the state
    """
    reviews = state["reviews"]
    
    # Combine reviews into a single text
    reviews_text = "\n\n".join(reviews)
    
    # Create prompt for extractive summarization
    prompt = f"""You are an information extraction robot. Your task is to select and return 3-5 most representative quotes from these reviews. DO NOT CHANGE A SINGLE WORD. Return only the quotes, each on a new line.

Reviews:
{reviews_text}"""
    
    # Call LLM
    response = llm.invoke(prompt)
    extractive_summary = response.content
    
    return {"extractive_summary": extractive_summary}


def abstractive_summarizer_node(state: GraphState) -> Dict[str, Any]:
    """
    Node to create an abstractive summary of the reviews.
    
    Args:
        state: Current graph state containing reviews
        
    Returns:
        Dictionary with abstractive_summary to update the state
    """
    reviews = state["reviews"]
    
    # Combine reviews into a single text
    reviews_text = "\n\n".join(reviews)
    
    # Create prompt for abstractive summarization
    prompt = f"""You are an experienced product reviewer. Read all these reviews and write a short, coherent summary. Structure your response: first a 'Pros:' section, then a 'Cons:' section.

Reviews:
{reviews_text}"""
    
    # Call LLM
    response = llm.invoke(prompt)
    abstractive_summary = response.content
    
    return {"abstractive_summary": abstractive_summary}


def thematic_analysis_node(state: GraphState) -> Dict[str, Any]:
    """
    Node to extract themes and related quotes from reviews.
    
    Args:
        state: Current graph state containing reviews
        
    Returns:
        Dictionary with thematic_analysis to update the state
    """
    reviews = state["reviews"]
    
    # Combine reviews into a single text
    reviews_text = "\n\n".join(reviews)
    
    # Create prompt for thematic analysis
    prompt = f"""Analyze these reviews. Extract 5-7 key themes (e.g., 'Taste', 'Packaging', 'Price'). For each theme, select 2-3 relevant quotes. Return the result strictly in JSON format, where keys are theme names and values are lists of quotes.

Reviews:
{reviews_text}

Return only valid JSON in this format:
{{
  "Theme Name": ["quote 1", "quote 2", "quote 3"],
  "Another Theme": ["quote 1", "quote 2"]
}}"""
    
    try:
        # Call LLM
        response = llm.invoke(prompt)
        response_text = response.content.strip()
        
        # Try to extract JSON from response
        if response_text.startswith("```json"):
            response_text = response_text[7:-3]
        elif response_text.startswith("```"):
            response_text = response_text[3:-3]
        
        # Parse JSON
        thematic_analysis = json.loads(response_text)
        
        # Validate structure
        if not isinstance(thematic_analysis, dict):
            raise ValueError("Response is not a dictionary")
        
        # Clean up the analysis
        cleaned_analysis = {}
        for theme, quotes in thematic_analysis.items():
            if isinstance(quotes, list):
                cleaned_analysis[theme] = quotes
            else:
                cleaned_analysis[theme] = [str(quotes)]
        
        return {"thematic_analysis": cleaned_analysis}
        
    except (json.JSONDecodeError, ValueError) as e:
        # Fallback: create simple thematic analysis
        fallback_analysis = {
            "Quality": ["Product quality mentioned in reviews"],
            "Value": ["Price and value comments"],
            "Experience": ["General user experience"]
        }
        return {"thematic_analysis": fallback_analysis}


def final_report_node(state: GraphState) -> Dict[str, Any]:
    """
    Node to create the final report combining both summaries.
    
    Args:
        state: Current graph state containing both summaries
        
    Returns:
        Dictionary with final_report to update the state
    """
    extractive_summary = state["extractive_summary"]
    abstractive_summary = state["abstractive_summary"]
    
    # Create prompt for final report
    prompt = f"""You are an AI analyst. Below are two summaries of product reviews: extractive (direct quotes) and abstractive (paraphrase). Write a final report for the buyer in Markdown format. The report should contain:
1. Heading 'Extractive Summary (Direct Quotes)'
2. The extractive summary text
3. Heading 'Abstractive Summary (Pros and Cons)'
4. The abstractive summary text

Extractive Summary:
{extractive_summary}

Abstractive Summary:
{abstractive_summary}"""
    
    # Call LLM
    response = llm.invoke(prompt)
    final_report = response.content
    
    return {"final_report": final_report}


def create_sentiment_chart(df: pd.DataFrame):
    """
    Create a line chart showing average rating over time.
    
    Args:
        df: DataFrame with columns reviewText, overall, reviewTime
        
    Returns:
        Plotly figure object
    """
    if df.empty:
        return None
    
    # Create a copy to avoid modifying original
    chart_df = df.copy()
    
    # Extract year-month from reviewTime
    chart_df['year_month'] = chart_df['reviewTime'].dt.to_period('M')
    
    # Group by month and calculate average rating
    monthly_ratings = chart_df.groupby('year_month')['overall'].agg(['mean', 'count']).reset_index()
    monthly_ratings['year_month'] = monthly_ratings['year_month'].astype(str)
    
    # Create bar chart
    fig = px.bar(
        monthly_ratings,
        x='year_month',
        y='mean',
        title='Average Rating Over Time',
        labels={
            'year_month': 'Month',
            'mean': 'Average Rating',
            'count': 'Number of Reviews'
        }
    )
    
    # Add hover information
    fig.update_traces(
        hovertemplate='<b>%{x}</b><br>Average Rating: %{y:.2f}<extra></extra>'
    )
    
    # Calculate overall mean and median
    overall_mean = df['overall'].mean()
    overall_median = df['overall'].median()
    
    # Add horizontal lines for mean and median with annotations
    fig.add_hline(
        y=overall_mean,
        line_dash="dash",
        line_color="red",
        annotation=dict(
            text=f"<span style='color:red'>Mean: {overall_mean:.2f}</span>",
            x=1.02,
            xref="paper",
            showarrow=False,
            xanchor="left"
        )
    )
    
    fig.add_hline(
        y=overall_median,
        line_dash="dot",
        line_color="green",
        annotation=dict(
            text=f"<span style='color:green'>Median: {overall_median:.1f}</span>",
            x=1.02,
            xref="paper",
            showarrow=False,
            xanchor="left",
            yshift=15
        )
    )
    
    # Update layout
    fig.update_layout(
        xaxis_title="Month",
        yaxis_title="Average Rating",
        yaxis=dict(range=[0, 5]),
        height=400,
        showlegend=True,
        margin=dict(r=100)  # Add right margin for annotations
    )
    
    return fig


def create_review_count_chart(df: pd.DataFrame):
    """
    Create a line chart showing number of reviews over time.
    
    Args:
        df: DataFrame with columns reviewText, overall, reviewTime
        
    Returns:
        Plotly figure object
    """
    if df.empty:
        return None
    
    # Create a copy to avoid modifying original
    chart_df = df.copy()
    
    # Extract year-month from reviewTime
    chart_df['year_month'] = chart_df['reviewTime'].dt.to_period('M')
    
    # Group by month and count reviews
    monthly_counts = chart_df.groupby('year_month').size().reset_index(name='review_count')
    monthly_counts['year_month'] = monthly_counts['year_month'].astype(str)
    
    # Create bar chart
    fig = px.bar(
        monthly_counts,
        x='year_month',
        y='review_count',
        title='Number of Reviews Over Time',
        labels={
            'year_month': 'Month',
            'review_count': 'Number of Reviews'
        }
    )
    
    # Add hover information and styling
    fig.update_traces(
        marker_color='#ff7f0e',
        hovertemplate='<b>%{x}</b><br>Reviews: %{y}<extra></extra>'
    )
    
    # Update layout
    fig.update_layout(
        xaxis_title="Month",
        yaxis_title="Number of Reviews",
        height=400
    )
    
    return fig


def create_rating_histogram(df: pd.DataFrame):
    """
    Create a histogram showing distribution of ratings.
    
    Args:
        df: DataFrame with columns reviewText, overall, reviewTime
        
    Returns:
        Plotly figure object
    """
    if df.empty:
        return None
    
    # Create histogram
    fig = px.histogram(
        df,
        x='overall',
        nbins=5,
        title='Distribution of Review Ratings',
        labels={'overall': 'Rating', 'count': 'Number of Reviews'},
        color_discrete_sequence=['#1f77b4']
    )
    
    # Update layout
    fig.update_layout(
        xaxis=dict(
            tick0=1,
            dtick=1,
            range=[0.5, 5.5]
        ),
        yaxis_title="Number of Reviews",
        xaxis_title="Rating",
        height=400,
        showlegend=False
    )
    
    # Add text annotations on bars
    fig.update_traces(
        texttemplate='%{y}',
        textposition='outside'
    )
    
    return fig


def get_product_metrics(df: pd.DataFrame):
    """
    Calculate basic product metrics.
    
    Args:
        df: DataFrame with columns reviewText, overall, reviewTime
        
    Returns:
        Dictionary with metrics
    """
    if df.empty:
        return {
            'total_reviews': 0,
            'first_review_date': None,
            'last_review_date': None,
            'avg_rating': 0
        }
    
    metrics = {
        'total_reviews': len(df),
        'first_review_date': df['reviewTime'].min(),
        'last_review_date': df['reviewTime'].max(),
        'avg_rating': df['overall'].mean()
    }
    
    return metrics


def get_reviews_by_date(date_selected: str):
    """
    Get all reviews for a specific date.
    
    Args:
        date_selected: Date in YYYY-MM-DD format
        
    Returns:
        DataFrame with reviews for that date
    """
    try:
        # Read the reviews CSV file
        df = pd.read_csv('data/reviews.csv')
        
        # Convert Time column to datetime
        df['reviewTime'] = pd.to_datetime(df['Time'], unit='s')
        df['reviewDate'] = df['reviewTime'].dt.date
        
        # Filter by selected date
        selected_date = pd.to_datetime(date_selected).date()
        date_reviews = df[df['reviewDate'] == selected_date].copy()
        
        # Standardize column names
        if 'Text' in date_reviews.columns:
            date_reviews['reviewText'] = date_reviews['Text']
        if 'Score' in date_reviews.columns:
            date_reviews['overall'] = date_reviews['Score']
        
        return date_reviews
        
    except Exception as e:
        st.error(f"Error reading reviews: {str(e)}")
        return pd.DataFrame()


def get_all_review_dates():
    """
    Get all unique review dates from the dataset.
    
    Returns:
        List of dates
    """
    try:
        df = pd.read_csv('data/reviews.csv')
        df['reviewTime'] = pd.to_datetime(df['Time'], unit='s')
        df['reviewDate'] = df['reviewTime'].dt.date
        
        # Get unique dates and sort
        dates = sorted(df['reviewDate'].unique())
        return dates
        
    except Exception as e:
        st.error(f"Error reading dates: {str(e)}")
        return []


def get_user_analytics(user_id: str):
    """
    Get comprehensive analytics for a specific user.
    
    Args:
        user_id: The user ID to analyze
        
    Returns:
        Dictionary with user analytics
    """
    try:
        df = pd.read_csv('data/reviews.csv')
        
        # Filter by user
        user_reviews = df[df['UserId'] == user_id].copy()
        
        if user_reviews.empty:
            return None
        
        # Convert time to datetime
        user_reviews['reviewTime'] = pd.to_datetime(user_reviews['Time'], unit='s')
        user_reviews['reviewDate'] = user_reviews['reviewTime'].dt.date
        
        # Basic stats
        analytics = {
            'total_reviews': len(user_reviews),
            'avg_rating': user_reviews['Score'].mean(),
            'rating_distribution': user_reviews['Score'].value_counts().to_dict(),
            'first_review': user_reviews['reviewTime'].min(),
            'last_review': user_reviews['reviewTime'].max(),
            'unique_products': user_reviews['ProductId'].nunique(),
            'reviews_df': user_reviews
        }
        
        # Activity over time
        activity_by_date = user_reviews.groupby('reviewDate').size()
        analytics['activity_by_date'] = activity_by_date
        
        # Most common rating
        analytics['most_common_rating'] = user_reviews['Score'].mode().iloc[0] if len(user_reviews['Score'].mode()) > 0 else None
        
        # Profile name
        analytics['profile_name'] = user_reviews['ProfileName'].iloc[0] if 'ProfileName' in user_reviews.columns else user_id
        
        return analytics
        
    except Exception as e:
        st.error(f"Error analyzing user: {str(e)}")
        return None


def get_all_users():
    """
    Get all unique user IDs from the dataset.
    
    Returns:
        List of user IDs sorted by review count
    """
    try:
        df = pd.read_csv('data/reviews.csv')
        
        # Get user review counts
        user_counts = df['UserId'].value_counts()
        
        # Return as list of tuples (user_id, count)
        return [(user_id, count) for user_id, count in user_counts.items()]
        
    except Exception as e:
        st.error(f"Error reading users: {str(e)}")
        return []


def get_top_products(sort_by="most_reviews"):
    """
    Get top products based on different criteria.
    
    Args:
        sort_by: Criteria for sorting ("most_reviews", "most_negative", "lowest_avg_rating", "highest_avg_rating")
        
    Returns:
        List of tuples (product_id, metric_value, description)
    """
    try:
        df = pd.read_csv('data/reviews.csv')
        
        # Group by product and calculate metrics
        product_stats = df.groupby('ProductId').agg({
            'Score': ['count', 'mean', 'std'],
            'Text': 'first'  # Get first review text for preview
        }).round(2)
        
        # Flatten column names
        product_stats.columns = ['review_count', 'avg_rating', 'rating_std', 'sample_text']
        
        # Calculate negative reviews (1-2 stars)
        negative_reviews = df[df['Score'] <= 2].groupby('ProductId').size()
        product_stats['negative_count'] = negative_reviews.fillna(0).astype(int)
        
        # Calculate negative percentage
        product_stats['negative_percentage'] = (product_stats['negative_count'] / product_stats['review_count'] * 100).round(1)
        
        # Sort based on criteria
        if sort_by == "most_reviews":
            sorted_products = product_stats.sort_values('review_count', ascending=False)
            result = [(idx, row['review_count'], f"{row['review_count']} reviews") 
                     for idx, row in sorted_products.head(50).iterrows()]
        
        elif sort_by == "most_negative":
            sorted_products = product_stats.sort_values('negative_count', ascending=False)
            result = [(idx, row['negative_count'], f"{row['negative_count']} negative reviews") 
                     for idx, row in sorted_products.head(50).iterrows()]
        
        elif sort_by == "lowest_avg_rating":
            # Only products with at least 3 reviews
            filtered_products = product_stats[product_stats['review_count'] >= 3]
            sorted_products = filtered_products.sort_values('avg_rating', ascending=True)
            result = [(idx, row['avg_rating'], f"★{row['avg_rating']} avg rating") 
                     for idx, row in sorted_products.head(50).iterrows()]
        
        elif sort_by == "highest_avg_rating":
            # Only products with at least 3 reviews
            filtered_products = product_stats[product_stats['review_count'] >= 3]
            sorted_products = filtered_products.sort_values('avg_rating', ascending=False)
            result = [(idx, row['avg_rating'], f"★{row['avg_rating']} avg rating") 
                     for idx, row in sorted_products.head(50).iterrows()]
        
        elif sort_by == "highest_negative_percentage":
            # Only products with at least 5 reviews
            filtered_products = product_stats[product_stats['review_count'] >= 5]
            sorted_products = filtered_products.sort_values('negative_percentage', ascending=False)
            result = [(idx, row['negative_percentage'], f"{row['negative_percentage']}% negative") 
                     for idx, row in sorted_products.head(50).iterrows()]
        
        else:
            result = []
        
        return result
        
    except Exception as e:
        st.error(f"Error getting top products: {str(e)}")
        return []


# Create the workflow graph
workflow = StateGraph(GraphState)

# Add all nodes to the graph
workflow.add_node("fetch_reviews", fetch_reviews_node)
workflow.add_node("extractive_summarizer", extractive_summarizer_node)
workflow.add_node("abstractive_summarizer", abstractive_summarizer_node)
workflow.add_node("thematic_analysis", thematic_analysis_node)
workflow.add_node("final_report", final_report_node)

# Set fetch_reviews as the entry point
workflow.set_entry_point("fetch_reviews")

# Define edges: after fetch_reviews, run summarizers and thematic analysis in parallel
workflow.add_edge("fetch_reviews", "extractive_summarizer")
workflow.add_edge("fetch_reviews", "abstractive_summarizer")
workflow.add_edge("fetch_reviews", "thematic_analysis")

# After all three complete, run final_report
workflow.add_edge("extractive_summarizer", "final_report")
workflow.add_edge("abstractive_summarizer", "final_report")
workflow.add_edge("thematic_analysis", "final_report")

# Set final_report as the end point
workflow.add_edge("final_report", END)

# Compile the graph
app = workflow.compile()

# Streamlit Web Interface
st.title("Product Pulse Dashboard")

# Add sidebar for navigation
page = st.sidebar.selectbox(
    "Select Page",
    ["Product Analysis", "Date Analytics", "User Analytics"]
)

if page == "Product Analysis":
    st.header("📊 Product Analysis")
    
    # Check if we're coming from date analytics with a selected product
    default_product_id = "B001GVISJM"
    if 'selected_product_id' in st.session_state:
        default_product_id = st.session_state.selected_product_id
        # Clear the session state after using it
        del st.session_state.selected_product_id
    
    # Product selection method
    product_search_method = st.radio(
        "Choose how to select product:",
        ["Search by Product ID", "Browse top products"],
        key="product_search_method"
    )
    
    if product_search_method == "Search by Product ID":
        # Input field for product ID
        product_id_input = st.text_input("Enter Product ID for Analysis:", default_product_id)
        
        # Check if product exists
        if product_id_input and product_id_input != default_product_id:
            top_products = get_top_products("most_reviews")
            product_ids = [pid for pid, _, _ in top_products]
            if product_id_input not in product_ids:
                st.warning(f"⚠️ Product ID '{product_id_input}' may not exist or have few reviews")
        
        selected_product = product_id_input
        
    else:  # Browse top products
        # Top products selection
        top_category = st.selectbox(
            "Select category:",
            [
                "Most Reviews",
                "Most Negative Reviews", 
                "Lowest Average Rating",
                "Highest Average Rating",
                "Highest Negative Percentage"
            ],
            key="top_products_category"
        )
        
        # Map display names to function parameters
        category_mapping = {
            "Most Reviews": "most_reviews",
            "Most Negative Reviews": "most_negative",
            "Lowest Average Rating": "lowest_avg_rating",
            "Highest Average Rating": "highest_avg_rating",
            "Highest Negative Percentage": "highest_negative_percentage"
        }
        
        # Get top products for selected category
        top_products = get_top_products(category_mapping[top_category])
        
        if top_products:
            # Create product selector
            product_options = [f"{pid} ({desc})" for pid, _, desc in top_products]
            product_ids = [pid for pid, _, _ in top_products]
            
            selected_product_display = st.selectbox(
                f"Select product from {top_category.lower()}:",
                product_options,
                key="top_product_selector"
            )
            
            # Extract product ID from selection
            selected_product = product_ids[product_options.index(selected_product_display)]
            
            # Show additional info about selected product
            selected_info = next((desc for pid, _, desc in top_products if pid == selected_product), "")
            st.info(f"Selected: {selected_product} - {selected_info}")
        else:
            st.error("No products found for the selected category")
            selected_product = None
    
    # Update the product_id_input for the rest of the code
    product_id_input = selected_product if selected_product else default_product_id

    # Analyze button
    if st.button("Analyze") or f"analyzed_{product_id_input}" in st.session_state:
        if product_id_input:
            try:
                # Check if we already have analysis for this product
                if f"analyzed_{product_id_input}" not in st.session_state:
                    # Show loading spinner
                    with st.spinner('Analyzing reviews...'):
                        # Invoke the app with the product ID
                        final_state = app.invoke({"product_id": product_id_input})
                    
                    # Store the analysis in session state
                    st.session_state[f"analyzed_{product_id_input}"] = final_state
                else:
                    # Use cached analysis
                    final_state = st.session_state[f"analyzed_{product_id_input}"]
                
                # Get data for metrics and charts
                reviews_df = final_state["reviews_df"]
                metrics = get_product_metrics(reviews_df)
                
                # Display product metrics
                st.markdown("## Product Overview")
                st.markdown("---")
                
                # Create columns for metrics
                col1, col2, col3, col4 = st.columns(4)
                
                with col1:
                    st.metric(
                        label="Total Reviews",
                        value=metrics['total_reviews']
                    )
                
                with col2:
                    st.metric(
                        label="Average Rating",
                        value=f"{metrics['avg_rating']:.2f}" if metrics['avg_rating'] else "N/A"
                    )
                
                with col3:
                    if metrics['first_review_date']:
                        first_date = metrics['first_review_date'].strftime("%Y-%m-%d")
                        st.markdown(f"""
                        <div style="background-color: #f0f2f6; padding: 16px; border-radius: 4px; border-left: 4px solid #ff6b6b;">
                            <p style="color: #666; font-size: 14px; margin: 0;">First Review</p>
                            <p style="color: #1f2937; font-size: 16px; font-weight: 600; margin: 4px 0 0 0;">{first_date}</p>
                        </div>
                        """, unsafe_allow_html=True)
                    else:
                        st.markdown(f"""
                        <div style="background-color: #f0f2f6; padding: 16px; border-radius: 4px; border-left: 4px solid #ff6b6b;">
                            <p style="color: #666; font-size: 14px; margin: 0;">First Review</p>
                            <p style="color: #1f2937; font-size: 16px; font-weight: 600; margin: 4px 0 0 0;">N/A</p>
                        </div>
                        """, unsafe_allow_html=True)
                
                with col4:
                    if metrics['last_review_date']:
                        last_date = metrics['last_review_date'].strftime("%Y-%m-%d")
                        st.markdown(f"""
                        <div style="background-color: #f0f2f6; padding: 16px; border-radius: 4px; border-left: 4px solid #1f77b4;">
                            <p style="color: #666; font-size: 14px; margin: 0;">Last Review</p>
                            <p style="color: #1f2937; font-size: 16px; font-weight: 600; margin: 4px 0 0 0;">{last_date}</p>
                        </div>
                        """, unsafe_allow_html=True)
                    else:
                        st.markdown(f"""
                        <div style="background-color: #f0f2f6; padding: 16px; border-radius: 4px; border-left: 4px solid #1f77b4;">
                            <p style="color: #666; font-size: 14px; margin: 0;">Last Review</p>
                            <p style="color: #1f2937; font-size: 16px; font-weight: 600; margin: 4px 0 0 0;">N/A</p>
                        </div>
                        """, unsafe_allow_html=True)
                
                # Display rating histogram
                st.markdown("## Rating Distribution")
                st.markdown("---")
                rating_histogram = create_rating_histogram(reviews_df)
                
                if rating_histogram:
                    st.plotly_chart(rating_histogram, use_container_width=True)
                    
                    # Add interactive review viewer
                    st.markdown("### 🔍 Explore Reviews by Rating")
                    
                    # Create rating selector
                    available_ratings = sorted(reviews_df['overall'].unique())
                    # Default to 1 star if available, otherwise lowest rating
                    default_index = 0 if 1 in available_ratings else 0
                    selected_rating = st.selectbox(
                        "Select rating to view reviews:",
                        available_ratings,
                        index=default_index,  # Default to 1 star (lowest rating)
                        key=f"rating_selector_{product_id_input}"
                    )
                    
                    # Filter reviews by selected rating and sort by date (newest first)
                    filtered_reviews = reviews_df[reviews_df['overall'] == selected_rating].copy()
                    filtered_reviews = filtered_reviews.sort_values('reviewTime', ascending=False)
                    
                    if not filtered_reviews.empty:
                        total_reviews = len(filtered_reviews)
                        st.write(f"**{total_reviews} reviews with {selected_rating} stars (sorted by newest first):**")
                        
                        # Pagination settings
                        reviews_per_page = 5
                        total_pages = (total_reviews + reviews_per_page - 1) // reviews_per_page
                        
                        # Initialize page state
                        page_key = f"page_{product_id_input}_{selected_rating}"
                        if page_key not in st.session_state:
                            st.session_state[page_key] = 1
                        
                        current_page = st.session_state[page_key]
                        
                        # Calculate review range for current page
                        start_idx = (current_page - 1) * reviews_per_page
                        end_idx = min(start_idx + reviews_per_page, total_reviews)
                        
                        # Show current page reviews
                        page_reviews = filtered_reviews.iloc[start_idx:end_idx]
                        
                        for idx, (_, review) in enumerate(page_reviews.iterrows(), start_idx + 1):
                            # Create a preview of the review (first 100 characters)
                            review_preview = review['reviewText'][:100] + "..." if len(review['reviewText']) > 100 else review['reviewText']
                            
                            # Format the date
                            review_date = review['reviewTime'].strftime("%Y-%m-%d") if pd.notna(review['reviewTime']) else "Unknown date"
                            
                            with st.expander(f"Review {idx} - {review_date}: {review_preview}"):
                                st.write(review['reviewText'])
                                
                                # Show additional info if available
                                if 'ProductId' in review:
                                    st.caption(f"Product ID: {review['ProductId']}")
                        
                        # Pagination controls
                        if total_pages > 1:
                            st.markdown("---")
                            col1, col2, col3, col4, col5 = st.columns([1, 1, 2, 1, 1])
                            
                            with col1:
                                if st.button("⏮️ First", disabled=(current_page == 1), key=f"first_{page_key}"):
                                    st.session_state[page_key] = 1
                                    st.rerun()
                            
                            with col2:
                                if st.button("⏪ Previous", disabled=(current_page == 1), key=f"prev_{page_key}"):
                                    st.session_state[page_key] -= 1
                                    st.rerun()
                            
                            with col3:
                                st.write(f"Page {current_page} of {total_pages} | Showing {start_idx + 1}-{end_idx} of {total_reviews} reviews")
                            
                            with col4:
                                if st.button("Next ⏩", disabled=(current_page == total_pages), key=f"next_{page_key}"):
                                    st.session_state[page_key] += 1
                                    st.rerun()
                            
                            with col5:
                                if st.button("Last ⏭️", disabled=(current_page == total_pages), key=f"last_{page_key}"):
                                    st.session_state[page_key] = total_pages
                                    st.rerun()
                    else:
                        st.info(f"No reviews found with {selected_rating} stars")
                else:
                    st.info("No rating data available for histogram")
                
                # Display the final report
                st.markdown("## Final Report")
                st.markdown("---")
                st.markdown(final_state["final_report"])
                
                # Display sentiment chart
                st.markdown("## Rating Trend Analysis")
                st.markdown("---")
                reviews_df = final_state["reviews_df"]
                sentiment_chart = create_sentiment_chart(reviews_df)
                
                if sentiment_chart:
                    st.plotly_chart(sentiment_chart, use_container_width=True)
                    
                    # Add month selector for viewing reviews
                    st.markdown("#### 📅 View Reviews by Month")
                    
                    # Get available months
                    reviews_df['year_month'] = reviews_df['reviewTime'].dt.to_period('M').astype(str)
                    available_months = sorted(reviews_df['year_month'].unique())
                    
                    selected_month = st.selectbox(
                        "Select month to view reviews:",
                        available_months,
                        index=len(available_months)-1,  # Default to latest month
                        key=f"month_selector_{product_id_input}"
                    )
                    
                    # Filter reviews for selected month
                    month_reviews = reviews_df[reviews_df['year_month'] == selected_month].copy()
                    month_reviews = month_reviews.sort_values('reviewTime', ascending=False)
                    
                    if not month_reviews.empty:
                        avg_rating = month_reviews['overall'].mean()
                        total_month_reviews = len(month_reviews)
                        
                        st.write(f"**{total_month_reviews} reviews in {selected_month} (Average: {avg_rating:.2f} stars)**")
                        
                        # Show first 5 reviews with option to see more
                        show_key = f"show_month_{product_id_input}_{selected_month}"
                        if show_key not in st.session_state:
                            st.session_state[show_key] = 5
                        
                        reviews_to_show = st.session_state[show_key]
                        
                        for idx, (_, review) in enumerate(month_reviews.head(reviews_to_show).iterrows(), 1):
                            review_date = review['reviewTime'].strftime("%Y-%m-%d")
                            stars = int(review['overall'])
                            stars_emoji = "⭐" * stars
                            
                            with st.expander(f"{review_date} - {stars_emoji} ({stars} stars)"):
                                st.write(review['reviewText'])
                        
                        # Show more button
                        if reviews_to_show < total_month_reviews:
                            if st.button(f"Show 5 more reviews (showing {reviews_to_show}/{total_month_reviews})", 
                                        key=f"more_month_{product_id_input}_{selected_month}"):
                                st.session_state[show_key] = min(reviews_to_show + 5, total_month_reviews)
                                st.rerun()
                    else:
                        st.info(f"No reviews found for {selected_month}")
                else:
                    st.info("No rating data available for chart generation")
                
                # Display review count chart
                st.markdown("## Review Volume Over Time")
                st.markdown("---")
                count_chart = create_review_count_chart(reviews_df)
                
                if count_chart:
                    st.plotly_chart(count_chart, use_container_width=True)
                else:
                    st.info("No review count data available for chart generation")
                
                # Display thematic analysis with filters
                st.markdown("## Thematic Analysis")
                st.markdown("---")
                thematic_analysis = final_state["thematic_analysis"]
                
                if thematic_analysis:
                    # Create theme selector
                    theme_options = list(thematic_analysis.keys())
                    selected_themes = st.multiselect(
                        "Select themes to explore:",
                        options=theme_options,
                        default=theme_options[:3] if len(theme_options) > 3 else theme_options,
                        key=f"theme_selector_{product_id_input}"
                    )
                    
                    # Display selected themes and their quotes
                    if selected_themes:
                        for theme in selected_themes:
                            st.subheader(f"📌 {theme}")
                            quotes = thematic_analysis[theme]
                            for i, quote in enumerate(quotes, 1):
                                st.write(f"{i}. *\"{quote}\"*")
                            st.markdown("---")
                    else:
                        st.info("Select themes above to see related quotes")
                else:
                    st.info("No thematic analysis available")
                
            except Exception as e:
                st.error(f"Error during analysis: {str(e)}")
        else:
            st.warning("Please enter a product ID")

elif page == "User Analytics":
    st.header("👤 User Analytics")
    
    # Get all users
    all_users = get_all_users()
    
    if all_users:
        # User selection method
        search_method = st.radio(
            "Choose how to select user:",
            ["Browse top users", "Search by User ID"],
            key="user_search_method"
        )
        
        if search_method == "Browse top users":
            # Create user selector with review count info
            user_options = [f"{user_id} ({count} reviews)" for user_id, count in all_users[:100]]  # Top 100 users
            user_ids = [user_id for user_id, count in all_users[:100]]
            
            selected_user_display = st.selectbox(
                "Select User to Analyze:",
                user_options,
                key="user_selector"
            )
            
            # Extract user ID from selection
            selected_user = user_ids[user_options.index(selected_user_display)]
            
        else:  # Search by User ID
            search_user_id = st.text_input(
                "Enter User ID to search:",
                placeholder="e.g., A1D87F6ZCVE5NK",
                key="user_search_input"
            )
            
            if search_user_id:
                # Check if user exists
                user_dict = {user_id: count for user_id, count in all_users}
                if search_user_id in user_dict:
                    selected_user = search_user_id
                    st.success(f"✅ User found: {search_user_id} ({user_dict[search_user_id]} reviews)")
                else:
                    st.error(f"❌ User ID '{search_user_id}' not found in dataset")
                    selected_user = None
            else:
                selected_user = None
        
        if st.button("Analyze User", disabled=(selected_user is None)):
            analytics = get_user_analytics(selected_user)
            
            if analytics:
                # Display user overview
                st.markdown("## User Overview")
                st.markdown("---")
                
                col1, col2, col3, col4 = st.columns(4)
                
                with col1:
                    st.metric("Total Reviews", analytics['total_reviews'])
                
                with col2:
                    st.metric("Average Rating", f"{analytics['avg_rating']:.2f}")
                
                with col3:
                    st.metric("Products Reviewed", analytics['unique_products'])
                
                with col4:
                    st.metric("Most Common Rating", f"{analytics['most_common_rating']} ⭐")
                
                # Profile info
                st.write(f"**Profile Name:** {analytics['profile_name']}")
                st.write(f"**Active Period:** {analytics['first_review'].strftime('%Y-%m-%d')} to {analytics['last_review'].strftime('%Y-%m-%d')}")
                
                # Rating distribution
                st.markdown("## Rating Distribution")
                st.markdown("---")
                
                rating_dist = analytics['rating_distribution']
                rating_df = pd.DataFrame([
                    {"Rating": f"{r} ⭐", "Count": rating_dist.get(r, 0)} 
                    for r in range(1, 6)
                ])
                
                fig_rating = px.bar(
                    rating_df,
                    x='Rating',
                    y='Count',
                    title="User's Rating Distribution",
                    color_discrete_sequence=['#1f77b4']
                )
                st.plotly_chart(fig_rating, use_container_width=True)
                
                # Activity timeline
                st.markdown("## Review Activity Timeline")
                st.markdown("---")
                
                activity_df = pd.DataFrame({
                    'Date': analytics['activity_by_date'].index,
                    'Reviews': analytics['activity_by_date'].values
                })
                
                fig_timeline = px.scatter(
                    activity_df,
                    x='Date',
                    y='Reviews',
                    title="Review Activity Over Time",
                    size='Reviews',
                    size_max=20
                )
                fig_timeline.update_layout(yaxis=dict(dtick=1))
                st.plotly_chart(fig_timeline, use_container_width=True)
                
                # Suspicious patterns check
                st.markdown("## Pattern Analysis")
                st.markdown("---")
                
                # Check for suspicious patterns
                suspicious_patterns = []
                
                # Pattern 1: All same rating
                if len(rating_dist) == 1:
                    suspicious_patterns.append("🚩 User gives only one rating value")
                
                # Pattern 2: Multiple reviews same day
                max_reviews_per_day = analytics['activity_by_date'].max()
                if max_reviews_per_day > 5:
                    suspicious_patterns.append(f"🚩 {max_reviews_per_day} reviews in a single day")
                
                # Pattern 3: Very high or very low average
                if analytics['avg_rating'] >= 4.8 or analytics['avg_rating'] <= 1.5:
                    suspicious_patterns.append(f"🚩 Extreme average rating: {analytics['avg_rating']:.2f}")
                
                if suspicious_patterns:
                    st.warning("**Potential Suspicious Patterns:**")
                    for pattern in suspicious_patterns:
                        st.write(pattern)
                else:
                    st.success("✅ No obvious suspicious patterns detected")
                
                # Show recent reviews
                st.markdown("## Recent Reviews")
                st.markdown("---")
                
                reviews_df = analytics['reviews_df'].sort_values('reviewTime', ascending=False)
                
                for idx, (_, review) in enumerate(reviews_df.head(5).iterrows(), 1):
                    stars = "⭐" * int(review['Score'])
                    date = review['reviewTime'].strftime('%Y-%m-%d')
                    
                    with st.expander(f"{date} - Product {review['ProductId']} - {stars}"):
                        st.write(f"**Review:** {review['Text']}")
                        if 'Summary' in review:
                            st.write(f"**Summary:** {review['Summary']}")
            else:
                st.error(f"No data found for user: {selected_user}")
    else:
        st.error("No users found in the dataset")

elif page == "Date Analytics":
    st.header("📅 Date Analytics")
    
    # Get available dates
    available_dates = get_all_review_dates()
    
    if available_dates:
        # Date selector
        selected_date = st.date_input(
            "Select Date for Analysis:",
            value=available_dates[-1] if available_dates else None,
            min_value=min(available_dates) if available_dates else None,
            max_value=max(available_dates) if available_dates else None
        )
        
        if st.button("Analyze Date"):
            # Get reviews for selected date
            date_reviews = get_reviews_by_date(str(selected_date))
            
            if not date_reviews.empty:
                # Display date overview
                st.markdown("## Date Overview")
                st.markdown("---")
                
                total_reviews = len(date_reviews)
                avg_rating = date_reviews['overall'].mean()
                
                col1, col2 = st.columns(2)
                with col1:
                    st.metric("Total Reviews", total_reviews)
                with col2:
                    st.metric("Average Rating", f"{avg_rating:.2f}")
                
                # Display products with reviews
                st.markdown("## Products with Reviews")
                st.markdown("---")
                
                product_stats = date_reviews.groupby('ProductId').agg({
                    'overall': ['count', 'mean'],
                    'reviewText': 'first'
                }).round(2)
                
                product_stats.columns = ['Review Count', 'Avg Rating', 'Sample Review']
                product_stats = product_stats.sort_values('Avg Rating')
                
                # Show problematic products (rating < 3)
                problematic_products = product_stats[product_stats['Avg Rating'] < 3]
                
                if not problematic_products.empty:
                    st.markdown("### ⚠️ Problematic Products (Rating < 3)")
                    
                    for product_id, row in problematic_products.iterrows():
                        with st.expander(f"Product {product_id} - Rating: {row['Avg Rating']:.1f} ({row['Review Count']} reviews)"):
                            st.write(f"**Sample Review:** {row['Sample Review'][:200]}...")
                            
                            # Add button to analyze this product
                            if st.button(f"Analyze Product {product_id}", key=f"analyze_{product_id}"):
                                # Set session state to switch to product analysis
                                st.session_state.selected_product_id = product_id
                                st.session_state.switch_to_product_analysis = True
                                st.rerun()
                
                # Show all products
                st.markdown("### All Products")
                st.dataframe(product_stats, use_container_width=True)
                
                # Show low rating reviews
                low_rating_reviews = date_reviews[date_reviews['overall'] <= 2]
                if not low_rating_reviews.empty:
                    st.markdown("### 🔴 Low Rating Reviews (≤ 2 stars)")
                    
                    for idx, review in low_rating_reviews.iterrows():
                        with st.expander(f"Product {review['ProductId']} - {review['overall']} stars"):
                            st.write(review['reviewText'])
                            if st.button(f"Analyze Product {review['ProductId']}", key=f"analyze_low_{idx}"):
                                st.session_state.selected_product_id = review['ProductId']
                                st.session_state.switch_to_product_analysis = True
                                st.rerun()
            else:
                st.info(f"No reviews found for {selected_date}")
    else:
        st.error("No review dates available in the dataset")

# Handle page switching from date analytics
if 'switch_to_product_analysis' in st.session_state and st.session_state.switch_to_product_analysis:
    st.session_state.switch_to_product_analysis = False
    st.sidebar.selectbox(
        "Select Page",
        ["Product Analysis", "Date Analytics"],
        index=0  # Switch to Product Analysis
    )
    st.rerun()