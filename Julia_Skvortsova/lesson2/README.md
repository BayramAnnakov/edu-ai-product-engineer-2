# Review Analysis Pipeline with Agents Network

A comprehensive AI-powered pipeline that analyzes user reviews and generates virtual board configurations for product concept validation. The system uses a network of specialized AI agents to process reviews, extract insights, and create research sessions.

## 🚀 Overview

This pipeline transforms raw user reviews into actionable product insights through an 8-step automated process, culminating in a virtual board session for concept validation.

### Key Features

- **🤖 Agents Network**: 8 specialized AI agents handling different pipeline stages
- **📊 Automated Analysis**: Review summarization, feature extraction, and persona matching
- **🎯 RICE Prioritization**: Feature scoring using Reach, Impact, Confidence, Effort framework
- **💡 Product Concept Generation**: AI-generated product concepts with hypotheses
- **🔬 Research Design**: Automated generation of research questions and hypotheses
- **🎭 Virtual Board**: Automated user research sessions with AI personas
- **📈 Structured Output**: Pydantic models ensure consistent data formats

## 🏗️ Architecture

### Agents Network

The pipeline uses 8 specialized agents, each with specific instructions and expertise:

| Agent | Purpose | Input | Output |
|-------|---------|-------|--------|
| **Review Summarizer** | Analyzes and summarizes review data | Raw reviews JSON | Structured summary |
| **Feature Extractor** | Identifies feature requests from reviews | Sample reviews | Feature requests list |
| **Persona Extractor** | Extracts user personas from review patterns | Review data | User personas |
| **Persona Matcher** | Matches extracted to existing personas | Extracted + existing personas | Match scores |
| **RICE Analyst** | Scores features using RICE framework | Features + context | Priority scores |
| **Product Conceptor** | Generates product concepts | Features + personas + summary | Product concept |
| **Market Researcher** | Creates market research prompts | Product concept | Research prompts |
| **Research Designer** | Designs research questions & hypotheses | Concept + personas | Questions + hypotheses |

### Pipeline Flow

```
CSV Reviews → Review Summarizer → Feature Extractor → RICE Analyst → Product Conceptor
                     ↓                    ↓                ↓              ↓
                Persona Extractor → Persona Matcher → Best Personas → Research Designer
                                                           ↓              ↓
                                                    Market Researcher → Board Config
                                                                          ↓
                                                                   Virtual Board
```

## 🛠️ Installation

### Prerequisites

- Python 3.11+
- OpenAI API key with Agents SDK access
- Conda environment (recommended)

### Setup

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd lesson2
   ```

2. **Create conda environment**
   ```bash
   conda create -n virtual-board python=3.12
   conda activate virtual-board
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Set up environment variables**
   ```bash
   cp .env.example .env
   # Edit .env with your OpenAI API key
   echo "OPENAI_API_KEY=your_api_key_here" >> .env
   ```

5. **Prepare data files**
   ```bash
   # Ensure these files exist:
   # - data/reviews.csv (your review data)
   # - docs/personas.yml (existing personas)
   ```

## 📊 Data Formats

### Input Files

#### `data/reviews.csv`
```csv
id,source_id,published_at,rating,sentiment,categories,content
1,101,2024-01-15,4,1,"['usability','features']","Great course but needs reset feature"
```

#### `docs/personas.yml`
```yaml
learners:
  - id: "nastya"
    name: "Anastasia Moroz"
    background: "21-year-old economics student..."
teachers:
  - id: "instructor_alex"
    name: "Alex Thompson"
    background: "Experienced online instructor..."
```

### Output Artifacts

Each pipeline run creates timestamped artifacts in `artifacts/YYYY-MM-DD_HH-MM-SS/`:

- `summary.json` - Review analysis summary
- `features.json` - Extracted feature requests
- `personas.json` - Extracted personas
- `persona_matches.json` - Persona matching results
- `best_personas.json` - Top matching personas
- `priorities.json` - RICE-scored features
- `product_concept.json` - Generated product concept
- `research_questions.json` - Research questions
- `board_config.yml` - Virtual board configuration
- `generated_hypotheses.json` - Auto-generated hypotheses (if any)

## 🚀 Usage

### Full Pipeline

Run the complete analysis pipeline:

```bash
python -m pipeline
```

### Generate Research Config Only

Create research questions and board config for a custom product concept:

```bash
python generate_research_config.py
```

This script demonstrates:
- Creating custom product concepts
- Using existing personas from `personas.yml`
- Generating hypotheses when missing
- Creating board configurations

### Virtual Board Session

After generating a board config:

```bash
cd virtual-board
python main.py
```

## 🔧 Configuration

### Pipeline Settings

Configure the pipeline through `PipelineConfig` in `pipeline_models.py`:

```python
class PipelineConfig(BaseModel):
    # Data files
    reviews_file: str = "data/reviews.csv"
    personas_file: str = "docs/personas.yml"
    
    # Output settings
    output_language: str = "English"
    artifacts_dir: str = "artifacts"
    
    # Model selection
    reasoning_model: str = "gpt-4.1"
    categorization_model: str = "gpt-4.1-nano"
    
    # Feature extraction
    min_feature_frequency: int = 2
    max_features_to_extract: int = 10
    
    # Virtual board
    num_personas_for_board: int = 4
    max_hypotheses: int = 3
```

### Agent Instructions

Each agent's behavior is defined by markdown files in `prompts/agents/`:

- `review_summarizer.md` - Review analysis instructions
- `feature_extractor.md` - Feature identification guidelines
- `persona_extractor.md` - Persona extraction criteria
- `persona_matcher.md` - Matching logic and scoring
- `rice_analyst.md` - RICE scoring methodology
- `product_conceptor.md` - Product concept generation
- `market_researcher.md` - Market research prompt creation
- `research_designer.md` - Research question design & hypothesis generation

## 🎯 Key Features

### Automatic Hypothesis Generation

The Research Designer agent can automatically generate testable hypotheses when none are provided:

```python
# If product concept has no hypotheses, agent generates them
concept = ProductConcept(
    name="ReplayLearn",
    hypotheses_to_test=[]  # Empty - will be auto-generated
)

# Agent creates hypotheses like:
# H1: Users will utilize the course reset feature when returning to courses
# H2: The reset feature will increase learner satisfaction
# H3: Progress reset provides competitive advantage
```

### Structured Output

All agents use Pydantic models for consistent, type-safe outputs:

```python
class FeatureExtractionOutput(BaseModel):
    features: list[FeatureRequest]

class ResearchQuestionsOutput(BaseModel):
    hypotheses: Optional[list[ProductHypothesis]] = []
    research_questions: ResearchQuestions
```

### Persona Matching

The system intelligently matches extracted personas to existing ones:

```python
# Extracted personas are matched to real existing personas
# Returns actual personas from personas.yml, not extracted ones
best_personas = pipeline._get_best_matching_personas(
    extracted_personas, matches, max_personas=3
)
```

### Clean YAML Generation

Board configurations are generated using PyYAML with custom formatting:

```yaml
product:
  name: ReplayLearn
  description: Course progress reset feature

hypotheses:
- id: H1
  description: Users will utilize the course reset feature...

questions:
  diverge:
  - text: "What are your thoughts on course reset functionality?"
    covers: ["H1", "H2"]
    rationale: "Tests user perception and value proposition"
```

## 🧪 Testing

### Manual Testing

Test specific pipeline steps:

```python
# Test steps 8-9 with custom concept
python generate_research_config.py

# Test hypothesis generation
concept = ProductConcept(name="TestProduct", hypotheses_to_test=[])
questions = await pipeline.generate_research_questions(concept, personas)
```

### Example Outputs

The pipeline generates rich, structured outputs:

**Product Concept:**
```json
{
  "name": "ReplayLearn",
  "tagline": "Revisit concepts you struggled with, or start fresh",
  "hypotheses_to_test": [
    {
      "id": "H1",
      "description": "Users will utilize the course reset feature",
      "assumption": "Learners want to restart courses for mastery"
    }
  ]
}
```

**Research Questions:**
```json
{
  "warmup": ["Tell us about your learning habits..."],
  "diverge": [
    {
      "text": "What are your thoughts on course reset?",
      "covers": ["H1", "H2"],
      "rationale": "Tests perceived value and use cases"
    }
  ]
}
```

## 🐛 Troubleshooting

### Common Issues

1. **Missing OpenAI API Key**
   ```bash
   export OPENAI_API_KEY="your_key_here"
   # Or add to .env file
   ```

2. **Virtual Board Import Errors**
   ```bash
   # Ensure you're in the virtual-board conda environment
   conda activate virtual-board
   ```

3. **Missing Data Files**
   ```bash
   # Check required files exist:
   ls data/reviews.csv
   ls docs/personas.yml
   ```

4. **Agent Response Parsing Errors**
   - Agents use structured output - check Pydantic model compatibility
   - Review agent instruction files in `prompts/agents/`

### Debug Mode

Enable detailed logging:

```python
import logging
logging.basicConfig(level=logging.DEBUG)
```

## 📈 Performance

### Pipeline Execution Time

- **Full Pipeline**: ~2-5 minutes (depending on review count)
- **Steps 8-9 Only**: ~20-30 seconds
- **Virtual Board Session**: 10-30 minutes (varies by discussion depth)

### Cost Optimization

- Uses different models for different tasks (`gpt-4.1` vs `gpt-4.1-nano`)
- Structured output reduces token usage
- Efficient prompt design minimizes API calls

## 🤝 Contributing

### Adding New Agents

1. Create instruction file in `prompts/agents/new_agent.md`
2. Add agent type to `PipelineAgentType` enum
3. Implement in `PipelineAgents` class
4. Update pipeline flow in main pipeline

### Extending Output Models

1. Define new Pydantic models in `pipeline_models.py`
2. Update agent instructions for structured output
3. Modify pipeline methods to handle new formats

## 📁 Project Structure

```
lesson2/
├── pipeline.py                 # Main pipeline implementation
├── pipeline_agents.py          # Agents network manager
├── pipeline_constants.py       # Agent type constants
├── pipeline_models.py          # Pydantic data models
├── pipeline_utils.py           # Utilities and logging
├── pipeline_prompts.py         # Prompt management
├── generate_research_config.py # Manual testing script
├── data/
│   └── reviews.csv            # Input review data
├── docs/
│   └── personas.yml           # Existing personas
├── prompts/
│   ├── agents/                # Agent instruction files
│   └── evaluate_product_idea.md
├── artifacts/                 # Generated outputs
└── virtual-board/             # Virtual board session system
```

## 🙋‍♀️ Support

For questions or issues:
1. Check the troubleshooting section
2. Review agent instruction files
3. Examine recent pipeline artifacts
4. Check logs for detailed error information

---

*Built with ❤️ using OpenAI Agents SDK and Python*