import os
import pandas as pd
from typing import List, Dict, Any, TypedDict
from dotenv import load_dotenv
from langchain_google_genai import ChatGoogleGenerativeAI
from langgraph.graph import StateGraph, END

# Load environment variables from .env file
load_dotenv()

# Initialize Gemini model
llm = ChatGoogleGenerativeAI(
    model="gemini-1.5-flash-latest",
    google_api_key=os.getenv("GOOGLE_API_KEY")
)

def get_reviews_for_product(product_id: str) -> List[str]:
    """
    Read reviews from CSV file and return all review texts for a specific product.
    
    Args:
        product_id: The ID of the product to get reviews for
        
    Returns:
        List of review texts for the specified product
    """
    try:
        # Read the reviews CSV file
        df = pd.read_csv('data/reviews.csv')
        
        # Filter reviews for the specific product ID
        product_reviews = df[df['ProductId'] == product_id]
        
        # Extract review texts, handling potential column name variations
        if 'reviewText' in df.columns:
            review_texts = product_reviews['reviewText'].dropna().tolist()
        elif 'Text' in df.columns:
            review_texts = product_reviews['Text'].dropna().tolist()
        else:
            # Try to find a column that might contain review text
            text_columns = [col for col in df.columns if 'text' in col.lower() or 'review' in col.lower()]
            if text_columns:
                review_texts = product_reviews[text_columns[0]].dropna().tolist()
            else:
                raise ValueError("Could not find review text column in CSV")
        
        return review_texts
        
    except FileNotFoundError:
        print("Error: reviews.csv file not found in data directory")
        return []
    except Exception as e:
        print(f"Error reading reviews: {str(e)}")
        return []


class GraphState(TypedDict):
    """
    State structure for the LangGraph application.
    This defines all the data that will be passed between nodes in the graph.
    """
    product_id: str
    reviews: List[str]
    extractive_summary: str
    abstractive_summary: str
    final_report: str


def fetch_reviews_node(state: GraphState) -> Dict[str, Any]:
    """
    Node to fetch reviews for a given product ID.
    
    Args:
        state: Current graph state containing product_id
        
    Returns:
        Dictionary with reviews to update the state
    """
    product_id = state["product_id"]
    reviews = get_reviews_for_product(product_id)
    return {"reviews": reviews}


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
5. Heading 'Comparison and Verdict', where you briefly compare their usefulness and give a final recommendation.

Extractive Summary:
{extractive_summary}

Abstractive Summary:
{abstractive_summary}"""
    
    # Call LLM
    response = llm.invoke(prompt)
    final_report = response.content
    
    return {"final_report": final_report}


# Create the workflow graph
workflow = StateGraph(GraphState)

# Add all nodes to the graph
workflow.add_node("fetch_reviews", fetch_reviews_node)
workflow.add_node("extractive_summarizer", extractive_summarizer_node)
workflow.add_node("abstractive_summarizer", abstractive_summarizer_node)
workflow.add_node("final_report", final_report_node)

# Set fetch_reviews as the entry point
workflow.set_entry_point("fetch_reviews")

# Define edges: after fetch_reviews, run both summarizers in parallel
workflow.add_edge("fetch_reviews", "extractive_summarizer")
workflow.add_edge("fetch_reviews", "abstractive_summarizer")

# After both summarizers complete, run final_report
workflow.add_edge("extractive_summarizer", "final_report")
workflow.add_edge("abstractive_summarizer", "final_report")

# Set final_report as the end point
workflow.add_edge("final_report", END)

# Compile the graph
app = workflow.compile()

# Main execution block
if __name__ == "__main__":
    # Define the product ID to analyze
    product_id_to_analyze = "B001GVISJM"  # This product has multiple reviews in the dataset
    
    # Run the application
    print(f"Analyzing reviews for product: {product_id_to_analyze}")
    print("=" * 50)
    
    try:
        # Invoke the app with the product ID
        final_state = app.invoke({"product_id": product_id_to_analyze})
        
        # Print the final report
        print("\nFINAL REPORT:")
        print("=" * 50)
        print(final_state["final_report"])
        
    except Exception as e:
        print(f"Error during analysis: {str(e)}")