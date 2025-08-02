import yaml
from pathlib import Path
from pydantic import BaseModel, Field


class PersonaConfig(BaseModel):
    model_config = {"extra": "forbid"}
    
    id: str
    name: str
    background: str


class QuestionConfig(BaseModel):
    model_config = {"extra": "forbid"}
    
    text: str
    covers: list[str] = Field(default_factory=list)
    rationale: str = Field(default="", description="Optional rationale for why this question tests specific hypotheses")


class ProductConfig(BaseModel):
    model_config = {"extra": "forbid"}
    
    name: str
    description: str


class HypothesisConfig(BaseModel):
    model_config = {"extra": "forbid"}
    
    id: str
    description: str


class QuestionsConfig(BaseModel):
    model_config = {"extra": "forbid"}
    
    warmup: list[str] = Field(default_factory=list)
    diverge: list[QuestionConfig] = Field(default_factory=list)
    reflect: list[str] = Field(default_factory=list)
    converge: list[str] = Field(default_factory=list)
    closure: list[str] = Field(default_factory=list)


class FollowUpConfig(BaseModel):
    """Configuration for follow-up decision criteria"""
    model_config = {"extra": "forbid"}
    
    min_word_count: int = Field(default=30, description="Minimum words for complete response")
    min_themes_covered: int = Field(default=2, description="Minimum themes to cover")
    min_sentiment_strength: float = Field(default=0.3, description="Minimum sentiment clarity")
    target_hypothesis_coverage: float = Field(default=0.7, description="Target coverage per question")
    prioritize_uncovered: bool = Field(default=True, description="Prioritize uncovered hypotheses")


class PhaseConfig(BaseModel):
    """Configuration for discussion phases"""
    model_config = {"extra": "forbid"}
    
    warmup: dict = Field(default_factory=dict)
    diverge: dict = Field(default_factory=lambda: {"max_follow_ups": 2})
    reflect: dict = Field(default_factory=lambda: {"share_synthesized_themes": True})
    converge: dict = Field(default_factory=lambda: {"force_tradeoffs": True})
    closure: dict = Field(default_factory=lambda: {"max_follow_ups": 0})


class BoardConfig(BaseModel):
    model_config = {"extra": "forbid"}
    
    product: ProductConfig
    hypotheses: list[HypothesisConfig]
    questions: QuestionsConfig
    personas: list[PersonaConfig]
    phase_config: PhaseConfig = Field(default_factory=PhaseConfig)
    followup_criteria: FollowUpConfig = Field(default_factory=FollowUpConfig)
    policy: dict = Field(default_factory=dict)
    
    def get_hypothesis_ids(self) -> list[str]:
        return [h.id for h in self.hypotheses]
    
    def get_persona_ids(self) -> list[str]:
        return [p.id for p in self.personas]
    
    def get_all_questions(self) -> list[str]:
        all_questions = []
        all_questions.extend(self.questions.warmup)
        all_questions.extend([q.text for q in self.questions.diverge])
        all_questions.extend(self.questions.reflect)
        all_questions.extend(self.questions.converge)
        all_questions.extend(self.questions.closure)
        return all_questions


def load_config(config_path: str | Path) -> BoardConfig:
    config_path = Path(config_path)
    
    if not config_path.suffix in ['.yml', '.yaml']:
        raise ValueError("Configuration file must be a YAML file (.yml or .yaml)")
    
    if not config_path.exists():
        raise FileNotFoundError(f"Configuration file not found: {config_path}")
    
    with open(config_path, 'r', encoding='utf-8') as f:
        data = yaml.safe_load(f)
    
    if not data:
        raise ValueError("Configuration file is empty")
    
    # Convert diverge questions to QuestionConfig objects
    if 'questions' in data and 'diverge' in data['questions']:
        diverge_questions = []
        for q in data['questions']['diverge']:
            if isinstance(q, dict):
                diverge_questions.append(QuestionConfig(**q))
            else:
                diverge_questions.append(QuestionConfig(text=q, covers=[]))
        data['questions']['diverge'] = diverge_questions
    
    return BoardConfig(**data)


def validate_config(config: BoardConfig) -> list[str]:
    """Validate configuration and return list of warnings"""
    warnings = []
    
    # Check if all hypotheses have at least one question
    hypothesis_ids = set(config.get_hypothesis_ids())
    covered_hypotheses = set()
    
    for question in config.questions.main:
        covered_hypotheses.update(question.covers)
    
    uncovered = hypothesis_ids - covered_hypotheses
    if uncovered:
        warnings.append(f"Hypotheses not covered by any question: {', '.join(uncovered)}")
    
    # Check if we have at least 2 personas
    if len(config.personas) < 2:
        warnings.append("At least 2 personas are recommended for meaningful discussion")
    
    # Check if we have questions for each phase
    if not config.questions.warmup:
        warnings.append("No warmup questions defined")
    if not config.questions.diverge:
        warnings.append("No diverge questions defined")
    if not config.questions.converge:
        warnings.append("No convergence questions defined")
    if not config.questions.closure:
        warnings.append("No closure questions defined")
    
    return warnings