"""
Test script for the updated YouTrack MCP client
"""
import asyncio
import sys
import os
import pytest

# Add the app directory to Python path
sys.path.insert(0, '/app')


@pytest.fixture(scope="session")
async def youtrack_client():
    """Fixture to create YouTrack MCP client for testing"""
    from src.services.youtrack_client import YouTrackMCPClient
    
    async with YouTrackMCPClient("http://mcp_youtrack:8002/mcp") as client:
        yield client


async def test_search_issues(youtrack_client):
    """Test 1: Search Issues"""
    print("=== Test 1: Search Issues ===")
    try:
        result = await youtrack_client.search_issues("project: INT", max_results=3)
        print(f"✓ Search successful")
        print(f"  Total found: {result.get('total', 0)}")
        print(f"  Issues returned: {len(result.get('issues', []))}")
        if result.get('issues'):
            print(f"  First issue: {result['issues'][0].get('summary', 'N/A')}")
        assert result is not None
        assert 'total' in result
    except Exception as e:
        print(f"✗ Search failed: {e}")
        raise


async def test_create_issue_and_operations(youtrack_client):
    """Test 2-4: Create Issue, Add Comment, Get Details"""
    print("=== Test 2: Create Issue ===")
    try:
        result = await youtrack_client.create_issue(
            project="INT",
            summary="[TEST] Updated Client Test",
            description="Testing the updated YouTrack MCP client",
            issue_type="Bug",
            priority="Minor",
            tags=["test", "client-update"]
        )
        print(f"✓ Issue created successfully")
        issue_id = result.get('id')
        print(f"  Issue ID: {issue_id}")
        print(f"  URL: {result.get('url', 'N/A')}")
        
        assert result is not None
        assert issue_id is not None
        
        # Test 3: Add comment to created issue
        if issue_id:
            print("\n=== Test 3: Add Comment ===")
            try:
                comment_result = await youtrack_client.add_comment(
                    issue_id=issue_id,
                    text="This comment was added by the updated YouTrack MCP client!"
                )
                print(f"✓ Comment added successfully")
                print(f"  Comment ID: {comment_result.get('id', 'N/A')}")
                assert comment_result is not None
            except Exception as e:
                print(f"✗ Add comment failed: {e}")
                raise
            
            # Test 4: Get issue details
            print("\n=== Test 4: Get Issue Details ===")
            try:
                issue_details = await youtrack_client.get_issue(issue_id)
                print(f"✓ Retrieved issue details")
                print(f"  Summary: {issue_details.get('summary', 'N/A')}")
                print(f"  State: {issue_details.get('state', 'N/A')}")
                print(f"  Comments: {len(issue_details.get('comments', []))}")
                assert issue_details is not None
                assert 'summary' in issue_details
            except Exception as e:
                print(f"✗ Get issue details failed: {e}")
                raise
                
    except Exception as e:
        print(f"✗ Create issue failed: {e}")
        raise


async def test_get_projects(youtrack_client):
    """Test 5: Get Projects"""
    print("=== Test 5: Get Projects ===")
    try:
        projects_result = await youtrack_client.get_projects()
        print(f"✓ Retrieved projects")
        projects = projects_result.get('projects', [])
        print(f"  Projects count: {len(projects)}")
        if projects:
            for project in projects[:3]:  # Show first 3
                print(f"  - {project.get('shortName', 'N/A')}: {project.get('name', 'N/A')}")
        assert projects_result is not None
        assert 'projects' in projects_result
    except Exception as e:
        print(f"✗ Get projects failed: {e}")
        raise