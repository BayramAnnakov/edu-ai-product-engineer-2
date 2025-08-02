# Persona Drift Check Prompt

Check if this response is consistent with the persona's background.

**Current Response:** {{response}}
**Persona Background:** {{persona_background}}
**Previous Responses:** {{previous_responses}}

Check for inconsistencies in tone, opinions, demographics, or behavior patterns.

Return your analysis as a JSON object matching the following schema:
{{persona_drift_schema}}

Respond ONLY with valid JSON. Do not include any explanations or other text or formatting before or after the JSON object.