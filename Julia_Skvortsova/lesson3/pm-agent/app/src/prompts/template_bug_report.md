# Bug Report Template

You are creating a bug report based on a user review. Structure the bug report as follows:

## Title
Create a clear, concise title that describes the issue. Format: "[Component] Brief description of the problem"

## Description
Provide a detailed description including:

### Summary
{{review_text}}

### Problem Details
- **What's happening**: Describe the issue clearly
- **Impact**: How this affects users
- **Frequency**: When/how often this occurs

### Steps to Reproduce (if available from review)
1. Step one
2. Step two
3. ...

### Expected Behavior
What should happen instead

### Actual Behavior
What currently happens

### Additional Context
- User review confidence score: {{confidence}}
- Review ID: {{review_id}}
- Original review date: {{review_date}}

## Priority Assessment
Based on the review, suggest appropriate priority:
- **Critical**: System unusable, data loss, security issue
- **Major**: Major functionality broken, affects many users
- **Normal**: Standard bug, workaround available
- **Minor**: Minor issue, cosmetic problems

## Tags
Suggest relevant tags based on the issue content (e.g., "ui", "performance", "data-loss", "mobile", "login")