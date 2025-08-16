Please classify all reviews in the file: {{file_path}}

Workflow Run ID: {{workflow_run_id}}

Steps:
1. Read the reviews from the CSV file  
2. Classify each review individually using your natural language understanding
3. Return results as JSON matching this schema:
{{batch_classification_schema}}

4. For database storage, the system will parse your JSON output automatically

Please be thorough and consistent in your classifications.

Respond ONLY with valid JSON. Do not include any explanations or other text or formatting before or after the JSON object.