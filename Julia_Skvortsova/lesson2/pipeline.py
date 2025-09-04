"""Main pipeline for review analysis and virtual board generation"""
import asyncio
import json
import pandas as pd
import yaml
from datetime import datetime
from pathlib import Path
from typing import Optional
import os

from pipeline_models import (
    ReviewData, ReviewSummary, FeatureRequest, ExtractedPersona,
    PersonaMatch, RICEScore, ProductConcept, ProductIdea, 
    PipelineArtifacts, PipelineConfig
)
from pipeline_utils import (
    ArtifactManager, log_step, 
    logger, format_percentage
)
from pipeline_agents import PipelineAgents
from pipeline_constants import PipelineAgentType
from pipeline_prompts import PromptManager


class ReviewAnalysisPipeline:
    """Main pipeline for analyzing reviews and generating virtual board"""
    
    def __init__(self, config: PipelineConfig):
        self.config = config
        self.artifacts = ArtifactManager(config.artifacts_dir)
        self.agents = PipelineAgents(config)
        self.prompts = PromptManager(config.prompts_dir)
        
    @log_step("Step 1-2: Load and summarize reviews")
    async def load_and_summarize_reviews(self) -> ReviewSummary:
        """Load reviews from CSV and create LLM summary"""
        # Load reviews
        df = pd.read_csv(self.config.reviews_file)
        logger.info(f"Loaded {len(df)} reviews")
        
        # Convert to ReviewData objects
        reviews = []
        for _, row in df.iterrows():
            # Parse categories from string representation
            categories = eval(row['categories']) if isinstance(row['categories'], str) else row['categories']
            
            review = ReviewData(
                id=row['id'],
                source_id=row['source_id'],
                published_at=pd.to_datetime(row['published_at']),
                rating=int(row['rating']),
                sentiment=row['sentiment'],
                categories=categories,
                content=row['content']
            )
            reviews.append(review)
        
        # Calculate basic stats
        avg_rating = df['rating'].mean()
        sentiment_dist = {str(k): v for k, v in df['sentiment'].value_counts().to_dict().items()}
        
        # Prepare reviews for LLM
        reviews_json = json.dumps([{
            'id': r.id,
            'source_name': f"Source_{r.source_id}",
            'date': r.published_at.strftime('%Y-%m-%d'),
            'rating': r.rating,
            'text': r.content,
            'version': 'unknown'
        } for r in reviews], ensure_ascii=False)
        
        # Get LLM summary
        summary_text = await self.agents.run_agent(
            PipelineAgentType.REVIEW_SUMMARIZER,
            f"Analyze these reviews in {self.config.output_language}:\n\n{reviews_json}",
            temperature=0.3
        )
        
        # Parse summary into structured format
        summary = self._parse_summary(summary_text, len(reviews), avg_rating, sentiment_dist)
        
        # Save artifacts
        self.artifacts.save_json(summary, "summary.json")
        self.artifacts.save_text(summary_text, "summary_raw.txt")
        
        return summary
    
    def _parse_summary(self, summary_text: str, total_reviews: int, 
                      avg_rating: float, sentiment_dist: dict) -> ReviewSummary:
        """Parse LLM summary text into structured format"""
        # This is a simplified parser - in production would be more robust
        lines = summary_text.split('\n')
        
        # Extract sections
        executive_summary = ""
        top_complaints = []
        positive_feedback = []
        technical_issues = []
        suggestions = []
        confidence = 80.0
        limitations = []
        
        current_section = None
        for line in lines:
            line = line.strip()
            if not line:
                continue
                
            # Detect sections
            if "Executive Summary" in line:
                current_section = "executive"
            elif "Top Complaints" in line:
                current_section = "complaints"
            elif "Positive Feedback" in line:
                current_section = "positive"
            elif "Technical Issues" in line:
                current_section = "technical"
            elif "Improvement Suggestions" in line:
                current_section = "suggestions"
            elif "Confidence" in line:
                current_section = "confidence"
            else:
                # Add content to current section
                if current_section == "executive" and line:
                    executive_summary += line + " "
                elif current_section == "complaints" and line.startswith("-"):
                    top_complaints.append({"description": line[1:].strip(), "severity": 0.7})
                elif current_section == "positive" and line.startswith("-"):
                    positive_feedback.append({"description": line[1:].strip(), "importance": 0.8})
                elif current_section == "technical" and line.startswith("-"):
                    technical_issues.append(line[1:].strip())
                elif current_section == "suggestions" and line.startswith("-"):
                    suggestions.append(line[1:].strip())
                elif current_section == "confidence" and "confidence score" in line.lower():
                    # Try to extract confidence score
                    try:
                        import re
                        match = re.search(r'(\d+)', line)
                        if match:
                            confidence = float(match.group(1))
                    except:
                        pass
        
        return ReviewSummary(
            total_reviews=total_reviews,
            average_rating=avg_rating,
            sentiment_distribution=sentiment_dist,
            executive_summary=executive_summary.strip(),
            top_complaints=top_complaints[:5],
            positive_feedback=positive_feedback[:3],
            technical_issues=technical_issues,
            improvement_suggestions=suggestions,
            confidence_score=confidence,
            limitations=limitations or ["Limited review sample size"]
        )
    
    @log_step("Step 3: Extract features")
    async def extract_features(self, summary: ReviewSummary) -> list[FeatureRequest]:
        """Extract feature requests from reviews"""
        # Load sample of reviews for feature extraction
        df = pd.read_csv(self.config.reviews_file)
        sample_reviews = df.sample(min(100, len(df))).to_dict('records')
        
        reviews_json = json.dumps(sample_reviews, ensure_ascii=False)
        
        response = await self.agents.run_agent(
            PipelineAgentType.FEATURE_EXTRACTOR,
            f"Analyze these reviews:\n\n{reviews_json}",
            temperature=0.3,
            response_format={"type": "json_object"}
        )
        
        # With structured output, response is already a FeatureExtractionOutput object 
        if hasattr(response, 'features'):
            features = response.features
        else:
            # Fallback for string response
            features_data = json.loads(str(response))
            features = [FeatureRequest(**f) for f in features_data['features']]
        
        # Filter by minimum frequency
        features = [f for f in features if f.frequency >= self.config.min_feature_frequency]
        features = features[:self.config.max_features_to_extract]
        
        self.artifacts.save_json(features, "features.json")
        return features
    
    @log_step("Step 4: Extract and match personas")
    async def extract_personas(self, summary: ReviewSummary) -> tuple[list[ExtractedPersona], list[PersonaMatch]]:
        """Extract personas from reviews and match to existing"""
        # Load sample of reviews
        df = pd.read_csv(self.config.reviews_file)
        sample_reviews = df.sample(min(100, len(df))).to_dict('records')
        reviews_json = json.dumps(sample_reviews, ensure_ascii=False)
        
        # Extract personas
        response = await self.agents.run_agent(
            PipelineAgentType.PERSONA_EXTRACTOR,
            f"Extract personas from these reviews:\n\n{reviews_json}",
            temperature=0.5,
            response_format={"type": "json_object"}
        )
        
        # With structured output, response is already a PersonaExtractionOutput object
        if hasattr(response, 'personas'):
            extracted_personas = response.personas
        else:
            # Fallback for string response
            personas_data = json.loads(str(response))
            extracted_personas = [ExtractedPersona(**p) for p in personas_data['personas']]
        
        # Load existing personas
        with open(self.config.personas_file, 'r') as f:
            existing_data = yaml.safe_load(f)
        
        # Flatten existing personas
        existing_personas = []
        for category in ['teachers', 'learners']:
            if category in existing_data:
                existing_personas.extend(existing_data[category])
        
        # Match personas
        extracted_json = json.dumps([p.model_dump() for p in extracted_personas], ensure_ascii=False)
        existing_json = json.dumps(existing_personas, ensure_ascii=False)
        
        match_response = await self.agents.run_agent(
            PipelineAgentType.PERSONA_MATCHER,
            f"Match these extracted personas:\n{extracted_json}\n\nWith existing personas:\n{existing_json}",
            temperature=0.3,
            response_format={"type": "json_object"}
        )
        
        # With structured output, response is already a PersonaMatchingOutput object
        if hasattr(match_response, 'matches'):
            matches = match_response.matches
        else:
            # Fallback for string response
            matches_data = json.loads(str(match_response))
            matches = [PersonaMatch(**m) for m in matches_data['matches']]
        
        self.artifacts.save_json(extracted_personas, "personas.json")
        self.artifacts.save_json(matches, "persona_matches.json")
        
        return extracted_personas, matches
    
    def _get_best_matching_personas(self, extracted_personas: list[ExtractedPersona], 
                                  matches: list[PersonaMatch], 
                                  max_personas: int = 3) -> list[dict]:
        """Get the best matching existing personas based on match scores"""
        # Load existing personas
        with open(self.config.personas_file, 'r') as f:
            existing_data = yaml.safe_load(f)
        
        # Flatten existing personas with their data
        existing_personas_map = {}
        for category in ['teachers', 'learners']:
            if category in existing_data:
                for persona in existing_data[category]:
                    existing_personas_map[persona['id']] = persona
        
        # Sort matches by score (highest first) and get those with existing matches
        sorted_matches = sorted(matches, key=lambda x: x.match_score, reverse=True)
        
        # Get the best existing personas
        best_personas = []
        for match in sorted_matches:
            if len(best_personas) >= max_personas:
                break
            # Only include matches that have existing persona mappings
            if (hasattr(match, 'existing_persona_id') and 
                match.existing_persona_id and 
                match.existing_persona_id in existing_personas_map):
                existing_persona = existing_personas_map[match.existing_persona_id].copy()
                existing_persona['match_score'] = match.match_score
                existing_persona['extracted_persona_id'] = match.extracted_persona_id
                best_personas.append(existing_persona)
        
        # If we don't have enough matches with existing personas, fill with best extracted personas
        if len(best_personas) < max_personas:
            remaining_slots = max_personas - len(best_personas)
            used_extracted_ids = {p.get('extracted_persona_id') for p in best_personas}
            
            for match in sorted_matches:
                if remaining_slots <= 0:
                    break
                if match.extracted_persona_id not in used_extracted_ids:
                    # Convert extracted persona to dict format
                    extracted_persona = None
                    for ep in extracted_personas:
                        if ep.id == match.extracted_persona_id:
                            extracted_persona = {
                                'id': ep.id,
                                'name': ep.name,
                                'background': ep.background,
                                'match_score': match.match_score,
                                'extracted_persona_id': ep.id
                            }
                            break
                    if extracted_persona:
                        best_personas.append(extracted_persona)
                        remaining_slots -= 1
        
        return best_personas
    
    @log_step("Step 5: RICE scoring")
    async def prioritize_features(self, features: list[FeatureRequest], 
                                summary: ReviewSummary) -> list[RICEScore]:
        """Score features using RICE framework"""
        features_json = json.dumps([f.model_dump() for f in features], ensure_ascii=False)
        pain_points = [c['description'] for c in summary.top_complaints[:3]]
        
        response = await self.agents.run_agent(
            PipelineAgentType.RICE_ANALYST,
            f"Features to score:\n{features_json}\n\nContext:\n- Total reviews: {summary.total_reviews}\n- Average rating: {summary.average_rating}\n- Top pain points: {json.dumps(pain_points, ensure_ascii=False)}",
            temperature=0.3,
            response_format={"type": "json_object"}
        )
        
        # With structured output, response is already a RICEScoringOutput object
        if hasattr(response, 'scores'):
            scores = response.scores
        else:
            # Fallback for string response
            scores_data = json.loads(str(response))
            scores = []
            for score_data in scores_data['scores']:
                score = RICEScore(**score_data)
                scores.append(score)
        
        # Calculate RICE scores
        for score in scores:
            score.calculate_score()
        
        # Sort by RICE score
        scores.sort(key=lambda x: x.rice_score, reverse=True)
        
        self.artifacts.save_json(scores, "priorities.json")
        return scores
    
    @log_step("Step 6: Generate product concept")
    async def generate_product_concept(self, priorities: list[RICEScore], 
                                     personas: list,
                                     summary: ReviewSummary) -> ProductConcept:
        """Generate detailed product concept using LLM reasoning"""
        # Prepare data for the prompt
        top_features = priorities[:5]  # Top 5 features for context
        
        features_summary = []
        for f in top_features:
            features_summary.append({
                "feature": f.feature_description,
                "rice_score": f.rice_score,
                "reach": f"{f.reach_percent}%",
                "impact": f.impact,
                "confidence": f.confidence,
                "effort": f"{f.effort_weeks} weeks"
            })
        
        personas_summary = []
        for p in personas[:3]:  # Top 3 personas
            # Handle both dict and object formats
            if isinstance(p, dict):
                personas_summary.append({
                    "name": p.get("name", "Unknown"),
                    "background": p.get("background", ""),
                    "pain_points": p.get("pain_points", []),
                    "needs": p.get("needs", []),
                    "frequency": f"{p.get('match_score', 0.0):.0%}"
                })
            else:
                personas_summary.append({
                    "name": p.name,
                    "background": p.background,
                    "pain_points": p.pain_points,
                    "needs": p.needs,
                    "frequency": f"{p.frequency:.0%}"
                })
        
        review_summary_data = {
            "total_reviews": summary.total_reviews,
            "average_rating": summary.average_rating,
            "executive_summary": summary.executive_summary,
            "top_complaints": summary.top_complaints[:3],
            "positive_feedback": summary.positive_feedback[:3]
        }
        
        # Generate product concept
        response = await self.agents.run_agent(
            PipelineAgentType.PRODUCT_CONCEPTOR,
            f"Review Summary:\n{json.dumps(review_summary_data, ensure_ascii=False)}\n\nTop Features:\n{json.dumps(features_summary, ensure_ascii=False)}\n\nUser Personas:\n{json.dumps(personas_summary, ensure_ascii=False)}",
            temperature=0.4,
            response_format={"type": "json_object"}
        )
        
        # With structured output, response is already a ProductConceptOutput object
        if hasattr(response, 'product_concept'):
            concept = response.product_concept
        else:
            # Fallback for string response
            concept_data = json.loads(str(response))
            concept = ProductConcept(**concept_data['product_concept'])
        
        # Save artifact
        self.artifacts.save_json(concept, "product_concept.json")
        
        return concept
    
    @log_step("Step 7: Generate market research")
    async def generate_market_research(self, concept: ProductConcept) -> str:
        """Generate market research prompt for the product concept"""
        '''
        try:
            # Try to generate market research prompt using the market researcher agent
            research_prompt = await self.agents.run_agent(
                PipelineAgentType.MARKET_RESEARCHER,
                f"Product idea: {concept.one_sentence_description}",
                temperature=0.3
            )
        except Exception as e:
            logger.warning(f"Market researcher agent failed: {e}, using default template")
        '''

        research_prompt = self.prompts.get_prompt(
            "evaluate_product_idea.md",
            SHORT_IDEA_DESCRIPTION=concept.one_sentence_description
        )

        # Save artifact
        self.artifacts.save_text(research_prompt, "market_research_prompt.md")
        
        logger.info("Market research prompt generated. Execute manually:")
        logger.info(f"Research focus: {concept.one_sentence_description}")
        
        return research_prompt
    
    @log_step("Step 8: Generate research questions")
    async def generate_research_questions(self, concept: ProductConcept, 
                                        personas: list) -> dict:
        """Generate tailored research questions for virtual board phases"""
        # Prepare data for the prompt
        personas_summary = []
        for p in personas[:self.config.num_personas_for_board]:
            # Handle both dict and object formats
            if isinstance(p, dict):
                personas_summary.append({
                    "name": p.get("name", "Unknown"),
                    "background": p.get("background", ""),
                    "pain_points": p.get("pain_points", []),
                    "needs": p.get("needs", [])
                })
            else:
                personas_summary.append({
                    "name": p.name,
                    "background": p.background,
                    "pain_points": p.pain_points,
                    "needs": p.needs
                })
        
        # Check if concept has hypotheses, if not, let the agent generate them
        hypotheses_summary = []
        if concept.hypotheses_to_test:
            for h in concept.hypotheses_to_test:
                hypotheses_summary.append({
                    "id": h.id,
                    "description": h.description,
                    "assumption": h.assumption
                })
        
        concept_summary = {
            "name": concept.name,
            "tagline": concept.tagline,
            "description": concept.description,
            "target_market": concept.target_market,
            "key_value_propositions": concept.key_value_propositions,
            "core_features": concept.core_features
        }
        
        # Generate research questions (and possibly hypotheses)
        prompt = f"Product Concept:\n{json.dumps(concept_summary, ensure_ascii=False)}\n\nUser Personas:\n{json.dumps(personas_summary, ensure_ascii=False)}"
        if hypotheses_summary:
            prompt += f"\n\nHypotheses:\n{json.dumps(hypotheses_summary, ensure_ascii=False)}"
        else:
            prompt += "\n\nNote: No hypotheses provided - please generate 2-3 testable hypotheses based on the product concept."
        
        response = await self.agents.run_agent(
            PipelineAgentType.RESEARCH_DESIGNER,
            prompt,
            temperature=0.3,
            response_format={"type": "json_object"}
        )
        
        # Extract research questions and any generated hypotheses
        research_questions = None
        generated_hypotheses = []
        
        # Handle structured output from agent
        try:
            if isinstance(response, str):
                # Parse JSON string response
                questions_data = json.loads(response)
                research_questions = questions_data['research_questions']
                if 'hypotheses' in questions_data and questions_data['hypotheses']:
                    from pipeline_models import ProductHypothesis
                    generated_hypotheses = [ProductHypothesis(**h) for h in questions_data['hypotheses']]
            else:
                # Handle object response with attributes
                if hasattr(response, 'research_questions'):
                    research_questions = response.research_questions
                if hasattr(response, 'hypotheses') and response.hypotheses:
                    generated_hypotheses = response.hypotheses
        except (json.JSONDecodeError, KeyError) as e:
            logger.error(f"Failed to parse research questions response: {e}")
            # Fallback to empty structure
            research_questions = {"warmup": [], "diverge": [], "converge": [], "closure": []}
        
        # If hypotheses were generated, update the concept
        if generated_hypotheses and not concept.hypotheses_to_test:
            concept.hypotheses_to_test = generated_hypotheses
            # Save updated concept
            self.artifacts.save_json(concept, "product_concept_updated.json")
            logger.info(f"Generated {len(generated_hypotheses)} hypotheses for the product concept")
        
        # Ensure we always return a valid dict
        if research_questions is None:
            research_questions = {"warmup": [], "diverge": [], "converge": [], "closure": []}
        
        # Save artifacts
        self.artifacts.save_json(research_questions, "research_questions.json")
        if generated_hypotheses:
            self.artifacts.save_json(generated_hypotheses, "generated_hypotheses.json")
        
        return research_questions
    
    @log_step("Step 9: Generate board config")
    async def generate_board_config(self, concept: ProductConcept, 
                                   personas: list,
                                   research_questions: dict) -> ProductIdea:
        """Generate virtual board configuration"""
        # Create compatible ProductIdea from concept
        persona_names = []
        for p in personas[:3]:
            if isinstance(p, dict):
                persona_names.append(p.get("name", "Unknown"))
            else:
                persona_names.append(p.name)
        
        product_idea = ProductIdea.from_concept(concept, persona_names)
        
        # Generate board config using the detailed concept and research questions
        board_config = self._generate_board_config(concept, personas, research_questions)
        
        # Save artifacts
        self.artifacts.save_json(product_idea, "product_idea.json")
        
        # Generate YAML with proper formatting
        yaml_content = self._dump_yaml_with_comments(board_config)
        config_path = self.artifacts.save_text(yaml_content, "board_config.yml")
        
        return product_idea
    
    def _generate_board_config(self, concept: ProductConcept, personas: list, 
                               research_questions: dict) -> dict:
        """Generate virtual board configuration from product concept and research questions"""
        # Select personas for board
        selected_personas = personas[:self.config.num_personas_for_board]
        
        # Convert personas to board format
        board_personas = []
        for p in selected_personas:
            if isinstance(p, dict):
                board_personas.append({
                    'id': p.get('id', p.get('extracted_persona_id', 'P001')),
                    'name': p.get('name', 'Unknown'),
                    'background': p.get('background', '')
                })
            else:
                board_personas.append({
                    'id': p.id,
                    'name': p.name,
                    'background': p.background
                })
        
        # Convert research questions to proper format
        questions_dict = self._convert_research_questions(research_questions)
        
        # Ensure diverge questions have proper format
        if 'diverge' in questions_dict:
            diverge_formatted = []
            for q in questions_dict['diverge']:
                if isinstance(q, dict) and 'text' in q:
                    # Already has the right format
                    diverge_formatted.append(q)
                else:
                    # Convert to dict format
                    diverge_formatted.append({
                        'text': str(q),
                        'covers': []
                    })
            questions_dict['diverge'] = diverge_formatted
        
        config = {
            'product': {
                'name': concept.name,
                'description': concept.description
            },
            'hypotheses': [
                {'id': h.id, 'description': h.description}
                for h in concept.hypotheses_to_test
            ],
            'questions': questions_dict,
            'personas': board_personas,
            
            # Phase-specific configuration
            'phase_config': {
                'warmup': {
                    'max_follow_ups': 1
                },
                'diverge': {
                    'max_follow_ups': 2
                },
                'converge': {
                    'force_tradeoffs': True,
                    'ranking_method': 'points',
                    'max_follow_ups': 1
                },
                'closure': {
                    'max_follow_ups': 0  # No follow-ups in final phase
                }
            },
            
            # Explicit follow-up decision criteria
            'followup_criteria': {
                'min_word_count': 40,  # Responses should be at least 40 words
                'min_themes_covered': 2,  # Should cover at least 2 themes/aspects
                'min_sentiment_strength': 0.4,  # Clear positive/negative stance
                'target_hypothesis_coverage': 0.8,  # Aim for 80% hypothesis coverage
                'prioritize_uncovered': True  # Focus on uncovered hypotheses
            },
            
            # Policy configuration
            'policy': {
                'min_personas': 3,
                'max_personas': 5,
                'target_coverage': 0.8,
                'allow_early_convergence': True
            }
        }
        
        return config
    
    
    def _dump_yaml_with_comments(self, data: dict) -> str:
        """Dump YAML with proper formatting and comments"""
        
        # Custom YAML dumper to handle multiline strings properly
        class CustomDumper(yaml.SafeDumper):
            def represent_str(self, value):
                if '\n' in value or len(value) > 60:
                    return self.represent_scalar('tag:yaml.org,2002:str', value, style='|')
                return self.represent_scalar('tag:yaml.org,2002:str', value)
        
        CustomDumper.add_representer(str, CustomDumper.represent_str)
        
        # Generate base YAML
        yaml_str = yaml.dump(
            data, 
            Dumper=CustomDumper,
            default_flow_style=False,
            sort_keys=False,
            allow_unicode=True,
            width=1000  # Prevent unwanted line wrapping
        )
        
        # Add section comments
        yaml_lines = yaml_str.split('\n')
        result_lines = []
        
        for i, line in enumerate(yaml_lines):
            # Add comment before phase_config section
            if line.startswith('phase_config:'):
                result_lines.append('# Phase-specific configuration')
            # Add comment before followup_criteria section  
            elif line.startswith('followup_criteria:'):
                result_lines.append('# Explicit follow-up decision criteria')
            
            result_lines.append(line)
            
            # Add inline comments for followup_criteria
            if 'followup_criteria:' in yaml_lines[:i+5]:  # Within followup_criteria section
                if 'min_word_count:' in line:
                    result_lines[-1] += '  # Responses should be at least 40 words'
                elif 'min_themes_covered:' in line:
                    result_lines[-1] += '  # Should cover at least 2 themes/aspects'
                elif 'min_sentiment_strength:' in line:
                    result_lines[-1] += '  # Clear positive/negative stance'
                elif 'target_hypothesis_coverage:' in line:
                    result_lines[-1] += '  # Aim for 80% hypothesis coverage'
                elif 'prioritize_uncovered:' in line:
                    result_lines[-1] += '  # Focus on uncovered hypotheses'
        
        return '\n'.join(result_lines)
    
    def _convert_research_questions(self, research_questions):
        """Convert research questions to plain dict format for YAML serialization"""
        if hasattr(research_questions, 'model_dump'):
            # It's a Pydantic ResearchQuestions object
            data = research_questions.model_dump()
        elif hasattr(research_questions, 'dict'):
            # Older Pydantic version
            data = research_questions.dict()
        elif isinstance(research_questions, dict):
            # Already a dict
            data = research_questions
        else:
            # Unknown format, return as is
            return research_questions
        
        # Convert diverge questions to plain dicts if needed
        if 'diverge' in data and isinstance(data['diverge'], list):
            diverge_questions = []
            for q in data['diverge']:
                if hasattr(q, 'model_dump'):
                    diverge_questions.append(q.model_dump())
                elif hasattr(q, 'dict'):
                    diverge_questions.append(q.dict())
                elif isinstance(q, dict):
                    diverge_questions.append(q)
                else:
                    # Convert object attributes to dict
                    diverge_questions.append({
                        'text': getattr(q, 'text', ''),
                        'covers': getattr(q, 'covers', []),
                        'rationale': getattr(q, 'rationale', '')
                    })
            data['diverge'] = diverge_questions
        
        return data
    
    @log_step("Step 10: Run virtual board")
    async def run_virtual_board(self, config_path: str) -> Optional[str]:
        """Execute virtual board session"""
        logger.info("Virtual board config generated. To run the virtual board:")
        logger.info(f"1. cd virtual-board")
        logger.info(f"2. cp ../{config_path} config/board_config.yml")
        logger.info(f"3. python main.py")
        
        # For now, just return None as virtual board requires manual execution
        return None
    
    async def run(self) -> PipelineArtifacts:
        """Run the complete pipeline"""
        # Start artifact tracking
        self.artifacts.start_run()
        
        # Step 1-2: Load and summarize
        summary = await self.load_and_summarize_reviews()
        
        # Step 3: Extract features
        features = await self.extract_features(summary)
        
        # Step 4: Extract personas
        personas, matches = await self.extract_personas(summary)
        
        # Get best matching personas for further steps
        best_personas = self._get_best_matching_personas(personas, matches)
        self.artifacts.save_json(best_personas, "best_personas.json")
        
        # Step 5: RICE scoring
        priorities = await self.prioritize_features(features, summary)
        
        # Step 6: Generate product concept
        concept = await self.generate_product_concept(priorities, best_personas, summary)
        
        # Step 7: Generate market research
        market_research_prompt = await self.generate_market_research(concept)
        
        # Step 8: Generate research questions
        research_questions = await self.generate_research_questions(concept, best_personas)
        
        # Step 9: Generate board config
        product = await self.generate_board_config(concept, best_personas, research_questions)
        
        # Step 10: Run virtual board (optional)
        board_config_path = str(self.artifacts.get_path("board_config.yml"))
        report_path = None
        
        if os.getenv("RUN_VIRTUAL_BOARD", "false").lower() == "true":
            report_path = await self.run_virtual_board(board_config_path)
        
        # Create final artifacts summary
        artifacts = PipelineArtifacts(
            timestamp=datetime.now(),
            summary=summary,
            features=features,
            personas=personas,
            persona_matches=matches,
            priorities=priorities,
            product_concept=concept,
            top_idea=product,
            market_research_prompt=str(self.artifacts.get_path("market_research_prompt.md")),
            board_config_path=board_config_path,
            final_report_path=report_path
        )
        
        # Save complete artifacts
        self.artifacts.save_json(artifacts, "pipeline_artifacts.json")
        
        # Print summary
        logger.info("\n" + "="*60)
        logger.info("PIPELINE COMPLETE")
        logger.info("="*60)
        logger.info(f"Reviews analyzed: {summary.total_reviews}")
        logger.info(f"Average rating: {summary.average_rating:.1f}")
        logger.info(f"Features extracted: {len(features)}")
        logger.info(f"Personas identified: {len(personas)} (best: {len(best_personas)})")
        logger.info(f"Product concept: {concept.name}")
        logger.info(f"Tagline: {concept.tagline}")
        logger.info(f"Artifacts saved to: {self.artifacts.run_dir}")
        logger.info("="*60)
        
        return artifacts


async def main():
    """Main entry point"""
    # Load configuration
    config = PipelineConfig()
    
    # Check if required files exist
    if not Path(config.reviews_file).exists():
        logger.error(f"Reviews file not found: {config.reviews_file}")
        return
    
    if not Path(config.personas_file).exists():
        logger.error(f"Personas file not found: {config.personas_file}")
        return
    
    # Create pipeline and run
    pipeline = ReviewAnalysisPipeline(config)
    await pipeline.run()


if __name__ == "__main__":
    # Set up environment
    from dotenv import load_dotenv
    load_dotenv()
    
    # Run pipeline
    asyncio.run(main())