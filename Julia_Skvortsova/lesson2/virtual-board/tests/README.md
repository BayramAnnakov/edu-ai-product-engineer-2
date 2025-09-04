# Virtual Board Tests

This directory contains comprehensive tests for the Virtual Board system, designed to verify functionality without expensive OpenAI API calls.

## Test Categories

### 1. **test_constants.py** - Constants and Enums
- Tests all Phase, AgentType, and MemoryEntryType enums
- Validates enum values and relationships
- Fast execution, no external dependencies

### 2. **test_models.py** - Pydantic Models
- Tests all data models (Answer, Analysis, BoardState, etc.)
- Tests structured output models (ResponseAnalysis, BiasCheck, etc.)
- Validates model creation, validation, and serialization
- Fast execution, no external dependencies

### 3. **test_prompt_loading.py** - Prompt System
- Tests markdown prompt loading
- Validates template variable substitution
- Tests all agent instruction prompts
- Tests all analysis prompt templates
- Fast execution, no external dependencies

### 4. **test_tools.py** - Python Function Tools
- Tests hypothesis coverage calculation
- Tests phase transition logic
- Tests all Python function tools
- Fast execution, no external dependencies

### 5. **test_config.py** - Configuration Loading
- Tests YAML configuration loading
- Tests config validation
- Tests error handling for invalid configs
- Fast execution, no external dependencies

### 6. **test_session_integration.py** - Session Integration (Mocked)
- Tests VirtualBoardSession functionality
- Uses mocked agents to avoid OpenAI costs
- Tests ask_persona, analyze_response, generate_followup
- Tests bias checking and drift detection
- **Mocked** - no API calls, fast execution

## Running Tests

### Run All Fast Tests
```bash
python run_tests.py
```

### Run Specific Test Category
```bash
python run_tests.py models
python run_tests.py prompt_loading
python run_tests.py tools
```

### Run Individual Test Files
```bash
pytest tests/test_models.py -v
pytest tests/test_tools.py::TestHypothesisCoverage -v
```

### Run with Coverage
```bash
pytest tests/ --cov=src --cov-report=html
```

## Test Design Philosophy

### ✅ **Included (Fast & Cheap)**
- **Unit tests** for all models, tools, and utilities
- **Mocked integration tests** that verify component interaction
- **Configuration tests** with temporary files
- **Prompt loading tests** that validate templates

### ❌ **Excluded (Expensive)**
- **Full OpenAI API calls** (use mocking instead)
- **End-to-end orchestrator runs** (too expensive for CI)
- **Real agent interactions** (mock the agents)

## Mocking Strategy

The tests use Python's `unittest.mock` to:
- Mock OpenAI Agent creation and responses
- Mock Runner.run() calls with predetermined outputs
- Simulate structured outputs (ResponseAnalysis, BiasCheck, etc.)
- Test error handling without triggering real errors

## Adding New Tests

When adding new functionality:

1. **Add unit tests** for new models/functions
2. **Mock external dependencies** (OpenAI, file system)
3. **Test both success and error cases**
4. **Keep tests fast** (< 1 second each)
5. **Use descriptive test names**

Example test structure:
```python
class TestNewFeature:
    def test_basic_functionality(self):
        # Test the happy path
        
    def test_error_handling(self):
        # Test error conditions
        
    @pytest.mark.asyncio
    async def test_async_functionality(self):
        # Test async functions with mocking
```

## Continuous Integration

These tests are designed to run in CI environments:
- **No API keys required** (everything is mocked)
- **Fast execution** (entire suite < 30 seconds)
- **Deterministic results** (no external dependencies)
- **Clear failure messages** for debugging

## Test Coverage Goals

- **Models**: 100% coverage (easy to achieve)
- **Tools**: 95% coverage (focus on edge cases)
- **Prompt Loading**: 100% coverage (no external deps)
- **Session Logic**: 80% coverage (complex interactions)
- **Configuration**: 95% coverage (error handling important)

Run coverage analysis:
```bash
pytest tests/ --cov=src --cov-report=term-missing
```