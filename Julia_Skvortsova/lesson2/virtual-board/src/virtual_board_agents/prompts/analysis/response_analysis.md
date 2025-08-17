# Response Analysis Prompt

{{analysis_context}}

Analyze this response for themes, sentiment, and hypothesis coverage:

**Response to analyze:** {{response}}
**Question asked:** {{question}}
**Hypotheses:** {{hypotheses}}
**Persona:** {{persona_name}} - {{persona_background}}

## Important Guidelines:
- Only include hypothesis IDs in hypotheses_hit where the response CLEARLY addresses that hypothesis
- Be precise and conservative with hypothesis coverage
- Extract 1-3 key quotes that best represent the response
- Sentiment should reflect overall positivity/negativity (-1 to +1)
- Themes should be specific and actionable