# Virtual Board: AI-Powered Product Validation System

An advanced AI system that simulates customer panels using multiple AI personas to validate product concepts through structured research sessions. The virtual board conducts realistic user research discussions to test hypotheses and gather insights about product-market fit.

## 🚀 Overview

Virtual Board creates authentic user research sessions by deploying AI personas that embody real user characteristics, behaviors, and motivations. Each persona participates in structured discussions across multiple phases to validate product hypotheses and provide actionable feedback.

### Key Features

- **🎭 AI Personas**: Realistic user personas with distinct backgrounds, motivations, and behaviors
- **📋 Structured Research**: Multi-phase discussion flow (Warmup → Diverge → Converge → Closure)
- **🎯 Hypothesis Testing**: Questions mapped to specific hypotheses for systematic validation
- **🧠 Intelligent Moderation**: AI facilitator manages discussions and follow-ups
- **📊 Real-time Analysis**: Sentiment analysis, bias detection, and theme clustering
- **⚖️ Bias Mitigation**: Automated bias detection and question reformulation
- **🔄 Adaptive Flow**: Dynamic follow-up questions based on response quality

## 🏗️ Architecture

### Core Components

```
Virtual Board System
├── Orchestrator          # Manages session flow and phase transitions
├── Personas             # AI personas with unique characteristics
├── Facilitator          # Moderates discussions and asks questions
├── Analyst              # Analyzes responses and extracts insights
├── Bias Moderator       # Detects and mitigates research bias
└── Theme Analyst        # Clusters themes and identifies patterns
```

### Research Phases

1. **🔥 Warmup**: Build rapport and establish context
2. **🌟 Diverge**: Explore broad reactions and gather diverse perspectives
3. **🎯 Converge**: Focus on priorities, trade-offs, and decisions
4. **✅ Closure**: Identify risks, deal-breakers, and final validation

### Agent Network

The system uses specialized AI agents powered by the OpenAI Agents SDK:

| Agent | Role | Responsibilities |
|-------|------|-----------------|
| **Orchestrator** | Session Manager | Controls flow, transitions, hypothesis tracking |
| **Facilitator** | Moderator | Asks questions, manages discussions |
| **Personas** | Participants | Provide authentic user perspectives |
| **Analyst** | Researcher | Analyzes responses, extracts insights |
| **Bias Moderator** | Quality Control | Detects bias, suggests improvements |
| **Theme Analyst** | Pattern Recognition | Identifies themes, clusters insights |

## 🛠️ Installation

### Prerequisites

- Python 3.11+ (recommend 3.12)
- OpenAI API key with Agents SDK access
- Conda environment (recommended)

### Setup Options

#### Option 1: Using Conda (Recommended)

```bash
# Create new conda environment
conda create -n virtual-board python=3.12
conda activate virtual-board

# Install dependencies
pip install -r requirements.txt
```

#### Option 2: Using pyenv

```bash
# Install Python 3.12
pyenv install 3.12
pyenv local 3.12

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

## 🔧 Configuration

### Environment Setup

1. **Set OpenAI API Key**
   ```bash
   export OPENAI_API_KEY="your-key-here"
   # Or add to .env file in project root
   ```

2. **Board Configuration**
   
   Edit `config/board_config.yml` to define your research session:

```yaml
product:
  name: "Your Product Name"
  description: "Product description for context"

hypotheses:
  - id: "H1"
    description: "Your first hypothesis to test"
  - id: "H2"
    description: "Your second hypothesis to test"

questions:
  warmup:
    - "Rapport-building question"
    - "Context-setting question"
  
  diverge:
    - text: "Open exploration question"
      covers: ["H1", "H2"]
      rationale: "Why this question tests these hypotheses"
  
  converge:
    - "Priority/trade-off question"
    - "Decision-focused question"
  
  closure:
    - "Risk/concern question"
    - "Recommendation question"

personas:
  - id: "persona1"
    name: "Persona Name"
    background: |
      Detailed persona background including demographics,
      motivations, behaviors, and relevant context.

# Phase configuration
phase_config:
  warmup:
    max_follow_ups: 1
  diverge:
    max_follow_ups: 2
  converge:
    force_tradeoffs: true
    ranking_method: "points"
    max_follow_ups: 1
  closure:
    max_follow_ups: 0

# Follow-up decision criteria
followup_criteria:
  min_word_count: 40
  min_themes_covered: 2
  min_sentiment_strength: 0.4
  target_hypothesis_coverage: 0.8
  prioritize_uncovered: true

# Policy settings
policy:
  min_personas: 3
  max_personas: 5
  target_coverage: 0.8
  allow_early_convergence: true
```

### Persona Design

Effective personas should include:

- **Demographics**: Age, role, location, experience level
- **Motivations**: Goals, needs, pain points
- **Context**: Relevant background and circumstances
- **Personality**: Communication style and preferences

Example:
```yaml
- id: "tech_savvy_student"
  name: "Alex Chen"
  background: |
    22-year-old computer science student at a top university.
    Heavy user of productivity apps and online learning platforms.
    Values efficiency and tends to try new technologies early.
    Often compares features across different platforms.
```

## 🚀 Running Sessions

### Basic Usage

```bash
python main.py
```

### Session Flow

1. **Initialization**: Loads config, initializes personas and agents
2. **Product Introduction**: Introduces the product concept to all personas
3. **Research Phases**: Executes warmup, diverge, converge, and closure phases
4. **Analysis**: Generates insights, sentiment analysis, and hypothesis validation
5. **Reporting**: Creates session summary and recommendations

### Output

The system generates:

- **Real-time output**: Live session progress and persona responses
- **Session transcripts**: Complete discussion records
- **Analysis reports**: Insights, themes, and hypothesis validation
- **Recommendations**: Actionable next steps based on findings

## 📊 Understanding Results

### Response Analysis

Each persona response includes:

- **Content**: The actual response text
- **Sentiment Score**: Positive/negative sentiment (-1 to +1)
- **Themes**: Identified discussion themes
- **Hypothesis Coverage**: Which hypotheses the response addresses
- **Quality Metrics**: Word count, depth, relevance

### Hypothesis Validation

Track how well each hypothesis is validated:

- **Coverage Percentage**: How much each hypothesis was discussed
- **Sentiment Distribution**: Positive vs negative reactions
- **Key Insights**: Supporting or contradicting evidence
- **Confidence Level**: Strength of validation

### Bias Detection

The system automatically detects and flags:

- **Leading questions**: Questions that guide toward desired answers
- **Assumption bias**: Questions that assume certain behaviors or preferences
- **Demographic bias**: Questions that exclude certain user groups
- **Confirmation bias**: Questions that only seek supporting evidence

## 🎯 Best Practices

### Question Design

1. **Open-ended**: Use "How", "What", "Why" questions
2. **Neutral**: Avoid leading or biased phrasing
3. **Specific**: Target clear aspects of your hypotheses
4. **Progressive**: Build from general to specific

### Persona Selection

1. **Diverse**: Include varied demographics and perspectives
2. **Relevant**: Ensure personas match your target market
3. **Realistic**: Base on real user research when possible
4. **Distinct**: Ensure personas have different motivations

### Session Management

1. **Hypothesis Focus**: Ensure questions map to specific hypotheses
2. **Time Management**: Allow sufficient time for each phase
3. **Follow-up Strategy**: Use follow-ups to deepen insights
4. **Bias Monitoring**: Pay attention to bias warnings

## 🧪 Testing and Validation

### Running Tests

```bash
pytest tests/
```

### Test Coverage

The test suite covers:

- Configuration loading and validation
- Persona behavior consistency
- Question flow and logic
- Analysis accuracy
- Bias detection effectiveness

### Manual Testing

Test individual components:

```python
# Test persona responses
from src.virtual_board_agents.agents import VirtualBoardAgents
personas = agents.get_persona_responses(question, context)

# Test bias detection
from src.analysis.bias_detection import detect_bias
bias_check = detect_bias(question)
```

## 🔄 Integration with Pipeline

Virtual Board integrates seamlessly with the Review Analysis Pipeline:

1. **Pipeline generates** board configs from review analysis
2. **Virtual Board executes** research sessions using generated configs
3. **Results inform** product development and feature prioritization

### Automated Integration

```bash
# Run full pipeline + virtual board
cd ..
python -m pipeline
cd virtual-board
python main.py
```

## 🐛 Troubleshooting

### Common Issues

1. **Agent Import Errors**
   ```bash
   # Ensure virtual-board conda environment is active
   conda activate virtual-board
   pip install -r requirements.txt
   ```

2. **Configuration Errors**
   - Check YAML syntax in `config/board_config.yml`
   - Ensure all required fields are present
   - Validate persona background text formatting

3. **OpenAI API Issues**
   ```bash
   # Check API key is set
   echo $OPENAI_API_KEY
   
   # Verify API access
   curl -H "Authorization: Bearer $OPENAI_API_KEY" \
        https://api.openai.com/v1/models
   ```

4. **Session Hangs or Timeouts**
   - Check internet connection
   - Verify OpenAI API quota and limits
   - Review persona complexity (simpler personas respond faster)

### Debug Mode

Enable detailed logging:

```python
import logging
logging.basicConfig(level=logging.DEBUG)
```

### Performance Optimization

- **Reduce personas**: Use 3-4 personas for faster sessions
- **Shorter backgrounds**: Concise persona descriptions speed up responses
- **Focused questions**: Specific questions get more targeted responses
- **Phase limits**: Set appropriate `max_follow_ups` in config

## 📈 Advanced Features

### Custom Analysis

Extend the analysis capabilities:

```python
# Custom theme analysis
from src.analysis.theme_clustering import ThemeClusterer
clusterer = ThemeClusterer(custom_categories=['usability', 'pricing'])

# Custom bias detection
from src.analysis.bias_detection import BiasDetector
detector = BiasDetector(additional_checks=['cultural_bias'])
```

### Multi-Session Tracking

Track insights across multiple sessions:

```python
# Session comparison
from src.utils.session_comparison import compare_sessions
insights = compare_sessions(session1, session2)
```

### Export and Reporting

Generate various report formats:

```bash
# Export to different formats
python export_results.py --format json
python export_results.py --format csv
python export_results.py --format pdf
```

## 🤝 Contributing

### Development Setup

1. Fork the repository
2. Create feature branch
3. Install development dependencies: `pip install -r requirements-dev.txt`
4. Run tests: `pytest`
5. Submit pull request

### Extending Agents

Add new analysis capabilities:

1. Create new agent in `src/virtual_board_agents/`
2. Define agent instructions in `src/virtual_board_agents/prompts/agents/`
3. Update orchestrator to use new agent
4. Add tests for new functionality

## 📄 License

[Your License Here]

## 🙋‍♀️ Support

For issues specific to Virtual Board:

1. Check configuration files are properly formatted
2. Review session logs for error details
3. Test with simpler configurations first
4. Verify OpenAI API access and quotas

For pipeline integration issues, see the main project README.

---

*Virtual Board - Bringing user research into the AI age* 🚀