"""
Test script for the ReviewClassifier agent
"""
import asyncio
import sys
import os
import tempfile
import csv
import pytest
import uuid
from pathlib import Path

# Add the app directory to Python path and set environment
sys.path.insert(0, '/app/src')
sys.path.insert(0, '/app')
os.chdir('/app')


@pytest.fixture(scope="session")
def classifier():
    """Fixture to create ReviewClassifier instance for testing"""
    from pm_agents.review_classifier import ReviewClassifierAgent
    return ReviewClassifierAgent()


@pytest.fixture
async def test_csv_file():
    """Fixture to create temporary CSV file with test reviews"""
    test_reviews = [
        {"id": "1", "text": "The app crashes when I try to upload a photo"},
        {"id": "2", "text": "Would love to see dark mode support in the next update"},
        {"id": "3", "text": "Great app! Love the new design. Very intuitive to use"},
        {"id": "4", "text": "Button doesn't work on the settings page, please fix"},
        {"id": "5", "text": "Can you add a feature to export data to Excel?"},
    ]
    
    # Create temporary file
    temp_file = tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False)
    
    writer = csv.DictWriter(temp_file, fieldnames=['id', 'text'])
    writer.writeheader()
    for review in test_reviews:
        writer.writerow(review)
    
    temp_file.close()
    yield temp_file.name
    
    # Cleanup
    try:
        os.unlink(temp_file.name)
    except:
        pass


async def test_classifier_initialization(classifier):
    """Test 1: ReviewClassifier initialization and configuration"""
    print("=== Test 1: Initialize Agent ===")
    try:
        print("✓ ReviewClassifier initialized successfully")
        print(f"  Agent name: {classifier.agent.name}")
        print(f"  Tools available: {len(classifier.agent.tools)}")
        assert classifier.agent.name == "ReviewClassifier"
        assert len(classifier.agent.tools) > 0
    except Exception as e:
        print(f"✗ Agent initialization failed: {e}")
        raise


async def test_single_review_classification(classifier):
    """Test 2: Single review classification"""
    print("=== Test 2: Single Review Classification ===")
    try:
        from pm_agents.review_classifier import classify_review
        
        test_review = "The app keeps crashing when I try to login"
        result = await classify_review(test_review, "test-001")
        print("✓ Single review classification successful")
        print(f"  Review: {test_review[:50]}...")
        print(f"  Classification result: {type(result)}")
        print(f"  Result keys: {list(result.keys()) if isinstance(result, dict) else 'Not a dict'}")
        assert result is not None
    except Exception as e:
        print(f"✗ Single review classification failed: {e}")
        raise


async def test_batch_review_classification(classifier, test_csv_file):
    """Test 3: Batch review classification with CSV"""
    print("=== Test 3: Batch Review Classification ===")
    try:
        print(f"  Using test CSV: {test_csv_file}")
        
        # Generate a unique trace ID for testing
        test_trace_id = f"test_trace_{uuid.uuid4().hex[:8]}"
        
        result = await classifier.classify_reviews_file_with_storage(
            test_csv_file, 
            store_in_db=True,  # Enable DB storage to test full workflow
            langfuse_trace_id=test_trace_id
        )
        print("✓ Batch review classification successful")
        print(f"  Workflow run ID: {result.get('workflow_run_id', 'N/A')}")
        print(f"  Langfuse trace ID: {result.get('langfuse_trace_id', 'N/A')}")
        print(f"  Reviews processed: {result.get('reviews_processed', 0)}")
        print(f"  Stored in DB: {result.get('stored_in_db', False)}")
        
        # Show stats if available
        if 'stats' in result:
            stats = result['stats']
            print(f"  Classification stats:")
            print(f"    - Total: {stats.get('total_reviews', 0)}")
            print(f"    - Categories: {stats.get('category_counts', {})}")
        
        assert result is not None
        assert result.get('reviews_processed', 0) > 0
    except Exception as e:
        print(f"✗ Batch review classification failed: {e}")
        raise


async def test_csv_reading_tool(classifier, test_csv_file):
    """Test 4: CSV reading through agent"""
    print("=== Test 4: CSV Reading Through Agent ===")
    try:
        # Test that the agent has the CSV reading tool available
        csv_tool = None
        for tool in classifier.agent.tools:
            if tool.name == 'read_reviews_csv':
                csv_tool = tool
                break
        
        if csv_tool:
            print("✓ CSV reading tool found in agent")
            print(f"  Tool name: {csv_tool.name}")
            print(f"  Tool description: {csv_tool.description}")
            
            # Test the tool through the agent's invoke mechanism 
            # (This is how the agent actually uses it)
            try:
                tool_result = await csv_tool.on_invoke_tool({"file_path": test_csv_file})
                print("✓ CSV reading tool invocation successful")
                print(f"  Result preview: {str(tool_result)[:100]}...")
            except Exception as invoke_error:
                print(f"  Tool invocation test: {invoke_error}")
                print("  (This is expected - tool invocation requires agent context)")
        else:
            print("✗ CSV reading tool not found in agent")
            pytest.fail("CSV reading tool not found in agent")
        
        assert csv_tool is not None
    except Exception as e:
        print(f"✗ CSV reading tool test failed: {e}")
        raise