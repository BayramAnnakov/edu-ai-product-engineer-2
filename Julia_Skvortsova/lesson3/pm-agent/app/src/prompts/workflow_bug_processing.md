# Bug Processing Workflow

Process this user review for bug tracking in YouTrack project **{{project}}**.

## Review Information
- **Review ID**: {{review_id}}
- **Confidence Score**: {{confidence}}
- **Review Text**: 
  > {{review_text}}
- **Processed Date**: {{review_date}}

## Required Workflow Steps

### Step 1: Information Extraction
Analyze the review and extract:
- **Keywords**: Main terms that describe the problem
- **Error Patterns**: Specific error messages, symptoms, or failure modes  
- **Affected Components**: UI elements, features, or system parts mentioned
- **User Impact**: How this affects the user experience
- **Reproduction Context**: Any steps, conditions, or scenarios mentioned

### Step 2: Comprehensive Duplicate Search
You have access to these YouTrack tools through MCP. Execute a thorough search strategy:

1. **Primary Search**: Use extracted keywords to find potential matches
2. **Error-Focused Search**: If specific errors are mentioned
3. **Component Search**: Search by affected features  
4. **Comprehensive Search**: If many potential matches exist, use search_all_pages

### Step 3: Detailed Duplicate Analysis
For each potential duplicate found:

1. **Get Full Details**: Examine issue content and comments
2. **Similarity Assessment**: Compare symptoms, context, and impact
3. **Score Similarity**: Rate from 0.0 to 1.0 based on:
   - Problem similarity (same underlying issue?)
   - Context similarity (same component/scenario?)
   - Impact similarity (same user effect?)

### Step 4: Decision and Action

#### If Duplicate Found (similarity > 0.85):
Add a comment to the existing issue using the duplicate comment template with:
- Review details and context
- Similarity analysis and reasoning
- Any new information from this report
- Impact assessment (user count, priority considerations)

#### If No Duplicate (create new issue):
Create a new issue with:
- Clear, descriptive title following "[Component] Brief description" format
- Structured description using bug report template
- Appropriate priority level assessment
- Relevant tags for categorization

**Available MCP Tools:**
- search_youtrack_issues: Search for issues using query syntax
- search_all_pages: Comprehensive multi-page search
- get_youtrack_issue: Get detailed issue information
- create_youtrack_issue: Create new issues
- add_issue_comment: Add comments to existing issues
- link_issue_as_duplicate: Link issues as duplicates

### Step 5: Structured Response
Return your complete analysis as JSON following this schema:

{{bug_processing_schema}}

## Templates Available

### Bug Report Template
For new issues, use this structure:
{{bug_report_template}}

### Duplicate Comment Template  
For duplicate reports, format comments using:
{{duplicate_comment_template}}

## Quality Checklist

Before finalizing your response, verify:
- [ ] Searched comprehensively using multiple strategies
- [ ] Examined full details of potential duplicates
- [ ] Applied consistent similarity scoring criteria  
- [ ] Used appropriate templates for formatting
- [ ] Included all required schema fields
- [ ] Provided clear reasoning for decisions
- [ ] Listed all search queries and examined issues

Remember: Thorough analysis prevents duplicate issues and ensures high-quality bug tracking.