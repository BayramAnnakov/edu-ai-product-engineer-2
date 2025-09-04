# Duplicate Issue Detection

You are analyzing whether a new bug report is a duplicate of existing issues in YouTrack.

## New Bug Report
**Summary**: {{new_issue_summary}}
**Description**: {{new_issue_description}}
**Key Problems**: {{key_problems}}

## Existing Issues to Compare
{{existing_issues}}

## Analysis Instructions

For each existing issue, analyze:

1. **Problem Similarity** (0-100%)
   - Are they describing the same underlying issue?
   - Do they have the same root cause?
   - Are the symptoms identical or very similar?

2. **Context Similarity** (0-100%)
   - Same component/feature affected?
   - Similar user actions leading to the issue?
   - Same platform/environment?

3. **Impact Similarity** (0-100%)
   - Similar severity/impact on users?
   - Same type of functionality affected?

## Decision Criteria

Consider an issue a duplicate if:
- Overall similarity score > 85%
- The core problem is the same (even if described differently)
- The issues would have the same fix

## Output Format

Return your analysis as a JSON object matching the following schema:
{{duplicate_analysis_schema}}

Respond ONLY with valid JSON. Do not include any explanations or other text or formatting before or after the JSON object.