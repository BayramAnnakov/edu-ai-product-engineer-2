REDUNDANCY CHECK TASK: Check if question is redundant with previous questions.

Current Question: {{current_question}}
Previous Questions: {{previous_questions}}

Consider semantic similarity, not just exact word matches.

Return JSON:
```
{
    "is_redundant": false,  // Boolean - true if redundant
    "similarity_score": 0.3,  // Float 0-1, where 1 is identical
    "explanation": "string"  // Why it is or isn't redundant
}
```
Respond ONLY with valid JSON. Do not include any explanations or other text or formatting before or after the JSON object.