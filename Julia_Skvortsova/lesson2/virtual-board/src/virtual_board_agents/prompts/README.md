# Virtual Board Prompts

This directory contains all prompts for the Virtual Board agents system, organized as markdown files for better maintainability and version control.

## Structure

```
prompts/
├── agents/           # Agent system instructions
│   ├── facilitator.md
│   ├── analyst.md
│   ├── theme_analyst.md
│   ├── bias_moderator.md
│   ├── moderator.md
│   ├── persona.md
│   └── orchestrator.md
└── analysis/         # Task-specific analysis prompts
    ├── response_analysis.md
    ├── theme_clustering.md
    ├── bias_check.md
    ├── followup.md
    ├── persona_drift.md
    └── insight_synthesis.md
```

## Usage

Prompts are loaded using the `prompt_loader` module:

```python
from src.virtual_board_agents.prompts.prompt_loader import load_agent_instructions, load_analysis_prompt

# Load agent instructions
instructions = load_agent_instructions("facilitator")

# Load agent instructions with variables
persona_instructions = load_agent_instructions(
    "persona",
    persona_name="Sarah Chen",
    persona_background="Busy parent of two..."
)

# Load analysis prompts
prompt = load_analysis_prompt(
    "response_analysis",
    response="...",
    question="...",
    hypotheses=[...],
    persona_name="Sarah Chen",
    persona_background="...",
    analysis_context="..."
)
```

## Template Variables

Prompts use `{{variable_name}}` syntax for template variables. The markdown loader automatically substitutes these with provided values.

Example:
```markdown
You are {{persona_name}}.

Background: {{persona_background}}
```

Complex data types (lists, dicts) are automatically converted to JSON strings during substitution.

## Adding New Prompts

1. Create a new `.md` file in the appropriate directory
2. Use `{{variable}}` syntax for template variables
3. Document required variables in the file
4. The prompt will be automatically available through the loader