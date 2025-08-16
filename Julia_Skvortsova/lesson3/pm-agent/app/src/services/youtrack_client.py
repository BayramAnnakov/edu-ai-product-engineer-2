"""
Direct YouTrack client that calls MCP server tools without LLM agent
"""
import json
from typing import Dict, Any, Optional
import structlog
from fastmcp import Client

from ..config import settings

logger = structlog.get_logger()

class YouTrackMCPClient:
    """Direct client for YouTrack MCP server tools using FastMCP"""
    
    def __init__(self, mcp_url: str = None):
        self.mcp_url = mcp_url or settings.services.mcp.youtrack_url
        self._client = None
    
    async def _ensure_client(self):
        """Ensure FastMCP client is initialized"""
        if self._client is None:
            self._client = Client(self.mcp_url)
            await self._client.__aenter__()
    
    async def close(self):
        """Close FastMCP client"""
        if self._client is not None:
            await self._client.__aexit__(None, None, None)
            self._client = None
    
    async def __aenter__(self):
        await self._ensure_client()
        return self
        
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.close()
    
    def _extract_result_text(self, result) -> str:
        """Extract text from FastMCP CallToolResult"""
        if result.content and len(result.content) > 0:
            return result.content[0].text
        return ""
    
    async def _call_tool(self, tool_name: str, **kwargs) -> Dict[str, Any]:
        """Call an MCP tool using FastMCP Client"""
        try:
            await self._ensure_client()
            result = await self._client.call_tool(tool_name, kwargs)
            
            # Extract and parse the JSON result
            result_text = self._extract_result_text(result)
            if result_text:
                parsed_result = json.loads(result_text)
            else:
                parsed_result = {}
            
            logger.debug(
                "MCP tool called successfully",
                tool=tool_name,
                params=kwargs,
                result_keys=list(parsed_result.keys()) if isinstance(parsed_result, dict) else "non-dict"
            )
            
            return parsed_result
            
        except Exception as e:
            logger.error(
                "Failed to call MCP tool",
                tool=tool_name,
                params=kwargs,
                error=str(e)
            )
            raise
    
    async def create_issue(
        self,
        project: str,
        summary: str,
        description: str = "",
        issue_type: str = "Bug",
        priority: str = "Normal",
        tags: Optional[list] = None
    ) -> Dict[str, Any]:
        """
        Create a new YouTrack issue
        
        Args:
            project: Project ID or shortName
            summary: Issue title/summary
            description: Issue description
            issue_type: Type of issue (default "Bug")
            priority: Priority level (default "Normal")
            tags: Optional list of tags
            
        Returns:
            Created issue details including ID and URL
        """
        params = {
            "project": project,
            "summary": summary,
            "description": description,
            "issue_type": issue_type,  # MCP tool uses issue_type not type
            "priority": priority
        }
        
        if tags:
            params["tags"] = tags
            
        result = await self._call_tool("create_youtrack_issue", **params)
        
        logger.info(
            "Created YouTrack issue",
            project=project,
            summary=summary,
            issue_id=result.get("id"),  # MCP returns 'id' not 'issue_id'
            priority=priority
        )
        
        return result
    
    async def add_comment(
        self,
        issue_id: str,
        text: str,
        use_markdown: bool = True
    ) -> Dict[str, Any]:
        """
        Add a comment to an existing YouTrack issue
        
        Args:
            issue_id: Issue ID to add comment to
            text: Comment text
            use_markdown: Whether to use markdown formatting (note: MCP tool may not support this param)
            
        Returns:
            Comment details including ID
        """
        # Note: The MCP tool might not support use_markdown parameter
        result = await self._call_tool(
            "add_issue_comment",
            issue_id=issue_id,
            text=text
        )
        
        logger.info(
            "Added comment to YouTrack issue",
            issue_id=issue_id,
            comment_length=len(text),
            comment_id=result.get("id")
        )
        
        return result
    
    async def search_issues(
        self,
        query: str,
        max_results: int = 20
    ) -> Dict[str, Any]:
        """
        Search YouTrack issues
        
        Args:
            query: Search query
            max_results: Maximum number of results
            
        Returns:
            Search results with 'total' and 'issues' keys
        """
        result = await self._call_tool(
            "search_youtrack_issues",
            query=query,
            max_results=max_results
        )
        
        logger.debug(
            "Searched YouTrack issues",
            query=query,
            total_found=result.get("total", 0),
            results_returned=len(result.get("issues", []))
        )
        
        return result
    
    async def get_issue(self, issue_id: str) -> Dict[str, Any]:
        """
        Get details of a specific YouTrack issue
        
        Args:
            issue_id: Issue ID to retrieve
            
        Returns:
            Issue details including summary, description, comments, etc.
        """
        result = await self._call_tool("get_youtrack_issue", issue_id=issue_id)
        
        logger.debug(
            "Retrieved YouTrack issue", 
            issue_id=issue_id,
            summary=result.get("summary", "N/A"),
            comments_count=len(result.get("comments", []))
        )
        
        return result
    
    async def get_projects(self) -> Dict[str, Any]:
        """
        Get list of available YouTrack projects
        
        Returns:
            List of projects
        """
        result = await self._call_tool("get_youtrack_projects")
        
        logger.debug(
            "Retrieved YouTrack projects",
            projects_count=len(result.get("projects", []))
        )
        
        return result