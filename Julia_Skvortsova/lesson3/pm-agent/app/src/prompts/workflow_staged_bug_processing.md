# Staged Bug Processing Workflow

Process this user review for bug tracking in YouTrack project **{{project}}** using a staged duplicate detection approach designed to handle large result sets efficiently.

## Review Information
- **Review ID**: {{review_id}}
- **Confidence Score**: {{confidence}}
- **Review Text**: 
  > {{review_text}}
- **Processed Date**: {{review_date}}

## Staged Processing Strategy

This workflow uses a 4-stage approach to efficiently handle large numbers of potential duplicates while staying within resource limits.

### Stage 1: Smart Multi-Query Search (Target: 50-200 candidates)

Execute **multiple targeted searches** instead of one broad search:

1. **Keyword Search**: Extract 3-5 key terms from the review text
   - Query: `project: {{project}} (keyword1 OR keyword2 OR keyword3)`

2. **Error Message Search**: If specific errors/symptoms are mentioned
   - Query: `project: {{project}} summary: "error_terms"`

3. **Component Search**: If UI elements or features are identifiable, extract the most relevant component/feature area from the review text and search accordingly  
   - First identify the component (e.g., "upload", "login", "payment", "ui", etc.) based on the review content
   - Query: `project: {{project}} #[extracted_component] OR summary: [feature_name]`

4. **Recent Issues Search**: Bias towards recent issues (more likely duplicates)
   - Query: `project: {{project}} created: {{"{This week}"}} AND (keywords)` (use YouTrack syntax for recent issues)

**Stage 1 Limits:**
- Maximum 50 results per query
- Maximum 200 total candidates across all queries
- Stop early if high-confidence duplicate found

### Stage 2: Fast Pre-Filtering (Target: 10-15 candidates)

For each candidate from Stage 1, calculate **pre-filter scores**:

1. **Title Similarity** (0-1): Compare issue titles for keyword overlap
2. **Recency Score** (0-1): Weight newer issues higher  
3. **Component Match** (0-1): Same component/feature area
4. **Combined Score**: Weighted average of above

**Pre-Filtering Rules:**
- Keep only candidates with combined score > 0.3
- Prioritize top 10-15 candidates for detailed analysis
- If >20 candidates have score >0.3, take top 15 only

### Stage 3: Detailed Analysis (Maximum: 10 candidates)

For the filtered candidates, perform **deep analysis**:

1. **Fetch Full Details**: Use `get_youtrack_issue` with comments
2. **Semantic Analysis**: Compare descriptions and contexts
3. **Similarity Scoring**:
   - Problem similarity: Same root cause/issue? (0-1)
   - Context similarity: Same scenario/steps? (0-1)  
   - Impact similarity: Same user effect? (0-1)
   - **Final Score**: (Problem×0.5 + Context×0.3 + Impact×0.2)

**Stage 3 Limits:**
- Maximum 10 candidates for detailed analysis
- Stop immediately if any candidate scores >0.85 (high confidence duplicate)
- Skip detailed analysis if taking >120 seconds

### Stage 4: Final Decision & Action

**Duplicate Found (score ≥ 0.75):**
- Use `add_issue_comment` with structured duplicate comment
- Include similarity analysis and new information
- Optionally link as duplicate using `link_issue_as_duplicate`

**No Duplicate Found (all scores < 0.75):**
- Use `create_youtrack_issue` with structured bug report
- Include extracted keywords and component information
- Set appropriate priority and tags

## Processing Constraints & Limits

To ensure reasonable performance and resource usage:

- **Total Processing Time**: Maximum 5 minutes  
- **API Call Limit**: Maximum 100 API calls total
- **Detailed Analysis**: Maximum 20 candidates
- **Early Termination**: Stop if duplicate confidence >0.85
- **Fallback**: If limits exceeded, create new issue with note about incomplete search

## Available MCP Tools

- `search_youtrack_issues`: Search with pagination support
- `search_all_pages`: Auto-paginated comprehensive search (use sparingly)
- `get_youtrack_issue`: Get full issue details with comments
- `create_youtrack_issue`: Create new issues
- `add_issue_comment`: Add structured comments
- `link_issue_as_duplicate`: Link issues as duplicates

## Structured Response Format

Return your complete analysis as JSON following this schema:

{{bug_processing_schema}}

**Required fields for staged processing:**
- `duplicate_session_id`: Generate UUID for session tracking
- `total_candidates_found`: Count from Stage 1
- `candidates_analyzed_in_detail`: Count from Stage 3
- `search_queries_used`: List all queries executed
- `issues_examined`: List all issue IDs analyzed in detail
- `processing_time_ms`: Actual time spent (estimate)
- `api_calls_made`: Number of API calls made

## Templates for Consistent Formatting

### Bug Report Template
{{bug_report_template}}

### Duplicate Comment Template  
{{duplicate_comment_template}}

## Stage Progress Tracking

Document your progress through each stage:

1. **Stage 1 Results**: "Found X candidates across Y queries"
2. **Stage 2 Results**: "Pre-filtered to X candidates (scores >0.3)"  
3. **Stage 3 Results**: "Analyzed X candidates in detail, top score: Y"
4. **Stage 4 Decision**: "Action: [created_issue|commented_on_duplicate]"

## Quality & Efficiency Checklist

- [ ] Used targeted search queries (not broad searches)
- [ ] Applied pre-filtering to reduce candidate set
- [ ] Limited detailed analysis to top candidates only  
- [ ] Applied early termination if high-confidence duplicate found
- [ ] Stayed within processing time and API call limits
- [ ] Documented complete stage progression
- [ ] Included all required schema fields with session tracking
- [ ] Provided clear reasoning for final decision

**Key Principle**: Balance thoroughness with efficiency. Find true duplicates without exhaustive analysis of every potential match.