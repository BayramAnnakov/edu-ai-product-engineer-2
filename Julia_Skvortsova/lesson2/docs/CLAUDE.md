# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Overview

This repository contains a Virtual Board Pre-Test system that uses AI personas to simulate customer panels for product validation. The system is built with Python 3.10+ and uses OpenAI's API to create multi-agent simulations for testing product hypotheses before engaging real users.

## Key Commands

### Setup
```bash
# Create and activate virtual environment (Python 3.12 recommended)
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
cd virtual-board
pip install -r requirements.txt

# Set OpenAI API key
export OPENAI_API_KEY="your-key-here"
```

### Running the Application
```bash
# Run the main Virtual Board session
cd virtual-board
python main.py

# Configuration is in virtual-board/config/board_config.yml
```

### Testing
```bash
# Run all tests
cd virtual-board
pytest

# Run specific test files
pytest tests/test_agents_functionality.py -v
pytest tests/test_session_integration.py -v

# Run smoke tests
pytest tests/test_agents_smoke.py -v
```

## Architecture Overview

### Multi-Agent System
The system implements a production-ready multi-agent architecture using OpenAI's Agents SDK:

- **Orchestrator Agent**: Coordinates all other agents and manages phase transitions
- **Facilitator Agent**: Drives discussions, generates follow-ups, synthesizes insights
- **Analyst Agent**: Analyzes responses, clusters themes, tracks hypothesis coverage
- **Moderator Agent**: Checks for bias, persona drift, and redundancy
- **Persona Agents**: AI-simulated customer archetypes responding to questions

### Core Components

1. **Session Management** (`src/virtual_board_agents/session.py`): 
   - Manages the complete virtual board session lifecycle
   - Handles phase transitions (warmup → diverge → converge → closure)
   - Exports memory and state for analysis

2. **Agent Definitions** (`src/virtual_board_agents/agents.py`):
   - Defines each agent type with their specialized tools
   - Implements tool-based capabilities for autonomous operation

3. **Shared Memory** (`src/virtual_board_agents/memory.py`):
   - Centralized memory store for all agent interactions
   - Tracks responses, themes, hypothesis coverage
   - Enables cross-agent collaboration

4. **Production Features** (`src/virtual_board_agents/production.py`):
   - Guardrails for input/output validation
   - Execution tracing for debugging
   - Error handling with recovery strategies

### Configuration Structure
Configuration is managed through YAML files:
- `config/board_config.yml`: Define product, hypotheses, personas, and questions
- Questions are organized by phase (warmup, diverge, converge, closure)
- Phase-specific configurations control behavior

### Key Data Models
- Uses Pydantic for structured data validation
- Models defined in `src/models.py`
- Includes Product, Hypothesis, Persona, and various response types

## Important Notes

- Always ensure OPENAI_API_KEY is set before running
- The system uses GPT-4 for complex reasoning tasks
- Session outputs are saved with timestamps in the project root
- Memory exports include complete interaction history for analysis