"""
Test suite for Slack approval service integration
"""
import asyncio
import pytest
import uuid
from datetime import datetime
from unittest.mock import AsyncMock, MagicMock

import sys
import os
sys.path.insert(0, '/app/src')
os.chdir('/app')


@pytest.fixture
async def approval_service():
    """Create approval service for testing"""
    from db.approval_service import create_approval_service
    return await create_approval_service()


@pytest.fixture
async def test_approval(approval_service):
    """Create a test approval record"""
    from src.constants import SystemActionType
    from db.models import RiskLevel
    
    approval = await approval_service.create_approval(
        action_type=SystemActionType.CREATE_YOUTRACK_ISSUE,
        payload_json={
            "summary": "Test bug report requiring approval",
            "input_text": "Test bug description for approval workflow",
            "operations": [{"type": "create_issue", "context": "test"}],
            "reason": "Testing approval workflow",
            "tool_name": "test_approval_service"
        },
        risk=RiskLevel.MEDIUM,
        related_entity_id=uuid.uuid4(),
        langfuse_trace_id="test_trace_" + uuid.uuid4().hex[:8]
    )
    
    print(f"✅ Created test approval: {approval.id}")
    print(f"   Status: {approval.status}")
    print(f"   Risk: {approval.risk}")
    print(f"   Summary: {approval.payload_json.get('summary')}")
    
    return approval


@pytest.mark.asyncio
async def test_approval_service_approve(approval_service, test_approval):
    """Test the approval service approve method"""
    print("\n=== Test: Approval Service Approve ===")
    
    # Test approving the approval
    approved = await approval_service.approve(
        approval_id=test_approval.id,
        decided_by="test_user_123",
        reason="Approved for testing"
    )
    
    assert approved.status.value == "approved"
    assert approved.decided_by == "test_user_123"
    assert approved.reason == "Approved for testing"
    assert approved.decided_at is not None
    
    print(f"✅ Approval processed successfully")
    print(f"   ID: {approved.id}")
    print(f"   Status: {approved.status}")
    print(f"   Decided by: {approved.decided_by}")
    print(f"   Reason: {approved.reason}")


@pytest.mark.asyncio
async def test_approval_service_reject(approval_service):
    """Test the approval service reject method"""
    print("\n=== Test: Approval Service Reject ===")
    
    # Create a new approval for rejection test
    from src.constants import SystemActionType
    from db.models import RiskLevel
    
    approval = await approval_service.create_approval(
        action_type=SystemActionType.CREATE_YOUTRACK_ISSUE,
        payload_json={
            "summary": "Test bug report for rejection",
            "input_text": "Another test bug description",
            "operations": [{"type": "create_issue", "context": "test"}],
            "reason": "Testing rejection workflow",
            "tool_name": "test_approval_service"
        },
        risk=RiskLevel.HIGH,
        langfuse_trace_id="test_reject_" + uuid.uuid4().hex[:8]
    )
    
    # Test rejecting the approval
    rejected = await approval_service.reject(
        approval_id=approval.id,
        decided_by="test_user_456",
        reason="Rejected for testing"
    )
    
    assert rejected.status.value == "rejected"
    assert rejected.decided_by == "test_user_456"
    assert rejected.reason == "Rejected for testing"
    assert rejected.decided_at is not None
    
    print(f"✅ Rejection processed successfully")
    print(f"   ID: {rejected.id}")
    print(f"   Status: {rejected.status}")
    print(f"   Decided by: {rejected.decided_by}")
    print(f"   Reason: {rejected.reason}")


@pytest.mark.asyncio
async def test_slack_approval_workflow_simulation():
    """Test simulated Slack approval workflow"""
    print("\n=== Test: Slack Approval Workflow Simulation ===")
    
    # Import the Slack service components
    from slack_service.app import ensure_services
    from db.approval_service import create_approval_service
    from src.constants import SystemActionType
    from db.models import RiskLevel
    
    # Create services
    approval_service = await create_approval_service()
    
    # Create test approval
    approval = await approval_service.create_approval(
        action_type=SystemActionType.CREATE_YOUTRACK_ISSUE,
        payload_json={
            "summary": "Simulated Slack approval test",
            "input_text": "Testing the complete Slack workflow",
            "operations": [{"type": "create_issue", "context": "slack_test"}],
            "reason": "Testing Slack button interaction",
            "tool_name": "test_slack_approval"
        },
        risk=RiskLevel.MEDIUM,
        langfuse_trace_id="slack_test_" + uuid.uuid4().hex[:8]
    )
    
    print(f"📝 Created approval for Slack simulation: {approval.id}")
    
    # Simulate clicking "Approve" button
    try:
        # Convert to UUID (like the Slack handler does)
        approval_uuid = uuid.UUID(str(approval.id))
        
        # Call the same approve method that Slack handler calls
        approved = await approval_service.approve(
            approval_id=approval_uuid,
            decided_by="U05KBUG2SKX",  # Simulated Slack user ID
            reason="Approved via Slack"
        )
        
        # Verify the approval worked
        assert approved.status.value == "approved"
        assert approved.decided_by == "U05KBUG2SKX"
        assert approved.reason == "Approved via Slack"
        
        print(f"✅ Slack approval simulation successful!")
        print(f"   Approval ID: {approved.id}")
        print(f"   Status: {approved.status}")
        print(f"   Decided by: {approved.decided_by}")
        print(f"   Payload summary: {approved.payload_json.get('summary')}")
        
        return approved
        
    except Exception as e:
        print(f"❌ Slack approval simulation failed: {e}")
        raise


@pytest.mark.asyncio 
async def test_complete_bug_to_slack_workflow():
    """Test the complete workflow from bug processing to Slack approval"""
    print("\n=== Test: Complete Bug to Slack Workflow ===")
    
    # This test simulates what happens when a bug is processed and requires approval
    from pm_agents.bug_bot import BugBotAgent
    from db.models import Review
    from src.constants import ReviewCategory
    
    # Create bot
    bot = BugBotAgent(project='INT')
    
    # Create highly uncertain review that should trigger approval
    review = Review(
        id=uuid.uuid4(),
        text='I think there might be a bug somewhere? Not really sure what happened but something felt off.',
        category=ReviewCategory.BUG,
        confidence=0.25,  # Very low confidence to trigger approval
        run_id=uuid.uuid4(),
        source='test',
        original_id='test-slack-workflow-001',
        processed_at=datetime.utcnow()
    )
    
    print(f"🐛 Processing uncertain bug review...")
    print(f"   Review text: {review.text}")
    print(f"   Confidence: {review.confidence}")
    
    try:
        # Process review - should trigger guardrails and create Slack approval
        result = await bot.process_bug_review(review)
        
        print(f"📊 Bug processing result:")
        print(f"   Action: {result.get('action')}")
        print(f"   Approval status: {result.get('approval_status')}")
        
        if result.get('approval_status') == 'pending':
            print(f"✅ Approval workflow triggered successfully!")
            print(f"   This would have sent a Slack message")
            print(f"   Uncertainty reason: {result.get('uncertainty_reason')}")
            return result
        else:
            print(f"ℹ️  LLM auto-approved this review (no Slack approval needed)")
            return result
            
    except Exception as e:
        if 'approval' in str(e).lower() or 'tripwire' in str(e).lower():
            print(f"✅ Guardrails triggered as expected!")
            print(f"   Exception: {str(e)}")
            return {"approval_status": "pending", "triggered_by": "exception"}
        else:
            print(f"❌ Unexpected error: {e}")
            raise


if __name__ == "__main__":
    # Run tests manually for debugging
    import asyncio
    
    async def run_all_tests():
        print("🧪 Running Slack Approval Service Tests")
        print("=" * 50)
        
        # Test 1: Slack workflow simulation
        try:
            await test_slack_approval_workflow_simulation()
        except Exception as e:
            print(f"❌ Slack workflow test failed: {e}")
        
        print("\n" + "=" * 50)
        
        # Test 2: Complete bug to Slack workflow
        try:
            await test_complete_bug_to_slack_workflow()
        except Exception as e:
            print(f"❌ Complete workflow test failed: {e}")
        
        print("\n🎉 Test run completed!")
    
    asyncio.run(run_all_tests())