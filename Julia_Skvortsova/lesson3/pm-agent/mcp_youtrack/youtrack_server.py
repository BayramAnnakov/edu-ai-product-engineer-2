"""
YouTrack MCP Server - Provides tools for interacting with YouTrack REST API
"""
import os
import httpx
import structlog
import asyncio
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
from dotenv import load_dotenv
from fastmcp import FastMCP
from pydantic import BaseModel, Field
from cache_service import get_cache, SmartCacheStrategy

# Load environment variables
load_dotenv()

# Configure structlog to output to stderr to avoid interfering with MCP STDIO
import sys
import logging

# Set up minimal logging to stderr only
structlog.configure(
    wrapper_class=structlog.make_filtering_bound_logger(logging.WARNING),  # WARNING level only
    logger_factory=structlog.WriteLoggerFactory(file=sys.stderr),
    cache_logger_on_first_use=True,
)

logger = structlog.get_logger()

# YouTrack configuration
YOUTRACK_BASE_URL = os.getenv("YOUTRACK_BASE_URL", "").rstrip("/")
YOUTRACK_TOKEN = os.getenv("YOUTRACK_TOKEN", "")
DEFAULT_PROJECT = os.getenv("YOUTRACK_DEFAULT_PROJECT", "DEMO")

# Rate limiting configuration
RATE_LIMIT_REQUESTS = int(os.getenv("YOUTRACK_RATE_LIMIT_REQUESTS", "100"))  # requests per minute
RATE_LIMIT_WINDOW = 60  # seconds
MAX_RETRIES = 3
RETRY_DELAY = 1  # seconds

# Validate configuration
if not YOUTRACK_BASE_URL or not YOUTRACK_TOKEN:
    raise ValueError("YOUTRACK_BASE_URL and YOUTRACK_TOKEN must be set in environment variables")

# HTTP client configuration
headers = {
    "Authorization": f"Bearer {YOUTRACK_TOKEN}",
    "Accept": "application/json",
    "Content-Type": "application/json"
}

# Rate limiter
class RateLimiter:
    def __init__(self, max_requests: int, window_seconds: int):
        self.max_requests = max_requests
        self.window_seconds = window_seconds
        self.requests = []
    
    async def wait_if_needed(self):
        """Wait if rate limit would be exceeded"""
        now = datetime.now()
        # Remove old requests outside the window
        self.requests = [req_time for req_time in self.requests 
                        if (now - req_time).total_seconds() < self.window_seconds]
        
        if len(self.requests) >= self.max_requests:
            # Calculate wait time
            oldest_request = min(self.requests)
            wait_time = self.window_seconds - (now - oldest_request).total_seconds() + 1
            logger.warning(f"Rate limit reached, waiting {wait_time:.1f} seconds")
            await asyncio.sleep(wait_time)
        
        self.requests.append(now)

rate_limiter = RateLimiter(RATE_LIMIT_REQUESTS, RATE_LIMIT_WINDOW)

# Helper functions
async def make_request(method: str, endpoint: str, **kwargs) -> Dict[str, Any]:
    """Make an authenticated request to YouTrack API with rate limiting and retries"""
    url = f"{YOUTRACK_BASE_URL}/api{endpoint}"
    
    # Apply rate limiting
    await rate_limiter.wait_if_needed()
    
    last_error = None
    for attempt in range(MAX_RETRIES):
        async with httpx.AsyncClient() as client:
            try:
                response = await client.request(
                    method=method,
                    url=url,
                    headers=headers,
                    timeout=30.0,
                    **kwargs
                )
                
                # Handle rate limit responses
                if response.status_code == 429:
                    retry_after = response.headers.get('Retry-After', '60')
                    wait_time = int(retry_after)
                    logger.warning(f"Rate limited by YouTrack, waiting {wait_time} seconds")
                    await asyncio.sleep(wait_time)
                    continue
                
                response.raise_for_status()
                
                # Return empty dict for 204 No Content responses
                if response.status_code == 204:
                    return {}
                    
                return response.json()
                
            except httpx.HTTPStatusError as e:
                last_error = e
                if e.response.status_code in [502, 503, 504]:  # Server errors
                    logger.warning(f"Server error on attempt {attempt + 1}, retrying...")
                    await asyncio.sleep(RETRY_DELAY * (attempt + 1))
                    continue
                    
                logger.error("YouTrack API error", 
                            status_code=e.response.status_code,
                            response_text=e.response.text,
                            url=url)
                raise Exception(f"YouTrack API error: {e.response.status_code} - {e.response.text}")
                
            except (httpx.ConnectError, httpx.TimeoutException) as e:
                last_error = e
                if attempt < MAX_RETRIES - 1:
                    logger.warning(f"Connection error on attempt {attempt + 1}, retrying...")
                    await asyncio.sleep(RETRY_DELAY * (attempt + 1))
                    continue
                logger.exception("Request failed", url=url)
                raise
                
            except Exception as e:
                logger.exception("Unexpected error", url=url)
                raise
    
    # If we get here, all retries failed
    logger.error(f"All {MAX_RETRIES} attempts failed", url=url)
    raise last_error if last_error else Exception("All retry attempts failed")

# Initialize FastMCP server
mcp = FastMCP(
    name="youtrack",
    instructions="YouTrack MCP Server for managing issues, comments, and searches with smart caching"
)

@mcp.tool()
async def search_youtrack_issues(
    query: str,
    max_results: int = 10,
    fields: Optional[str] = None,
    skip: int = 0,
    bypass_cache: bool = False
) -> Dict[str, Any]:
    """
    Search for issues in YouTrack using query syntax with pagination support and smart caching.
    
    Common query examples:
    - 'project: DEMO bug': Find bugs in DEMO project
    - 'summary: login': Find issues with 'login' in title
    - 'description: registration': Find issues with 'registration' in description
    - '#Unresolved': Find unresolved issues
    - 'created: {Today}': Find issues created today
    - 'project: DEMO (keyword1 OR keyword2 OR keyword3)': Find issues in DEMO project with specific keywords
    - 'project: DEMO #{Auth component} OR summary: login': Find issues in DEMO project with Auth component or 'login' in title
    
    Pagination:
    - max_results: Number of results per page (default 10, max 100)
    - skip: Number of results to skip (for pagination)
    - bypass_cache: Skip cache lookup for debugging (default False)
    """
    return await _search_single_page(
        query=query,
        max_results=max_results,
        fields=fields,
        skip=skip,
        bypass_cache=bypass_cache
    )

@mcp.tool()
async def create_youtrack_issue(
    project: str,
    summary: str,
    description: str = "",  # Changed from Optional[str] = None
    issue_type: str = "Bug",
    priority: str = "Normal",
    tags: Optional[List[str]] = None
) -> Dict[str, Any]:
    """
    Create a new issue in YouTrack.
    
    Args:
        project: Project shortName (e.g. "INT") or full project ID (e.g. "0-31")
        summary: Issue title/summary
        description: Optional issue description
        issue_type: Issue type (default "Bug")
        priority: Priority level (default "Normal") 
        tags: Optional list of tags
    
    Returns the created issue details including its ID.
    """
    # If project looks like a shortName, try to find the full project ID
    project_id = project
    if not project.startswith("0-") and len(project) <= 10:  # Likely a shortName
        try:
            # Get all projects and find by shortName (query might not work)
            projects_result = await make_request(
                "GET", 
                "/admin/projects",
                params={"fields": "id,shortName"}
            )
            logger.warning(f"Searching for project with shortName '{project}' in {len(projects_result) if projects_result else 0} projects")
            
            if projects_result and isinstance(projects_result, list):
                for proj in projects_result:
                    if isinstance(proj, dict) and proj.get("shortName") == project:
                        project_id = proj.get("id", project)
                        logger.warning(f"Resolved project shortName '{project}' to ID '{project_id}'")
                        break
                else:
                    logger.warning(f"Project shortName '{project}' not found in available projects")
        except Exception as e:
            logger.warning(f"Could not resolve project shortName '{project}': {e}")
            # Fall back to using the original value
    
    logger.debug(f"Using project ID: {project_id} (original: {project})")
    
    # Prepare the issue payload
    issue_data = {
        "project": {"id": project_id},
        "summary": summary
    }
    
    if description and description.strip():
        issue_data["description"] = description
    
    # Add custom fields directly during creation using official YouTrack API format
    custom_fields = []
    
    # Add Type field if specified
    if issue_type:
        custom_fields.append({
            "name": "Type",
            "$type": "SingleEnumIssueCustomField",
            "value": {"name": issue_type}
        })
    
    # Add Priority field if specified
    if priority:
        custom_fields.append({
            "name": "Priority", 
            "$type": "SingleEnumIssueCustomField",
            "value": {"name": priority}
        })
    
    if custom_fields:
        issue_data["customFields"] = custom_fields
    
    # Log the payload for debugging
    logger.info(f"Creating issue with payload: {issue_data}")
    
    # Create the issue
    result = await make_request(
        "POST", 
        "/issues",
        json=issue_data,
        params={"fields": "id,idReadable,summary,description,created"}
    )
    
    # Add tags if provided
    issue_id = result.get("id")
    if tags and issue_id:
        for tag in tags:
            try:
                await make_request(
                    "POST",
                    f"/issues/{issue_id}/tags",
                    json={"name": tag}
                )
            except Exception as e:
                logger.warning(f"Failed to add tag '{tag}': {e}")
    
    # Invalidate cache for this project since we created a new issue
    cache = get_cache()
    await cache.invalidate_pattern(f"project: {project}")
    logger.debug("Invalidated cache after creating issue", project=project)
    
    return {
        "id": result.get("idReadable", result.get("id")),
        "summary": result.get("summary"),
        "description": result.get("description"),
        "created": result.get("created"),
        "url": f"{YOUTRACK_BASE_URL}/issue/{result.get('idReadable', result.get('id'))}"
    }

@mcp.tool()
async def get_youtrack_issue(
    issue_id: str,
    fields: Optional[str] = None
) -> Dict[str, Any]:
    """
    Get detailed information about a specific issue.
    """
    params = {}
    
    if fields:
        params["fields"] = fields
    else:
        # Comprehensive default fields with detailed field values
        params["fields"] = "id,idReadable,summary,description,created,updated,resolved,reporter(login,fullName),comments(id,text,author(login,fullName),created),fields(name,value(name,localizedName,$type)),tags(name)"
    
    result = await make_request("GET", f"/issues/{issue_id}", params=params)
    
    # Format the response
    formatted = {
        "id": result.get("idReadable", result.get("id")),
        "summary": result.get("summary"),
        "description": result.get("description"),
        "created": result.get("created"),
        "updated": result.get("updated"),
        "resolved": result.get("resolved"),
        "reporter": result.get("reporter", {}).get("fullName", "Unknown"),
        "url": f"{YOUTRACK_BASE_URL}/issue/{result.get('idReadable', result.get('id'))}"
    }
    
    # Include comments if requested
    if "comments" in result:
        formatted["comments"] = [
            {
                "author": comment.get("author", {}).get("fullName", "Unknown"),
                "text": comment.get("text"),
                "created": comment.get("created")
            }
            for comment in result["comments"]
        ]
    
    # Include tags if present
    if "tags" in result:
        formatted["tags"] = [tag.get("name") for tag in result["tags"]]
    
    return formatted

@mcp.tool()
async def get_youtrack_projects() -> Dict[str, Any]:
    """
    Get list of available YouTrack projects.
    
    Returns project information including IDs and names.
    """
    try:
        result = await make_request(
            "GET", 
            "/admin/projects",
            params={"fields": "id,name,shortName,description"}
        )
        
        projects = []
        for project in result:
            projects.append({
                "id": project.get("id"),
                "name": project.get("name"), 
                "shortName": project.get("shortName"),
                "description": project.get("description", "")
            })
        
        return {
            "status": "success",
            "projects": projects,
            "total": len(projects)
        }
        
    except Exception as e:
        logger.error("Failed to get projects", error=str(e))
        return {
            "status": "error",
            "message": f"Failed to get projects: {str(e)}"
        }
'''
@mcp.tool()
async def get_issue_fields(issue_id: str) -> Dict[str, Any]:
    """
    Get detailed field information for a specific issue to understand field structure.
    
    This is useful for debugging field updates.
    """
    try:
        result = await make_request(
            "GET", 
            f"/issues/{issue_id}",
            params={"fields": "id,fields(name,value,projectCustomField(field(name)))"}
        )
        
        fields_info = []
        if "fields" in result:
            for field in result["fields"]:
                field_info = {
                    "name": field.get("name"),
                    "value": field.get("value"),
                    "field_type": type(field.get("value")).__name__
                }
                
                # Get project custom field info if available
                if "projectCustomField" in field:
                    pcf = field["projectCustomField"]
                    if "field" in pcf:
                        field_info["field_name"] = pcf["field"].get("name")
                
                fields_info.append(field_info)
        
        return {
            "status": "success",
            "issue_id": issue_id,
            "fields": fields_info
        }
        
    except Exception as e:
        logger.error("Failed to get issue fields", error=str(e))
        return {
            "status": "error",
            "message": f"Failed to get issue fields: {str(e)}"
        }

@mcp.tool()
async def clear_search_cache() -> Dict[str, Any]:
    """
    Clear the search result cache (useful for debugging enum field issues).
    
    Returns the number of cache entries cleared.
    """
    cache = get_cache()
    cleared_count = await cache.clear()
    logger.warning(f"Cache cleared: {cleared_count} entries removed")  # Use WARNING so it shows up
    
    return {
        "status": "success",
        "cleared_entries": cleared_count,
        "message": f"Cache cleared: {cleared_count} entries removed"
    }
'''
    
@mcp.tool()
async def add_issue_comment(
    issue_id: str,
    text: str,
    use_markdown: bool = True
) -> Dict[str, Any]:
    """
    Add a comment to an existing YouTrack issue.
    
    Returns the created comment details.
    """
    comment_data = {
        "text": text,
        "usesMarkdown": use_markdown
    }
    
    result = await make_request(
        "POST",
        f"/issues/{issue_id}/comments",
        json=comment_data,
        params={"fields": "id,text,created,author(login,fullName)"}
    )
    
    return {
        "id": result.get("id"),
        "text": result.get("text"),
        "created": result.get("created"),
        "author": result.get("author", {}).get("fullName", "Unknown"),
        "issue_id": issue_id
    }

# Helper function for multi-page search (not decorated as tool)
async def _search_single_page(
    query: str,
    max_results: int = 10,
    fields: Optional[str] = None,
    skip: int = 0,
    bypass_cache: bool = False
) -> Dict[str, Any]:
    """Internal helper for single page search"""
    # Limit max_results to prevent too large requests
    max_results = min(max_results, 100)
    
    params = {
        "query": query,
        "$top": max_results,
        "$skip": skip
    }
    
    if fields:
        params["fields"] = fields
    else:
        # Default fields for comprehensive search results - include detailed field values
        params["fields"] = "id,idReadable,summary,description,created,updated,resolved,reporter(login,fullName),fields(name,value(name,localizedName,$type))"
    
    # Try to get from cache first (unless bypassing cache for debugging)
    cache = get_cache()
    cached_result = None
    
    if not bypass_cache:
        cached_result = await cache.get(query, params)
        
        if cached_result is not None:
            logger.debug("Using cached search result", query=query[:50], skip=skip, max_results=max_results)
            return cached_result
    
    # Cache miss or bypass - make API request
    cache_status = "cache bypassed" if bypass_cache else "cache miss"
    logger.debug(f"{cache_status}, making API request", query=query[:50], skip=skip, max_results=max_results)
    result = await make_request("GET", "/issues", params=params)
    
    # Format the response for easier consumption
    issues = []
    for issue in result:
        formatted_issue = {
            "id": issue.get("idReadable", issue.get("id")),
            "summary": issue.get("summary"),
            "description": issue.get("description"),
            "created": issue.get("created"),
            "resolved": issue.get("resolved"),
            "reporter": issue.get("reporter", {}).get("fullName", "Unknown")
        }
        
        # Extract custom fields if present
        if "fields" in issue:
            for field in issue["fields"]:
                field_name = field.get("name", "").lower().replace(" ", "_")
                field_value = field.get("value")
                
                # Handle different value types (enums, bundles, etc.)
                if isinstance(field_value, dict):
                    if "name" in field_value:
                        # Enum/Bundle element - use the name
                        formatted_issue[field_name] = field_value["name"]
                    elif "$type" in field_value:
                        # Handle other structured types
                        if field_value["$type"] in ["EnumBundleElement", "StateBundleElement"]:
                            formatted_issue[field_name] = field_value.get("name", "Unknown")
                        else:
                            # For other complex types, try to extract meaningful value or skip
                            formatted_issue[field_name] = field_value.get("name", field_value.get("value", "Unknown"))
                    else:
                        # Generic dict - try to find a meaningful value
                        formatted_issue[field_name] = field_value.get("name", field_value.get("value", None))
                elif isinstance(field_value, list):
                    # Handle arrays (like sprints)
                    formatted_list = []
                    for item in field_value:
                        if isinstance(item, dict):
                            formatted_list.append(item.get("name", item.get("value", "Unknown")))
                        else:
                            formatted_list.append(item)
                    formatted_issue[field_name] = formatted_list
                else:
                    # Simple values (strings, numbers, booleans, null)
                    formatted_issue[field_name] = field_value
        
        issues.append(formatted_issue)
    
    # Check if there are more results
    has_more = len(issues) == max_results
    
    response = {
        "total": len(issues),
        "issues": issues,
        "query": query,
        "pagination": {
            "skip": skip,
            "limit": max_results,
            "has_more": has_more,
            "next_skip": skip + len(issues) if has_more else None
        }
    }
    
    # Cache the result using smart caching strategy (unless cache was bypassed)
    if not bypass_cache and SmartCacheStrategy.should_cache_query(query, len(issues)):
        ttl = SmartCacheStrategy.get_ttl_for_query(query, len(issues))
        await cache.set(query, response, params, ttl_seconds=ttl)
        logger.debug("Cached search result", query=query[:50], ttl_seconds=ttl, issues_count=len(issues))
    elif bypass_cache:
        logger.debug("Skipped caching due to cache bypass", query=query[:50], issues_count=len(issues))
    
    return response

@mcp.tool()
async def search_all_pages(
    query: str,
    page_size: int = 50,
    max_total: int = 500
) -> Dict[str, Any]:
    """
    Search for issues and automatically fetch all pages up to max_total.
    
    This is a convenience function that handles pagination automatically.
    Use this when you need to search through many results.
    
    Args:
        query: YouTrack query string
        page_size: Number of results per page (default 50)
        max_total: Maximum total results to fetch (default 500)
    """
    all_issues = []
    skip = 0
    
    while len(all_issues) < max_total:
        result = await _search_single_page(
            query=query,
            max_results=min(page_size, max_total - len(all_issues)),
            skip=skip
        )
        
        issues = result.get("issues", [])
        if not issues:
            break
            
        all_issues.extend(issues)
        
        # Check if there are more pages
        pagination = result.get("pagination", {})
        if not pagination.get("has_more", False):
            break
            
        skip = pagination.get("next_skip", skip + page_size)
        
        # Add small delay between pages to be nice to the API
        await asyncio.sleep(0.1)
    
    return {
        "total": len(all_issues),
        "issues": all_issues,
        "query": query,
        "fetched_all": len(all_issues) < max_total or not result.get("pagination", {}).get("has_more", False)
    }

# MCP Prompts
@mcp.prompt()
async def search_for_duplicates_prompt(bug_summary: str) -> str:
    """Generate a prompt for searching potential duplicate issues."""
    return f"""Search YouTrack for issues that might be duplicates of this bug report:

Summary: {bug_summary}

Use the search_youtrack_issues tool to find similar issues. Try multiple search strategies:
1. Search for key terms from the summary
2. Search for the main error or problem described
3. Look for issues in the same component/area

After finding potential matches, use get_youtrack_issue to examine each one in detail, including comments.

Report which issues might be duplicates and explain why."""

@mcp.prompt()
async def create_bug_report_prompt(review_text: str, project: str = "INT") -> str:
    """Generate a prompt for creating a bug report from user review."""
    return f"""Create a bug report in YouTrack project {project} (use shortName like 'INT') based on this user review:

{review_text}

First, search for potential duplicates using search_youtrack_issues.
If you find a duplicate (very similar issue), add a comment to the existing issue instead of creating a new one.
If no duplicate exists, create a new issue with:
- Clear, descriptive summary
- Detailed description with steps to reproduce (if available)
- Appropriate type (Bug) and priority
- Relevant tags

Return the issue ID and URL of either the existing issue (if duplicate) or the newly created issue."""

@mcp.prompt()
async def analyze_issue_trends_prompt(project: str = DEFAULT_PROJECT) -> str:
    """Generate a prompt for analyzing issue trends in a project."""
    return f"""Analyze issue trends in YouTrack project {project}:

1. Search for recent issues: `project: {project} created: {{This week}}`
2. Search for unresolved issues: `project: {project} #Unresolved`
3. Search for critical issues: `project: {project} Priority: Critical`

For each category:
- Count the issues
- Identify common patterns in summaries
- Look for recurring components or areas
- Suggest focus areas for the team

Provide insights on what the team should prioritize."""

if __name__ == "__main__":
    # Run with STDIO transport for MCP Inspector
    # All logging is configured to go to stderr to avoid interfering with MCP communication
    mcp.run("stdio")