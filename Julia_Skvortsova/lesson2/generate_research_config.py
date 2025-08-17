#!/usr/bin/env python3
"""
Test script to call steps 8-9 with custom concept but existing personas from personas.yml
"""
import asyncio
import json
import yaml
from dotenv import load_dotenv
from pipeline import ReviewAnalysisPipeline
from pipeline_models import PipelineConfig, ProductConcept, ProductHypothesis

# Load environment variables
load_dotenv()

async def generate_research_config_by_concept():
    # Create pipeline config
    config = PipelineConfig()
    pipeline = ReviewAnalysisPipeline(config)
    
    # Create custom product concept
    concept = ProductConcept(
        name="ReplayLearn",
        tagline="Revisit concepts you struggled with, or simply start again from scratch",
        description="Course progress reset feature",
        target_market="Returning learners who paused a course and want to start over fresh, and Mastery-driven learners who completed a course but wish to repeat it for reinforcement",
        key_value_propositions=[
        ],
        core_features=[
            "Course progress reset functionality to restart or repeat material easily"
        ],
        hypotheses_to_test=[],
        success_metrics=[],
    )
    
    # Load existing personas from personas.yml and convert to expected format
    with open(config.personas_file, 'r') as f:
        existing_data = yaml.safe_load(f)
    
    # Select specific personas (you can change these IDs)
    selected_persona_ids = ["svetlana", "nikita", "nastya"]
    
    personas = []
    for category in ['teachers', 'learners']:
        if category in existing_data:
            for persona in existing_data[category]:
                if persona['id'] in selected_persona_ids:
                    personas.append({
                        "id": persona['id'],
                        "name": persona['name'], 
                        "background": persona['background'],
                        "pain_points": [],  # Not defined in personas.yml
                        "needs": []  # Not defined in personas.yml
                    })
    
    print(f"📋 Using {len(personas)} existing personas:")
    for p in personas:
        print(f"  - {p['name']} ({p['id']})")
    
    # Initialize artifacts directory
    pipeline.artifacts.start_run()
    
    # Call steps 8-9 directly
    print(f"\n🚀 Calling Steps 8 and 9 for '{concept.name}'...")
    research_questions = await pipeline.generate_research_questions(concept, personas)
    product = await pipeline.generate_board_config(concept, personas, research_questions)
    
    print(f"\n✅ Board config generated at: {pipeline.artifacts.get_path('board_config.yml')}")

    # Display results
    print("\n✅ Research Questions Generated:")

    # Print research questions as JSON, handling Pydantic and dict types
    try:
        if hasattr(research_questions, 'model_dump'):
            data = research_questions.model_dump()
        elif hasattr(research_questions, 'dict'):
            data = research_questions.dict()
        else:
            data = research_questions
        print(json.dumps(data, indent=2, ensure_ascii=False))
    except Exception as e:
        print(f"Error displaying research questions: {e}")
    
    
    return research_questions

if __name__ == "__main__":
    asyncio.run(generate_research_config_by_concept())