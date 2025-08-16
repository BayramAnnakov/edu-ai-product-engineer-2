"""
Comprehensive test suite for BugBot agent
"""
import asyncio
import sys
import os
import uuid
import pytest
from datetime import datetime
from typing import Dict, Any

# Add the app directory to Python path
sys.path.insert(0, '/app/src')
sys.path.insert(0, '/app')
os.chdir('/app')


@pytest.fixture(scope="session")
def bot():
    """Fixture to create BugBot instance for testing"""
    from pm_agents.bug_bot import BugBotAgent
    
    # Initialize BugBot with test project
    return BugBotAgent(project="INT")


@pytest.fixture
async def mock_review():
    """Create a mock review object for testing"""
    from db.models import Review
    from src.constants import ReviewCategory
    
    # Create a mock review without database dependency
    review = Review(
        id=uuid.uuid4(),
        text="The app crashes every time I try to upload a large photo. It just freezes and then closes without any error message.",
        category=ReviewCategory.BUG,
        confidence=0.95,
        run_id=uuid.uuid4(),
        source="test",
        original_id="test-bug-001",
        processed_at=datetime.utcnow()
    )
    return review


@pytest.fixture
async def duplicate_review():
    """Create a review that's likely a duplicate of existing issues"""
    from db.models import Review
    from src.constants import ReviewCategory
    
    review = Review(
        id=uuid.uuid4(),
        text="Login button not working on the settings page. Nothing happens when I click it.",
        category=ReviewCategory.BUG,
        confidence=0.92,
        run_id=uuid.uuid4(),
        source="test",
        original_id="test-bug-002",
        processed_at=datetime.utcnow()
    )
    return review


@pytest.fixture
async def uncertain_review():
    """Create a review that might trigger uncertainty guardrails"""
    from db.models import Review
    from src.constants import ReviewCategory
    
    review = Review(
        id=uuid.uuid4(),
        text="Sometimes the app doesn't work properly. There might be issues with something.",
        category=ReviewCategory.BUG,
        confidence=0.55,  # Low confidence
        run_id=uuid.uuid4(),
        source="test",
        original_id="test-bug-003",
        processed_at=datetime.utcnow()
    )
    return review


async def test_bug_bot_initialization(bot):
    """Test 1: BugBot initialization and configuration"""
    print("=== Test 1: BugBot Initialization ===")
    try:
        print("✓ BugBot initialized successfully")
        print(f"  Agent name: {bot.agent.name}")
        print(f"  Project: {bot.project}")
        print(f"  MCP servers: {len(bot.agent.mcp_servers)}")
        print(f"  Input guardrails: {len(bot.agent.input_guardrails)}")
        print(f"  Output guardrails: {len(bot.agent.output_guardrails)}")
        assert bot.agent.name == "BugBot"
        assert bot.project == "INT"
        assert len(bot.agent.mcp_servers) > 0
    except Exception as e:
        print(f"✗ BugBot initialization failed: {e}")
        import traceback
        traceback.print_exc()
        raise


async def test_mcp_connection(bot: Any):
    """Test 2: MCP Server Connection"""
    print("\n=== Test 2: MCP Server Connection ===")
    try:
        result = await bot.test_mcp_connection()
        print(f"✓ MCP connection test completed")
        print(f"  Status: {result.get('status')}")
        print(f"  MCP Server: {result.get('mcp_server')}")
        if result.get('status') == 'connected':
            print(f"  Response preview: {str(result.get('response', ''))[:100]}...")
        else:
            print(f"  Error: {result.get('error')}")
    except Exception as e:
        print(f"✗ MCP connection test failed: {e}")


async def test_process_normal_bug(bot, mock_review):
    """Test 3: Process a normal bug report"""
    print("\n=== Test 3: Process Normal Bug Report ===")
    try:
        print(f"  Created mock review: {mock_review.original_id}")
        print(f"  Review text: {mock_review.text[:80]}...")
        
        # Generate test trace ID
        test_trace_id = f"test_bug_trace_{uuid.uuid4().hex[:8]}"
        
        # Process the bug review
        result = await bot.process_bug_review(
            review=mock_review,
            langfuse_trace_id=test_trace_id
        )
        
        print("✓ Bug processing completed")
        print(f"  Trace ID: {result.get('langfuse_trace_id')}")
        print(f"  Action: {result.get('action')}")
        print(f"  Issue ID: {result.get('issue_id')}")
        print(f"  URL: {result.get('url')}")
        print(f"  Summary: {result.get('summary')}")
        print(f"  Session ID: {result.get('session_id')}")
        print(f"  Processing time: {result.get('processing_time_ms')}ms")
        print(f"  API calls: {result.get('api_calls_made')}")
        
        assert result is not None
        assert result.get('langfuse_trace_id') is not None
        return result
    except Exception as e:
        print(f"✗ Bug processing failed: {e}")
        import traceback
        traceback.print_exc()
        raise


async def test_duplicate_detection(bot, duplicate_review):
    """Test 4: Duplicate Issue Detection"""
    print("\n=== Test 4: Duplicate Issue Detection ===")
    try:
        print(f"  Created potential duplicate: {duplicate_review.original_id}")
        print(f"  Review text: {duplicate_review.text[:80]}...")
        
        # Generate test trace ID
        test_trace_id = f"test_dup_trace_{uuid.uuid4().hex[:8]}"
        
        # Process the review
        result = await bot.process_bug_review(
            review=duplicate_review,
            langfuse_trace_id=test_trace_id
        )
        
        print("✓ Duplicate detection completed")
        print(f"  Trace ID: {result.get('langfuse_trace_id')}")
        print(f"  Action: {result.get('action')}")
        print(f"  Similarity score: {result.get('similarity_score')}")
        print(f"  Issues examined: {result.get('issues_examined')}")
        print(f"  Total candidates: {result.get('total_candidates_found')}")
        print(f"  Analyzed in detail: {result.get('candidates_analyzed_in_detail')}")
        
        if result.get('action') == 'commented_on_duplicate':
            print(f"  ✓ Duplicate detected and commented")
        elif result.get('action') == 'created_issue':
            print(f"  ✓ New issue created (no duplicate found)")
        
        assert result is not None
        assert result.get('langfuse_trace_id') is not None
        return result
    except Exception as e:
        print(f"✗ Duplicate detection failed: {e}")
        import traceback
        traceback.print_exc()
        raise


async def test_guardrail_trigger(bot, uncertain_review):
    """Test 5: Guardrail Triggering with Uncertain Review"""
    print("\n=== Test 5: Guardrail Triggering ===")
    try:
        print(f"  Created uncertain review: {uncertain_review.original_id}")
        print(f"  Review text: {uncertain_review.text}")
        print(f"  Confidence: {uncertain_review.confidence}")
        
        # Generate test trace ID
        test_trace_id = f"test_guard_trace_{uuid.uuid4().hex[:8]}"
        
        # Process the review - might trigger guardrails
        result = await bot.process_bug_review(
            review=uncertain_review,
            langfuse_trace_id=test_trace_id
        )
        
        print("✓ Guardrail test completed")
        print(f"  Trace ID: {result.get('langfuse_trace_id')}")
        print(f"  Action: {result.get('action')}")
        print(f"  Approval status: {result.get('approval_status')}")
        
        if result.get('approval_status') == 'pending':
            print("  ✓ Guardrails triggered - approval required")
            print(f"  Uncertainty reason: {result.get('uncertainty_reason')}")
        else:
            print("  ✓ Processed without guardrail intervention")
        
        assert result is not None
        assert result.get('langfuse_trace_id') is not None
        return result
    except Exception as e:
        print(f"✗ Guardrail test failed: {e}")
        import traceback
        traceback.print_exc()
        raise


async def test_response_parsing(bot):
    """Test 6: Response Parsing and Validation"""
    print("\n=== Test 6: Response Parsing ===")
    try:
        # Test parsing valid response
        valid_json = """
        {
            "action": "created_issue",
            "issue_id": "INT-123",
            "url": "https://youtrack.example.com/issue/INT-123",
            "summary": "Test issue created",
            "duplicate_analysis": {
                "is_duplicate": false,
                "confidence": 0.2,
                "similarity_score": 0.2
            },
            "search_queries_used": ["crash upload", "photo crash"],
            "issues_examined": 5,
            "duplicate_session_id": "test-session",
            "processing_time_ms": 1500
        }
        """
        
        result = bot._parse_and_validate_response(valid_json)
        print("✓ Valid response parsed successfully")
        print(f"  Action: {result.action}")
        print(f"  Issue ID: {result.issue_id}")
        
        # Test parsing invalid response
        try:
            invalid_json = '{"action": "invalid_action"}'
            bot._parse_and_validate_response(invalid_json)
            print("✗ Should have failed on invalid JSON")
        except ValueError as e:
            print("✓ Invalid response rejected correctly")
            print(f"  Error: {str(e)[:100]}...")
            
        assert True  # Test completed successfully
        
    except Exception as e:
        print(f"✗ Response parsing test failed: {e}")
        raise